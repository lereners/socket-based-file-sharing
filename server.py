import os
import socket
import threading
import pandas as pd
from threading import Lock
import json
from server_file_commands import (
    server_handle_upload,
    server_handle_dir,
    server_handle_subfolder,
    server_handle_delete,
    server_handle_download
)
import srp
from srp import Verifier
import pickle, json


# IP = "0.0.0.0"
IP = "localhost"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"

#ROOT_DIR = "server_root"
DATA_DIR = "server_data"

# Initiate server root 
ROOT_DIR = "server_root" 
if not os.path.exists(ROOT_DIR): 
    os.makedirs(ROOT_DIR)

USER_DB_FILE = os.path.join(ROOT_DIR, "users.json")

# Utility authentication functions
def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    os.makedirs(os.path.dirname(USER_DB_FILE), exist_ok=True)
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)


# Main server authentication logic function
def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "User already exists."
    
    salt, vkey = srp.create_salted_verification_key(username, password)
    users[username] = {"salt": salt.hex(), "vkey": vkey.hex()}
    save_users(users)
    return True, "User registered successfully."

file_data_lock = Lock()

def recv_cmd(conn, SIZE, FORMAT) -> str:
    """
        Receive a text command
        Do NOT want binary data, boooo
    """

    raw = conn.recv(SIZE)
    if not raw:
        return None

    try:
        return raw.decode(FORMAT)
    except UnicodeDecodeError:
        print("Error: Received binary data when expecting a text command.")
        return None

def handle_client (conn,addr,file_data, download_info, response_times):
        
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the server".encode(FORMAT))

    while True:
        data =  recv_cmd(conn, SIZE, FORMAT)
        if not data:
            break

        split = data.split("@",3)                       # split incoming data up to 2 times
        cmd = split[0].upper()                          # convert command to uppercase, easier handling
       
        arg1 = split[1] if len(split) > 1 else None     # first argument, if exists
        arg2 = split[2] if len(split) > 2 else None     # second argument, if exists
        arg3 = split[3] if len(split) > 3 else None     # third argument, if exists
       
        send_data = "OK@"

        if cmd == "AUTHENTICATE":
            try:
                payload = pickle.loads(conn.recv(4096))
                action = payload.get("action")
            except:
                conn.send(pickle.dumps({"status": "fail", "msg": "Invalid auth payload"}))
                continue

            if action == "register":
                username, password = payload["username"], payload["password"]
                ok, msg = register_user(username, password)
                conn.sendall(pickle.dumps({"status": "ok" if ok else "fail", "msg": msg}))
            
            elif action == "login":
                users = load_users()
                username, A = payload['username'], payload['A']

                if username not in users:
                    conn.sendall(pickle.dumps({"status": "fail", "msg": "Unknown user"}))
                    continue
                
                # create salt & verification key to encrypt password
                salt = bytes.fromhex(users[username]["salt"])
                vkey = bytes.fromhex(users[username]["vkey"])

                # create SRP verifier & get challenge
                v = srp.Verifier(username, salt, vkey, A)
                B = v.get_challenge()[1]

                if B is None:
                    B = v.B

                conn.sendall(pickle.dumps({
                    "salt": salt.hex(), 
                    "B": B.hex()
                }))

                # receive client proof M
                data = pickle.loads(conn.recv(4096))
                M = data["M"]

                # verify session @ HAMK
                HAMK = v.verify_session(M)

                if HAMK:
                    # !! Would use if login authentication worked fully
                    #authenticated = True
                    conn.sendall(pickle.dumps({"status": "ok", "HAMK": HAMK.hex()}))
                    print(f"User {username} authenticated successfully.")
                else:
                    conn.sendall(pickle.dumps({"status": "fail", "HAMK": ""}))
                    print(f"Authentication failed for {username}.")
                continue

        # !! Would use if login authentication worked fully
        #if cmd not in ["AUTHENTICATE", "LOGOUT", "HELLO", "TASK"]:
        #    if not authenticated:
        #        conn.send("ERR@You must log in first!".encode(FORMAT))
        #        continue

        elif cmd == "LOGOUT":
            conn.send("OK@Goodbye".encode(FORMAT))
            break

        elif cmd == "HELLO":
            send_data += "HI!!!"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "TASK":
            send_data += "LOGOUT from the server.\n"    # maybe we describe each command here? :D
            conn.send(send_data.encode(FORMAT))

        elif cmd == "CONNECT":                        # all these 'You input' statements are just for checking :3
            send_data += "You input 'CONNECT'.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "UPLOAD":
            if len(split) < 3: # if 3 arguments are not provided, not enough info
                conn.send("ERR@No filename/size provided.".encode(FORMAT))
                continue

            # giving arguments meaningful names!!!
            file_name = arg1
            file_size = int(arg2)
            server_folder = arg3

            with file_data_lock: # this prevents multiple clients from attempting to modify file_data at once! releases when func returns
                send_data = server_handle_upload(conn, addr, file_name, file_size, server_folder, SIZE, file_data_path, file_data, response_times, response_times_path, FORMAT)
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DOWNLOAD":
            server_handle_download(conn, arg1, arg2, SIZE, FORMAT, download_info, download_info_path, response_times, response_times_path)

        elif cmd == "DELETE":
            send_data = server_handle_delete(arg1, arg2, file_data_path, file_data, response_times, response_times_path, FORMAT)
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DIR":
            send_data = server_handle_dir(arg1, root_path, response_times)
            conn.send(send_data.encode(FORMAT))

        elif cmd == "SUBFOLDER":
            send_data = server_handle_subfolder(arg1, arg2, root_path, response_times)
            conn.send(send_data.encode(FORMAT))

        else:
            send_data = "ERR@Invalid Command\n"
            conn.send(send_data.encode(FORMAT))


    print(f"{addr} disconnected")
    conn.close()

def init_directories():

    os.chdir("..")
    os.makedirs(DATA_DIR, exist_ok=True)
    os.chdir(DATA_DIR)
    cwd = os.getcwd()

    fdata_path = os.path.join(cwd, "file_data.csv")
    dinf_path = os.path.join(cwd, "download_info.csv")
    rtime_path = os.path.join(cwd, "response_times.csv")

    return fdata_path, dinf_path, rtime_path

def main():
        
    # create a directory to hold files uploaded to server!!
    os.makedirs(ROOT_DIR, exist_ok=True)            # exist_ok means no error raised if dir already exists
    os.chdir(ROOT_DIR)                              # move current directory to server_root
    print(f"Server root is set to: {os.getcwd()}")  # get current working directory

    # os.chdir("..")
    # print("data dir init dir: " + os.getcwd())
    
    global file_data_path
    global download_info_path
    global response_times_path

    file_data_path, download_info_path, response_times_path = init_directories()

    os.chdir("..")
    os.chdir(ROOT_DIR)

    # read file data from csv into dataframe, create a new csv if one does not exist
    try :
        # read csv into a dataframe
        file_data = pd.read_csv(file_data_path, encoding=FORMAT)
        file_data.set_index("FileID", inplace=True)

    except FileNotFoundError:
        print(f"Error: {file_data_path} was not found. Creating an empty dataframe.")
        df_cols = ["FileID", "FileName", "ServerPath", "FileSize", "UploadTime", "FileType"]
        file_data = pd.DataFrame(columns=df_cols)
        file_data.set_index("FileID", inplace=True)
        file_data.to_csv(file_data_path, encoding=FORMAT)

    except Exception as e:
        print(f"Error: {e}")

    # DOWNLOAD INFO
    try:
        download_info = pd.read_csv(download_info_path)

    except FileNotFoundError:
        print(f"Error: {download_info_path} was not found. Creating an empty dataframe.")
        didf_columns = ["FileSize", "DownloadTime"]
        download_info = pd.DataFrame(columns=didf_columns)
        download_info.to_csv(download_info_path, index=False)

    except Exception as e:
        print(f"Error for {download_info_path}: {e}")

    # RESPONSE TIMES
    try:
        response_times = pd.read_csv(response_times_path)
    except FileNotFoundError:
        print(f"Error: {response_times_path} was not found. Creating an empty dataframe.")
        rtdf_columns = ["ResponseTime", "Command"]
        response_times = pd.DataFrame(columns=rtdf_columns)
        response_times.to_csv(response_times_path, index=False)
    except Exception as e:
        print(f"Error for {response_times_path}: {e}")

    global root_path
    root_path = os.getcwd()

    print("Starting the server")
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)   # used IPV4 and TCP connection
    server.bind(ADDR)                                           # bind the address
    server.listen()                                             # start listening
    print(f"server is listening on {IP}: {PORT}")

    while True:
        conn, addr = server.accept() # accept a connection from a client
        print(f"{conn} + {addr} accepted")
        thread = threading.Thread(target = handle_client, args = (conn, addr, file_data, download_info, response_times)) # assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()
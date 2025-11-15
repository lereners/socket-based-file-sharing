import os
import socket
import threading
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

# Initiate server root
ROOT_DIR = "server_root"
if not os.path.exists(ROOT_DIR):
    os.makedirs(ROOT_DIR)

USER_DB_FILE = os.path.join(ROOT_DIR, "users.json")

# IP = "0.0.0.0"
IP = "localhost"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"

# Utility authentication functions
def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
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


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the server!".encode(FORMAT))

    # !! Would use if login authentication worked fully
    #authenticated = False

    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT)
        except Exception:
            break

        if not data:
            break

        split = data.split("@", 3)                      # split incoming data up to 2 times
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

        elif cmd == "UPLOAD":
            if len(split) < 3:  # if 3 arguments are not provided, not enough info
                conn.send("ERR@No filename/size provided.".encode(FORMAT))
            else:
                # giving arguments meaningful names!!!
                file_name = arg1
                file_size = int(arg2)
                server_folder = arg3

                server_handle_upload(conn, addr, file_name, file_size, server_folder, SIZE)
                conn.send(f"OK@File '{file_name}' received!!".encode(FORMAT))

        elif cmd == "DOWNLOAD":
            server_handle_download(conn, arg1, arg2, SIZE, FORMAT)

        elif cmd == "DELETE":
            send_data = server_handle_delete(arg1, arg2)
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DIR":
            send_data = server_handle_dir(arg1, root_path)
            conn.send(send_data.encode(FORMAT))

        elif cmd == "SUBFOLDER":
            send_data = server_handle_subfolder(arg1, arg2, root_path)
            conn.send(send_data.encode(FORMAT))

        else:
            send_data = "ERR@Invalid Command\n"
            conn.send(send_data.encode(FORMAT))

    print(f"{addr} disconnected")
    conn.close()


def main():

    print("Starting the server")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # used IPV4 and TCP connection
    server.bind(ADDR)                                           # bind the address
    server.listen()                                             # start listening
    print(f"server is listening on {IP}: {PORT}")

    global root_path
    root_path = os.getcwd()

    while True:
        conn, addr = server.accept() # accept a connection from a client
        print(f"{conn} + {addr} accepted")
        thread = threading.Thread(target=handle_client, args=(conn, addr)) # assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()
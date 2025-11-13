import os
import socket
from client_file_commands import client_handle_upload, client_handle_delete, client_handle_download
from srp import User
import pickle


# IP = "172.20.10.6"
IP = "localhost"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"


def login(client):
    """Authentication function for logging in!!"""
    # get username & password from user
    u = input("Username: ")
    p = input("Password: ")

    # start authentication!!
    usr = User(u, p)
    uname, A = usr.start_authentication()

    # send A to server
    client.send("AUTHENTICATE@".encode(FORMAT))
    client.sendall(pickle.dumps({
        "action": "login",
        "username": uname,
        "A": A
    }))
    
    response = pickle.loads(client.recv(4096))
    if "error" in response:
        print("Error:", response["error"])
        return True

    # get salt & B from server
    salt, B = response["salt"], response["B"]

    # process challenge from server & send M to server
    M = usr.process_challenge(salt, B)
    client.sendall(pickle.dumps({"M": M}))

    # get HAMK from server & verify session
    result = pickle.loads(client.recv(4096))
    if result.get("status") == "ok":
        HAMK = result["HAMK"]
        if usr.verify_session(HAMK):
            print("Login successful!!!")
        else:
            print("Session verification failed.")
    else:
        print("Authentication failed.")


def handle_response(data) -> bool:
    """Function to be passed decrypted response for printing. Returns False only upon server disconnect."""
    split = data.split("@", 1) # split just once
    cmd = split[0]
    msg = split[1] if split[1] else ""
    
    # header indicates the nature of response
    if cmd == "OK":
        print(f"{msg}")
    elif cmd == "ERR":
        print(f"{msg}")
    elif cmd == "DISCONNECTED":
        print(f"{msg}")
        return False

    return True

def process_command(cmd, client, split, arg1, arg2) -> bool:

    if cmd == "UPLOAD":
        if not arg1 or not os.path.exists(arg1): # if no path provided or path does not exist
            print("UPLOAD requires a filename.")
            return True
            
        success = client_handle_upload(arg1, arg2, client, SIZE, FORMAT)
        if not success: # unsuccessful client_handle_upload
            return True
        
    elif cmd == "AUTHENTICATE":
        choice = input("Do you want to (r)egister or (l)ogin? ").strip().lower()
        
        if choice.startswith("r"):
            client.send("AUTHENTICATE@".encode(FORMAT))
            username = input("Choose a username: ")
            password = input("Choose a password: ")
            client.sendall(pickle.dumps({
                "action": "register",
                "username": username,
                "password": password
            }))

            response = pickle.loads(client.recv(4096))
            print(response["msg"])
            return True
        else:
            if login(client) == True:
                return True
    
    elif cmd == "DOWNLOAD":
        if not arg1:
            print("DOWNLOAD requires a filename.")
            return True
        
        success = client_handle_download(client, arg1, SIZE, FORMAT)
        if not success:
            print("File download failed.")
        return True

    elif cmd == "DELETE":
        if not arg1:
            print("DELETE requires a filename.")
            return True
        
        success = client_handle_delete(client, arg1, FORMAT)
        if not success:
            return True

    elif cmd == "SUBFOLDER":
        if len(split) < 3:
            print("SUBFOLDER requires two arguments.")
            return True
            
        full_cmd = f"{cmd}@{arg1}@{arg2}"
        client.send(full_cmd.encode(FORMAT))

    elif cmd == "DIR":
        full_cmd = f"{cmd}@{arg1}"
        client.send(full_cmd.encode(FORMAT))

    elif cmd == "LOGOUT":
        client.send(cmd.encode(FORMAT))
        return False

    else: # invalid command
        full_cmd = f"{cmd}@{arg1}" if arg1 else cmd # building cmd with or without arguments
        client.send(full_cmd.encode(FORMAT))

    response = client.recv(SIZE).decode(FORMAT) # the server's response to the latest client command
    success = handle_response(response)         # if message was not successful, disconnected from server (break)
    if not success:
        return False
    else:
        return True


    
def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)

    # receive the initial server message
    data = client.recv(SIZE).decode(FORMAT)
    handle_response(data)
    tag = True
    while tag:  ### multiple communications
        
        data = input("> ")
        split = data.split(" ")                     # delimiting w/ space is not ideal, esp if user provides path w/ spaces -> file won't be found
        cmd = split[0].upper()
        arg1 = split[1] if len(split) > 1 else None # first argument, if provided
        arg2 = split[2] if len(split) > 2 else None # second argument, if provided
        tag = process_command(cmd, client, split, arg1, arg2)

    print("Disconnected from the server.")
    client.close() ## close the connection


if __name__ == "__main__":
    main()
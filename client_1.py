import os
import socket
from client_file_commands import client_handle_upload, client_handle_delete, client_handle_download

# IP = "172.20.10.6"
IP = "localhost"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

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
import os
import socket
from client_file_commands import client_handle_upload


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
    msg = split[1]
    
    # header indicates the nature of response
    if cmd == "OK":
        print(f"{msg}")
    elif cmd == "ERR":
        print(f"{msg}")
    elif cmd == "DISCONNECTED":
        print(f"{msg}")
        return False

    return True


def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)

    # receive the initial server message
    data = client.recv(SIZE).decode(FORMAT)
    handle_response(data)


    while True:  ### multiple communications
        
        data = input("> ")
        split = data.split(" ")
        cmd = split[0].upper()
        arg = split[1] if len(split) > 1 else None # only arg if provided

        if cmd == "UPLOAD":
            if not arg or not os.path.exists(arg): # if no argument OR file name invalid
                print("UPLOAD requires a valid filename")
                continue
            client_handle_upload(arg, client, SIZE, FORMAT)

        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break

        else: # invalid command
            full_cmd = f"{cmd}@{arg}" if arg else cmd # building cmd with or without arguments
            client.send(full_cmd.encode(FORMAT))

        response = client.recv(SIZE).decode(FORMAT) # the server's response to the latest client command
        success = handle_response(response)         # if message was not successful, disconnected from server (break)
        if not success:
            break
    

    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()
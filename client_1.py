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

def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)
    while True:  ### multiple communications
        data = client.recv(SIZE).decode(FORMAT)
        split = data.split("@", 1) # splitting just once
        cmd = split[0]
        msg = split[1] if len(split) > 1 else ""
        

        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "ERR":
            print(f"{msg}")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break
        
        data = input("> ") 
        split = data.split(" ")
        cmd = split[0].upper()
        arg = split[1] if len(split) > 1 else None # only arg if provided

        # list of valid commands, other than LOGOUT
        valid_commands = ["CONNECT", "TASK", "HELLO", "UPLOAD", "DOWNLOAD", "DELETE", "DIR", "SUBFOLDER"]

        # check if provided command is valid
        if cmd == "UPLOAD":
            if arg is None:
                print("UPLOAD requires a filename")
            else:
                client_handle_upload(arg, client, SIZE, FORMAT)

        # handle logout
        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break

        elif cmd == "DIR":
            client.send(cmd.encode(FORMAT))

        elif cmd in valid_commands:
            client.send(cmd.encode(FORMAT))

        # handling invalid commands
        else:
            client.send(cmd.encode(FORMAT))
      

    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()
import os
import socket
import threading
from server_file_commands import server_handle_upload, server_handle_dir

# IP = "0.0.0.0"
IP = "localhost"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"

def handle_client (conn,addr):
        
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the server".encode(FORMAT))

    while True:
        data =  conn.recv(SIZE).decode(FORMAT)
        split = data.split("@",2)
        cmd = split[0].upper()
        arg1 = split[1] if len(split) > 1 else None # info after base command
        arg2 = split[2] if len(split) > 2 else None
       
        send_data = "OK@"

        if cmd == "LOGOUT":
            break

        elif cmd == "HELLO":
            send_data += "HI!!!\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "TASK": 
            send_data += "LOGOUT from the server.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "CONNECT":                        # all these 'You input' statements are just for checking :3
            send_data += "You input 'CONNECT'.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "UPLOAD":
            if len(split) != 3:
                conn.send("ERR@No filename/size provided.".encode(FORMAT))
            else:
                file_name, file_size = arg1, arg2
                server_handle_upload(conn, addr, file_name, int(file_size), SIZE)
                conn.send(f"OK@File '{arg1}' received!!".encode(FORMAT))

        elif cmd == "DOWNLOAD":
            send_data += "You input 'DOWNLOAD'.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DELETE":
            send_data += "You input 'DELETE'.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DIR":
            send_data = server_handle_dir(os.getcwd())
            conn.send(send_data.encode(FORMAT))

        elif cmd == "SUBFOLDER":
            send_data += "You input 'SUBFOLDER'.\n"
            conn.send(send_data.encode(FORMAT))

        else:
            send_data = "ERR@Invalid Command\n"
            conn.send(send_data.encode(FORMAT))


    print(f"{addr} disconnected")
    conn.close()


def main():

    # create a directory to hold files uploaded to server!!
    ROOT_DIR = "server_root"
    os.makedirs(ROOT_DIR, exist_ok=True) # exist_ok means no error raised if dir already exists
    os.chdir(ROOT_DIR) # move current directory to server_root
    print(f"Server root is set to: {os.getcwd()}") # get current working directory

    print("Starting the server")
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) ## used IPV4 and TCP connection
    server.bind(ADDR) # bind the address
    server.listen() ## start listening
    print(f"server is listening on {IP}: {PORT}")
    while True:
        conn, addr = server.accept() ### accept a connection from a client
        print(f"{conn} + {addr} accepted")
        thread = threading.Thread(target = handle_client, args = (conn, addr)) ## assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()
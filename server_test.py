import os
import socket
import threading

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
        data = data.split("@")
        cmd = data[0]
       
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
            send_data += "You input 'UPLOAD'.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DOWNLOAD":
            send_data += "You input 'DOWNLOAD'.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DELETE":
            send_data += "You input 'DELETE'.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DIR":
            send_data += "You input 'DIR'.\n"
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
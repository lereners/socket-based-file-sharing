import os
import socket
import threading
from server_file_commands import (
    server_handle_upload,
    server_handle_dir,
    server_handle_subfolder,
    server_handle_delete,
    server_handle_download,
    AuthenticationFailed,
)
# from server_data import FileRegistry, ConnectionPool, ReadWriteLock ???
from cryptography.fernet import Fernet
import srp
import pickle

# IP = "0.0.0.0"
IP = "localhost"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the server (use SRP).".encode(FORMAT))

    # Per-connection authentication state
    authenticated = False
    username = None
    pending_username = None
    svr = None  # srp.Verifier instance for this session

    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT)
        except Exception:
            break

        if not data:
            break

        split = data.split("@", 3)
        cmd = split[0].upper()
        arg1 = split[1] if len(split) > 1 else None
        arg2 = split[2] if len(split) > 2 else None
        arg3 = split[3] if len(split) > 3 else None

        send_data = "OK@"

        # SRP authentication initialization: client -> AUTH_INIT@username@A_hex
        if cmd == "AUTH_INIT":
            if not arg1 or not arg2:
                conn.send("ERR@AUTH_INIT requires username and A".encode(FORMAT))
                continue

            uname = arg1
            try:
                A = bytes.fromhex(arg2)
            except Exception:
                conn.send("ERR@Invalid A encoding".encode(FORMAT))
                continue

            # Load server SRP data (mapping username -> (salt_hex, vkey_hex))
            if not os.path.exists("server_srp_data.pkl"):
                conn.send("ERR@Server has no SRP database".encode(FORMAT))
                continue

            with open("server_srp_data.pkl", "rb") as f:
                try:
                    db = pickle.load(f)
                except Exception:
                    conn.send("ERR@SRP DB load error".encode(FORMAT))
                    continue

            entry = db.get(uname)
            if not entry:
                conn.send("ERR@Unknown user".encode(FORMAT))
                continue

            salt_hex, vkey_hex = entry
            try:
                salt = bytes.fromhex(salt_hex)
                vkey = bytes.fromhex(vkey_hex)
            except Exception:
                conn.send("ERR@Invalid stored SRP data".encode(FORMAT))
                continue

            # create Verifier and produce challenge (s, B)
            try:
                svr = srp.Verifier(uname, salt, vkey, A)
                s, B = svr.get_challenge()
            except Exception:
                conn.send("ERR@SRP verifier error".encode(FORMAT))
                svr = None
                continue

            if s is None or B is None:
                conn.send("ERR@SRP challenge generation failed".encode(FORMAT))
                svr = None
                continue

            pending_username = uname
            # send salt and B as hex strings
            conn.send(f"AUTH_CHALLENGE@{s.hex()}@{B.hex()}".encode(FORMAT))

        # SRP proof from client: AUTH_PROOF@M_hex
        elif cmd == "AUTH_PROOF":
            if svr is None or pending_username is None:
                conn.send("ERR@No pending authentication".encode(FORMAT))
                continue

            if not arg1:
                conn.send("ERR@AUTH_PROOF requires proof M".encode(FORMAT))
                continue

            try:
                M = bytes.fromhex(arg1)
            except Exception:
                conn.send("ERR@Invalid M encoding".encode(FORMAT))
                continue

            # Verify client's proof and produce HAMK
            try:
                HAMK = svr.verify_session(M)
            except Exception:
                HAMK = None

            if HAMK is None:
                conn.send("ERR@Authentication failed".encode(FORMAT))
                svr = None
                pending_username = None
                continue

            # Success
            authenticated = True
            username = pending_username
            pending_username = None
            conn.send(f"AUTH_SUCCESS@{HAMK.hex()}".encode(FORMAT))

        elif cmd == "LOGOUT":
            conn.send("OK@Goodbye".encode(FORMAT))
            break

        # protect file ops: must be authenticated
        elif not authenticated:
            conn.send("ERR@Authenticate first (AUTH_INIT/AUTH_PROOF)".encode(FORMAT))

        elif cmd == "HELLO":
            send_data += f"HI {username}!\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "TASK":
            send_data += "LOGOUT from the server.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "CONNECT":
            send_data += f"You are connected as '{username}'.\n"
            conn.send(send_data.encode(FORMAT))

        elif cmd == "UPLOAD":
            if len(split) < 3:
                conn.send("ERR@No filename/size provided.".encode(FORMAT))
            else:
                file_name = arg1
                file_size = int(arg2)
                server_folder = arg3

                print(f"[{username}] uploading file '{file_name}'")
                server_handle_upload(conn, addr, file_name, file_size, server_folder, SIZE)
                conn.send(f"OK@File '{file_name}' received!!".encode(FORMAT))

        elif cmd == "DOWNLOAD":
            print(f"[{username}] downloading file '{arg1}'")
            server_handle_download(conn, arg1, arg2, SIZE, FORMAT)

        elif cmd == "DELETE":
            print(f"[{username}] deleting file '{arg1}'")
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

    # c`re`ate a directory to hold files uploaded to server!!
    ROOT_DIR = "server_root"
    os.makedirs(ROOT_DIR, exist_ok=True)            # exist_ok means no error raised if dir already exists
    os.chdir(ROOT_DIR)                              # move current directory to server_root
    print(f"Server root is set to: {os.getcwd()}")  # get current working directory


    global root_path
    root_path = os.getcwd()

    print("Starting the server")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # used IPV4 and TCP connection
    server.bind(ADDR)                                           # bind the address
    server.listen()                                             # start listening
    print(f"server is listening on {IP}: {PORT}")

    while True:
        conn, addr = server.accept() # accept a connection from a client
        print(f"{conn} + {addr} accepted")
        thread = threading.Thread(target=handle_client, args=(conn, addr)) # assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()
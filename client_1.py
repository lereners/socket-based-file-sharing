import os
import socket
from client_file_commands import client_handle_upload, client_handle_delete, client_handle_download
from server_file_commands import AuthenticationFailed
import srp
import pickle
import getpass


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
        
    elif cmd == "AUTHENTICATE":
        # SRP client flow:
        # 1) prompt username/password
        # 2) create srp.User and start_authentication -> (username, A)
        # 3) send AUTH_INIT@username@A_hex to server
        # 4) receive AUTH_CHALLENGE@s_hex@B_hex
        # 5) process_challenge(s, B) -> M
        # 6) send AUTH_PROOF@M_hex
        # 7) receive AUTH_SUCCESS@HAMK_hex and verify session locally

        u = input("Username: ")
        # use getpass so password isn't echoed
        p = getpass.getpass("Password: ")

        usr = srp.User(u, p)
        uname, A = usr.start_authentication()
        if A is None:
            print("SRP: failed to start authentication")
            return True

        # send username and A (hex-encoded)
        client.send(f"AUTH_INIT@{uname}@{A.hex()}".encode(FORMAT))

        # wait for server challenge
        resp = client.recv(SIZE).decode(FORMAT)
        parts = resp.split("@", 2)
        if parts[0] != "AUTH_CHALLENGE":
            print("Unexpected server response:", resp)
            return True

        s_hex = parts[1]
        B_hex = parts[2]
        try:
            s = bytes.fromhex(s_hex)
            B = bytes.fromhex(B_hex)
        except Exception:
            print("Invalid challenge encoding from server")
            return True

        # compute proof M
        M = usr.process_challenge(s, B)
        if M is None:
            print("SRP: client failed to produce proof")
            return True

        client.send(f"AUTH_PROOF@{M.hex()}".encode(FORMAT))

        # receive server verification HAMK
        resp = client.recv(SIZE).decode(FORMAT)
        parts = resp.split("@", 1)
        if parts[0] != "AUTH_SUCCESS":
            print("Authentication failed:", resp)
            return True

        hamk_hex = parts[1]
        try:
            HAMK = bytes.fromhex(hamk_hex)
        except Exception:
            print("Invalid HAMK from server")
            return True

        if usr.verify_session(HAMK):
            print("Authentication successful. Session established.")
        else:
            print("Authentication failed: server proof did not verify")
            return True
        
        # on success fall through and return True
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
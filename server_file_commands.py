import os
import socket

def server_handle_upload (conn, addr, file_name, file_size, file_path, SIZE) -> bool:
    """
        Given the connection, client address, given file, given file size, and buffer size,
        Create a new file on the server with the received data
    """
    received = 0
    file_name = os.path.basename(file_name)         # getting file name from path (is either a relative or direct path)

    if not file_path or file_path in ("None", ""):  # server path was not given
        file_path = None

    if file_path:                                   # server path was given, create the path if it does not exist
        os.makedirs(file_path, exist_ok=True)       # makedirs (not mkdir) creates all folders in a given path

    full_path = os.path.join(file_path, file_name) if file_path else file_name      # path if subfolder provided, otherwise just name

    print(f"Receiving {file_name} from {addr} ({file_size} bytes)...")              # server is ready to receive file

    try:
        with open(full_path, "wb") as file: # wb = write, binary
            while received < file_size:                             # yet to receive whole file :3c
                chunk = conn.recv(min(SIZE, file_size - received))  # receive either a full chunk or what remains

                if not chunk:   # if chunk is not received + file is not complete, connection was lost
                    print(f"Connection lost while receiving'{file_name}'")
                    return False

                # write incoming data, increment received counter
                file.write(chunk)
                received += len(chunk)

    except OSError as e:    # handle OSError, unsuccessful file transfer, return False
        print(f"File write error: {e}")
        return False

    # file successfully received! return True
    print(f"File {file_name} received successfully! Saved to '{full_path}'")
    return True
    

def server_handle_dir (dir, root_path) -> str:
    """
        Given the current working directory,
        Return the list of files and subfolders within
    """
    try:
        path = root_path if dir in (None, "None", "") else os.path.join(root_path, dir)

        dir_contents = os.listdir(path)
        file_list = "\n ".join(dir_contents) if dir_contents else f"--- Empty ---"
        return f"OK@ {file_list}"

    except Exception as e:
        return f"ERR@{str(e)}"
    
def server_handle_subfolder (action_arg, path_arg, root_path) -> str:
    """
        CREATE or DELETE a subfolder, given the action, subfolder name, and root directory path
    """

    full_path = os.path.join(root_path, path_arg)   # create full path with server's root directory + new subfolder
    action_arg = action_arg.upper()

    if action_arg == "CREATE":
        if os.path.exists(full_path):
            return f"ERR@Subfolder '{path_arg}' already exists."
        try:
            os.makedirs(full_path)
            return f"OK@Subfolder '{path_arg}' created."
        except OSError as e:
            return f"ERR@Error creating '{path_arg}': {e}"

    elif action_arg == "DELETE":
        if not os.path.exists(full_path):
            return f"ERR@Subfolder '{path_arg}' does not exist."
        try:
            os.rmdir(full_path)
            return f"OK@Subfolder '{path_arg}' deleted."
        except OSError as e:
            return f"ERR@Error deleting '{path_arg}': {e}"

    else:
        return f"ERR@'{action_arg}' is not a valid argument."
    
def server_handle_delete (file_name, file_path) -> str:
    """Given a file and its path, delete thte file from the server, if it exists"""

    if not os.path.exists(file_path):
        return f"ERR@File '{file_name}' does not exist on server."
    
    if not os.path.isfile(file_path):
        return f"ERR@'{file_name}' is not a file. To delete a subfolder, use SUBFOLDER DELETE."
    
    os.remove(file_path)
    return f"OK@File '{file_name}' removed from server."

def server_handle_download (conn, file_name, file_path, SIZE, FORMAT) -> bool:
    """
        Send a server file to a client device, given the connection, file name, file path, SIZE of packets, and encryption FORMAT.
    """

    full_path = os.path.join(file_path, file_name) if file_path != file_name else file_name     # build the full path if a file path was given, otherwise path is just the file name

    if not os.path.isfile(full_path):   # the file does not exist on the server or is not a file
        conn.send(f"ERR@'{file_name}' not found or is not a file. {full_path}".encode(FORMAT))
        return False
    
    file_size = os.path.getsize(full_path)          # get the size of the file to be sent to client
    conn.send(f"OK@{file_size}".encode(FORMAT))     # send file_size to client so it knows the expected file's size

    ack = conn.recv(SIZE).decode(FORMAT)            # await ACK from client that it received file_size
    if ack != "OK":                                 # error in receiving file_size
        return False
    
    try:
        with open(full_path, "rb") as file:
            sent = 0
            while chunk := file.read(SIZE):
                conn.sendall(chunk)
                sent += len(chunk)

    except OSError as e:
        conn.send(f"ERR@File read error: {e}".encode(FORMAT))
        return False

    print(f"File '{file_name}' ({file_size} bytes) sent successfully.")
    return True
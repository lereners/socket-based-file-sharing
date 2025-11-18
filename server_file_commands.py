import os
import pandas as pd
import time

def insert_file_data (name:str, path:str, size:int, upload_time:float, extension:str, file_data_path:str, file_data:pd.DataFrame, FORMAT) -> bool:
    """
        Insert new file metadata into file_data and append to CSV
    """

    extension = extension.lower()   # lowercase for consistency

    # supported file extensions by type
    types = {
        "Audio": ["wav", "mp3"],
        "Image": ["png", "jpg"],
        "Video": ["mp4", "mov"],
        "Text": ["md", "txt", "csv", "doc", "docx", "pdf"]
    }

    # ID prefixes listed with their type
    prefixes = {
        "Audio": "AS",
        "Image": "IS",
        "Video": "VS",
        "Text": "TS"
    }

    # check if the extension is supported + assign filetype, return False if not
    ftype = None
    for file_type, ext_list in types.items():
        if extension in ext_list:
            ftype = file_type
            break

    if ftype is None:
        print(f"Unsupported file extension: {extension}")
        return False
    
    # build the file id!!
    ID_prefix = prefixes[ftype]
    same_type = file_data[file_data["FileType"] == ftype]

    # if there are currently no files of the type, begin at 1, else increment from largest ID
    if same_type.empty:
        new_id = f"{ID_prefix}_1"
    else:
        same_type_sorted = same_type.sort_index()
        last = same_type_sorted.index[-1]
        prev_num = int(last.split("_")[1])
        new_id = f"{ID_prefix}_{prev_num + 1}"

    # prepare new data for insertion
    new_row = pd.DataFrame({
        "FileID": [new_id],
        "FileName": [name],
        "ServerPath": [path.replace("\\", "/")],
        "FileSize": [int(size)],
        "UploadTime": [float(upload_time)],
        "FileType": [ftype]
    }).set_index("FileID")

    # if the CSV is empty, it needs a header w/ column names
    need_header = not os.path.exists(file_data_path) or os.path.getsize(file_data_path) == 0

    # append (mode="a") new data to CSV
    new_row.to_csv(file_data_path, mode="a", header=need_header, encoding=FORMAT)
    file_data.loc[new_id] = new_row.iloc[0]

    return True

def insert_download_data(size:float, time:float, download_info_path:str, download_info: pd.DataFrame) -> bool:
    # inserting the size and time into the download data file
    new_row_df = pd.DataFrame({'FileSize': [size], 'DownloadTime': [time]})
    new_row_df.to_csv(download_info_path, mode="a", index=False, header=False)

    return True

def insert_response_time(time:float, command_type:str, response_times_path:str, response_times: pd.DataFrame) -> bool:
    new_row_df = pd.DataFrame({'ResponseTime': [time], 'Command' : [command_type]})
    new_row_df.to_csv(response_times_path, mode="a", index=False, header=False)

    return True
    

def server_handle_upload (conn, addr, file_name, file_size, file_path, SIZE, file_data_path, file_data, response_times, response_times_path, FORMAT, SERVER_ROOT) -> str:
    """
        Given the connection, client address, given file, given file size, and buffer size,
        Create a new file on the server with the received data
    """
    start_time = time.time()

    if not file_path or file_path in ("None", ""):  # server path was not given
        file_path = ""

    file_path = os.path.normpath(file_path) # normalize slashes
    server_path = os.path.join(SERVER_ROOT, file_path)
    os.makedirs(server_path, exist_ok=True)         # makedirs (not mkdir) creates all folders in a given path

    file_name = os.path.basename(file_name)         # getting file name from path (is either a relative or direct path)
    full_path = os.path.abspath(os.path.join(SERVER_ROOT, file_path, file_name))
    
    if os.path.commonpath([full_path, SERVER_ROOT]) != SERVER_ROOT:
        return "ERR@Invalid path traversal."

    received = 0


    if os.path.exists(full_path):
        print(f"Client upload failed: {file_name} already exists at desired upload location.")
        return(f"ERR@{file_name} already exists at desired upload loaction. Rename the upload or delete the existing file.")
    else:
        conn.send(f"OK@Ready to receive".encode(FORMAT))

    print(f"Receiving {file_name} from {addr} ({file_size} bytes)...")              # server is ready to receive file

    try:
        with open(full_path, "wb") as file: # wb = write, binary
            while received < file_size:                             # yet to receive whole file :3c
                chunk = conn.recv(min(SIZE, file_size - received))  # receive either a full chunk or what remains

                if not chunk:   # if chunk is not received + file is not complete, connection was lost
                    return(f"ERR@Connection lost while receiving'{file_name}'")

                # write incoming data, increment received counter
                file.write(chunk)
                received += len(chunk)

    except OSError as e:    # handle OSError, unsuccessful file transfer, return False
        return(f"ERR@File write error: {e}")

    end_time = time.time()
    upload_time = end_time - start_time

    insert_file_data(file_name, full_path, file_size, upload_time, file_name.split(".")[1], file_data_path, file_data, FORMAT)
    insert_response_time(upload_time, "upload", response_times_path, response_times)

    # file successfully received! return True
    return(f"OK@File {file_name} received successfully! Saved to '{full_path}'")
    

def server_handle_dir (dir, SERVER_ROOT, response_times) -> str:
    """
        Given the current working directory,
        Return the list of files and subfolders within
    """
    try:
        path = SERVER_ROOT if dir in (None, "None", "") else os.path.join(SERVER_ROOT, dir)

        dir_contents = os.listdir(path)
        file_list = "\n ".join(dir_contents) if dir_contents else f"--- Empty ---"
        return f"OK@ {file_list}"

    except Exception as e:
        return f"ERR@{str(e)}"
    
def server_handle_subfolder (action_arg, path_arg, SERVER_ROOT, response_times) -> str:
    """
        CREATE or DELETE a subfolder, given the action, subfolder name, and root directory path
    """

    full_path = os.path.join(SERVER_ROOT, path_arg)   # create full path with server's root directory + new subfolder
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
    
def server_handle_delete (file_name, file_path, file_data_path, file_data:pd.DataFrame, response_times, response_times_path, FORMAT, ROOT_DIR) -> str:
    """Given a file and its path, delete thte file from the server, if it exists"""

    server_path = os.path.join(ROOT_DIR, file_path) if file_path else ROOT_DIR
    server_path = os.path.abspath(server_path)

    if not server_path.startswith(os.path.abspath(ROOT_DIR)):
        return "ERR@Invalid path traversal."

    start_time = time.time()
    if not os.path.exists(server_path):
        return f"ERR@File '{file_name}' does not exist on server."
    
    if not os.path.isfile(server_path):
        return f"ERR@'{file_name}' is not a file. To delete a subfolder, use SUBFOLDER DELETE."
    
    # deletes the file on the server, its record in the file_data dataframe, and re-writes the csv
    os.remove(server_path)
    file_data = file_data.loc[(file_data['FileName'] != file_name) & (file_data['ServerPath'] != file_path)]
    file_data.to_csv(file_data_path, encoding=FORMAT)
    
    # ADDED
    end_time = time.time()
    delete_time = end_time - start_time
    insert_response_time(delete_time, "delete", response_times_path, response_times)

    return f"OK@File '{file_name}' removed from server."

def server_handle_download (conn, file_name, file_path, SIZE, FORMAT, download_info, download_info_path, response_times, response_times_path, ROOT_DIR) -> bool:
    """
        Send a server file to a client device, given the connection, file name, file path, SIZE of packets, and encryption FORMAT.
    """
    start_time = time.time()

    file_path = file_path or "" 

    file_name = os.path.basename(file_name or "")
    full_path = os.path.abspath(os.path.join(ROOT_DIR, file_path))

    if not full_path.startswith(os.path.abspath(ROOT_DIR)):
        conn.send(f"ERR@Invalid path traversal".encode(FORMAT))
        return False

    if not os.path.isfile(full_path):   # the file does not exist on the server or is not a file
        conn.send(f"ERR@'{file_name}' not found".encode(FORMAT))
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
    
    end_time = time.time()
    download_time = end_time - start_time

    # ADDED
    insert_download_data(file_size, download_time, download_info_path, download_info)
    insert_response_time(download_time, "download", response_times_path, response_times)

    print(f"File '{file_name}' ({file_size} bytes) sent successfully.")
    return True 
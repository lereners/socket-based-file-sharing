import os
import socket
import pandas as pd
import time

def insert_file_data (name:str, path:str, size:int, upload_time:float, extension:str, file_data_path:str, file_data:pd.DataFrame) -> bool:
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
        last = same_type.index[-1]
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
    new_row.to_csv(file_data_path, mode="a", header=need_header)
    file_data.loc[new_id] = new_row.iloc[0]

    return True

# ADDED
def insert_download_data(size:float, time:float, download_info_path:str, download_info: pd.DataFrame) -> bool:
    # inserting the size and time into the download data file
    # "FileSize", "DownloadTime"
    # new_row = {'FileSize': size, 'DownloadTime': time}
    new_row_df = pd.DataFrame({'FileSize': [size], 'DownloadTime': [time]})
    download_info = pd.concat([download_info, new_row_df], ignore_index=True)
    new_row_df.to_csv(download_info_path, mode="a", index=False, header=False)
    # download_info._append(new_row_df, ignore_index=True)

    return True

def insert_response_time(time:float, command_type:str, response_times_path:str, response_times: pd.DataFrame) -> bool:
    # new_row = {'ResponseTime': [time]}
    new_row_df = pd.DataFrame({'ResponseTime': [time], 'Command' : [command_type]})
    response_times = pd.concat([response_times, new_row_df], ignore_index=True)
    # response_times._append(new_row_df, ignore_index=True)
    new_row_df.to_csv(response_times_path, mode="a", index=False, header=False)


    return True
    

def server_handle_upload (conn, addr, file_name, file_size, file_path, SIZE, file_data_path, file_data, response_times, response_times_path) -> bool:
    """
        Given the connection, client address, given file, given file size, and buffer size,
        Create a new file on the server with the received data
    """

    start_time = time.time()

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

    end_time = time.time()
    upload_time = end_time - start_time

    insert_file_data(file_name, full_path, file_size, upload_time, file_name.split(".")[1], file_data_path, file_data)
    insert_response_time(upload_time, "upload", response_times_path, response_times)

    # file successfully received! return True
    print(f"File {file_name} received successfully! Saved to '{full_path}'")
    return True
    

def server_handle_dir (dir, root_path, response_times) -> str:
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
    
def server_handle_subfolder (action_arg, path_arg, root_path, response_times) -> str:
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
    
def server_handle_delete (file_name, file_path, response_times, response_times_path) -> str:
    """Given a file and its path, delete thte file from the server, if it exists"""

    start_time = time.time()
    if not os.path.exists(file_path):
        return f"ERR@File '{file_name}' does not exist on server."
    
    if not os.path.isfile(file_path):
        return f"ERR@'{file_name}' is not a file. To delete a subfolder, use SUBFOLDER DELETE."
    
    os.remove(file_path)
    # ADDED
    end_time = time.time()
    delete_time = end_time - start_time
    insert_response_time(delete_time, "delete", response_times_path, response_times)

    return f"OK@File '{file_name}' removed from server."

def server_handle_download (conn, file_name, file_path, SIZE, FORMAT, download_info, download_info_path, response_times, response_times_path) -> bool:
    """
        Send a server file to a client device, given the connection, file name, file path, SIZE of packets, and encryption FORMAT.
    """
    start_time = time.time()

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
    
    end_time = time.time()
    download_time = end_time - start_time

    # ADDED
    insert_download_data(file_size, download_time, download_info_path, download_info)
    insert_response_time(download_time, "download", response_times_path, response_times)

    print(f"File '{file_name}' ({file_size} bytes) sent successfully.")
    return True
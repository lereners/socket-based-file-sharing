import os

def client_handle_upload (client_path, server_path, client, SIZE, FORMAT) -> bool:
    """
        Given the name of the file to upload, the client socket, buffer size, and encryption format,
        Upload file data to the server
    """

    client_file_path = client_path          # client provides full or relative path of file to be uploaded from device
    server_folder_path = server_path or ""  # optional subfolder on server, empty string if not provided

    file_name = os.path.basename(client_file_path)  # get the file name from client path
    file_size = os.path.getsize(client_file_path)   # get the size of file to be uploaded

    if not os.path.exists(client_file_path):        # file does not exist on client
        print(f"File '{file_name}' not found.")
        return False                                # unable to locate file, return False
    
    if not os.path.isfile(client_file_path):
        print(f"'{file_name}' is not a file. Only files may be uploaded.")  # prevent from uploading non-files
        return False
    
    client.send(f"UPLOAD@{file_name}@{file_size}@{server_folder_path}".encode(FORMAT))  # provide UPLOAD command, file name, file size, and the path (if provided) to be uploaded to

    print(f"Sending '{file_name}' ({file_size} btyes) to server...")    # note start of sending

    with open(client_file_path, "rb") as file: # rb = read, binary
        sent = 0                               # for counting sent chunks
        while chunk := file.read(SIZE):        # while chunks are being read
            client.sendall(chunk)
            sent += len(chunk)

    return True # file sent successfully, return True

def client_handle_delete (client, server_path, FORMAT) -> bool:
    """Given the path to a server file, delete the file"""

    file_name = os.path.basename(server_path)
    client.send(f"DELETE@{file_name}@{server_path}".encode(FORMAT))
    return True

def client_handle_download (client, file_path, SIZE, FORMAT) -> bool:
    """Given the path to a server file, download to the client device"""

    file_name = os.path.basename(file_path) # get the file name

    client.send(f"DOWNLOAD@{file_name}@{file_path}".encode(FORMAT)) # send DOWNLOAD command with file name + path

    response = client.recv(SIZE).decode(FORMAT) # wait for server to receive the command and send an ACk with the incoming file's size
    split = response.split("@",1)

    if split[0] == "ERR":   # the server returned an error (like, file does not exist on server)
        print(f"Error: {split[1]}")
        return False

    try:
        file_size = int(split[1])           # the server returned the file size
        client.send("OK".encode(FORMAT))    # send ACK to server, client has received file size, ready to download

    except ValueError:  # received data invalid as file size
        print(f"Invalid size received: {split[1]}")
        return False

    if os.path.exists(file_name):   # if the file already exists on the client, make sure you don't
        print(f"File '{file_name}' already exists on client device. Rename or relocate the file.")
        return False
    
    received = 0    # count of received bytes to ensure full file download
    try:
        with open(file_name, "wb") as file:
            while received < file_size:
                chunk = client.recv(min(SIZE, file_size - received))

                if not chunk:
                    print(f"Connection lost while downloading '{file_name}'.")
                    return False
                
                file.write(chunk)
                received += len(chunk)

    except OSError as e:
        print(f"File write error: {e}")
        return False


    print(f"File '{file_name}' ({file_size} bytes) downloaded successfully!")
    return True
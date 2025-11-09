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
        print(f"File {file_name} not found.")
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
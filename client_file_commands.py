import os

def client_handle_upload (file_name, client, SIZE, FORMAT) -> bool:
    if not os.path.exists(file_name):
        print(f"File {file_name} not found.")
        return False
    
    file_size = os.path.getsize(file_name)
    client.send(f"UPLOAD@{file_name}@{file_size}".encode(FORMAT))
    print(f"Sending '{file_name}' ({file_size} btyes) to server...")


    with open(file_name, "rb") as file: # rb = read, binary
        sent = 0

        while chunk := file.read(SIZE): # while chunks are being read
            client.sendall(chunk)
            sent += len(chunk)

    print("Done sending!!!!")
    return True
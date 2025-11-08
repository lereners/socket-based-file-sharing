import os

def server_handle_upload (conn, addr, file_name, file_size, SIZE) -> bool:
    received = 0
    file_name = os.path.basename(file_name)
    with open(file_name, "wb") as file: # wb = write, binary
        print(f"Receiving {file_name} from {addr} ({file_size} bytes)...")

        while received < file_size:
            chunk = conn.recv(min(SIZE, file_size - received)) # receive either a full chunk or what remains
            file.write(chunk)
            received += len(chunk)

  
    print(f"File {file_name} received!!")
    return True
    

def server_handle_dir (cwd) -> str:
    try:
        dir_contents = os.listdir(cwd)
        file_list = "\n".join(dir_contents) if dir_contents else "(empty)"
        return f"OK@{file_list}"

    except Exception as e:
        return f"ERR@{str(e)}"
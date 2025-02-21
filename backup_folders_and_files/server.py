import os
import socket
import threading
import ssl
import glob
from pathlib import Path

#openssl certificates and keys generate using https://www.electricmonk.nl/log/2018/06/02/ssl-tls-client-certificate-verification-with-python-v3-4-sslcontext/
server_cert = 'server.crt'
server_key = 'server.key'
client_certs = 'client.crt'

#IP = socket.gethostbyname(socket.gethostname())
IP = '192.168.10.134'
#IP = '192.168.144.134'
PORT = 4456
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "new_backup_3"

# SSL related configuration
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile=server_cert, keyfile=server_key)
context.load_verify_locations(cafile=client_certs)

# initialize list/set of all connected client's sockets
client_sockets = set()

def tree(directory):
    result = f'+ {directory}\n'
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = '    ' * depth
        if path.is_dir():  # Check if path is a directory
            result += f'{spacer}d {path.name}\n'
        elif path.is_file():  # Check if path is a file
            result += f'{spacer}f {path.name}\n'
    return result

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the File Server.".encode(FORMAT))

    while True:
        try:
            data = conn.recv(SIZE).decode(FORMAT)
            data = data.split("@")
            cmd = data[0]

            if cmd =="LIST":
                path = Path(SERVER_DATA_PATH)
                send_data = "OK@"
                send_data += tree(path)
                conn.send(send_data.encode(FORMAT))

            if cmd == "FILES_LIST":
                files = os.listdir(SERVER_DATA_PATH)
                send_data = "OK@"

                if len(files) == 0:
                    send_data += "The server directory is empty"
                else:
                    send_data += "\n".join(f for f in files)
                    # send_data += "\n".join(f for f in file)
                conn.send(send_data.encode(FORMAT))

            # server.py
            elif cmd == "UPLOAD":
                name, text = data[1], data[2]
                filepath = os.path.join(SERVER_DATA_PATH, name)
                # os.makedirs(os.path.dirname(filepath),exist_ok=True)


        # Check the type of file and organize them into folders
                # Check the type of file and organize them into folders
                if name.endswith(('.txt', '.pdf')):
                    file_folder = os.path.join(SERVER_DATA_PATH, 'Files')
                # elif name.endswith(('.jpg', '.png', '.gif','.jpeg')):
                #     file_folder = os.path.join(SERVER_DATA_PATH, 'pictures')
                else:
                    file_folder = os.path.join(SERVER_DATA_PATH, "Other")
                    pass

                os.makedirs(file_folder, exist_ok=True)
                filepath = os.path.join(file_folder, os.path.normpath(name))

                with open(filepath, "w") as f:
                    f.write(text)

                send_data = f"OK@File uploaded successfully. Path: {filepath}"
                conn.send(send_data.encode(FORMAT))

            elif cmd == "FOLDER_RECURSIVE_UPLOAD":
                name, text = data[1], data[2]
                filepath = os.path.join(SERVER_DATA_PATH, name)
                os.makedirs(os.path.dirname(filepath),exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(text)

                send_data = "OK@Files uploaded successfully."
                conn.send(send_data.encode(FORMAT)) 

            elif cmd == "RESTORE":
                path_on_server, destination_path_on_client = data[1], data[2]
                # construct the file path on server and iterate through the folder on server
                for fn in glob.iglob(f"{path_on_server}/**", recursive=True):
                    if os.path.isfile(fn): # filter dirs
                        # fpath=fn.partition('/')
                        # print("fpath: ",fpath)
                        # filename_with_path = fpath[-1]
                        print("fn:", fn)
                        # print("filename:", filename_with_path)

                        with open(f"{fn}", "r") as f:
                            text = f.read()
                        send_data = f"RESTORE@Restoring files@{destination_path_on_client}@{fn}@{text}"
                        conn.send(send_data.encode(FORMAT))
                
                send_data = "OK@Files restored successfully."
                conn.send(send_data.encode(FORMAT)) 
            

            elif cmd == "UPLOAD_FOLDER":
                name, text = data[1], data[2]
                filepath = os.path.join(SERVER_DATA_PATH, name)
                os.makedirs(os.path.dirname(filepath),exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(text)

                send_data = "OK@File uploaded successfully."
                conn.send(send_data.encode(FORMAT)) 

            
            elif cmd == "WATCH":
                name, text = data[1], data[2]
                filepath = os.path.join(SERVER_DATA_PATH, name)
                os.makedirs(os.path.dirname(filepath),exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(text)

                send_data = "OK@File uploaded successfully."
                conn.send(send_data.encode(FORMAT))       

            elif cmd == "DELETE":
                files = os.listdir(SERVER_DATA_PATH)
                send_data = "OK@"
                filename = data[1]

                if len(files) == 0:
                    send_data += "The server directory is empty"
                else:
                    if filename in files:
                        os.remove(f"{SERVER_DATA_PATH}/{filename}")
                        send_data += "File deleted successfully."
                    else:
                        send_data += "File not found."

                conn.send(send_data.encode(FORMAT))

            elif cmd == "LOGOUT":
                break

            elif cmd == "BACKUP":
                name, text = data[1], data[2]
                filepath = os.path.join(SERVER_DATA_PATH, name)

                # Check the type of file and organize them into folders
                if name.endswith(('.txt', '.doc', '.pdf')):
                    file_folder = os.path.join(SERVER_DATA_PATH, 'files')
                elif name.endswith(('.jpg', '.png', '.gif')):
                    file_folder = os.path.join(SERVER_DATA_PATH, 'pictures')
                else:
                    file_folder = os.path.join(SERVER_DATA_PATH, 'other')

                os.makedirs(file_folder, exist_ok=True)
                filepath = os.path.join(file_folder, name)

                with open(filepath, "w") as f:
                    f.write(text)

                send_data = f"OK@File uploaded successfully. Path: {filepath}"
                conn.send(send_data.encode(FORMAT))

            elif cmd == "HELP":
                data = "OK@"
                data += "LIST: List all the subfolders and files from the server.\n"
                data += "FILES_LIST: List all the files from the server.\n"
                data += "UPLOAD <foldername>/<filename>: Upload a single file from <foldername>/<filename> to the server.\n"
                data += "FOLDER_RECURSIVE_UPLOAD <foldername>/: Upload the contents of a folder from <foldername>/ to the server.\n"
                data += "WATCH <foldername>: Watch folder with <foldername> and upload files to the server.\n"
                data += "DELETE <filename>: Delete a file with <filename> from the server.\n"
                data += "RESTORE <relative_folder_path_on_server> <destination_folder_on_client>,  source directory must be with in the working directory\n"
                data += "LOGOUT: Disconnect from the server.\n"
                data += "HELP: List all the commands."
                data += "Scheduled Backup: List all the commands."

                conn.send(data.encode(FORMAT))
            # elif cmd == "BACKUP":
            #     path = data[1]
            #     send_data = "OK@"

            #     try:
            #         files = os.listdir(path)
            #         if len(files) == 0:
            #             send_data += "The specified directory is empty"
            #         else:
            #             for file in files:
            #                 file_path = os.path.join(path, file)
            #                 with open(file_path, "r") as f:
            #                     text = f.read()
            #                 send_data += f"\nUPLOAD@{file}@{text}"
            #     except FileNotFoundError:
            #         send_data += "The specified directory does not exist."

            #     conn.send(send_data.encode(FORMAT))  

        except:
            break

    print(f"[DISCONNECTED] {addr} disconnected")
    conn.close()

def main():
    print("[STARTING] Server is starting")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server.settimeout(10)
    server.bind(ADDR)
    server.listen()
    print(f"[LISTENING] Server is listening on {IP}:{PORT}.")

    while True:
        try: 
            # while True:
                newsocket, addr = server.accept()
                print(f"[+] {addr} connected.")
                # add the new connected client to connected sockets
                conn = context.wrap_socket(newsocket, server_side=True)
                client_sockets.add(conn)
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                # make the thread daemon so it ends whenever the main thread ends
                thread.daemon = True
                thread.start()
                # thread.join() // remove or comment to be able to connect multiple clients
                print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
        except KeyboardInterrupt:
            print(f"Bye!")
            # server.shutdown(socket.SHUT_RDWR)
            # for cs in client_sockets:
            #     cs.close()
            # server.close()py
            break
        # except socket.timeout:
        #     pass
            

if __name__ == "__main__":
    main()

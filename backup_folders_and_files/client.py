import os
import socket
import schedule
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ssl
import glob

# SSL related configuration
server_sni_hostname = 'example.com'
server_cert = 'server.crt'
client_cert = 'client.crt'
client_key = 'client.key'

IP = socket.gethostbyname(socket.gethostname())
# IP = '127.0.0.1'
PORT = 4456
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024

# SSL related configuration
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=server_cert)
context.load_cert_chain(certfile=client_cert, keyfile=client_key)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client = context.wrap_socket(s, server_side=False, server_hostname=server_sni_hostname)
client.connect(ADDR)

class MyHandler(FileSystemEventHandler):
    def __init__(self,p):
        self.p=p
        # super().__init__()
    def on_created(self, event):
        if not event.is_directory:
            command = "WATCH"
            print("p: ",self.p)
            path = event.src_path
            print("path: ",path)
            if ":" in path:
                fldr = self.p.split('\\')
                print("fldr[-1]: ",fldr[-1])
                spt = path.partition(f'{fldr[-1]}\\')
                print("spt: ",spt)
                filename = spt[-1]
            else:
                fpath=path.partition('\\')
                filename = fpath[-1]
            # fpath=path.partition('\\')
            # filename = fpath[-1]
            print("path:", path)
            print("filename:", filename)
            with open(f"{path}", "r") as f:
                text = f.read()
            send_data = f"{command}@{filename}@{text}"
            client.send(send_data.encode(FORMAT))

# def upload_r_folder(path):
#     command = "UPLOAD_R_FOLDER"
#     for fn in glob.iglob(f"{path}/**", recursive=True):
#         if os.path.isfile(fn): # filter dirs
#             fpath=fn.partition('\\')
#             filename = fpath[-1]
#             print("fn:", fn)
#             print("filename:", filename)
#             with open(f"{fn}", "r") as f:
#                 text = f.read()
#             send_data = f"{command}@{filename}@{text}"
#             client.send(send_data.encode(FORMAT))
def upload_r_folder(path):
    command = "FOLDER_RECURSIVE_UPLOAD"
    if ":" in path:
        fldr = path.split('\\')
        print("fldr[-1]: ",fldr[-1])
    for fn in glob.iglob(f"{path}/**", recursive=True):
        if os.path.isfile(fn): # filter dirs
            if ":" in path:

                spt = fn.partition(f'{fldr[-1]}\\')
                print("spt: ",spt)
                filename = spt[-1]
            else:
                fpath=fn.partition('\\')
                filename = fpath[-1]
            
            print("fn:", fn)
            print("filename:", filename)
            with open(f"{fn}", "r") as f:
                text = f.read()
            send_data = f"{command}@{filename}@{text}"
            client.send(send_data.encode(FORMAT))
            # print(send_data)

        
def upload_file(path):
    # if not event.is_directory:
        command = "UPLOAD"
        # path = event.src_path
        fpath=path.partition('\\')
        filename = fpath[-1]
        print("New file created:", path)
        print("New file created:", filename)
        with open(f"{path}", "r") as f:
            text = f.read()
        send_data = f"{command}@{filename}@{text}"
        client.send(send_data.encode(FORMAT))


def backup_file(path):
    print(f"Provided path: {path}")

    # Replace forward slashes with backslashes in the path
    # path = path.replace('/', '\\')
    print(f"Formatted path: {path}")

    if os.path.isfile(path):
        print("It's a file.")
        with open(path, "rb") as f:
            text = f.read()
        filename = os.path.basename(path)
        send_data = f"UPLOAD@{filename}@{text}"
        client.send(send_data.encode(FORMAT))
    elif os.path.isdir(path):
        print("It's a folder.")
        for root, dirs, files in os.walk(path):
            for file in files:
                # file_path = os.path.join(root, file)
                # with open(file_path, "rb") as f:
                #     text = f.read()
                # filename = os.path.relpath(file_path, path)
                # send_data = f"UPLOAD@{filename}@{text}"
                # client.send(send_data.encode(FORMAT))
                command = "UPLOAD_FOLDER"
                # path = event.src_path
                fpath=path.partition('\\')
                print("fpath: \n",fpath)
                filename = fpath[-1]
                print("New file created:", path)
                print("New file created:", filename)
                with open(f"{filename}", "r") as f:
                    text = f.read()
                send_data = f"{command}@{filename}@{text}"
                client.send(send_data.encode(FORMAT))

    else:
        print("Invalid path. Please provide a valid file or folder path.")

def scheduled_backup(path):
    # Schedule backup job every hour
    schedule.every(20).seconds.do(upload_r_folder, path=path)

    # Run the scheduled jobs
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("exiting")


def restore_files_folders(dest_path,filename_with_path,text):
    filepath = os.path.join(dest_path, filename_with_path)
    os.makedirs(os.path.dirname(filepath),exist_ok=True)
    with open(filepath, "w") as f:
        f.write(text)
    print("Restored file: ",filename_with_path)

def main():
    while True:
        data = client.recv(SIZE).decode(FORMAT)
        data_return = data.split("@")
        ret_cmd = data_return[0]
        ret_msg = data_return[1]
        # if len(data_return) > 2 and cmd == "RESTORE":
        #     filename = data[2]
        #     text = data[3]
        # cmd, msg = data.split("@")

        if ret_cmd == "DISCONNECTED":
            print(f"[SERVER]: {ret_msg}")
            break
        # elif ret_cmd == "OK":
        #     print(f"{ret_msg}")
        elif ret_cmd == "RESTORE" and len(data_return) > 2:
            print(f"restoring files")
            dest_path = data_return[2]
            print("dest_path: ",dest_path)
            filename_with_path = data_return[3]
            print("filename_with_path: ",filename_with_path)
            text = data_return[4]
            print("text: ",text)
            restore_files_folders(dest_path,filename_with_path,text)

        elif ret_cmd == "OK":
            print(f"{ret_msg}")

            data = input("> ")
            data = data.split(" ", 1)  # Split only at the first space
            print("data: ",data)
            cmd = data[0].upper()

            if cmd == "HELP":
                client.send(cmd.encode(FORMAT))
            elif cmd == "LOGOUT":
                client.send(cmd.encode(FORMAT))
                break
            elif cmd == "FILES_LIST":
                client.send(cmd.encode(FORMAT))  #enhance this to print the folders aswell

            elif cmd == "LIST":
                client.send(cmd.encode(FORMAT))  #enhaned  print the folders aswell
            
            elif cmd == "RESTORE":
                # split the res_data = data[1].split(" ",1)
                res_data = data[1].split(" ",1)
                server_path = res_data[0]
                destination_path_on_client = res_data[1]
                send_data = f"{cmd}@{server_path}@{destination_path_on_client}"
                client.send(send_data.encode(FORMAT))

            elif cmd == "DELETE":
                client.send(f"{cmd}@{data[1]}".encode(FORMAT))
            elif cmd == "UPLOAD":
                path = data[1]
                backup_file(path)
            elif cmd == "FOLDER_RECURSIVE_UPLOAD":
                path = data[1]
                upload_r_folder(path)
            elif cmd == "BACKUP":
                path = input("Enter the path of the file or folder to schedule backup: ")
                scheduled_backup(path)

            elif cmd == "WATCH":
                path = data[1]
                observer = Observer()
                event_handler = MyHandler(path)
                observer.schedule(event_handler, path=f"{path}", recursive=True)
                observer.start()
                try:
                    while True:
                        pass
                except KeyboardInterrupt:
                    observer.stop()
                observer.join()

    print("Disconnected from the server.")
    client.close()

if __name__ == "__main__":
    main()


#! /usr/bin/python3.7

import socket
import os
import hashlib
import json

bufsize = 4096

class FileClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def upload_file(self, filename):
        s = self.create_socket()
        s.send(f'FileUpload {filename}'.encode('utf-8'))
        file_size = os.path.getsize(filename)
        s.send(str(file_size).encode('utf-8'))
        with open(filename, 'rb') as file_to_send:
            data = file_to_send.read(bufsize)
            while data:
                s.send(data)
                data = file_to_send.read(bufsize)
        s.close()
        print('File upload successful')

    def download_file(self, filename):
        s = self.create_socket()
        s.send(f'FileDownload {filename}'.encode('utf-8'))
        file_size = int(s.recv(1024).decode('utf-8'))
        with open(filename, 'wb') as file_to_write:
            remaining = file_size
            while remaining > 0:
                data = s.recv(min(bufsize, remaining))
                file_to_write.write(data)
                remaining -= len(data)
        s.close()
        print('File download successful')

    def list_files(self):
        s = self.create_socket()
        s.send('lls'.encode('utf-8'))
        files = s.recv(4096).decode('utf-8')
        s.close()
        return files.split(' ')

    def register_user(self, user_data):
        s = self.create_socket()
        s.send(f'Register {json.dumps(user_data)}'.encode('utf-8'))
        user_id = s.recv(1024).decode('utf-8')
        with open(f"{user_data['username']}_LNS.txt", "w") as f:
            f.write(user_id)
        s.close()
        print(f'User {user_data["username"]} registered with ID {user_id}')

    def retrieve_user(self, username):
        s = self.create_socket()
        s.send(f'Retrieve {username}'.encode('utf-8'))
        user_id = s.recv(1024).decode('utf-8')
        s.close()
        if user_id == 'User not found':
            print(f'User {username} not found')
        else:
            print(f'User ID for {username} is {user_id}')

    def sync_lns(self):
        s = self.create_socket()
        local_lns = self.get_local_lns()
        s.send(f'Sync {json.dumps(local_lns)}'.encode('utf-8'))
        updated_lns = json.loads(s.recv(4096).decode('utf-8'))
        self.update_local_lns(updated_lns)
        s.close()
        print('LNS sync successful')

    def get_local_lns(self):
        lns_files = [f for f in os.listdir() if f.endswith('_LNS.txt')]
        local_lns = {}
        for lns_file in lns_files:
            username = lns_file.replace('_LNS.txt', '')
            with open(lns_file, 'r') as f:
                user_id = f.read()
            local_lns[username] = user_id
        return local_lns

    def update_local_lns(self, lns):
        for username, user_id in lns.items():
            with open(f"{username}_LNS.txt", "w") as f:
                f.write(user_id)

    def create_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        return s

if __name__ == "__main__":
    client = FileClient('127.0.0.1', 8000)
    while True:
        command = input("Enter command (upload, download, list, register, retrieve, sync, quit): ")
        if command == 'quit':
            break
        elif command == 'upload':
            filename = input("Enter filename to upload: ")
            client.upload_file(filename)
        elif command == 'download':
            filename = input("Enter filename to download: ")
            client.download_file(filename)
        elif command == 'list':
            files = client.list_files()
            print("Files on server:", files)
        elif command == 'register':
            user_data = {
                "username": input("Enter username: "),
                "dob": input("Enter date of birth (YYYY-MM-DD): "),
                "full_name": input("Enter full name: ")
            }
            client.register_user(user_data)
        elif command == 'retrieve':
            username = input("Enter username to retrieve: ")
            client.retrieve_user(username)
        elif command == 'sync':
            client.sync_lns()

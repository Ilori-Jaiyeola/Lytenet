#! /usr/bin/python3.7

import socket
import os
import threading
import hashlib
import json
import time
from typing import List, Dict, Any
import requests

HOST = '0.0.0.0'
PORT = 8000
bufsize = 4096
BLOCKSIZE = 65536

class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.current_transactions: List[Dict[str, Any]] = []
        self.nodes = set()
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address: str):
        self.nodes.add(address)

    def new_block(self, proof: int, previous_hash: str = None) -> Dict[str, Any]:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, data: Dict[str, Any]) -> int:
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'data': data,
            'timestamp': time.time()
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def validate_chain(self, chain: List[Dict[str, Any]]) -> bool:
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self) -> bool:
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        for node in neighbours:
            response = self.request_chain(node)
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.validate_chain(chain):
                    max_length = length
                    new_chain = chain
        if new_chain:
            self.chain = new_chain
            return True
        return False

    def request_chain(self, node: str):
        response = requests.get(f'http://{node}/chain')
        return response

class FileServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.blockchain = Blockchain()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print('Server started')
        threading.Thread(target=self.listen_for_connections, daemon=True).start()

    def listen_for_connections(self):
        while True:
            conn, addr = self.server_socket.accept()
            print(f'Connected with {addr[0]}:{addr[1]}')
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self, conn):
        req_command = conn.recv(1024).decode("utf-8", errors='ignore')
        print(f'Client> {req_command}')
        command = req_command.split(' ', 1)

        if req_command == 'lls':
            files = " ".join(os.listdir(os.getcwd()))
            conn.send(files.encode('utf-8'))
        
        elif command[0] == 'FileUpload' and len(command) > 1:
            self.file_upload(conn, command[1])
        
        elif command[0] == 'FileDownload' and len(command) > 1:
            self.file_download(conn, command[1])
        
        elif command[0] == 'Register':
            user_data = json.loads(command[1])
            self.register_user(conn, user_data)
        
        elif command[0] == 'Retrieve':
            self.retrieve_user(conn, command[1])

        elif command[0] == 'Sync':
            self.sync_lns(conn, json.loads(command[1]))

        conn.close()

    def file_upload(self, conn, filename):
        file_size = int(conn.recv(1024).decode('utf-8'))
        with open(filename, 'wb') as file_to_write:
            remaining = file_size
            while remaining > 0:
                data = conn.recv(min(bufsize, remaining))
                file_to_write.write(data)
                remaining -= len(data)
        print('File upload successful')

    def file_download(self, conn, filename):
        with open(filename, 'rb') as file_to_send:
            file_size = os.path.getsize(filename)
            conn.send(str(file_size).encode('utf-8'))
            data = file_to_send.read(bufsize)
            while data:
                conn.send(data)
                data = file_to_send.read(bufsize)
        print('File download successful')

    def register_user(self, conn, user_data):
        user_id = hashlib.sha256(user_data["username"].encode()).hexdigest()
        user_data["user_id"] = user_id
        self.blockchain.new_transaction(sender="0", recipient=user_id, data=user_data)
        proof = self.blockchain.proof_of_work(self.blockchain.last_block['proof'])
        self.blockchain.new_block(proof)
        with open(f"{user_data['username']}_LNS.txt", "w") as f:
            f.write(user_id)
        conn.send(user_id.encode('utf-8'))
        print(f'User {user_data["username"]} registered with ID {user_id}')

    def retrieve_user(self, conn, username):
        try:
            with open(f"{username}_LNS.txt", "r") as f:
                user_id = f.read()
            conn.send(user_id.encode('utf-8'))
            print(f'User ID for {username} retrieved: {user_id}')
        except FileNotFoundError:
            conn.send(b'User not found')
            print(f'User ID for {username} not found')

    def sync_lns(self, conn, other_lns):
        local_lns = self.get_local_lns()
        combined_lns = {**local_lns, **other_lns}
        combined_lns = dict(list(combined_lns.items())[:1000])  # Ensure LNS has at most 1000 entries
        self.update_local_lns(combined_lns)
        conn.send(json.dumps(combined_lns).encode('utf-8'))
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

if __name__ == "__main__":
    server = FileServer(HOST, PORT)
    server.start_server()
    input("Press Enter to stop the server...\n")

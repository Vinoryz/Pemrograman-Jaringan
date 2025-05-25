from socket import *
import socket
import logging
import json
import time
import sys
from concurrent.futures import ProcessPoolExecutor

from file_protocol import FileProtocol

MAX_DATA = 10485760
fp = FileProtocol()


def handle_client_request(data):
    try:
        d = data.decode()
        hasil = fp.proses_string(d)
        hasil = hasil + "\r\n\r\n"
        return hasil.encode()
    except Exception as e:
        return json.dumps(dict(status="ERROR", data=str(e))).encode()


class Server:
    def __init__(self, ipaddress, port, max_workers):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.executor = ProcessPoolExecutor()

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)

        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning(f"connection from {client_address}")
            data = connection.recv(MAX_DATA)
            if data:
                future = self.executor.submit(handle_client_request, data)
                hasil = future.result()
                connection.sendall(hasil)
            connection.close()


def main():
    max_workers = 1  # default
    if len(sys.argv) > 1:
        try:
            max_workers = int(sys.argv[1])
        except:
            print("Gunakan: python file_server.py [jumlah_worker]")
            sys.exit(1)

    svr = Server(ipaddress='0.0.0.0', port=46666, max_workers=max_workers)
    svr.run()


if __name__ == "__main__":
    main()

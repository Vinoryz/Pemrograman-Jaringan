from socket import *
import socket
import threading
import logging
import json
import time
import sys
from time import sleep


from file_protocol import  FileProtocol
fp = FileProtocol()


class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        data_received = b""
        # it = 1
        while True:
            # Receive data in chunks
            data = self.connection.recv(1024000)
            # print(it)
            # it += 1
            if data:
                data_received += data
                # Check if the end-of-message delimiter is in the buffer
                if b"\r\n\r\n" in data_received:
                    # Decode the complete message and remove the delimiter
                    d = data_received.decode().strip()
                    # Process the complete string
                    hasil = fp.proses_string(d)
                    hasil = hasil + "\r\n\r\n"
                    self.connection.sendall(hasil.encode())
                    # Reset buffer for the next command
                    data_received = b""
            else:
                # If no data is received, the client has closed the connection
                break
        self.connection.close()

class Server(threading.Thread):
    def __init__(self,ipaddress,port):
        self.ipinfo=(ipaddress,port)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(1)
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning(f"connection from {self.client_address}")

            clt = ProcessTheClient(self.connection, self.client_address)
            clt.start()
            self.the_clients.append(clt)


def main():
    svr = Server(ipaddress='0.0.0.0',port=46666)
    svr.start()


if __name__ == "__main__":
    main()


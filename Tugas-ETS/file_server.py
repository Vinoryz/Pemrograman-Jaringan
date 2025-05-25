from socket import *
import socket
import threading
import logging
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor

from file_protocol import  FileProtocol
fp = FileProtocol()


class ProcessTheClient:
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address

    def run(self):
        try:
            while True:
                data = self.connection.recv(209715200)
                if data:
                    d = data.decode()
                    hasil = fp.proses_string(d)
                    hasil=hasil+"\r\n\r\n"
                    self.connection.sendall(hasil.encode())
                else:
                    break
            self.connection.close()
        except Exception as e:
            print(e)
        finally:
            self.connection.close()


class Server(threading.Thread):
    def __init__(self,ipaddress,port,max_workers):
        self.ipinfo=(ipaddress,port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        threading.Thread.__init__(self)

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        try:
            self.my_socket.bind(self.ipinfo)
            self.my_socket.listen(10)
            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"connection from {client_address}")

                self.executor.submit(self.handle_client, connection, client_address)
        except Exception as e:
            print(e)
        finally:
            self.executor.shutdown(wait=True)
            self.my_socket.close()

    def handle_client(self, connection, client_address):
        client_processor = ProcessTheClient(connection, client_address)
        client_processor.run()


def main():
    svr = Server(ipaddress='0.0.0.0',port=46666,max_workers=5)
    svr.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.warning("Server interrupted by user, shutting down.")
        # The server's run method's finally block will handle executor shutdown and socket closing
        sys.exit(0)


if __name__ == "__main__":
    main()


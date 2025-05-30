from socket import *
import socket
import threading
import logging
import json
import sys
from time import sleep
from concurrent.futures import ProcessPoolExecutor, TimeoutError
from file_protocol import FileProtocol

fp = FileProtocol()

# Global counters
successful_requests = 0
failed_requests = 0
counter_lock = threading.Lock()


# Function to process request in subprocess
def handle_request(data_bytes):
    try:
        print("Inside handle_request")
        d = data_bytes.decode()
        hasil_handle = fp.proses_string(d)
    except Exception as e:
        hasil_handle = json.dumps(dict(status="ERROR", data=str(e)))
    return hasil_handle + "\r\n\r\n"



class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address, pool):
        super().__init__()
        self.connection = connection
        self.address = address
        self.pool = pool
        self.running = True

    def run(self):
        global successful_requests, failed_requests
        try:
            buffer = b""
            while self.running:
                data = self.connection.recv(300000000)
                if not data:
                    break

                buffer += data
                # print(f"{buffer}\n")
                # sleep(5)

                # Only proceed if the buffer has a full message (ends with our delimiter)
                if b"\r\n\r\n" not in buffer:
                    continue

                # We extract up to the delimiter
                full_data, _, remainder = buffer.partition(b"\r\n\r\n")
                buffer = remainder  # Save any trailing data for next round

                try:
                    future = self.pool.submit(handle_request, full_data)
                    print(future.result())
                    hasil = future.result(timeout=10)
                    self.connection.sendall(hasil.encode())

                    with counter_lock:
                        successful_requests += 1
                except TimeoutError:
                    self.connection.sendall(b'{"status": "ERROR", "data": "Processing timeout"}\r\n\r\n')
                    with counter_lock:
                        failed_requests += 1
                except Exception as e:
                    self.connection.sendall(b'{"status": "ERROR", "data": "Unhandled error"}\r\n\r\n')
                    with counter_lock:
                        failed_requests += 1

        finally:
            self.connection.close()

class Server(threading.Thread):
    def __init__(self, ipaddress, port, pool):
        super().__init__()
        self.ipinfo = (ipaddress, port)
        self.pool = pool
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True

    def run(self):
        logging.warning(f"Server running at {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)
        try:
            while self.running:
                conn, addr = self.my_socket.accept()
                logging.warning(f"Connection from {addr}")
                clt = ProcessTheClient(conn, addr, self.pool)
                clt.start()
                self.the_clients.append(clt)
        except Exception as e:
            logging.warning(f"Server exception: {str(e)}")
        finally:
            self.my_socket.close()

    def stop(self):
        self.running = False
        self.my_socket.close()
        for c in self.the_clients:
            c.running = False
            c.join()


def main():
    global successful_requests, failed_requests

    pool = ProcessPoolExecutor(max_workers=10)
    server = Server(ipaddress='0.0.0.0', port=46666, pool=pool)

    try:
        server.start()
        server.join()
    except KeyboardInterrupt:
        logging.warning("KeyboardInterrupt received. Shutting down server.")
        server.stop()
        pool.shutdown(wait=True)

        with counter_lock:
            print(f"\nTotal Success: {successful_requests}")
            print(f"Total Failed : {failed_requests}")


if __name__ == "__main__":
    main()

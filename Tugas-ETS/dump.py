from socket import *
import socket
import threading
import logging
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Manager, current_process

from file_protocol import FileProtocol
fp = FileProtocol()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("server_metrics.log"), # Log to a file
                        logging.StreamHandler(sys.stdout)          # Also log to console
                    ])

# Using Manager for multiprocessing-safe counters
manager = Manager()
server_success_count_mp = manager.Value('i', 0)
server_failure_count_mp = manager.Value('i', 0)
server_lock_mp = manager.Lock()

# For multithreading
server_success_count_thread = 0
server_failure_count_thread = 0
server_lock_thread = threading.Lock()

class ProcessTheClient:
    def __init__(self, connection, address, pool_type):
        self.connection = connection
        self.address = address
        self.total_bytes_processed = 0
        self.pool_type = pool_type

    def run(self):
        global server_success_count_thread, server_failure_count_thread
        global server_success_count_mp, server_failure_count_mp, server_lock_mp

        start_time = time.time()
        client_success = False
        process_id = current_process().name if self.pool_type == "process" else threading.current_thread().name

        logging.info(f"[{process_id}] Handling connection from {self.address}")
        try:
            while True:
                data = self.connection.recv(4096)
                if data:
                    self.total_bytes_processed += len(data)
                    d = data.decode()
                    hasil = fp.proses_string(d)
                    hasil = hasil + "\r\n\r\n"
                    self.connection.sendall(hasil.encode())
                else:
                    break
            client_success = True

        except Exception as e:
            logging.error(f"[{process_id}] Error handling client {self.address}: {e}")
            client_success = False
        finally:
            self.connection.close()
            end_time = time.time()
            total_time = end_time - start_time

            if self.pool_type == "thread":
                with server_lock_thread:
                    if client_success:
                        server_success_count_thread += 1
                    else:
                        server_failure_count_thread += 1
            elif self.pool_type == "process":
                with server_lock_mp:
                    if client_success:
                        server_success_count_mp.value += 1
                    else:
                        server_failure_count_mp.value += 1

            if total_time > 0:
                throughput = self.total_bytes_processed / total_time
                logging.info(
                    f"[{process_id}] Client {self.address}: Total Time = {total_time:.4f} seconds, Throughput = {throughput:.2f} bytes/second, Bytes Processed = {self.total_bytes_processed}")
            else:
                logging.info(
                    f"[{process_id}] Client {self.address}: Total Time = {total_time:.4f} seconds (too fast for throughput calculation), Bytes Processed = {self.total_bytes_processed}")

            logging.info(f"[{process_id}] Connection from {self.address} closed.")


class Server(threading.Thread):
    def __init__(self, ipaddress, port, max_workers, pool_type="thread"):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)
        self.pool_type = pool_type

        if self.pool_type == "thread":
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            logging.warning(f"Server using ThreadPoolExecutor with {max_workers} workers")
        elif self.pool_type == "process":
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
            logging.warning(f"Server using ProcessPoolExecutor with {max_workers} workers")
        else:
            raise ValueError("Invalid pool_type. Must be 'thread' or 'process'.")

    def run(self):
        logging.warning(f"Server running at ip address {self.ipinfo} with {self.pool_type} pool")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)

        try:
            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"Connection from {client_address}")

                client_handler = ProcessTheClient(connection, client_address, self.pool_type)
                self.executor.submit(client_handler.run)
        except KeyboardInterrupt:
            logging.info("Server is shutting down...")
        finally:
            self.executor.shutdown(wait=True)
            self.my_socket.close()
            if self.pool_type == "thread":
                logging.info(f"Server shutdown complete. Server successes: {server_success_count_thread}, Server failures: {server_failure_count_thread}")
            elif self.pool_type == "process":
                logging.info(f"Server shutdown complete. Server successes: {server_success_count_mp.value}, Server failures: {server_failure_count_mp.value}")


def main():
    # Example usage:
    # To run with ThreadPoolExecutor:
    # svr = Server(ipaddress='0.0.0.0', port=46666, max_workers=5, pool_type="thread")
    # svr.start()

    # To run with ProcessPoolExecutor:
    # svr = Server(ipaddress='0.0.0.0', port=46666, max_workers=5, pool_type="process")
    # svr.start()

    # Default to thread pool for initial run
    svr = Server(ipaddress='0.0.0.0', port=46666, max_workers=10, pool_type="thread")
    svr.start()


if __name__ == "__main__":
    main()
from socket import *
import socket
import logging
import json
import time
import sys
from concurrent.futures import ProcessPoolExecutor
from file_protocol import FileProtocol
import threading
import signal

MAX_DATA = 10485760 * 100
fp = FileProtocol()

# Logging konfigurasi
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)

# Counter thread-safe
total_requests = 0
success_count = 0
fail_count = 0
counter_lock = threading.Lock()

def handle_client_request(data):
    try:
        d = data.decode()
        hasil = fp.proses_string(d)
        hasil = hasil + "\r\n\r\n"
        return hasil.encode()
    except Exception as e:
        raise Exception(f"Gagal memproses request: {e}")

class Server:
    def __init__(self, ipaddress, port, max_workers):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.running = True

    def on_worker_done(self, future, conn, client_address):
        global success_count, fail_count
        try:
            result = future.result()
            conn.sendall(result)
            with counter_lock:
                success_count += 1
            logging.info(f"✅ Worker sukses dari {client_address}")
        except Exception as e:
            error_msg = json.dumps(dict(status="ERROR", data=str(e))).encode()
            try:
                conn.sendall(error_msg)
            except:
                logging.warning("Tidak bisa mengirim pesan error ke client (mungkin sudah tertutup)")
            with counter_lock:
                fail_count += 1
            logging.error(f"❌ Worker gagal dari {client_address} - {e}")
        finally:
            conn.close()

    def run(self):
        global total_requests
        logging.info(f"🚀 Server berjalan di {self.ipinfo[0]}:{self.ipinfo[1]}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)

        # Tangani sinyal Ctrl+C untuk ringkasan
        def signal_handler(sig, frame):
            self.running = False
            logging.info("✋ Server dihentikan oleh user (Ctrl+C)")
            self.show_summary()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        while self.running:
            try:
                connection, client_address = self.my_socket.accept()
                logging.info(f"🔌 Koneksi dari {client_address}")
                data = connection.recv(MAX_DATA)
                if data:
                    with counter_lock:
                        total_requests += 1
                    future = self.executor.submit(handle_client_request, data)
                    future.add_done_callback(
                        lambda fut, conn=connection, addr=client_address: self.on_worker_done(fut, conn, addr)
                    )
                else:
                    connection.close()
            except Exception as e:
                logging.error(f"⚠️ Kesalahan di loop utama: {e}")

    def show_summary(self):
        logging.info("\n===== 📊 RINGKASAN SERVER 📊 =====")
        logging.info(f"Total request diterima : {total_requests}")
        logging.info(f"Worker berhasil         : {success_count}")
        logging.info(f"Worker gagal            : {fail_count}")
        logging.info("===================================")


def main():
    max_workers = 1
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

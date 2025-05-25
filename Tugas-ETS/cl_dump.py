import socket
import json
import base64
import logging
import time
import os
import random
import string
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Configure logging for the client
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("client_metrics.log"),  # Log to a file
                        logging.StreamHandler(sys.stdout)  # Also log to console
                    ])


class FileClient:
    def __init__(self, server_address):
        self.server_address = server_address

    def send_command(self, command_str=""):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(self.server_address)
            # logging.info(f"Connecting to {self.server_address}")
            sock.sendall(command_str.encode())
            data_received = ""
            while True:
                data = sock.recv(4096)  # Increased buffer size for efficiency
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            # Remove the trailing "\r\n\r\n" before parsing JSON
            data_received = data_received.replace("\r\n\r\n", "")
            hasil = json.loads(data_received)
            return hasil
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error: {e} - Data received: '{data_received}'")
            return {"status": "ERROR", "data": "Invalid JSON response"}
        except Exception as e:
            logging.error(f"Error during data receiving: {e}")
            return {"status": "ERROR", "data": str(e)}
        finally:
            sock.close()

    def remote_list(self):
        command_str = f"LIST"
        hasil = self.send_command(command_str)
        if (hasil and hasil.get('status') == 'OK'):
            # print("daftar file : ")
            # for nmfile in hasil['data']:
            #     print(f"- {nmfile}")
            return True
        else:
            # print("Gagal remote list")
            return False

    def remote_get(self, filename=""):
        command_str = f"GET {filename}"
        hasil = self.send_command(command_str)
        if (hasil and hasil.get('status') == 'OK'):
            namafile = hasil['data_namafile']
            isifile = base64.b64decode(hasil['data_file'])
            with open(f"downloads/{namafile}", 'wb+') as fp:
                fp.write(isifile)
            return True
        else:
            # print(f"Gagal remote get {filename}")
            return False

    def remote_upload(self, filename=""):
        try:
            with open(filename, 'rb') as f:
                contents = f.read()
                file_content = base64.b64encode(contents).decode()
        except FileNotFoundError:
            logging.error(f"File {filename} not found for upload.")
            return False
        except Exception as e:
            logging.error(f"Error reading file {filename} for upload: {e}")
            return False

        command_str = f"UPLOAD {filename} {file_content}"
        hasil = self.send_command(command_str)

        if (hasil and hasil.get('status') == 'OK'):
            # print(f"File {filename} berhasil diupload")
            return True
        else:
            # print(f"Gagal upload {filename}")
            return False


def create_dummy_file(filename, size_mb):
    """Creates a dummy file of specified size in MB."""
    size_bytes = size_mb * 1024 * 1024
    try:
        with open(filename, 'wb') as f:
            f.write(os.urandom(size_bytes))
        # logging.info(f"Created dummy file: {filename} of size {size_mb} MB")
    except Exception as e:
        logging.error(f"Error creating dummy file {filename}: {e}")


def run_client_task(client_id, server_address, operation, volume_mb):
    client = FileClient(server_address)
    start_time = time.time()
    task_success = False
    bytes_processed = 0

    local_filename = ""
    remote_filename = ""

    try:
        if operation == "download":
            remote_filename = f"dummy_{volume_mb}MB.bin"  # Assuming server has these dummy files
            if client.remote_get(remote_filename):
                task_success = True
                bytes_processed = volume_mb * 1024 * 1024
                # Clean up downloaded file
                if os.path.exists(f"downloads/{remote_filename}"):
                    os.remove(f"downloads/{remote_filename}")
            else:
                logging.error(f"Client {client_id}: Failed to download {remote_filename}")
        elif operation == "upload":
            local_filename = f"temp_upload_{client_id}_{volume_mb}MB.bin"
            create_dummy_file(local_filename, volume_mb)
            if client.remote_upload(local_filename):
                task_success = True
                bytes_processed = volume_mb * 1024 * 1024
            else:
                logging.error(f"Client {client_id}: Failed to upload {local_filename}")
        elif operation == "list":
            if client.remote_list():
                task_success = True
                bytes_processed = 0  # List operation doesn't transfer significant data
            else:
                logging.error(f"Client {client_id}: Failed to list files")
        else:
            logging.error(f"Client {client_id}: Unknown operation {operation}")
            task_success = False
    except Exception as e:
        logging.error(f"Client {client_id}: An unexpected error occurred during {operation}: {e}")
        task_success = False
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        if local_filename and os.path.exists(local_filename):
            os.remove(local_filename)  # Clean up temporary upload file

    throughput = bytes_processed / total_time if total_time > 0 else 0
    return {
        "client_id": client_id,
        "operation": operation,
        "volume_mb": volume_mb,
        "total_time": total_time,
        "throughput": throughput,
        "success": task_success,
        "bytes_processed": bytes_processed
    }


def stress_test(pool_type, operation, volume_mb, num_client_workers, server_address):
    results = []
    executor = None

    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    # Pre-create dummy files on the client side for download tests
    if operation == "download":
        dummy_filename = f"dummy_{volume_mb}MB.bin"
        if not os.path.exists(dummy_filename):  # Only create if it doesn't exist
            create_dummy_file(dummy_filename, volume_mb)

    if pool_type == "thread":
        executor = ThreadPoolExecutor(max_workers=num_client_workers)
        logging.info(
            f"Starting stress test with ThreadPoolExecutor for {operation} ({volume_mb}MB) using {num_client_workers} client workers.")
    elif pool_type == "process":
        executor = ProcessPoolExecutor(max_workers=num_client_workers)
        logging.info(
            f"Starting stress test with ProcessPoolExecutor for {operation} ({volume_mb}MB) using {num_client_workers} client workers.")
    else:
        raise ValueError("Invalid pool_type. Must be 'thread' or 'process'.")

    futures = [executor.submit(run_client_task, i, server_address, operation, volume_mb) for i in
               range(num_client_workers)]

    for future in futures:
        results.append(future.result())

    executor.shutdown(wait=True)

    # Clean up pre-created dummy files on the client side for download tests
    if operation == "download":
        dummy_filename = f"dummy_{volume_mb}MB.bin"
        if os.path.exists(dummy_filename):
            os.remove(dummy_filename)

    return results


if __name__ == '__main__':
    server_address = ('172.16.16.101', 46666)  # MAKE SURE THIS IS YOUR SERVER IP

    # Ensure the 'downloads' directory exists
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    # Example of running individual client operations
    # client_instance = FileClient(server_address)
    # client_instance.remote_list()
    # client_instance.remote_get('dummy_10MB.bin') # Make sure this file exists on the server
    # client_instance.remote_upload('client_upload_test.txt') # Make sure this file exists locally

    # Stress test parameters
    operations = ["download", "upload"]
    volumes_mb = [10, 50, 100]
    num_client_worker_pools = [1, 5, 50]
    num_server_worker_pools = [1, 5, 50]  # This needs to be configured on the server side manually for each run

    # Prepare for output
    all_results = []
    result_counter = 1

    # --- Important ---
    # Before running this client script for stress tests, you need to manually
    # start the server (`file_server.py`) with the desired `num_server_worker_pools`
    # and `pool_type` (thread or process).
    # For instance, for server thread pool with 5 workers, you'd run:
    # python file_server.py
    # and modify main() to: svr = Server(ipaddress='0.0.0.0', port=46666, max_workers=5, pool_type="thread")

    print("\n--- Starting Stress Tests ---")
    print("Please ensure your server is running with the correct configuration for each test combination.")

    # Create dummy files for server to serve for downloads
    # YOU NEED TO RUN THIS ON THE SERVER MACHINE ONCE
    # FOR VOLUME IN volumes_mb:
    #     create_dummy_file(f"files/dummy_{VOLUME}MB.bin", VOLUME)
    # This ensures the server has files to send to clients during download tests.

    for op in operations:
        for vol in volumes_mb:
            # Need to pre-create dummy files on the server for download operations
            # This part should ideally be handled on the server startup or as a setup script.
            # For this exercise, assume the server has `dummy_10MB.bin`, `dummy_50MB.bin`, `dummy_100MB.bin`
            # in its 'files/' directory. You can create them using the `create_dummy_file` function.
            # Example: create_dummy_file("files/dummy_10MB.bin", 10) on the server machine.

            for client_workers in num_client_worker_pools:
                for server_workers in num_server_worker_pools:
                    print(
                        f"\nRunning test: Op={op}, Vol={vol}MB, ClientWorkers={client_workers}, ServerWorkers={server_workers}")
                    print(f"**REMINDER: Start server with pool_type and max_workers={server_workers} for this test.**")

                    # You will need to manually start the server with the appropriate
                    # pool_type and max_workers for each iteration of `server_workers`.
                    # For example, to test with server_workers = 5 and thread pool,
                    # you'd run file_server.py with:
                    # svr = Server(ipaddress='0.0.0.0', port=46666, max_workers=5, pool_type="thread")
                    # before running this client script.

                    # Running client with ThreadPoolExecutor
                    print(f"  Testing with Client ThreadPoolExecutor...")
                    client_thread_results = stress_test(
                        pool_type="thread",
                        operation=op,
                        volume_mb=vol,
                        num_client_workers=client_workers,
                        server_address=server_address
                    )
                    client_thread_success = sum(1 for r in client_thread_results if r['success'])
                    client_thread_failure = len(client_thread_results) - client_thread_success
                    avg_time_thread = sum(r['total_time'] for r in client_thread_results) / len(
                        client_thread_results) if client_thread_results else 0
                    total_bytes_thread = sum(r['bytes_processed'] for r in client_thread_results)
                    total_time_thread_all_clients = sum(
                        r['total_time'] for r in client_thread_results)  # Sum of individual client times
                    overall_throughput_thread = total_bytes_thread / total_time_thread_all_clients if total_time_thread_all_clients > 0 else 0

                    all_results.append({
                        "Nomor": result_counter,
                        "Operasi": op,
                        "Volume": f"{vol} MB",
                        "Jumlah client worker pool": f"{client_workers} (Thread)",
                        "Jumlah server worker pool": f"{server_workers} (manual setup)",
                        "Waktu total per client": f"{avg_time_thread:.4f}",
                        "Throughput per client": f"{overall_throughput_thread:.2f}",
                        "Jumlah worker client yang sukses dan gagal": f"S: {client_thread_success}, G: {client_thread_failure}",
                        "Jumlah worker server yang sukses dan gagal": "N/A (check server logs)"
                        # Server metrics collected server-side
                    })
                    result_counter += 1

                    # Running client with ProcessPoolExecutor
                    print(f"  Testing with Client ProcessPoolExecutor...")
                    client_process_results = stress_test(
                        pool_type="process",
                        operation=op,
                        volume_mb=vol,
                        num_client_workers=client_workers,
                        server_address=server_address
                    )
                    client_process_success = sum(1 for r in client_process_results if r['success'])
                    client_process_failure = len(client_process_results) - client_process_success
                    avg_time_process = sum(r['total_time'] for r in client_process_results) / len(
                        client_process_results) if client_process_results else 0
                    total_bytes_process = sum(r['bytes_processed'] for r in client_process_results)
                    total_time_process_all_clients = sum(
                        r['total_time'] for r in client_process_results)  # Sum of individual client times
                    overall_throughput_process = total_bytes_process / total_time_process_all_clients if total_time_process_all_clients > 0 else 0

                    all_results.append({
                        "Nomor": result_counter,
                        "Operasi": op,
                        "Volume": f"{vol} MB",
                        "Jumlah client worker pool": f"{client_workers} (Process)",
                        "Jumlah server worker pool": f"{server_workers} (manual setup)",
                        "Waktu total per client": f"{avg_time_process:.4f}",
                        "Throughput per client": f"{overall_throughput_process:.2f}",
                        "Jumlah worker client yang sukses dan gagal": f"S: {client_process_success}, G: {client_process_failure}",
                        "Jumlah worker server yang sukses dan gagal": "N/A (check server logs)"
                    })
                    result_counter += 1

    # Print the results in a table format
    print("\n--- Stress Test Results ---")
    headers = all_results[0].keys() if all_results else []

    # Calculate column widths for pretty printing
    column_widths = {header: len(header) for header in headers}
    for row in all_results:
        for header, value in row.items():
            column_widths[header] = max(column_widths[header], len(str(value)))

    # Print header
    header_line = " | ".join(header.ljust(column_widths[header]) for header in headers)
    print(header_line)
    print("-+-".join("-" * column_widths[header] for header in headers))

    # Print rows
    for row in all_results:
        row_line = " | ".join(str(row[header]).ljust(column_widths[header]) for header in headers)
        print(row_line)

    print(
        "\nNote: 'Jumlah worker server yang sukses dan gagal' needs to be manually retrieved from the server's `server_metrics.log` after each server configuration run.")
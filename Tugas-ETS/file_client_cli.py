import socket
import json
import base64
import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import os

server_address = ('172.16.16.101', 46666)

def send_command(command_str=""):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    try:
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(16)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        hasil = json.loads(data_received)
        return hasil
    except Exception as e:
        logging.warning(f"Error: {str(e)}")
        return False
    finally:
        sock.close()

def remote_list():
    command_str = "LIST"
    hasil = send_command(command_str)
    if hasil['status'] == 'OK':
        print("Daftar file:")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal mendapatkan daftar file")
        return False


def remote_get(filename="", suffix=""):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)

    if hasil['status'] == 'OK':
        namafile = hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])

        if suffix:
            namafile = f"{Path(namafile).stem}_{suffix}{Path(namafile).suffix}"

        with open(namafile, 'wb+') as fp:
            fp.write(isifile)

        print(f"[Worker {suffix}] File '{namafile}' berhasil didownload")
        return True
    else:
        print(f"[Worker {suffix}] Gagal download file {filename}")
        return False


def remote_upload(filename, index):
    """Upload file ke server, hitung waktu dan throughput"""
    try:
        with open(filename, 'rb') as f:
            contents = f.read()
        file_content = base64.b64encode(contents).decode()
        filesize_MB = len(contents) / (1024 * 1024)
    except Exception as e:
        return {'worker': index, 'status': 'FAILED', 'error': str(e)}

    command_str = f"UPLOAD {Path(filename).name} {file_content}"

    start = time.perf_counter()
    hasil = send_command(command_str)
    end = time.perf_counter()

    elapsed = round(end - start, 4)
    throughput = round(filesize_MB / elapsed, 4) if elapsed > 0 else 0

    if hasil and hasil.get('status') == 'OK':
        return {
            'worker': index,
            'status': 'SUCCESS',
            'time': elapsed,
            'throughput': throughput
        }
    else:
        return {
            'worker': index,
            'status': 'FAILED',
            'time': elapsed,
            'throughput': 0,
            'error': hasil.get('data') if hasil else 'No response'
        }


def remote_delete(filename):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if hasil['status'] == 'OK':
        print(f"File {filename} berhasil dihapus")
        return True
    else:
        print(f"Gagal menghapus {filename}")
        return False


def main():
    logging.basicConfig(level=logging.WARNING)

    # Konfigurasi
    filename = 'dummy_50MB.bin'
    num_workers = 1
    command = remote_upload
    command_str = "remote_upload"

    remote_list()

    print(f"\n🔧 Melakukan {command_str}() file '{filename}' secara paralel dengan {num_workers} worker...\n")
    start_total = time.perf_counter()

    results = []
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        tasks = [executor.submit(command, filename, i+1) for i in range(num_workers)]

        for future in as_completed(tasks):
            result = future.result()
            results.append(result)
            print(f"[Worker {result['worker']}] - {result['status']} - "
                  f"{result.get('time', 0)}s - {result.get('throughput', 0)} MB/s")

    end_total = time.perf_counter()
    total_time = round(end_total - start_total, 4)

    # Statistik
    success = sum(1 for r in results if r['status'] == 'SUCCESS')
    failed = num_workers - success
    avg_time = round(sum(r.get('time', 0) for r in results) / num_workers, 4)
    throughput = round(sum(r.get('throughput', 0) for r in results), 4)

    print("\n📊 Ringkasan:")
    print(f"- Total waktu        : {total_time} detik")
    print(f"- Jumlah berhasil    : {success}")
    print(f"- Jumlah gagal       : {failed}")
    print(f"- Rata-rata waktu    : {avg_time} detik")
    print(f"- Throughput: {throughput} MB/s")

if __name__ == '__main__':
    main()

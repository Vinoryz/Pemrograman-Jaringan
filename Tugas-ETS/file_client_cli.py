import socket
import json
import base64
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

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


def remote_list(_):
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



def remote_upload(filename):
    try:
        with open(filename, 'rb') as f:
            contents = f.read()
        file_content = base64.b64encode(contents).decode()
    except:
        print(f"[Worker] Gagal membuka file {filename}")
        return False

    command_str = f"UPLOAD {Path(filename).name} {file_content}"
    hasil = send_command(command_str)
    if hasil['status'] == 'OK':
        print(f"[Worker] Berhasil upload {filename}")
        return True
    else:
        print(f"[Worker] Gagal upload {filename}")
        return False

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

    filename = 'dummy_10MB.bin'
    num_workers = 1

    remote_command_str = "remote_get"
    remote_command = remote_get

    print(f"Melakukan GET file '{filename}' sebanyak {num_workers} worker secara paralel...")
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Setiap proses akan menerima suffix unik agar nama file tidak sama
        suffixes = [f"{i + 1}" for i in range(num_workers)]
        executor.map(lambda sfx: remote_get(filename, sfx), suffixes)


if __name__ == '__main__':
    main()

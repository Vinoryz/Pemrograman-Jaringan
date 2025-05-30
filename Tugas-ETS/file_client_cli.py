import socket
import json
import base64
import logging
import os
import time
import threading

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        # ✅ Append delimiter so the server knows where the message ends
        full_command = command_str + "\r\n\r\n"
        logging.warning(f"sending message")
        sock.sendall(full_command.encode())

        data_received = ""  # empty string
        while True:
            data = sock.recv(20000000)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break

        hasil = json.loads(data_received.replace("\r\n\r\n", ""))
        logging.warning("data received from server:")
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving: {str(e)}")
        return False
    finally:
        sock.close()



def remote_list():
    command_str=f"LIST"
    hasil = send_command(command_str)
    print(hasil)
    if hasil['status']== 'OK':
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_get(filename="", index=0):
    command_str=f"GET {filename}"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        namafile= f"{index}_{hasil['data_namafile']}"  # ➕ Nama unik
        isifile = base64.b64decode(hasil['data_file'])
        with open(namafile, 'wb') as fp:
            fp.write(isifile)
        os.remove(namafile)
        return True
    else:
        print("Gagal")
        return False

def remote_upload(filename=""):
    try:
        f = open(filename,'rb')
        contents = f.read()
        file_content = base64.b64encode(contents).decode()
    except:
        return None

    command_str=f"UPLOAD {filename} {file_content}"
    hasil = send_command(command_str)

    if (hasil['status']=='OK'):
        print("File berhasil diupload")
        return True
    else:
        print("Gagal")
        return False

def remote_delete(filename=""):
    command_str=f"DELETE {filename}"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("File telah terhapus")
        return True
    else:
        print("Gagal")
        return False

if __name__=='__main__':
    server_address=('172.16.16.101',46666)
    start_time = time.time()
    # send_command("LIST")
    remote_list()
    # remote_delete('dummy_10MB.bin')

    threads = []

    for i in range(1):
        t = threading.Thread(target=remote_get, args=('dummy_50MB.bin', i))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    # remote_upload('dummy_10MB.bin')
    # remote_delete("pokijan.jpg")
    end_time = time.time()
    print(f"\nSemua thread selesai. Total waktu eksekusi: {end_time - start_time:.2f} detik")
from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()

#untuk menggunakan threadpool executor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def ProcessTheClient(connection, address):
    rcv = b""
    while True:
        try:
            data = connection.recv(32)
            if data:
                rcv += data

                if b'\r\n\r\n' in rcv:
                    header_part, body_part = rcv.split(b'\r\n\r\n', 1)

                    header_text = header_part.decode()
                    content_length = 0
                    for line in header_text.split('\r\n'):
                        if line.lower().startswith('content-length'):
                            try:
                                content_length = int(line.split(":")[1].strip())
                            except:
                                content_length = 0

                    while len(body_part) < content_length:
                        more_data = connection.recv(32)
                        if not more_data:
                            break
                        body_part += more_data

                    full_request = header_part + b'\r\n\r\n' + body_part
                    full_request_str = full_request.decode()

                    hasil = httpserver.proses(full_request_str)
                    hasil = hasil + b"\r\n\r\n"
                    connection.sendall(hasil)
                    break
            else:
                break
        except OSError as e:
            break
    connection.close()
    return

def Server():
    the_clients = []
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(('0.0.0.0', 8885))
    my_socket.listen(1)

    with ThreadPoolExecutor(20) as executor:
        while True:
            connection, client_address = my_socket.accept()
            #logging.warning("connection from {}".format(client_address))
            p = executor.submit(ProcessTheClient, connection, client_address)
            the_clients.append(p)
            #menampilkan jumlah process yang sedang aktif
            jumlah = ['x' for i in the_clients if i.running()==True]
            print(jumlah)

def main():
    Server()

if __name__=="__main__":
    main()

from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer

httpserver = HttpServer()

#untuk menggunakan processpoolexecutor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def handle_http_request(request_bytes):
	request_str = request_bytes.decode(errors='replace')
	hasil = httpserver.proses(request_str)
	return hasil + b"\r\n\r\n"


def ProcessClientInMainProcess(connection):
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
					return full_request, connection
			else:
				break
		except OSError:
			break
	return None, connection



def Server():
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	my_socket.bind(('0.0.0.0', 8889))
	my_socket.listen(1)

	with ProcessPoolExecutor(20) as executor:
		while True:
			connection, client_address = my_socket.accept()
			logging.warning(f"Connection from {client_address}")

			request_str, conn = ProcessClientInMainProcess(connection)
			if request_str is not None:

				future = executor.submit(handle_http_request, request_str)

				hasil = future.result()
				try:
					conn.sendall(hasil)
				except:
					pass
			conn.close()


def main():
	Server()

if __name__=="__main__":
	main()


from socket import *
import socket
import threading
import logging
from datetime import datetime

def request_process(request):
	response = "Unrecognized command\n"
	if request.startswith("TIME") and request.endswith("\n"):
		now = datetime.now()
		waktu = now.strftime("%d %m %Y %H:%M:%S")
		response = f"JAM {waktu}\r\n"
	elif request.startswith("QUIT") and request.endswith("\n"):
		response = "quit"
	return response

class ProcessTheClient(threading.Thread):
	def __init__(self,connection,address):
		self.connection = connection
		self.address = address
		threading.Thread.__init__(self)

	def run(self):
		while True:
			data = self.connection.recv(32)
			if data:
				request_string = data.decode()
				respond_string = request_process(request_string)
				if respond_string == "quit":
					self.connection.close()
					break
				self.connection.sendall(respond_string.encode())
			else:
				break
		self.connection.close()

class Server(threading.Thread):
	def __init__(self):
		self.the_clients = []
		self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		threading.Thread.__init__(self)

	def run(self):
		self.my_socket.bind(('0.0.0.0',45000))
		self.my_socket.listen(1)
		while True:
			self.connection, self.client_address = self.my_socket.accept()
			logging.warning(f"connection from {self.client_address}")

			clt = ProcessTheClient(self.connection, self.client_address)
			clt.start()
			self.the_clients.append(clt)


def main():
	svr = Server()
	svr.start()

if __name__=="__main__":
	main()


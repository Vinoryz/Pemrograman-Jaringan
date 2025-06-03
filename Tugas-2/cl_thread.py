import socket
import threading
import time

SERVER_HOST = '172.16.16.101'
SERVER_PORT = 45000

NUM_THREADS = 5

COMMANDS_TO_SEND = [
    "TIME\r\n",
    "SOME_OTHER_COMMAND\r\n",
    "TIME\r\n",
    "QUIT\r\n"
]

def client_thread_function(thread_id, commands):
    print(f"Thread-{thread_id}: Starting")
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print(f"Thread-{thread_id}: Connecting to {SERVER_HOST}:{SERVER_PORT}")
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"Thread-{thread_id}: Connected")

        for command in commands:
            print(f"Thread-{thread_id}: Sending: {command.strip()}")
            client_socket.sendall(command.encode())

            response = client_socket.recv(1024)
            response_str = response.decode().strip()
            print(f"Thread-{thread_id}: Received: {response_str}")

            if command.startswith("QUIT"):
                print(f"Thread-{thread_id}: QUIT command sent, closing connection.")
                break
            time.sleep(0.1)

    except socket.error as e:
        print(f"Thread-{thread_id}: Socket error: {e}")
    except Exception as e:
        print(f"Thread-{thread_id}: An error occurred: {e}")
    finally:
        if 'client_socket' in locals() and client_socket.fileno() != -1:
            client_socket.close()
        print(f"Thread-{thread_id}: Finished and connection closed")

def main_client():
    threads = []
    for i in range(NUM_THREADS):
        thread = threading.Thread(target=client_thread_function, args=(i + 1, COMMANDS_TO_SEND))
        threads.append(thread)
        thread.start()
        time.sleep(0.05)

    for thread in threads:
        thread.join()

    print("All client threads have completed.")

if __name__ == "__main__":
    main_client()
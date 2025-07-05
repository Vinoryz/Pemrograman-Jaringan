import http.client
import os

HOST = '172.16.16.101'
PORT = 8889

LOCAL_FILE = 'test.txt'
REMOTE_FILE = 'test_remote.txt'

def upload_file():
    if not os.path.exists(LOCAL_FILE):
        print(f"[ERROR] File {LOCAL_FILE} tidak ditemukan.")
        return

    with open(LOCAL_FILE, 'rb') as f:
        data = f.read()

    conn = http.client.HTTPConnection(HOST, PORT)
    headers = {
        "Content-Length": str(len(data)),
        "Content-Type": "application/octet-stream"
    }

    conn.request("POST", f"/{REMOTE_FILE}", body=data, headers=headers)
    response = conn.getresponse()
    print(f"[UPLOAD] {response.status} {response.reason}")
    print(response.read().decode())
    conn.close()

def delete_file():
    conn = http.client.HTTPConnection(HOST, PORT)
    conn.request("DELETE", f"/{REMOTE_FILE}")
    response = conn.getresponse()
    print(f"[DELETE] {response.status} {response.reason}")
    print(response.read().decode())
    conn.close()

def list_files():
    conn = http.client.HTTPConnection(HOST, PORT)
    conn.request("GET", "/list")
    response = conn.getresponse()
    print(f"[LIST] {response.status} {response.reason}")
    print(response.read().decode())
    conn.close()

if __name__ == "__main__":
    print("=== LIST FILES SEBELUM UPLOAD ===")
    list_files()

    print("\n=== UPLOAD FILE ===")
    upload_file()

    print("\n=== LIST FILES SETELAH UPLOAD ===")
    list_files()

    print("\n=== DELETE FILE ===")
    delete_file()

    print("\n=== LIST FILES SETELAH DELETE ===")
    list_files()
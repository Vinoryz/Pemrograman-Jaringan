import os
import random

def create_dummy_file_server(filename, size_mb):
    size_bytes = size_mb * 1024 * 1024
    if not os.path.exists('files'):
        os.makedirs('files')
    filepath = os.path.join('files', filename)
    try:
        with open(filepath, 'wb') as f:
            f.write(os.urandom(size_bytes))
        print(f"Created dummy file: {filepath} of size {size_mb} MB")
    except Exception as e:
        print(f"Error creating dummy file {filepath}: {e}")

volumes_mb = [10, 50, 100]
for vol in volumes_mb:
    create_dummy_file_server(f"dummy_{vol}MB.bin", vol)
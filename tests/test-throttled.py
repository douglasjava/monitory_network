import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

# Configurações do teste
URL = "http://localhost:6000/api/storage/v1/upload"
FILE_PATH = "C:/Users/Casa/Downloads/manter.jsf.pdf"
MAX_WORKERS = 10  # Tentaremos mais do que o limite de 5
FILES_TO_UPLOAD = 5  # Número total de uploads para testar concorrência
CHUNK_SIZE = 1024 * 1024  # 1 MB por chunk

def upload_file_with_chunk_timing(i):
    params = {
        "nameFile": f"PILOTO/test_file_{i}.pdf",
        "typeFile": "application/pdf",
        "description": "PILOTO",
        "source": "COST_CENTER_BH",
        "product": "MRC",
        "storageTier": "COOL"
    }

    file_size = os.path.getsize(FILE_PATH)
    chunk_times = []

    class FileWrapper:
        def __init__(self, path):
            self.f = open(path, "rb")
        def read(self, n=-1):
            if n <= 0:
                n = CHUNK_SIZE
            start = time.time()
            chunk = self.f.read(n)
            end = time.time()
            if chunk:
                duration = end - start
                chunk_times.append((len(chunk), duration))
            return chunk
        def close(self):
            self.f.close()

    files = {"file": (os.path.basename(FILE_PATH), FileWrapper(FILE_PATH), "application/pdf")}
    try:
        response = requests.post(URL, params=params, files=files)
        # Calculando taxa média por chunk
        rates = [(size / duration) / (1024*1024) for size, duration in chunk_times if duration > 0]
        avg_rate = sum(rates)/len(rates) if rates else 0
        max_rate = max(rates) if rates else 0
        min_rate = min(rates) if rates else 0

        if response.status_code == 429:
            return f"[{i}] TOO MANY REQUESTS - Avg: {avg_rate:.2f} MB/s, Max: {max_rate:.2f} MB/s, Min: {min_rate:.2f} MB/s"
        elif response.status_code == 200:
            return f"[{i}] Upload OK - Avg: {avg_rate:.2f} MB/s, Max: {max_rate:.2f} MB/s, Min: {min_rate:.2f} MB/s"
        else:
            return f"[{i}] Status {response.status_code} - Avg: {avg_rate:.2f} MB/s, Max: {max_rate:.2f} MB/s, Min: {min_rate:.2f} MB/s"
    except Exception as e:
        return f"[{i}] Exception: {e}"
    finally:
        files["file"][1].close()


# Executando uploads simultâneos
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(upload_file_with_chunk_timing, i) for i in range(FILES_TO_UPLOAD)]
    for future in as_completed(futures):
        print(future.result())

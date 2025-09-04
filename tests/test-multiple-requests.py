import requests
import concurrent.futures
import time
import statistics

URL = "http://localhost:6000/api/storage/v1/upload"
PARAMS = {
    "nameFile": "PILOTO/102_VeiculoProprioBruno.pdf",
    "typeFile": "application/pdf",
    "description": "PILOTO",
    "source": "COST_CENTER_BH",
    "product": "MRC",
    "storageTier": "COOL"
}
HEADERS = {"Accept": "application/json"}
FILE_PATH = r"C:/Users/Casa/Downloads/certidao_de-inteiro_teor_chassi-9C2KC2500PR123372 (1).pdf"


def upload_file(i):
    """Função para simular upload de um arquivo e medir tempo"""
    try:
        start = time.perf_counter()
        with open(FILE_PATH, "rb") as f:
            files = {"file": (FILE_PATH, f, "application/pdf")}
            response = requests.post(URL, params=PARAMS, headers=HEADERS, files=files)
        elapsed = time.perf_counter() - start

        return {
            "id": i,
            "status": response.status_code,
            "elapsed": elapsed,
            "ok": response.ok,
            "message": response.text[:200]
        }
    except Exception as e:
        return {
            "id": i,
            "status": "ERR",
            "elapsed": 0,
            "ok": False,
            "message": str(e)
        }


def main():
    num_requests = 10  # número de uploads concorrentes
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(upload_file, i) for i in range(num_requests)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # --- Métricas ---
    success_times = [r["elapsed"] for r in results if r["ok"]]
    success_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - success_count

    print("\n=== Resultados Individuais ===")
    for r in results:
        print(f"[Upload {r['id']}] Status: {r['status']} | Tempo: {r['elapsed']:.2f}s | Msg: {r['message']}")

    print("\n=== Métricas Gerais ===")
    print(f"Total requisições: {len(results)}")
    print(f"Sucessos: {success_count} | Falhas: {fail_count}")

    if success_times:
        print(f"Tempo médio: {statistics.mean(success_times):.2f}s")
        print(f"Tempo mínimo: {min(success_times):.2f}s")
        print(f"Tempo máximo: {max(success_times):.2f}s")
        if len(success_times) > 1:
            print(f"Desvio padrão: {statistics.stdev(success_times):.2f}s")


if __name__ == "__main__":
    main()

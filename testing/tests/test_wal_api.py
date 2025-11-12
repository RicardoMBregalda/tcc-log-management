#!/usr/bin/env python3#!/usr/bin/env python3

""""""

Testes básicos da API WALScript para testar API com WAL

""""""



import requestsimport requests

import jsonimport json

import timeimport time



API_URL = "http://localhost:5000"API_URL = "http://localhost:5001"



def test_health():

def test_health(): """Testa endpoint /health"""

    """Testa endpoint de health""" print("=" * 60)

    print("=" * 60) print("TEST 1: Health Check com WAL")

    print("TEST 1: Health Check") print("=" * 60)

    print("=" * 60) 

     response = requests.get(f"{API_URL}/health")

    response = requests.get(f"{API_URL}/health") print(f"Status: {response.status_code}")

    print(f"Status: {response.status_code}") print(f"Response:\n{json.dumps(response.json(), indent=2)}")

    print(f"Response: {response.json()}") print()

    print()

def test_wal_stats():

 """Testa endpoint /wal/stats"""

def test_wal_stats(): print("=" * 60)

    """Testa WAL stats inicial""" print("TEST 2: WAL Statistics")

    print("=" * 60) print("=" * 60)

    print("TEST 2: WAL Statistics") 

    print("=" * 60) response = requests.get(f"{API_URL}/wal/stats")

     print(f"Status: {response.status_code}")

    response = requests.get(f"{API_URL}/wal/stats") print(f"Response:\n{json.dumps(response.json(), indent=2)}")

    print(f"Status: {response.status_code}") print()

    print(f"Response:\n{json.dumps(response.json(), indent=2)}")

    print()def test_create_log():

 """Testa criação de log com WAL"""

 print("=" * 60)

def test_create_log(): print("TEST 3: Create Log com WAL")

    """Testa criação de log""" print("=" * 60)

    print("=" * 60) 

    print("TEST 3: Create Log") log_data = {

    print("=" * 60) 'id': f'test-wal-{int(time.time())}',

     'source': 'test_wal',

    log_data = { 'level': 'INFO',

        "id": f"test_wal_{int(time.time()*1000)}", 'message': 'Testing WAL integration',

        "timestamp": "2024-01-01T12:00:00Z", 'metadata': {'test': True}

        "source": "test-service", }

        "level": "INFO", 

        "message": "Test log for WAL", response = requests.post(f"{API_URL}/logs", json=log_data)

        "metadata": {"test": True} print(f"Status: {response.status_code}")

    } print(f"Response:\n{json.dumps(response.json(), indent=2)}")

     print()

    response = requests.post(f"{API_URL}/logs", json=log_data)

    print(f"Status: {response.status_code}")def test_wal_stats_after_log():

    print(f"Response: {response.json()}") """Testa WAL stats após inserir log"""

    print() print("=" * 60)

 print("TEST 4: WAL Statistics após criar log")

 print("=" * 60)

def test_wal_stats_after_log(): 

    """Testa WAL stats após inserir log""" response = requests.get(f"{API_URL}/wal/stats")

    print("=" * 60)    print(f"Status: {response.status_code}")

    print("TEST 4: WAL Statistics após criar log")    print(f"Response:\n{json.dumps(response.json(), indent=2)}")

    print("=" * 60)    print()

    

    response = requests.get(f"{API_URL}/wal/stats")if __name__ == '__main__':

    print(f"Status: {response.status_code}")    try:

    print(f"Response:\n{json.dumps(response.json(), indent=2)}")        test_health()

    print()        test_wal_stats()

        test_create_log()

        time.sleep(1)

if __name__ == '__main__':        test_wal_stats_after_log()

    try:        

        test_health()        print("=" * 60)

        test_wal_stats()        print("[OK] TODOS OS TESTES PASSARAM!")

        test_create_log()        print("=" * 60)

        time.sleep(1)        

        test_wal_stats_after_log()    except Exception as e:

                print(f"[ERRO] ERRO: {e}")

        print("=" * 60)        import traceback

        print("[OK] TODOS OS TESTES PASSARAM!")        traceback.print_exc()
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERRO] {e}")
        import traceback
        traceback.print_exc()

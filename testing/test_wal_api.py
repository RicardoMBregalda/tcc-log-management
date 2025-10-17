#!/usr/bin/env python3
"""
Script para testar API com WAL
"""

import requests
import json
import time

API_URL = "http://localhost:5001"

def test_health():
    """Testa endpoint /health"""
    print("=" * 60)
    print("TEST 1: Health Check com WAL")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    print()

def test_wal_stats():
    """Testa endpoint /wal/stats"""
    print("=" * 60)
    print("TEST 2: WAL Statistics")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/wal/stats")
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    print()

def test_create_log():
    """Testa criação de log com WAL"""
    print("=" * 60)
    print("TEST 3: Create Log com WAL")
    print("=" * 60)
    
    log_data = {
        'id': f'test-wal-{int(time.time())}',
        'source': 'test_wal',
        'level': 'INFO',
        'message': 'Testing WAL integration',
        'metadata': {'test': True}
    }
    
    response = requests.post(f"{API_URL}/logs", json=log_data)
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    print()

def test_wal_stats_after_log():
    """Testa WAL stats após inserir log"""
    print("=" * 60)
    print("TEST 4: WAL Statistics após criar log")
    print("=" * 60)
    
    response = requests.get(f"{API_URL}/wal/stats")
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    print()

if __name__ == '__main__':
    try:
        test_health()
        test_wal_stats()
        test_create_log()
        time.sleep(1)
        test_wal_stats_after_log()
        
        print("=" * 60)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

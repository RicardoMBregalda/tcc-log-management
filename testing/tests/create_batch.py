#!/usr/bin/env python3
import requests
import sys

batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 100

print(f"Criando batch com {batch_size} logs...")
r = requests.post('http://localhost:5001/merkle/batch', json={'batch_size': batch_size}, timeout=30)

result = r.json()
print(f"\n✅ Batch criado:")
print(f"   Batch ID: {result['batch_id']}")
print(f"   Merkle Root: {result['merkle_root']}")
print(f"   Número de Logs: {result['num_logs']}")
print(f"\n🔍 Para verificar: python3 verify_merkle_integrity.py {result['batch_id']}")

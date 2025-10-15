#!/usr/bin/env python3
"""
Test Script for Stacktrace Feature

Demonstrates stacktrace support in log format:
1. INFO log without stacktrace
2. WARNING log without stacktrace
3. ERROR log with stacktrace (automatic)

Usage:
    python test_stacktrace.py
"""

import requests
import json
from datetime import datetime

API_URL = "http://localhost:5001"

def create_test_logs():
    """Create test logs with and without stacktrace"""
    
    print("=" * 70)
    print("TESTE DE SUPORTE A STACKTRACE")
    print("=" * 70)
    
    # Test 1: INFO log (no stacktrace)
    print("\n1️⃣  Criando log INFO (sem stacktrace)...")
    info_log = {
        "source": "auth-service",
        "level": "INFO",
        "message": "Usuario autenticado com sucesso",
        "metadata": {
            "userId": 12345,
            "requestId": "req-abc-123"
        }
    }
    
    try:
        response = requests.post(f"{API_URL}/logs", json=info_log, timeout=10)
        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ Log INFO criado: {result['log_id']}")
            print(f"   📄 {json.dumps(info_log, indent=6)}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exceção: {e}")
    
    # Test 2: WARNING log (no stacktrace)
    print("\n2️⃣  Criando log WARNING (sem stacktrace)...")
    warning_log = {
        "source": "payment-service",
        "level": "WARNING",
        "message": "Tentativa de pagamento com cartao invalido",
        "metadata": {
            "transactionId": "TX-999",
            "amount": 150.00
        }
    }
    
    try:
        response = requests.post(f"{API_URL}/logs", json=warning_log, timeout=10)
        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ Log WARNING criado: {result['log_id']}")
            print(f"   📄 {json.dumps(warning_log, indent=6)}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exceção: {e}")
    
    # Test 3: ERROR log WITH stacktrace
    print("\n3️⃣  Criando log ERROR (COM stacktrace)...")
    error_log = {
        "source": "auth-service",
        "level": "ERROR",
        "message": "Falha ao autenticar usuario ID=12345",
        "metadata": {
            "requestId": "req-xyz-789",
            "userId": 12345,
            "attemptCount": 3
        },
        "stacktrace": 'File "/app/auth.py", line 42, in auth_user\n  raise InvalidCredentialsException("Invalid password")\nInvalidCredentialsException: Invalid password'
    }
    
    try:
        response = requests.post(f"{API_URL}/logs", json=error_log, timeout=10)
        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ Log ERROR criado: {result['log_id']}")
            print(f"   📄 Log completo:")
            print(f"   {json.dumps(error_log, indent=6)}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exceção: {e}")
    
    # Test 4: Another ERROR with different stacktrace
    print("\n4️⃣  Criando outro log ERROR (stacktrace diferente)...")
    error_log_2 = {
        "source": "database-connector",
        "level": "ERROR",
        "message": "Falha ao conectar no banco de dados",
        "metadata": {
            "host": "db.example.com",
            "port": 5432,
            "database": "production"
        },
        "stacktrace": 'File "/app/db/connector.py", line 156, in connect\n  conn = psycopg2.connect(dsn)\npsycopg2.OperationalError: could not connect to server'
    }
    
    try:
        response = requests.post(f"{API_URL}/logs", json=error_log_2, timeout=10)
        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ Log ERROR criado: {result['log_id']}")
            print(f"   📄 Log completo:")
            print(f"   {json.dumps(error_log_2, indent=6)}")
        else:
            print(f"   ❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exceção: {e}")
    
    print("\n" + "=" * 70)
    print("✅ TESTE CONCLUÍDO!")
    print("=" * 70)
    print("\n📋 RESUMO:")
    print("   - Campo 'stacktrace' é OPCIONAL")
    print("   - Deve ser incluído automaticamente em logs ERROR")
    print("   - Formato segue padrão Python (File, line, function)")
    print("   - Logs INFO/WARNING não precisam de stacktrace")
    print("\n💾 Armazenamento:")
    print("   - MongoDB: Campo 'stacktrace' opcional no documento")
    print("   - PostgreSQL: Coluna stacktrace TEXT NULL")
    print("   - Fabric: Campo Stacktrace no struct Log (omitempty)")
    print("\n🔍 Para verificar os logs criados:")
    print(f"   curl {API_URL}/logs")
    print()


if __name__ == "__main__":
    create_test_logs()

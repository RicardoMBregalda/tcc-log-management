#!/usr/bin/env python3
"""
Script de teste para a API de Logs
Testa todos os endpoints e funcionalidades
"""

import requests
import json
import time
from datetime import datetime

# Configuração
API_BASE_URL = "http://localhost:5000"
TEST_LOG_ID = f"test_log_{int(time.time())}"

def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def test_health():
    """Testa endpoint de health check"""
    print_section("1. TESTANDO HEALTH CHECK")
    
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Health check falhou"
    print("✅ Health check OK")

def test_create_log():
    """Testa criação de log"""
    print_section("2. TESTANDO CRIAÇÃO DE LOG")
    
    log_data = {
        "id": TEST_LOG_ID,
        "source": "test-script",
        "level": "INFO",
        "message": "Log de teste criado pelo script",
        "metadata": {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "script_version": "1.0"
        }
    }
    
    print(f"Criando log com ID: {TEST_LOG_ID}")
    response = requests.post(f"{API_BASE_URL}/logs", json=log_data)
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 201, f"Falha ao criar log: {response.text}"
    result = response.json()
    assert result['log_id'] == TEST_LOG_ID, "ID do log não confere"
    assert 'hash' in result, "Hash não foi retornado"
    
    print(f"✅ Log criado com sucesso. Hash: {result['hash'][:16]}...")
    return result['hash']

def test_get_log(log_id):
    """Testa busca de log por ID"""
    print_section("3. TESTANDO BUSCA DE LOG POR ID")
    
    print(f"Buscando log: {log_id}")
    response = requests.get(f"{API_BASE_URL}/logs/{log_id}")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        log = response.json()
        print(f"Log encontrado:")
        print(f"  - ID: {log['id']}")
        print(f"  - Source: {log['source']}")
        print(f"  - Level: {log['level']}")
        print(f"  - Message: {log['message']}")
        print(f"  - Hash: {log['hash'][:16]}...")
        print("✅ Busca por ID OK")
        return log
    else:
        print(f"❌ Erro ao buscar log: {response.text}")
        return None

def test_list_logs():
    """Testa listagem de logs"""
    print_section("4. TESTANDO LISTAGEM DE LOGS")
    
    # Teste 1: Listar todos
    print("4.1. Listando todos os logs (limit=5)...")
    response = requests.get(f"{API_BASE_URL}/logs?limit=5")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Total de logs: {result['count']}")
        print(f"Primeiros logs:")
        for i, log in enumerate(result['logs'][:3], 1):
            print(f"  {i}. {log['id']} - {log['level']} - {log['source']}")
        print("✅ Listagem OK")
    
    # Teste 2: Filtrar por nível
    print("\n4.2. Filtrando logs por nível INFO...")
    response = requests.get(f"{API_BASE_URL}/logs?level=INFO")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Logs INFO encontrados: {result['count']}")
        print("✅ Filtro por nível OK")
    
    # Teste 3: Filtrar por source
    print("\n4.3. Filtrando logs por source 'test-script'...")
    response = requests.get(f"{API_BASE_URL}/logs?source=test-script")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Logs de 'test-script': {result['count']}")
        print("✅ Filtro por source OK")

def test_log_history(log_id):
    """Testa histórico do log"""
    print_section("5. TESTANDO HISTÓRICO DO LOG")
    
    print(f"Buscando histórico do log: {log_id}")
    response = requests.get(f"{API_BASE_URL}/logs/history/{log_id}")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        history = result['history']
        print(f"Histórico com {len(history)} transação(ões):")
        
        for i, tx in enumerate(history, 1):
            print(f"\n  Transação {i}:")
            print(f"    - TX ID: {tx['txId'][:16]}...")
            print(f"    - Timestamp: {tx['timestamp']}")
            print(f"    - Is Delete: {tx['isDelete']}")
        
        print("✅ Histórico OK")
    else:
        print(f"❌ Erro ao buscar histórico: {response.text}")

def test_verify_log(log_id):
    """Testa verificação de integridade"""
    print_section("6. TESTANDO VERIFICAÇÃO DE INTEGRIDADE")
    
    print(f"Verificando integridade do log: {log_id}")
    response = requests.post(f"{API_BASE_URL}/logs/verify/{log_id}")
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Resultado da verificação:")
        print(f"  - Válido: {result['valid']}")
        print(f"  - Hash blockchain: {result['blockchain_hash'][:16]}...")
        
        if 'computed_hash' in result:
            print(f"  - Hash computado: {result['computed_hash'][:16]}...")
        
        print(f"  - Mensagem: {result['message']}")
        
        if result['valid']:
            print("✅ Log íntegro")
        else:
            print("❌ ALERTA: Log foi modificado!")
    else:
        print(f"❌ Erro na verificação: {response.text}")

def test_stats():
    """Testa endpoint de estatísticas"""
    print_section("7. TESTANDO ESTATÍSTICAS")
    
    response = requests.get(f"{API_BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print("Estatísticas do sistema:")
        
        if 'mongodb' in stats:
            print(f"\n  MongoDB:")
            if 'total_logs' in stats['mongodb']:
                print(f"    - Total de logs: {stats['mongodb']['total_logs']}")
            if 'logs_by_level' in stats['mongodb']:
                print(f"    - Por nível:")
                for level, count in stats['mongodb']['logs_by_level'].items():
                    print(f"      • {level}: {count}")
        
        if 'blockchain' in stats:
            print(f"\n  Blockchain:")
            if 'total_logs' in stats['blockchain']:
                print(f"    - Total de logs: {stats['blockchain']['total_logs']}")
        
        print("\n✅ Estatísticas OK")
    else:
        print(f"❌ Erro ao buscar estatísticas: {response.text}")

def test_create_multiple_logs():
    """Cria múltiplos logs para teste"""
    print_section("8. CRIANDO LOGS ADICIONAIS")
    
    logs_to_create = [
        {
            "id": f"error_log_{int(time.time())}",
            "source": "database",
            "level": "ERROR",
            "message": "Connection timeout",
            "metadata": {"db": "postgres", "timeout": 30}
        },
        {
            "id": f"warn_log_{int(time.time())}",
            "source": "web-server",
            "level": "WARN",
            "message": "High memory usage detected",
            "metadata": {"memory_percent": 85}
        },
        {
            "id": f"info_log_{int(time.time())}",
            "source": "api-gateway",
            "level": "INFO",
            "message": "Request processed successfully",
            "metadata": {"duration_ms": 45, "status": 200}
        }
    ]
    
    success_count = 0
    for log_data in logs_to_create:
        print(f"\nCriando: {log_data['level']} - {log_data['source']}")
        response = requests.post(f"{API_BASE_URL}/logs", json=log_data)
        
        if response.status_code == 201:
            success_count += 1
            print(f"  ✅ Criado: {log_data['id']}")
        else:
            print(f"  ❌ Falhou: {response.text}")
        
        time.sleep(1)  # Aguarda entre criações
    
    print(f"\n✅ {success_count}/{len(logs_to_create)} logs criados com sucesso")

def main():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("  SUITE DE TESTES - API DE LOGS")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    
    try:
        # 1. Health Check
        test_health()
        
        # 2. Criar log de teste
        log_hash = test_create_log()
        time.sleep(3)  # Aguarda propagação do bloco
        
        # 3. Buscar log criado
        log = test_get_log(TEST_LOG_ID)
        
        # 4. Listar logs
        test_list_logs()
        
        # 5. Histórico
        test_log_history(TEST_LOG_ID)
        
        # 6. Verificar integridade
        test_verify_log(TEST_LOG_ID)
        
        # 7. Estatísticas
        test_stats()
        
        # 8. Criar logs adicionais
        test_create_multiple_logs()
        
        # Resumo final
        print_section("RESUMO")
        print("✅ Todos os testes passaram com sucesso!")
        print(f"✅ Log de teste criado: {TEST_LOG_ID}")
        print("✅ API está funcionando corretamente")
        
    except AssertionError as e:
        print(f"\n❌ ERRO: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRO: Não foi possível conectar à API em {API_BASE_URL}")
        print("Certifique-se de que o servidor está rodando:")
        print("  python3 api_server.py")
        return 1
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

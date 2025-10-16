#!/usr/bin/env python3
"""
Configurações Centralizadas - TCC Log Management

Este módulo centraliza todas as configurações do projeto,
facilitando manutenção e evitando duplicação de código.
"""

import os
from typing import Dict


# ==================== API HÍBRIDA (MongoDB + Fabric) ====================
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', '5001'))
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# Timeouts
API_TIMEOUT = 30  # segundos
API_LONG_TIMEOUT = 120  # para operações longas (batches grandes)


# ==================== POSTGRESQL ====================
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
POSTGRES_DB = os.getenv('POSTGRES_DB', 'logdb')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'loguser')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'logpass')

# Connection Pool Settings
POSTGRES_MIN_CONN = 5
POSTGRES_MAX_CONN = 20


# ==================== MONGODB ====================
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', '27017'))
MONGO_URL = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
MONGO_DB = 'logdb'
MONGO_COLLECTION = 'logs'

# Connection Pool Settings
MONGO_MIN_POOL_SIZE = 10
MONGO_MAX_POOL_SIZE = 100
MONGO_MAX_IDLE_TIME_MS = 45000
MONGO_SERVER_SELECTION_TIMEOUT_MS = 5000


# ==================== REDIS ====================
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = 0

# Cache Settings
REDIS_DEFAULT_TTL = 300  # 5 minutos
REDIS_LONG_TTL = 3600    # 1 hora


# ==================== HYPERLEDGER FABRIC ====================
FABRIC_API_URL = os.getenv('FABRIC_API_URL', 'http://localhost:3000')
FABRIC_CHANNEL = os.getenv('FABRIC_CHANNEL', 'logchannel')
FABRIC_CHAINCODE = os.getenv('FABRIC_CHAINCODE', 'logchaincode')

# Thread Pool Settings
FABRIC_SYNC_MAX_WORKERS = 20

# HTTP Session Pool
HTTP_POOL_CONNECTIONS = 50
HTTP_POOL_MAXSIZE = 100
HTTP_MAX_RETRIES = 1


# ==================== FLASK API ====================
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5001'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'


# ==================== MERKLE TREE AUTO-BATCHING ====================
AUTO_BATCH_ENABLED = os.getenv('AUTO_BATCH_ENABLED', 'True').lower() == 'true'
AUTO_BATCH_SIZE = int(os.getenv('AUTO_BATCH_SIZE', '50'))
AUTO_BATCH_INTERVAL = int(os.getenv('AUTO_BATCH_INTERVAL', '30'))  # segundos
BATCH_EXECUTOR_MAX_WORKERS = 2


# ==================== TESTES DE PERFORMANCE ====================

# Cenários de Teste (S1-S9)
TEST_SCENARIOS: Dict[str, Dict] = {
    'S1': {'volume': 10000, 'rate': 100, 'description': 'Baixo Volume + Baixa Taxa'},
    'S2': {'volume': 10000, 'rate': 1000, 'description': 'Baixo Volume + Média Taxa'},
    'S3': {'volume': 10000, 'rate': 10000, 'description': 'Baixo Volume + Alta Taxa'},
    'S4': {'volume': 100000, 'rate': 100, 'description': 'Médio Volume + Baixa Taxa'},
    'S5': {'volume': 100000, 'rate': 1000, 'description': 'Médio Volume + Média Taxa'},
    'S6': {'volume': 100000, 'rate': 10000, 'description': 'Médio Volume + Alta Taxa'},
    'S7': {'volume': 1000000, 'rate': 100, 'description': 'Alto Volume + Baixa Taxa'},
    'S8': {'volume': 1000000, 'rate': 1000, 'description': 'Alto Volume + Média Taxa'},
    'S9': {'volume': 1000000, 'rate': 10000, 'description': 'Alto Volume + Alta Taxa'},
}

# Configurações de Teste
DEFAULT_BATCH_SIZE = 100
MONITORING_INTERVAL = 1.0  # segundos

# Thread Pool para testes
TEST_MAX_WORKERS = 50


# ==================== LOGGING ====================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


# ==================== DIRETÓRIOS ====================
RESULTS_DIR = 'results'
SCRIPTS_DIR = 'scripts'


# ==================== HTTP SESSION ====================
HTTP_POOL_CONNECTIONS = 50
HTTP_POOL_MAXSIZE = 100
HTTP_MAX_RETRIES = 1


# ==================== FUNÇÕES AUXILIARES ====================

def get_postgres_connection_string() -> str:
    """Retorna string de conexão PostgreSQL"""
    return f"host={POSTGRES_HOST} port={POSTGRES_PORT} dbname={POSTGRES_DB} " \
           f"user={POSTGRES_USER} password={POSTGRES_PASSWORD}"


def get_test_scenario(scenario_id: str) -> Dict:
    """
    Retorna configuração de um cenário de teste
    
    Args:
        scenario_id: ID do cenário (S1-S9)
        
    Returns:
        Dicionário com volume, rate e description
        
    Raises:
        KeyError: Se o cenário não existir
    """
    if scenario_id not in TEST_SCENARIOS:
        raise KeyError(f"Cenário {scenario_id} não encontrado. "
                      f"Cenários disponíveis: {', '.join(TEST_SCENARIOS.keys())}")
    return TEST_SCENARIOS[scenario_id]


def validate_scenario_id(scenario_id: str) -> bool:
    """Valida se um ID de cenário é válido"""
    return scenario_id in TEST_SCENARIOS


# ==================== VALIDAÇÃO ====================

def validate_config() -> bool:
    """
    Valida configurações essenciais
    
    Returns:
        True se todas as configurações estão válidas
    """
    errors = []
    
    # Valida portas
    if not (1 <= API_PORT <= 65535):
        errors.append(f"API_PORT inválida: {API_PORT}")
    if not (1 <= POSTGRES_PORT <= 65535):
        errors.append(f"POSTGRES_PORT inválida: {POSTGRES_PORT}")
    if not (1 <= MONGO_PORT <= 65535):
        errors.append(f"MONGO_PORT inválida: {MONGO_PORT}")
    if not (1 <= REDIS_PORT <= 65535):
        errors.append(f"REDIS_PORT inválida: {REDIS_PORT}")
    
    # Valida timeouts
    if API_TIMEOUT <= 0:
        errors.append(f"API_TIMEOUT deve ser maior que 0")
    
    if errors:
        print("❌ Erros de configuração:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True


if __name__ == "__main__":
    """Testa configurações quando executado diretamente"""
    print("="*70)
    print("CONFIGURAÇÕES DO PROJETO".center(70))
    print("="*70)
    
    print(f"\n📡 API Híbrida:")
    print(f"   URL: {API_BASE_URL}")
    print(f"   Timeout: {API_TIMEOUT}s")
    
    print(f"\n🐘 PostgreSQL:")
    print(f"   Host: {POSTGRES_HOST}:{POSTGRES_PORT}")
    print(f"   Database: {POSTGRES_DB}")
    print(f"   User: {POSTGRES_USER}")
    print(f"   Pool: {POSTGRES_MIN_CONN}-{POSTGRES_MAX_CONN} conexões")
    
    print(f"\n🍃 MongoDB:")
    print(f"   URL: {MONGO_URL}")
    print(f"   Database: {MONGO_DB}")
    print(f"   Collection: {MONGO_COLLECTION}")
    print(f"   Pool: {MONGO_MIN_POOL_SIZE}-{MONGO_MAX_POOL_SIZE} conexões")
    
    print(f"\n📦 Redis:")
    print(f"   Host: {REDIS_HOST}:{REDIS_PORT}")
    print(f"   TTL padrão: {REDIS_DEFAULT_TTL}s")
    
    print(f"\n⛓️  Hyperledger Fabric:")
    print(f"   API: {FABRIC_API_URL}")
    print(f"   Channel: {FABRIC_CHANNEL}")
    print(f"   Chaincode: {FABRIC_CHAINCODE}")
    
    print(f"\n🧪 Cenários de Teste:")
    for scenario_id, config in TEST_SCENARIOS.items():
        print(f"   {scenario_id}: {config['volume']:,} logs @ {config['rate']:,} logs/s")
    
    print(f"\n✅ Validação:")
    if validate_config():
        print("   Todas as configurações estão válidas!")
    else:
        print("   Existem erros de configuração!")

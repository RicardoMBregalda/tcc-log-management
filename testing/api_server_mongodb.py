#!/usr/bin/env python3
"""
API Server - MongoDB + Fabric (Híbrido)

Arquitetura:
- MongoDB: Armazenamento rápido NoSQL
- Fabric: Blockchain para imutabilidade
- Redis: Cache para consultas
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import requests
import time
from redis_cache import get_from_cache, set_in_cache, invalidate_cache
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import hashlib

app = Flask(__name__)

# Configurações
FABRIC_API_URL = "http://localhost:3000"
MONGO_URL = "mongodb://localhost:27017/"
MONGO_DB = "logdb"
MONGO_COLLECTION = "logs"

# MongoDB Connection (Connection Pooling automático no PyMongo)
try:
    mongo_client = MongoClient(
        MONGO_URL,
        maxPoolSize=50,
        minPoolSize=5,
        maxIdleTimeMS=30000,
        serverSelectionTimeoutMS=5000
    )
    # Testa conexão
    mongo_client.admin.command('ping')
    db = mongo_client[MONGO_DB]
    logs_collection = db[MONGO_COLLECTION]
    sync_control_collection = db['sync_control']
    
    # Cria índices para performance
    logs_collection.create_index([("id", ASCENDING)], unique=True)
    logs_collection.create_index([("timestamp", ASCENDING)])
    logs_collection.create_index([("source", ASCENDING)])
    logs_collection.create_index([("level", ASCENDING)])
    sync_control_collection.create_index([("log_id", ASCENDING)], unique=True)
    
    print("✅ MongoDB conectado com sucesso!")
    print(f"   - Database: {MONGO_DB}")
    print(f"   - Collection: {MONGO_COLLECTION}")
    print(f"   - Pool: 5-50 conexões")
    
except ConnectionFailure as e:
    print(f"❌ Erro ao conectar no MongoDB: {e}")
    exit(1)

# HTTP Session Pooling (OTIMIZAÇÃO 2)
http_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=20,
    pool_maxsize=50,
    max_retries=1
)
http_session.mount('http://', adapter)
http_session.mount('https://', adapter)

print("\n✅ Otimizações Aplicadas:")
print("  1. MongoDB Connection Pool (5-50 conexões)")
print("  2. HTTP Session Pool (20 conexões, 50 max)")
print("  3. Timeout reduzido: 5s (antes 30s)")
print("  4. Redis Cache integrado\n")


def send_to_fabric(log_data, timeout=5):
    """
    Envia log para Fabric com timeout reduzido (OTIMIZAÇÃO 3)
    
    Antes: timeout=30s
    Depois: timeout=5s
    """
    try:
        payload = {
            'channelName': 'logchannel',
            'chaincodeName': 'logchaincode',
            'function': 'CreateLog',
            'args': [
                log_data['id'],
                log_data['hash'],
                log_data['timestamp'],
                log_data['source'],
                log_data['level'],
                log_data['message'],
                json.dumps(log_data.get('metadata', {}))
            ]
        }

        # Usa session com pooling ao invés de requests.post direto
        response = http_session.post(
            f"{FABRIC_API_URL}/invoke",
            json=payload,
            timeout=timeout  # Reduzido de 30 para 5
        )

        if response.status_code == 200:
            result = response.json()
            return True, result.get('transactionId', 'unknown')
        else:
            return False, f"Fabric error: {response.status_code}"

    except requests.Timeout:
        return False, "Fabric timeout (5s)"
    except Exception as e:
        return False, f"Fabric error: {str(e)}"


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'database': 'mongodb', 'blockchain': 'fabric'}), 200


@app.route('/logs', methods=['POST'])
def create_log():
    """
    Cria novo log - MongoDB + Fabric Híbrido
    
    Otimizações:
    - Connection pool MongoDB
    - Session HTTP reutilizável
    - Timeout 5s (não 30s)
    - Hash para integridade
    """
    data = request.json

    # Validação
    required_fields = ['source', 'level', 'message']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Gera ID, timestamp e hash
    log_id = f"{data['source']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Gera hash do conteúdo para integridade
    content = f"{log_id}{timestamp}{data['source']}{data['level']}{data['message']}"
    log_hash = hashlib.sha256(content.encode()).hexdigest()

    try:
        # Documento MongoDB
        log_doc = {
            'id': log_id,
            'hash': log_hash,
            'timestamp': timestamp,
            'source': data['source'],
            'level': data['level'],
            'message': data['message'],
            'metadata': data.get('metadata', {}),
            'created_at': datetime.utcnow()
        }

        # Insere no MongoDB
        logs_collection.insert_one(log_doc)

        # Tenta sincronizar com Fabric (com timeout curto)
        log_data = {
            'id': log_id,
            'hash': log_hash,
            'timestamp': timestamp,
            'source': data['source'],
            'level': data['level'],
            'message': data['message'],
            'metadata': data.get('metadata', {})
        }

        fabric_success, fabric_result = send_to_fabric(log_data, timeout=5)

        # Atualiza status de sincronização
        if fabric_success:
            sync_control_collection.insert_one({
                'log_id': log_id,
                'sync_status': 'synced',
                'fabric_tx_id': fabric_result,
                'synced_at': datetime.utcnow()
            })
        else:
            sync_control_collection.insert_one({
                'log_id': log_id,
                'sync_status': 'failed',
                'error': fabric_result,
                'synced_at': datetime.utcnow()
            })

        # Invalida cache
        invalidate_cache('logs_list')

        return jsonify({
            'id': log_id,
            'hash': log_hash,
            'status': 'success',
            'fabric_synced': fabric_success,
            'fabric_result': fabric_result
        }), 201

    except DuplicateKeyError:
        return jsonify({'error': 'Log ID already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Lista logs com filtros e cache
    
    Parâmetros:
    - source: filtra por fonte
    - level: filtra por nível
    - limit: limite de resultados (default 100)
    - offset: paginação
    """
    # Parâmetros
    source = request.args.get('source')
    level = request.args.get('level')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    # Chave de cache
    cache_key = f"logs_list_{source}_{level}_{limit}_{offset}"
    
    # Tenta cache (OTIMIZAÇÃO 4)
    cached = get_from_cache(cache_key)
    if cached:
        return jsonify({
            'logs': cached,
            'cached': True,
            'count': len(cached)
        }), 200

    try:
        # Query MongoDB
        query = {}
        if source:
            query['source'] = source
        if level:
            query['level'] = level

        # Busca com projeção (não retorna _id do MongoDB)
        logs = list(logs_collection.find(
            query,
            {'_id': 0}  # Exclui _id do MongoDB
        ).sort('timestamp', -1).skip(offset).limit(limit))

        # Converte datetime para string
        for log in logs:
            if isinstance(log.get('created_at'), datetime):
                log['created_at'] = log['created_at'].isoformat()

        # Salva no cache
        set_in_cache(cache_key, logs)

        return jsonify({
            'logs': logs,
            'cached': False,
            'count': len(logs)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logs/<log_id>', methods=['GET'])
def get_log_by_id(log_id):
    """
    Busca log específico por ID com cache
    """
    # Tenta cache primeiro
    cache_key = f"log_{log_id}"
    cached = get_from_cache(cache_key)
    if cached:
        return jsonify({
            'log': cached,
            'cached': True
        }), 200

    try:
        # Busca no MongoDB
        log = logs_collection.find_one({'id': log_id}, {'_id': 0})
        
        if not log:
            return jsonify({'error': 'Log not found'}), 404

        # Converte datetime
        if isinstance(log.get('created_at'), datetime):
            log['created_at'] = log['created_at'].isoformat()

        # Busca status de sincronização
        sync_status = sync_control_collection.find_one({'log_id': log_id}, {'_id': 0})
        if sync_status:
            if isinstance(sync_status.get('synced_at'), datetime):
                sync_status['synced_at'] = sync_status['synced_at'].isoformat()
            log['sync_status'] = sync_status

        # Salva no cache
        set_in_cache(cache_key, log)

        return jsonify({
            'log': log,
            'cached': False
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Estatísticas do sistema
    """
    try:
        total_logs = logs_collection.count_documents({})
        synced_logs = sync_control_collection.count_documents({'sync_status': 'synced'})
        failed_logs = sync_control_collection.count_documents({'sync_status': 'failed'})

        # Logs por nível
        pipeline = [
            {'$group': {'_id': '$level', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        logs_by_level = list(logs_collection.aggregate(pipeline))

        return jsonify({
            'total_logs': total_logs,
            'synced_logs': synced_logs,
            'failed_logs': failed_logs,
            'sync_rate': f"{(synced_logs/total_logs*100):.1f}%" if total_logs > 0 else "0%",
            'logs_by_level': logs_by_level
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 API Server - MongoDB + Fabric Híbrido")
    print("="*60)
    print("📊 Arquitetura:")
    print("  - MongoDB: Dados rápidos (NoSQL)")
    print("  - Fabric: Blockchain (imutabilidade)")
    print("  - Redis: Cache (performance)")
    print("\n🔧 Otimizações:")
    print("  ✅ Connection Pooling MongoDB (5-50)")
    print("  ✅ HTTP Session Pooling (20-50)")
    print("  ✅ Timeout reduzido (5s)")
    print("  ✅ Cache Redis (5min TTL)")
    print("  ✅ Índices MongoDB otimizados")
    print("\n🌐 Endpoints:")
    print("  GET  /health")
    print("  POST /logs")
    print("  GET  /logs")
    print("  GET  /logs/<id>")
    print("  GET  /stats")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)

#!/usr/bin/env python3
"""
API REST para gerenciamento de logs com Hyperledger Fabric e MongoDB
Implementa endpoints para criar, consultar e listar logs
"""

import os
import json
import hashlib
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilita CORS para aceitar requisições de diferentes origens

# --- Configuração da Conexão com o MongoDB ---
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', '27017'))

try:
    mongo_client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/", serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    db = mongo_client.tcc_logdb
    log_collection = db.logs
    print(f"Conexão com MongoDB estabelecida: {MONGO_HOST}:{MONGO_PORT}")
except ConnectionFailure as e:
    print(f"Erro de conexão com MongoDB: {e}")
    print("Servidor iniciará sem MongoDB - apenas operações Fabric estarão disponíveis")
    mongo_client = None
    log_collection = None


# --- Utilitários ---
def generate_log_hash(log_data):
    """Gera hash SHA256 do log para registro na blockchain"""
    log_str = json.dumps(log_data, sort_keys=True)
    return hashlib.sha256(log_str.encode()).hexdigest()


def invoke_fabric_chaincode(function, args):
    """
    Executa uma função do chaincode através do container CLI
    """
    args_json = json.dumps(args)
    chaincode_args = f'{{"function":"{function}","Args":{args_json}}}'
    
    command = [
        "docker", "exec", "cli",
        "peer", "chaincode", "invoke",
        "-o", "orderer.example.com:7050",
        "--ordererTLSHostnameOverride", "orderer.example.com",
        "--tls", 
        "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
        "-C", "logchannel",
        "-n", "logchaincode",
        "-c", chaincode_args
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        
        if result.returncode == 0 and ("Chaincode invoke successful" in output or "status:200" in output):
            return True, output
        else:
            return False, output
    except subprocess.TimeoutExpired:
        return False, "Timeout ao invocar chaincode"
    except Exception as e:
        return False, str(e)


def query_fabric_chaincode(function, args):
    """
    Consulta o chaincode (operação read-only)
    """
    args_json = json.dumps(args)
    chaincode_args = f'{{"function":"{function}","Args":{args_json}}}'
    
    command = [
        "docker", "exec", "cli",
        "peer", "chaincode", "query",
        "-C", "logchannel",
        "-n", "logchaincode",
        "-c", chaincode_args
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout ao consultar chaincode"
    except Exception as e:
        return False, str(e)


# --- Health Check ---
@app.route('/health', methods=['GET'])
def health_check():
    """Verifica saúde da API e dependências"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "mongodb": "connected" if log_collection is not None else "disconnected",
            "fabric": "unknown"
        }
    }
    
    try:
        success, _ = query_fabric_chaincode("LogExists", ["test"])
        health["services"]["fabric"] = "connected" if success else "error"
    except:
        health["services"]["fabric"] = "error"
    
    return jsonify(health), 200


# --- Endpoints de Logs ---
@app.route('/logs', methods=['POST'])
def create_log():
    data = request.get_json()
    
    required_fields = ['id', 'source', 'level', 'message']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Campo obrigatório ausente: {field}"}), 400
    
    log_id = data['id']
    if 'timestamp' in data:
        timestamp = data['timestamp']
        if not timestamp.endswith('Z') and '+' not in timestamp and timestamp.count(':') == 2:
            timestamp += 'Z'
    else:
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    source = data['source']
    level = data['level']
    message = data['message']
    metadata = json.dumps(data.get('metadata', {}))
    
    log_hash = generate_log_hash(data)
    
    success, fabric_output = invoke_fabric_chaincode(
        "CreateLog",
        [log_id, log_hash, timestamp, source, level, message, metadata]
    )
    
    if not success:
        return jsonify({
            "error": "Falha ao registrar log na blockchain",
            "details": fabric_output
        }), 500
    
    if log_collection is not None:
        try:
            log_entry = {
                "_id": log_id,
                "hash": log_hash,
                "timestamp": timestamp,
                "source": source,
                "level": level,
                "message": message,
                "metadata": data.get('metadata', {}),
                "created_at": datetime.now(),
                "blockchain_synced": True
            }
            log_collection.insert_one(log_entry)
        except Exception as e:
            print(f"Log registrado na blockchain mas falhou no MongoDB: {e}")
    
    return jsonify({
        "status": "success",
        "message": "Log criado com sucesso",
        "log_id": log_id,
        "hash": log_hash
    }), 201


@app.route('/logs/<log_id>', methods=['GET'])
def get_log(log_id):
    success, output = query_fabric_chaincode("QueryLog", [log_id])
    
    if not success:
        return jsonify({"error": "Log não encontrado na blockchain"}), 404
    
    try:
        log_data = json.loads(output)
        
        if log_collection is not None:
            mongo_data = log_collection.find_one({"_id": log_id})
            if mongo_data:
                mongo_data.pop('_id', None)
                log_data['mongo_metadata'] = mongo_data
        
        return jsonify(log_data), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Erro ao decodificar resposta da blockchain"}), 500


@app.route('/logs', methods=['GET'])
def list_logs():
    source = request.args.get('source') or request.args.get('souce')
    level = request.args.get('level')
    limit = int(request.args.get('limit', 100))
    
    print(f"GET /logs - Parâmetros: source={source}, level={level}, limit={limit}")
    
    if level:
        print(f"Buscando logs por nível: {level}")
        success, output = query_fabric_chaincode("QueryLogsByLevel", [level])
    elif source:
        print(f"Buscando logs por source: {source}")
        success, output = query_fabric_chaincode("QueryLogsBySource", [source])
    else:
        print("Buscando todos os logs")
        success, output = query_fabric_chaincode("GetAllLogs", [])
    
    if not success:
        error_msg = f"Erro ao buscar logs: {output}"
        print(error_msg)
        return jsonify({"error": "Erro ao buscar logs", "details": output}), 500
    
    try:
        logs = json.loads(output)
        if not logs:
            logs = []
        if isinstance(logs, list) and len(logs) > limit:
            logs = logs[:limit]
        
        log_count = len(logs) if isinstance(logs, list) else 1
        print(f"Retornando {log_count} logs")
        
        return jsonify({
            "count": log_count,
            "logs": logs,
            "filters": {
                "source": source,
                "level": level,
                "limit": limit
            }
        }), 200
    except json.JSONDecodeError as e:
        error_msg = f"Erro ao decodificar resposta: {str(e)}"
        print(error_msg)
        return jsonify({"error": "Erro ao decodificar resposta", "details": str(e)}), 500


@app.route('/logs/history/<log_id>', methods=['GET'])
def get_log_history(log_id):
    success, output = query_fabric_chaincode("GetLogHistory", [log_id])
    
    if not success:
        return jsonify({"error": "Erro ao buscar histórico", "details": output}), 404
    
    try:
        history = json.loads(output)
        return jsonify({
            "log_id": log_id,
            "history": history
        }), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Erro ao decodificar histórico"}), 500


@app.route('/logs/verify/<log_id>', methods=['POST'])
def verify_log(log_id):
    success, output = query_fabric_chaincode("QueryLog", [log_id])
    
    if not success:
        return jsonify({"error": "Log não encontrado"}), 404
    
    try:
        blockchain_log = json.loads(output)
        blockchain_hash = blockchain_log.get('hash')
        
        if log_collection is not None:
            mongo_log = log_collection.find_one({"_id": log_id})
            if mongo_log:
                mongo_log.pop('_id', None)
                mongo_log.pop('created_at', None)
                mongo_log.pop('blockchain_synced', None)
                
                computed_hash = generate_log_hash(mongo_log)
                is_valid = (computed_hash == blockchain_hash)
                
                return jsonify({
                    "log_id": log_id,
                    "valid": is_valid,
                    "blockchain_hash": blockchain_hash,
                    "computed_hash": computed_hash,
                    "message": "Log íntegro" if is_valid else "ALERTA: Log foi modificado!"
                }), 200
        
        return jsonify({
            "log_id": log_id,
            "blockchain_hash": blockchain_hash,
            "message": "Hash verificado na blockchain (MongoDB não disponível)"
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({"error": "Erro ao processar log"}), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    stats = {
        "timestamp": datetime.now().isoformat()
    }
    
    if log_collection is not None:
        try:
            stats["mongodb"] = {
                "total_logs": log_collection.count_documents({}),
                "logs_by_level": {}
            }
            pipeline = [{"$group": {"_id": "$level", "count": {"$sum": 1}}}]
            for doc in log_collection.aggregate(pipeline):
                stats["mongodb"]["logs_by_level"][doc["_id"]] = doc["count"]
        except Exception as e:
            stats["mongodb"] = {"error": str(e)}
    
    try:
        success, output = query_fabric_chaincode("GetAllLogs", [])
        if success:
            logs = json.loads(output)
            stats["blockchain"] = {
                "total_logs": len(logs) if isinstance(logs, list) else 0
            }
    except:
        stats["blockchain"] = {"error": "Erro ao consultar blockchain"}
    
    return jsonify(stats), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint não encontrado"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Erro interno do servidor"}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("API de Logs - Hyperledger Fabric + MongoDB")
    print("=" * 50)
    print(f"Servidor: http://0.0.0.0:5000")
    print(f"MongoDB: {MONGO_HOST}:{MONGO_PORT}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

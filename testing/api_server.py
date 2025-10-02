import os
import subprocess
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

app = Flask(__name__)

# --- Configuração da Conexão com o MongoDB ---
try:
    mongo_client = MongoClient("mongodb://localhost:27017/")
    # A linha abaixo força a conexão e gera um erro se o mongo não estiver de pé
    mongo_client.admin.command('ping') 
    db = mongo_client.tcc_logdb
    log_collection = db.logs
    print("✅ Conexão com o MongoDB estabelecida com sucesso.")
except ConnectionFailure as e:
    print(f"❌ Erro de conexão com o MongoDB: {e}")
    # Se não conseguir conectar ao Mongo, não há sentido em continuar.
    exit(1)


# --- Ponte para o Hyperledger Fabric ---
# Usamos o container 'cli' como um proxy para interagir com a rede.
# Esta é uma abordagem prática para um PoC/TCC quando não há um SDK oficial mantido.
def invoke_fabric_chaincode(log_id, log_hash):
    """
    Executa o comando 'peer chaincode invoke' dentro do container CLI do Fabric.
    """
    command = [
        "docker", "exec", "cli",
        "peer", "chaincode", "invoke",
        "-o", "orderer.example.com:7050",
        "--tls", "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
        "-C", "logchannel", # Nome do nosso canal
        "-n", "logchaincode", # Nome do nosso chaincode
        "-c", f'{{"Args":["CreateLogHash","{log_id}","{log_hash}"]}}'
    ]
    
    try:
        # Executa o comando e captura a saída
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # O resultado do invoke bem sucedido geralmente vai para stderr, então checamos ambos
        output = result.stdout + result.stderr
        if "Chaincode invoke successful" in output or "status:200" in output:
            return True, output
        else:
            return False, output
            
    except subprocess.CalledProcessError as e:
        # Este erro acontece se o comando retornar um código de saída diferente de zero
        return False, e.stderr
    except Exception as e:
        return False, str(e)


@app.route('/logs', methods=['POST'])
def add_log():
    data = request.get_json()
    if not data or 'log_data' not in data or 'log_hash' not in data:
        return jsonify({"error": "Payload inválido"}), 400

    log_entry = data['log_data']
    log_hash = data['log_hash']
    log_id = log_entry.get('id')

    # 1. Armazena o log completo no MongoDB (off-chain)
    try:
        log_collection.insert_one(log_entry)
    except Exception as e:
        return jsonify({"error": f"Falha ao salvar no MongoDB: {e}"}), 500

    # 2. Registra o hash na Blockchain (on-chain)
    success, fabric_output = invoke_fabric_chaincode(log_id, log_hash)
    
    if not success:
        # Se falhar no Fabric, o ideal seria ter uma lógica para reverter a inserção no Mongo
        # ou marcar o log como "não ancorado". Para este TCC, apenas retornamos o erro.
        print(f"Erro no Fabric: {fabric_output}")
        return jsonify({
            "error": "Log salvo no MongoDB, mas falhou ao registrar hash na blockchain.",
            "details": fabric_output
        }), 500

    return jsonify({"status": "Log recebido e hash registrado com sucesso"}), 201


if __name__ == '__main__':
    # Roda o servidor Flask na porta 5000, acessível por qualquer IP
    app.run(host='0.0.0.0', port=5000, debug=True)
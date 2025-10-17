#!/bin/bash
# Script para iniciar API em background

cd /root/tcc-log-management/testing

# Matar processos antigos
pkill -f api_server_mongodb.py 2>/dev/null
sleep 1

# Limpar sync_control para evitar erros de índice duplicado
docker exec mongo mongosh --quiet logdb --eval "db.sync_control.deleteMany({})" > /dev/null 2>&1

# Iniciar nova instância
nohup python3 src/api_server_mongodb.py > /tmp/api.log 2>&1 &

# Aguardar inicialização
sleep 3

# Verificar se está rodando
if pgrep -f api_server_mongodb.py > /dev/null; then
    echo "✅ API iniciada com sucesso"
    curl -s http://localhost:5001/health
else
    echo "❌ Falha ao iniciar API"
    echo "Últimos logs:"
    tail -10 /tmp/api.log
    exit 1
fi

#!/bin/bash

# Script para consultar logs específicos no Hyperledger Fabric
# Uso: ./query_fabric.sh <log_id>

LOG_ID="$1"

if [ -z "$LOG_ID" ]; then
    echo "Uso: $0 <log_id>"
    echo ""
    echo "Exemplo:"
    echo "  $0 log-123456789"
    echo ""
    echo "Para listar IDs disponíveis no MongoDB:"
    echo "  docker exec mongo mongosh logdb --quiet --eval \"db.logs.find({}, {id:1, _id:0}).limit(10).toArray()\""
    exit 1
fi

echo "🔍 Consultando log no Fabric: $LOG_ID"
echo ""

# Consultar via peer chaincode
RESULT=$(docker exec peer0.org1.example.com peer chaincode query \
    -C logchannel \
    -n logchaincode \
    -c "{\"function\":\"GetLog\",\"Args\":[\"$LOG_ID\"]}" \
    2>&1)

if [[ "$RESULT" == *"Error"* ]]; then
    echo "❌ Log não encontrado no Fabric ou erro na consulta:"
    echo "$RESULT"
    exit 1
else
    echo "✅ Log encontrado no Fabric:"
    echo ""
    echo "$RESULT" | jq '.' 2>/dev/null || echo "$RESULT"
fi

echo ""
echo "💡 Para comparar com MongoDB:"
echo "   docker exec mongo mongosh logdb --quiet --eval \"db.logs.findOne({id: '$LOG_ID'})\""

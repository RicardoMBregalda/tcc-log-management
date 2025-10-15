#!/bin/bash
# Script SIMPLIFICADO para atualizar chaincode (sem reiniciar rede)
# Execute este script se a rede já está rodando e você só quer atualizar o chaincode

set -e

echo "=========================================="
echo "ATUALIZANDO CHAINCODE (Rede Existente)"
echo "=========================================="
echo ""

cd "$(dirname "$0")/.."

# 1. Verificar rede
echo "1️⃣  Verificando rede..."
if ! docker ps | grep -q "cli"; then
    echo "❌ Rede não está rodando. Use o script reinstall_chaincode_with_stacktrace.sh"
    exit 1
fi
echo "   ✅ Rede rodando"

# 2. Compilar chaincode
echo ""
echo "2️⃣  Compilando chaincode..."
cd ../chaincode
GO111MODULE=on go build -o logchaincode
echo "   ✅ Compilado"

# 3. Copiar para container
echo ""
echo "3️⃣  Copiando para container..."
cd ..
docker exec cli rm -rf /opt/gopath/src/github/chaincode 2>/dev/null || true
docker cp chaincode cli:/opt/gopath/src/github/
echo "   ✅ Copiado"

# 4. Empacotar
echo ""
echo "4️⃣  Empacotando chaincode..."
TIMESTAMP=$(date +%s)
docker exec cli peer lifecycle chaincode package logchaincode_${TIMESTAMP}.tar.gz \
  --path /opt/gopath/src/github/chaincode \
  --lang golang \
  --label logchaincode_v${TIMESTAMP}
echo "   ✅ Empacotado"

# 5. Instalar em peer0
echo ""
echo "5️⃣  Instalando em peer0..."
docker exec cli peer lifecycle chaincode install logchaincode_${TIMESTAMP}.tar.gz

# 6. Obter Package ID
echo ""
echo "6️⃣  Obtendo Package ID..."
docker exec cli peer lifecycle chaincode queryinstalled > /tmp/queryinstalled.txt
PACKAGE_ID=$(grep "logchaincode_v${TIMESTAMP}" /tmp/queryinstalled.txt | awk '{print $3}' | sed 's/,$//')
echo "   Package ID: $PACKAGE_ID"

if [ -z "$PACKAGE_ID" ]; then
    echo "❌ Erro ao obter Package ID"
    cat /tmp/queryinstalled.txt
    exit 1
fi

# 7. Aprovar
echo ""
echo "7️⃣  Aprovando chaincode..."
NEW_SEQUENCE=$(docker exec cli peer lifecycle chaincode querycommitted --channelID logchannel --name logchaincode 2>/dev/null | grep "Sequence" | awk '{print $2}' || echo "0")
NEW_SEQUENCE=$((NEW_SEQUENCE + 1))
echo "   Nova sequence: $NEW_SEQUENCE"

docker exec -e CC_PACKAGE_ID=$PACKAGE_ID cli peer lifecycle chaincode approveformyorg \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID logchannel \
  --name logchaincode \
  --version ${TIMESTAMP} \
  --package-id $PACKAGE_ID \
  --sequence $NEW_SEQUENCE \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# 8. Comitar
echo ""
echo "8️⃣  Comitando chaincode..."
docker exec cli peer lifecycle chaincode commit \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID logchannel \
  --name logchaincode \
  --version ${TIMESTAMP} \
  --sequence $NEW_SEQUENCE \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses peer0.org1.example.com:7051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo ""
echo "=========================================="
echo "✅ CHAINCODE ATUALIZADO!"
echo "=========================================="
echo ""
echo "🚀 Próximos passos:"
echo "   1. Reiniciar API: cd ../../testing/scripts && ./start_api_mongodb.sh"
echo "   2. Testar: cd ../../testing && python test_stacktrace.py"
echo ""

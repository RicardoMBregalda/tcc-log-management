#!/bin/bash
# Script para reinstalar o chaincode após modificações (EXECUTA NO HOST)
# Este script copia o chaincode atualizado e executa a instalação dentro do container CLI

set -e

echo "=========================================="
echo "REINSTALANDO CHAINCODE COM STACKTRACE"
echo "=========================================="
echo ""

# Voltar para o diretório raiz do fabric-network
cd "$(dirname "$0")/.."

# 1. Verificar se a rede está rodando
echo "1️⃣  Verificando se a rede Fabric está rodando..."
if ! docker ps | grep -q "cli"; then
    echo "❌ Container CLI não encontrado. A rede Fabric está rodando?"
    echo "   Execute: cd hybrid-architecture/fabric-network && docker-compose up -d"
    exit 1
fi
echo "   ✅ Rede Fabric rodando"

# 2. Rebuildar o chaincode
echo ""
echo "2️⃣  Recompilando chaincode..."
cd ../chaincode
if [ ! -f "logchaincode" ]; then
    echo "   Compilando chaincode..."
    GO111MODULE=on go build -o logchaincode
fi
echo "   ✅ Chaincode compilado"

# 3. Copiar chaincode para o container
echo ""
echo "3️⃣  Copiando chaincode para container CLI..."
cd ..
docker exec cli rm -rf /opt/gopath/src/github.com/chaincode 2>/dev/null || true
docker cp chaincode cli:/opt/gopath/src/github/
echo "   ✅ Chaincode copiado"

# 4. Parar a rede e limpar dados antigos
echo ""
echo "4️⃣  Parando rede e limpando dados antigos..."
cd fabric-network
docker-compose down
docker volume prune -f
echo "   ✅ Dados limpos"

# 5. Reiniciar a rede
echo ""
echo "5️⃣  Reiniciando rede Fabric..."
docker-compose up -d
echo "   Aguardando 10 segundos para rede inicializar..."
sleep 10
echo "   ✅ Rede reiniciada"

# 6. Criar canal e juntar peers
echo ""
echo "6️⃣  Configurando canal..."
docker exec cli peer channel create \
  -o orderer.example.com:7050 \
  -c logchannel \
  -f /opt/gopath/src/github.com/hyperledger/fabric/peer/config/logchannel.tx \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo "   Aguardando 5 segundos..."
sleep 5

echo "   Juntando peer0 ao canal..."
docker exec cli peer channel join -b logchannel.block

echo "   Juntando peer1 ao canal..."
docker exec -e CORE_PEER_ADDRESS=peer1.org1.example.com:9051 \
  -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt \
  cli peer channel join -b logchannel.block

echo "   Juntando peer2 ao canal..."
docker exec -e CORE_PEER_ADDRESS=peer2.org1.example.com:11051 \
  -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer2.org1.example.com/tls/ca.crt \
  cli peer channel join -b logchannel.block

echo "   ✅ Canal configurado"

# 7. Empacotar chaincode
echo ""
echo "7️⃣  Empacotando chaincode..."
docker exec cli peer lifecycle chaincode package logchaincode.tar.gz \
  --path /opt/gopath/src/github/chaincode \
  --lang golang \
  --label logchaincode_v2
echo "   ✅ Chaincode empacotado"

# 8. Instalar em todos os peers
echo ""
echo "8️⃣  Instalando chaincode nos peers..."

echo "   - Instalando em peer0..."
docker exec cli peer lifecycle chaincode install logchaincode.tar.gz

echo "   - Instalando em peer1..."
docker exec -e CORE_PEER_ADDRESS=peer1.org1.example.com:9051 \
  -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt \
  cli peer lifecycle chaincode install logchaincode.tar.gz

echo "   - Instalando em peer2..."
docker exec -e CORE_PEER_ADDRESS=peer2.org1.example.com:11051 \
  -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer2.org1.example.com/tls/ca.crt \
  cli peer lifecycle chaincode install logchaincode.tar.gz

echo "   ✅ Chaincode instalado"

# 9. Obter Package ID
echo ""
echo "9️⃣  Obtendo Package ID..."
docker exec cli peer lifecycle chaincode queryinstalled > /tmp/queryinstalled.txt
PACKAGE_ID=$(grep "logchaincode_v2" /tmp/queryinstalled.txt | awk '{print $3}' | sed 's/,$//')
echo "   Package ID: $PACKAGE_ID"

if [ -z "$PACKAGE_ID" ]; then
    echo "   ❌ Erro ao obter Package ID"
    exit 1
fi

# 10. Aprovar chaincode
echo ""
echo "🔟 Aprovando chaincode..."
docker exec -e CC_PACKAGE_ID=$PACKAGE_ID cli peer lifecycle chaincode approveformyorg \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID logchannel \
  --name logchaincode \
  --version 2.0 \
  --package-id $PACKAGE_ID \
  --sequence 2 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo "   ✅ Chaincode aprovado"

# 11. Verificar prontidão
echo ""
echo "1️⃣1️⃣ Verificando prontidão para commit..."
docker exec cli peer lifecycle chaincode checkcommitreadiness \
  --channelID logchannel \
  --name logchaincode \
  --version 2.0 \
  --sequence 2 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --output json

# 12. Comitar chaincode
echo ""
echo "1️⃣2️⃣ Comitando chaincode..."
docker exec cli peer lifecycle chaincode commit \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID logchannel \
  --name logchaincode \
  --version 2.0 \
  --sequence 2 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses peer0.org1.example.com:7051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo "   ✅ Chaincode comitado"

# 13. Verificar instalação
echo ""
echo "1️⃣3️⃣ Verificando chaincode instalado..."
docker exec cli peer lifecycle chaincode querycommitted \
  --channelID logchannel \
  --name logchaincode \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

echo ""
echo "=========================================="
echo "✅ CHAINCODE REINSTALADO COM SUCESSO!"
echo "=========================================="
echo ""
echo "📋 Mudanças implementadas:"
echo "   - Struct Log: campo Stacktrace adicionado"
echo "   - CreateLog: 8º parâmetro 'stacktrace' adicionado"
echo "   - Versão atualizada: v2.0 (sequence 2)"
echo ""
echo "🚀 Próximos passos:"
echo "   1. Reiniciar API: cd ../../testing/scripts && ./start_api_mongodb.sh"
echo "   2. Testar: cd ../../testing && python test_stacktrace.py"
echo ""

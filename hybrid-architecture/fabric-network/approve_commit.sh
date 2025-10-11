#!/bin/bash
set -e

echo "🔧 Aprovando e fazendo commit do chaincode otimizado..."

# Configurar ambiente
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID='Org1MSP'
export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

PACKAGE_ID="logchaincode_1:5fdb2a0343cb288afeaf12aa39a7693cba0aae5f7f3eb28d4aaf3c5e2a34574c"

cd /opt/gopath/src/github.com/hyperledger/fabric/peer

echo ""
echo "1️⃣ Aprovando chaincode..."
peer lifecycle chaincode approveformyorg \
  -o orderer.example.com:7050 \
  --tls --cafile $ORDERER_CA \
  --channelID logchannel \
  --name logchaincode \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1

echo ""
echo "2️⃣ Verificando aprovação..."
peer lifecycle chaincode checkcommitreadiness \
  --channelID logchannel \
  --name logchaincode \
  --version 1.0 \
  --sequence 1

echo ""
echo "3️⃣ Fazendo commit do chaincode..."
peer lifecycle chaincode commit \
  -o orderer.example.com:7050 \
  --tls --cafile $ORDERER_CA \
  --channelID logchannel \
  --name logchaincode \
  --version 1.0 \
  --sequence 1 \
  --peerAddresses peer0.org1.example.com:7051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo ""
echo "4️⃣ Verificando chaincode committed..."
peer lifecycle chaincode querycommitted --channelID logchannel --name logchaincode

echo ""
echo "✅ Chaincode otimizado instalado e ativo!"

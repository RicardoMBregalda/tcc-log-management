#!/bin/bash

# Script de teste do chaincode
set -e

echo "=========================================="
echo "🧪 TESTANDO CHAINCODE LOGCHAINCODE"
echo "=========================================="

cd /opt/gopath/src/github.com/hyperledger/fabric/peer

# Configuração
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID='Org1MSP'
export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

CHANNEL_NAME="logchannel"
CHAINCODE_NAME="logchaincode"

echo ""
echo "📝 Teste 1: Criar um log de teste..."
peer chaincode invoke \
  -C $CHANNEL_NAME \
  -n $CHAINCODE_NAME \
  -c '{"Args":["CreateLog","AUTO001","abc123hash","2025-10-16T22:00:00Z","init-script","INFO","Sistema inicializado automaticamente","{}",""]}' \
  --tls \
  --cafile $ORDERER_CA

echo ""
echo "⏳ Aguardando transação ser processada..."
sleep 3

echo ""
echo "📖 Teste 2: Consultar o log criado..."
peer chaincode query \
  -C $CHANNEL_NAME \
  -n $CHAINCODE_NAME \
  -c '{"Args":["QueryLog","AUTO001"]}' | jq '.'

echo ""
echo "=========================================="
echo "✅ TESTES CONCLUÍDOS!"
echo "=========================================="

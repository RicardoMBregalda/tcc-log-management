#!/bin/bash

# Script para instalar e instanciar o chaincode de logs
set -e

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID='Org1MSP'
export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp

echo "========================================"
echo "INSTALANDO CHAINCODE DE LOGS"
echo "========================================"

# Empacotar chaincode
echo "1. Empacotando chaincode..."
peer lifecycle chaincode package logchaincode.tar.gz \
  --path /opt/gopath/src/github.com/chaincode \
  --lang golang \
  --label logchaincode_1

echo "2. Instalando chaincode nos peers..."

# Instalar em peer0
echo "   - Instalando em peer0..."
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
peer lifecycle chaincode install logchaincode.tar.gz

# Instalar em peer1
echo "   - Instalando em peer1..."
export CORE_PEER_ADDRESS=peer1.org1.example.com:9051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt
peer lifecycle chaincode install logchaincode.tar.gz

# Instalar em peer2
echo "   - Instalando em peer2..."
export CORE_PEER_ADDRESS=peer2.org1.example.com:11051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer2.org1.example.com/tls/ca.crt
peer lifecycle chaincode install logchaincode.tar.gz

# Voltar para peer0 para as próximas operações
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo "3. Obtendo Package ID..."
peer lifecycle chaincode queryinstalled >& log.txt
export CC_PACKAGE_ID=$(sed -n "/logchaincode_1/{s/^Package ID: //; s/, Label:.*$//; p;}" log.txt)
echo "   Package ID: $CC_PACKAGE_ID"

echo "4. Aprovando chaincode para Org1..."
peer lifecycle chaincode approveformyorg \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID logchannel \
  --name logchaincode \
  --version 1.0 \
  --package-id $CC_PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile $ORDERER_CA

echo "5. Verificando prontidão para commit..."
peer lifecycle chaincode checkcommitreadiness \
  --channelID logchannel \
  --name logchaincode \
  --version 1.0 \
  --sequence 1 \
  --tls \
  --cafile $ORDERER_CA \
  --output json

echo "6. Comitando definição do chaincode..."
peer lifecycle chaincode commit \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID logchannel \
  --name logchaincode \
  --version 1.0 \
  --sequence 1 \
  --tls \
  --cafile $ORDERER_CA \
  --peerAddresses peer0.org1.example.com:7051 \
  --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo "7. Verificando chaincode comitado..."
peer lifecycle chaincode querycommitted \
  --channelID logchannel \
  --name logchaincode \
  --cafile $ORDERER_CA

echo "========================================"
echo "CHAINCODE INSTALADO COM SUCESSO!"
echo "========================================"

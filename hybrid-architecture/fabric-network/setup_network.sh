#!/bin/bash

# Aborta o script se qualquer comando falhar
set -e

# Define as variáveis de ambiente globais
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID='Org1MSP'
export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp

# ---------------------------------
# 1. CRIAR E JUNTAR CANAL
# ---------------------------------
echo "########### Criando o canal logchannel... ###########"
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
peer channel create -o orderer.example.com:7050 -c logchannel -f ./channel-artifacts/logchannel.tx --tls --cafile $ORDERER_CA
sleep 3

echo "########### Juntando peer0 ao canal logchannel... ###########"
peer channel join -b logchannel.block
sleep 3

echo "########### Juntando peer1 ao canal logchannel... ###########"
export CORE_PEER_ADDRESS=peer1.org1.example.com:9051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt
peer channel join -b logchannel.block
sleep 3

echo "########### Juntando peer2 ao canal logchannel... ###########"
export CORE_PEER_ADDRESS=peer2.org1.example.com:11051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer2.org1.example.com/tls/ca.crt
peer channel join -b logchannel.block
sleep 3

# ---------------------------------
# 2. INSTALAR CHAINCODE
# ---------------------------------
echo "########### Empacotando e Instalando o Chaincode... ###########"
peer lifecycle chaincode package logchaincode.tar.gz --path /opt/gopath/src/github.com/chaincode --lang golang --label logchaincode_1

echo "--> Instalando em peer0..."
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
peer lifecycle chaincode install logchaincode.tar.gz
echo "--> Chaincode instalado em peer0."
sleep 3

echo "--> Instalando em peer1..."
export CORE_PEER_ADDRESS=peer1.org1.example.com:9051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt
peer lifecycle chaincode install logchaincode.tar.gz
echo "--> Chaincode instalado em peer1."
sleep 3

echo "--> Instalando em peer2..."
export CORE_PEER_ADDRESS=peer2.org1.example.com:11051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer2.org1.example.com/tls/ca.crt
peer lifecycle chaincode install logchaincode.tar.gz
echo "--> Chaincode instalado em peer2."
sleep 3

# ---------------------------------
# 3. APROVAR E COMITAR CHAINCODE
# ---------------------------------
echo "########### Aprovando e Comitando o Chaincode... ###########"
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo "--> Consultando Package ID..."
peer lifecycle chaincode queryinstalled >& cc.log
export CC_PACKAGE_ID=$(grep -o 'logchaincode_1:[a-f0-9]*' cc.log)
echo "---> Usando Package ID: $CC_PACKAGE_ID"

echo "--> Aprovando para a organização..."
peer lifecycle chaincode approveformyorg -o orderer.example.com:7050 --channelID logchannel --name logchaincode --version 1.0 --package-id $CC_PACKAGE_ID --sequence 1 --tls --cafile $ORDERER_CA

echo "--> Comitando a definição do chaincode..."
export PEER0_CA_CERT=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export PEER1_CA_CERT=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt
export PEER2_CA_CERT=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer2.org1.example.com/tls/ca.crt
peer lifecycle chaincode commit -o orderer.example.com:7050 --channelID logchannel --name logchaincode --version 1.0 --sequence 1 --tls --cafile $ORDERER_CA --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles $PEER0_CA_CERT --peerAddresses peer1.org1.example.com:9051 --tlsRootCertFiles $PEER1_CA_CERT --peerAddresses peer2.org1.example.com:11051 --tlsRootCertFiles $PEER2_CA_CERT

echo "########### FIM DO SETUP - SUCESSO! ###########"
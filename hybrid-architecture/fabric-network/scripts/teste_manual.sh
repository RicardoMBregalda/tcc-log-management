#!/bin/bash

# Script de teste manual do chaincode

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID='Org1MSP'
export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo "=========================================="
echo "TESTE MANUAL DO CHAINCODE"
echo "=========================================="

# Criar um log personalizado
echo ""
echo "1. Criando log personalizado..."
peer chaincode invoke \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls \
  --cafile $ORDERER_CA \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"CreateLog","Args":["log999","myhash999","2025-10-09T22:00:00Z","meu-teste","INFO","Log criado manualmente para teste","{\"usuario\":\"Ricardo\"}"]}'

echo ""
echo "2. Aguardando 3 segundos..."
sleep 3

# Consultar o log criado
echo ""
echo "3. Consultando o log criado (log999)..."
peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"QueryLog","Args":["log999"]}'

# Listar todos os logs
echo ""
echo ""
echo "4. Listando TODOS os logs..."
peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"GetAllLogs","Args":[]}'

# Consultar histórico
echo ""
echo ""
echo "5. Consultando histórico do log999..."
peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"GetLogHistory","Args":["log999"]}'

# Verificar altura da blockchain
echo ""
echo ""
echo "6. Verificando altura da blockchain..."
peer channel getinfo -c logchannel

echo ""
echo "=========================================="
echo "TESTE CONCLUÍDO!"
echo "=========================================="

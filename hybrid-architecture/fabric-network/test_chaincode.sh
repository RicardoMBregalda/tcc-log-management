#!/bin/bash

# Script para testar o chaincode de logs
set -e

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID='Org1MSP'
export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

echo "========================================"
echo "TESTANDO CHAINCODE DE LOGS"
echo "========================================"

# Teste 1: Criar um log
echo "1. Criando um log de teste..."
peer chaincode invoke \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls \
  --cafile $ORDERER_CA \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"CreateLog","Args":["log001","abc123hash","2025-10-09T20:00:00Z","app-server","INFO","Test log message","{\"user\":\"admin\"}"]}'

echo ""
echo "2. Aguardando propagação do bloco..."
sleep 3

# Teste 2: Consultar o log criado
echo "3. Consultando o log criado..."
peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"QueryLog","Args":["log001"]}'

echo ""
echo "4. Criando mais alguns logs..."
peer chaincode invoke \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls \
  --cafile $ORDERER_CA \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"CreateLog","Args":["log002","def456hash","2025-10-09T20:01:00Z","database","ERROR","Database connection failed","{\"db\":\"postgres\"}"]}'

sleep 2

peer chaincode invoke \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls \
  --cafile $ORDERER_CA \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"CreateLog","Args":["log003","ghi789hash","2025-10-09T20:02:00Z","web-server","WARN","High memory usage","{\"memory\":\"85%\"}"]}'

echo ""
echo "5. Aguardando propagação..."
sleep 3

# Teste 3: Listar todos os logs
echo "6. Listando todos os logs..."
peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"GetAllLogs","Args":[]}'

echo ""
echo "7. Consultando histórico do log001..."
peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"GetLogHistory","Args":["log001"]}'

echo ""
echo "========================================"
echo "TESTES CONCLUÍDOS COM SUCESSO!"
echo "========================================"

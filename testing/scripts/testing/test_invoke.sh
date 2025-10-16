#!/bin/bash

# Test direct chaincode invoke
docker exec cli peer chaincode invoke \
  -o orderer.example.com:7050 \
  --tls \
  --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"StoreMerkleRoot","Args":["test_batch_001","abc123def456","2025-10-14T01:00:00Z","10","[\"log1\",\"log2\"]"]}'

echo ""
echo "Waiting 3 seconds..."
sleep 3

# Query the batch back
echo "Querying batch test_batch_001..."
docker exec cli peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"QueryMerkleBatch","Args":["test_batch_001"]}'

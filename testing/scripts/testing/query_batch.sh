#!/bin/bash
docker exec cli peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c "{\"function\":\"QueryMerkleBatch\",\"Args\":[\"$1\"]}"

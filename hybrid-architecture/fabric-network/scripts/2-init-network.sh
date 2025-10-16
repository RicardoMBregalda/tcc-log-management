#!/bin/bash

# Script de inicialização automática da rede Fabric
# Este script é executado automaticamente quando o container CLI inicia

set -e

CHANNEL_NAME="logchannel"
CHAINCODE_NAME="logchaincode"
CHAINCODE_VERSION="1.0"
SEQUENCE=1

# Diretório de trabalho
cd /opt/gopath/src/github.com/hyperledger/fabric/peer

# Aguardar os serviços estarem prontos
echo "⏳ Aguardando serviços da rede Fabric ficarem prontos..."
sleep 10

# Configurações globais
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID='Org1MSP'
export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp

# ============================================
# VERIFICAR SE CANAL JÁ EXISTE
# ============================================
echo "🔍 Verificando se canal já existe..."
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

if peer channel list 2>/dev/null | grep -q "$CHANNEL_NAME"; then
    echo "✅ Canal $CHANNEL_NAME já existe"
else
    echo "📝 Criando canal $CHANNEL_NAME..."
    
    # Criar diretório para artifacts se não existir
    mkdir -p channel-artifacts
    
    # Copiar transaction file se não existir
    if [ ! -f "channel-artifacts/logchannel.tx" ]; then
        cp config/logchannel.tx channel-artifacts/
    fi
    
    # Criar canal
    peer channel create \
        -o orderer.example.com:7050 \
        -c $CHANNEL_NAME \
        -f ./channel-artifacts/logchannel.tx \
        --tls \
        --cafile $ORDERER_CA
    
    echo "✅ Canal criado com sucesso"
    sleep 3
fi

# ============================================
# JUNTAR PEERS AO CANAL
# ============================================
echo "🔗 Juntando peers ao canal..."

# Peer0
echo "  → Juntando peer0..."
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
if ! peer channel list 2>/dev/null | grep -q "$CHANNEL_NAME"; then
    peer channel join -b logchannel.block
    echo "  ✅ peer0 juntou ao canal"
else
    echo "  ℹ️  peer0 já está no canal"
fi
sleep 2

# Peer1
echo "  → Juntando peer1..."
export CORE_PEER_ADDRESS=peer1.org1.example.com:9051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt
if ! peer channel list 2>/dev/null | grep -q "$CHANNEL_NAME"; then
    peer channel join -b logchannel.block
    echo "  ✅ peer1 juntou ao canal"
else
    echo "  ℹ️  peer1 já está no canal"
fi
sleep 2

# Peer2
echo "  → Juntando peer2..."
export CORE_PEER_ADDRESS=peer2.org1.example.com:11051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer2.org1.example.com/tls/ca.crt
if ! peer channel list 2>/dev/null | grep -q "$CHANNEL_NAME"; then
    peer channel join -b logchannel.block
    echo "  ✅ peer2 juntou ao canal"
else
    echo "  ℹ️  peer2 já está no canal"
fi
sleep 2

# ============================================
# INSTALAR CHAINCODE
# ============================================
echo "📦 Verificando chaincode instalado..."

# Voltar para peer0
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

# Verificar se chaincode já está instalado
if peer lifecycle chaincode queryinstalled 2>/dev/null | grep -q "logchaincode_1"; then
    echo "ℹ️  Chaincode já instalado, obtendo Package ID..."
    peer lifecycle chaincode queryinstalled > /tmp/installed.txt
    export CC_PACKAGE_ID=$(sed -n "/logchaincode_1/{s/^Package ID: //; s/, Label:.*$//; p;}" /tmp/installed.txt)
    echo "  Package ID: $CC_PACKAGE_ID"
else
    echo "📦 Empacotando chaincode..."
    peer lifecycle chaincode package logchaincode.tar.gz \
        --path /opt/gopath/src/github.com/chaincode \
        --lang golang \
        --label logchaincode_1
    
    echo "📥 Instalando chaincode nos peers..."
    
    # Peer0
    echo "  → Instalando em peer0..."
    export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
    export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    peer lifecycle chaincode install logchaincode.tar.gz
    
    # Peer1
    echo "  → Instalando em peer1..."
    export CORE_PEER_ADDRESS=peer1.org1.example.com:9051
    export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer1.org1.example.com/tls/ca.crt
    peer lifecycle chaincode install logchaincode.tar.gz
    
    # Peer2
    echo "  → Instalando em peer2..."
    export CORE_PEER_ADDRESS=peer2.org1.example.com:11051
    export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer2.org1.example.com/tls/ca.crt
    peer lifecycle chaincode install logchaincode.tar.gz
    
    echo "✅ Chaincode instalado em todos os peers"
    
    # Obter Package ID
    export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
    export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    peer lifecycle chaincode queryinstalled > /tmp/installed.txt
    export CC_PACKAGE_ID=$(sed -n "/logchaincode_1/{s/^Package ID: //; s/, Label:.*$//; p;}" /tmp/installed.txt)
    echo "  Package ID: $CC_PACKAGE_ID"
fi

# ============================================
# APROVAR CHAINCODE
# ============================================
echo "✔️  Verificando aprovação do chaincode..."

if peer lifecycle chaincode checkcommitreadiness \
    -C $CHANNEL_NAME \
    -n $CHAINCODE_NAME \
    -v $CHAINCODE_VERSION \
    --sequence $SEQUENCE \
    --tls \
    --cafile $ORDERER_CA \
    --output json 2>/dev/null | grep -q '"Org1MSP": true'; then
    echo "ℹ️  Chaincode já aprovado pela Org1MSP"
else
    echo "✍️  Aprovando chaincode para Org1MSP..."
    peer lifecycle chaincode approveformyorg \
        -o orderer.example.com:7050 \
        --tls \
        --cafile $ORDERER_CA \
        -C $CHANNEL_NAME \
        -n $CHAINCODE_NAME \
        -v $CHAINCODE_VERSION \
        --package-id $CC_PACKAGE_ID \
        --sequence $SEQUENCE
    
    echo "✅ Chaincode aprovado"
    sleep 3
fi

# ============================================
# COMMIT CHAINCODE
# ============================================
echo "🚀 Verificando commit do chaincode..."

if peer lifecycle chaincode querycommitted -C $CHANNEL_NAME 2>/dev/null | grep -q "$CHAINCODE_NAME"; then
    echo "✅ Chaincode já está committed no canal"
else
    echo "📝 Fazendo commit do chaincode..."
    peer lifecycle chaincode commit \
        -o orderer.example.com:7050 \
        --tls \
        --cafile $ORDERER_CA \
        -C $CHANNEL_NAME \
        -n $CHAINCODE_NAME \
        -v $CHAINCODE_VERSION \
        --sequence $SEQUENCE \
        --peerAddresses peer0.org1.example.com:7051 \
        --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    
    echo "✅ Chaincode committed com sucesso"
    sleep 3
fi

# ============================================
# VERIFICAÇÃO FINAL
# ============================================
echo ""
echo "=========================================="
echo "✅ REDE FABRIC CONFIGURADA COM SUCESSO!"
echo "=========================================="
echo ""
echo "📊 Status da Rede:"
echo "  • Canal: $CHANNEL_NAME"
echo "  • Chaincode: $CHAINCODE_NAME v$CHAINCODE_VERSION"
echo "  • Peers: peer0, peer1, peer2"
echo ""
echo "🧪 Para testar, execute:"
echo "   docker exec cli peer chaincode query -C $CHANNEL_NAME -n $CHAINCODE_NAME -c '{\"Args\":[\"queryAllLogs\"]}'"
echo ""
echo "=========================================="

# Manter container rodando
echo "Container CLI pronto para uso. Pressione Ctrl+C para sair."
tail -f /dev/null

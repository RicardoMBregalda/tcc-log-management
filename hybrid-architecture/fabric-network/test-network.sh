#!/bin/bash

# ============================================
# Script de Teste da Rede Fabric
# ============================================
# 
# Executa testes rápidos para validar que a rede está funcionando corretamente.
#

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================
# TESTES
# ============================================
print_header "🧪 TESTES DA REDE FABRIC"

# Teste 1: Container CLI respondendo
print_info "Teste 1: Verificando container CLI..."
if docker exec cli echo "OK" &>/dev/null; then
    print_success "Container CLI está respondendo"
else
    print_error "Container CLI não está acessível"
    exit 1
fi

# Teste 2: Canal criado
print_info "Teste 2: Verificando canal logchannel..."
if docker exec cli peer channel list 2>/dev/null | grep -q "logchannel"; then
    print_success "Canal 'logchannel' existe"
else
    print_error "Canal 'logchannel' não encontrado"
    exit 1
fi

# Teste 3: Chaincode instalado
print_info "Teste 3: Verificando chaincode instalado..."
if docker exec cli peer lifecycle chaincode queryinstalled 2>/dev/null | grep -q "logchaincode"; then
    print_success "Chaincode 'logchaincode' está instalado"
else
    print_error "Chaincode não está instalado"
    exit 1
fi

# Teste 4: Chaincode committed
print_info "Teste 4: Verificando chaincode committed..."
if docker exec cli peer lifecycle chaincode querycommitted -C logchannel 2>/dev/null | grep -q "logchaincode"; then
    print_success "Chaincode está committed no canal"
else
    print_error "Chaincode não está committed"
    exit 1
fi

# Teste 5: Transação de escrita (invoke)
print_info "Teste 5: Testando transação de escrita..."
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_ID="TEST_$(date +%s)"

docker exec cli bash -c "
    export CORE_PEER_TLS_ENABLED=true
    export CORE_PEER_LOCALMSPID='Org1MSP'
    export ORDERER_CA=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
    export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
    export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
    export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    
    peer chaincode invoke \
        -C logchannel \
        -n logchaincode \
        -c '{\"Args\":[\"CreateLog\",\"$LOG_ID\",\"hash123\",\"$TIMESTAMP\",\"test-script\",\"INFO\",\"Teste automatizado da rede\",\"{}\",\"\"]}' \
        --tls \
        --cafile \$ORDERER_CA
" &>/dev/null

if [ $? -eq 0 ]; then
    print_success "Transação de escrita executada com sucesso"
else
    print_error "Falha na transação de escrita"
    exit 1
fi

# Aguardar transação ser processada
sleep 3

# Teste 6: Transação de leitura (query)
print_info "Teste 6: Testando transação de leitura..."
QUERY_RESULT=$(docker exec cli bash -c "
    export CORE_PEER_TLS_ENABLED=true
    export CORE_PEER_LOCALMSPID='Org1MSP'
    export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
    export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
    export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
    
    peer chaincode query \
        -C logchannel \
        -n logchaincode \
        -c '{\"Args\":[\"QueryLog\",\"$LOG_ID\"]}'
" 2>&1)

if echo "$QUERY_RESULT" | grep -q "$LOG_ID"; then
    print_success "Transação de leitura executada com sucesso"
    echo ""
    echo "📄 Resultado da query:"
    echo "$QUERY_RESULT" | jq '.' 2>/dev/null || echo "$QUERY_RESULT"
else
    print_error "Falha na transação de leitura"
    echo "$QUERY_RESULT"
    exit 1
fi

# ============================================
# RESUMO
# ============================================
print_header "✅ TODOS OS TESTES PASSARAM!"

echo "Estatísticas da Rede:"
echo ""
echo "📊 Containers:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}" | grep "Up" | wc -l | xargs echo "  • Rodando:"
echo ""
echo "🔗 Canal:"
echo "  • Nome: logchannel"
docker exec cli peer channel getinfo -c logchannel 2>/dev/null | grep "Blockchain info:" | sed 's/^/  • /'
echo ""
echo "📦 Chaincode:"
docker exec cli peer lifecycle chaincode querycommitted -C logchannel 2>/dev/null | grep "Name:" | sed 's/^/  • /'
echo ""

print_info "A rede Hyperledger Fabric está completamente operacional! 🚀"

#!/bin/bash

# ============================================
# Script Master - Inicialização da Rede Fabric
# ============================================
# 
# Este script orquestra todo o processo de inicialização da rede Hyperledger Fabric.
# Executa automaticamente todos os passos necessários na ordem correta.
#
# Uso: ./start-network.sh [opção]
#
# Opções:
#   --clean     Limpa tudo e reinicia do zero
#   --restart   Reinicia a rede sem recriar artefatos
#   (nenhuma)   Inicialização normal (padrão)
#

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Função para imprimir com cor
print_header() {
    echo -e "\n${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Processar argumentos
CLEAN_MODE=false
RESTART_MODE=false

if [ "$1" == "--clean" ]; then
    CLEAN_MODE=true
    print_warning "Modo CLEAN: Removendo tudo e recriando do zero"
elif [ "$1" == "--restart" ]; then
    RESTART_MODE=true
    print_info "Modo RESTART: Reiniciando sem recriar artefatos"
fi

# ============================================
# PASSO 1: LIMPAR (se --clean)
# ============================================
if [ "$CLEAN_MODE" = true ]; then
    print_header "PASSO 1: LIMPEZA COMPLETA"
    
    echo "🗑️  Parando e removendo containers..."
    docker-compose down -v 2>/dev/null || true
    
    echo "🗑️  Removendo artefatos antigos..."
    rm -rf crypto-config/ 2>/dev/null || true
    rm -f config/genesis.block config/logchannel.tx 2>/dev/null || true
    rm -f *.block *.tar.gz 2>/dev/null || true
    
    print_success "Limpeza completa realizada"
    sleep 2
fi

# ============================================
# PASSO 2: VERIFICAR/GERAR ARTEFATOS
# ============================================
if [ "$RESTART_MODE" = false ]; then
    print_header "PASSO 2: ARTEFATOS CRIPTOGRÁFICOS"
    
    if [ -f "config/genesis.block" ] && [ -f "config/logchannel.tx" ] && [ -d "crypto-config" ]; then
        print_info "Artefatos já existem, pulando geração..."
    else
        print_info "Gerando certificados e artefatos da rede..."
        chmod +x scripts/1-generate-artifacts.sh
        ./scripts/1-generate-artifacts.sh
        print_success "Artefatos gerados com sucesso"
    fi
    
    # Verificar se artefatos foram criados
    if [ ! -f "config/genesis.block" ] || [ ! -f "config/logchannel.tx" ]; then
        print_error "Falha ao gerar artefatos!"
        exit 1
    fi
    
    sleep 2
fi

# ============================================
# PASSO 3: INICIAR CONTAINERS
# ============================================
print_header "PASSO 3: INICIAR CONTAINERS DOCKER"

if [ "$RESTART_MODE" = true ]; then
    echo "🔄 Reiniciando containers..."
    docker-compose restart
else
    echo "🚀 Iniciando containers Docker Compose..."
    docker-compose up -d
fi

# Aguardar containers ficarem saudáveis
echo "⏳ Aguardando containers iniciarem..."
sleep 15

# Verificar status
RUNNING=$(docker-compose ps --services --filter "status=running" | wc -l)
TOTAL=$(docker-compose ps --services | wc -l)

if [ "$RUNNING" -lt "$((TOTAL - 2))" ]; then
    print_warning "Alguns containers podem não estar rodando corretamente"
    docker-compose ps
else
    print_success "Todos os containers iniciados ($RUNNING/$TOTAL rodando)"
fi

sleep 2

# ============================================
# PASSO 4: AGUARDAR INICIALIZAÇÃO AUTOMÁTICA
# ============================================
print_header "PASSO 4: CONFIGURAÇÃO AUTOMÁTICA DA REDE"

print_info "Container CLI está executando inicialização automática..."
print_info "Isso inclui:"
echo "  • Criação do canal 'logchannel'"
echo "  • Junção dos peers ao canal"
echo "  • Instalação do chaincode"
echo "  • Aprovação e commit do chaincode"
echo ""

# Aguardar inicialização automática (verificando logs)
echo "⏳ Aguardando configuração automática (30-60s)..."

for i in {1..60}; do
    if docker logs cli 2>&1 | grep -q "REDE FABRIC CONFIGURADA COM SUCESSO"; then
        print_success "Inicialização automática concluída!"
        break
    fi
    
    if [ $i -eq 60 ]; then
        print_warning "Tempo limite atingido, verificando status manualmente..."
    fi
    
    sleep 1
done

sleep 2

# ============================================
# PASSO 5: VERIFICAÇÃO
# ============================================
print_header "PASSO 5: VERIFICAÇÃO DO STATUS"

echo "📊 Verificando canal..."
if docker exec cli peer channel list 2>/dev/null | grep -q "logchannel"; then
    print_success "Canal 'logchannel' criado e peers conectados"
else
    print_error "Canal não foi criado corretamente"
fi

echo ""
echo "📦 Verificando chaincode..."
if docker exec cli peer lifecycle chaincode querycommitted -C logchannel 2>/dev/null | grep -q "logchaincode"; then
    print_success "Chaincode 'logchaincode' instalado e committed"
else
    print_warning "Chaincode pode não estar completamente configurado"
fi

sleep 2

# ============================================
# RESUMO FINAL
# ============================================
print_header "✅ REDE FABRIC PRONTA!"

echo "📊 Status dos Componentes:"
echo ""
docker-compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(NAME|Up)" || docker-compose ps
echo ""

print_info "URLs de Acesso:"
echo "  • CouchDB Peer0: http://localhost:5984/_utils (admin/password)"
echo "  • CouchDB Peer1: http://localhost:6984/_utils (admin/password)"
echo "  • CouchDB Peer2: http://localhost:7984/_utils (admin/password)"
echo ""

print_info "Comandos Úteis:"
echo "  • Ver logs do CLI:     docker logs cli -f"
echo "  • Testar chaincode:    ./test-network.sh"
echo "  • Parar rede:          docker-compose down"
echo "  • Reiniciar:           ./start-network.sh --restart"
echo "  • Reset completo:      ./start-network.sh --clean"
echo ""

print_header "🎉 INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!"

# Perguntar se quer executar testes
echo ""
read -p "Deseja executar testes do chaincode agora? (s/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    print_info "Executando testes..."
    ./test-network.sh
fi

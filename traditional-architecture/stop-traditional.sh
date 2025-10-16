#!/bin/bash

# ============================================
# Script de Parada da Arquitetura Tradicional
# ============================================
# 
# Para todos os containers e opcionalmente remove volumes.
#
# Uso: ./stop-traditional.sh [opção]
#
# Opções:
#   --clean     Para e remove todos os volumes (dados PostgreSQL serão perdidos)
#   (nenhuma)   Apenas para os containers (mantém volumes e dados)
#

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verificar opção --clean
if [ "$1" == "--clean" ]; then
    print_warning "ATENÇÃO: Modo --clean irá remover TODOS os volumes!"
    print_warning "Todos os dados do PostgreSQL (Primary e Standby) serão PERDIDOS!"
    echo ""
    read -p "Tem certeza que deseja continuar? (s/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Operação cancelada"
        exit 0
    fi
    
    echo ""
    print_info "Parando containers e removendo volumes..."
    docker-compose down -v
    print_success "Containers parados e volumes removidos"
    
else
    print_info "Parando containers..."
    docker-compose down
    print_success "Containers parados (volumes e dados mantidos)"
    
    echo ""
    print_info "Para remover volumes também, use: ./stop-traditional.sh --clean"
fi

echo ""
print_success "Arquitetura Tradicional parada com sucesso!"

#!/bin/bash

# ============================================
# Script Master - Inicialização Arquitetura Tradicional
# ============================================
# 
# Inicia PostgreSQL com replicação streaming (Primary + Standby)
# e stack completa de monitoramento.
#
# Uso: ./start-traditional.sh [opção]
#
# Opções:
#   --clean     Limpa tudo e reinicia do zero
#   --restart   Reinicia sem recriar volumes
#   (nenhuma)   Inicialização normal (padrão)
#

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funções de print
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

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Processar argumentos
CLEAN_MODE=false
RESTART_MODE=false

if [ "$1" == "--clean" ]; then
    CLEAN_MODE=true
    print_warning "Modo CLEAN: Removendo tudo e recriando do zero"
elif [ "$1" == "--restart" ]; then
    RESTART_MODE=true
    print_info "Modo RESTART: Reiniciando sem recriar volumes"
fi

# ============================================
# PASSO 1: LIMPAR (se --clean)
# ============================================
if [ "$CLEAN_MODE" = true ]; then
    print_header "PASSO 1: LIMPEZA COMPLETA"
    
    echo "🗑️  Parando e removendo containers..."
    docker-compose down -v 2>/dev/null || true
    
    print_success "Limpeza completa realizada"
    sleep 2
fi

# ============================================
# PASSO 2: INICIAR CONTAINERS
# ============================================
print_header "PASSO 2: INICIAR CONTAINERS DOCKER"

if [ "$RESTART_MODE" = true ]; then
    echo "🔄 Reiniciando containers..."
    docker-compose restart
else
    echo "🚀 Iniciando containers Docker Compose..."
    docker-compose up -d
fi

# Aguardar containers ficarem saudáveis
echo "⏳ Aguardando containers iniciarem..."
sleep 10

# Verificar status
RUNNING=$(docker-compose ps --services --filter "status=running" | wc -l)
TOTAL=$(docker-compose ps --services | wc -l)

if [ "$RUNNING" -lt "$((TOTAL - 1))" ]; then
    print_warning "Alguns containers podem não estar rodando corretamente"
    docker-compose ps
else
    print_success "Todos os containers iniciados ($RUNNING/$TOTAL rodando)"
fi

sleep 2

# ============================================
# PASSO 3: VERIFICAR POSTGRESQL PRIMARY
# ============================================
print_header "PASSO 3: VERIFICAR POSTGRESQL PRIMARY"

print_info "Aguardando PostgreSQL Primary ficar pronto..."
for i in {1..30}; do
    if docker exec postgres-primary pg_isready -U loguser 2>/dev/null | grep -q "accepting connections"; then
        print_success "PostgreSQL Primary está pronto!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        print_error "Timeout aguardando PostgreSQL Primary"
        exit 1
    fi
    
    sleep 2
done

# Verificar se banco foi inicializado
echo ""
print_info "Verificando banco de dados 'logdb'..."
if docker exec postgres-primary psql -U loguser -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw logdb; then
    print_success "Banco 'logdb' existe e está acessível"
else
    print_warning "Banco 'logdb' pode não estar inicializado corretamente"
fi

sleep 2

# ============================================
# PASSO 4: VERIFICAR REPLICAÇÃO STANDBY
# ============================================
print_header "PASSO 4: VERIFICAR REPLICAÇÃO STANDBY"

print_info "Aguardando PostgreSQL Standby ficar pronto..."
for i in {1..60}; do
    if docker exec postgres-standby pg_isready -U loguser 2>/dev/null | grep -q "accepting connections"; then
        print_success "PostgreSQL Standby está pronto!"
        break
    fi
    
    if [ $i -eq 60 ]; then
        print_warning "Standby pode ainda estar sincronizando (normal em primeira inicialização)"
        break
    fi
    
    sleep 2
done

# Verificar replicação
echo ""
print_info "Verificando status da replicação..."
sleep 3

REPL_STATUS=$(docker exec postgres-primary psql -U loguser -d logdb -c "SELECT state FROM pg_stat_replication;" -t 2>/dev/null | xargs)

if [ ! -z "$REPL_STATUS" ]; then
    if echo "$REPL_STATUS" | grep -q "streaming"; then
        print_success "Replicação ativa: $REPL_STATUS"
    else
        print_warning "Replicação em estado: $REPL_STATUS"
    fi
else
    print_warning "Replicação ainda não iniciada (pode levar alguns segundos)"
fi

sleep 2

# ============================================
# PASSO 5: VERIFICAÇÃO FINAL
# ============================================
print_header "PASSO 5: VERIFICAÇÃO DO STATUS"

echo "🗄️  PostgreSQL Primary:"
docker exec postgres-primary psql -U loguser -d logdb -c "SELECT version();" 2>/dev/null | head -3 || echo "  ⚠️  Não acessível"

echo ""
echo "🔄 PostgreSQL Standby:"
docker exec postgres-standby psql -U loguser -d logdb -c "SELECT pg_is_in_recovery();" 2>/dev/null | head -3 || echo "  ⚠️  Ainda não disponível"

sleep 2

# ============================================
# RESUMO FINAL
# ============================================
print_header "✅ ARQUITETURA TRADICIONAL PRONTA!"

echo "📊 Status dos Componentes:"
echo ""
docker-compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(NAME|Up)" || docker-compose ps
echo ""

print_info "URLs de Acesso:"
echo "  • PostgreSQL Primary: localhost:5432 (loguser/logpass)"
echo "  • PostgreSQL Standby: localhost:5433 (loguser/logpass)"
echo ""

print_info "Comandos Úteis:"
echo "  • Testar replicação:   ./test-traditional.sh"
echo "  • Ver logs Primary:    docker logs postgres-primary"
echo "  • Ver logs Standby:    docker logs postgres-standby"
echo "  • Conectar no Primary: docker exec -it postgres-primary psql -U loguser -d logdb"
echo "  • Parar tudo:          ./stop-traditional.sh"
echo ""

print_header "🎉 INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!"

# Perguntar se quer executar testes
echo ""
read -p "Deseja executar testes de replicação agora? (s/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    print_info "Executando testes..."
    ./test-traditional.sh
fi

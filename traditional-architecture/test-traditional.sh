#!/bin/bash

# ============================================
# Script de Teste da Arquitetura Tradicional
# ============================================
# 
# Executa testes para validar PostgreSQL com replicação streaming.
#

set -e

# Cores
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
print_header "🧪 TESTES DA ARQUITETURA TRADICIONAL"

# Teste 1: PostgreSQL Primary respondendo
print_info "Teste 1: Verificando PostgreSQL Primary..."
if docker exec postgres-primary pg_isready -U loguser 2>/dev/null | grep -q "accepting connections"; then
    print_success "PostgreSQL Primary está respondendo"
else
    print_error "PostgreSQL Primary não está acessível"
    exit 1
fi

# Teste 2: PostgreSQL Standby respondendo
print_info "Teste 2: Verificando PostgreSQL Standby..."
if docker exec postgres-standby pg_isready -U loguser 2>/dev/null | grep -q "accepting connections"; then
    print_success "PostgreSQL Standby está respondendo"
else
    print_error "PostgreSQL Standby não está acessível"
    exit 1
fi

# Teste 3: Banco logdb existe
print_info "Teste 3: Verificando banco 'logdb'..."
if docker exec postgres-primary psql -U loguser -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw logdb; then
    print_success "Banco 'logdb' existe"
else
    print_error "Banco 'logdb' não encontrado"
    exit 1
fi

# Teste 4: Standby está em modo recovery
print_info "Teste 4: Verificando modo recovery do Standby..."
IN_RECOVERY=$(docker exec postgres-standby psql -U loguser -d logdb -t -c "SELECT pg_is_in_recovery();" 2>/dev/null | xargs)
if [ "$IN_RECOVERY" = "t" ]; then
    print_success "Standby está em modo recovery (correto)"
else
    print_error "Standby NÃO está em modo recovery"
    exit 1
fi

# Teste 5: Replicação ativa
print_info "Teste 5: Verificando replicação streaming..."
REPL_STATE=$(docker exec postgres-primary psql -U loguser -d logdb -t -c "SELECT state FROM pg_stat_replication;" 2>/dev/null | xargs)
if echo "$REPL_STATE" | grep -q "streaming"; then
    print_success "Replicação streaming ativa: $REPL_STATE"
else
    print_error "Replicação não está em modo streaming: $REPL_STATE"
    exit 1
fi

# Teste 6: Criar tabela de teste no Primary
print_info "Teste 6: Criando tabela de teste no Primary..."
TEST_TABLE="test_replication_$(date +%s)"

docker exec postgres-primary psql -U loguser -d logdb -c "
    CREATE TABLE IF NOT EXISTS $TEST_TABLE (
        id SERIAL PRIMARY KEY,
        data TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
" &>/dev/null

if [ $? -eq 0 ]; then
    print_success "Tabela '$TEST_TABLE' criada no Primary"
else
    print_error "Falha ao criar tabela no Primary"
    exit 1
fi

# Teste 7: Inserir dados no Primary
print_info "Teste 7: Inserindo dados no Primary..."
docker exec postgres-primary psql -U loguser -d logdb -c "
    INSERT INTO $TEST_TABLE (data) VALUES 
    ('Teste 1 - $(date)'),
    ('Teste 2 - $(date)'),
    ('Teste 3 - $(date)');
" &>/dev/null

if [ $? -eq 0 ]; then
    print_success "Dados inseridos no Primary"
else
    print_error "Falha ao inserir dados no Primary"
    exit 1
fi

# Aguardar replicação
echo ""
print_info "⏳ Aguardando replicação (3 segundos)..."
sleep 3

# Teste 8: Verificar dados replicados no Standby
print_info "Teste 8: Verificando dados replicados no Standby..."
STANDBY_COUNT=$(docker exec postgres-standby psql -U loguser -d logdb -t -c "SELECT COUNT(*) FROM $TEST_TABLE;" 2>/dev/null | xargs)

if [ "$STANDBY_COUNT" = "3" ]; then
    print_success "Dados replicados com sucesso! ($STANDBY_COUNT registros)"
    echo ""
    echo "📄 Dados no Standby:"
    docker exec postgres-standby psql -U loguser -d logdb -c "SELECT * FROM $TEST_TABLE;"
else
    print_error "Dados NÃO foram replicados corretamente (encontrados: $STANDBY_COUNT registros, esperados: 3)"
    exit 1
fi

# Teste 9: Verificar LSN (Log Sequence Number)
echo ""
print_info "Teste 9: Verificando sincronização LSN..."

PRIMARY_LSN=$(docker exec postgres-primary psql -U loguser -d logdb -t -c "SELECT pg_current_wal_lsn();" 2>/dev/null | xargs)
STANDBY_LSN=$(docker exec postgres-standby psql -U loguser -d logdb -t -c "SELECT pg_last_wal_replay_lsn();" 2>/dev/null | xargs)

echo "  Primary LSN:  $PRIMARY_LSN"
echo "  Standby LSN:  $STANDBY_LSN"

if [ ! -z "$PRIMARY_LSN" ] && [ ! -z "$STANDBY_LSN" ]; then
    print_success "LSN disponíveis (sincronização ativa)"
else
    print_error "Não foi possível obter LSN"
    exit 1
fi

# Teste 10: Limpar tabela de teste
echo ""
print_info "Teste 10: Limpando tabela de teste..."
docker exec postgres-primary psql -U loguser -d logdb -c "DROP TABLE IF EXISTS $TEST_TABLE;" &>/dev/null
print_success "Tabela de teste removida"

# ============================================
# RESUMO
# ============================================
print_header "✅ TODOS OS TESTES PASSARAM!"

echo "Estatísticas da Replicação:"
echo ""
echo "📊 Informações do Primary:"
docker exec postgres-primary psql -U loguser -d logdb -c "
    SELECT 
        client_addr,
        state,
        sync_state,
        replay_lsn
    FROM pg_stat_replication;
" 2>/dev/null || echo "  Não disponível"

echo ""
echo "📊 Informações do Standby:"
docker exec postgres-standby psql -U loguser -d logdb -c "
    SELECT pg_is_in_recovery() as in_recovery,
           pg_last_wal_receive_lsn() as receive_lsn,
           pg_last_wal_replay_lsn() as replay_lsn;
" 2>/dev/null || echo "  Não disponível"

echo ""
print_info "A replicação PostgreSQL está funcionando perfeitamente! 🚀"

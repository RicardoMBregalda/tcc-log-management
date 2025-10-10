#!/bin/bash
# Script para remover arquivos obsoletos do sistema antigo de sincronização
# Mantém apenas os arquivos da nova solução (insert_and_sync_log.py)

set -e

echo "=========================================="
echo "Limpeza de Arquivos Obsoletos"
echo "Sistema: sync_service.py (antigo)"
echo "=========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR="/root/tcc-log-management/testing"
cd "$BASE_DIR"

# Contador
REMOVED=0
BACKUP_COUNT=0

# Pergunta ao usuário
echo -e "${YELLOW}Este script irá remover 10 arquivos obsoletos relacionados ao sync_service.py${NC}"
echo ""
echo "Arquivos a serem removidos:"
echo "  • sync_service.py"
echo "  • sync_service.env"
echo "  • sync_service.service"
echo "  • sync_service.log"
echo "  • scripts/setup_sync.sh"
echo "  • scripts/monitor_sync.sh"
echo "  • scripts/test_sync.sh"
echo "  • scripts/test_single_sync.sh"
echo "  • scripts/test_batch_sync.sh"
echo "  • scripts/populate_postgres.sh"
echo ""
echo -e "${GREEN}Arquivos que serão mantidos:${NC}"
echo "  ✓ api_server.py"
echo "  ✓ insert_and_sync_log.py (NOVO)"
echo "  ✓ send_log_to_fabric.py (NOVO)"
echo "  ✓ test_api.py"
echo "  ✓ log_generator.py"
echo "  ✓ scripts/test_direct_sync.sh (NOVO)"
echo ""

read -p "Deseja fazer backup antes de remover? [S/n] " -n 1 -r
echo
MAKE_BACKUP=$REPLY

if [[ $MAKE_BACKUP =~ ^[Ss]$ ]] || [[ -z $MAKE_BACKUP ]]; then
    echo ""
    echo "📦 Criando backup..."
    
    BACKUP_DIR="../backup/old-sync-service-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR/scripts"
    
    # Backup arquivos principais
    [ -f "sync_service.py" ] && cp sync_service.py "$BACKUP_DIR/" && ((BACKUP_COUNT++))
    [ -f "sync_service.env" ] && cp sync_service.env "$BACKUP_DIR/" && ((BACKUP_COUNT++))
    [ -f "sync_service.service" ] && cp sync_service.service "$BACKUP_DIR/" && ((BACKUP_COUNT++))
    [ -f "sync_service.log" ] && cp sync_service.log "$BACKUP_DIR/" && ((BACKUP_COUNT++))
    
    # Backup scripts
    [ -f "scripts/setup_sync.sh" ] && cp scripts/setup_sync.sh "$BACKUP_DIR/scripts/" && ((BACKUP_COUNT++))
    [ -f "scripts/monitor_sync.sh" ] && cp scripts/monitor_sync.sh "$BACKUP_DIR/scripts/" && ((BACKUP_COUNT++))
    [ -f "scripts/test_sync.sh" ] && cp scripts/test_sync.sh "$BACKUP_DIR/scripts/" && ((BACKUP_COUNT++))
    [ -f "scripts/test_single_sync.sh" ] && cp scripts/test_single_sync.sh "$BACKUP_DIR/scripts/" && ((BACKUP_COUNT++))
    [ -f "scripts/test_batch_sync.sh" ] && cp scripts/test_batch_sync.sh "$BACKUP_DIR/scripts/" && ((BACKUP_COUNT++))
    [ -f "scripts/populate_postgres.sh" ] && cp scripts/populate_postgres.sh "$BACKUP_DIR/scripts/" && ((BACKUP_COUNT++))
    
    echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"
    echo -e "  $BACKUP_COUNT arquivos copiados"
    echo ""
fi

echo ""
read -p "Confirma a remoção dos arquivos obsoletos? [S/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]] && [[ ! -z $REPLY ]]; then
    echo -e "${YELLOW}❌ Operação cancelada pelo usuário${NC}"
    exit 0
fi

echo ""
echo "🗑️  Removendo arquivos obsoletos..."
echo ""

# Para sync_service se estiver rodando
if pgrep -f sync_service.py > /dev/null; then
    echo "⚠️  Parando sync_service.py em execução..."
    pkill -f sync_service.py
    sleep 2
    echo -e "${GREEN}✓ Processo parado${NC}"
fi

# Remove arquivos principais
if [ -f "sync_service.py" ]; then
    rm -f sync_service.py
    echo -e "${GREEN}✓ Removido: sync_service.py${NC}"
    ((REMOVED++))
fi

if [ -f "sync_service.env" ]; then
    rm -f sync_service.env
    echo -e "${GREEN}✓ Removido: sync_service.env${NC}"
    ((REMOVED++))
fi

if [ -f "sync_service.service" ]; then
    rm -f sync_service.service
    echo -e "${GREEN}✓ Removido: sync_service.service${NC}"
    ((REMOVED++))
fi

if [ -f "sync_service.log" ]; then
    rm -f sync_service.log
    echo -e "${GREEN}✓ Removido: sync_service.log${NC}"
    ((REMOVED++))
fi

# Remove scripts obsoletos
if [ -f "scripts/setup_sync.sh" ]; then
    rm -f scripts/setup_sync.sh
    echo -e "${GREEN}✓ Removido: scripts/setup_sync.sh${NC}"
    ((REMOVED++))
fi

if [ -f "scripts/monitor_sync.sh" ]; then
    rm -f scripts/monitor_sync.sh
    echo -e "${GREEN}✓ Removido: scripts/monitor_sync.sh${NC}"
    ((REMOVED++))
fi

if [ -f "scripts/test_sync.sh" ]; then
    rm -f scripts/test_sync.sh
    echo -e "${GREEN}✓ Removido: scripts/test_sync.sh${NC}"
    ((REMOVED++))
fi

if [ -f "scripts/test_single_sync.sh" ]; then
    rm -f scripts/test_single_sync.sh
    echo -e "${GREEN}✓ Removido: scripts/test_single_sync.sh${NC}"
    ((REMOVED++))
fi

if [ -f "scripts/test_batch_sync.sh" ]; then
    rm -f scripts/test_batch_sync.sh
    echo -e "${GREEN}✓ Removido: scripts/test_batch_sync.sh${NC}"
    ((REMOVED++))
fi

if [ -f "scripts/populate_postgres.sh" ]; then
    rm -f scripts/populate_postgres.sh
    echo -e "${GREEN}✓ Removido: scripts/populate_postgres.sh${NC}"
    ((REMOVED++))
fi

# Remove arquivos temporários relacionados
if [ -f "/tmp/sync_service.log" ]; then
    rm -f /tmp/sync_service.log
    echo -e "${GREEN}✓ Removido: /tmp/sync_service.log${NC}"
    ((REMOVED++))
fi

if [ -f "/tmp/sync_test.log" ]; then
    rm -f /tmp/sync_test.log
    echo -e "${GREEN}✓ Removido: /tmp/sync_test.log${NC}"
    ((REMOVED++))
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Limpeza Concluída!${NC}"
echo "=========================================="
echo ""
echo "📊 Resumo:"
echo "  • Arquivos removidos: $REMOVED"
if [[ $MAKE_BACKUP =~ ^[Ss]$ ]] || [[ -z $MAKE_BACKUP ]]; then
    echo "  • Backup criado: $BACKUP_DIR"
fi
echo ""
echo "📁 Arquivos mantidos (nova solução):"
ls -1 *.py 2>/dev/null | grep -E "(api_server|insert_and_sync|send_log|test_api|log_generator)" | while read file; do
    echo "  ✓ $file"
done
echo ""
echo "📁 Scripts mantidos:"
ls -1 scripts/*.sh 2>/dev/null | grep -E "(test_direct_sync|start_api)" | while read file; do
    echo "  ✓ $file"
done
echo ""
echo "🎯 Próximos passos:"
echo "  1. Use 'python3 insert_and_sync_log.py' para criar logs"
echo "  2. Execute 'bash scripts/test_direct_sync.sh' para testar"
echo "  3. Leia 'README_DIRECT_SYNC.md' para mais informações"
echo ""

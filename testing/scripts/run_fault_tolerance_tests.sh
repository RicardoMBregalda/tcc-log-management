#!/bin/bash
#
# Script para executar testes de tolerância a falhas
# Compara arquiteturas Híbrida vs Tradicional
#
# Uso: ./run_fault_tolerance_tests.sh
#

set -e

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ TESTES DE TOLERÂNCIA A FALHAS - TCC LOG MANAGEMENT ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar se as arquiteturas estão rodando
echo -e "${YELLOW} Verificando containers...${NC}"

check_container() {
 local container=$1
 if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
 echo -e " ${GREEN}[OK]${NC} $container"
 return 0
 else
 echo -e " ${RED}[ERRO]${NC} $container (não encontrado)"
 return 1
 fi
}

all_ok=true

echo -e "${BLUE}Arquitetura Híbrida:${NC}"
check_container "mongo" || all_ok=false
check_container "peer0.org1.example.com" || all_ok=false
check_container "peer1.org1.example.com" || all_ok=false
check_container "orderer.example.com" || all_ok=false

echo ""
echo -e "${BLUE}Arquitetura Tradicional:${NC}"
check_container "postgres-primary" || all_ok=false
check_container "postgres-standby" || all_ok=false

if [ "$all_ok" = false ]; then
 echo ""
 echo -e "${RED}[ERRO] Erro: Alguns containers não estão rodando${NC}"
 echo -e "${YELLOW}💡 Inicie as arquiteturas antes de executar os testes:${NC}"
 echo ""
 echo -e " ${BLUE}Híbrida:${NC}"
 echo " cd ../hybrid-architecture/fabric-network"
 echo " ./start-network.sh"
 echo ""
 echo -e " ${BLUE}Tradicional:${NC}"
 echo " cd ../traditional-architecture"
 echo " ./start-traditional.sh"
 echo ""
 exit 1
fi

echo ""
echo -e "${GREEN}[OK] Todos os containers necessários estão rodando${NC}"
echo ""

# Perguntar se quer continuar
echo -e "${YELLOW}[AVISO] ATENÇÃO:${NC}"
echo " • Os testes irão PARAR e REINICIAR containers"
echo " • Dados em memória podem ser perdidos"
echo " • Duração estimada: ~10 minutos"
echo ""
read -p "Deseja continuar? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
 echo -e "${YELLOW}Operação cancelada${NC}"
 exit 0
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE} INICIANDO TESTES${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Ir para diretório do script
cd "$(dirname "$0")/.."

# Executar testes
python3 tests/test_fault_tolerance.py

# Verificar se gerou relatório
if [ -f "results/fault_tolerance_report.md" ]; then
 echo ""
 echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
 echo -e "${GREEN}║ TESTES CONCLUÍDOS ║${NC}"
 echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
 echo ""
 echo -e "${GREEN} Relatórios gerados:${NC}"
 echo " • results/fault_tolerance_report.json"
 echo " • results/fault_tolerance_report.md"
 echo ""
 echo -e "${BLUE}Para visualizar o relatório:${NC}"
 echo " cat results/fault_tolerance_report.md"
 echo ""
else
 echo -e "${RED}[AVISO] Nenhum relatório foi gerado${NC}"
fi

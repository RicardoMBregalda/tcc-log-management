#!/bin/bash
###############################################################################
# Script de Execução - Testes de Resiliência
# 
# Este script facilita a execução dos testes de resiliência,
# verificando pré-requisitos e fornecendo opções de configuração.
#
# Uso: ./run_resilience_tests.sh [opções]
#
# Autor: Ricardo M Bregalda
# Data: 2025-10-14
###############################################################################

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TESTS_DIR="$PROJECT_ROOT/testing/tests"
RESULTS_DIR="$PROJECT_ROOT/testing/results"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       TESTES DE RESILIÊNCIA - TCC LOG MANAGEMENT        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# FUNÇÕES
###############################################################################

check_docker() {
    echo -e "${YELLOW}🔍 Verificando Docker...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker não encontrado!${NC}"
        echo "   Instale Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        echo -e "${RED}❌ Docker não está rodando!${NC}"
        echo "   Inicie o Docker daemon e tente novamente."
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker OK${NC}"
}

check_containers() {
    echo -e "${YELLOW}🔍 Verificando containers necessários...${NC}"
    
    local required_containers=(
        "peer0.org1.example.com"
        "orderer.example.com"
        "mongodb"
        "postgres-primary"
        "postgres-standby"
    )
    
    local missing_containers=()
    
    for container in "${required_containers[@]}"; do
        if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            missing_containers+=("$container")
        fi
    done
    
    if [ ${#missing_containers[@]} -gt 0 ]; then
        echo -e "${RED}❌ Containers não encontrados:${NC}"
        for container in "${missing_containers[@]}"; do
            echo "   - $container"
        done
        echo ""
        echo -e "${YELLOW}💡 Inicie os serviços com:${NC}"
        echo "   cd hybrid-architecture/fabric-network"
        echo "   docker-compose up -d"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Todos os containers estão rodando${NC}"
}

check_api() {
    echo -e "${YELLOW}🔍 Verificando API...${NC}"
    
    local api_url="${API_HOST:-localhost}:${API_PORT:-5001}"
    
    if curl -s "http://${api_url}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API respondendo em http://${api_url}${NC}"
    else
        echo -e "${RED}❌ API não está respondendo em http://${api_url}${NC}"
        echo ""
        echo -e "${YELLOW}💡 Verifique:${NC}"
        echo "   - API Flask está rodando?"
        echo "   - Porta correta (padrão: 5001)?"
        echo "   - Firewall bloqueando conexão?"
        exit 1
    fi
}

check_python() {
    echo -e "${YELLOW}🔍 Verificando Python...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 não encontrado!${NC}"
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python ${python_version}${NC}"
}

show_menu() {
    echo ""
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  OPÇÕES DE TESTE${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  1) Executar TODOS os testes (recomendado)"
    echo "  2) Testar apenas queda de Peer Fabric"
    echo "  3) Testar apenas queda de Ordering Service"
    echo "  4) Testar apenas queda de MongoDB"
    echo "  5) Testar apenas Failover PostgreSQL"
    echo "  6) Testar apenas Isolamento de rede"
    echo "  7) Executar modo interativo (Python)"
    echo "  8) Ver resultados anteriores"
    echo "  0) Sair"
    echo ""
}

run_all_tests() {
    echo -e "${GREEN}🚀 Executando TODOS os testes de resiliência...${NC}"
    echo ""
    
    cd "$TESTS_DIR"
    python3 test_resilience.py
    
    show_results
}

run_single_test() {
    local test_name="$1"
    echo -e "${GREEN}🚀 Executando teste: ${test_name}${NC}"
    echo ""
    
    cd "$TESTS_DIR"
    python3 -c "
from test_resilience import ResilienceTest
tester = ResilienceTest()
tester.${test_name}()
"
}

show_results() {
    echo ""
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  RESULTADOS${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════${NC}"
    echo ""
    
    if [ -f "$RESULTS_DIR/resilience_report.md" ]; then
        echo -e "${GREEN}📄 Relatório Markdown:${NC}"
        echo "   $RESULTS_DIR/resilience_report.md"
        echo ""
        
        # Mostrar resumo
        if command -v head &> /dev/null; then
            head -n 20 "$RESULTS_DIR/resilience_report.md"
            echo ""
            echo "   ... (veja arquivo completo para detalhes)"
        fi
    else
        echo -e "${YELLOW}⚠️ Nenhum resultado encontrado ainda${NC}"
    fi
    
    if [ -f "$RESULTS_DIR/resilience_report.json" ]; then
        echo ""
        echo -e "${GREEN}📊 Relatório JSON:${NC}"
        echo "   $RESULTS_DIR/resilience_report.json"
    fi
}

###############################################################################
# VERIFICAÇÕES PRÉ-TESTE
###############################################################################

echo -e "${YELLOW}🔍 Executando verificações pré-teste...${NC}"
echo ""

check_docker
check_python
check_containers
check_api

echo ""
echo -e "${GREEN}✅ Todas as verificações passaram!${NC}"

###############################################################################
# MENU INTERATIVO
###############################################################################

while true; do
    show_menu
    
    read -p "Escolha uma opção [0-8]: " choice
    
    case $choice in
        1)
            run_all_tests
            ;;
        2)
            run_single_test "test_peer_failure"
            ;;
        3)
            run_single_test "test_orderer_failure"
            ;;
        4)
            run_single_test "test_mongodb_failure"
            ;;
        5)
            run_single_test "test_postgres_failover"
            ;;
        6)
            run_single_test "test_network_isolation"
            ;;
        7)
            echo -e "${GREEN}🐍 Iniciando modo interativo Python...${NC}"
            cd "$TESTS_DIR"
            python3 -i -c "from test_resilience import ResilienceTest; tester = ResilienceTest(); print('Use: tester.test_peer_failure(), etc')"
            ;;
        8)
            show_results
            ;;
        0)
            echo ""
            echo -e "${BLUE}👋 Até logo!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opção inválida!${NC}"
            ;;
    esac
    
    echo ""
    read -p "Pressione ENTER para continuar..."
done

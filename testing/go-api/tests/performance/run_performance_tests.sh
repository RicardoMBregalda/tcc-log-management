#!/bin/bash

# Performance Tests Runner for Go API
# Equivalent to testing/run_all_tests.sh for Python

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
API_URL="http://localhost:5001"
POSTGRES_CONN="host=localhost port=5432 user=loguser password=logpass dbname=logdb sslmode=disable connect_timeout=5"
SCENARIOS_FILE="../../../src/test_scenarios.json"
RESULTS_DIR="results_go"
QUICK_MODE=false
SPECIFIC_SCENARIOS=""
ARCHITECTURE="both"  # hybrid, traditional, or both

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --quick                  Run quick tests (S1, S5, S9 only)"
    echo "  --scenarios LIST         Run specific scenarios (comma-separated, e.g., S1,S3,S5)"
    echo "  --architecture ARCH      Architecture to test: hybrid, traditional, or both (default: both)"
    echo "  --api-url URL            API base URL for hybrid architecture (default: $API_URL)"
    echo "  --postgres-conn CONN     PostgreSQL connection string (default: host=localhost port=5432...)"
    echo "  --results DIR            Results directory (default: $RESULTS_DIR)"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Run all scenarios on both architectures"
    echo "  $0 --quick                                  # Run quick tests on both architectures"
    echo "  $0 --architecture hybrid                    # Test only hybrid (MongoDB+Fabric)"
    echo "  $0 --architecture traditional               # Test only PostgreSQL"
    echo "  $0 --architecture both --quick              # Quick test on both architectures"
    echo "  $0 --scenarios S1,S2,S3 --architecture both # Specific scenarios on both"
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --scenarios)
            SPECIFIC_SCENARIOS="$2"
            shift 2
            ;;
        --architecture)
            ARCHITECTURE="$2"
            shift 2
            ;;
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --postgres-conn)
            POSTGRES_CONN="$2"
            shift 2
            ;;
        --results)
            RESULTS_DIR="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            ;;
    esac
done

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║          Performance Tests - Go Implementation            ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}📋 Arquitetura(s) a testar: ${YELLOW}$ARCHITECTURE${NC}\n"

# Check architectures
if [ "$ARCHITECTURE" = "hybrid" ] || [ "$ARCHITECTURE" = "both" ]; then
    echo -e "${YELLOW}🏥 Verificando API Híbrida (MongoDB+Fabric)...${NC}"
    if ! curl -s -f "$API_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}❌ API Híbrida não está respondendo em $API_URL${NC}"
        echo ""
        echo -e "${YELLOW}💡 Para iniciar a API:${NC}"
        echo "   cd ../../go-api"
        echo "   ./api"
        echo ""
        
        if [ "$ARCHITECTURE" = "hybrid" ]; then
            exit 1
        else
            echo -e "${YELLOW}⚠️  Continuando apenas com PostgreSQL...${NC}"
            ARCHITECTURE="traditional"
        fi
    else
        echo -e "${GREEN}✅ API Híbrida está respondendo${NC}"
    fi
    echo ""
fi

if [ "$ARCHITECTURE" = "traditional" ] || [ "$ARCHITECTURE" = "both" ]; then
    echo -e "${YELLOW}🏥 Verificando PostgreSQL...${NC}"
    
    # Verificar se PostgreSQL está acessível
    if ! docker exec postgres-primary psql -U loguser -d logdb -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${RED}❌ PostgreSQL não está respondendo${NC}"
        echo ""
        echo -e "${YELLOW}💡 Para iniciar o PostgreSQL:${NC}"
        echo "   cd ../../../../traditional-architecture"
        echo "   ./start-traditional.sh"
        echo ""
        
        if [ "$ARCHITECTURE" = "traditional" ]; then
            exit 1
        else
            echo -e "${YELLOW}⚠️  Continuando apenas com API Híbrida...${NC}"
            ARCHITECTURE="hybrid"
        fi
    else
        echo -e "${GREEN}✅ PostgreSQL está respondendo${NC}"
    fi
    echo ""
fi

# Check if scenarios file exists
if [ ! -f "$SCENARIOS_FILE" ]; then
    echo -e "${RED}❌ Arquivo de cenários não encontrado: $SCENARIOS_FILE${NC}"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"

# Build the test program
echo -e "${YELLOW}🔨 Compilando testes...${NC}"

# Instalar dependências se necessário
if ! go mod download 2>/dev/null; then
    echo -e "${YELLOW}📦 Baixando dependências...${NC}"
    go get github.com/lib/pq
fi

if ! go build -o performance_tests .; then
    echo -e "${RED}❌ Falha na compilação${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Compilação concluída${NC}"

# Prepare arguments
TEST_ARGS="-api-url=$API_URL -postgres-conn=$POSTGRES_CONN -scenarios=$SCENARIOS_FILE -results=$RESULTS_DIR -architecture=$ARCHITECTURE"

if [ "$QUICK_MODE" = true ]; then
    TEST_ARGS="$TEST_ARGS -quick"
    echo -e "\n${BLUE}🚀 Executando testes em modo RÁPIDO (S1, S5, S9)${NC}"
    echo -e "${BLUE}   Arquitetura(s): $ARCHITECTURE${NC}"
elif [ -n "$SPECIFIC_SCENARIOS" ]; then
    TEST_ARGS="$TEST_ARGS -scenarios-list=$SPECIFIC_SCENARIOS"
    echo -e "\n${BLUE}🚀 Executando cenários específicos: $SPECIFIC_SCENARIOS${NC}"
    echo -e "${BLUE}   Arquitetura(s): $ARCHITECTURE${NC}"
else
    echo -e "\n${BLUE}🚀 Executando TODOS os cenários${NC}"
    echo -e "${BLUE}   Arquitetura(s): $ARCHITECTURE${NC}"
fi

# Run tests
echo -e "${YELLOW}Starting tests...${NC}\n"
START_TIME=$(date +%s)

./performance_tests $TEST_ARGS

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Summary
echo -e "\n${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                  Testes Concluídos!                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${BLUE}⏱️  Duração: $((DURATION / 60)) minutos e $((DURATION % 60)) segundos${NC}"
echo -e "${BLUE}📁 Resultados salvos em: $RESULTS_DIR${NC}"
echo ""
echo -e "${YELLOW}📊 Arquivos gerados:${NC}"
echo "   - all_results.json                (todos os resultados em JSON)"
echo "   - results.csv                     (resultados em CSV)"
echo "   - report.md                       (relatório em Markdown)"
if [ "$ARCHITECTURE" = "hybrid" ] || [ "$ARCHITECTURE" = "both" ]; then
    echo "   - S*_hybrid_insert.json           (resultados híbrida inserção)"
    echo "   - S*_hybrid_query.json            (resultados híbrida consulta)"
fi
if [ "$ARCHITECTURE" = "traditional" ] || [ "$ARCHITECTURE" = "both" ]; then
    echo "   - S*_postgres_insert.json         (resultados PostgreSQL inserção)"
    echo "   - S*_postgres_query.json          (resultados PostgreSQL consulta)"
fi
echo ""

# Compare with Python results if they exist
PYTHON_RESULTS="../../src/results"
if [ -d "$PYTHON_RESULTS" ]; then
    echo -e "${YELLOW}💡 Para comparar com os resultados Python:${NC}"
    echo "   diff $RESULTS_DIR/results.csv $PYTHON_RESULTS/performance_results.csv"
    echo ""
fi

echo -e "${GREEN}✅ Processo concluído com sucesso!${NC}"

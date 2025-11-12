#!/bin/bash
#
# Script de Testes - TCC Log Management
# Versão Minimalista
#

set -e

# Configurações
QUICK_MODE=false
ARCHITECTURE="both"

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick) QUICK_MODE=true; shift ;;
        --architecture) ARCHITECTURE="$2"; shift 2 ;;
        *) echo "Opção desconhecida: $1"; exit 1 ;;
    esac
done

# Banner
echo ""
echo "========================================================================"
echo "TESTES - TCC LOG MANAGEMENT"
echo "========================================================================"
echo "Modo: $([ "$QUICK_MODE" = true ] && echo 'Rápido (S1,S5,S9)' || echo 'Completo')"
echo "Arquitetura: $(echo $ARCHITECTURE | tr '[:lower:]' '[:upper:]')"
echo ""

cd "$(dirname "$0")"

# Verificações
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 não encontrado"
    exit 1
fi

if ! python3 -c "import requests, psycopg2, psutil" &> /dev/null; then
    pip3 install -r requirements.txt > /dev/null 2>&1
fi

# Verifica containers
check_container() {
    docker ps --format '{{.Names}}' | grep -q "^$1$"
}

all_ok=true
if [ "$ARCHITECTURE" = "hybrid" ] || [ "$ARCHITECTURE" = "both" ]; then
    check_container "mongo" || all_ok=false
    check_container "peer0.org1.example.com" || all_ok=false
    check_container "orderer.example.com" || all_ok=false
fi

if [ "$ARCHITECTURE" = "postgres" ] || [ "$ARCHITECTURE" = "both" ]; then
    check_container "postgres-primary" || all_ok=false
fi

if [ "$all_ok" = false ]; then
    echo "[ERRO] Containers não estão rodando"
    echo "Inicie: cd ../hybrid-architecture/fabric-network && ./start-network.sh"
    exit 1
fi

echo "[OK] Containers rodando"
echo ""

# Backup
mkdir -p results
BACKUP="results/backup_$(date +%Y%m%d_%H%M%S)"
if [ -d "results" ] && [ "$(ls -A results 2>/dev/null)" ]; then
    mkdir -p "$BACKUP"
    cp results/*.{json,csv,md} "$BACKUP/" 2>/dev/null || true
fi

# Confirmação
if [ -t 0 ]; then
    read -p "Iniciar testes? (s/N): " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Ss]$ ]] && exit 0
fi

# Limpeza
echo "Limpando dados..."
bash scripts/clean_logs_fast.sh
echo ""

# Testes
echo "Iniciando testes..."
echo ""

START_TIME=$(date +%s)

if [ "$QUICK_MODE" = true ]; then
    for scenario in S1 S5 S9; do
        echo "Cenário $scenario..."
        
        if [ "$ARCHITECTURE" = "hybrid" ] || [ "$ARCHITECTURE" = "both" ]; then
            python3 -c "
import sys
sys.path.insert(0, 'src')
from performance_tester import run_single_scenario, load_test_scenarios

config = load_test_scenarios()
scenario = next((s for s in config['scenarios'] if s['id'] == '$scenario'), None)
if scenario:
    run_single_scenario(scenario, 'hybrid')
"
        fi
        
        if [ "$ARCHITECTURE" = "postgres" ] || [ "$ARCHITECTURE" = "both" ]; then
            python3 -c "
import sys
sys.path.insert(0, 'src')
from performance_tester import run_single_scenario, load_test_scenarios

config = load_test_scenarios()
scenario = next((s for s in config['scenarios'] if s['id'] == '$scenario'), None)
if scenario:
    run_single_scenario(scenario, 'postgres')
"
        fi
        echo ""
    done
else
    ARCHS="['hybrid', 'postgres']"
    [ "$ARCHITECTURE" = "hybrid" ] && ARCHS="['hybrid']"
    [ "$ARCHITECTURE" = "postgres" ] && ARCHS="['postgres']"
    
    python3 -c "
import sys
sys.path.insert(0, 'src')
from performance_tester import run_all_scenarios

run_all_scenarios($ARCHS)
"
fi

# Análise
if [ -f "results/all_scenarios.json" ]; then
    python3 src/analyze_results.py
fi

# Final
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "========================================================================"
echo "CONCLUÍDO"
echo "========================================================================"
echo "Tempo: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo "Resultados: testing/results/"
echo ""

if [ -d "results" ]; then
    ls -lh results/*.{json,csv,md} 2>/dev/null | awk '{print $9 " (" $5 ")"}'
fi

#!/bin/bash

# ========================================
# Script de Teste Rápido - Cenários S1-S3
# ========================================
# 
# Executa apenas os cenários pequenos (10k logs) para validação rápida:
# - S1: 10k logs @ 100 logs/s = 100 segundos
# - S2: 10k logs @ 1k logs/s = 10 segundos
# - S3: 10k logs @ 10k logs/s = 1 segundo
# 
# Tempo estimado total: ~2-3 minutos
# ========================================

set -e

echo "========================================"
echo "  TESTE RÁPIDO - Cenários S1-S3"
echo "========================================"
echo ""
echo "Este é um teste rápido com apenas 10k logs"
echo "para validar o funcionamento antes de executar"
echo "os cenários grandes (100k e 1M logs)."
echo ""
echo "Tempo estimado: ~3 minutos"
echo ""

# Verifica se a API está rodando
echo "Verificando se a API está rodando..."
if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "❌ ERRO: API não está respondendo em http://localhost:5001"
    echo "   Execute primeiro: python3 api_server_mongodb.py"
    exit 1
fi
echo "✓ API está rodando"
echo ""

# Cria diretório de resultados
mkdir -p results

# Marca hora de início
START_TIME=$(date +%s)
echo "Iniciando em: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Executa apenas cenários S1, S2, S3
for scenario in S1 S2 S3; do
    echo "========================================"
    echo "  Executando cenário: $scenario"
    echo "========================================"
    
    # Executa o cenário via Python diretamente
    python3 -c "
import sys
import json
sys.path.insert(0, '.')
from performance_tester import load_test_scenarios, run_single_scenario, save_scenario_result

config = load_test_scenarios()
scenario = next((s for s in config['scenarios'] if s['id'] == '$scenario'), None)

if scenario:
    # Hybrid
    result_hybrid = run_single_scenario(scenario, 'hybrid')
    save_scenario_result(result_hybrid)
    
    # PostgreSQL
    result_postgres = run_single_scenario(scenario, 'postgres')
    save_scenario_result(result_postgres)
else:
    print(f'Cenário $scenario não encontrado!')
    sys.exit(1)
"
    
    echo ""
    echo "✓ Cenário $scenario concluído"
    echo ""
    sleep 5  # Pausa entre cenários
done

# Calcula tempo total
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "========================================"
echo "  TESTE RÁPIDO CONCLUÍDO!"
echo "========================================"
echo "Tempo total: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Resultados salvos em:"
echo "  - results/scenario_S1_hybrid.json"
echo "  - results/scenario_S1_postgres.json"
echo "  - results/scenario_S2_hybrid.json"
echo "  - results/scenario_S2_postgres.json"
echo "  - results/scenario_S3_hybrid.json"
echo "  - results/scenario_S3_postgres.json"
echo ""
echo "Para ver análise comparativa, execute:"
echo "  python3 analyze_results.py"
echo ""
echo "Para executar TODOS os cenários (incluindo 100k e 1M logs):"
echo "  ./run_all_scenarios.sh"
echo "========================================"

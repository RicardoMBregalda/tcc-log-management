#!/bin/bash

# ========================================
# Script de Execução de Todos os Cenários TCC
# ========================================
# 
# Este script executa os 9 cenários de teste:
# - 3 volumes: 10k, 100k, 1M logs
# - 3 taxas: 100, 1k, 10k logs/segundo
# 
# Tempo estimado total:
# - S1-S3 (10k logs): 111 segundos (~2 minutos)
# - S4-S6 (100k logs): 1.110 segundos (~18 minutos)
# - S7-S9 (1M logs): 11.100 segundos (~3 horas)
# ========================================

set -e  # Para em caso de erro

echo "========================================"
echo "  MATRIZ DE CENÁRIOS TCC - EXECUÇÃO"
echo "========================================"
echo ""
echo "Total de cenários: 9"
echo "Arquiteturas: Hybrid (MongoDB+Fabric) e PostgreSQL"
echo ""
echo "⚠️  AVISO: Este processo pode levar várias horas"
echo "⚠️  Certifique-se que todos os serviços estão rodando:"
echo "   - MongoDB"
echo "   - PostgreSQL"
echo "   - Hyperledger Fabric"
echo "   - API (porta 5001)"
echo ""
read -p "Pressione ENTER para continuar ou Ctrl+C para cancelar..."

# Cria diretório de resultados
mkdir -p results

# Marca hora de início
START_TIME=$(date +%s)
echo ""
echo "Iniciando em: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Executa matriz de cenários
echo "Executando todos os cenários..."
python3 performance_tester.py --all-scenarios

# Calcula tempo total
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "========================================"
echo "  EXECUÇÃO CONCLUÍDA!"
echo "========================================"
echo "Tempo total: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo ""
echo "Resultados salvos em:"
echo "  - results/all_scenarios.json"
echo "  - results/all_scenarios.csv"
echo "  - results/consolidated_report.md"
echo "  - results/scenario_*.json (individuais)"
echo ""
echo "Para análise detalhada, execute:"
echo "  python3 analyze_results.py"
echo "========================================"

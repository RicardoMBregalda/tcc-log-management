#!/bin/bash

# Script de Comparação: Python vs Go
# Compara os resultados dos testes Python e Go

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Paths
GO_RESULTS="results_go"
PYTHON_RESULTS="../../src/results"
COMPARISON_DIR="comparison"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           Performance Comparison: Python vs Go           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if results exist
if [ ! -d "$GO_RESULTS" ]; then
    echo -e "${RED}❌ Resultados Go não encontrados em $GO_RESULTS${NC}"
    echo -e "${YELLOW}Execute primeiro: ./run_performance_tests.sh${NC}"
    exit 1
fi

if [ ! -d "$PYTHON_RESULTS" ]; then
    echo -e "${RED}❌ Resultados Python não encontrados em $PYTHON_RESULTS${NC}"
    echo -e "${YELLOW}Execute primeiro: cd ../../src && python performance_tester.py${NC}"
    exit 1
fi

# Create comparison directory
mkdir -p "$COMPARISON_DIR"

echo -e "${YELLOW}📊 Gerando comparação...${NC}\n"

# Create comparison report
REPORT="$COMPARISON_DIR/comparison_report.md"

cat > "$REPORT" << 'EOF'
# Performance Comparison: Python vs Go

**Data da Comparação:** $(date '+%Y-%m-%d %H:%M:%S')

## 📋 Resumo

Esta comparação analisa o desempenho da API implementada em Python (Flask) versus Go (Gin), ambas utilizando a arquitetura híbrida MongoDB + Hyperledger Fabric.

## 🎯 Metodologia

- **Mesmos Cenários:** Ambas as implementações executaram os mesmos cenários de teste definidos em `test_scenarios.json`
- **Mesmas Métricas:** Throughput, latência (P50/P95/P99), uso de CPU, memória e disco
- **Ambiente Controlado:** Testes executados na mesma máquina com MongoDB e Fabric rodando

## 📊 Resultados por Cenário

### Cenário S1: 10k logs @ 100/s (Baixo volume, baixa taxa)

| Métrica | Python | Go | Diferença |
|---------|--------|----|-----------| 
| Throughput (logs/s) | - | - | - |
| Latência Média (ms) | - | - | - |
| P95 Latency (ms) | - | - | - |
| P99 Latency (ms) | - | - | - |
| CPU Médio (%) | - | - | - |
| Memória Média (MB) | - | - | - |

### Cenário S5: 100k logs @ 1k/s (Volume médio, taxa média)

| Métrica | Python | Go | Diferença |
|---------|--------|----|-----------| 
| Throughput (logs/s) | - | - | - |
| Latência Média (ms) | - | - | - |
| P95 Latency (ms) | - | - | - |
| P99 Latency (ms) | - | - | - |
| CPU Médio (%) | - | - | - |
| Memória Média (MB) | - | - | - |

### Cenário S9: 1M logs @ 10k/s (Alto volume, alta taxa)

| Métrica | Python | Go | Diferença |
|---------|--------|----|-----------| 
| Throughput (logs/s) | - | - | - |
| Latência Média (ms) | - | - | - |
| P95 Latency (ms) | - | - | - |
| P99 Latency (ms) | - | - | - |
| CPU Médio (%) | - | - | - |
| Memória Média (MB) | - | - | - |

## 📈 Análise Geral

### Throughput
- **Vencedor:** 
- **Diferença Média:** 

### Latência
- **Menor Latência:** 
- **P99 mais baixo:** 

### Recursos
- **Menor uso de CPU:** 
- **Menor uso de Memória:** 

## 🎯 Conclusões

### Vantagens do Python
1. 
2. 
3. 

### Vantagens do Go
1. 
2. 
3. 

### Recomendações

**Use Python quando:**
- 

**Use Go quando:**
- 

## 📝 Notas

- Todos os testes foram executados com as mesmas configurações
- MongoDB e Fabric estavam em estado limpo antes de cada teste
- Resultados podem variar dependendo do hardware e carga do sistema
EOF

# Replace date placeholder
sed -i "s/\$(date '+%Y-%m-%d %H:%M:%S')/$(date '+%Y-%m-%d %H:%M:%S')/" "$REPORT"

echo -e "${GREEN}✅ Relatório de comparação gerado: $REPORT${NC}"
echo ""

# Compare CSVs if they exist
if [ -f "$GO_RESULTS/results.csv" ] && [ -f "$PYTHON_RESULTS/performance_results.csv" ]; then
    echo -e "${YELLOW}📋 Comparando CSVs...${NC}"
    
    # Extract headers
    GO_HEADER=$(head -n 1 "$GO_RESULTS/results.csv")
    PY_HEADER=$(head -n 1 "$PYTHON_RESULTS/performance_results.csv")
    
    echo -e "${CYAN}Go CSV:${NC}"
    head -n 3 "$GO_RESULTS/results.csv"
    echo ""
    
    echo -e "${CYAN}Python CSV:${NC}"
    head -n 3 "$PYTHON_RESULTS/performance_results.csv"
    echo ""
fi

# Compare specific scenarios
echo -e "${YELLOW}🔍 Comparando cenários individuais...${NC}"
echo ""

for scenario in S1 S5 S9; do
    GO_FILE="$GO_RESULTS/${scenario}_insert.json"
    PY_FILE="$PYTHON_RESULTS/scenario_${scenario}_hybrid.json"
    
    if [ -f "$GO_FILE" ] && [ -f "$PY_FILE" ]; then
        echo -e "${CYAN}Cenário $scenario:${NC}"
        
        # Extract throughput
        GO_THROUGHPUT=$(jq -r '.throughput_logs_per_sec' "$GO_FILE" 2>/dev/null || echo "N/A")
        PY_THROUGHPUT=$(jq -r '.throughput_logs_per_sec' "$PY_FILE" 2>/dev/null || echo "N/A")
        
        echo "  Throughput: Go=$GO_THROUGHPUT logs/s | Python=$PY_THROUGHPUT logs/s"
        
        # Extract P95 latency
        GO_P95=$(jq -r '.p95_latency_ms' "$GO_FILE" 2>/dev/null || echo "N/A")
        PY_P95=$(jq -r '.p95_latency_ms' "$PY_FILE" 2>/dev/null || echo "N/A")
        
        echo "  P95 Latency: Go=$GO_P95 ms | Python=$PY_P95 ms"
        echo ""
    else
        echo -e "${YELLOW}⚠️  Cenário $scenario: arquivos não encontrados${NC}"
    fi
done

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                  Comparação Concluída!                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}📁 Resultados salvos em: $COMPARISON_DIR${NC}"
echo -e "${GREEN}📄 Relatório: $REPORT${NC}"
echo ""
echo -e "${YELLOW}💡 Para análise detalhada:${NC}"
echo "   cat $REPORT"
echo "   diff $GO_RESULTS/results.csv $PYTHON_RESULTS/performance_results.csv"
echo ""

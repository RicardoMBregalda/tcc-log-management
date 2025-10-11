#!/bin/bash
set -e

SCRIPTS_DIR="/root/tcc-log-management/testing/scripts"

echo "========================================================================"
echo "🚀 APLICANDO TODAS AS OTIMIZAÇÕES EXTREMAS"
echo "========================================================================"
echo ""
echo "Este script irá aplicar:"
echo "  1. Otimizações ultra-agressivas do Fabric (BatchTimeout, TickInterval)"
echo "  2. Desabilitar modo DEBUG (logs WARNING)"
echo "  3. Aumentar recursos Docker (CPU, RAM)"
echo "  4. Otimizar PostgreSQL (shared_buffers, work_mem)"
echo "  5. Otimizar Kernel Linux (rede, arquivos)"
echo ""
read -p "Deseja continuar? (s/N): " CONTINUE
if [ "$CONTINUE" != "s" ] && [ "$CONTINUE" != "S" ]; then
    echo "Operação cancelada"
    exit 0
fi

echo ""
echo "1️⃣  APLICANDO PERFIL ULTRA-AGRESSIVO..."
cd "$SCRIPTS_DIR"
bash apply_aggressive_optimizations.sh ultra-aggressive

echo ""
echo "2️⃣  OTIMIZANDO POSTGRESQL..."
bash optimize_postgres.sh

echo ""
echo "3️⃣  OTIMIZANDO KERNEL..."
bash optimize_kernel.sh

echo ""
echo "========================================================================"
echo "✅ TODAS AS OTIMIZAÇÕES APLICADAS!"
echo "========================================================================"
echo ""
echo "📊 RESUMO DAS OTIMIZAÇÕES:"
echo ""
echo "┌─────────────────────────────────────┬──────────────┐"
echo "│ Componente                          │ Otimização   │"
echo "├─────────────────────────────────────┼──────────────┤"
echo "│ Fabric BatchTimeout                 │ 500ms → 200ms│"
echo "│ Fabric MaxMessageCount              │ 100 → 200    │"
echo "│ Fabric TickInterval                 │ 100ms → 50ms │"
echo "│ Fabric Logs                         │ INFO→WARNING │"
echo "│ Docker CPU per peer                 │ 2 cores      │"
echo "│ Docker RAM per peer                 │ 2GB          │"
echo "│ PostgreSQL shared_buffers           │ 512MB        │"
echo "│ PostgreSQL work_mem                 │ 16MB         │"
echo "│ Kernel somaxconn                    │ 4096         │"
echo "│ Connection Pool (PostgreSQL)        │ 5-50         │"
echo "│ Connection Pool (HTTP)              │ 20/50        │"
echo "└─────────────────────────────────────┴──────────────┘"
echo ""
echo "🎯 GANHOS ESPERADOS:"
echo "   Latência atual: 30-40ms"
echo "   Com otimizações: 10-20ms"
echo "   Throughput: 150-250 ops/s"
echo "   Redução total vs baseline: 94-97% (336ms → 15ms)"
echo ""
echo "📝 Próximos passos:"
echo "   1. Testar performance:"
echo "      cd /root/tcc-log-management/testing"
echo "      python3 performance_tester.py"
echo ""
echo "   2. Analisar resultados:"
echo "      python3 analyze_results.py"
echo ""
echo "========================================================================"

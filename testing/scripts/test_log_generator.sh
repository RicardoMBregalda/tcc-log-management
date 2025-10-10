#!/bin/bash
# Test Script para Log Generator
# Testa diferentes cenários de geração de logs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_GENERATOR="$TESTING_DIR/log_generator.py"

echo "========================================================================"
echo "🧪 TEST LOG GENERATOR - Teste de Geração de Logs"
echo "========================================================================"
echo ""

# Verifica se log_generator.py existe
if [ ! -f "$LOG_GENERATOR" ]; then
    echo "❌ Erro: log_generator.py não encontrado em $LOG_GENERATOR"
    exit 1
fi

echo "✅ Script encontrado: $LOG_GENERATOR"
echo ""

# Função para executar teste
run_test() {
    local test_name="$1"
    local description="$2"
    shift 2
    local args="$@"
    
    echo "========================================================================"
    echo "🔬 TESTE: $test_name"
    echo "📝 $description"
    echo "========================================================================"
    echo "Comando: python3 $LOG_GENERATOR $args"
    echo ""
    
    if python3 "$LOG_GENERATOR" $args; then
        echo ""
        echo "✅ $test_name - SUCESSO"
    else
        echo ""
        echo "❌ $test_name - FALHOU"
        return 1
    fi
    
    echo ""
    sleep 2
}

# ============================================================================
# TESTES
# ============================================================================

echo "Iniciando bateria de testes..."
echo ""
sleep 2

# Teste 1: Quantidade fixa pequena
run_test \
    "Teste 1: Quantidade Fixa" \
    "Gera 10 logs sequencialmente" \
    "-n 10"

# Teste 2: Cenário de carga baixa
run_test \
    "Teste 2: Carga Baixa" \
    "2 logs/segundo por 10 segundos (total: ~20 logs)" \
    "--rate 2 --duration 10"

# Teste 3: Cenário de carga média
run_test \
    "Teste 3: Carga Média" \
    "10 logs/segundo por 10 segundos (total: ~100 logs)" \
    "--rate 10 --duration 10"

# Teste 4: Cenário de carga alta
run_test \
    "Teste 4: Carga Alta" \
    "50 logs/segundo por 5 segundos (total: ~250 logs)" \
    "--rate 50 --duration 5"

# Teste 5: Modo simulação (sem Fabric)
run_test \
    "Teste 5: Modo Simulação" \
    "20 logs em modo simulação (sem enviar para Fabric)" \
    "-n 20 --no-fabric"

# ============================================================================
# RESUMO
# ============================================================================

echo "========================================================================"
echo "✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO"
echo "========================================================================"
echo ""
echo "📊 Resumo dos testes executados:"
echo "  1. ✅ Geração de quantidade fixa (10 logs)"
echo "  2. ✅ Carga baixa (2 logs/seg por 10s)"
echo "  3. ✅ Carga média (10 logs/seg por 10s)"
echo "  4. ✅ Carga alta (50 logs/seg por 5s)"
echo "  5. ✅ Modo simulação (20 logs sem Fabric)"
echo ""
echo "Total estimado: ~400 logs gerados e sincronizados"
echo ""
echo "🔍 Para verificar os logs no PostgreSQL:"
echo "   docker exec -it postgres-primary psql -U loguser -d logdb -c \"SELECT COUNT(*) FROM logs;\""
echo ""
echo "🔍 Para verificar sincronização:"
echo "   docker exec -it postgres-primary psql -U loguser -d logdb -c \"SELECT sync_status, COUNT(*) FROM sync_control GROUP BY sync_status;\""
echo ""

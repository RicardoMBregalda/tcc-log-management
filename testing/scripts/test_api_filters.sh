#!/bin/bash
# Script de Teste da API - Verifica filtros de consulta

set -e

API_URL="http://localhost:5000"

echo "========================================================================"
echo "🧪 TESTE DA API - Consulta de Logs"
echo "========================================================================"
echo ""

# Verifica se API está rodando
echo "1️⃣  Verificando se API está rodando..."
if curl -s "${API_URL}/health" > /dev/null 2>&1; then
    echo "✅ API está respondendo"
else
    echo "❌ API não está respondendo em ${API_URL}"
    echo "   Execute: python3 api_server.py"
    exit 1
fi

echo ""
echo "2️⃣  Criando logs de teste..."

# Cria 5 logs de diferentes sources
python3 insert_and_sync_log.py "api-gateway" "INFO" "Requisição processada" > /dev/null 2>&1
python3 insert_and_sync_log.py "api-gateway" "ERROR" "Erro de autenticação" > /dev/null 2>&1
python3 insert_and_sync_log.py "user-service" "INFO" "Usuário criado" > /dev/null 2>&1
python3 insert_and_sync_log.py "auth-service" "WARNING" "Token expirando" > /dev/null 2>&1
python3 insert_and_sync_log.py "api-gateway" "WARNING" "Rate limit atingido" > /dev/null 2>&1

echo "✅ 5 logs criados (3 de api-gateway, 1 de user-service, 1 de auth-service)"

echo ""
echo "========================================================================"
echo "3️⃣  TESTANDO CONSULTAS"
echo "========================================================================"

# Teste 1: Todos os logs
echo ""
echo "📊 Teste 1: GET /logs (todos os logs)"
echo "----------------------------------------------------------------------"
RESPONSE=$(curl -s "${API_URL}/logs")
TOTAL=$(echo "$RESPONSE" | jq -r '.count')
echo "Resultado: $TOTAL logs encontrados"
echo ""

# Teste 2: Filtro por source=api-gateway
echo "📊 Teste 2: GET /logs?source=api-gateway"
echo "----------------------------------------------------------------------"
RESPONSE=$(curl -s "${API_URL}/logs?source=api-gateway")
COUNT=$(echo "$RESPONSE" | jq -r '.count')
SOURCES=$(echo "$RESPONSE" | jq -r '.logs[].Source' | sort | uniq)

echo "Resultado: $COUNT logs encontrados"
echo "Sources retornadas: $SOURCES"

if [ "$COUNT" -ge 3 ]; then
    echo "✅ Filtro funcionando corretamente"
else
    echo "⚠️  Esperado >= 3 logs de api-gateway, encontrado: $COUNT"
fi
echo ""

# Teste 3: Filtro com erro de digitação (souce)
echo "📊 Teste 3: GET /logs?souce=api-gateway (erro de digitação)"
echo "----------------------------------------------------------------------"
RESPONSE=$(curl -s "${API_URL}/logs?souce=api-gateway")
COUNT=$(echo "$RESPONSE" | jq -r '.count')

echo "Resultado: $COUNT logs encontrados"

if [ "$COUNT" -ge 3 ]; then
    echo "✅ Tolerância a erro de digitação funcionando!"
else
    echo "⚠️  Filtro com 'souce' não funcionou"
fi
echo ""

# Teste 4: Filtro por level=ERROR
echo "📊 Teste 4: GET /logs?level=ERROR"
echo "----------------------------------------------------------------------"
RESPONSE=$(curl -s "${API_URL}/logs?level=ERROR")
COUNT=$(echo "$RESPONSE" | jq -r '.count')
LEVELS=$(echo "$RESPONSE" | jq -r '.logs[].Level' | sort | uniq)

echo "Resultado: $COUNT logs encontrados"
echo "Níveis retornados: $LEVELS"

if [ "$COUNT" -ge 1 ]; then
    echo "✅ Filtro por nível funcionando"
else
    echo "⚠️  Esperado >= 1 log ERROR, encontrado: $COUNT"
fi
echo ""

# Teste 5: Filtro por source=user-service
echo "📊 Teste 5: GET /logs?source=user-service"
echo "----------------------------------------------------------------------"
RESPONSE=$(curl -s "${API_URL}/logs?source=user-service")
COUNT=$(echo "$RESPONSE" | jq -r '.count')

echo "Resultado: $COUNT logs encontrados"

if [ "$COUNT" -ge 1 ]; then
    echo "✅ Filtro para user-service funcionando"
else
    echo "⚠️  Esperado >= 1 log de user-service, encontrado: $COUNT"
fi
echo ""

# Teste 6: Limite de resultados
echo "📊 Teste 6: GET /logs?limit=2"
echo "----------------------------------------------------------------------"
RESPONSE=$(curl -s "${API_URL}/logs?limit=2")
COUNT=$(echo "$RESPONSE" | jq -r '.count')

echo "Resultado: $COUNT logs encontrados"

if [ "$COUNT" -eq 2 ]; then
    echo "✅ Limite funcionando corretamente"
else
    echo "⚠️  Esperado 2 logs, encontrado: $COUNT"
fi
echo ""

# Teste 7: Logs detalhados de api-gateway
echo "📊 Teste 7: Logs detalhados de api-gateway"
echo "----------------------------------------------------------------------"
RESPONSE=$(curl -s "${API_URL}/logs?source=api-gateway")
echo "$RESPONSE" | jq '.logs[] | {id: .ID, source: .Source, level: .Level, message: .Message}'
echo ""

echo "========================================================================"
echo "✅ TESTES CONCLUÍDOS"
echo "========================================================================"
echo ""
echo "💡 Dicas de uso:"
echo "   GET /logs                       # Todos os logs"
echo "   GET /logs?source=api-gateway    # Logs de api-gateway"
echo "   GET /logs?level=ERROR           # Logs de nível ERROR"
echo "   GET /logs?limit=10              # Primeiros 10 logs"
echo ""
echo "   Combinações:"
echo "   GET /logs?source=auth-service&limit=5"
echo ""
echo "🌐 Teste no navegador:"
echo "   ${API_URL}/logs"
echo "   ${API_URL}/logs?source=api-gateway"
echo ""

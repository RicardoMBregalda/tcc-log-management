#!/bin/bash

# Script de teste rápido da API MongoDB + Fabric

echo "🧪 Testando API MongoDB + Fabric"
echo "=================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função de teste
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -n "📝 $description... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "http://localhost:5001$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "http://localhost:5001$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $http_code)"
        if [ ! -z "$body" ]; then
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
        fi
    else
        echo -e "${RED}❌ FALHOU${NC} (HTTP $http_code)"
        echo "$body"
        return 1
    fi
    
    echo ""
}

# Verificar se API está rodando
if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo -e "${RED}❌ API não está rodando!${NC}"
    echo "   Execute: ./scripts/start_api_mongodb.sh"
    exit 1
fi

# Testes
echo "1️⃣  HEALTH CHECK"
test_endpoint "GET" "/health" "" "Verificando saúde da API"

echo "2️⃣  ESTATÍSTICAS"
test_endpoint "GET" "/stats" "" "Obtendo estatísticas"

echo "3️⃣  INSERÇÃO DE LOG"
log_data='{
    "id": "test-'$(date +%s)'",
    "timestamp": "'$(date -Iseconds)'",
    "level": "INFO",
    "source": "test-script",
    "message": "Teste de inserção via API MongoDB",
    "metadata": {"test": true}
}'
test_endpoint "POST" "/logs" "$log_data" "Inserindo novo log"

echo "4️⃣  LISTAGEM DE LOGS"
test_endpoint "GET" "/logs?limit=5" "" "Listando últimos 5 logs"

echo "5️⃣  BUSCA POR NÍVEL"
test_endpoint "GET" "/logs?level=INFO&limit=3" "" "Buscando logs INFO"

echo ""
echo "=================================="
echo -e "${GREEN}✅ Todos os testes concluídos!${NC}"
echo "=================================="

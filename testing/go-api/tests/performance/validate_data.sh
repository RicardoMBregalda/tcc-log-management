#!/bin/bash

# Script para validar dados no MongoDB e Hyperledger Fabric
# Autor: Ricardo M Bregalda
# Data: 2025-11-15

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Validação de Dados - MongoDB + Hyperledger Fabric    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ==================== PARÂMETROS ====================

SOURCE_FILTER="${1:-test-service}"  # Filtro de source (padrão: test-service)
SAMPLE_SIZE="${2:-10}"              # Quantidade de logs para verificar

echo -e "${CYAN}📋 Configuração:${NC}"
echo "   Source filter: $SOURCE_FILTER"
echo "   Sample size: $SAMPLE_SIZE logs"
echo ""

# ==================== MONGODB ====================

echo -e "${YELLOW}[1/3] Verificando MongoDB...${NC}"

# Contar total de logs
MONGO_TOTAL=$(docker exec mongo mongosh logdb --quiet --eval "db.logs.countDocuments({source: /^${SOURCE_FILTER}/})" 2>/dev/null || echo "0")

echo -e "   Total de logs no MongoDB: ${GREEN}${MONGO_TOTAL}${NC}"

if [ "$MONGO_TOTAL" = "0" ]; then
    echo -e "${RED}   ❌ Nenhum log encontrado no MongoDB${NC}"
    echo ""
else
    echo -e "${GREEN}   ✅ MongoDB contém logs${NC}"
    
    # Mostrar amostra
    echo -e "\n${CYAN}   📄 Amostra de logs (primeiros 3):${NC}"
    docker exec mongo mongosh logdb --quiet --eval "
        db.logs.find({source: /^${SOURCE_FILTER}/})
        .limit(3)
        .forEach(log => {
            print('      ID: ' + log.id);
            print('      Source: ' + log.source);
            print('      Level: ' + log.level);
            print('      Message: ' + log.message.substring(0, 50) + '...');
            print('      Timestamp: ' + log.timestamp);
            print('      ---');
        })
    " 2>/dev/null
    echo ""
fi

# ==================== HYPERLEDGER FABRIC ====================

echo -e "${YELLOW}[2/3] Verificando Hyperledger Fabric...${NC}"

# Verificar se peer está rodando
if ! docker ps | grep -q "peer0.org1.example.com"; then
    echo -e "${RED}   ❌ Peer0 não está rodando${NC}"
    echo -e "${YELLOW}   💡 Inicie a rede Fabric: cd hybrid-architecture/fabric-network && ./start-network.sh${NC}"
    echo ""
    FABRIC_OK=false
else
    echo -e "${GREEN}   ✅ Peer0 está rodando${NC}"
    FABRIC_OK=true
fi

if [ "$FABRIC_OK" = true ]; then
    # Buscar logs de amostra do MongoDB para validar no Fabric
    echo -e "\n${CYAN}   🔍 Buscando IDs de logs no MongoDB para validar no Fabric...${NC}"
    
    LOG_IDS=$(docker exec mongo mongosh logdb --quiet --eval "
        db.logs.find({source: /^${SOURCE_FILTER}/})
        .limit(${SAMPLE_SIZE})
        .toArray()
        .map(log => log.id)
        .join(',')
    " 2>/dev/null)
    
    if [ -z "$LOG_IDS" ]; then
        echo -e "${YELLOW}   ⚠️  Nenhum log encontrado para validar${NC}"
    else
        # Converter para array
        IFS=',' read -ra LOG_ID_ARRAY <<< "$LOG_IDS"
        
        echo -e "   Validando ${#LOG_ID_ARRAY[@]} logs no Fabric..."
        echo ""
        
        FABRIC_FOUND=0
        FABRIC_NOT_FOUND=0
        
        for LOG_ID in "${LOG_ID_ARRAY[@]}"; do
            # Remover espaços e aspas
            LOG_ID=$(echo "$LOG_ID" | tr -d ' "')
            
            if [ -z "$LOG_ID" ]; then
                continue
            fi
            
            # Consultar log no Fabric via peer chaincode query
            RESULT=$(docker exec peer0.org1.example.com peer chaincode query \
                -C logchannel \
                -n logchaincode \
                -c "{\"function\":\"GetLog\",\"Args\":[\"$LOG_ID\"]}" \
                2>/dev/null || echo "ERROR")
            
            if [[ "$RESULT" == *"Error"* ]] || [[ "$RESULT" == "ERROR" ]]; then
                echo -e "      ${RED}❌${NC} Log $LOG_ID não encontrado no Fabric"
                ((FABRIC_NOT_FOUND++))
            else
                echo -e "      ${GREEN}✅${NC} Log $LOG_ID encontrado no Fabric"
                ((FABRIC_FOUND++))
            fi
        done
        
        echo ""
        echo -e "   ${CYAN}Resumo da validação Fabric:${NC}"
        echo -e "      Encontrados: ${GREEN}${FABRIC_FOUND}${NC}/${#LOG_ID_ARRAY[@]}"
        echo -e "      Não encontrados: ${RED}${FABRIC_NOT_FOUND}${NC}/${#LOG_ID_ARRAY[@]}"
        
        # Calcular taxa de consistência
        if [ ${#LOG_ID_ARRAY[@]} -gt 0 ]; then
            CONSISTENCY_RATE=$(echo "scale=2; $FABRIC_FOUND * 100 / ${#LOG_ID_ARRAY[@]}" | bc)
            echo -e "      Taxa de consistência: ${CYAN}${CONSISTENCY_RATE}%${NC}"
        fi
    fi
fi

echo ""

# ==================== COMPARAÇÃO E ESTATÍSTICAS ====================

echo -e "${YELLOW}[3/3] Estatísticas e Comparação...${NC}"

# Estatísticas do MongoDB
echo -e "\n${CYAN}📊 MongoDB - Estatísticas por Source:${NC}"
docker exec mongo mongosh logdb --quiet --eval "
    db.logs.aggregate([
        { \$match: { source: /^${SOURCE_FILTER}/ } },
        { \$group: {
            _id: '\$source',
            count: { \$sum: 1 },
            levels: { \$addToSet: '\$level' }
        }},
        { \$sort: { count: -1 } },
        { \$limit: 5 }
    ]).forEach(result => {
        print('   ' + result._id + ': ' + result.count + ' logs (' + result.levels.join(', ') + ')');
    })
" 2>/dev/null

# Estatísticas por nível
echo -e "\n${CYAN}📊 MongoDB - Estatísticas por Level:${NC}"
docker exec mongo mongosh logdb --quiet --eval "
    db.logs.aggregate([
        { \$match: { source: /^${SOURCE_FILTER}/ } },
        { \$group: {
            _id: '\$level',
            count: { \$sum: 1 }
        }},
        { \$sort: { count: -1 } }
    ]).forEach(result => {
        print('   ' + result._id + ': ' + result.count + ' logs');
    })
" 2>/dev/null

# Timestamp range
echo -e "\n${CYAN}📊 MongoDB - Intervalo de Tempo:${NC}"
docker exec mongo mongosh logdb --quiet --eval "
    const result = db.logs.aggregate([
        { \$match: { source: /^${SOURCE_FILTER}/ } },
        { \$group: {
            _id: null,
            first: { \$min: '\$timestamp' },
            last: { \$max: '\$timestamp' },
            count: { \$sum: 1 }
        }}
    ]).toArray()[0];
    
    if (result) {
        print('   Primeiro log: ' + result.first);
        print('   Último log: ' + result.last);
        print('   Total: ' + result.count + ' logs');
    }
" 2>/dev/null

echo ""

# ==================== RESUMO FINAL ====================

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     RESUMO FINAL                          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$MONGO_TOTAL" != "0" ]; then
    echo -e "${GREEN}✅ MongoDB:${NC} $MONGO_TOTAL logs armazenados"
else
    echo -e "${RED}❌ MongoDB:${NC} Nenhum log encontrado"
fi

if [ "$FABRIC_OK" = true ]; then
    if [ "$FABRIC_FOUND" -gt 0 ]; then
        echo -e "${GREEN}✅ Fabric:${NC} $FABRIC_FOUND/$SAMPLE_SIZE logs verificados (${CONSISTENCY_RATE}% consistente)"
    else
        echo -e "${YELLOW}⚠️  Fabric:${NC} Logs não verificados ou não encontrados"
    fi
else
    echo -e "${RED}❌ Fabric:${NC} Peer não está rodando"
fi

echo ""

# Verificar consistência geral
if [ "$MONGO_TOTAL" != "0" ] && [ "$FABRIC_OK" = true ] && [ "$FABRIC_FOUND" -gt 0 ]; then
    if (( $(echo "$CONSISTENCY_RATE >= 95" | bc -l) )); then
        echo -e "${GREEN}🎉 Sistema está consistente! MongoDB e Fabric sincronizados.${NC}"
    elif (( $(echo "$CONSISTENCY_RATE >= 80" | bc -l) )); then
        echo -e "${YELLOW}⚠️  Sistema parcialmente consistente. Algumas inconsistências detectadas.${NC}"
    else
        echo -e "${RED}❌ Sistema inconsistente! Verificar sincronização entre MongoDB e Fabric.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Não foi possível validar consistência completa.${NC}"
fi

echo ""
echo -e "${CYAN}💡 Dicas:${NC}"
echo "   - Para verificar logs específicos: $0 <source-pattern> <sample-size>"
echo "   - Exemplo: $0 test-service 20"
echo "   - Para limpar dados de teste: docker exec mongo mongosh logdb --eval \"db.logs.deleteMany({source: /^test-service/})\""
echo ""

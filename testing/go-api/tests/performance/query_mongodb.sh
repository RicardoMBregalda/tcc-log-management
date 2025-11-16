#!/bin/bash

# Script para consultar logs no MongoDB
# Uso: ./query_mongodb.sh [opções]

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

show_help() {
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  -i, --id <log_id>        Buscar por ID específico"
    echo "  -s, --source <pattern>   Buscar por source (regex)"
    echo "  -l, --level <level>      Buscar por level (DEBUG, INFO, WARNING, ERROR)"
    echo "  -n, --limit <num>        Limitar resultados (padrão: 10)"
    echo "  -c, --count              Apenas contar logs"
    echo "  --stats                  Mostrar estatísticas"
    echo "  -h, --help               Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 --id log-123456789                    # Buscar log específico"
    echo "  $0 --source test-service --limit 5       # 5 logs de test-service"
    echo "  $0 --level ERROR --count                 # Contar logs de erro"
    echo "  $0 --stats                               # Estatísticas gerais"
    exit 0
}

# Valores padrão
LOG_ID=""
SOURCE=""
LEVEL=""
LIMIT=10
COUNT_ONLY=false
SHOW_STATS=false

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--id)
            LOG_ID="$2"
            shift 2
            ;;
        -s|--source)
            SOURCE="$2"
            shift 2
            ;;
        -l|--level)
            LEVEL="$2"
            shift 2
            ;;
        -n|--limit)
            LIMIT="$2"
            shift 2
            ;;
        -c|--count)
            COUNT_ONLY=true
            shift
            ;;
        --stats)
            SHOW_STATS=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Opção desconhecida: $1"
            show_help
            ;;
    esac
done

# Mostrar estatísticas
if [ "$SHOW_STATS" = true ]; then
    echo -e "${BLUE}📊 Estatísticas do MongoDB${NC}"
    echo ""
    
    echo -e "${CYAN}Total de logs:${NC}"
    docker exec mongo mongosh logdb --quiet --eval "print(db.logs.countDocuments({}))"
    
    echo -e "\n${CYAN}Por Source:${NC}"
    docker exec mongo mongosh logdb --quiet --eval "
        db.logs.aggregate([
            { \$group: { _id: '\$source', count: { \$sum: 1 } }},
            { \$sort: { count: -1 } },
            { \$limit: 10 }
        ]).forEach(r => print('  ' + r._id + ': ' + r.count))
    "
    
    echo -e "\n${CYAN}Por Level:${NC}"
    docker exec mongo mongosh logdb --quiet --eval "
        db.logs.aggregate([
            { \$group: { _id: '\$level', count: { \$sum: 1 } }},
            { \$sort: { count: -1 } }
        ]).forEach(r => print('  ' + r._id + ': ' + r.count))
    "
    
    echo -e "\n${CYAN}Intervalo de Tempo:${NC}"
    docker exec mongo mongosh logdb --quiet --eval "
        const result = db.logs.aggregate([
            { \$group: {
                _id: null,
                first: { \$min: '\$timestamp' },
                last: { \$max: '\$timestamp' }
            }}
        ]).toArray()[0];
        if (result) {
            print('  Primeiro: ' + result.first);
            print('  Último: ' + result.last);
        }
    "
    
    exit 0
fi

# Construir query
QUERY="{"

if [ -n "$LOG_ID" ]; then
    QUERY="${QUERY}id: '$LOG_ID'"
else
    FILTERS=()
    
    if [ -n "$SOURCE" ]; then
        FILTERS+=("source: /$SOURCE/")
    fi
    
    if [ -n "$LEVEL" ]; then
        FILTERS+=("level: '$LEVEL'")
    fi
    
    if [ ${#FILTERS[@]} -gt 0 ]; then
        QUERY="${QUERY}$(IFS=, ; echo "${FILTERS[*]}")"
    fi
fi

QUERY="${QUERY}}"

echo -e "${BLUE}🔍 Consultando MongoDB${NC}"
echo -e "${CYAN}Query: $QUERY${NC}"
echo ""

# Executar query
if [ "$COUNT_ONLY" = true ]; then
    COUNT=$(docker exec mongo mongosh logdb --quiet --eval "db.logs.countDocuments($QUERY)")
    echo -e "${GREEN}Total: $COUNT logs${NC}"
else
    docker exec mongo mongosh logdb --quiet --eval "
        db.logs.find($QUERY)
            .limit($LIMIT)
            .forEach(log => {
                print('─'.repeat(60));
                print('ID: ' + log.id);
                print('Source: ' + log.source);
                print('Level: ' + log.level);
                print('Message: ' + log.message);
                print('Timestamp: ' + log.timestamp);
                if (log.metadata) {
                    print('Metadata: ' + JSON.stringify(log.metadata));
                }
            })
    "
fi

echo ""
echo -e "${YELLOW}💡 Dica: Use --help para ver todas as opções${NC}"

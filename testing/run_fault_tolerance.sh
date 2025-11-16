#!/bin/bash

# Script de execução dos testes de tolerância a falhas
# Autor: Ricardo M Bregalda
# Data: 2025-11-15

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   TESTES DE TOLERÂNCIA A FALHAS - TCC LOG MANAGEMENT           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==================== VERIFICAÇÕES PRÉ-TESTE ====================

echo -e "${YELLOW}[1/5] Verificando dependências Python...${NC}"
if ! python3 -c "import requests, psycopg2, pymongo" 2>/dev/null; then
    echo -e "${RED}❌ Dependências faltando. Instalando...${NC}"
    pip install requests psycopg2-binary pymongo
else
    echo -e "${GREEN}✅ Dependências OK${NC}"
fi
echo ""

echo -e "${YELLOW}[2/5] Verificando containers Docker...${NC}"

# Verificar containers híbridos
echo -e "  ${BLUE}Arquitetura Híbrida:${NC}"
HYBRID_CONTAINERS=("mongo" "peer0.org1.example.com" "peer1.org1.example.com" "orderer.example.com")
HYBRID_OK=true

for container in "${HYBRID_CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "    ✅ ${container}"
    else
        echo -e "    ${RED}❌ ${container} não está rodando${NC}"
        HYBRID_OK=false
    fi
done

# Verificar containers tradicionais
echo -e "  ${BLUE}Arquitetura Tradicional:${NC}"
TRADITIONAL_CONTAINERS=("postgres-primary" "postgres-standby")
TRADITIONAL_OK=true

for container in "${TRADITIONAL_CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "    ✅ ${container}"
    else
        echo -e "    ${RED}❌ ${container} não está rodando${NC}"
        TRADITIONAL_OK=false
    fi
done
echo ""

# Se algum container não estiver rodando, oferecer para iniciar
if [ "$HYBRID_OK" = false ] || [ "$TRADITIONAL_OK" = false ]; then
    echo -e "${YELLOW}⚠️  Alguns containers não estão rodando.${NC}"
    echo ""
    echo "Opções:"
    echo "  1) Iniciar automaticamente (recomendado)"
    echo "  2) Continuar assim mesmo (pode falhar)"
    echo "  3) Cancelar e iniciar manualmente"
    echo ""
    read -p "Escolha [1-3]: " choice
    
    case $choice in
        1)
            echo -e "${BLUE}Iniciando containers...${NC}"
            
            if [ "$HYBRID_OK" = false ]; then
                echo -e "  ${YELLOW}Iniciando arquitetura híbrida...${NC}"
                cd ../hybrid-architecture/fabric-network
                ./start-network.sh
                cd "$SCRIPT_DIR"
                
                echo -e "  ${YELLOW}Iniciando API híbrida...${NC}"
                ./scripts/start_api.sh
                sleep 5
            fi
            
            if [ "$TRADITIONAL_OK" = false ]; then
                echo -e "  ${YELLOW}Iniciando arquitetura tradicional...${NC}"
                cd ../traditional-architecture
                ./start-traditional.sh
                cd "$SCRIPT_DIR"
                sleep 5
            fi
            
            echo -e "${GREEN}✅ Containers iniciados${NC}"
            echo ""
            ;;
        2)
            echo -e "${YELLOW}⚠️  Continuando sem iniciar containers...${NC}"
            echo ""
            ;;
        3)
            echo -e "${YELLOW}Cancelado. Inicie os containers manualmente:${NC}"
            echo ""
            echo "Híbrida:"
            echo "  cd ../hybrid-architecture/fabric-network && ./start-network.sh"
            echo "  cd ../../testing && ./scripts/start_api.sh"
            echo ""
            echo "Tradicional:"
            echo "  cd ../traditional-architecture && ./start-traditional.sh"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Opção inválida${NC}"
            exit 1
            ;;
    esac
fi

echo -e "${YELLOW}[3/5] Verificando API híbrida...${NC}"
API_URL="http://localhost:5001/health"
MAX_RETRIES=5
RETRY=0

while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s -f "$API_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API híbrida respondendo${NC}"
        break
    else
        RETRY=$((RETRY + 1))
        if [ $RETRY -lt $MAX_RETRIES ]; then
            echo -e "  ${YELLOW}Tentativa ${RETRY}/${MAX_RETRIES}... Aguardando 3s${NC}"
            sleep 3
        else
            echo -e "${RED}❌ API não responde após ${MAX_RETRIES} tentativas${NC}"
            echo -e "${YELLOW}Iniciando API...${NC}"
            ./scripts/start_api.sh
            sleep 5
        fi
    fi
done
echo ""

echo -e "${YELLOW}[4/5] Verificando conectividade PostgreSQL...${NC}"

# Primary
if docker exec postgres-primary psql -U loguser -d logdb -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "  ✅ PostgreSQL Primary (porta 5432)"
else
    echo -e "  ${RED}❌ PostgreSQL Primary não responde${NC}"
fi

# Standby
if docker exec postgres-standby psql -U loguser -d logdb -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "  ✅ PostgreSQL Standby (porta 5433)"
else
    echo -e "  ${RED}❌ PostgreSQL Standby não responde${NC}"
fi
echo ""

echo -e "${YELLOW}[5/5] Verificando conectividade MongoDB...${NC}"
if docker exec mongo mongosh --quiet --eval "db.adminCommand('ping').ok" 2>/dev/null | grep -q "1"; then
    echo -e "${GREEN}✅ MongoDB respondendo${NC}"
else
    echo -e "${RED}❌ MongoDB não responde${NC}"
fi
echo ""

# ==================== BACKUP DE RESULTADOS ANTERIORES ====================

if [ -f "results/fault_tolerance_report.json" ]; then
    echo -e "${YELLOW}📦 Fazendo backup de resultados anteriores...${NC}"
    BACKUP_DIR="results/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    mv results/fault_tolerance_report.json "$BACKUP_DIR/" 2>/dev/null || true
    mv results/fault_tolerance_report.md "$BACKUP_DIR/" 2>/dev/null || true
    
    echo -e "${GREEN}✅ Backup salvo em: $BACKUP_DIR${NC}"
    echo ""
fi

# ==================== EXECUTAR TESTES ====================

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    INICIANDO TESTES                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}⏱️  Duração estimada: 15-20 minutos${NC}"
echo -e "${YELLOW}📊 Cenários: 3 (falha primary, falha réplica, falha rede)${NC}"
echo -e "${YELLOW}🏗️  Arquiteturas: 2 (híbrida, tradicional)${NC}"
echo ""
echo -e "${BLUE}Os testes vão:${NC}"
echo "  1. Injetar falhas nos containers Docker (stop/pause)"
echo "  2. Medir tempo de detecção e recuperação"
echo "  3. Verificar perda de dados"
echo "  4. Avaliar disponibilidade durante falhas"
echo ""

read -p "Pressione ENTER para continuar ou Ctrl+C para cancelar..."
echo ""

# Executar testes
cd tests
if python3 test_fault_tolerance.py; then
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   TESTES CONCLUÍDOS COM SUCESSO                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Mostrar resumo
    if [ -f "../results/fault_tolerance_report.json" ]; then
        echo -e "${BLUE}📊 Resumo dos Resultados:${NC}"
        echo ""
        
        # Extrair pontuação do JSON usando Python
        python3 << 'EOF'
import json

with open('../results/fault_tolerance_report.json', 'r') as f:
    report = json.load(f)

summary = report['summary']
hybrid_total = sum(summary['hybrid_wins'].values())
traditional_total = sum(summary['traditional_wins'].values())

print(f"  🏆 PONTUAÇÃO GERAL:")
print(f"     Híbrida:     {hybrid_total} pontos")
print(f"     Tradicional: {traditional_total} pontos")
print()

print(f"  📈 VITÓRIAS POR MÉTRICA:")
print(f"     Detecção:        Híbrida {summary['hybrid_wins']['detection']} × {summary['traditional_wins']['detection']} Tradicional")
print(f"     Recuperação:     Híbrida {summary['hybrid_wins']['recovery']} × {summary['traditional_wins']['recovery']} Tradicional")
print(f"     Perda de Dados:  Híbrida {summary['hybrid_wins']['data_loss']} × {summary['traditional_wins']['data_loss']} Tradicional")
print(f"     Disponibilidade: Híbrida {summary['hybrid_wins']['availability']} × {summary['traditional_wins']['availability']} Tradicional")
print()

if hybrid_total > traditional_total:
    print("  🎯 VENCEDOR: Arquitetura Híbrida")
elif traditional_total > hybrid_total:
    print("  🎯 VENCEDOR: Arquitetura Tradicional")
else:
    print("  🤝 RESULTADO: Empate Técnico")
EOF
        
        echo ""
        echo -e "${BLUE}📁 Relatórios gerados:${NC}"
        echo "  - results/fault_tolerance_report.json (dados completos)"
        echo "  - results/fault_tolerance_report.md (relatório formatado)"
        echo ""
        
        # Oferecer visualizar relatório
        echo -e "${YELLOW}Deseja visualizar o relatório Markdown? [s/N]${NC}"
        read -p "> " view_report
        
        if [[ "$view_report" =~ ^[Ss]$ ]]; then
            if command -v bat &> /dev/null; then
                bat ../results/fault_tolerance_report.md
            elif command -v less &> /dev/null; then
                less ../results/fault_tolerance_report.md
            else
                cat ../results/fault_tolerance_report.md
            fi
        fi
    fi
else
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                     TESTES FALHARAM                              ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Verifique os logs acima para identificar o problema.${NC}"
    echo ""
    echo "Possíveis causas:"
    echo "  - Containers não estão rodando"
    echo "  - API não está respondendo"
    echo "  - Dependências Python faltando"
    echo "  - Permissões insuficientes para manipular containers"
    echo ""
    exit 1
fi

# ==================== LIMPEZA ====================

echo -e "${YELLOW}🧹 Deseja limpar logs de teste do banco de dados? [s/N]${NC}"
read -p "> " cleanup

if [[ "$cleanup" =~ ^[Ss]$ ]]; then
    echo -e "${BLUE}Limpando logs de teste...${NC}"
    
    # MongoDB
    if docker exec mongo mongosh logdb --quiet --eval "db.logs.deleteMany({source: 'fault-tolerance-test'})" > /dev/null 2>&1; then
        echo -e "  ✅ MongoDB limpo"
    fi
    
    # PostgreSQL
    if docker exec postgres-primary psql -U loguser -d logdb -c "DELETE FROM logs WHERE source = 'fault-tolerance-test'" > /dev/null 2>&1; then
        echo -e "  ✅ PostgreSQL limpo"
    fi
    
    echo -e "${GREEN}✅ Limpeza concluída${NC}"
fi

echo ""
echo -e "${GREEN}✨ Pronto!${NC}"

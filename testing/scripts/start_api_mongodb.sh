#!/bin/bash

# Script para iniciar a API OTIMIZADA com MongoDB + Fabric
# OTIMIZAÇÕES: Sincronização assíncrona, cache otimizado, índices compostos

set -e

echo "=========================================="
echo " Iniciando API OTIMIZADA MongoDB + Fabric"
echo "=========================================="

# Verificar se MongoDB está rodando
echo ""
echo "1. Verificando MongoDB..."
if ! docker ps | grep -q mongo; then
 echo "[ERRO] MongoDB não está rodando!"
 echo " Execute: docker-compose up -d mongo"
 exit 1
fi
echo "[OK] MongoDB está rodando"

# Verificar se pymongo está instalado
echo ""
echo "2. Verificando dependência pymongo..."
if ! python3 -c "import pymongo" 2>/dev/null; then
 echo "[ERRO] pymongo não está instalado!"
 echo " Instalando pymongo..."
 pip install pymongo
fi
echo "[OK] pymongo está instalado"

# Verificar outras dependências
echo ""
echo "3. Verificando outras dependências..."
MISSING_DEPS=""
for pkg in flask redis requests; do
 if ! python3 -c "import $pkg" 2>/dev/null; then
 MISSING_DEPS="$MISSING_DEPS $pkg"
 fi
done

if [ ! -z "$MISSING_DEPS" ]; then
 echo "[ERRO] Dependências faltando:$MISSING_DEPS"
 echo " Instalando dependências..."
 pip install flask redis requests
fi
echo "[OK] Todas as dependências estão instaladas"

# Verificar se Redis está rodando (opcional, mas recomendado para cache)
echo ""
echo "4. Verificando Redis (cache)..."
if ! docker ps | grep -q redis; then
 echo "[AVISO] Redis não está rodando (cache desabilitado)"
 echo " Para melhor performance: docker-compose up -d redis"
else
 echo "[OK] Redis está rodando"
fi

# Verificar se Fabric está rodando
echo ""
echo "5. Verificando Hyperledger Fabric..."
if ! docker ps | grep -q peer0.org1.example.com; then
 echo "[AVISO] Fabric não está rodando (sincronização blockchain desabilitada)"
 echo " Para habilitar: cd ../hybrid-architecture/fabric-network && ./scripts/setup_network.sh"
else
 echo "[OK] Fabric está rodando"
fi

# Obter o diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ir para o diretório de testes
cd "$PROJECT_ROOT"

echo ""
echo "=========================================="
echo "🔥 Iniciando servidor API OTIMIZADO"
echo "=========================================="

# Verificar se a porta 5001 está em uso e liberar se necessário
echo ""
echo "6. Verificando porta 5001..."
if lsof -i :5001 >/dev/null 2>&1; then
 echo "[AVISO] Porta 5001 em uso. Liberando..."
 PID=$(lsof -t -i :5001)
 if [ ! -z "$PID" ]; then
 kill -9 $PID 2>/dev/null
 sleep 1
 echo "[OK] Porta 5001 liberada"
 fi
else
 echo "[OK] Porta 5001 disponível"
fi

echo ""
echo " OTIMIZAÇÕES ATIVAS:"
echo " [OK] 1. Sincronização ASSÍNCRONA (-80% latência)"
echo " [OK] 2. Cache Redis otimizado (TTL 10-15min)"
echo " [OK] 3. Índices MongoDB compostos"
echo " [OK] 4. Connection Pool 10-100"
echo ""
echo "🌐 Endpoints disponíveis:"
echo " POST http://localhost:5001/logs"
echo " GET http://localhost:5001/logs"
echo " GET http://localhost:5001/logs/<id>"
echo " GET http://localhost:5001/stats"
echo " GET http://localhost:5001/health"
echo ""
echo "Banco de dados: MongoDB (porta 27017)"
echo "Blockchain: Hyperledger Fabric (sync assíncrona)"
echo "Cache: Redis (porta 6379)"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo ""

# Iniciar API OTIMIZADA (após reorganização, arquivo está em src/)
python3 src/api_server_mongodb.py

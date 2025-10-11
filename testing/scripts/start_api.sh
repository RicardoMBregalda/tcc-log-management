#!/bin/bash

# Script de inicialização da API de Logs
# Verifica dependências e inicia o servidor

set -e

echo "=========================================="
echo "🚀 Inicializando API de Logs"
echo "=========================================="

# Verifica se Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não está instalado"
    exit 1
fi

echo "✅ Python3 encontrado: $(python3 --version)"

# Verifica se pip3 está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não está instalado"
    echo "Instale com: sudo apt-get install python3-pip"
    exit 1
fi

echo "✅ pip3 encontrado"

# Instala dependências se necessário
echo ""
echo "📦 Verificando dependências..."

if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚙️  Instalando dependências Python..."
    pip3 install -r requirements.txt
else
    echo "✅ Dependências já instaladas"
fi

# Verifica se Redis está rodando
echo ""
echo "🗄️  Verificando Redis..."

if docker ps | grep -q redis; then
    echo "✅ Redis está rodando (cache otimizado)"
else
    echo "⚠️  Redis não está rodando"
    echo "   A API funcionará sem cache (performance reduzida)"
    echo "   Para iniciar Redis: docker run -d --name redis -p 6379:6379 redis:alpine"
fi

# Verifica se Fabric está rodando
echo ""
echo "🔗 Verificando Hyperledger Fabric..."

if docker ps | grep -q peer0.org1.example.com; then
    echo "✅ Fabric está rodando"
else
    echo "❌ Fabric não está rodando"
    echo "   Inicie a rede Fabric primeiro:"
    echo "   cd ../hybrid-architecture/fabric-network"
    echo "   docker-compose up -d"
    exit 1
fi

# Verifica se chaincode está instalado
echo ""
echo "📜 Verificando chaincode..."

if docker exec cli peer lifecycle chaincode querycommitted -C logchannel -n logchaincode 2>/dev/null | grep -q "logchaincode"; then
    echo "✅ Chaincode 'logchaincode' está ativo"
else
    echo "❌ Chaincode não está instalado/ativo"
    echo "   Execute o script de teste primeiro:"
    echo "   docker exec cli bash /opt/gopath/src/github.com/hyperledger/fabric/peer/test_chaincode.sh"
    exit 1
fi

# Inicia o servidor
echo ""
echo "=========================================="
echo "🎉 Tudo pronto! Iniciando servidor..."
echo "=========================================="
echo ""
echo "📡 API estará disponível em: http://localhost:5001"
echo ""
echo "Para testar a API, execute em outro terminal:"
echo "  python3 test_api.py"
echo ""
echo "Para testes de performance:"
echo "  python3 performance_tester.py"
echo ""
echo "=========================================="
echo ""

# Inicia o servidor Flask (versão otimizada)
python3 api_server.py

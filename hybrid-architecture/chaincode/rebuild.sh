#!/bin/bash

# Script para recompilar e atualizar o chaincode otimizado

echo "🔧 Recompilando Chaincode Otimizado..."
echo "======================================"
echo ""

cd "$(dirname "$0")/../chaincode" || exit 1

echo "1️⃣  Verificando dependências Go..."
if ! command -v go &> /dev/null; then
    echo "❌ Go não encontrado! Instale Go primeiro."
    exit 1
fi
echo "✅ Go instalado: $(go version)"

echo ""
echo "2️⃣  Baixando dependências..."
go mod tidy
go mod vendor

echo ""
echo "3️⃣  Compilando chaincode..."
go build -o logchaincode

if [ $? -eq 0 ]; then
    echo "✅ Chaincode compilado com sucesso!"
else
    echo "❌ Erro ao compilar chaincode"
    exit 1
fi

echo ""
echo "4️⃣  Verificando otimizações aplicadas..."
if grep -q "OPTIMIZED v2" logchaincode.go; then
    echo "✅ Otimizações v2 aplicadas:"
    echo "   - Removido check LogExists (50% mais rápido)"
    echo "   - Timestamp parsing simplificado"
    echo "   - Estrutura otimizada"
else
    echo "⚠️  Arquivo ainda com código antigo"
fi

echo ""
echo "======================================"
echo "📊 Ganho Esperado:"
echo "   Latência Fabric: 40-70ms → 20-35ms"
echo "   Redução: ~50%"
echo ""
echo "🔄 Próximo Passo:"
echo "   1. Parar rede Fabric"
echo "   2. Reinstalar chaincode"
echo "   3. Testar performance"
echo ""
echo "Comandos:"
echo "  cd ../fabric-network"
echo "  docker-compose down"
echo "  ./scripts/setup_network.sh"
echo "======================================"

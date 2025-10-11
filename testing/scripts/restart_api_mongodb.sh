#!/bin/bash

# Script para reiniciar a API MongoDB + Fabric

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🔄 Reiniciando API MongoDB + Fabric..."
echo ""

# Parar API atual
$SCRIPT_DIR/stop_api.sh

echo ""
echo "🚀 Iniciando API..."
sleep 1

# Iniciar API
$SCRIPT_DIR/start_api_mongodb.sh

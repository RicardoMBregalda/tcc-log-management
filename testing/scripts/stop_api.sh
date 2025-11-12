#!/bin/bash

# Script para parar a API MongoDB + Fabric

echo "🛑 Parando API MongoDB + Fabric..."

# Encontrar processos na porta 5001
PIDS=$(lsof -t -i :5001 2>/dev/null)

if [ -z "$PIDS" ]; then
 echo "[OK] Nenhuma API rodando na porta 5001"
 exit 0
fi

# Parar processos
echo " Encontrados PIDs: $PIDS"
kill -9 $PIDS 2>/dev/null

sleep 1

# Verificar se parou
if lsof -i :5001 >/dev/null 2>&1; then
 echo "[ERRO] Falha ao parar API"
 exit 1
else
 echo "[OK] API parada com sucesso"
 exit 0
fi

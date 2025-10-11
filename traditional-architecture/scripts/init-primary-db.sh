#!/bin/bash
set -e

# Adiciona uma linha ao final do arquivo pg_hba.conf
# Esta linha permite que qualquer host (0.0.0.0/0)
# se conecte para fins de replicação (replication)
# usando qualquer usuário (all) com o método de autenticação 'trust'.
# 'trust' é seguro aqui pois só estamos expondo o banco na rede Docker interna.
echo "host    replication     all             0.0.0.0/0               trust" >> "${PGDATA}/pg_hba.conf"

# Aguarda o PostgreSQL estar pronto
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Aguardando PostgreSQL..."
  sleep 2
done

# Executa script de inicialização do schema de logs
if [ -f /docker-entrypoint-initdb.d/init-logdb.sql ]; then
  echo "Inicializando schema de logs..."
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/init-logdb.sql
  echo "Schema de logs inicializado com sucesso"
fi

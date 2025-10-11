#!/bin/bash
set -e

# Variáveis de ambiente para conexão
PRIMARY_HOST=postgres-primary
PRIMARY_PORT=5432
DB_USER=${POSTGRES_USER}

echo "Servidor Standby iniciando..."
echo "Aguardando o servidor primário (${PRIMARY_HOST}) ficar disponível..."

# Loop para esperar até que o servidor primário esteja pronto para aceitar conexões
until pg_isready -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "$DB_USER"; do
  echo "Primário ainda não está pronto... tentando novamente em 5 segundos."
  sleep 5
done

echo "Primário está pronto! Iniciando a cópia da base de dados (pg_basebackup)..."

# Limpa o diretório de dados do standby antes de copiar
rm -rf ${PGDATA}/*

# Executa o backup base do primário para o diretório de dados do standby
# -R (ou --write-recovery-conf) cria o standby.signal e configura a replicação automaticamente
pg_basebackup -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "$DB_USER" -D "${PGDATA}" -Fp -Xs -R -P

# Garante que o usuário postgres tenha permissão no diretório de dados
chown -R postgres:postgres "${PGDATA}"
chmod 0700 "${PGDATA}"

echo "Backup concluído. Iniciando o servidor PostgreSQL em modo standby."

# Executa o comando padrão do PostgreSQL para iniciar o servidor
exec gosu postgres postgres

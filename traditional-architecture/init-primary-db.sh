#!/bin/bash
set -e

# Adiciona uma linha ao final do arquivo pg_hba.conf
# Esta linha permite que qualquer host (0.0.0.0/0)
# se conecte para fins de replicação (replication)
# usando qualquer usuário (all) com o método de autenticação 'trust'.
# 'trust' é seguro aqui pois só estamos expondo o banco na rede Docker interna.
echo "host    replication     all             0.0.0.0/0               trust" >> "${PGDATA}/pg_hba.conf"

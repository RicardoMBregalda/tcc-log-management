#!/bin/bash

# ==============================================================================
# Script para Configuração Inicial do Ambiente do TCC
#
# Autor: Seu Nome
# Data: 21/09/2025
#
# Este script cria a estrutura de diretórios necessária para o projeto
# e o arquivo docker-compose.yml base que define a rede compartilhada.
# ==============================================================================

# Define o diretório raiz do projeto
PROJECT_ROOT="../"

# Mensagem de início
echo "🚀 Iniciando a configuração do ambiente para o TCC..."

# Cria a estrutura de diretórios
echo "📂 Criando estrutura de diretórios..."
mkdir -p "${PROJECT_ROOT}traditional-architecture"
mkdir -p "${PROJECT_ROOT}hybrid-architecture/chaincode"
mkdir -p "${PROJECT_ROOT}hybrid-architecture/fabric-network"
mkdir -p "${PROJECT_ROOT}scripts"

# Cria o arquivo docker-compose.yml na raiz do projeto
# Usamos 'cat <<EOF >' para escrever um bloco de texto multilinha em um arquivo.
echo "📄 Gerando o arquivo docker-compose.yml de base..."
cat <<EOF > "${PROJECT_ROOT}docker-compose.yml"
version: '3.7'

# A seção 'networks' define as redes que nossos serviços podem usar.
# Vamos criar uma rede personalizada chamada 'log-net' para garantir
# que todos os contêineres do projeto possam se comunicar usando
# nomes de serviço como hostname.
networks:
  log-net:
    driver: bridge
    name: tcc_log_network
EOF

# Deixa placeholders vazios nos outros arquivos docker-compose para passos futuros
touch "${PROJECT_ROOT}traditional-architecture/docker-compose.yml"
touch "${PROJECT_ROOT}hybrid-architecture/docker-compose.yml"


echo "✅ Estrutura de diretórios e arquivos de configuração base criados com sucesso!"
echo ""
echo "Próximos passos:"
echo "1. Navegue para o diretório raiz do projeto ('cd tcc-log-management')."
echo "2. Suba a rede base com o comando: docker-compose up -d"
echo "3. Verifique se a rede foi criada com: docker network ls | grep tcc_log_network"
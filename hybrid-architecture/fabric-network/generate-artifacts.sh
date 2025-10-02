#!/bin/bash

# Define o binário do configtxgen e cryptogen
export PATH=${PWD}/bin:$PATH
export FABRIC_CFG_PATH=${PWD}

# Limpa artefatos antigos para garantir uma geração limpa
rm -rf crypto-config
rm -rf config
mkdir config

# Gera o material criptográfico (certificados e chaves)
echo "####### Gerando material criptográfico usando cryptogen... #######"
cryptogen generate --config=./crypto-config.yaml

# Gera o bloco gênesis do serviço de ordenação
echo "####### Gerando o Bloco Gênesis... #######"
configtxgen -profile OneOrgOrdererGenesis -outputBlock ./config/genesis.block -channelID system-channel

# Gera a transação de criação do canal
echo "####### Gerando a transação de criação do canal... #######"
configtxgen -profile OneOrgChannel -outputCreateChannelTx ./config/logchannel.tx -channelID logchannel

echo "####### Geração de artefatos concluída! #######"
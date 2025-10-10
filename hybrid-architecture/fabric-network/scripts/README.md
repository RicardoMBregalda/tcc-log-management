# Scripts da Rede Hyperledger Fabric

Scripts para configuração, instalação e teste da rede blockchain Hyperledger Fabric.

## Scripts de Configuração

### install-fabric.sh

Baixa e instala as ferramentas do Hyperledger Fabric.

```bash
./install-fabric.sh
```

**O que faz:**

- Baixa binários do Fabric (cryptogen, configtxgen, peer, orderer, etc)
- Instala na pasta `bin/`
- Baixa imagens Docker oficiais do Fabric

**Uso:** Execute uma vez no início, antes de gerar os artefatos.

---

### generate-artifacts.sh

Gera todos os artefatos criptográficos e de configuração da rede.

```bash
./generate-artifacts.sh
```

**O que faz:**

- Gera certificados e chaves (crypto-config/)
- Cria bloco gênesis (config/genesis.block)
- Cria transação de canal (config/logchannel.tx)

**Requer:**

- Binários instalados (install-fabric.sh)
- Arquivos crypto-config.yaml e configtx.yaml

**Uso:** Execute sempre que modificar crypto-config.yaml ou configtx.yaml

---

### setup_network.sh

Configura a rede Fabric após os contêineres subirem.

```bash
# Execute dentro do contêiner CLI
docker exec cli ./scripts/setup_network.sh
```

**O que faz:**

1. Cria o canal `logchannel`
2. Faz todos os peers (peer0, peer1, peer2) entrarem no canal
3. Define anchor peers
4. Empacota o chaincode
5. Instala chaincode em todos os peers
6. Aprova e comita o chaincode no canal

**Duração:** ~30-40 segundos

**Resultado esperado:**

```bash
########### FIM DO SETUP - SUCESSO! ###########
```

---

## Scripts de Instalação do Chaincode

### install_chaincode.sh

Instala ou atualiza o chaincode na rede.

```bash
./install_chaincode.sh
```

**O que faz:**

- Empacota o chaincode Go (../chaincode/)
- Instala em todos os 3 peers
- Aprova como Org1
- Comita a definição no canal

**Uso:** Execute após modificações no chaincode Go

**Requer:** Rede Fabric já inicializada e canal criado

---

## Scripts de Teste

### test_chaincode.sh

Testa as principais funções do chaincode.

```bash
./test_chaincode.sh
```

**Testes executados:**

1. HealthCheck - Verifica se chaincode está ativo
2. StoreLog - Armazena um log de teste
3. GetLog - Recupera o log armazenado
4. QueryLogsByTimeRange - Busca logs por período

**Uso:** Execute para validar que o chaincode está funcionando

---

### teste_manual.sh

Testes manuais detalhados do chaincode.

```bash
./teste_manual.sh
```

**Testes mais completos:**

- Inserção de múltiplos logs
- Queries por diferentes critérios
- Validação de respostas
- Medições de latência

---

## Ordem de Execução Recomendada

### Setup Inicial (primeira vez)

```bash
cd /root/tcc-log-management/hybrid-architecture/fabric-network

# 1. Instalar ferramentas do Fabric
cd scripts
./install-fabric.sh
cd ..

# 2. Gerar artefatos criptográficos
./scripts/generate-artifacts.sh

# 3. Inicializar módulo do chaincode
cd ../chaincode
go mod init logchaincode
go mod tidy
cd ../fabric-network

# 4. Subir a rede
docker compose up -d

# 5. Aguardar 40 segundos para estabilizar
sleep 40

# 6. Configurar canal e chaincode
docker exec cli ./scripts/setup_network.sh

# 7. Testar
docker exec cli ./scripts/test_chaincode.sh
```

### Atualização do Chaincode

```bash
cd /root/tcc-log-management/hybrid-architecture/fabric-network

# 1. Modificar o chaincode em ../chaincode/logchaincode.go
# 2. Reinstalar
docker exec cli ./scripts/install_chaincode.sh

# 3. Testar
docker exec cli ./scripts/test_chaincode.sh
```

### Regenerar Rede (limpar tudo)

```bash
cd /root/tcc-log-management/hybrid-architecture/fabric-network

# 1. Parar contêineres
docker compose down --volumes

# 2. Limpar artefatos
rm -rf crypto-config/ config/

# 3. Gerar novamente
./scripts/generate-artifacts.sh

# 4. Subir e configurar
docker compose up -d
sleep 40
docker exec cli ./scripts/setup_network.sh
```

---

## Estrutura dos Arquivos Gerados

```bash
fabric-network/
├── scripts/               # Scripts (você está aqui)
├── bin/                  # Binários do Fabric
├── crypto-config/        # Certificados e chaves (gerado)
│   ├── ordererOrganizations/
│   └── peerOrganizations/
├── config/               # Artefatos de configuração (gerado)
│   ├── genesis.block
│   └── logchannel.tx
├── configtx.yaml         # Configuração de rede
├── crypto-config.yaml    # Configuração de certificados
└── docker-compose.yml    # Contêineres da rede
```

---

## Troubleshooting

### Erro: "command not found: cryptogen"

**Solução:**

```bash
cd scripts
./install-fabric.sh
```

### Erro: "channel already exists"

**Solução:** Limpar e recriar

```bash
docker compose down --volumes
rm -rf crypto-config/ config/
./scripts/generate-artifacts.sh
docker compose up -d
sleep 40
docker exec cli ./scripts/setup_network.sh
```

### Erro: "chaincode not found"

**Solução:** Reinstalar chaincode

```bash
docker exec cli ./scripts/install_chaincode.sh
```

### Peers não se conectam ao orderer

**Solução:** Verificar se os certificados estão corretos

```bash
ls -la crypto-config/peerOrganizations/org1.example.com/peers/
```

Se vazio, regerar:

```bash
./scripts/generate-artifacts.sh
```

---

## Variáveis de Ambiente Importantes

### Dentro do contêiner CLI

```bash
# MSP e TLS
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID='Org1MSP'
export CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/.../Admin@org1.example.com/msp

# Endereço do peer
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051

# Certificado TLS do peer
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/.../peer0.org1.example.com/tls/ca.crt

# Certificado do orderer
export ORDERER_CA=/opt/gopath/src/.../orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
```

---

## Comandos Úteis

### Verificar status da rede

```bash
docker compose ps
docker logs peer0.org1.example.com
docker logs orderer.example.com
```

### Consultar chaincode manualmente

```bash
docker exec cli peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"HealthCheck","Args":[]}'
```

### Ver logs de um peer

```bash
docker logs -f peer0.org1.example.com
```

---

## Documentação Completa

Para informações detalhadas sobre a implementação:

- [README Principal](../../README.md)

- [Documentação Completa](../../docs/)

## Referências

- [Hyperledger Fabric Documentation](https://hyperledger-fabric.readthedocs.io/)
- [Fabric Samples](https://github.com/hyperledger/fabric-samples)

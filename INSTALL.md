# Guia de Instalação - Sistema de Gerenciamento de Logs

Este guia fornece instruções detalhadas para instalação e configuração do sistema.

## Pré-requisitos

### Sistema Operacional
- Ubuntu 22.04.3 LTS (recomendado)
- Windows 10/11 com WSL2
- macOS 12+ (parcialmente testado)

### Hardware Recomendado
- CPU: 8 vCPUs ou mais
- RAM: 16GB mínimo
- Armazenamento: 100GB SSD NVMe

### Software Necessário

#### Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Verificar instalação
docker --version
docker-compose --version
```

#### Python 3.9+
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3-pip python3-venv

# Verificar instalação
python3 --version
pip3 --version
```

#### Git
```bash
# Ubuntu/Debian
sudo apt install git

# Verificar instalação
git --version
```

## Instalação

### 1. Clonar Repositório

```bash
git clone <repository-url>
cd tcc-log-management
```

### 2. Configurar Ambiente Python

```bash
cd testing

# Criar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
.\venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` no diretório `testing/`:

```bash
# API Configuration
API_PORT=5001
FLASK_HOST=0.0.0.0
FLASK_DEBUG=false

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=logdb
POSTGRES_USER=loguser
POSTGRES_PASSWORD=logpass

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Hyperledger Fabric
FABRIC_API_URL=http://localhost:3000
FABRIC_CHANNEL=logchannel
FABRIC_CHAINCODE=logchaincode

# Merkle Tree Auto-Batching
AUTO_BATCH_ENABLED=true
AUTO_BATCH_SIZE=50
AUTO_BATCH_INTERVAL=30

# Logging
LOG_LEVEL=INFO
```

## Configuração por Arquitetura

### Arquitetura Tradicional (PostgreSQL)

#### 1. Verificar Docker Compose

```bash
cd traditional-architecture
cat docker-compose.yml
```

#### 2. Ajustar Configurações (Opcional)

Edite `docker-compose.yml` para ajustar:
- Portas
- Recursos (CPU, memória)
- Volumes

#### 3. Iniciar Serviços

```bash
./start-traditional.sh
```

Aguarde até que todos os containers estejam prontos (aproximadamente 30-60 segundos).

#### 4. Verificar Status

```bash
docker ps
docker logs postgres-primary
docker logs postgres-standby
```

#### 5. Testar Conexão

```bash
./test-traditional.sh
```

### Arquitetura Híbrida (MongoDB + Fabric)

#### 1. Gerar Artefatos Criptográficos

```bash
cd hybrid-architecture/fabric-network
./scripts/1-generate-artifacts.sh
```

Este script irá:
- Gerar certificados usando `cryptogen`
- Criar genesis block
- Criar transaction de canal

#### 2. Iniciar Rede Fabric

```bash
./scripts/2-init-network.sh
```

Este script irá:
- Iniciar orderer e peers
- Criar e unir canal
- Instalar e instanciar chaincode
- Iniciar MongoDB e Redis

#### 3. Verificar Status da Rede

```bash
docker ps
```

Você deve ver containers:
- orderer.example.com
- peer0.org1.example.com
- peer0.org2.example.com
- mongodb
- redis
- cli

#### 4. Testar Chaincode

```bash
./scripts/3-test-network.sh
```

#### 5. Iniciar API

```bash
cd ../../testing/src
python api_server_mongodb.py
```

A API estará disponível em `http://localhost:5001`

#### 6. Verificar API

Abra um novo terminal:

```bash
# Health check
curl http://localhost:5001/health

# Documentação Swagger
# Abra no navegador: http://localhost:5001/api/docs
```

## Verificação da Instalação

### 1. Arquitetura Tradicional

```bash
cd traditional-architecture

# Verificar logs
docker logs postgres-primary
docker logs postgres-standby

# Verificar replicação
docker exec -it postgres-primary psql -U loguser -d logdb -c "\x" -c "SELECT * FROM pg_stat_replication;"

# Testar inserção
docker exec -it postgres-primary psql -U loguser -d logdb -c "INSERT INTO logs (source, level, message, timestamp) VALUES ('test', 'INFO', 'Test message', NOW());"

# Verificar replicação
docker exec -it postgres-standby psql -U loguser -d logdb -c "SELECT COUNT(*) FROM logs;"
```

### 2. Arquitetura Híbrida

```bash
# Verificar MongoDB
docker exec -it mongodb mongosh --eval "db.logs.countDocuments()"

# Verificar Redis
docker exec -it redis redis-cli PING

# Verificar Fabric chaincode
cd hybrid-architecture/fabric-network
docker exec cli peer chaincode query -C logchannel -n logchaincode -c '{"Args":["GetAllLogs"]}'

# Testar API
curl -X POST http://localhost:5001/logs \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "level": "INFO",
    "message": "Installation test"
  }'

# Verificar log criado
curl http://localhost:5001/logs?limit=1
```

## Resolução de Problemas

### Erro: "Cannot connect to Docker daemon"

```bash
# Verificar se Docker está rodando
sudo systemctl status docker

# Iniciar Docker
sudo systemctl start docker

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### Erro: "Port already in use"

```bash
# Verificar portas em uso
sudo lsof -i :5001  # API
sudo lsof -i :27017 # MongoDB
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis

# Parar containers conflitantes
docker ps
docker stop <container_id>
```

### Erro: "Connection refused" ao conectar MongoDB

```bash
# Verificar se container está rodando
docker ps | grep mongodb

# Verificar logs
docker logs mongodb

# Reiniciar container
docker restart mongodb
```

### Erro: "Chaincode instantiation failed"

```bash
# Verificar logs do peer
docker logs peer0.org1.example.com

# Reinstalar chaincode
cd hybrid-architecture/chaincode
docker exec cli peer chaincode install -n logchaincode -v 1.0 -p github.com/chaincode/logchaincode

# Verificar instalação
docker exec cli peer chaincode list --installed
```

### WAL com logs pendentes após restart

```bash
# Verificar estatísticas do WAL
curl http://localhost:5001/wal/stats

# Forçar processamento
curl -X POST http://localhost:5001/wal/force-process
```

## Limpeza e Reset

### Limpar Dados de Teste

```bash
# PostgreSQL
cd traditional-architecture
docker exec -it postgres-primary psql -U loguser -d logdb -c "TRUNCATE TABLE logs CASCADE;"

# MongoDB + Fabric
cd testing/scripts
./clean_logs_fast.sh
```

### Parar Todos os Serviços

```bash
# PostgreSQL
cd traditional-architecture
./stop-traditional.sh

# Híbrido
cd hybrid-architecture/fabric-network
./stop-network.sh
```

### Reset Completo

```bash
# Remover todos os containers, volumes e redes
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)
docker volume prune -f
docker network prune -f

# Remover artefatos criptográficos do Fabric
cd hybrid-architecture/fabric-network
rm -rf crypto-config/
rm -rf config/genesis.block config/logchannel.tx
```

## Próximos Passos

1. Executar testes de performance: veja `testing/README.md`
2. Ajustar parâmetros de otimização em `testing/config.py`
3. Revisar logs da aplicação e métricas do sistema

## Suporte

Para problemas relacionados a:
- **Docker/Containers**: Consulte logs com `docker logs <container>`
- **Python/API**: Verifique logs da aplicação e `testing/config.py`
- **Fabric**: Consulte logs do peer e orderer
- **Performance**: Execute testes com `performance_tester.py` e analise resultados

## Backup e Restauração

### Backup PostgreSQL

```bash
docker exec postgres-primary pg_dump -U loguser logdb > backup_postgres_$(date +%Y%m%d).sql
```

### Backup MongoDB

```bash
docker exec mongodb mongodump --out=/backup --db=logdb
docker cp mongodb:/backup ./backup_mongodb_$(date +%Y%m%d)
```

### Restauração

```bash
# PostgreSQL
cat backup_postgres_20241223.sql | docker exec -i postgres-primary psql -U loguser -d logdb

# MongoDB
docker cp backup_mongodb_20241223 mongodb:/backup
docker exec mongodb mongorestore /backup
```

# API REST - Sistema de Logs com Hyperledger Fabric

API REST para gerenciamento de logs usando Hyperledger Fabric (on-chain) e MongoDB (off-chain).

## Arquitetura

- **Blockchain (Fabric)**: Armazena logs com hash para garantir imutabilidade
- **MongoDB**: Armazena dados completos dos logs para consultas rápidas
- **API REST**: Interface HTTP para interação com o sistema

## Instalação

1. Instalar dependências Python:
```bash
cd testing
pip3 install -r requirements.txt
```

2. Configurar variáveis de ambiente (opcional):
```bash
export MONGO_HOST=localhost
export MONGO_PORT=27017
```

3. Iniciar o servidor:
```bash
python3 api_server.py
```

O servidor estará disponível em `http://localhost:5000`

## Endpoints

### 1. Health Check
```
GET /health
```
Verifica saúde da API e conectividade com MongoDB e Fabric.

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-09T21:00:00",
  "services": {
    "mongodb": "connected",
    "fabric": "connected"
  }
}
```

### 2. Criar Log
```
POST /logs
Content-Type: application/json
```

**Body:**
```json
{
  "id": "log001",
  "source": "app-server",
  "level": "INFO",
  "message": "Application started successfully",
  "metadata": {
    "version": "1.0",
    "user": "admin"
  }
}
```

**Resposta (201):**
```json
{
  "status": "success",
  "message": "Log criado com sucesso",
  "log_id": "log001",
  "hash": "abc123..."
}
```

### 3. Buscar Log por ID
```
GET /logs/:id
```

**Exemplo:** `GET /logs/log001`

**Resposta:**
```json
{
  "id": "log001",
  "hash": "abc123...",
  "timestamp": "2025-10-09T21:00:00Z",
  "source": "app-server",
  "level": "INFO",
  "message": "Application started successfully",
  "metadata": "{\"version\":\"1.0\"}"
}
```

### 4. Listar Logs
```
GET /logs
```

**Query Parameters:**
- `source`: Filtrar por origem (ex: `app-server`)
- `level`: Filtrar por nível (ex: `ERROR`)
- `limit`: Limitar resultados (padrão: 100)

**Exemplos:**
- `GET /logs` - Lista todos
- `GET /logs?level=ERROR` - Apenas erros
- `GET /logs?source=database&limit=50` - 50 logs do database

**Resposta:**
```json
{
  "count": 3,
  "logs": [
    {
      "id": "log001",
      "source": "app-server",
      "level": "INFO",
      "message": "...",
      ...
    },
    ...
  ]
}
```

### 5. Histórico do Log
```
GET /logs/history/:id
```

Retorna todo o histórico de transações de um log na blockchain.

**Exemplo:** `GET /logs/history/log001`

**Resposta:**
```json
{
  "log_id": "log001",
  "history": [
    {
      "txId": "abc123...",
      "timestamp": "2025-10-09T21:00:00Z",
      "isDelete": false,
      "log": {
        "id": "log001",
        "hash": "...",
        ...
      }
    }
  ]
}
```

### 6. Verificar Integridade
```
POST /logs/verify/:id
```

Verifica se o log foi alterado comparando hash da blockchain com hash recalculado.

**Exemplo:** `POST /logs/verify/log001`

**Resposta:**
```json
{
  "log_id": "log001",
  "valid": true,
  "blockchain_hash": "abc123...",
  "computed_hash": "abc123...",
  "message": "Log íntegro"
}
```

### 7. Estatísticas
```
GET /stats
```

Retorna estatísticas do sistema.

**Resposta:**
```json
{
  "timestamp": "2025-10-09T21:00:00",
  "mongodb": {
    "total_logs": 150,
    "logs_by_level": {
      "INFO": 100,
      "ERROR": 30,
      "WARN": 20
    }
  },
  "blockchain": {
    "total_logs": 150
  }
}
```

## Exemplos de Uso

### cURL

**Criar log:**
```bash
curl -X POST http://localhost:5000/logs \
  -H "Content-Type: application/json" \
  -d '{
    "id": "log123",
    "source": "web-app",
    "level": "ERROR",
    "message": "Database connection failed",
    "metadata": {"db": "postgres", "retry": 3}
  }'
```

**Buscar log:**
```bash
curl http://localhost:5000/logs/log123
```

**Listar erros:**
```bash
curl http://localhost:5000/logs?level=ERROR
```

**Verificar integridade:**
```bash
curl -X POST http://localhost:5000/logs/verify/log123
```

### Python

```python
import requests

# Criar log
response = requests.post('http://localhost:5000/logs', json={
    "id": "log456",
    "source": "api-gateway",
    "level": "INFO",
    "message": "Request processed",
    "metadata": {"duration_ms": 45}
})
print(response.json())

# Buscar log
log = requests.get('http://localhost:5000/logs/log456').json()
print(log)

# Listar logs
logs = requests.get('http://localhost:5000/logs?limit=10').json()
print(f"Total: {logs['count']}")
```

## Códigos de Status HTTP

- `200 OK` - Sucesso em consulta
- `201 Created` - Log criado com sucesso
- `400 Bad Request` - Dados inválidos
- `404 Not Found` - Log não encontrado
- `500 Internal Server Error` - Erro no servidor/blockchain

## Tratamento de Erros

Todos os erros retornam JSON com estrutura:
```json
{
  "error": "Mensagem de erro",
  "details": "Detalhes adicionais (opcional)"
}
```

## Notas de Implementação

1. **Duplo Armazenamento**: Logs são armazenados tanto na blockchain (hash) quanto no MongoDB (dados completos)
2. **Imutabilidade**: Uma vez criado, o log não pode ser modificado na blockchain
3. **Verificação**: Use `/logs/verify/:id` para detectar adulterações
4. **Performance**: Consultas rápidas vêm do MongoDB; verificação de integridade da blockchain
5. **Docker**: A API executa comandos no container `cli` do Fabric via Docker

## Troubleshooting

### Erro: "Log não encontrado na blockchain"
- Verifique se o chaincode está instalado: `docker exec cli peer lifecycle chaincode querycommitted -C logchannel`
- Teste manualmente: `docker exec cli bash /opt/gopath/src/github.com/hyperledger/fabric/peer/teste_manual.sh`

### Erro: MongoDB connection failed
- Verifique se o MongoDB está rodando: `docker ps | grep mongo`
- Teste conexão: `mongo --eval "db.adminCommand('ping')"`

### Timeout ao invocar chaincode
- Verifique logs dos peers: `docker logs peer0.org1.example.com`
- Aumente o timeout em `api_server.py` (padrão: 30s)

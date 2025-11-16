 🔍 Guia de Validação de Dados - MongoDB + Hyperledger Fabric

## 📋 Scripts Disponíveis

### 1. `validate_data.sh` - Validação Completa
Script principal que verifica consistência entre MongoDB e Fabric.

**Uso:**
```bash
cd /root/tcc-log-management/testing/go-api/tests/performance

# Validação padrão (logs de test-service, amostra de 10)
./validate_data.sh

# Validação customizada
./validate_data.sh <source-pattern> <sample-size>

# Exemplos:
./validate_data.sh test-service 20     # 20 logs de test-service
./validate_data.sh performance 15       # 15 logs de performance
```

**O que ele faz:**
- ✅ Conta total de logs no MongoDB
- ✅ Mostra amostra de logs (primeiros 3)
- ✅ Busca IDs no MongoDB e valida no Fabric
- ✅ Calcula taxa de consistência (% de logs sincronizados)
- ✅ Mostra estatísticas por source, level e timestamp
- ✅ Resumo final com status do sistema

**Exemplo de saída:**
```
╔═══════════════════════════════════════════════════════════╗
║     Validação de Dados - MongoDB + Hyperledger Fabric    ║
╚═══════════════════════════════════════════════════════════╝

📋 Configuração:
   Source filter: test-service
   Sample size: 10 logs

[1/3] Verificando MongoDB...
   Total de logs no MongoDB: 10000
   ✅ MongoDB contém logs

[2/3] Verificando Hyperledger Fabric...
   ✅ Peer0 está rodando
   Validando 10 logs no Fabric...
      ✅ Log abc123 encontrado no Fabric
      ✅ Log def456 encontrado no Fabric
      ...
   
   Resumo da validação Fabric:
      Encontrados: 10/10
      Não encontrados: 0/10
      Taxa de consistência: 100.00%

[3/3] Estatísticas e Comparação...
📊 MongoDB - Estatísticas por Source:
   test-service-1: 2500 logs (DEBUG, INFO, WARNING, ERROR)
   test-service-2: 2500 logs (DEBUG, INFO, WARNING, ERROR)
   ...

╔═══════════════════════════════════════════════════════════╗
║                     RESUMO FINAL                          ║
╚═══════════════════════════════════════════════════════════╝

✅ MongoDB: 10000 logs armazenados
✅ Fabric: 10/10 logs verificados (100.00% consistente)

🎉 Sistema está consistente! MongoDB e Fabric sincronizados.
```

---

### 2. `query_mongodb.sh` - Consultas no MongoDB
Script para consultar e analisar logs no MongoDB.

**Uso:**
```bash
# Ver ajuda
./query_mongodb.sh --help

# Buscar por ID específico
./query_mongodb.sh --id log-123456789

# Buscar por source (com regex)
./query_mongodb.sh --source test-service --limit 5

# Buscar por level
./query_mongodb.sh --level ERROR --limit 10

# Contar logs
./query_mongodb.sh --source performance --count

# Estatísticas gerais
./query_mongodb.sh --stats

# Combinações
./query_mongodb.sh --source test-service --level WARNING --limit 20
```

**Exemplos práticos:**

```bash
# Ver últimos 5 logs de erro
./query_mongodb.sh --level ERROR --limit 5

# Contar quantos logs de teste foram inseridos
./query_mongodb.sh --source test-service --count

# Ver estatísticas completas
./query_mongodb.sh --stats
```

**Exemplo de saída (--stats):**
```
📊 Estatísticas do MongoDB

Total de logs:
1670000

Por Source:
  test-service-1: 417500
  test-service-2: 417500
  test-service-3: 417500
  test-service-4: 417500

Por Level:
  INFO: 668000
  DEBUG: 501000
  WARNING: 334000
  ERROR: 167000

Intervalo de Tempo:
  Primeiro: 2025-11-15T00:30:15.123Z
  Último: 2025-11-15T02:45:30.456Z
```

---

### 3. `query_fabric.sh` - Consultas no Fabric
Script para consultar logs específicos no Hyperledger Fabric.

**Uso:**
```bash
# Consultar log específico
./query_fabric.sh <log_id>

# Exemplo:
./query_fabric.sh log-123456789
```

**Como obter IDs para consultar:**
```bash
# Listar 10 IDs do MongoDB
docker exec mongo mongosh logdb --quiet --eval \
  "db.logs.find({}, {id:1, _id:0}).limit(10).toArray()"

# Pegar um ID e consultar no Fabric
./query_fabric.sh <id-obtido-acima>
```

**Exemplo de saída:**
```
🔍 Consultando log no Fabric: log-abc123

✅ Log encontrado no Fabric:

{
  "id": "log-abc123",
  "timestamp": "2025-11-15T01:30:45.123Z",
  "source": "test-service-1",
  "level": "INFO",
  "message": "Performance test: login by user1",
  "metadata": "{\"test_id\":789,\"user\":\"user1\",\"action\":\"login\"}"
}

💡 Para comparar com MongoDB:
   docker exec mongo mongosh logdb --quiet --eval "db.logs.findOne({id: 'log-abc123'})"
```

---

## 🎯 Fluxo de Validação Recomendado

### Após executar testes de performance:

```bash
cd /root/tcc-log-management/testing/go-api/tests/performance

# 1. Validação geral (amostra de 10 logs)
./validate_data.sh

# 2. Se quiser validar mais logs (amostra maior)
./validate_data.sh test-service 50

# 3. Ver estatísticas detalhadas do MongoDB
./query_mongodb.sh --stats

# 4. Validar log específico no Fabric
# Primeiro, pegue um ID do MongoDB
docker exec mongo mongosh logdb --quiet --eval \
  "print(db.logs.findOne({source: /test-service/}).id)"

# Depois consulte no Fabric
./query_fabric.sh <id-obtido>
```

---

## 🔍 Verificações Manuais Adicionais

### MongoDB - Consultas diretas:
```bash
# Total de logs
docker exec mongo mongosh logdb --eval "db.logs.countDocuments({})"

# Últimos 5 logs
docker exec mongo mongosh logdb --eval "db.logs.find().sort({timestamp:-1}).limit(5).pretty()"

# Logs por level
docker exec mongo mongosh logdb --eval "db.logs.aggregate([
  {\$group: {_id: '\$level', count: {\$sum: 1}}},
  {\$sort: {count: -1}}
])"

# Verificar índices
docker exec mongo mongosh logdb --eval "db.logs.getIndexes()"
```

### Hyperledger Fabric - Consultas diretas:
```bash
# Entrar no container do peer
docker exec -it peer0.org1.example.com bash

# Consultar log específico
peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"GetLog","Args":["<log_id>"]}'

# Listar histórico de um log (auditoria)
peer chaincode query \
  -C logchannel \
  -n logchaincode \
  -c '{"function":"GetLogHistory","Args":["<log_id>"]}'
```

---

## 📊 Interpretando Resultados

### Taxa de Consistência:
- **100%**: Perfeito! Todos os logs estão sincronizados
- **95-99%**: Excelente, pode ter atraso de sincronização
- **80-94%**: Bom, mas investigar possíveis falhas
- **< 80%**: Atenção! Verificar logs de erro da API e Fabric

### Possíveis Inconsistências:

1. **Logs no MongoDB mas não no Fabric:**
   - Causa: Falha na invocação do chaincode
   - Solução: Verificar logs da API (`/root/tcc-log-management/testing/api.log`)

2. **Diferença nos timestamps:**
   - Normal: Pequena diferença devido ao processo assíncrono
   - Problema: Se diferença > 5 segundos, verificar performance

3. **Logs duplicados:**
   - Verificar: `docker exec mongo mongosh logdb --eval "db.logs.aggregate([{\$group: {_id: '\$id', count: {\$sum: 1}}}, {\$match: {count: {\$gt: 1}}}])"`

---

## 🧹 Limpeza de Dados de Teste

### Remover logs de teste do MongoDB:
```bash
# Remover logs de test-service
docker exec mongo mongosh logdb --eval \
  "db.logs.deleteMany({source: /^test-service/})"

# Remover logs de performance
docker exec mongo mongosh logdb --eval \
  "db.logs.deleteMany({source: /^performance/})"

# Remover todos os logs (CUIDADO!)
docker exec mongo mongosh logdb --eval "db.logs.deleteMany({})"
```

### Fabric:
> **Nota**: Logs no Fabric são imutáveis e não podem ser deletados (por design do blockchain). Para "limpar", você precisaria recriar a rede:

```bash
cd /root/tcc-log-management/hybrid-architecture/fabric-network
./stop-network.sh
docker volume prune -f  # Remove volumes persistentes
./start-network.sh
```

---

## 🐛 Troubleshooting

### Problema: "Peer não está rodando"
```bash
# Verificar containers
docker ps | grep peer

# Iniciar rede Fabric
cd /root/tcc-log-management/hybrid-architecture/fabric-network
./start-network.sh
```

### Problema: "MongoDB não responde"
```bash
# Verificar container
docker ps | grep mongo

# Reiniciar MongoDB
docker restart mongo
```

### Problema: "Taxa de consistência baixa"
```bash
# Ver logs da API
tail -f /root/tcc-log-management/testing/api.log

# Ver logs do chaincode
docker logs peer0.org1.example.com | grep chaincode
```

---

## 📚 Referências

- Scripts: `testing/go-api/tests/performance/*.sh`
- API logs: `testing/api.log`
- Chaincode: `hybrid-architecture/chaincode/logchaincode.go`
- Configuração Fabric: `hybrid-architecture/fabric-network/`

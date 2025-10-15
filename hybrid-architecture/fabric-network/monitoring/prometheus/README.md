# 📊 Prometheus Monitoring - TCC

Configuração completa de monitoramento para coleta de métricas do TCC.

## 🎯 Métricas Coletadas

### 1. Hyperledger Fabric
- **Orderer**: Blocos criados, latência de consenso, throughput
- **Peers**: Endossos, validações, estado do ledger
- **Chaincode**: Execuções, duração, erros
- **Source**: Métricas nativas do Fabric (endpoint `:9443/metrics`)

### 2. MongoDB (Off-chain)
- **Operações**: Inserts, queries, updates
- **Performance**: Latência, throughput
- **Recursos**: Conexões, memória, cache
- **Source**: `mongodb-exporter` (porta 9216)

### 3. PostgreSQL (Traditional)
- **Conexões**: Ativas, idle, máximo
- **Queries**: Lentas, frequentes, duração
- **Replicação**: Lag primário-standby
- **Cache**: Hit ratio, blocos lidos
- **Source**: `postgres-exporter` (portas 9187/9188)

### 4. Redis (Cache)
- **Cache**: Hits, misses, hit ratio
- **Memória**: Uso, máximo, evictions
- **Conexões**: Clientes conectados
- **Source**: `redis-exporter` (porta 9121)

### 5. API Flask
- **Requisições**: Total, por endpoint, status
- **Latência**: Média, P50, P95, P99
- **Logs**: Criados, por severidade
- **Merkle**: Batches, verificações, adulterações
- **Source**: Instrumentação customizada (porta 5001)

### 6. Docker Containers
- **CPU**: Uso por container
- **Memória**: RAM, swap, limites
- **Disco**: I/O leitura/escrita
- **Rede**: Bytes enviados/recebidos
- **Source**: `cAdvisor` (porta 8080)

### 7. Sistema Host
- **CPU**: Uso total, por core
- **Memória**: Total, disponível, swap
- **Disco**: Uso, I/O, latência
- **Rede**: Tráfego, erros
- **Source**: `node-exporter` (porta 9100)

---

## 🚀 Como Usar

### 1. Instalar Dependência na API

Adicione ao `requirements.txt`:
```txt
prometheus-client==0.19.0
```

Instale:
```bash
cd testing
pip3 install prometheus-client
```

### 2. Adicionar Instrumentação na API

No arquivo `src/api_server_mongodb.py`, adicione:

```python
from prometheus_metrics import (
    metrics_endpoint,
    logs_created_total,
    log_creation_duration_seconds,
    record_merkle_batch,
    record_blockchain_sync,
    cache_hits_total,
    cache_misses_total
)

# Endpoint de métricas
@app.route('/metrics')
def metrics():
    """Expõe métricas para Prometheus"""
    return metrics_endpoint()

# Exemplo de instrumentação ao criar log
@app.route('/logs', methods=['POST'])
def create_log():
    start_time = time.time()
    
    # ... lógica de criação do log ...
    
    # Registrar métricas
    logs_created_total.labels(
        source=log_data['source'],
        severity=log_data['severity'],
        architecture='hybrid'
    ).inc()
    
    duration = time.time() - start_time
    log_creation_duration_seconds.labels(architecture='hybrid').observe(duration)
    
    return jsonify(result), 201
```

### 3. Subir o Stack Completo

```bash
cd hybrid-architecture/fabric-network

# Subir todos os serviços incluindo monitoramento
docker-compose up -d

# Verificar se todos os exporters estão rodando
docker-compose ps | grep -E '(prometheus|grafana|exporter|cadvisor)'
```

### 4. Acessar Interfaces

#### Prometheus
- **URL**: http://localhost:9091
- **Uso**: Consultas PromQL, visualização de métricas brutas
- **Exemplos de queries**:
  ```promql
  # Taxa de requisições HTTP por segundo
  rate(flask_http_request_total[5m])
  
  # Latência P95 da API
  histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))
  
  # Uso de CPU por container
  rate(container_cpu_usage_seconds_total[5m])
  
  # Cache hit ratio do Redis
  rate(redis_keyspace_hits_total[5m]) / 
  (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
  ```

#### Grafana
- **URL**: http://localhost:3001
- **Login**: admin / admin
- **Uso**: Dashboards visuais, alertas
- **Dashboards**: (serão criados no próximo prompt)

#### cAdvisor
- **URL**: http://localhost:8080
- **Uso**: Visualização de métricas de containers

#### Exporters (apenas métricas brutas)
- Node Exporter: http://localhost:9100/metrics
- MongoDB Exporter: http://localhost:9216/metrics
- Postgres Exporter: http://localhost:9187/metrics
- Redis Exporter: http://localhost:9121/metrics
- API Flask: http://localhost:5001/metrics

---

## 📈 Queries Úteis para o TCC

### Performance - Latência

```promql
# Latência média de criação de logs (híbrida)
rate(log_creation_duration_seconds_sum{architecture="hybrid"}[5m]) / 
rate(log_creation_duration_seconds_count{architecture="hybrid"}[5m])

# Latência P95 de requisições HTTP
histogram_quantile(0.95, 
  rate(flask_http_request_duration_seconds_bucket[5m])
)

# Latência de transações blockchain
rate(blockchain_transaction_duration_seconds_sum[5m]) / 
rate(blockchain_transaction_duration_seconds_count[5m])
```

### Performance - Throughput

```promql
# Logs criados por segundo
rate(logs_created_total[1m])

# Transações blockchain por segundo
rate(consensus_etcdraft_committed_block_number[1m])

# Requisições HTTP por segundo
rate(flask_http_request_total[1m])
```

### Recursos - CPU

```promql
# CPU por container (%)
rate(container_cpu_usage_seconds_total[5m]) * 100

# CPU total do host (%)
(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))) * 100
```

### Recursos - Memória

```promql
# Memória usada por container (MB)
container_memory_usage_bytes / 1024 / 1024

# Memória disponível no host (GB)
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024
```

### Recursos - Disco

```promql
# I/O de disco por container (bytes/s)
rate(container_fs_reads_bytes_total[5m]) + 
rate(container_fs_writes_bytes_total[5m])

# Espaço em disco usado (%)
(node_filesystem_size_bytes{mountpoint="/"} - 
 node_filesystem_avail_bytes{mountpoint="/"}) / 
node_filesystem_size_bytes{mountpoint="/"} * 100
```

### Cache - Redis

```promql
# Cache hit ratio (%)
rate(redis_keyspace_hits_total[5m]) / 
(rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100

# Memória usada (%)
(redis_memory_used_bytes / redis_memory_max_bytes) * 100
```

### Banco de Dados

```promql
# PostgreSQL - Conexões ativas
pg_stat_activity_count{state="active"}

# PostgreSQL - Lag de replicação (segundos)
pg_replication_lag

# MongoDB - Operações por segundo
rate(mongodb_op_counters_total[1m])
```

### Blockchain

```promql
# Blocos criados por minuto
rate(consensus_etcdraft_committed_block_number[1m]) * 60

# Endossos por segundo
rate(endorser_successful_proposals[1m])

# Taxa de sucesso de transações (%)
rate(endorser_successful_proposals[5m]) / 
rate(endorser_proposals_received[5m]) * 100
```

---

## 🎨 Exportar Métricas para Análise

### 1. Via API do Prometheus

```bash
# Exportar todos os dados de uma query
curl -G 'http://localhost:9091/api/v1/query_range' \
  --data-urlencode 'query=rate(logs_created_total[5m])' \
  --data-urlencode 'start=2025-01-01T00:00:00Z' \
  --data-urlencode 'end=2025-01-01T23:59:59Z' \
  --data-urlencode 'step=60s' > metrics_data.json
```

### 2. Via Python (para análise)

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

# Configuração
PROMETHEUS_URL = 'http://localhost:9091'
query = 'rate(logs_created_total[5m])'
end = datetime.now()
start = end - timedelta(hours=1)

# Buscar dados
response = requests.get(f'{PROMETHEUS_URL}/api/v1/query_range', params={
    'query': query,
    'start': start.timestamp(),
    'end': end.timestamp(),
    'step': '15s'
})

data = response.json()['data']['result']

# Converter para DataFrame
for series in data:
    labels = series['metric']
    values = series['values']
    df = pd.DataFrame(values, columns=['timestamp', 'value'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['value'] = df['value'].astype(float)
    print(df)
```

---

## 🔔 Alertas Configurados

Veja `alerts.yml` para lista completa. Principais:

- ⚠️ **ServiceDown**: Serviço inacessível por > 1 minuto
- ⚠️ **HighCPUUsage**: CPU > 80% por > 2 minutos
- ⚠️ **HighMemoryUsage**: Memória > 90% por > 2 minutos
- ⚠️ **HighDiskUsage**: Disco < 10% disponível
- ⚠️ **HighAPILatency**: P95 > 2 segundos por > 3 minutos
- ⚠️ **PostgreSQLReplicationLag**: Lag > 60 segundos

---

## 🐛 Troubleshooting

### Prometheus não está coletando métricas

1. Verificar se serviço está UP:
   ```bash
   curl http://localhost:9091/api/v1/targets
   ```

2. Ver logs do Prometheus:
   ```bash
   docker logs prometheus-fabric
   ```

3. Testar endpoint diretamente:
   ```bash
   curl http://localhost:9216/metrics  # MongoDB Exporter
   ```

### Exporter não conecta no banco

1. Verificar configuração de rede:
   ```bash
   docker network inspect tcc_log_network
   ```

2. Testar conectividade:
   ```bash
   docker exec mongodb-exporter ping mongodb
   ```

3. Verificar credenciais no docker-compose.yml

### API Flask não expõe métricas

1. Verificar se prometheus-client está instalado:
   ```bash
   pip3 list | grep prometheus
   ```

2. Testar endpoint:
   ```bash
   curl http://localhost:5001/metrics
   ```

3. Ver logs da API:
   ```bash
   docker logs -f <api-container-name>
   ```

---

## 📊 Próximos Passos

1. ✅ **Prometheus configurado** - COMPLETO
2. ⏳ **Criar Dashboards Grafana** - Use PROMPT 2.2
3. ⏳ **Adicionar instrumentação na API** - Integrar prometheus_metrics.py
4. ⏳ **Executar testes e coletar métricas** - run_all_scenarios.sh
5. ⏳ **Analisar dados para TCC** - Gerar gráficos e tabelas

---

**✅ Prometheus está pronto!** 

Execute `docker-compose up -d` e acesse http://localhost:9091 para verificar.

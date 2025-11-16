# 🔥 Como Executar os Testes de Tolerância a Falhas

## 📋 Visão Geral

Os testes de tolerância a falhas comparam **Arquitetura Híbrida** (MongoDB + Hyperledger Fabric) com **Arquitetura Tradicional** (PostgreSQL com Streaming Replication).

**Arquivo de teste:** `testing/tests/test_fault_tolerance.py`

## 🎯 Cenários Testados

### Cenário 1: Falha do Banco de Dados Principal
- **PostgreSQL**: Primary cai, standby deve assumir (promoção manual)
- **Híbrida**: MongoDB cai, sistema falha (sem replicação configurada)
- **Métricas**: RTO, RPO, perda de dados, disponibilidade

### Cenário 2: Falha do Nó de Replicação
- **PostgreSQL**: Standby cai, primary continua operando
- **Híbrida**: Peer secundário cai, rede Fabric continua
- **Métricas**: Impacto na disponibilidade, sincronização pós-recuperação

### Cenário 3: Falha de Rede Temporária
- **PostgreSQL**: Primary pausado (simula perda de rede)
- **Híbrida**: MongoDB pausado
- **Métricas**: Tempo de recuperação, perda de dados durante partição

## 🚀 Pré-requisitos

### 1. Arquitetura Híbrida (MongoDB + Fabric)

```bash
# 1.1 Iniciar rede Fabric
cd /root/tcc-log-management/hybrid-architecture/fabric-network
./start-network.sh

# 1.2 Iniciar API híbrida
cd /root/tcc-log-management/testing
./scripts/start_api.sh

# 1.3 Verificar containers
docker ps | grep -E 'mongo|peer|orderer'
```

Containers esperados:
- `mongo`
- `peer0.org1.example.com`
- `peer1.org1.example.com`
- `peer2.org1.example.com`
- `orderer.example.com`

### 2. Arquitetura Tradicional (PostgreSQL)

```bash
# 2.1 Iniciar PostgreSQL com replicação
cd /root/tcc-log-management/traditional-architecture
./start-traditional.sh

# 2.2 Verificar containers
docker ps | grep postgres
```

Containers esperados:
- `postgres-primary`
- `postgres-standby`

### 3. Dependências Python

```bash
cd /root/tcc-log-management/testing
pip install -r requirements.txt

# Dependências específicas:
# - requests
# - psycopg2-binary
# - pymongo
```

## ⚡ Executar Testes

### Método 1: Execução Completa (Recomendado)

```bash
cd /root/tcc-log-management/testing/tests
python3 test_fault_tolerance.py
```

**Duração estimada:** 15-20 minutos (3 cenários × 2 arquiteturas)

### Método 2: Execução Individual por Cenário

Edite o arquivo `test_fault_tolerance.py` e comente cenários não desejados na função `main()`:

```python
# CENÁRIO 1: Falha do banco principal
hybrid_s1 = tester.test_scenario_1_primary_failure('hybrid')
traditional_s1 = tester.test_scenario_1_primary_failure('traditional')

# CENÁRIO 2: Falha de réplica (comentar se não quiser executar)
# hybrid_s2 = tester.test_scenario_2_standby_failure('hybrid')
# traditional_s2 = tester.test_scenario_2_standby_failure('traditional')
```

## 📊 Resultados

Os resultados são salvos em `testing/results/`:

```
results/
├── fault_tolerance_report.json  # Dados estruturados completos
└── fault_tolerance_report.md    # Relatório formatado em Markdown
```

### Exemplo de Relatório JSON

```json
{
  "test_date": "2025-11-15T...",
  "total_scenarios": 3,
  "summary": {
    "hybrid_wins": {
      "detection": 0,
      "recovery": 0,
      "data_loss": 1,
      "availability": 0
    },
    "traditional_wins": {
      "detection": 2,
      "recovery": 3,
      "data_loss": 0,
      "availability": 0
    }
  },
  "comparisons": [...]
}
```

### Exemplo de Relatório Markdown

```markdown
# Relatório de Testes de Tolerância a Falhas

## 📊 Resumo Geral

| Métrica | Híbrida | Tradicional | Empate |
|---------|---------|-------------|--------|
| Detecção de Falha | 0 | 2 | 1 |
| Recuperação | 0 | 3 | 0 |
| Perda de Dados | 1 | 0 | 2 |
| Disponibilidade | 0 | 0 | 3 |

### 🏆 Pontuação Total
- **Híbrida**: 1 ponto
- **Tradicional**: 5 pontos

**Vencedor Geral**: 🎯 Arquitetura Tradicional
```

## 🔍 Monitoramento Durante Testes

### Terminal 1: Logs da API Híbrida
```bash
cd /root/tcc-log-management/testing
tail -f api.log
```

### Terminal 2: Logs PostgreSQL Primary
```bash
docker logs -f postgres-primary
```

### Terminal 3: Status dos Containers
```bash
watch -n 2 'docker ps --format "table {{.Names}}\t{{.Status}}"'
```

## 🐛 Troubleshooting

### Problema: Containers não iniciam

```bash
# Limpar ambiente
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# Reiniciar redes
cd /root/tcc-log-management/hybrid-architecture/fabric-network
./stop-network.sh
./start-network.sh

cd /root/tcc-log-management/traditional-architecture
./stop-traditional.sh
./start-traditional.sh
```

### Problema: API não responde

```bash
# Verificar saúde
curl http://localhost:5001/health

# Reiniciar API
cd /root/tcc-log-management/testing
./scripts/stop_api.sh
./scripts/start_api.sh

# Verificar logs
cat api.log
```

### Problema: PostgreSQL replicação quebrada

```bash
# Verificar status de replicação no primary
docker exec postgres-primary psql -U loguser -d logdb -c "SELECT * FROM pg_stat_replication;"

# Verificar se standby está em recovery
docker exec postgres-standby psql -U loguser -d logdb -c "SELECT pg_is_in_recovery();"

# Reconstruir standby
cd /root/tcc-log-management/traditional-architecture
./stop-traditional.sh
docker volume rm traditional-architecture_postgres_standby_data
./start-traditional.sh
```

### Problema: MongoDB não aceita conexões

```bash
# Verificar logs
docker logs mongo

# Reiniciar
docker restart mongo

# Testar conexão
docker exec mongo mongosh --eval "db.adminCommand('ping')"
```

## 📈 Métricas Coletadas

### Tempos (RTO - Recovery Time Objective)
- **Detection Time**: Tempo para detectar a falha (segundos)
- **Recovery Time**: Tempo para recuperar o serviço (segundos)
- **Total Downtime**: Tempo total de indisponibilidade (segundos)

### Integridade (RPO - Recovery Point Objective)
- **Logs Sent**: Total de logs enviados durante teste
- **Logs Received**: Total de logs persistidos com sucesso
- **Logs Lost**: Diferença entre enviados e recebidos
- **Loss Percentage**: Porcentagem de perda de dados

### Disponibilidade
- **Continued Operating**: Sistema continuou operando durante falha? (true/false)
- **Automatic Recovery**: Recuperação foi automática? (true/false)
- **Data Consistent**: Dados mantiveram consistência? (true/false)

## 🔬 Análise dos Resultados Anteriores (Outubro 2025)

### Vencedores por Métrica:
1. **Detecção**: PostgreSQL (2 vitórias)
2. **Recuperação**: PostgreSQL (3 vitórias)
3. **Perda de Dados**: Híbrida (1 vitória)
4. **Disponibilidade**: Empate (3 empates)

### Insights:
- **PostgreSQL** recupera mais rápido (1.29s vs 6.94s no cenário de falha do primary)
- **Híbrida** tem menor perda de dados (0% vs 38.17% no cenário de falha do primary)
- Ambas mantêm disponibilidade quando réplica cai
- PostgreSQL tem melhor RTO, Híbrida tem melhor RPO

## 📝 Próximos Passos Recomendados

1. **Re-executar testes** com ambiente limpo
2. **Comparar resultados** com baseline de outubro/2025
3. **Ajustar configurações** se necessário:
   - MongoDB replication set (melhorar RTO híbrida)
   - PostgreSQL synchronous replication (melhorar RPO tradicional)
4. **Documentar no TCC** os trade-offs identificados

## 📚 Referências

- Código dos testes: `testing/tests/test_fault_tolerance.py`
- Configuração API: `testing/config.py`
- Scripts auxiliares: `testing/scripts/`
- Resultados anteriores: `testing/results/backup_existing/fault_tolerance_report.json`

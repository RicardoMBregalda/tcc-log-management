# 🛡️ Testes de Resiliência

Testes automatizados de recuperação de falhas para o TCC Log Management.

## 🎯 Objetivo

Avaliar a capacidade de **detecção, recuperação e manutenção de integridade** dos dados frente a falhas controladas em ambas as arquiteturas (híbrida e tradicional).

## 📋 Cenários Testados

### 1️⃣ Queda de Peer Fabric
- **Componente:** `peer0.org1.example.com`
- **Método:** `docker stop`
- **Expectativa:** Sistema híbrido continua operando (outros peers ativos)
- **Métricas:** Tempo de recuperação, % logs perdidos

### 2️⃣ Queda do Ordering Service
- **Componente:** `orderer.example.com`
- **Método:** `docker stop`
- **Expectativa:** MongoDB continua aceitando logs, blockchain pausado
- **Métricas:** Tempo de recuperação, sincronização retomada

### 3️⃣ Queda do MongoDB
- **Componente:** `mongodb`
- **Método:** `docker stop`
- **Expectativa:** API rejeita logs (sem armazenamento disponível)
- **Métricas:** Tempo de detecção, tempo de recuperação

### 4️⃣ Failover PostgreSQL
- **Componente:** `postgres-primary`
- **Método:** `docker stop`
- **Expectativa:** Standby disponível para promoção
- **Métricas:** Tempo de detecção, tempo de failover, replicação OK
- **Nota:** Failover automático requer Patroni/repmgr (não configurado)

### 5️⃣ Isolamento de Rede
- **Componente:** `api-flask`
- **Método:** `docker network disconnect`
- **Expectativa:** API inacessível, recupera após `reconnect`
- **Métricas:** Tempo de detecção, tempo de reconexão

---

## 🚀 Como Executar

### Método 1: Script Bash (Recomendado)

```bash
cd testing/scripts
chmod +x run_resilience_tests.sh
./run_resilience_tests.sh
```

**Funcionalidades:**
- ✅ Verificação automática de pré-requisitos
- ✅ Menu interativo
- ✅ Execução de testes individuais ou conjunto completo
- ✅ Visualização de resultados

### Método 2: Python Direto

```bash
cd testing/tests
python3 test_resilience.py
```

### Método 3: Teste Individual

```python
cd testing/tests
python3 -c "
from test_resilience import ResilienceTest
tester = ResilienceTest()

# Executar apenas um cenário
tester.test_peer_failure()

# Salvar resultados
tester.save_results_json('resilience_report.json')
tester.generate_markdown_report('resilience_report.md')
"
```

---

## 📊 Saídas Geradas

### `resilience_report.json`

Estrutura completa dos resultados em JSON:

```json
{
  "test_suite": "resilience_tests",
  "generated_at": "2025-10-14 15:30:00",
  "total_tests": 5,
  "tests_passed": 4,
  "tests_failed": 1,
  "results": [
    {
      "scenario": "peer_failure",
      "component": "peer0.org1",
      "architecture": "hybrid",
      "detection_time_seconds": null,
      "recovery_time_seconds": 12.34,
      "logs_lost": 0,
      "loss_percentage": 0.0,
      "success": true,
      "events": [...]
    }
  ]
}
```

### `resilience_report.md`

Relatório narrativo em Markdown com:
- Status de cada teste (✅/❌)
- Tempos de detecção e recuperação
- Estatísticas de logs (enviados, recebidos, perdidos)
- Verificação de integridade
- Observações e notas

**Exemplo:**

```markdown
## PEER FAILURE
**Status:** ✅ PASSOU
**Componente:** peer0.org1
**Arquitetura:** hybrid

### ⏱️ Tempos
- **Recuperação:** 12.34s

### 📊 Logs
- **Antes da falha:** 20
- **Durante falha:** 40
- **Após recuperação:** 40
- **Perdidos:** 0 (0.00%)

### 🔍 Integridade
- **Sistema continuou operando:** Sim
- **Integridade verificada:** Sim
```

---

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# API
export API_HOST=localhost
export API_PORT=5001

# PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=logdb
export POSTGRES_USER=logadmin
export POSTGRES_PASSWORD=logpassword

# MongoDB
export MONGO_HOST=localhost
export MONGO_PORT=27017
```

### Parâmetros de Teste

Edite `test_resilience.py`:

```python
TEST_CONFIG = {
    'logs_per_test': 100,           # Logs totais por teste
    'logs_before_failure': 20,      # Logs antes de simular falha
    'detection_timeout': 30,        # Timeout para detectar falha (s)
    'recovery_timeout': 60,         # Timeout para recuperação (s)
    'log_interval': 0.1,            # Intervalo entre logs (s)
}
```

### Nomes de Containers

Se seus containers têm nomes diferentes, ajuste:

```python
DOCKER_CONTAINERS = {
    'peer': 'peer0.org1.example.com',
    'orderer': 'orderer.example.com',
    'mongodb': 'mongodb',
    'postgres_primary': 'postgres-primary',
    'postgres_standby': 'postgres-standby',
    'api': 'api-flask'  # Opcional (se API em container)
}
```

---

## 📈 Métricas Coletadas

Para cada cenário:

| Métrica | Descrição |
|---------|-----------|
| **detection_time_seconds** | Tempo até detectar falha |
| **recovery_time_seconds** | Tempo até recuperar serviço |
| **logs_sent_before_failure** | Logs enviados antes da falha |
| **logs_sent_during_failure** | Logs durante período de falha |
| **logs_sent_after_recovery** | Logs após recuperação |
| **logs_total** | Total de logs enviados |
| **logs_received** | Logs efetivamente armazenados |
| **logs_lost** | Logs perdidos (total - recebidos) |
| **loss_percentage** | % de perda de dados |
| **system_continued_operating** | Sistema continuou operando? |
| **data_integrity_verified** | Integridade dos dados OK? |

---

## ✅ Critérios de Sucesso

Um teste **PASSA** se:

1. **Tempo de recuperação < 60s** (timeout)
2. **Perda de logs < 5%** (tolerância)
3. **Comportamento esperado alcançado**:
   - Peer failure: sistema continua operando
   - MongoDB failure: API rejeita logs corretamente
   - Network isolation: conectividade restaurada

---

## 🐛 Troubleshooting

### Erro: "Docker não encontrado"

```bash
# Verificar Docker instalado
docker --version

# Verificar Docker rodando
docker ps
```

### Erro: "Container não encontrado"

```bash
# Listar containers ativos
docker ps --format "table {{.Names}}\t{{.Status}}"

# Iniciar serviços
cd hybrid-architecture/fabric-network
docker-compose up -d
```

### Erro: "API não responde"

```bash
# Testar manualmente
curl http://localhost:5001/health

# Verificar porta correta
netstat -tulpn | grep 5001

# Ver logs da API
docker logs <api-container-name>
```

### Teste falha ao reconectar rede

Alguns ambientes não suportam `docker network disconnect/connect`. Nesse caso:

1. O teste detectará o erro e continuará
2. Resultado será marcado como "não aplicável"
3. Outros testes não são afetados

---

## 🔍 Análise de Resultados

### Comparação Híbrida vs Tradicional

| Aspecto | Híbrida | Tradicional |
|---------|---------|-------------|
| **Peer failure** | ✅ Continua operando | N/A |
| **Orderer failure** | ✅ MongoDB continua | N/A |
| **MongoDB failure** | ❌ API para | N/A |
| **DB Primary failure** | N/A | ⚠️ Requer failover |
| **Network isolation** | ❌ Inacessível | ❌ Inacessível |

### Interpretação

- ✅ **Verde:** Sistema resiliente, falha transparente
- ⚠️ **Amarelo:** Requer intervenção manual, mas dados preservados
- ❌ **Vermelho:** Sistema indisponível durante falha

---

## 📝 Notas Importantes

### Limitações

1. **Failover PostgreSQL:** Teste apenas simula queda do primário. Promoção automática do standby requer ferramenta de HA (Patroni, repmgr, PgPool-II)

2. **Network Isolation:** Requer API em container Docker. Se API roda fora do Docker, teste será pulado.

3. **Blockchain Sync:** Após recuperar orderer, sincronização retoma automaticamente, mas pode haver lag.

### Melhorias Futuras

- [ ] Integrar com Prometheus para métricas em tempo real
- [ ] Adicionar teste de split-brain (particionamento de rede)
- [ ] Testar cascata de falhas (múltiplos componentes)
- [ ] Automatizar promoção de standby PostgreSQL
- [ ] Adicionar teste de corrupção de dados

---

## 🎓 Uso no TCC

### Capítulo de Resultados

Use as métricas coletadas para:

1. **Tabela comparativa** de tempos de recuperação
2. **Gráfico de barras** de % perda de dados
3. **Análise qualitativa** de comportamento sob falha

### Critérios de Avaliação

Conforme metodologia do TCC:

> "O sistema híbrido deve demonstrar **resiliência superior** devido à distribuição de dados e consenso descentralizado, com **tempo de recuperação médio < 30 segundos** e **perda de dados < 2%**."

Resultados esperados:
- ✅ Peer failure: 0% perda (outros peers continuam)
- ✅ Orderer failure: 0% perda (MongoDB buffer)
- ❌ MongoDB failure: Sistema para (ponto único de falha)

---

**✅ Testes prontos para execução!**

Execute `./run_resilience_tests.sh` e colete os resultados para seu TCC.

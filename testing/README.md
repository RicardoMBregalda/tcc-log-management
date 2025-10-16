# 🧪 Testing - TCC Log Management

Este diretório contém todos os testes, ferramentas de análise e resultados para o projeto TCC Log Management.

## 📂 Estrutura

```
testing/
├── config.py                    # Configurações centralizadas
├── utils.py                     # Funções utilitárias reutilizáveis
├── requirements.txt             # Dependências Python
├── verify_folder.py            # ✨ Ferramenta de verificação automática
├── VERIFICATION_SUMMARY.md     # ✨ Relatório de verificação completo
│
├── src/                        # Código fonte principal
│   ├── api_server_mongodb.py   # Servidor API Flask + MongoDB
│   ├── performance_tester.py   # Testes de performance
│   ├── analyze_results.py      # Análise de resultados
│   ├── prometheus_metrics.py   # Métricas Prometheus
│   └── redis_cache.py          # Cache Redis
│
├── tests/                      # Testes automatizados
│   ├── test_resilience.py      # Testes de resiliência
│   ├── test_auto_batching.py   # Testes de batching automático
│   ├── test_tampering_*.py     # Testes de detecção de adulteração
│   ├── verify_merkle_integrity.py  # Verificação de integridade Merkle
│   └── README_RESILIENCE.md    # Documentação de testes de resiliência
│
├── scripts/                    # Scripts de automação
│   ├── start_api_mongodb.sh    # Iniciar API
│   ├── stop_api.sh             # Parar API
│   ├── run_resilience_tests.sh # Executar testes de resiliência
│   ├── apply_all_optimizations.sh  # Aplicar otimizações
│   └── testing/                # Scripts de teste específicos
│       ├── run_all_scenarios.sh
│       ├── run_quick_test.sh
│       └── ...
│
├── demos/                      # Demonstrações
│   ├── demo_auto_batching.py   # Demo de batching automático
│   └── demo_merkle_tree.py     # Demo de Merkle Tree
│
└── results/                    # Resultados de testes
    ├── all_scenarios.json      # Todos os cenários consolidados
    ├── scenario_S[1-9]_*.json  # Resultados individuais por cenário
    ├── performance_results.*   # Resultados de performance
    └── scenarios_analysis.*    # Análise consolidada
```

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
cd testing
pip install -r requirements.txt
```

### 2. Verificar Integridade

```bash
python3 verify_folder.py
```

Este comando verifica:
- ✅ Sintaxe de todos os arquivos Python
- ✅ Validade de todos os arquivos JSON e CSV
- ✅ Configurações do sistema
- ✅ Permissões de scripts
- ✅ Estrutura de diretórios

### 3. Executar Testes

#### Testes de Performance
```bash
cd src
python3 performance_tester.py
```

#### Testes de Resiliência
```bash
cd scripts
./run_resilience_tests.sh
```

#### Verificar Integridade Merkle
```bash
cd tests
python3 verify_merkle_integrity.py --all
```

## 📊 Cenários de Teste

9 cenários de teste estão configurados para avaliar diferentes combinações de volume e taxa:

| Cenário | Volume | Taxa (logs/s) | Descrição |
|---------|--------|---------------|-----------|
| **S1** | 10,000 | 100 | Baixo Volume + Baixa Taxa |
| **S2** | 10,000 | 1,000 | Baixo Volume + Média Taxa |
| **S3** | 10,000 | 10,000 | Baixo Volume + Alta Taxa |
| **S4** | 100,000 | 100 | Médio Volume + Baixa Taxa |
| **S5** | 100,000 | 1,000 | Médio Volume + Média Taxa |
| **S6** | 100,000 | 10,000 | Médio Volume + Alta Taxa |
| **S7** | 1,000,000 | 100 | Alto Volume + Baixa Taxa |
| **S8** | 1,000,000 | 1,000 | Alto Volume + Média Taxa |
| **S9** | 1,000,000 | 10,000 | Alto Volume + Alta Taxa |

## 🔧 Configuração

### Variáveis de Ambiente

Defina no arquivo `.env` ou exporte:

```bash
# API Híbrida
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

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Hyperledger Fabric
export FABRIC_API_URL=http://localhost:3000
export FABRIC_CHANNEL=logchannel
export FABRIC_CHAINCODE=logchaincode
```

### Customizar Cenários

Edite `config.py`:

```python
TEST_SCENARIOS: Dict[str, Dict] = {
    'S10': {'volume': 5000000, 'rate': 50000, 'description': 'Seu cenário personalizado'},
}
```

## 📈 Análise de Resultados

### Visualizar Resultados

```bash
cd src
python3 analyze_results.py
```

### Arquivos de Resultados

- **JSON**: Formato estruturado para análise programática
- **CSV**: Para importar em Excel/Google Sheets
- **MD**: Relatórios legíveis em Markdown

## 🛡️ Testes de Resiliência

Simula 5 cenários de falha:

1. **Queda de Peer Fabric** - Sistema deve continuar operando
2. **Queda do Ordering Service** - MongoDB continua aceitando logs
3. **Queda do MongoDB** - API deve rejeitar logs
4. **Failover PostgreSQL** - Standby disponível para promoção
5. **Isolamento de Rede** - Detectar e recuperar de perda de conectividade

Ver [tests/README_RESILIENCE.md](tests/README_RESILIENCE.md) para detalhes.

## 🔍 Verificação de Integridade

### Merkle Tree

Verifica integridade dos logs usando Merkle Tree:

```bash
# Criar batch
python3 tests/verify_merkle_integrity.py --create-batch

# Verificar batch específico
python3 tests/verify_merkle_integrity.py batch_20251016_123456

# Verificar todos os batches
python3 tests/verify_merkle_integrity.py --all

# Listar batches
python3 tests/verify_merkle_integrity.py --list
```

### Detecção de Adulteração

```bash
python3 tests/test_tampering_detection.py
python3 tests/test_tampering_auto.py
```

## 📦 Dependências

Todas verificadas quanto a vulnerabilidades de segurança:

- ✅ **Flask 3.0.0** - Framework web
- ✅ **flask-cors 4.0.0** - CORS para Flask
- ✅ **pymongo 4.6.0** - Driver MongoDB
- ✅ **psycopg2-binary 2.9.9** - Driver PostgreSQL
- ✅ **redis 5.0.1** - Cliente Redis
- ✅ **psutil 5.9.6** - Monitoramento de sistema
- ✅ **python-dotenv 1.0.0** - Variáveis de ambiente
- ✅ **requests 2.31.0** - Cliente HTTP

**Nenhuma vulnerabilidade conhecida!**

## 🧹 Manutenção

### Verificação Periódica

Execute regularmente para garantir integridade:

```bash
python3 verify_folder.py
```

Gera:
- `verification_report.json` - Relatório detalhado (não commitado)
- Saída no console com status de todos os arquivos

### Limpeza

```bash
# Remover resultados antigos (opcional)
rm -rf results/*.json results/*.csv

# Regenerar resultados
python3 src/performance_tester.py
```

## 🎓 Uso Acadêmico (TCC)

### Capítulos Relevantes

1. **Metodologia** - Descrever cenários S1-S9
2. **Implementação** - Arquitetura híbrida vs tradicional
3. **Resultados** - Métricas de performance e resiliência
4. **Discussão** - Análise comparativa

### Dados para Gráficos

Use os arquivos CSV em `results/`:
- `all_scenarios.csv` - Para gráficos de comparação
- `performance_results.csv` - Para tabelas de performance
- `scenarios_analysis.csv` - Para análise detalhada

## 🐛 Troubleshooting

### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

### Erro: "Connection refused"
```bash
# Verificar serviços rodando
docker ps
docker-compose ps

# Iniciar serviços
docker-compose up -d
```

### Scripts sem permissão
```bash
# Todos os scripts já têm permissão de execução
# Se necessário, reaplique:
chmod +x scripts/*.sh
chmod +x scripts/testing/*.sh
```

## ✨ Novidades

### Ferramenta de Verificação (`verify_folder.py`)

Nova ferramenta automática que verifica:
- Sintaxe Python
- Validade de JSON/CSV
- Configurações
- Permissões de scripts
- Estrutura de diretórios

**Adicionada em:** 2025-10-16  
**Status:** ✅ Todos os testes passando

### Relatório de Verificação (`VERIFICATION_SUMMARY.md`)

Relatório completo da verificação mais recente:
- 19 arquivos Python validados
- 22 arquivos JSON validados
- 3 arquivos CSV validados
- 10 scripts executáveis
- 0 vulnerabilidades de segurança

## 📚 Documentação Adicional

- [README_RESILIENCE.md](tests/README_RESILIENCE.md) - Testes de resiliência
- [VERIFICATION_SUMMARY.md](VERIFICATION_SUMMARY.md) - Relatório de verificação
- [IMPLEMENTATION_SUMMARY.md](tests/IMPLEMENTATION_SUMMARY.md) - Resumo de implementação

## 🤝 Contribuindo

Ao adicionar novos testes ou funcionalidades:

1. Seguir estrutura existente
2. Adicionar testes apropriados
3. Atualizar documentação
4. Executar `verify_folder.py` antes de commitar
5. Adicionar resultados em `results/`

## 📞 Suporte

Para questões sobre os testes:
1. Verificar documentação em `tests/README_RESILIENCE.md`
2. Executar `verify_folder.py` para diagnóstico
3. Verificar logs dos containers: `docker logs <container>`

---

**Status do Projeto:** ✅ Todos os testes validados  
**Última Verificação:** 2025-10-16  
**Arquivos Verificados:** 44 (19 Python + 22 JSON + 3 CSV)  
**Vulnerabilidades:** 0

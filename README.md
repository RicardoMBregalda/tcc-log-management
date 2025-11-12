# Sistema de Gerenciamento de Logs - Arquitetura Híbrida

Sistema de gerenciamento de logs desenvolvido como trabalho de conclusão de curso (TCC), comparando arquitetura tradicional baseada em PostgreSQL com arquitetura híbrida utilizando MongoDB, Hyperledger Fabric v2.4.9 e blockchain.

## Arquitetura

### Arquitetura Tradicional
- PostgreSQL 13.12 em cluster primary-standby
- Replicação streaming síncrona
- Failover automático
- Monitoramento com Prometheus e Grafana

### Arquitetura Híbrida
- MongoDB para armazenamento off-chain
- Hyperledger Fabric v2.4.9 para blockchain
- Write-Ahead Log (WAL) para durabilidade
- Redis para cache
- Merkle Tree para integridade
- API REST em Flask

## Requisitos

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9+
- Ubuntu 22.04.3 LTS (recomendado)
- 8 vCPUs, 16GB RAM, 100GB SSD NVMe

## Instalação

### 1. Clonar Repositório

```bash
git clone <repository-url>
cd tcc-log-management
```

### 2. Instalar Dependências Python

```bash
cd testing
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

As configurações estão centralizadas em `testing/config.py`. Para customizar, utilize variáveis de ambiente:

```bash
export API_PORT=5001
export MONGO_HOST=localhost
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
```

## Uso

### Arquitetura Tradicional (PostgreSQL)

#### Iniciar

```bash
cd traditional-architecture
./start-traditional.sh
```

O script irá:
- Iniciar containers PostgreSQL primary e standby
- Configurar replicação streaming
- Criar banco de dados e tabelas
- Iniciar Prometheus e Grafana

#### Testar

```bash
./test-traditional.sh
```

#### Parar

```bash
./stop-traditional.sh
```

### Arquitetura Híbrida (MongoDB + Fabric)

#### Iniciar

```bash
cd hybrid-architecture
./fabric-network/start-network.sh
```

O script irá:
- Gerar artefatos criptográficos
- Iniciar rede Hyperledger Fabric
- Criar canal e instalar chaincode
- Iniciar MongoDB e Redis
- Iniciar Prometheus e Grafana

#### Iniciar API

```bash
cd testing/src
python api_server_mongodb.py
```

A API estará disponível em `http://localhost:5001`

#### Testar

```bash
cd hybrid-architecture
./fabric-network/test-network.sh
```

#### Parar

```bash
cd hybrid-architecture
./fabric-network/stop-network.sh
```

## Testes de Performance

### Executar Todos os Cenários (S1-S9)

```bash
cd testing
./run_all_tests.sh
```

### Executar Cenário Específico

```bash
cd testing
python src/performance_tester.py --scenario S5 --architecture hybrid
```

### Cenários Disponíveis

| Cenário | Volume | Taxa (logs/s) | Descrição |
|---------|--------|---------------|-----------|
| S1 | 10.000 | 100 | Baixo Volume + Baixa Taxa |
| S2 | 10.000 | 1.000 | Baixo Volume + Média Taxa |
| S3 | 10.000 | 10.000 | Baixo Volume + Alta Taxa |
| S4 | 100.000 | 100 | Médio Volume + Baixa Taxa |
| S5 | 100.000 | 1.000 | Médio Volume + Média Taxa |
| S6 | 100.000 | 10.000 | Médio Volume + Alta Taxa |
| S7 | 1.000.000 | 100 | Alto Volume + Baixa Taxa |
| S8 | 1.000.000 | 1.000 | Alto Volume + Média Taxa |
| S9 | 1.000.000 | 10.000 | Alto Volume + Alta Taxa |

### Análise de Resultados

```bash
cd testing/src
python analyze_results.py
```

Os resultados serão salvos em:
- `testing/src/results/` (JSON e CSV)
- `testing/results/` (relatórios consolidados)

## API REST

### Documentação Swagger

Após iniciar a API, acesse a documentação interativa:

**http://localhost:5001/api/docs**

### Endpoints Principais

- `POST /logs` - Criar novo log
- `GET /logs` - Listar logs com filtros
- `GET /logs/<id>` - Buscar log específico
- `POST /merkle/batch` - Criar batch com Merkle Tree
- `GET /merkle/batch/<id>` - Consultar batch
- `POST /merkle/verify/<id>` - Verificar integridade do batch
- `GET /health` - Health check
- `GET /stats` - Estatísticas do sistema

### Exemplo de Uso

```bash
# Criar log
curl -X POST http://localhost:5001/logs \
  -H "Content-Type: application/json" \
  -d '{
    "source": "app-server",
    "level": "INFO",
    "message": "Application started successfully"
  }'

# Listar logs
curl http://localhost:5001/logs?source=app-server&limit=10
```

## Monitoramento

### Prometheus

- URL: `http://localhost:9090`
- Métricas: CPU, RAM, I/O, latência, throughput

### Grafana

- URL: `http://localhost:3000`
- Usuário: `admin`
- Senha: `admin`

Dashboards pré-configurados:
- PostgreSQL Overview
- MongoDB + Fabric Hybrid
- System Resources

## Estrutura do Projeto

```
tcc-log-management/
├── hybrid-architecture/        # Arquitetura híbrida
│   ├── chaincode/             # Smart contract Fabric
│   ├── fabric-network/        # Configurações da rede
│   └── monitoring/            # Prometheus e Grafana
├── traditional-architecture/   # Arquitetura PostgreSQL
│   ├── docker-compose.yml
│   ├── scripts/               # Scripts SQL
│   └── monitoring/            # Prometheus e Grafana
├── testing/                   # Framework de testes
│   ├── src/                   # Código fonte
│   │   ├── api_server_mongodb.py
│   │   ├── performance_tester.py
│   │   ├── write_ahead_log.py
│   │   └── redis_cache.py
│   ├── scripts/               # Scripts auxiliares
│   ├── results/               # Resultados dos testes
│   └── config.py              # Configurações centralizadas
└── TCC/                       # Documentação LaTeX
    └── 2-textuais/
        └── 6-resultados.tex   # Capítulo de resultados
```

## Otimizações Implementadas

### Arquitetura Híbrida
- Sincronização assíncrona com Fabric (redução de 80% na latência)
- Write-Ahead Log (WAL) com garantia de 0% de perda de dados
- Cache Redis com TTL otimizado (10-15 minutos)
- Connection pooling MongoDB (10-100 conexões)
- Índices compostos para queries otimizadas
- Merkle Tree auto-batching (batches de 50 logs a cada 30s)
- ThreadPoolExecutor para paralelização

### Arquitetura Tradicional
- Replicação streaming síncrona
- Connection pooling (5-20 conexões)
- Índices otimizados em timestamp e source
- Prepared statements
- Checkpoints configurados

## Testes de Tolerância a Falhas

```bash
cd testing/scripts
./run_fault_tolerance_tests.sh
```

Cenários testados:
- Desconexão de rede
- Falha de nó do banco de dados
- Recuperação pós-falha
- Integridade de dados após recovery

## Resultados

Os resultados completos dos experimentos estão documentados no capítulo 6 do TCC (`TCC/2-textuais/6-resultados.tex`).

### Principais Conclusões

#### Performance
- Arquitetura tradicional: throughput superior em cenários de baixa taxa
- Arquitetura híbrida: melhor desempenho em cenários de alta taxa com WAL
- Latência P95: PostgreSQL apresenta valores mais estáveis
- Latência P99: Fabric introduz variabilidade devido à consensus

#### Recursos
- PostgreSQL: menor consumo de CPU e RAM em cenários simples
- Híbrido: maior overhead devido ao blockchain e sincronização

#### Custo Operacional
- Arquitetura tradicional: US$ 107,39/mês (S1) a US$ 268,71/mês (S9)
- Arquitetura híbrida: US$ 178,78/mês (S1) a US$ 447,23/mês (S9)
- Incremento: 66,5% em média

#### Integridade
- Ambas as arquiteturas garantem ACID
- Híbrido oferece auditabilidade adicional via blockchain
- Merkle Tree permite verificação eficiente de integridade

## Licença

Este projeto foi desenvolvido como trabalho acadêmico para conclusão de curso.

## Autor

Trabalho de Conclusão de Curso - Engenharia de Computação

## Contato

Para dúvidas sobre a implementação, consulte a documentação do código ou os comentários inline nos arquivos fonte.

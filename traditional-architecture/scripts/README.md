# Scripts da Arquitetura Tradicional (PostgreSQL)

Scripts para configuração e inicialização do cluster PostgreSQL em modo primário-standby com replicação.

## Scripts de Configuração

### init-primary-db.sh

Inicializa o banco de dados PostgreSQL primário.

```bash
# Executado automaticamente pelo Docker
# Referenciado no docker-compose.yml
```

**O que faz:**

- Configura `pg_hba.conf` para permitir replicação
- Aguarda PostgreSQL estar pronto
- Executa init-logdb.sql para criar schema

**Quando é executado:** Automaticamente na primeira inicialização do contêiner postgres-primary

**Localização no Docker:** `/docker-entrypoint-initdb.d/init-primary-db.sh`

---

### init-standby.sh

Inicializa o banco de dados PostgreSQL standby (réplica).

```bash
# Executado automaticamente pelo Docker
# Referenciado no docker-compose.yml
```

**O que faz:**

- Para o PostgreSQL se estiver rodando
- Remove dados antigos
- Usa `pg_basebackup` para copiar dados do primário
- Cria arquivo `standby.signal` para modo réplica
- Configura `postgresql.conf` para replicação
- Inicia PostgreSQL em modo standby

**Quando é executado:** Automaticamente na primeira inicialização do contêiner postgres-standby

**Modo:** Somente leitura (read-only)

---

## Scripts SQL

### init-logdb.sql

Cria o schema completo para armazenamento de logs.

```bash
# Executado automaticamente pelo init-primary-db.sh
psql -U logadmin -d logdb -f scripts/init-logdb.sql
```

**Estrutura criada:**

1. **Tabela `logs`** - Armazena todos os logs

   ```sql
   - id VARCHAR(255) PRIMARY KEY
   - timestamp TIMESTAMPTZ
   - source VARCHAR(100)
   - level VARCHAR(20) (INFO, DEBUG, WARNING, ERROR, CRITICAL)
   - message TEXT
   - metadata JSONB
   - stacktrace TEXT
   - created_at TIMESTAMPTZ
   ```

2. **Índices:**
   - `idx_logs_timestamp` - Busca por período
   - `idx_logs_level` - Filtro por nível
   - `idx_logs_source` - Filtro por origem
   - `idx_logs_created_at` - Ordenação por criação

3. **Tabela `sync_control`** - Controle de sincronização com Fabric

   ```sql
   - log_id VARCHAR(255) PRIMARY KEY
   - synced_at TIMESTAMPTZ
   - fabric_hash VARCHAR(64)
   - sync_status VARCHAR(20) (pending, synced, failed, retrying)
   - retry_count INTEGER
   - last_error TEXT
   ```

4. **View `logs_pending_sync`** - Logs que precisam ser sincronizados

5. **Função `mark_log_for_sync()`** - Marca novos logs para sincronização

6. **Trigger** - Executa automaticamente em INSERT

**Uso:** Executado automaticamente na primeira inicialização

---

### create_sync_control.sql

Cria apenas a estrutura de controle de sincronização.

```bash
# Uso manual se necessário
psql -U logadmin -d logdb -f scripts/create_sync_control.sql
```

**O que cria:**

- Tabela `sync_control`
- View `logs_pending_sync`
- Função `mark_log_for_sync()`
- Trigger `trigger_mark_log_for_sync`

**Uso:** Somente se precisar recriar as tabelas de sincronização sem recriar a tabela `logs`

---

## Ordem de Execução (Automática)

Quando você executa `docker compose up -d`, os scripts são executados automaticamente nesta ordem:

### 1. Postgres Primary (postgres-primary)

```bash
1. Contêiner inicia
2. PostgreSQL é inicializado
3. init-primary-db.sh é executado
   ├─ Configura pg_hba.conf
   ├─ Aguarda PostgreSQL
   └─ Executa init-logdb.sql
       ├─ Cria tabela logs
       ├─ Cria índices
       ├─ Cria tabela sync_control
       ├─ Cria view logs_pending_sync
       ├─ Cria função mark_log_for_sync()
       └─ Cria trigger
4. Banco pronto para uso
```

### 2. Postgres Standby (postgres-standby)

```bash
1. Contêiner inicia
2. init-standby.sh é executado
   ├─ Para PostgreSQL
   ├─ Remove dados antigos
   ├─ pg_basebackup do primary
   ├─ Cria standby.signal
   ├─ Configura postgresql.conf
   └─ Inicia em modo réplica
3. Réplica sincronizada e somente leitura
```

---

## Configuração Manual (se necessário)

### Recriar Schema Completo

```bash
cd /root/tcc-log-management/traditional-architecture

# Entrar no contêiner primary
docker exec -it postgres-primary bash

# Conectar ao banco
psql -U logadmin -d logdb

# Dropar e recriar
DROP TABLE IF EXISTS sync_control CASCADE;
DROP TABLE IF EXISTS logs CASCADE;
\q

# Executar script
psql -U logadmin -d logdb -f /docker-entrypoint-initdb.d/scripts/init-logdb.sql
```

### Recriar Apenas Sincronização

```bash
docker exec -it postgres-primary psql -U logadmin -d logdb -f /docker-entrypoint-initdb.d/scripts/create_sync_control.sql
```

### Verificar Replicação

```bash
# No primary - verificar standby conectado
docker exec postgres-primary psql -U logadmin -d logdb -c "SELECT * FROM pg_stat_replication;"

# No standby - verificar modo read-only
docker exec postgres-standby psql -U logadmin -d logdb -c "SELECT pg_is_in_recovery();"
# Deve retornar: t (true)
```

---

## Estrutura dos Arquivos

```bash
traditional-architecture/
├── scripts/                      # Scripts (você está aqui)
│   ├── README.md                # Esta documentação
│   ├── init-primary-db.sh       # Inicialização do primary
│   ├── init-standby.sh          # Inicialização do standby
│   ├── init-logdb.sql           # Schema completo
│   └── create_sync_control.sql  # Apenas sincronização
├── monitoring/
│   ├── grafana/
│   └── prometheus/
└── docker-compose.yml           # Configuração dos contêineres
```

---

## Volumes e Persistência

### Volumes Docker

```yaml
postgres-primary-data:    # Dados do primary
postgres-standby-data:    # Dados do standby
prometheus-data:          # Métricas
grafana-storage:          # Dashboards e configs
```

### Limpar Tudo e Reiniciar

```bash
cd /root/tcc-log-management/traditional-architecture

# Parar e remover volumes
docker compose down --volumes

# Subir novamente (scripts executam automaticamente)
docker compose up -d
```

---

## Troubleshooting

### Standby não está replicando

**Verificar:**

```bash
# No primary
docker logs postgres-primary

# No standby
docker logs postgres-standby
```

**Solução:** Recriar standby

```bash
docker compose stop postgres-standby
docker volume rm traditional-architecture_postgres-standby-data
docker compose up -d postgres-standby
```

---

### Tabela logs não existe

**Verificar:**

```bash
docker exec postgres-primary psql -U logadmin -d logdb -c "\dt"
```

**Solução:** Executar init-logdb.sql manualmente

```bash
docker exec postgres-primary psql -U logadmin -d logdb -f /docker-entrypoint-initdb.d/scripts/init-logdb.sql
```

---

### Sincronização não está funcionando

**Verificar tabela sync_control:**

```bash
docker exec postgres-primary psql -U logadmin -d logdb -c "SELECT * FROM sync_control LIMIT 5;"
```

**Verificar trigger:**

```bash
docker exec postgres-primary psql -U logadmin -d logdb -c "\dft trigger_mark_log_for_sync"
```

**Recriar:**

```bash
docker exec postgres-primary psql -U logadmin -d logdb -f /docker-entrypoint-initdb.d/scripts/create_sync_control.sql
```

---

## Variáveis de Ambiente

Definidas no docker-compose.yml:

```bash
POSTGRES_USER=logadmin        # Usuário admin
POSTGRES_PASSWORD=logpass123  # Senha (MUDAR EM PRODUÇÃO!)
POSTGRES_DB=logdb             # Nome do banco
PGDATA=/var/lib/postgresql/data/pgdata  # Diretório de dados
```

---

## Comandos Úteis

### Consultas no Primary

```bash
# Conectar ao banco
docker exec -it postgres-primary psql -U logadmin -d logdb

# Ver tabelas
\dt

# Ver logs
SELECT * FROM logs ORDER BY timestamp DESC LIMIT 10;

# Ver logs pendentes de sincronização
SELECT * FROM logs_pending_sync LIMIT 10;

# Ver status de sincronização
SELECT 
    sync_status, 
    COUNT(*) as total 
FROM sync_control 
GROUP BY sync_status;
```

### Monitoramento

```bash
# Ver tamanho das tabelas
docker exec postgres-primary psql -U logadmin -d logdb -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Ver estatísticas de replicação
docker exec postgres-primary psql -U logadmin -d logdb -c "
SELECT * FROM pg_stat_replication;
"
```

---

## Referências

- [PostgreSQL Replication Documentation](https://www.postgresql.org/docs/current/high-availability.html)
- [pg_basebackup](https://www.postgresql.org/docs/current/app-pgbasebackup.html)
- [README Principal](../../README.md)
- [Documentação Completa](../../docs/)

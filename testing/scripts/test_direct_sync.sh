#!/bin/bash
# Script de teste para insert_and_sync_log.py
# Demonstra o envio direto de logs para PostgreSQL e Fabric

echo "=========================================="
echo "Teste: Insert + Sync Direto"
echo "PostgreSQL → Fabric (Sem polling)"
echo "=========================================="
echo ""

cd /root/tcc-log-management/testing

echo "1️⃣  Teste 1: Log INFO simples"
echo "----------------------------"
python3 insert_and_sync_log.py \
    "api-gateway" \
    "INFO" \
    "Requisição GET /api/users processada com sucesso" \
    '{"method": "GET", "path": "/api/users", "status": 200, "duration_ms": 45}'

echo ""
echo ""

echo "2️⃣  Teste 2: Log WARNING"
echo "----------------------------"
python3 insert_and_sync_log.py \
    "auth-service" \
    "WARNING" \
    "Tentativa de login com senha incorreta" \
    '{"user": "admin", "ip": "192.168.1.100", "attempts": 3}'

echo ""
echo ""

echo "3️⃣  Teste 3: Log ERROR"
echo "----------------------------"
python3 insert_and_sync_log.py \
    "payment-service" \
    "ERROR" \
    "Falha ao processar pagamento - timeout na conexão" \
    '{"transaction_id": "TXN-12345", "amount": 150.00, "error": "connection_timeout"}'

echo ""
echo ""

echo "4️⃣  Teste 4: Log DEBUG"
echo "----------------------------"
python3 insert_and_sync_log.py \
    "cache-service" \
    "DEBUG" \
    "Cache hit para chave user:profile:789" \
    '{"key": "user:profile:789", "ttl": 300, "size_bytes": 2048}'

echo ""
echo ""

echo "5️⃣  Teste 5: Log CRITICAL"
echo "----------------------------"
python3 insert_and_sync_log.py \
    "database-service" \
    "CRITICAL" \
    "Conexão com banco de dados perdida" \
    '{"host": "db-primary", "port": 5432, "retry_count": 3}'

echo ""
echo ""

echo "=========================================="
echo "Verificando Resultados"
echo "=========================================="
echo ""

echo "📊 Estatísticas PostgreSQL:"
docker exec postgres-primary psql -U logadmin -d logdb << 'EOF'
SELECT 
    sync_status,
    COUNT(*) as total
FROM sync_control
GROUP BY sync_status
ORDER BY sync_status;
EOF

echo ""
echo "📝 Últimos 5 logs inseridos:"
docker exec postgres-primary psql -U logadmin -d logdb << 'EOF'
SELECT 
    LEFT(l.id, 8) || '...' as id,
    l.source,
    l.level,
    LEFT(l.message, 40) || '...' as message,
    sc.sync_status,
    LEFT(sc.fabric_hash, 12) || '...' as hash
FROM logs l
LEFT JOIN sync_control sc ON l.id = sc.log_id
ORDER BY l.timestamp DESC
LIMIT 5;
EOF

echo ""
echo "=========================================="
echo "✅ Testes Concluídos!"
echo "=========================================="

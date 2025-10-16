#!/bin/bash
# Otimiza PostgreSQL para melhor performance

echo "🔧 Otimizando PostgreSQL..."

CONTAINER_NAME="postgres-primary"

# Aplicar configurações otimizadas
docker exec -u postgres $CONTAINER_NAME psql -U postgres -d logdb -c "
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '1536MB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET max_parallel_workers_per_gather = 2;
ALTER SYSTEM SET max_parallel_workers = 4;
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
"

# Reiniciar PostgreSQL para aplicar
docker restart $CONTAINER_NAME

echo "⏳ Aguardando PostgreSQL reiniciar..."
sleep 5

echo "✅ PostgreSQL otimizado!"
echo "   - shared_buffers: 512MB (25% de 2GB disponível para DB)"
echo "   - effective_cache_size: 1536MB"
echo "   - work_mem: 16MB"
echo "   - Ganho esperado: -10 a -20ms"

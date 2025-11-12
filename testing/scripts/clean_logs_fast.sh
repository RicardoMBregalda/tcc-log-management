#!/bin/bash
# Script rápido para limpar logs (drop + recreate)

echo " LIMPEZA RÁPIDA DE LOGS"
echo ""

# ============== MONGODB ==============
echo "📦 Limpando MongoDB..."
docker exec mongo mongosh --quiet logdb --eval "
db.logs.drop();
db.createCollection('logs');
db.logs.createIndex({ 'id': 1 }, { unique: true });
db.logs.createIndex({ 'source': 1, 'timestamp': -1 });
db.logs.createIndex({ 'created_at': -1 });
print('[OK] MongoDB: Collection recriada com índices');
" 2>&1

echo ""
echo "📦 Limpando sync_control..."
docker exec mongo mongosh --quiet logdb --eval "
db.sync_control.drop();
db.createCollection('sync_control');
print('[OK] sync_control: Collection recriada');
" 2>&1

echo ""
echo "📦 Limpando Redis..."
docker exec redis redis-cli FLUSHALL > /dev/null 2>&1
echo "[OK] Redis: Cache limpo"

# ============== POSTGRESQL ==============
echo ""
echo "📦 Limpando PostgreSQL..."
docker exec postgres-primary psql -U loguser -d logdb -c "
TRUNCATE TABLE logs CASCADE;
TRUNCATE TABLE sync_control CASCADE;
" 2>&1

echo "[OK] PostgreSQL: Tabelas truncadas"

# ============== VERIFICAÇÃO ==============
echo ""
echo "═══════════════════════════════════════════"
echo " VERIFICAÇÃO"
echo "═══════════════════════════════════════════"

mongo_count=$(docker exec mongo mongosh --quiet logdb --eval "db.logs.countDocuments()" 2>&1)
echo "MongoDB: $mongo_count logs"

pg_count=$(docker exec postgres-primary psql -U loguser -d logdb -t -c "SELECT COUNT(*) FROM logs;" 2>&1 | tr -d ' ')
echo "PostgreSQL: $pg_count logs"

echo ""
echo "[OK] Limpeza concluída!"

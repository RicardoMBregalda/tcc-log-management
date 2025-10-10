-- Verifica status dos últimos logs de teste
SELECT 
    l.id,
    l.source,
    sc.sync_status,
    sc.fabric_hash,
    sc.synced_at
FROM logs l
LEFT JOIN sync_control sc ON l.id = sc.log_id
WHERE l.id LIKE '%test%'
ORDER BY l.timestamp DESC
LIMIT 5;

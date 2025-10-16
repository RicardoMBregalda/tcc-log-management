-- Criação da tabela sync_control compatível com schema existente
CREATE TABLE IF NOT EXISTS sync_control (
    log_id TEXT PRIMARY KEY,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fabric_hash VARCHAR(64),
    sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed', 'retrying')),
    retry_count INTEGER DEFAULT 0,
    last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_control(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_synced_at ON sync_control(synced_at DESC);

-- View para facilitar consultas
CREATE OR REPLACE VIEW logs_pending_sync AS
SELECT 
    l.id::text as id,
    l.timestamp,
    l.content
FROM logs l
LEFT JOIN sync_control sc ON l.id::text = sc.log_id
WHERE sc.log_id IS NULL OR sc.sync_status IN ('pending', 'failed');

GRANT ALL PRIVILEGES ON TABLE sync_control TO logadmin;
GRANT SELECT ON logs_pending_sync TO logadmin;

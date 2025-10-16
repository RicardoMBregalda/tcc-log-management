-- Script de inicialização do banco de dados de logs PostgreSQL
-- Este script cria a estrutura necessária para armazenar logs na arquitetura tradicional

-- Criação da tabela principal de logs
CREATE TABLE IF NOT EXISTS logs (
    id VARCHAR(255) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    source VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL CHECK (level IN ('INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    metadata JSONB,
    stacktrace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para otimizar queries comuns
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_source ON logs(source);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);

-- Tabela de controle de sincronização para rastrear logs enviados ao Fabric
CREATE TABLE IF NOT EXISTS sync_control (
    log_id VARCHAR(255) PRIMARY KEY REFERENCES logs(id) ON DELETE CASCADE,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    fabric_hash VARCHAR(64),
    sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed', 'retrying')),
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    CONSTRAINT fk_log FOREIGN KEY (log_id) REFERENCES logs(id)
);

CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_control(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_synced_at ON sync_control(synced_at DESC);

-- View para facilitar consultas de logs não sincronizados
CREATE OR REPLACE VIEW logs_pending_sync AS
SELECT l.*
FROM logs l
LEFT JOIN sync_control sc ON l.id = sc.log_id
WHERE sc.log_id IS NULL OR sc.sync_status IN ('pending', 'failed');

-- Função para marcar log como pendente de sincronização (trigger)
CREATE OR REPLACE FUNCTION mark_log_for_sync()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO sync_control (log_id, sync_status)
    VALUES (NEW.id, 'pending')
    ON CONFLICT (log_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que marca automaticamente novos logs para sincronização
DROP TRIGGER IF EXISTS trigger_mark_log_for_sync ON logs;
CREATE TRIGGER trigger_mark_log_for_sync
    AFTER INSERT ON logs
    FOR EACH ROW
    EXECUTE FUNCTION mark_log_for_sync();

-- Inserir alguns logs de exemplo para teste
INSERT INTO logs (id, timestamp, source, level, message, metadata) VALUES
    ('log001', NOW() - INTERVAL '1 hour', 'api-gateway', 'INFO', 'Application started successfully', '{"version": "1.0.0", "environment": "production"}'),
    ('log002', NOW() - INTERVAL '50 minutes', 'database-connector', 'DEBUG', 'Connection pool initialized', '{"pool_size": 10, "timeout": 30}'),
    ('log003', NOW() - INTERVAL '30 minutes', 'auth-service', 'WARNING', 'High number of failed login attempts', '{"attempts": 15, "user": "admin"}'),
    ('log004', NOW() - INTERVAL '15 minutes', 'payment-worker', 'ERROR', 'Payment processing failed', '{"transaction_id": "TX12345", "amount": 100.50}'),
    ('log005', NOW() - INTERVAL '5 minutes', 'user-service', 'INFO', 'User profile updated', '{"user_id": "U789", "changes": ["email", "phone"]}')
ON CONFLICT (id) DO NOTHING;

-- Grant de permissões
GRANT ALL PRIVILEGES ON TABLE logs TO loguser;
GRANT ALL PRIVILEGES ON TABLE sync_control TO loguser;
GRANT SELECT ON logs_pending_sync TO loguser;

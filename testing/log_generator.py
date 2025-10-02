import json
import random
import datetime
import uuid

# --- Dados de exemplo para gerar logs variados ---
SOURCES = ['api-gateway', 'user-service', 'database-connector', 'auth-service', 'payment-worker']
SEVERITIES = ['INFO', 'DEBUG', 'WARNING', 'ERROR']
MESSAGES = {
    'INFO': 'User successfully authenticated.',
    'DEBUG': 'Cache miss for user_id: {id}. Fetching from DB.',
    'WARNING': 'API response time exceeded threshold: {ms}ms.',
    'ERROR': 'Failed to connect to database after 3 retries.'
}
STACKTRACE_TEMPLATE = """
Traceback (most recent call last):
  File "/app/services/connector.py", line 152, in connect
    self.connection = db.connect(self.dsn)
  File "/usr/lib/python3.9/site-packages/db_driver/__init__.py", line 89, in connect
    raise DBConnectionError("Connection timed out")
db_driver.errors.DBConnectionError: Connection timed out
"""

def generate_log_entry():
    """Gera uma única entrada de log no formato JSON."""
    
    severity = random.choice(SEVERITIES)
    source = random.choice(SOURCES)
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    log_id = str(uuid.uuid4()) # ID único para cada log

    # Cria a mensagem base
    if severity == 'DEBUG':
        message = MESSAGES[severity].format(id=random.randint(1000, 9999))
    elif severity == 'WARNING':
        message = MESSAGES[severity].format(ms=random.randint(200, 1000))
    else:
        message = MESSAGES[severity]

    log_entry = {
        "id": log_id,
        "timestamp": timestamp,
        "source": source,
        "severity": severity,
        "message": message,
        "metadata": {
            "request_id": str(uuid.uuid4()),
            "user_agent": f"python-requests/2.25.{random.randint(1,10)}",
            "remote_ip": f"192.168.1.{random.randint(1, 254)}"
        }
    }

    # Adiciona um stacktrace apenas para logs de ERRO
    if severity == 'ERROR':
        log_entry['stacktrace'] = STACKTRACE_TEMPLATE.strip()

    return log_entry

if __name__ == '__main__':
    # Exemplo de como usar: gera e imprime 3 logs de exemplo
    for _ in range(3):
        print(json.dumps(generate_log_entry(), indent=2))
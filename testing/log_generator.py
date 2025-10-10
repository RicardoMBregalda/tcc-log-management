#!/usr/bin/env python3
"""
Log Generator - Gerador de Logs com Integração Fabric

Gera diferentes tipos e volumes de logs, simulando carga realista,
e envia diretamente para PostgreSQL + Fabric Blockchain.

Características:
- Múltiplos cenários de carga (baixa, média, alta, pico)
- Distribuição realista de severidades (70% INFO, 20% WARNING, 8% ERROR, 2% CRITICAL)
- Diferentes tipos de logs (API, banco de dados, autenticação, pagamento, etc.)
- Taxa de geração configurável (logs/segundo)
- Integração direta com Fabric via insert_and_sync_log.py
- Métricas em tempo real (total, sucessos, falhas, taxa)
"""

import json
import random
import time
import sys
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Adiciona o diretório testing ao path para importar insert_and_sync_log
sys.path.insert(0, str(Path(__file__).parent))

try:
    from insert_and_sync_log import create_and_sync_log
    FABRIC_INTEGRATION = True
except ImportError:
    FABRIC_INTEGRATION = False
    print("Módulo insert_and_sync_log não encontrado. Rodando em modo simulação.")

# ============================================================================
# CONFIGURAÇÃO DE LOGS REALISTAS
# ============================================================================

SOURCES = [
    'api-gateway',
    'user-service', 
    'auth-service',
    'payment-service',
    'order-service',
    'inventory-service',
    'notification-service',
    'database-connector',
    'cache-service',
    'search-service'
]

SEVERITY_WEIGHTS = {
    'DEBUG': 0.05,
    'INFO': 0.65,
    'WARNING': 0.20,
    'ERROR': 0.08,
    'CRITICAL': 0.02
}

LOG_MESSAGES = {
    'DEBUG': [
        'Cache lookup for key: cache_key_{id}',
        'Database query executed in {ms}ms',
        'Request headers: {headers}',
        'Parsing JSON payload with {size} bytes',
        'Token validation started for user_{id}'
    ],
    'INFO': [
        'User user_{id} successfully authenticated',
        'API request completed: {method} {endpoint} - 200 OK',
        'Order order_{id} processed successfully',
        'Payment payment_{id} confirmed - Amount: ${amount}',
        'Database connection pool initialized - {pool_size} connections',
        'Cache invalidated for key: cache_key_{id}',
        'Email notification sent to user_{id}',
        'Inventory updated for product_{id} - Quantity: {qty}',
        'Search index refreshed - {count} documents',
        'Health check passed - All services operational'
    ],
    'WARNING': [
        'API response time exceeded threshold: {ms}ms for {endpoint}',
        'Database connection pool at {percent}% capacity',
        'Retry attempt {retry} for failed request to {service}',
        'Cache hit rate below 60%: current {percent}%',
        'Payment processing delayed - Queue size: {queue_size}',
        'High memory usage detected: {percent}% on {service}',
        'Rate limit approaching for client {client_id}: {rate}/min',
        'Deprecated API endpoint called: {endpoint}',
        'SSL certificate expires in {days} days',
        'Slow query detected: {query} took {ms}ms'
    ],
    'ERROR': [
        'Failed to connect to database after {retries} retries',
        'Payment gateway timeout - Transaction {tx_id}',
        'Authentication failed for user_{id} - Invalid credentials',
        'Failed to process order order_{id} - Insufficient inventory',
        'Message queue connection lost - Attempting reconnection',
        'Invalid API request - Missing required field: {field}',
        'Database query timeout after {timeout}s',
        'Failed to send notification to user_{id} - SMTP error',
        'Cache server unavailable - Redis connection refused',
        'File upload failed - Maximum size exceeded: {size}MB'
    ],
    'CRITICAL': [
        'Database connection pool exhausted - All connections in use',
        'Payment service completely unresponsive - All requests timing out',
        'Security breach detected - Unauthorized access attempt from {ip}',
        'Data corruption detected in table {table}',
        'Out of memory error - Application crash imminent',
        'All authentication servers down - Unable to verify users',
        'Distributed lock acquisition failed - Potential data race condition',
        'Backup system failure - Data loss risk detected'
    ]
}

STACKTRACES = {
    'database': """Traceback (most recent call last):
  File "/app/services/database.py", line 152, in connect
    self.connection = psycopg2.connect(self.dsn)
  File "/usr/lib/python3.9/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
psycopg2.OperationalError: could not connect to server: Connection timed out""",
    
    'payment': """Traceback (most recent call last):
  File "/app/services/payment.py", line 89, in process_payment
    response = requests.post(gateway_url, json=payload, timeout=5.0)
  File "/usr/lib/python3.9/site-packages/requests/api.py", line 117, in post
    return request('post', url, data=data, json=json, **kwargs)
requests.exceptions.Timeout: HTTPSConnectionPool(host='payment.gateway.com', port=443): Read timed out. (read timeout=5.0)""",
    
    'authentication': """Traceback (most recent call last):
  File "/app/services/auth.py", line 67, in verify_token
    payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
  File "/usr/lib/python3.9/site-packages/jwt/api_jwt.py", line 119, in decode
    raise InvalidSignatureError('Signature verification failed')
jwt.exceptions.InvalidSignatureError: Signature verification failed""",
    
    'memory': """Traceback (most recent call last):
  File "/app/services/processor.py", line 234, in process_batch
    result = [self.transform(item) for item in large_dataset]
  File "/app/services/processor.py", line 189, in transform
    return json.loads(data)
MemoryError: Unable to allocate memory for array"""
}

# ============================================================================
# GERADOR DE LOGS
# ============================================================================

class LogGenerator:
    """Gerador de logs com integração Fabric e simulação de carga."""
    
    def __init__(self, fabric_enabled=True):
        self.fabric_enabled = fabric_enabled and FABRIC_INTEGRATION
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'by_severity': {k: 0 for k in SEVERITY_WEIGHTS.keys()}
        }
        self.start_time = time.time()
    
    def generate_log(self):
        severity = random.choices(
            list(SEVERITY_WEIGHTS.keys()),
            weights=list(SEVERITY_WEIGHTS.values())
        )[0]
        
        source = random.choice(SOURCES)
        message_template = random.choice(LOG_MESSAGES[severity])
        message = self._fill_message_template(message_template, severity)
        metadata = self._generate_metadata(source, severity)
        stacktrace = None
        
        if severity in ['ERROR', 'CRITICAL'] and random.random() < 0.7:
            stacktrace = random.choice(list(STACKTRACES.values()))
        
        return {
            'source': source,
            'level': severity,
            'message': message,
            'metadata': metadata,
            'stacktrace': stacktrace
        }
    
    def _fill_message_template(self, template, severity):
        replacements = {
            'id': random.randint(10000, 99999),
            'ms': random.randint(100, 5000) if severity == 'WARNING' else random.randint(10, 200),
            'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            'endpoint': random.choice(['/api/users', '/api/orders', '/api/products', '/api/payments']),
            'amount': random.randint(10, 1000),
            'pool_size': random.randint(10, 50),
            'qty': random.randint(1, 100),
            'count': random.randint(100, 10000),
            'percent': random.randint(70, 99),
            'retry': random.randint(1, 5),
            'service': random.choice(SOURCES),
            'queue_size': random.randint(50, 500),
            'client_id': f"client_{random.randint(1000, 9999)}",
            'rate': random.randint(90, 120),
            'days': random.randint(1, 30),
            'query': 'SELECT * FROM users WHERE...',
            'retries': random.randint(3, 10),
            'tx_id': f"tx_{random.randint(100000, 999999)}",
            'field': random.choice(['user_id', 'amount', 'timestamp', 'token']),
            'timeout': random.randint(5, 30),
            'size': random.randint(10, 100),
            'ip': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            'table': random.choice(['users', 'orders', 'payments', 'inventory']),
            'headers': '{"Content-Type": "application/json"}',
            'cache_key': f"cache_{random.randint(1000, 9999)}"
        }
        
        try:
            return template.format(**replacements)
        except KeyError:
            return template
    
    def _generate_metadata(self, source, severity):
        metadata = {
            'environment': 'production',
            'service_version': f"v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
            'host': f"{source}-{random.randint(1, 5)}",
            'process_id': random.randint(1000, 9999)
        }
        if severity in ['ERROR', 'CRITICAL']:
            metadata['error_code'] = f"ERR_{random.randint(1000, 9999)}"
            metadata['correlation_id'] = f"corr_{random.randint(100000, 999999)}"
        return metadata
    
    def send_log(self, log_data):
        if not self.fabric_enabled:
            print(f"[SIM] {log_data['level']:8} | {log_data['source']:20} | {log_data['message'][:60]}")
            return True
        try:
            result = create_and_sync_log(
                source=log_data['source'],
                level=log_data['level'],
                message=log_data['message'],
                metadata=log_data['metadata'],
                stacktrace=log_data['stacktrace']
            )
            return result['status'] == 'synced'
        except Exception as e:
            print(f"Erro ao enviar log: {e}")
            return False
    
    def generate_and_send(self):
        log_data = self.generate_log()
        success = self.send_log(log_data)
        self.stats['total'] += 1
        self.stats['by_severity'][log_data['level']] += 1
        if success:
            self.stats['success'] += 1
        else:
            self.stats['failed'] += 1
        return success
    
    def print_stats(self):
        elapsed = time.time() - self.start_time
        rate = self.stats['total'] / elapsed if elapsed > 0 else 0
        
        print("\n" + "="*70)
        print(f"ESTATÍSTICAS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)
        print(f"Total:        {self.stats['total']:6} logs")
        print(f"Sucessos:     {self.stats['success']:6} logs")
        print(f"Falhas:       {self.stats['failed']:6} logs")
        print(f"Taxa:         {rate:6.2f} logs/segundo")
        print(f"Tempo:        {elapsed:6.1f} segundos")
        print("-"*70)
        print("Por Severidade:")
        for severity, count in self.stats['by_severity'].items():
            percent = (count / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
            print(f"  {severity:10} {count:6} ({percent:5.1f}%)")
        print("="*70)

# ============================================================================
# CENÁRIOS DE CARGA
# ============================================================================

LOAD_SCENARIOS = {
    'low': {'name': 'Carga Baixa', 'description': 'Tráfego normal durante madrugada', 'logs_per_second': 2, 'duration': 60},
    'medium': {'name': 'Carga Média', 'description': 'Tráfego normal durante o dia', 'logs_per_second': 10, 'duration': 60},
    'high': {'name': 'Carga Alta', 'description': 'Horário de pico', 'logs_per_second': 50, 'duration': 30},
    'spike': {'name': 'Pico de Carga', 'description': 'Evento especial (Black Friday, lançamento)', 'logs_per_second': 100, 'duration': 20},
    'stress': {'name': 'Teste de Estresse', 'description': 'Carga máxima para teste de limites', 'logs_per_second': 200, 'duration': 10}
}

def run_scenario(scenario_name, generator):
    scenario = LOAD_SCENARIOS[scenario_name]
    print(f"\nIniciando: {scenario['name']}")
    print(f"{scenario['description']}")
    print(f"Taxa: {scenario['logs_per_second']} logs/segundo")
    print(f"Duração: {scenario['duration']} segundos")
    print("-"*70)
    
    interval = 1.0 / scenario['logs_per_second']
    end_time = time.time() + scenario['duration']
    
    while time.time() < end_time:
        start = time.time()
        generator.generate_and_send()
        elapsed = time.time() - start
        if elapsed < interval:
            time.sleep(interval - elapsed)
    
    generator.print_stats()

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Gerador de Logs com Integração Fabric',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python log_generator.py -n 100
  python log_generator.py --scenario medium
  python log_generator.py --scenario stress
  python log_generator.py --rate 50 --duration 30
  python log_generator.py -n 50 --no-fabric
        """
    )
    
    parser.add_argument('-n', '--count', type=int, help='Número de logs a gerar')
    parser.add_argument('--scenario', choices=LOAD_SCENARIOS.keys(), help='Cenário de carga predefinido')
    parser.add_argument('--rate', type=float, help='Taxa de geração (logs/segundo)')
    parser.add_argument('--duration', type=int, help='Duração em segundos')
    parser.add_argument('--no-fabric', action='store_true', help='Modo simulação (não envia para Fabric)')
    parser.add_argument('--stats-interval', type=int, default=10, help='Intervalo para mostrar estatísticas (segundos)')
    
    args = parser.parse_args()
    
    if not any([args.count, args.scenario, args.rate]):
        parser.print_help()
        sys.exit(1)
    
    generator = LogGenerator(fabric_enabled=not args.no_fabric)
    
    print("\n" + "="*70)
    print("LOG GENERATOR - Gerador de Logs com Integração Fabric")
    print("="*70)
    print(f"Modo: {'SIMULAÇÃO' if args.no_fabric else 'PRODUÇÃO (PostgreSQL + Fabric)'}")
    print(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        if args.scenario:
            run_scenario(args.scenario, generator)
        elif args.count:
            print(f"\nGerando {args.count} logs...")
            for i in range(args.count):
                generator.generate_and_send()
                if (i + 1) % 10 == 0:
                    print(f"Progresso: {i + 1}/{args.count}")
            generator.print_stats()
        elif args.rate and args.duration:
            print(f"\nTaxa: {args.rate} logs/segundo")
            print(f"Duração: {args.duration} segundos")
            interval = 1.0 / args.rate
            end_time = time.time() + args.duration
            next_stats = time.time() + args.stats_interval
            while time.time() < end_time:
                start = time.time()
                generator.generate_and_send()
                if time.time() >= next_stats:
                    generator.print_stats()
                    next_stats = time.time() + args.stats_interval
                elapsed = time.time() - start
                if elapsed < interval:
                    time.sleep(interval - elapsed)
            generator.print_stats()
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário")
        generator.print_stats()
    
    print(f"\nConcluído: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == '__main__':
    main()

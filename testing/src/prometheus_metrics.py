#!/usr/bin/env python3
"""
Prometheus Metrics Instrumentação para API Flask

Adiciona métricas customizadas para monitoramento:
- Latência de requisições HTTP
- Contadores de requisições por endpoint
- Contadores de erros
- Métricas de blockchain sync
- Métricas de cache Redis
- Métricas de batching Merkle
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
from typing import Callable
from flask import Response

# ========================================
# MÉTRICAS HTTP
# ========================================

# Contador de requisições por método e endpoint
http_requests_total = Counter(
    'flask_http_request_total',
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status']
)

# Histograma de duração de requisições
http_request_duration_seconds = Histogram(
    'flask_http_request_duration_seconds',
    'Duração das requisições HTTP em segundos',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))
)

# Summary para percentis
http_request_duration_summary = Summary(
    'flask_http_request_duration_summary',
    'Summary da duração das requisições HTTP',
    ['method', 'endpoint']
)

# Requisições em andamento
http_requests_in_progress = Gauge(
    'flask_http_requests_in_progress',
    'Número de requisições HTTP em andamento',
    ['method', 'endpoint']
)

# ========================================
# MÉTRICAS DE LOGS
# ========================================

# Total de logs criados
logs_created_total = Counter(
    'logs_created_total',
    'Total de logs criados',
    ['source', 'severity', 'architecture']
)

# Total de logs por severidade (gauge)
logs_by_severity = Gauge(
    'logs_by_severity',
    'Número de logs por severidade',
    ['severity', 'architecture']
)

# Latência de criação de logs
log_creation_duration_seconds = Histogram(
    'log_creation_duration_seconds',
    'Duração da criação de logs em segundos',
    ['architecture'],
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, float('inf'))
)

# ========================================
# MÉTRICAS DE MERKLE TREE
# ========================================

# Total de batches criados
merkle_batches_created_total = Counter(
    'merkle_batches_created_total',
    'Total de batches Merkle criados'
)

# Logs por batch (distribuição)
merkle_logs_per_batch = Histogram(
    'merkle_logs_per_batch',
    'Número de logs por batch Merkle',
    buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, float('inf'))
)

# Tempo de criação de batch
merkle_batch_creation_duration_seconds = Histogram(
    'merkle_batch_creation_duration_seconds',
    'Duração da criação de batch Merkle em segundos',
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf'))
)

# Verificações de integridade
merkle_verifications_total = Counter(
    'merkle_verifications_total',
    'Total de verificações de integridade',
    ['result']  # success, failure
)

# Detecções de adulteração
merkle_tampering_detected_total = Counter(
    'merkle_tampering_detected_total',
    'Total de adulterações detectadas',
    ['log_id']
)

# ========================================
# MÉTRICAS DE BLOCKCHAIN SYNC
# ========================================

# Total de sincronizações
blockchain_syncs_total = Counter(
    'blockchain_syncs_total',
    'Total de sincronizações com blockchain',
    ['status']  # success, failure
)

# Duração de sincronização
blockchain_sync_duration_seconds = Histogram(
    'blockchain_sync_duration_seconds',
    'Duração da sincronização com blockchain em segundos',
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float('inf'))
)

# Tamanho da fila de sincronização
blockchain_sync_queue_size = Gauge(
    'blockchain_sync_queue_size',
    'Tamanho da fila de sincronização'
)

# Latência de transação blockchain
blockchain_transaction_duration_seconds = Histogram(
    'blockchain_transaction_duration_seconds',
    'Duração de transações no blockchain em segundos',
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float('inf'))
)

# ========================================
# MÉTRICAS DE CACHE REDIS
# ========================================

# Cache hits
cache_hits_total = Counter(
    'cache_hits_total',
    'Total de cache hits',
    ['operation']
)

# Cache misses
cache_misses_total = Counter(
    'cache_misses_total',
    'Total de cache misses',
    ['operation']
)

# Taxa de cache hit (gauge calculado)
cache_hit_ratio = Gauge(
    'cache_hit_ratio',
    'Taxa de cache hit (%)',
    ['operation']
)

# Latência de operações no cache
cache_operation_duration_seconds = Histogram(
    'cache_operation_duration_seconds',
    'Duração de operações no cache em segundos',
    ['operation'],
    buckets=(0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, float('inf'))
)

# ========================================
# MÉTRICAS DE MONGODB
# ========================================

# Operações no MongoDB
mongodb_operations_total = Counter(
    'mongodb_operations_total',
    'Total de operações no MongoDB',
    ['operation', 'collection', 'status']
)

# Latência de operações no MongoDB
mongodb_operation_duration_seconds = Histogram(
    'mongodb_operation_duration_seconds',
    'Duração de operações no MongoDB em segundos',
    ['operation', 'collection'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, float('inf'))
)

# Tamanho de documentos
mongodb_document_size_bytes = Histogram(
    'mongodb_document_size_bytes',
    'Tamanho de documentos no MongoDB em bytes',
    ['collection'],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, float('inf'))
)

# ========================================
# MÉTRICAS DE SISTEMA
# ========================================

# Uso de memória da aplicação
app_memory_usage_bytes = Gauge(
    'app_memory_usage_bytes',
    'Uso de memória da aplicação em bytes'
)

# Threads ativos
app_active_threads = Gauge(
    'app_active_threads',
    'Número de threads ativos na aplicação'
)

# Uptime da aplicação
app_uptime_seconds = Gauge(
    'app_uptime_seconds',
    'Tempo que a aplicação está rodando em segundos'
)

# ========================================
# DECORATORS PARA INSTRUMENTAÇÃO
# ========================================

def track_request_metrics(endpoint: str):
    """
    Decorator para rastrear métricas de requisições HTTP
    
    Usage:
        @app.route('/logs')
        @track_request_metrics('logs_list')
        def list_logs():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            method = 'GET'  # Pode ser extraído do request.method
            
            # Incrementa requests in progress
            http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
            
            # Mede duração
            start_time = time.time()
            try:
                response = func(*args, **kwargs)
                status = 200  # Pode ser extraído da response
                return response
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                
                # Atualiza métricas
                http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
                http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
                http_request_duration_summary.labels(method=method, endpoint=endpoint).observe(duration)
                http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
        
        return wrapper
    return decorator


def track_log_creation(architecture: str):
    """
    Decorator para rastrear criação de logs
    
    Usage:
        @track_log_creation('hybrid')
        def create_log(log_data):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Extrai informações do log (assumindo que retorna log_data)
                if isinstance(result, dict):
                    source = result.get('source', 'unknown')
                    severity = result.get('severity', 'INFO')
                    
                    logs_created_total.labels(
                        source=source,
                        severity=severity,
                        architecture=architecture
                    ).inc()
                
                return result
            finally:
                duration = time.time() - start_time
                log_creation_duration_seconds.labels(architecture=architecture).observe(duration)
        
        return wrapper
    return decorator


# ========================================
# ENDPOINT DE MÉTRICAS
# ========================================

def metrics_endpoint() -> Response:
    """
    Endpoint para expor métricas ao Prometheus
    
    Usage no Flask:
        @app.route('/metrics')
        def metrics():
            return metrics_endpoint()
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def update_cache_hit_ratio(operation: str, hits: int, misses: int) -> None:
    """Atualiza taxa de cache hit"""
    total = hits + misses
    if total > 0:
        ratio = (hits / total) * 100
        cache_hit_ratio.labels(operation=operation).set(ratio)


def record_blockchain_sync(status: str, duration: float) -> None:
    """Registra sincronização com blockchain"""
    blockchain_syncs_total.labels(status=status).inc()
    blockchain_sync_duration_seconds.observe(duration)


def record_merkle_batch(log_count: int, duration: float) -> None:
    """Registra criação de batch Merkle"""
    merkle_batches_created_total.inc()
    merkle_logs_per_batch.observe(log_count)
    merkle_batch_creation_duration_seconds.observe(duration)


def record_tampering_detection(log_id: str) -> None:
    """Registra detecção de adulteração"""
    merkle_tampering_detected_total.labels(log_id=log_id).inc()


# ========================================
# EXEMPLO DE USO
# ========================================

if __name__ == '__main__':
    print("📊 Prometheus Metrics Instrumentation")
    print("=" * 50)
    print("\nMétricas disponíveis:")
    print("- HTTP: requests, duration, in_progress")
    print("- Logs: created, by_severity, duration")
    print("- Merkle: batches, verifications, tampering")
    print("- Blockchain: syncs, transactions, queue_size")
    print("- Cache: hits, misses, hit_ratio")
    print("- MongoDB: operations, duration, doc_size")
    print("- System: memory, threads, uptime")
    print("\n✅ Pronto para integração com Flask API!")

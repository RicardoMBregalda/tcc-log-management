#!/usr/bin/env python3
"""
Performance Tester - Testes de Carga e Performance

Compara performance entre:
- PostgreSQL Tradicional
- MongoDB + Fabric Híbrido

Métricas coletadas:
- Throughput (transações/segundo)
- Latência (tempo de resposta)
- Uso de recursos (CPU, Memória, Disco)
"""

import time
import psutil
import psycopg2
import requests
import json
import sys
import threading
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Adiciona o diretório pai ao path para importar config e utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports locais
from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, 
    POSTGRES_USER, POSTGRES_PASSWORD,
    API_BASE_URL, API_TIMEOUT,
    get_postgres_connection_string,
    get_test_scenario
)
from utils import (
    print_header, print_section, format_bytes, format_duration,
    save_json, load_json, get_timestamp, get_timestamp_filename,
    calculate_percentile, calculate_statistics,
    ProgressTracker, ensure_directory
)


class PerformanceMonitor:
    """Monitor de recursos do sistema"""
    
    def __init__(self) -> None:
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.disk_samples: List[Dict[str, int]] = []
        self.monitoring: bool = False
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Inicia monitoramento de recursos em background"""
        self.monitoring = True
        self.cpu_samples = []
        self.memory_samples = []
        self.disk_samples = []
        
        def monitor_loop() -> None:
            while self.monitoring:
                self.collect_sample()
                time.sleep(1)  # Coleta a cada 1 segundo
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def collect_sample(self) -> None:
        """Coleta uma amostra de recursos"""
        if self.monitoring:
            self.cpu_samples.append(psutil.cpu_percent(interval=0.1))
            self.memory_samples.append(psutil.virtual_memory().percent)
            disk = psutil.disk_io_counters()
            if disk:
                self.disk_samples.append({
                    'read_bytes': disk.read_bytes,
                    'write_bytes': disk.write_bytes
                })
    
    def stop(self) -> Dict[str, Any]:
        """Para monitoramento e retorna estatísticas"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        return self.get_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas coletadas usando funções de utils.py"""
        # Calcula diferença de disco
        disk_read = 0
        disk_write = 0
        if len(self.disk_samples) >= 2:
            disk_read = self.disk_samples[-1]['read_bytes'] - self.disk_samples[0]['read_bytes']
            disk_write = self.disk_samples[-1]['write_bytes'] - self.disk_samples[0]['write_bytes']
        
        # Usa calculate_statistics de utils.py
        cpu_stats = calculate_statistics(self.cpu_samples) if self.cpu_samples else {
            'mean': 0, 'max': 0, 'min': 0, 'median': 0, 'p50': 0, 'p95': 0, 'p99': 0
        }
        memory_stats = calculate_statistics(self.memory_samples) if self.memory_samples else {
            'mean': 0, 'max': 0, 'min': 0, 'median': 0, 'p50': 0, 'p95': 0, 'p99': 0
        }
        
        return {
            'cpu': {
                'avg': cpu_stats['mean'],
                'max': cpu_stats['max'],
                'min': cpu_stats['min']
            },
            'memory': {
                'avg': memory_stats['mean'],
                'max': memory_stats['max'],
                'min': memory_stats['min']
            },
            'disk': {
                'read_mb': disk_read / (1024 * 1024),
                'write_mb': disk_write / (1024 * 1024)
            }
        }
    
    # Métodos legados para compatibilidade
    def start_monitoring(self) -> None:
        """Alias para start()"""
        self.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Alias para stop()"""
        return self.stop()




class PostgreSQLTester:
    """Testa performance do PostgreSQL tradicional"""
    
    def __init__(self) -> None:
        self.conn: Optional[Any] = None
    
    def connect(self) -> None:
        """Conecta ao PostgreSQL usando configurações de config.py"""
        self.conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
    
    def disconnect(self) -> None:
        """Desconecta do PostgreSQL"""
        if self.conn:
            self.conn.close()
    
    def insert_log(self, log_data: Dict[str, Any]) -> None:
        """Insere um log diretamente no PostgreSQL"""
        cursor = self.conn.cursor()
        query = """
            INSERT INTO logs (id, timestamp, source, level, message, metadata, stacktrace)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            log_data['id'],
            log_data['timestamp'],
            log_data['source'],
            log_data['level'],
            log_data['message'],
            json.dumps(log_data.get('metadata', {})),
            log_data.get('stacktrace')  # Optional stacktrace field
        ))
        self.conn.commit()
        cursor.close()
    
    def query_logs(self, source: str) -> List[Tuple]:
        """Consulta logs por source"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM logs WHERE source = %s LIMIT 100", (source,))
        results = cursor.fetchall()
        cursor.close()
        return results


class HybridTester:
    """Testa performance da arquitetura híbrida (MongoDB + Fabric)"""

    def insert_log_via_api(self, log_data: Dict[str, Any]) -> bool:
        """Insere log via API (MongoDB + Fabric)"""
        response = requests.post(
            f"{API_BASE_URL}/logs",
            json=log_data,
            timeout=API_TIMEOUT
        )
        return response.status_code == 201
    
    def query_logs_via_api(self, source: str) -> Optional[Dict]:
        """Consulta logs via API"""
        response = requests.get(
            f"{API_BASE_URL}/logs?source={source}",
            timeout=API_TIMEOUT
        )
        return response.json() if response.status_code == 200 else None


def generate_test_log(index: int) -> Dict[str, Any]:
    """Gera dados de log para teste"""
    level = ['INFO', 'WARNING', 'ERROR'][index % 3]
    
    log_data = {
        'id': f'perf_test_{index}_{int(time.time() * 1000)}',
        'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source': f'test-service-{index % 10}',
        'level': level,
        'message': f'Performance test message {index}',
        'metadata': {
            'test_id': index,
            'batch': int(index / 100)
        }
    }
    
    # Add stacktrace for ERROR logs
    if level == 'ERROR':
        log_data['stacktrace'] = f'File "/app/service.py", line {42 + (index % 100)}, in process_request\n  raise TestException("Simulated error for testing")'
    
    return log_data



def run_insert_test(tester: Any, duration: int, concurrency: int, test_type: str) -> Dict[str, Any]:
    """Executa teste de inserção"""
    print(f"\n[{test_type}] Teste de INSERÇÃO")
    print(f"Duração: {duration}s | Concorrência: {concurrency}")
    print("-" * 60)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    results: Dict[str, Any] = {
        'total_transactions': 0,
        'successful': 0,
        'failed': 0,
        'latencies': []
    }
    
    start_time = time.time()
    end_time = start_time + duration
    counter = 0
    
    def insert_single_log(index: int) -> Tuple[bool, float]:
        """Insere um único log e mede latência"""
        log_data = generate_test_log(index)
        insert_start = time.time()
        
        try:
            if test_type == 'PostgreSQL':
                tester.insert_log(log_data)
            else:  # Hybrid
                tester.insert_log_via_api(log_data)
            
            latency = (time.time() - insert_start) * 1000  # em ms
            return True, latency
        except Exception as e:
            return False, 0.0
    
    # Executa inserções com concorrência
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        while time.time() < end_time:
            monitor.collect_sample()
            
            futures = []
            for _ in range(concurrency):
                futures.append(executor.submit(insert_single_log, counter))
                counter += 1
            
            for future in as_completed(futures):
                results['total_transactions'] += 1
                success, latency = future.result()
                if success:
                    results['successful'] += 1
                    results['latencies'].append(latency)
                else:
                    results['failed'] += 1
    
    elapsed = time.time() - start_time
    resources = monitor.stop_monitoring()
    
    # Usa calculate_statistics de utils.py
    latency_stats = calculate_statistics(results['latencies']) if results['latencies'] else {
        'mean': 0, 'median': 0, 'p50': 0, 'p95': 0, 'p99': 0, 'min': 0, 'max': 0
    }
    
    # Calcula estatísticas
    results['duration'] = elapsed
    results['throughput'] = results['successful'] / elapsed
    results['latency'] = {
        'avg': latency_stats['mean'],
        'median': latency_stats['median'],
        'p95': latency_stats['p95'],
        'p99': latency_stats['p99'],
        'min': latency_stats['min'],
        'max': latency_stats['max']
    }
    results['resources'] = resources
    
    return results



def run_query_test(tester: Any, num_queries: int, concurrency: int, test_type: str) -> Dict[str, Any]:
    """Executa teste de consulta"""
    print(f"\n[{test_type}] Teste de CONSULTA")
    print(f"Consultas: {num_queries} | Concorrência: {concurrency}")
    print("-" * 60)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    results: Dict[str, Any] = {
        'total_queries': 0,
        'successful': 0,
        'failed': 0,
        'latencies': []
    }
    
    start_time = time.time()
    
    def query_single(index: int) -> Tuple[bool, float]:
        """Executa uma consulta e mede latência"""
        source = f'test-service-{index % 10}'
        query_start = time.time()
        
        try:
            if test_type == 'PostgreSQL':
                tester.query_logs(source)
            else:  # Hybrid
                tester.query_logs_via_api(source)
            
            latency = (time.time() - query_start) * 1000
            return True, latency
        except Exception as e:
            return False, 0.0
    
    # Executa consultas com concorrência
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(num_queries):
            monitor.collect_sample()
            futures.append(executor.submit(query_single, i))
        
        for future in as_completed(futures):
            results['total_queries'] += 1
            success, latency = future.result()
            if success:
                results['successful'] += 1
                results['latencies'].append(latency)
            else:
                results['failed'] += 1
    
    elapsed = time.time() - start_time
    resources = monitor.stop_monitoring()
    
    # Usa calculate_statistics de utils.py
    latency_stats = calculate_statistics(results['latencies']) if results['latencies'] else {
        'mean': 0, 'median': 0, 'p50': 0, 'p95': 0, 'p99': 0, 'min': 0, 'max': 0
    }
    
    # Calcula estatísticas
    results['duration'] = elapsed
    results['throughput'] = results['successful'] / elapsed if elapsed > 0 else 0
    results['latency'] = {
        'avg': latency_stats['mean'],
        'median': latency_stats['median'],
        'p95': latency_stats['p95'],
        'p99': latency_stats['p99'],
        'min': latency_stats['min'],
        'max': latency_stats['max']
    }
    results['resources'] = resources
    
    return results



def print_results(test_name: str, results: Dict[str, Any]) -> None:
    """Imprime resultados de um teste usando funções de utils.py"""
    print_section(f"Resultados - {test_name}")
    
    transactions_or_queries = results.get('total_transactions', results.get('total_queries', 0))
    print(f"Transações/Consultas: {transactions_or_queries}")
    print(f"Sucesso: {results['successful']}")
    print(f"Falhas: {results['failed']}")
    print(f"Duração: {format_duration(results['duration'])}")
    print(f"\nTHROUGHPUT: {results['throughput']:.2f} ops/segundo")
    print(f"\nLATÊNCIA (ms):")
    print(f"  Média:   {results['latency']['avg']:.2f}")
    print(f"  Mediana: {results['latency']['median']:.2f}")
    print(f"  P95:     {results['latency']['p95']:.2f}")
    print(f"  P99:     {results['latency']['p99']:.2f}")
    print(f"  Mín:     {results['latency']['min']:.2f}")
    print(f"  Máx:     {results['latency']['max']:.2f}")
    print(f"\nRECURSOS:")
    print(f"  CPU (%):")
    print(f"    Média: {results['resources']['cpu']['avg']:.1f}%")
    print(f"    Máx:   {results['resources']['cpu']['max']:.1f}%")
    print(f"  Memória (%):")
    print(f"    Média: {results['resources']['memory']['avg']:.1f}%")
    print(f"    Máx:   {results['resources']['memory']['max']:.1f}%")
    print(f"  Disco:")
    print(f"    Leitura:  {format_bytes(results['resources']['disk']['read_mb'] * 1024 * 1024)}")
    print(f"    Escrita:  {format_bytes(results['resources']['disk']['write_mb'] * 1024 * 1024)}")


def save_results_json(all_results: Dict[str, Any], filename: str = 'performance_results.json') -> None:
    """Salva resultados em JSON usando utils.py"""
    save_json(all_results, filename)
    print(f"\nResultados salvos em: {filename}")


def main() -> int:
    """Executa bateria completa de testes"""
    print_header("TESTES DE PERFORMANCE - TCC LOG MANAGEMENT")

    print("\nComparando:")
    print("1. PostgreSQL Tradicional")
    print("2. MongoDB + Fabric Híbrido")
    print()
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }
    
    # Configuração de testes
    duration = 30  # segundos
    concurrency = 10
    num_queries = 100
    
    print(f"\nConfiguração dos testes:")
    print(f"  Duração inserção: {duration}s")
    print(f"  Concorrência: {concurrency}")
    print(f"  Consultas: {num_queries}")
    
    input("\nPressione ENTER para iniciar os testes...")
    
    # ========================================================================
    # TESTE 1: PostgreSQL Tradicional - Inserção
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("TESTE 1: PostgreSQL Tradicional - INSERÇÃO")
    print("=" * 70)
    
    pg_tester = PostgreSQLTester()
    pg_tester.connect()
    
    pg_insert_results = run_insert_test(pg_tester, duration, concurrency, 'PostgreSQL')
    print_results("PostgreSQL - Inserção", pg_insert_results)
    
    all_results['tests'].append({
        'name': 'PostgreSQL - Inserção',
        'type': 'insert',
        'architecture': 'postgresql',
        'results': pg_insert_results
    })
    
    # ========================================================================
    # TESTE 2: PostgreSQL Tradicional - Consulta
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("TESTE 2: PostgreSQL Tradicional - CONSULTA")
    print("=" * 70)
    
    pg_query_results = run_query_test(pg_tester, num_queries, concurrency, 'PostgreSQL')
    print_results("PostgreSQL - Consulta", pg_query_results)
    
    pg_tester.disconnect()
    
    all_results['tests'].append({
        'name': 'PostgreSQL - Consulta',
        'type': 'query',
        'architecture': 'postgresql',
        'results': pg_query_results
    })
    
    # ========================================================================
    # TESTE 3: Híbrido - Inserção
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("TESTE 3: MongoDB + Fabric Híbrido - INSERÇÃO")
    print("=" * 70)
    
    hybrid_tester = HybridTester()
    
    hybrid_insert_results = run_insert_test(hybrid_tester, duration, concurrency, 'Hybrid')
    print_results("Híbrido - Inserção", hybrid_insert_results)
    
    all_results['tests'].append({
        'name': 'Híbrido - Inserção',
        'type': 'insert',
        'architecture': 'hybrid',
        'results': hybrid_insert_results
    })
    
    # ========================================================================
    # TESTE 4: Híbrido - Consulta
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("TESTE 4: MongoDB + Fabric Híbrido - CONSULTA")
    print("=" * 70)
    
    hybrid_query_results = run_query_test(hybrid_tester, num_queries, concurrency, 'Hybrid')
    print_results("Híbrido - Consulta", hybrid_query_results)
    
    all_results['tests'].append({
        'name': 'Híbrido - Consulta',
        'type': 'query',
        'architecture': 'hybrid',
        'results': hybrid_query_results
    })
    
    # ========================================================================
    # COMPARAÇÃO FINAL
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("ANÁLISE COMPARATIVA")
    print("=" * 70)
    
    print("\n1. THROUGHPUT (operações/segundo)")
    print("-" * 60)
    print(f"{'Teste':<30} {'PostgreSQL':>15} {'Híbrido':>15}")
    print("-" * 60)
    print(f"{'Inserção':<30} {pg_insert_results['throughput']:>15.2f} {hybrid_insert_results['throughput']:>15.2f}")
    print(f"{'Consulta':<30} {pg_query_results['throughput']:>15.2f} {hybrid_query_results['throughput']:>15.2f}")
    
    print("\n2. LATÊNCIA MÉDIA (ms)")
    print("-" * 60)
    print(f"{'Teste':<30} {'PostgreSQL':>15} {'Híbrido':>15}")
    print("-" * 60)
    print(f"{'Inserção':<30} {pg_insert_results['latency']['avg']:>15.2f} {hybrid_insert_results['latency']['avg']:>15.2f}")
    print(f"{'Consulta':<30} {pg_query_results['latency']['avg']:>15.2f} {hybrid_query_results['latency']['avg']:>15.2f}")
    
    print("\n3. USO DE RECURSOS (Média)")
    print("-" * 60)
    print(f"{'Métrica':<30} {'PostgreSQL':>15} {'Híbrido':>15}")
    print("-" * 60)
    print(f"{'CPU % (Inserção)':<30} {pg_insert_results['resources']['cpu']['avg']:>14.1f}% {hybrid_insert_results['resources']['cpu']['avg']:>14.1f}%")
    print(f"{'CPU % (Consulta)':<30} {pg_query_results['resources']['cpu']['avg']:>14.1f}% {hybrid_query_results['resources']['cpu']['avg']:>14.1f}%")
    print(f"{'Memória % (Inserção)':<30} {pg_insert_results['resources']['memory']['avg']:>14.1f}% {hybrid_insert_results['resources']['memory']['avg']:>14.1f}%")
    print(f"{'Memória % (Consulta)':<30} {pg_query_results['resources']['memory']['avg']:>14.1f}% {hybrid_query_results['resources']['memory']['avg']:>14.1f}%")
    
    # Salva resultados
    save_results_json(all_results)
    
    print_header("TESTES CONCLUÍDOS")
    
    return 0


# ========================================
# MATRIZ DE CENÁRIOS TCC
# ========================================

def load_test_scenarios() -> Dict[str, Any]:
    """Carrega configurações dos cenários de teste usando utils.py"""
    scenarios_file = Path(__file__).parent / 'test_scenarios.json'
    return load_json(str(scenarios_file))


def run_single_scenario(scenario: Dict[str, Any], architecture: str = 'hybrid') -> Dict[str, Any]:
    """
    Executa um único cenário de teste
    
    Args:
        scenario: Dicionário com configuração do cenário
        architecture: 'hybrid' ou 'postgres'
    
    Returns:
        dict: Resultados do cenário
    """
    print(f"\n{'='*70}")
    print(f"EXECUTANDO: {scenario['name']} ({scenario['id']})")
    print(f"Arquitetura: {architecture.upper()}")
    print(f"{'='*70}")
    print(f"Volume: {scenario['total_logs']:,} logs")
    print(f"Taxa: {scenario['rate']} logs/segundo")
    print(f"Duração estimada: {scenario['expected_duration_seconds']}s")
    print(f"{'='*70}\n")
    
    total_logs = scenario['total_logs']
    target_rate = scenario['rate']
    
    # Calcula número de threads para atingir a taxa desejada
    # Assumindo ~100ms por inserção, ajusta threads para atingir taxa
    workers = max(1, min(target_rate // 10, 100))
    
    # Inicializa monitor de recursos
    monitor = PerformanceMonitor()
    monitor.start()
    
    # Variáveis para métricas
    insert_latencies = []
    start_time = time.time()
    successful_inserts = 0
    failed_inserts = 0
    
    print(f"Iniciando inserção com {workers} workers...")
    
    # Função de inserção baseada na arquitetura
    def insert_log_worker(index):
        log_data = generate_test_log(index)
        insert_start = time.time()
        
        try:
            if architecture == 'postgres':
                # Usa PostgreSQLTester
                if not hasattr(insert_log_worker, 'pg_tester'):
                    insert_log_worker.pg_tester = PostgreSQLTester()
                    insert_log_worker.pg_tester.connect()
                insert_log_worker.pg_tester.insert_log(log_data)
            else:  # hybrid
                # Usa HybridTester (API)
                if not hasattr(insert_log_worker, 'hybrid_tester'):
                    insert_log_worker.hybrid_tester = HybridTester()
                insert_log_worker.hybrid_tester.insert_log_via_api(log_data)
            
            latency = (time.time() - insert_start) * 1000  # ms
            return ('success', latency)
        except Exception as e:
            return ('error', 0)
    
    # Controle de taxa (rate limiting)
    batch_size = 100  # Processa em lotes
    batches = total_logs // batch_size
    delay_between_batches = batch_size / target_rate if target_rate > 0 else 0
    
    logs_inserted = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for batch_num in range(batches + 1):
            batch_start_time = time.time()
            
            # Determina quantos logs neste batch
            if batch_num < batches:
                batch_count = batch_size
            else:
                batch_count = total_logs % batch_size
            
            if batch_count == 0:
                break
            
            # Submete batch de inserções
            futures = []
            for i in range(batch_count):
                log_index = logs_inserted + i
                future = executor.submit(insert_log_worker, log_index)
                futures.append(future)
            
            # Aguarda conclusão do batch
            for future in as_completed(futures):
                status, latency = future.result()
                if status == 'success':
                    successful_inserts += 1
                    insert_latencies.append(latency)
                else:
                    failed_inserts += 1
            
            logs_inserted += batch_count
            
            # Progresso
            if logs_inserted % (total_logs // 10) == 0:
                progress = (logs_inserted / total_logs) * 100
                elapsed = time.time() - start_time
                rate_actual = logs_inserted / elapsed if elapsed > 0 else 0
                print(f"  Progresso: {progress:.1f}% - {logs_inserted:,}/{total_logs:,} logs - Taxa: {rate_actual:.1f} logs/s")
            
            # Rate limiting - aguarda tempo necessário
            batch_elapsed = time.time() - batch_start_time
            if batch_elapsed < delay_between_batches:
                time.sleep(delay_between_batches - batch_elapsed)
    
    # Para monitor
    monitor.stop()
    total_time = time.time() - start_time
    
    # Calcula métricas usando calculate_statistics de utils.py
    actual_throughput = successful_inserts / total_time if total_time > 0 else 0
    
    if insert_latencies:
        latency_stats = calculate_statistics(insert_latencies)
        p50_insert = latency_stats['p50']
        p95_insert = latency_stats['p95']
        p99_insert = latency_stats['p99']
        avg_insert = latency_stats['mean']
    else:
        p50_insert = p95_insert = p99_insert = avg_insert = 0
    
    # Recursos
    resource_stats = monitor.get_stats()
    
    # Resultado
    result = {
        'scenario_id': scenario['id'],
        'scenario_name': scenario['name'],
        'architecture': architecture,
        'config': {
            'total_logs': total_logs,
            'target_rate': target_rate,
            'workers': workers
        },
        'execution': {
            'total_time_seconds': round(total_time, 2),
            'successful_inserts': successful_inserts,
            'failed_inserts': failed_inserts,
            'actual_throughput_logs_per_second': round(actual_throughput, 2)
        },
        'latency_insert_ms': {
            'p50': round(p50_insert, 2),
            'p95': round(p95_insert, 2),
            'p99': round(p99_insert, 2),
            'avg': round(avg_insert, 2)
        },
        'resources': resource_stats,
        'timestamp': datetime.now().isoformat()
    }
    
    # Imprime resumo
    print(f"\n{'='*70}")
    print(f"RESULTADO: {scenario['name']} - {architecture.upper()}")
    print(f"{'='*70}")
    print(f"Logs processados: {successful_inserts:,}/{total_logs:,}")
    print(f"Tempo total: {total_time:.2f}s")
    print(f"Throughput: {actual_throughput:.2f} logs/s (alvo: {target_rate})")
    print(f"Latência P50: {p50_insert:.2f}ms | P95: {p95_insert:.2f}ms | P99: {p99_insert:.2f}ms")
    print(f"CPU médio: {resource_stats['cpu']['avg']:.1f}% | RAM: {resource_stats['memory']['avg']:.1f}%")
    print(f"{'='*70}\n")
    
    return result


def run_all_scenarios(architectures: List[str] = None) -> List[Dict[str, Any]]:
    """
    Executa todos os 9 cenários para cada arquitetura
    
    Args:
        architectures: Lista de arquiteturas a testar ['hybrid', 'postgres']
    
    Returns:
        list: Resultados de todos os cenários
    """
    if architectures is None:
        architectures = ['hybrid', 'postgres']
    
    print_header("MATRIZ DE CENÁRIOS DE TESTE - TCC")
    print("9 Cenários: 3 Volumes × 3 Taxas")
    print("Arquiteturas: " + ", ".join([a.upper() for a in architectures]))
    print("=" * 70 + "\n")
    
    # Carrega cenários
    config = load_test_scenarios()
    scenarios = config['scenarios']
    
    all_results = []
    
    for architecture in architectures:
        for scenario in scenarios:
            result = run_single_scenario(scenario, architecture)
            all_results.append(result)
            
            # Salva resultado individual
            save_scenario_result(result)
            
            # Pausa entre cenários
            print("\nAguardando 10s antes do próximo cenário...")
            time.sleep(10)
    
    # Salva resultados consolidados
    save_consolidated_results(all_results)
    
    # Gera relatório consolidado
    generate_consolidated_report(all_results)
    
    print("\n" + "="*70)
    print("TODOS OS CENÁRIOS CONCLUÍDOS!")
    print(f"Total de cenários executados: {len(all_results)}")
    print(f"Resultados salvos em: testing/results/")
    print("="*70 + "\n")
    
    return all_results


def save_scenario_result(result: Dict[str, Any]) -> None:
    """Salva resultado individual de um cenário usando utils.py"""
    results_dir = Path(__file__).parent / 'results'
    ensure_directory(str(results_dir))
    
    filename = f"scenario_{result['scenario_id']}_{result['architecture']}.json"
    filepath = results_dir / filename
    
    save_json(result, str(filepath))
    print(f"✓ Resultado salvo: {filename}")


def save_consolidated_results(all_results: List[Dict[str, Any]]) -> None:
    """Salva todos os resultados em um único arquivo usando utils.py"""
    results_dir = Path(__file__).parent / 'results'
    ensure_directory(str(results_dir))
    
    # JSON
    json_file = results_dir / 'all_scenarios.json'
    save_json(all_results, str(json_file))
    
    # CSV
    csv_file = results_dir / 'all_scenarios.csv'
    with open(csv_file, 'w') as f:
        # Header
        f.write("scenario_id,scenario_name,architecture,total_logs,target_rate,")
        f.write("actual_throughput,total_time_seconds,")
        f.write("latency_p50_ms,latency_p95_ms,latency_p99_ms,")
        f.write("cpu_avg,ram_avg\n")
        
        # Data
        for r in all_results:
            f.write(f"{r['scenario_id']},{r['scenario_name']},{r['architecture']},")
            f.write(f"{r['config']['total_logs']},{r['config']['target_rate']},")
            f.write(f"{r['execution']['actual_throughput_logs_per_second']},")
            f.write(f"{r['execution']['total_time_seconds']},")
            f.write(f"{r['latency_insert_ms']['p50']},")
            f.write(f"{r['latency_insert_ms']['p95']},")
            f.write(f"{r['latency_insert_ms']['p99']},")
            f.write(f"{r['resources']['cpu']['avg']},")
            f.write(f"{r['resources']['memory']['avg']}\n")
    
    print(f"✓ Resultados consolidados salvos: all_scenarios.json e all_scenarios.csv")


def generate_consolidated_report(all_results: List[Dict[str, Any]]) -> None:
    """Gera relatório consolidado em Markdown"""
    results_dir = Path(__file__).parent / 'results'
    report_file = results_dir / 'consolidated_report.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Relatório Consolidado - Matriz de Cenários TCC\n\n")
        f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Cenários Testados\n\n")
        f.write("| ID | Nome | Volume | Taxa (logs/s) |\n")
        f.write("|---|---|---|---|\n")
        
        scenarios = {}
        for r in all_results:
            if r['scenario_id'] not in scenarios:
                scenarios[r['scenario_id']] = r
                f.write(f"| {r['scenario_id']} | {r['scenario_name']} | ")
                f.write(f"{r['config']['total_logs']:,} | {r['config']['target_rate']} |\n")
        
        f.write("\n## Resultados por Cenário\n\n")
        
        # Agrupa por cenário
        by_scenario = {}
        for r in all_results:
            sid = r['scenario_id']
            if sid not in by_scenario:
                by_scenario[sid] = []
            by_scenario[sid].append(r)
        
        for sid in sorted(by_scenario.keys()):
            results = by_scenario[sid]
            f.write(f"### {sid}: {results[0]['scenario_name']}\n\n")
            
            f.write("| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            
            for r in results:
                f.write(f"| {r['architecture'].upper()} | ")
                f.write(f"{r['execution']['actual_throughput_logs_per_second']:.2f} | ")
                f.write(f"{r['latency_insert_ms']['p50']:.2f} | ")
                f.write(f"{r['latency_insert_ms']['p95']:.2f} | ")
                f.write(f"{r['latency_insert_ms']['p99']:.2f} | ")
                f.write(f"{r['resources']['cpu']['avg']:.1f} | ")
                f.write(f"{r['resources']['memory']['avg']:.1f} |\n")
            
            f.write("\n")
        
        f.write("## Análise Comparativa\n\n")
        f.write("*Ver análise detalhada em analyze_results.py*\n")
    
    print(f"✓ Relatório consolidado gerado: consolidated_report.md")


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--all-scenarios':
            # Executa matriz completa de cenários
            run_all_scenarios(architectures=['hybrid', 'postgres'])
            sys.exit(0)
        else:
            # Executa teste padrão
            sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTestes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nErro durante execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

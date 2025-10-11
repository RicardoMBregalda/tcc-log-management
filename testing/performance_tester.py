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
import statistics
import json
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Adiciona o diretório testing ao path
sys.path.insert(0, str(Path(__file__).parent))

# Configurações
POSTGRES_HOST = 'localhost'
POSTGRES_PORT = 5432
POSTGRES_DB = 'logdb'
POSTGRES_USER = 'logadmin'
POSTGRES_PASSWORD = 'logpassword'
API_BASE_URL = 'http://localhost:5001'  # API Otimizada na porta 5001

# Configurações de teste
TEST_DURATIONS = [10, 30, 60]  # Duração dos testes em segundos
CONCURRENCY_LEVELS = [1, 5, 10, 20, 50]  # Níveis de concorrência


class PerformanceMonitor:
    """Monitor de recursos do sistema"""
    
    def __init__(self):
        self.cpu_samples = []
        self.memory_samples = []
        self.disk_samples = []
        self.monitoring = False
    
    def start_monitoring(self):
        """Inicia monitoramento de recursos"""
        self.monitoring = True
        self.cpu_samples = []
        self.memory_samples = []
        self.disk_samples = []
    
    def collect_sample(self):
        """Coleta uma amostra de recursos"""
        if self.monitoring:
            self.cpu_samples.append(psutil.cpu_percent(interval=0.1))
            self.memory_samples.append(psutil.virtual_memory().percent)
            disk = psutil.disk_io_counters()
            self.disk_samples.append({
                'read_bytes': disk.read_bytes,
                'write_bytes': disk.write_bytes
            })
    
    def stop_monitoring(self):
        """Para monitoramento e retorna estatísticas"""
        self.monitoring = False
        
        # Calcula diferença de disco
        disk_read = 0
        disk_write = 0
        if len(self.disk_samples) >= 2:
            disk_read = self.disk_samples[-1]['read_bytes'] - self.disk_samples[0]['read_bytes']
            disk_write = self.disk_samples[-1]['write_bytes'] - self.disk_samples[0]['write_bytes']
        
        return {
            'cpu': {
                'avg': statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
                'max': max(self.cpu_samples) if self.cpu_samples else 0,
                'min': min(self.cpu_samples) if self.cpu_samples else 0
            },
            'memory': {
                'avg': statistics.mean(self.memory_samples) if self.memory_samples else 0,
                'max': max(self.memory_samples) if self.memory_samples else 0,
                'min': min(self.memory_samples) if self.memory_samples else 0
            },
            'disk': {
                'read_mb': disk_read / (1024 * 1024),
                'write_mb': disk_write / (1024 * 1024)
            }
        }


class PostgreSQLTester:
    """Testa performance do PostgreSQL tradicional"""
    
    def __init__(self):
        self.conn = None
    
    def connect(self):
        """Conecta ao PostgreSQL"""
        self.conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
    
    def disconnect(self):
        """Desconecta do PostgreSQL"""
        if self.conn:
            self.conn.close()
    
    def insert_log(self, log_data):
        """Insere um log diretamente no PostgreSQL"""
        cursor = self.conn.cursor()
        query = """
            INSERT INTO logs (id, timestamp, source, level, message, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            log_data['id'],
            log_data['timestamp'],
            log_data['source'],
            log_data['level'],
            log_data['message'],
            json.dumps(log_data.get('metadata', {}))
        ))
        self.conn.commit()
        cursor.close()
    
    def query_logs(self, source):
        """Consulta logs por source"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM logs WHERE source = %s LIMIT 100", (source,))
        results = cursor.fetchall()
        cursor.close()
        return results


class HybridTester:
    """Testa performance da arquitetura híbrida (MongoDB + Fabric)"""

    def insert_log_via_api(self, log_data):
        """Insere log via API (MongoDB + Fabric)"""
        response = requests.post(
            f"{API_BASE_URL}/logs",
            json=log_data,
            timeout=30
        )
        return response.status_code == 201
    
    def query_logs_via_api(self, source):
        """Consulta logs via API"""
        response = requests.get(
            f"{API_BASE_URL}/logs?source={source}",
            timeout=30
        )
        return response.json() if response.status_code == 200 else None


def generate_test_log(index):
    """Gera dados de log para teste"""
    return {
        'id': f'perf_test_{index}_{int(time.time() * 1000)}',
        'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'source': f'test-service-{index % 10}',
        'level': ['INFO', 'WARNING', 'ERROR'][index % 3],
        'message': f'Performance test message {index}',
        'metadata': {
            'test_id': index,
            'batch': int(index / 100)
        }
    }


def run_insert_test(tester, duration, concurrency, test_type):
    """Executa teste de inserção"""
    print(f"\n[{test_type}] Teste de INSERÇÃO")
    print(f"Duração: {duration}s | Concorrência: {concurrency}")
    print("-" * 60)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    results = {
        'total_transactions': 0,
        'successful': 0,
        'failed': 0,
        'latencies': []
    }
    
    start_time = time.time()
    end_time = start_time + duration
    counter = 0
    
    def insert_single_log(index):
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
            return False, 0
    
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
    
    # Calcula estatísticas
    results['duration'] = elapsed
    results['throughput'] = results['successful'] / elapsed
    results['latency'] = {
        'avg': statistics.mean(results['latencies']) if results['latencies'] else 0,
        'median': statistics.median(results['latencies']) if results['latencies'] else 0,
        'p95': statistics.quantiles(results['latencies'], n=20)[18] if len(results['latencies']) > 20 else 0,
        'p99': statistics.quantiles(results['latencies'], n=100)[98] if len(results['latencies']) > 100 else 0,
        'min': min(results['latencies']) if results['latencies'] else 0,
        'max': max(results['latencies']) if results['latencies'] else 0
    }
    results['resources'] = resources
    
    return results


def run_query_test(tester, num_queries, concurrency, test_type):
    """Executa teste de consulta"""
    print(f"\n[{test_type}] Teste de CONSULTA")
    print(f"Consultas: {num_queries} | Concorrência: {concurrency}")
    print("-" * 60)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    results = {
        'total_queries': 0,
        'successful': 0,
        'failed': 0,
        'latencies': []
    }
    
    start_time = time.time()
    
    def query_single(index):
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
            return False, 0
    
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
    
    # Calcula estatísticas
    results['duration'] = elapsed
    results['throughput'] = results['successful'] / elapsed if elapsed > 0 else 0
    results['latency'] = {
        'avg': statistics.mean(results['latencies']) if results['latencies'] else 0,
        'median': statistics.median(results['latencies']) if results['latencies'] else 0,
        'p95': statistics.quantiles(results['latencies'], n=20)[18] if len(results['latencies']) > 20 else 0,
        'p99': statistics.quantiles(results['latencies'], n=100)[98] if len(results['latencies']) > 100 else 0,
        'min': min(results['latencies']) if results['latencies'] else 0,
        'max': max(results['latencies']) if results['latencies'] else 0
    }
    results['resources'] = resources
    
    return results


def print_results(test_name, results):
    """Imprime resultados de um teste"""
    print(f"\nResultados - {test_name}")
    print("=" * 60)
    print(f"Transações/Consultas: {results['total_transactions'] if 'total_transactions' in results else results['total_queries']}")
    print(f"Sucesso: {results['successful']}")
    print(f"Falhas: {results['failed']}")
    print(f"Duração: {results['duration']:.2f}s")
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
    print(f"    Leitura:  {results['resources']['disk']['read_mb']:.2f} MB")
    print(f"    Escrita:  {results['resources']['disk']['write_mb']:.2f} MB")


def save_results_json(all_results, filename='performance_results.json'):
    """Salva resultados em JSON"""
    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResultados salvos em: {filename}")


def main():
    """Executa bateria completa de testes"""
    print("=" * 70)
    print("TESTES DE PERFORMANCE - TCC LOG MANAGEMENT")
    print("=" * 70)
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
    
    print("\n" + "=" * 70)
    print("TESTES CONCLUÍDOS")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTestes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nErro durante execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

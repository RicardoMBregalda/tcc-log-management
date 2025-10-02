import time
import json
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque

import psycopg2
import requests

# Importa nosso gerador de logs
from log_generator import generate_log_entry

# --- Configurações das Arquiteturas ---
# Arquitetura Tradicional
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "logdb"
PG_USER = "logadmin"
PG_PASS = "logpassword"

# Arquitetura Híbrida (URLs de exemplo para uma API que você criará)
# Esta API receberia o log, salvaria no MongoDB e enviaria o hash para o Fabric
API_ENDPOINT_LOG = "http://localhost:5000/logs" 

# --- Lógica de Teste ---

def send_log_to_postgresql(log_entry):
    """Envia um único log para o PostgreSQL e mede a latência."""
    start_time = time.monotonic()
    conn = None
    try:
        # Conecta ao banco de dados
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
        )
        cur = conn.cursor()
        
        # Insere o log (como JSONB para flexibilidade)
        # Nota: Você precisa de uma tabela. Crie com:
        # CREATE TABLE logs (id UUID PRIMARY KEY, timestamp TIMESTAMPTZ, content JSONB);
        cur.execute(
            "INSERT INTO logs (id, timestamp, content) VALUES (%s, %s, %s)",
            (log_entry['id'], log_entry['timestamp'], json.dumps(log_entry))
        )
        conn.commit()
        cur.close()
        
        end_time = time.monotonic()
        return end_time - start_time
    except Exception as e:
        # print(f"Erro ao inserir no PostgreSQL: {e}")
        return None
    finally:
        if conn:
            conn.close()

def send_log_to_hybrid_api(log_entry):
    """Envia um único log para a API da arquitetura híbrida."""
    start_time = time.monotonic()
    try:
        # 1. Calcula o hash do log
        log_str = json.dumps(log_entry, sort_keys=True).encode('utf-8')
        log_hash = hashlib.sha256(log_str).hexdigest()

        # 2. Envia para a API (que salvará no Mongo e registrará o hash no Fabric)
        payload = {
            "log_data": log_entry,
            "log_hash": log_hash
        }
        response = requests.post(API_ENDPOINT_LOG, json=payload, timeout=10)
        
        if response.status_code != 201:
            # print(f"API retornou erro: {response.status_code}")
            return None

        end_time = time.monotonic()
        return end_time - start_time
    except Exception as e:
        # print(f"Erro ao chamar a API: {e}")
        return None

def run_test(target_function, total_logs, num_threads):
    """
    Executa o teste de carga usando um pool de threads.
    
    :param target_function: A função a ser chamada para cada log (ex: send_log_to_postgresql).
    :param total_logs: Número total de logs a serem enviados.
    :param num_threads: Número de workers concorrentes.
    """
    print(f"Iniciando teste com {total_logs} logs e {num_threads} threads...")
    
    latencies = deque()
    logs_ok = 0
    logs_fail = 0
    
    # Gera todos os logs de uma vez para não medir o tempo de geração
    logs_to_send = [generate_log_entry() for _ in range(total_logs)]
    
    start_time_total = time.monotonic()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submete todas as tarefas
        futures = {executor.submit(target_function, log): log for log in logs_to_send}
        
        for future in as_completed(futures):
            latency = future.result()
            if latency is not None:
                latencies.append(latency)
                logs_ok += 1
            else:
                logs_fail += 1

    end_time_total = time.monotonic()
    
    total_duration = end_time_total - start_time_total
    
    # --- Cálculo das Métricas ---
    throughput = logs_ok / total_duration if total_duration > 0 else 0
    avg_latency = (sum(latencies) / len(latencies)) * 1000 if latencies else 0
    min_latency = min(latencies) * 1000 if latencies else 0
    max_latency = max(latencies) * 1000 if latencies else 0

    # --- Exibição dos Resultados ---
    print("\n--- Resultados do Teste ---")
    print(f"Duração Total: {total_duration:.2f} segundos")
    print(f"Logs Enviados com Sucesso: {logs_ok}")
    print(f"Logs com Falha: {logs_fail}")
    print("-" * 25)
    print(f"Throughput: {throughput:.2f} logs/segundo")
    print(f"Latência Média: {avg_latency:.2f} ms")
    print(f"Latência Mínima: {min_latency:.2f} ms")
    print(f"Latência Máxima: {max_latency:.2f} ms")
    print("-" * 25)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de Teste de Performance para TCC.")
    parser.add_argument("architecture", choices=["postgresql", "hybrid"], help="A arquitetura a ser testada.")
    parser.add_argument("--count", type=int, default=1000, help="Número total de logs a serem enviados.")
    parser.add_argument("--threads", type=int, default=10, help="Número de threads concorrentes.")
    
    args = parser.parse_args()

    if args.architecture == "postgresql":
        # Antes de rodar, crie a tabela no banco 'logdb' com o comando:
        # docker exec -it postgres-primary psql -U logadmin logdb -c "CREATE TABLE logs (id UUID PRIMARY KEY, timestamp TIMESTAMPTZ, content JSONB);"
        run_test(send_log_to_postgresql, args.count, args.threads)
    elif args.architecture == "hybrid":
        print("NOTA: O teste 'hybrid' requer uma API rodando em " + API_ENDPOINT_LOG)
        run_test(send_log_to_hybrid_api, args.count, args.threads)
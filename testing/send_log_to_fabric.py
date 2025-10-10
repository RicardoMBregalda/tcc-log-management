#!/usr/bin/env python3
"""
Script para enviar log diretamente ao Fabric
Uso: python3 send_log_to_fabric.py <log_id>
"""

import sys
import json
import psycopg2
import requests
from datetime import datetime

# Configurações
POSTGRES_HOST = 'localhost'
POSTGRES_PORT = 5432
POSTGRES_DB = 'logdb'
POSTGRES_USER = 'logadmin'
POSTGRES_PASSWORD = 'logpassword'
API_BASE_URL = 'http://localhost:5000'


def get_log_from_postgres(log_id):
    """Busca log do PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()
        
        query = """
            SELECT id, timestamp, source, level, message, metadata, stacktrace
            FROM logs
            WHERE id = %s
        """
        cursor.execute(query, (log_id,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'timestamp': result[1].isoformat() if hasattr(result[1], 'isoformat') else str(result[1]),
                'source': result[2],
                'level': result[3],
                'message': result[4],
                'metadata': result[5] if result[5] else {},
                'stacktrace': result[6]
            }
        return None
    except Exception as e:
        print(f"Erro ao buscar log: {e}", file=sys.stderr)
        return None


def send_to_fabric(log_data):
    """Envia log para o Fabric via API"""
    try:
        payload = {
            'id': log_data['id'],
            'timestamp': log_data['timestamp'],
            'source': log_data['source'],
            'level': log_data['level'],
            'message': log_data['message'],
            'metadata': log_data['metadata']
        }
        
        # Adiciona stacktrace se existir
        if log_data.get('stacktrace'):
            if isinstance(payload['metadata'], dict):
                payload['metadata']['stacktrace'] = log_data['stacktrace']
        
        response = requests.post(
            f"{API_BASE_URL}/logs",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            return True, result.get('hash', '')
        elif response.status_code == 500 and 'already exists' in response.text.lower():
            # Log já existe, não é erro
            return True, 'existing'
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)


def update_sync_status(log_id, success, fabric_hash=None, error=None):
    """Atualiza status de sincronização no PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        cursor = conn.cursor()
        
        if success:
            query = """
                INSERT INTO sync_control (log_id, sync_status, fabric_hash, synced_at)
                VALUES (%s, 'synced', %s, NOW())
                ON CONFLICT (log_id) DO UPDATE
                SET sync_status = 'synced', fabric_hash = %s, synced_at = NOW()
            """
            cursor.execute(query, (log_id, fabric_hash, fabric_hash))
        else:
            query = """
                INSERT INTO sync_control (log_id, sync_status, retry_count, last_error)
                VALUES (%s, 'failed', 1, %s)
                ON CONFLICT (log_id) DO UPDATE
                SET sync_status = 'failed', 
                    retry_count = sync_control.retry_count + 1, 
                    last_error = %s
            """
            cursor.execute(query, (log_id, error, error))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao atualizar status: {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 send_log_to_fabric.py <log_id>", file=sys.stderr)
        sys.exit(1)
    
    log_id = sys.argv[1]
    
    # 1. Busca log do PostgreSQL
    log_data = get_log_from_postgres(log_id)
    if not log_data:
        print(f"Log {log_id} não encontrado no PostgreSQL", file=sys.stderr)
        sys.exit(1)
    
    # 2. Envia para o Fabric
    success, result = send_to_fabric(log_data)
    
    # 3. Atualiza status
    if success:
        update_sync_status(log_id, True, result)
        print(f"✅ Log {log_id} enviado com sucesso! Hash: {result}")
        sys.exit(0)
    else:
        update_sync_status(log_id, False, error=result)
        print(f"❌ Falha ao enviar log {log_id}: {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

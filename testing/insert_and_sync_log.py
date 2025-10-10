#!/usr/bin/env python3
"""
Script Unificado: Insere log no PostgreSQL e envia automaticamente para o Fabric
Uso: python3 insert_and_sync_log.py

Este script combina as operações de inserção e sincronização em uma única chamada
"""

import sys
import json
import uuid
import psycopg2
import requests
from datetime import datetime, timezone

# Configurações
POSTGRES_HOST = 'localhost'
POSTGRES_PORT = 5432
POSTGRES_DB = 'logdb'
POSTGRES_USER = 'logadmin'
POSTGRES_PASSWORD = 'logpassword'
API_BASE_URL = 'http://localhost:5000'


def insert_log_to_postgres(log_data):
    """Insere log no PostgreSQL"""
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
            log_data.get('stacktrace')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Log inserido no PostgreSQL"
    except Exception as e:
        return False, f"Erro ao inserir no PostgreSQL: {e}"


def send_to_fabric(log_data):
    """Envia log para o Fabric via API"""
    try:
        payload = {
            'id': log_data['id'],
            'timestamp': log_data['timestamp'],
            'source': log_data['source'],
            'level': log_data['level'],
            'message': log_data['message'],
            'metadata': log_data.get('metadata', {})
        }
        
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
            return True, result.get('hash', ''), "Log enviado ao Fabric com sucesso"
        elif response.status_code == 500 and 'already exists' in response.text.lower():
            return True, 'existing', "Log já existe no Fabric"
        else:
            return False, None, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, None, f"Erro ao enviar para Fabric: {e}"


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
                SET sync_status = 'failed', last_error = %s
            """
            cursor.execute(query, (log_id, error, error))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Aviso: Erro ao atualizar sync_control: {e}")


def create_and_sync_log(source, level, message, metadata=None, stacktrace=None):
    """
    Função principal: Cria log no PostgreSQL e sincroniza com Fabric
    """
    log_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    log_data = {
        'id': log_id,
        'timestamp': timestamp,
        'source': source,
        'level': level,
        'message': message,
        'metadata': metadata or {},
        'stacktrace': stacktrace
    }
    
    print(f"Criando log {log_id}...")
    
    pg_success, pg_message = insert_log_to_postgres(log_data)
    if not pg_success:
        print(pg_message)
        return {
            'success': False,
            'status': 'failed',
            'log_id': log_id,
            'fabric_hash': None,
            'message': pg_message
        }
    
    print(pg_message)
    print("Enviando para Fabric...")
    
    fabric_success, fabric_hash, fabric_message = send_to_fabric(log_data)
    
    if fabric_success:
        print(f"{fabric_message}")
        print(f"Hash: {fabric_hash}\n")
    else:
        print(f"{fabric_message}\n")
    
    update_sync_status(log_id, fabric_success, fabric_hash, fabric_message if not fabric_success else None)
    
    if pg_success and fabric_success:
        return {
            'success': True,
            'status': 'synced',
            'log_id': log_id,
            'fabric_hash': fabric_hash,
            'message': f"Log criado e sincronizado com sucesso! Hash: {fabric_hash}"
        }
    elif pg_success:
        return {
            'success': False,
            'status': 'failed',
            'log_id': log_id,
            'fabric_hash': None,
            'message': f"Log criado no PostgreSQL mas falhou sincronização: {fabric_message}"
        }
    else:
        return {
            'success': False,
            'status': 'failed',
            'log_id': log_id,
            'fabric_hash': None,
            'message': pg_message
        }


def main():
    """Exemplo de uso interativo"""
    print("=" * 60)
    print("Script de Criação e Sincronização de Logs")
    print("PostgreSQL -> Fabric -> MongoDB")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        if len(sys.argv) < 4:
            print("Uso: python3 insert_and_sync_log.py <source> <level> <message> [metadata_json]")
            print()
            print("Exemplo:")
            print('  python3 insert_and_sync_log.py api-gateway INFO "Requisição processada" \'{"user_id": "123"}\'')
            sys.exit(1)
        
        source = sys.argv[1]
        level = sys.argv[2]
        message = sys.argv[3]
        metadata = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        result = create_and_sync_log(source, level, message, metadata)
    else:
        print("Modo interativo - insira os dados do log:")
        print()
        
        source = input("Source (ex: api-gateway): ").strip() or "test-service"
        level = input("Level (INFO/DEBUG/WARNING/ERROR): ").strip().upper() or "INFO"
        message = input("Message: ").strip() or "Test log message"
        
        metadata_input = input("Metadata JSON (opcional, Enter para pular): ").strip()
        metadata = json.loads(metadata_input) if metadata_input else {"test": True}
        
        print()
        result = create_and_sync_log(source, level, message, metadata)
    
    print()
    print("=" * 60)
    if result['success']:
        print(f"SUCESSO: {result['message']}")
        print(f"   Log ID: {result['log_id']}\n")
        sys.exit(0)
    else:
        print(f"FALHA: {result['message']}")
        print(f"   Log ID: {result['log_id']}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()

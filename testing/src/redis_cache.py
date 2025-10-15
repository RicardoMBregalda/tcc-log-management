#!/usr/bin/env python3
"""
Cache Service com Redis

Implementa cache para consultas frequentes de logs
"""

import redis
import json
from datetime import datetime, timedelta

# Configuração Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
CACHE_TTL = 300  # 5 minutos

# Cliente Redis
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()
    CACHE_ENABLED = True
    print("Redis cache ativo")
except:
    redis_client = None
    CACHE_ENABLED = False
    print("Redis não disponível - cache desabilitado")


def get_cache_key(source=None, level=None, limit=100):
    """Gera chave de cache baseada nos filtros"""
    return f"logs:{source or 'all'}:{level or 'all'}:{limit}"


def get_from_cache(source=None, level=None, limit=100):
    """
    Obtém logs do cache
    
    Retorna None se não encontrado ou cache desabilitado
    """
    if not CACHE_ENABLED:
        return None
    
    try:
        cache_key = get_cache_key(source, level, limit)
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        return None
        
    except Exception as e:
        print(f"Erro ao ler cache: {e}")
        return None


def set_in_cache(logs, source=None, level=None, limit=100, ttl=CACHE_TTL):
    """
    Armazena logs no cache
    
    TTL padrão: 5 minutos
    """
    if not CACHE_ENABLED:
        return False
    
    try:
        cache_key = get_cache_key(source, level, limit)
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(logs)
        )
        return True
        
    except Exception as e:
        print(f"Erro ao gravar cache: {e}")
        return False


def invalidate_cache(source=None):
    """
    Invalida cache de logs
    
    Se source for None, invalida todo o cache de logs
    Se source for especificado, invalida apenas daquele source
    """
    if not CACHE_ENABLED:
        return
    
    try:
        if source:
            # Invalida cache específico
            pattern = f"logs:{source}:*"
        else:
            # Invalida todo cache de logs
            pattern = "logs:*"
        
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            print(f"Cache invalidado: {len(keys)} chaves removidas")
        
    except Exception as e:
        print(f"Erro ao invalidar cache: {e}")


def get_cache_stats():
    """Retorna estatísticas do cache"""
    if not CACHE_ENABLED:
        return {'enabled': False}
    
    try:
        info = redis_client.info('stats')
        keys_count = len(redis_client.keys('logs:*'))
        
        return {
            'enabled': True,
            'total_keys': keys_count,
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) * 100
        }
        
    except Exception as e:
        return {'enabled': False, 'error': str(e)}


if __name__ == '__main__':
    """Teste do cache"""
    print("Testando Redis Cache...")
    print(f"Redis ativo: {CACHE_ENABLED}")
    
    if CACHE_ENABLED:
        # Teste básico
        test_data = [
            {'id': '1', 'message': 'Test 1'},
            {'id': '2', 'message': 'Test 2'}
        ]
        
        print("\n1. Gravando no cache...")
        set_in_cache(test_data, source='test', level='INFO')
        
        print("2. Lendo do cache...")
        cached = get_from_cache(source='test', level='INFO')
        print(f"   Resultado: {cached}")
        
        print("\n3. Estatísticas:")
        stats = get_cache_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n4. Invalidando cache...")
        invalidate_cache(source='test')
        
        print("5. Tentando ler após invalidação...")
        cached = get_from_cache(source='test', level='INFO')
        print(f"   Resultado: {cached}")
        
        print("\nTeste concluído!")

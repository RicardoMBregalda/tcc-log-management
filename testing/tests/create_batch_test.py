#!/usr/bin/env python3
"""
Script para criar um batch Merkle de teste

Este script cria batches Merkle através da API híbrida,
agrupando logs sem batch_id e gerando uma raiz Merkle
que é armazenada no blockchain Hyperledger Fabric.

Uso:
    python3 create_batch_test.py [--batch-size SIZE]
"""

import argparse
import sys
import os
from typing import Dict, Optional
import requests

# Adiciona o diretório pai ao path para importar config e utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports locais
from config import API_BASE_URL, API_TIMEOUT, DEFAULT_BATCH_SIZE
from utils import print_header, print_key_value


# ==================== FUNÇÕES AUXILIARES ====================

def print_batch_info(batch: Dict) -> None:
    """Imprime informações do batch criado"""
    print(f"\n✅ Batch criado com sucesso!\n")
    print_key_value("Batch ID", batch['batch_id'], indent=3)
    print_key_value("Merkle Root", batch['merkle_root'], indent=3)
    print_key_value("Número de Logs", batch['num_logs'], indent=3)
    print_key_value("Status", batch['status'], indent=3)


def create_batch(api_url: str, batch_size: int) -> Optional[Dict]:
    """
    Cria um batch Merkle através da API
    
    Args:
        api_url: URL base da API
        batch_size: Número de logs para incluir no batch
        
    Returns:
        Dicionário com informações do batch criado ou None em caso de erro
    """
    print(f"\n📦 Criando batch de {batch_size} logs...")
    
    try:
        response = requests.post(
            f"{api_url}/merkle/batch",
            json={'batch_size': batch_size},
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.Timeout:
        print(f"❌ Erro: Timeout ao conectar com a API (>{API_TIMEOUT}s)")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Erro: Não foi possível conectar à API em {api_url}")
        print("   Certifique-se de que a API está rodando.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro HTTP {response.status_code}: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return None


def print_next_steps(batch_id: str, api_url: str) -> None:
    """Imprime instruções para próximos passos"""
    print(f"\n🔍 Para verificar integridade, execute:")
    print(f"   python3 verify_merkle_integrity.py {batch_id}")
    print(f"\n📊 Para listar todos os batches:")
    print(f"   curl {api_url}/merkle/batches")


# ==================== FUNÇÃO PRINCIPAL ====================

def main() -> int:
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Cria um batch Merkle de teste através da API"
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f'Número de logs para incluir no batch (padrão: {DEFAULT_BATCH_SIZE})'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default=API_BASE_URL,
        help=f'URL da API (padrão: {API_BASE_URL})'
    )
    
    args = parser.parse_args()
    
    # Validação
    if args.batch_size <= 0:
        print("❌ Erro: batch-size deve ser maior que 0")
        return 1
    
    # Executar
    print_header("CRIANDO BATCH MERKLE DE TESTE")
    
    batch = create_batch(args.api_url, args.batch_size)
    
    if batch:
        print_batch_info(batch)
        print_next_steps(batch['batch_id'], args.api_url)
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

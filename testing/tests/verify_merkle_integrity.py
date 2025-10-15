#!/usr/bin/env python3
"""
Script de Verificação de Integridade usando Merkle Tree

Este script demonstra como verificar a integridade de um batch de logs
comparando a Merkle Root armazenada no blockchain com uma recalculada
a partir dos logs no MongoDB.

Uso:
    python verify_merkle_integrity.py <batch_id>
    python verify_merkle_integrity.py --all
    python verify_merkle_integrity.py --create-batch
"""

import requests
import sys
import json
from datetime import datetime
from colorama import init, Fore, Style

# Inicializa colorama para cores no terminal
init(autoreset=True)

API_URL = "http://localhost:5001"


def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    print("=" * 70)


def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")


def print_error(text):
    """Imprime mensagem de erro"""
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")


def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")


def print_info(text):
    """Imprime mensagem informativa"""
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")


def create_merkle_batch(batch_size=100):
    """
    Cria um novo batch de Merkle
    
    Args:
        batch_size: Número de logs no batch
        
    Returns:
        dict: Resposta da API com detalhes do batch criado
    """
    print_header("CRIANDO MERKLE BATCH")
    
    try:
        response = requests.post(
            f"{API_URL}/merkle/batch",
            json={'batch_size': batch_size},
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print_success(f"Batch criado com sucesso!")
            print(f"\n{Fore.WHITE}Detalhes do Batch:{Style.RESET_ALL}")
            print(f"  Batch ID: {Fore.YELLOW}{result['batch_id']}{Style.RESET_ALL}")
            print(f"  Merkle Root: {Fore.YELLOW}{result['merkle_root'][:32]}...{Style.RESET_ALL}")
            print(f"  Número de Logs: {Fore.YELLOW}{result['num_logs']}{Style.RESET_ALL}")
            print(f"\n{Fore.WHITE}IDs dos Logs no Batch:{Style.RESET_ALL}")
            for i, log_id in enumerate(result['log_ids'][:10], 1):
                print(f"  {i}. {log_id}")
            if len(result['log_ids']) > 10:
                print(f"  ... e mais {len(result['log_ids']) - 10} logs")
            
            return result
        else:
            print_error(f"Falha ao criar batch: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Erro ao criar batch: {e}")
        return None


def verify_batch_integrity(batch_id):
    """
    Verifica a integridade de um batch específico
    
    Args:
        batch_id: ID do batch a verificar
        
    Returns:
        bool: True se íntegro, False caso contrário
    """
    print_header(f"VERIFICANDO INTEGRIDADE DO BATCH: {batch_id}")
    
    try:
        # Busca informações do batch
        print_info("Buscando informações do batch no blockchain...")
        batch_response = requests.get(
            f"{API_URL}/merkle/batch/{batch_id}",
            timeout=10
        )
        
        if batch_response.status_code != 200:
            print_error(f"Batch não encontrado: {batch_response.text}")
            return False
        
        batch_data = batch_response.json()
        batch_info = batch_data['batch']
        logs = batch_data['logs']
        
        print_success(f"Batch encontrado no blockchain")
        print(f"\n{Fore.WHITE}Informações do Batch:{Style.RESET_ALL}")
        print(f"  Batch ID: {Fore.YELLOW}{batch_info['batch_id']}{Style.RESET_ALL}")
        print(f"  Merkle Root Original: {Fore.YELLOW}{batch_info['merkle_root'][:32]}...{Style.RESET_ALL}")
        print(f"  Número de Logs: {Fore.YELLOW}{batch_info['num_logs']}{Style.RESET_ALL}")
        print(f"  Timestamp: {Fore.YELLOW}{batch_info['timestamp']}{Style.RESET_ALL}")
        
        # Verifica integridade
        print_info(f"\nRecalculando Merkle Root de {len(logs)} logs...")
        verify_response = requests.post(
            f"{API_URL}/merkle/verify/{batch_id}",
            timeout=15
        )
        
        if verify_response.status_code != 200:
            print_error(f"Falha ao verificar integridade: {verify_response.text}")
            return False
        
        result = verify_response.json()
        
        print(f"\n{Fore.WHITE}Resultado da Verificação:{Style.RESET_ALL}")
        print(f"  Merkle Root Original:     {Fore.CYAN}{result['original_merkle_root'][:32]}...{Style.RESET_ALL}")
        print(f"  Merkle Root Recalculado:  {Fore.CYAN}{result['recalculated_merkle_root'][:32]}...{Style.RESET_ALL}")
        print(f"  Status: {Fore.GREEN if result['is_valid'] else Fore.RED}{result['integrity']}{Style.RESET_ALL}")
        
        if result['is_valid']:
            print_success("✓ INTEGRIDADE VERIFICADA: Logs não foram adulterados")
            print(f"\n{Fore.GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{Style.BRIGHT}  BATCH ÍNTEGRO  {Style.RESET_ALL}")
            print(f"{Fore.GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")
            return True
        else:
            print_error("✗ INTEGRIDADE COMPROMETIDA: Logs foram adulterados!")
            print(f"\n{Fore.RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
            print(f"{Fore.RED}{Style.BRIGHT}  ALERTA: DADOS ADULTERADOS  {Style.RESET_ALL}")
            print(f"{Fore.RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")
            return False
            
    except Exception as e:
        print_error(f"Erro ao verificar integridade: {e}")
        return False


def verify_all_batches():
    """
    Verifica a integridade de todos os batches
    
    Returns:
        tuple: (num_valid, num_invalid, num_total)
    """
    print_header("VERIFICANDO TODOS OS BATCHES")
    
    try:
        # Lista todos os batches
        print_info("Buscando lista de batches...")
        response = requests.get(f"{API_URL}/merkle/batches", timeout=10)
        
        if response.status_code != 200:
            print_error(f"Falha ao buscar batches: {response.text}")
            return (0, 0, 0)
        
        data = response.json()
        batches = data['batches']
        
        if not batches:
            print_warning("Nenhum batch encontrado")
            return (0, 0, 0)
        
        print_success(f"Encontrados {len(batches)} batches")
        print()
        
        # Verifica cada batch
        results = []
        for i, batch in enumerate(batches, 1):
            batch_id = batch['batch_id']
            print(f"{Fore.CYAN}[{i}/{len(batches)}] Verificando {batch_id}...{Style.RESET_ALL}")
            
            is_valid = verify_batch_integrity(batch_id)
            results.append(is_valid)
            print()
        
        # Resumo
        num_valid = sum(results)
        num_invalid = len(results) - num_valid
        num_total = len(results)
        
        print_header("RESUMO DA VERIFICAÇÃO")
        print(f"\n{Fore.WHITE}Total de Batches Verificados: {Fore.YELLOW}{num_total}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Íntegros: {num_valid}{Style.RESET_ALL}")
        print(f"{Fore.RED}✗ Comprometidos: {num_invalid}{Style.RESET_ALL}")
        
        if num_invalid == 0:
            print_success("\n🎉 Todos os batches estão íntegros!")
        else:
            print_error(f"\n⚠️  {num_invalid} batch(es) com integridade comprometida!")
        
        return (num_valid, num_invalid, num_total)
        
    except Exception as e:
        print_error(f"Erro ao verificar batches: {e}")
        return (0, 0, 0)


def list_all_batches():
    """Lista todos os batches disponíveis"""
    print_header("LISTANDO TODOS OS BATCHES")
    
    try:
        response = requests.get(f"{API_URL}/merkle/batches", timeout=10)
        
        if response.status_code != 200:
            print_error(f"Falha ao buscar batches: {response.text}")
            return
        
        data = response.json()
        batches = data['batches']
        
        if not batches:
            print_warning("Nenhum batch encontrado")
            return
        
        print(f"\n{Fore.WHITE}Total de Batches: {Fore.YELLOW}{len(batches)}{Style.RESET_ALL}\n")
        
        for i, batch in enumerate(batches, 1):
            print(f"{Fore.CYAN}{i}. {batch['batch_id']}{Style.RESET_ALL}")
            print(f"   Merkle Root: {batch['merkle_root'][:32]}...")
            print(f"   Logs: {batch['num_logs']}")
            print(f"   Data: {batch['batched_at']}")
            print()
        
    except Exception as e:
        print_error(f"Erro ao listar batches: {e}")


def print_usage():
    """Imprime instruções de uso"""
    print(f"\n{Fore.CYAN}Uso:{Style.RESET_ALL}")
    print(f"  {sys.argv[0]} <batch_id>        # Verifica um batch específico")
    print(f"  {sys.argv[0]} --all             # Verifica todos os batches")
    print(f"  {sys.argv[0]} --create-batch    # Cria um novo batch")
    print(f"  {sys.argv[0]} --list            # Lista todos os batches")
    print(f"\n{Fore.CYAN}Exemplos:{Style.RESET_ALL}")
    print(f"  {sys.argv[0]} batch_20251013_153045_123456")
    print(f"  {sys.argv[0]} --all")
    print(f"  {sys.argv[0]} --create-batch\n")


def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print_error("Argumento inválido")
        print_usage()
        sys.exit(1)
    
    arg = sys.argv[1]
    
    # Check API health
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print_error(f"API não está disponível em {API_URL}")
            sys.exit(1)
    except Exception as e:
        print_error(f"Não foi possível conectar à API em {API_URL}: {e}")
        sys.exit(1)
    
    if arg == '--all':
        verify_all_batches()
    elif arg == '--create-batch':
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        result = create_merkle_batch(batch_size)
        if result:
            print_info("\nVocê pode verificar este batch com:")
            print(f"  python {sys.argv[0]} {result['batch_id']}")
    elif arg == '--list':
        list_all_batches()
    elif arg.startswith('batch_'):
        verify_batch_integrity(arg)
    else:
        print_error(f"Argumento inválido: {arg}")
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()

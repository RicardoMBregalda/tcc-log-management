#!/usr/bin/env python3
"""
Script AUTOMÁTICO para testar detecção de adulteração (sem prompts interativos)
"""
import requests
import sys
import time
from colorama import Fore, Style, init
from pymongo import MongoClient

init(autoreset=True)

API_URL = "http://localhost:5001"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "logdb"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
logs_collection = db['logs']


def create_test_batch(size=20):
    """Cria um batch de teste"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  ETAPA 1: CRIANDO BATCH DE TESTE ({size} logs)")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    response = requests.post(f"{API_URL}/merkle/batch", json={'batch_size': size}, timeout=30)
    
    if response.status_code == 201:
        result = response.json()
        print(f"{Fore.GREEN}✅ Batch criado!{Style.RESET_ALL}")
        print(f"   Batch ID: {Fore.YELLOW}{result['batch_id']}{Style.RESET_ALL}")
        print(f"   Merkle Root: {result['merkle_root']}")
        return result
    return None


def verify_integrity(batch_id):
    """Verifica integridade"""
    response = requests.post(f"{API_URL}/merkle/verify/{batch_id}", timeout=15)
    return response.json() if response.status_code == 200 else None


def tamper_logs(batch_id, num_logs=2):
    """Adultera logs"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  ETAPA 3: ADULTERANDO {num_logs} LOG(S)")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    logs = list(logs_collection.find({'batch_id': batch_id}).limit(num_logs))
    tampered_ids = []
    
    for log in logs:
        log_id = log['id']
        tampered_message = f"{log['message']} [ADULTERADO]"
        
        logs_collection.update_one({'id': log_id}, {'$set': {'message': tampered_message}})
        tampered_ids.append(log_id)
        print(f"{Fore.YELLOW}⚠️  Adulterado: {log_id}{Style.RESET_ALL}")
    
    return tampered_ids


def restore_logs(log_ids):
    """Restaura logs"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  ETAPA 5: RESTAURANDO LOGS")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    for log_id in log_ids:
        log = logs_collection.find_one({'id': log_id})
        if log:
            original = log['message'].replace(' [ADULTERADO]', '')
            logs_collection.update_one({'id': log_id}, {'$set': {'message': original}})
            print(f"{Fore.BLUE}ℹ️  Restaurado: {log_id}{Style.RESET_ALL}")


def display_result(result, step, scenario):
    """Exibe resultado"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  {step}")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"{Fore.WHITE}Cenário: {scenario}{Style.RESET_ALL}")
    print(f"  Batch: {result['batch_id']}")
    print(f"  Root Original:    {result['original_merkle_root'][:32]}...")
    print(f"  Root Recalculado: {result['recalculated_merkle_root'][:32]}...")
    
    if result['is_valid']:
        print(f"  Status: {Fore.GREEN}✓ ÍNTEGRO{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}{'━'*70}")
        print(f"  ✅ INTEGRIDADE VERIFICADA")
        print(f"{'━'*70}{Style.RESET_ALL}")
    else:
        print(f"  Status: {Fore.RED}✗ COMPROMETIDO{Style.RESET_ALL}")
        print(f"\n{Fore.RED}{'━'*70}")
        print(f"  ⚠️  ADULTERAÇÃO DETECTADA!")
        print(f"{'━'*70}{Style.RESET_ALL}")


def run_test(batch_size=20, num_logs_to_tamper=2):
    """Executa teste completo"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  🔒 TESTE AUTOMÁTICO DE DETECÇÃO DE ADULTERAÇÃO")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    # Criar batch
    batch = create_test_batch(batch_size)
    if not batch:
        print(f"{Fore.RED}❌ Falha ao criar batch{Style.RESET_ALL}")
        return
    
    batch_id = batch['batch_id']
    
    # Aguarda um pouco para o batch ser processado
    time.sleep(2)
    
    # VERIFICAÇÃO 1: Antes da adulteração
    result1 = verify_integrity(batch_id)
    if result1:
        display_result(result1, "ETAPA 2: VERIFICAÇÃO INICIAL", "Batch original (íntegro)")
    
    # Adulterar logs
    tampered_ids = tamper_logs(batch_id, num_logs_to_tamper)
    
    # VERIFICAÇÃO 2: Após adulteração
    result2 = verify_integrity(batch_id)
    if result2:
        display_result(result2, "ETAPA 4: VERIFICAÇÃO APÓS ADULTERAÇÃO", f"{num_logs_to_tamper} log(s) modificado(s)")
    
    # Restaurar logs
    restore_logs(tampered_ids)
    
    # VERIFICAÇÃO 3: Após restauração
    result3 = verify_integrity(batch_id)
    if result3:
        display_result(result3, "ETAPA 6: VERIFICAÇÃO APÓS RESTAURAÇÃO", "Logs restaurados")
    
    # RESUMO
    if not all([result1, result2, result3]):
        print(f"\n{Fore.RED}❌ Erro: Algumas verificações falharam{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  📊 RESUMO DO TESTE")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"  Verificação Inicial:   {Fore.GREEN if result1['is_valid'] else Fore.RED}{'✓ PASSOU' if result1['is_valid'] else '✗ FALHOU'}{Style.RESET_ALL}")
    print(f"  Detecção Adulteração:  {Fore.GREEN if not result2['is_valid'] else Fore.RED}{'✓ DETECTOU' if not result2['is_valid'] else '✗ NÃO DETECTOU'}{Style.RESET_ALL}")
    print(f"  Verificação Restaurada: {Fore.GREEN if result3['is_valid'] else Fore.RED}{'✓ PASSOU' if result3['is_valid'] else '✗ FALHOU'}{Style.RESET_ALL}")
    
    if result1['is_valid'] and not result2['is_valid'] and result3['is_valid']:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*70}")
        print(f"  ✅ TESTE BEM-SUCEDIDO!")
        print(f"  O Merkle Tree detectou corretamente a adulteração!")
        print(f"{'='*70}{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.RED}{Style.BRIGHT}{'='*70}")
        print(f"  ❌ TESTE FALHOU!")
        print(f"{'='*70}{Style.RESET_ALL}\n")


if __name__ == '__main__':
    try:
        batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 20
        num_logs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        run_test(batch_size, num_logs)
    except Exception as e:
        print(f"{Fore.RED}❌ Erro: {e}{Style.RESET_ALL}")
    finally:
        client.close()

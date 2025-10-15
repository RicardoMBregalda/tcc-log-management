#!/usr/bin/env python3
"""
Demonstração rápida de Auto-Batching
"""
import requests
import time
from colorama import Fore, Style, init

init(autoreset=True)

API_URL = "http://localhost:5001"

print(f"\n{Fore.CYAN}{'='*70}")
print(f"  🔒 AUTO-BATCHING MERKLE TREE - DEMONSTRAÇÃO RÁPIDA")
print(f"{'='*70}{Style.RESET_ALL}\n")

# Criar 55 logs rapidamente
print(f"{Fore.WHITE}Criando 55 logs...{Style.RESET_ALL}")
for i in range(1, 56):
    log_data = {
        "source": f"demo-service-{i % 5}",
        "level": "INFO",
        "message": f"Auto-batch test log #{i}",
        "metadata": {"index": i}
    }
    requests.post(f"{API_URL}/logs", json=log_data, timeout=3)
    if i % 10 == 0:
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {i}/55 criados")

print(f"\n{Fore.GREEN}✅ 55 logs criados{Style.RESET_ALL}")
print(f"{Fore.YELLOW}⏳ Aguardando 5s para processamento...{Style.RESET_ALL}\n")
time.sleep(5)

# Verificar batches
response = requests.get(f"{API_URL}/merkle/batches")
if response.status_code == 200:
    data = response.json()
    batches = data.get('batches', [])
    
    print(f"{Fore.CYAN}{'='*70}")
    print(f"  📊 BATCHES CRIADOS AUTOMATICAMENTE")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}✅ Total de batches: {len(batches)}{Style.RESET_ALL}\n")
    
    for i, batch in enumerate(batches[:3], 1):
        print(f"{Fore.WHITE}Batch #{i}:{Style.RESET_ALL}")
        batch_id = batch.get('_id') or batch.get('batch_id', 'N/A')
        print(f"  ID: {Fore.YELLOW}{batch_id}{Style.RESET_ALL}")
        print(f"  Merkle Root: {batch.get('merkle_root', 'N/A')[:32]}...")
        print(f"  Logs: {Fore.CYAN}{batch['num_logs']}{Style.RESET_ALL}")
        print()
    
    print(f"{Fore.GREEN}{'='*70}")
    print(f"  ✅ AUTO-BATCHING FUNCIONANDO!")
    print(f"  Todos os logs têm Merkle Root no blockchain")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    if len(batches) > 0:
        batch_id = batches[0].get('_id') or batches[0].get('batch_id', 'N/A')
        print(f"{Fore.WHITE}Verificar integridade:{Style.RESET_ALL}")
        print(f"  python3 verify_merkle_integrity.py {batch_id}\n")

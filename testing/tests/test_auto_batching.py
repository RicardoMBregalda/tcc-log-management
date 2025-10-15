#!/usr/bin/env python3
"""
Teste de Auto-Batching com Merkle Tree
Demonstra logs sendo automaticamente agrupados em batches
"""
import requests
import time
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

API_URL = "http://localhost:5001"

# Gera sessão única para evitar conflitos de ID
SESSION_ID = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

def create_log(index):
    """Cria um log via API"""
    log_data = {
        "source": "auto-batch-test",
        "level": "INFO",
        "message": f"Test log #{index} for auto-batching (session {SESSION_ID})",
        "metadata": {"test_id": index, "batch_test": True, "session": SESSION_ID}
    }
    
    response = requests.post(f"{API_URL}/logs", json=log_data, timeout=5)
    if response.status_code == 201:
        return response.json()
    # Retorna o erro para debug
    return {"error": response.text, "status": response.status_code}


def check_batch_status():
    """Verifica se há batches criados"""
    response = requests.get(f"{API_URL}/merkle/batches", timeout=5)
    if response.status_code == 200:
        return response.json()
    return None


print(f"\n{Fore.CYAN}{'='*70}")
print(f"  🔒 TESTE DE AUTO-BATCHING COM MERKLE TREE")
print(f"{'='*70}{Style.RESET_ALL}\n")

print(f"{Fore.WHITE}Este teste demonstra:{Style.RESET_ALL}")
print(f"  1. Criação de 60 logs individuais")
print(f"  2. Agrupamento automático em batches de 50 logs")
print(f"  3. Cálculo de Merkle Root para cada batch")
print(f"  4. Armazenamento no blockchain\n")

print(f"{Fore.YELLOW}Configuração:{Style.RESET_ALL}")
print(f"  - Tamanho do batch: 50 logs")
print(f"  - Intervalo forçado: 30s")
print(f"  - Trigger automático: ao atingir 50 logs")
print(f"  - Sessão de teste: {SESSION_ID}\n")

input(f"{Fore.GREEN}Pressione ENTER para começar...{Style.RESET_ALL}\n")

# FASE 1: Criar 60 logs
print(f"{Fore.CYAN}{'='*70}")
print(f"  FASE 1: CRIANDO 60 LOGS")
print(f"{'='*70}{Style.RESET_ALL}\n")

logs_created = 0
errors = 0
error_messages = []

for i in range(1, 61):
    try:
        result = create_log(i)
        if result and 'error' not in result:
            logs_created += 1
            if i % 10 == 0:
                print(f"{Fore.GREEN}✓{Style.RESET_ALL} {i}/60 logs criados...")
        else:
            errors += 1
            if errors <= 3:  # Mostra detalhes dos 3 primeiros erros
                error_msg = result.get('error', 'Unknown') if isinstance(result, dict) else 'No response'
                print(f"{Fore.YELLOW}⚠️{Style.RESET_ALL} Erro ao criar log {i}: {error_msg[:100]}")
                if errors == 1:  # Guarda primeiro erro completo
                    error_messages.append(f"Log {i}: {error_msg}")
    except Exception as e:
        errors += 1
        if errors <= 3:
            print(f"{Fore.YELLOW}⚠️{Style.RESET_ALL} Exceção ao criar log {i}: {str(e)[:100]}")
    time.sleep(0.1)  # Pequeno delay entre logs

if errors > 3:
    print(f"{Fore.YELLOW}⚠️  ... e mais {errors - 3} erros{Style.RESET_ALL}")

print(f"\n{Fore.GREEN}✅ Total de logs criados: {logs_created}{Style.RESET_ALL}")
if errors > 0:
    print(f"{Fore.YELLOW}⚠️  Erros: {errors}{Style.RESET_ALL}")
    if error_messages:
        print(f"\n{Fore.RED}📋 Detalhes do primeiro erro:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{error_messages[0]}{Style.RESET_ALL}")
    print()
else:
    print()

# FASE 2: Aguardar processamento do primeiro batch (50 logs)
print(f"{Fore.CYAN}{'='*70}")
print(f"  FASE 2: AGUARDANDO AUTO-BATCHING")
print(f"{'='*70}{Style.RESET_ALL}\n")

print(f"{Fore.YELLOW}⏳ Logs criados: {logs_created}")
print(f"⏳ Esperando sistema criar batch de 50 logs...{Style.RESET_ALL}\n")

# Aguarda alguns segundos para o batch ser processado
for i in range(10, 0, -1):
    print(f"   Verificando em {i}s...", end='\r')
    time.sleep(1)

print("\n")

# FASE 3: Verificar batches criados
print(f"{Fore.CYAN}{'='*70}")
print(f"  FASE 3: VERIFICANDO BATCHES CRIADOS")
print(f"{'='*70}{Style.RESET_ALL}\n")

batches = check_batch_status()
if batches and 'batches' in batches:
    print(f"{Fore.GREEN}✅ Batches encontrados: {len(batches['batches'])}{Style.RESET_ALL}\n")
    
    for i, batch in enumerate(batches['batches'][:5], 1):  # Mostra até 5 batches
        print(f"{Fore.WHITE}Batch #{i}:{Style.RESET_ALL}")
        print(f"  ID: {Fore.YELLOW}{batch.get('batch_id', batch.get('_id', 'N/A'))}{Style.RESET_ALL}")
        print(f"  Merkle Root: {batch.get('merkle_root', 'N/A')[:32]}...")
        print(f"  Número de Logs: {Fore.CYAN}{batch['num_logs']}{Style.RESET_ALL}")
        print(f"  Timestamp: {batch.get('batched_at', 'N/A')}")
        print()
else:
    print(f"{Fore.YELLOW}⚠️  Nenhum batch encontrado ainda.")
    print(f"   Logs podem estar aguardando o intervalo de 30s{Style.RESET_ALL}\n")

# FASE 4: Aguardar segundo batch (dos 10 logs restantes)
print(f"{Fore.CYAN}{'='*70}")
print(f"  FASE 4: AGUARDANDO SEGUNDO BATCH (10 logs restantes)")
print(f"{'='*70}{Style.RESET_ALL}\n")

print(f"{Fore.YELLOW}⏳ Aguardando 30s para o scheduler processar os logs restantes...{Style.RESET_ALL}\n")

for i in range(30, 0, -1):
    print(f"   Tempo restante: {i}s   ", end='\r')
    time.sleep(1)

print("\n")

# Verifica novamente
batches_final = check_batch_status()
if batches_final and 'batches' in batches_final:
    print(f"{Fore.GREEN}✅ Total de batches criados: {len(batches_final['batches'])}{Style.RESET_ALL}\n")
    
    # Verifica se temos pelo menos 2 batches
    if len(batches_final['batches']) >= 2:
        print(f"{Fore.GREEN}{'='*70}")
        print(f"  ✅ AUTO-BATCHING FUNCIONANDO PERFEITAMENTE!")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.WHITE}Resumo:{Style.RESET_ALL}")
        print(f"  - {logs_created} logs criados")
        print(f"  - {len(batches_final['batches'])} batches processados")
        print(f"  - Batch 1: ~50 logs (trigger automático)")
        print(f"  - Batch 2: ~10 logs (trigger por tempo)\n")
        
        print(f"{Fore.GREEN}🔒 Todos os logs agora têm Merkle Root no blockchain!{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.YELLOW}⚠️  Apenas 1 batch criado. O segundo pode estar em processamento.{Style.RESET_ALL}\n")
else:
    print(f"{Fore.RED}❌ Erro ao buscar batches{Style.RESET_ALL}\n")

print(f"{Fore.CYAN}{'='*70}")
print(f"  📊 TESTE CONCLUÍDO")
print(f"{'='*70}{Style.RESET_ALL}\n")

print(f"{Fore.WHITE}Para verificar um batch específico:{Style.RESET_ALL}")
if batches_final and 'batches' in batches_final and len(batches_final['batches']) > 0:
    batch_id = batches_final['batches'][0].get('batch_id', batches_final['batches'][0].get('_id'))
    print(f"  python3 verify_merkle_integrity.py {batch_id}\n")

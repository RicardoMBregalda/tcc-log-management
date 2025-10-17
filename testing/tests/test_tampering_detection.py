#!/usr/bin/env python3
"""
Script para testar detecção de adulteração de logs usando Merkle Tree
"""
import requests
import sys
from colorama import Fore, Back, Style, init
from pymongo import MongoClient

# Inicializa colorama
init(autoreset=True)

API_URL = "http://localhost:5001"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "logdb"

# Conecta ao MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
logs_collection = db['logs']


def print_header(text):
    """Imprime cabeçalho formatado"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Style.RESET_ALL}\n")


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


def create_test_batch(size=20):
    """
    Cria um batch de teste
    
    Args:
        size: Número de logs no batch
        
    Returns:
        dict: Informações do batch criado
    """
    print_header("ETAPA 1: CRIANDO BATCH DE TESTE")
    
    print_info(f"Criando batch com {size} logs...")
    response = requests.post(
        f"{API_URL}/merkle/batch",
        json={'batch_size': size},
        timeout=30
    )
    
    if response.status_code == 201:
        result = response.json()
        print_success(f"Batch criado com sucesso!")
        print(f"\n{Fore.WHITE}Detalhes do Batch:{Style.RESET_ALL}")
        print(f"  Batch ID: {Fore.YELLOW}{result['batch_id']}{Style.RESET_ALL}")
        print(f"  Merkle Root: {Fore.YELLOW}{result['merkle_root']}{Style.RESET_ALL}")
        print(f"  Número de Logs: {Fore.YELLOW}{result['num_logs']}{Style.RESET_ALL}")
        return result
    else:
        print_error(f"Falha ao criar batch: {response.text}")
        return None


def verify_integrity(batch_id):
    """
    Verifica integridade de um batch
    
    Args:
        batch_id: ID do batch a verificar
        
    Returns:
        dict: Resultado da verificação
    """
    response = requests.post(
        f"{API_URL}/merkle/verify/{batch_id}",
        timeout=15
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print_error(f"Falha ao verificar: {response.text}")
        return None


def tamper_with_logs(batch_id, num_logs_to_tamper=1):
    """
    Adultera logs de um batch no MongoDB
    
    Args:
        batch_id: ID do batch
        num_logs_to_tamper: Número de logs a adulterar
        
    Returns:
        list: IDs dos logs adulterados
    """
    print_header("ETAPA 2: ADULTERANDO LOGS NO MONGODB")
    
    # Busca logs do batch
    logs = list(logs_collection.find({'batch_id': batch_id}).limit(num_logs_to_tamper))
    
    if not logs:
        print_error("Nenhum log encontrado no batch")
        return []
    
    tampered_ids = []
    for log in logs:
        log_id = log['id']
        original_message = log['message']
        
        # Adultera a mensagem
        tampered_message = f"{original_message} [ADULTERADO - DADO MODIFICADO]"
        
        result = logs_collection.update_one(
            {'id': log_id},
            {'$set': {'message': tampered_message}}
        )
        
        if result.modified_count > 0:
            tampered_ids.append(log_id)
            print_warning(f"Log adulterado: {log_id}")
            print(f"  Original: {Fore.WHITE}{original_message[:50]}...{Style.RESET_ALL}")
            print(f"  Modificado: {Fore.RED}{tampered_message[:50]}...{Style.RESET_ALL}")
    
    print_warning(f"\nTotal de logs adulterados: {len(tampered_ids)}")
    return tampered_ids


def restore_logs(log_ids, batch_id):
    """
    Restaura logs adulterados (remove o marcador de adulteração)
    
    Args:
        log_ids: Lista de IDs dos logs a restaurar
        batch_id: ID do batch
    """
    print_header("RESTAURANDO LOGS")
    
    for log_id in log_ids:
        log = logs_collection.find_one({'id': log_id})
        if log:
            # Remove o marcador de adulteração
            original_message = log['message'].replace(' [ADULTERADO - DADO MODIFICADO]', '')
            
            logs_collection.update_one(
                {'id': log_id},
                {'$set': {'message': original_message}}
            )
            print_info(f"Log restaurado: {log_id}")
    
    print_success(f"Total de logs restaurados: {len(log_ids)}")


def display_verification_result(result, scenario):
    """
    Exibe resultado da verificação de forma formatada
    
    Args:
        result: Dicionário com resultado da verificação
        scenario: Descrição do cenário
    """
    print(f"\n{Fore.WHITE}{'─'*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Cenário: {scenario}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'─'*70}{Style.RESET_ALL}")
    
    print(f"\n{Fore.WHITE}Resultado da Verificação:{Style.RESET_ALL}")
    print(f"  Batch ID: {Fore.YELLOW}{result['batch_id']}{Style.RESET_ALL}")
    print(f"  Número de Logs: {Fore.YELLOW}{result['num_logs']}{Style.RESET_ALL}")
    print(f"  Merkle Root Original:     {Fore.CYAN}{result['original_merkle_root'][:32]}...{Style.RESET_ALL}")
    print(f"  Merkle Root Recalculado:  {Fore.CYAN}{result['recalculated_merkle_root'][:32]}...{Style.RESET_ALL}")
    
    if result['is_valid']:
        print(f"  Status: {Fore.GREEN}{Style.BRIGHT}✓ {result['integrity']}{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{Style.BRIGHT}  INTEGRIDADE VERIFICADA ✓  {Style.RESET_ALL}")
        print(f"{Fore.GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    else:
        print(f"  Status: {Fore.RED}{Style.BRIGHT}✗ {result['integrity']}{Style.RESET_ALL}")
        print(f"\n{Fore.RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}  ⚠️  ADULTERAÇÃO DETECTADA! ⚠️  {Style.RESET_ALL}")
        print(f"{Fore.RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")


def run_tampering_test(batch_size=20, num_logs_to_tamper=3):
    """
    Executa teste completo de detecção de adulteração
    
    Args:
        batch_size: Tamanho do batch de teste
        num_logs_to_tamper: Número de logs a adulterar
    """
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  🔒 TESTE DE DETECÇÃO DE ADULTERAÇÃO - MERKLE TREE")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"{Fore.WHITE}Este teste demonstra:{Style.RESET_ALL}")
    print(f"  1. Criação de um batch íntegro")
    print(f"  2. Verificação de integridade (deve passar)")
    print(f"  3. Adulteração de {num_logs_to_tamper} log(s) no MongoDB")
    print(f"  4. Verificação de integridade (deve FALHAR)")
    print(f"  5. Restauração dos logs")
    print(f"  6. Verificação de integridade (deve passar novamente)")
    
    input(f"\n{Fore.YELLOW}Pressione ENTER para começar...{Style.RESET_ALL}\n")
    
    # ETAPA 1: Criar batch de teste
    batch = create_test_batch(batch_size)
    if not batch:
        print_error("Falha ao criar batch. Abortando teste.")
        return
    
    batch_id = batch['batch_id']
    
    # ETAPA 2: Verificar integridade ANTES da adulteração
    print_header("ETAPA 2: VERIFICAÇÃO ANTES DA ADULTERAÇÃO")
    print_info("Verificando integridade do batch original...")
    
    result_before = verify_integrity(batch_id)
    if result_before:
        display_verification_result(result_before, "Batch Original (sem adulteração)")
    else:
        print_error("Não foi possível verificar a integridade (Fabric pode estar indisponível)")
        print_warning("Continuando com o teste de adulteração no MongoDB...")
    
    input(f"\n{Fore.YELLOW}Pressione ENTER para adulterar os logs...{Style.RESET_ALL}\n")
    
    # ETAPA 3: Adulterar logs
    tampered_ids = tamper_with_logs(batch_id, num_logs_to_tamper)
    
    if not tampered_ids:
        print_error("Falha ao adulterar logs. Abortando teste.")
        return
    
    input(f"\n{Fore.YELLOW}Pressione ENTER para verificar novamente...{Style.RESET_ALL}\n")
    
    # ETAPA 4: Verificar integridade APÓS adulteração
    print_header("ETAPA 3: VERIFICAÇÃO APÓS ADULTERAÇÃO")
    print_info("Verificando integridade do batch adulterado...")
    
    result_after = verify_integrity(batch_id)
    if result_after:
        display_verification_result(result_after, f"Batch Adulterado ({num_logs_to_tamper} log(s) modificado(s))")
    
    # Pausa para observar resultado
    input(f"\n{Fore.YELLOW}Pressione ENTER para restaurar os logs...{Style.RESET_ALL}\n")
    
    # ETAPA 5: Restaurar logs
    restore_logs(tampered_ids, batch_id)
    
    input(f"\n{Fore.YELLOW}Pressione ENTER para verificar novamente...{Style.RESET_ALL}\n")
    
    # ETAPA 6: Verificar integridade APÓS restauração
    print_header("ETAPA 4: VERIFICAÇÃO APÓS RESTAURAÇÃO")
    print_info("Verificando integridade do batch restaurado...")
    
    result_restored = verify_integrity(batch_id)
    if result_restored:
        display_verification_result(result_restored, "Batch Restaurado (logs corrigidos)")
    
    # Resumo Final
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  📊 RESUMO DO TESTE")
    print(f"{'='*70}{Style.RESET_ALL}\n")
    
    print(f"{Fore.WHITE}Resultados:{Style.RESET_ALL}")
    
    # Verifica se todas as etapas foram concluídas
    if result_before and result_after and result_restored:
        print(f"  Verificação Original:  {Fore.GREEN if result_before['is_valid'] else Fore.RED}{'✓ PASSOU' if result_before['is_valid'] else '✗ FALHOU'}{Style.RESET_ALL}")
        print(f"  Verificação Adulterada: {Fore.GREEN if not result_after['is_valid'] else Fore.RED}{'✓ DETECTOU ADULTERAÇÃO' if not result_after['is_valid'] else '✗ NÃO DETECTOU'}{Style.RESET_ALL}")
        print(f"  Verificação Restaurada: {Fore.GREEN if result_restored['is_valid'] else Fore.RED}{'✓ PASSOU' if result_restored['is_valid'] else '✗ FALHOU'}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Batch ID testado: {Fore.YELLOW}{batch_id}{Style.RESET_ALL}")
        
        # Conclusão
        if result_before['is_valid'] and not result_after['is_valid'] and result_restored['is_valid']:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*70}")
            print(f"  ✅ TESTE BEM-SUCEDIDO!")
            print(f"  O Merkle Tree detectou corretamente a adulteração!")
            print(f"{'='*70}{Style.RESET_ALL}\n")
        else:
            print(f"\n{Fore.RED}{Style.BRIGHT}{'='*70}")
            print(f"  ❌ TESTE FALHOU!")
            print(f"  Algo está errado com a detecção de adulteração.")
            print(f"{'='*70}{Style.RESET_ALL}\n")
    else:
        print_warning("Teste incompleto: Fabric/Chaincode não está disponível")
        print_info("Para teste completo, certifique-se que o Fabric está rodando:")
        print(f"  {Fore.WHITE}docker ps | grep 'peer\\|orderer\\|cli'{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}{'='*70}")
        print(f"  ⚠️  TESTE PARCIAL (SEM FABRIC)")
        print(f"{'='*70}{Style.RESET_ALL}\n")


if __name__ == '__main__':
    try:
        # Parâmetros opcionais via linha de comando
        batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 20
        num_logs_to_tamper = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        
        run_tampering_test(batch_size, num_logs_to_tamper)
        
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Teste interrompido pelo usuário.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Erro durante o teste: {e}")
        sys.exit(1)
    finally:
        client.close()

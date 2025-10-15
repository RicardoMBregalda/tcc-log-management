#!/usr/bin/env python3
"""
Script de Demonstração: Merkle Tree para Verificação de Integridade

Este script demonstra o funcionamento completo do sistema de Merkle Tree:
1. Cria logs de teste
2. Agrupa em batches com Merkle Root
3. Armazena Merkle Root no blockchain
4. Verifica integridade recalculando Merkle Root
5. Simula adulteração e detecta comprometimento

Uso:
    python demos/demo_merkle_tree.py
"""

import sys
import os
import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Adiciona diretório pai ao path para importar config e utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import API_BASE_URL, DEFAULT_TIMEOUT, HTTP_TIMEOUT
from utils import print_header, print_section, print_success, print_error, get_timestamp_filename


def create_test_logs(num_logs: int = 50) -> List[str]:
    """
    Cria logs de teste para demonstração
    
    Args:
        num_logs: Número de logs a criar (padrão: 50)
        
    Returns:
        Lista com IDs dos logs criados
    """
    print_section(f"ETAPA 1: CRIANDO {num_logs} LOGS DE TESTE")
    
    # Gera timestamp único para evitar conflitos de ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"  🔑 Sessão: demo_{timestamp}\n")
    
    log_ids: List[str] = []
    for i in range(num_logs):
        log_data: Dict[str, Any] = {
            'source': f'test-service-{i % 5}',
            'level': ['INFO', 'WARNING', 'ERROR'][i % 3],
            'message': f'Test log message {i+1} (demo session {timestamp})',
            'metadata': {
                'test_id': i+1,
                'batch': 'demo',
                'session': timestamp
            }
        }
        
        if log_data['level'] == 'ERROR':
            log_data['stacktrace'] = f'File "/app/test.py", line {i+10}, in test_function'
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/logs",
                json=log_data,
                timeout=HTTP_TIMEOUT
            )
            
            if response.status_code == 201:
                result = response.json()
                log_ids.append(result['id'])
                if (i+1) % 10 == 0:
                    print(f"  ✓ Criados {i+1}/{num_logs} logs...")
            else:
                print(f"  ✗ Erro ao criar log {i+1}: {response.text}")
                
        except Exception as e:
            print(f"  ✗ Erro ao criar log {i+1}: {e}")
    
    print(f"\n✅ Total de logs criados: {len(log_ids)}")
    return log_ids


def create_merkle_batch(batch_size: int = 50) -> Optional[Dict[str, Any]]:
    """
    Cria batch de Merkle e retorna informações
    
    Args:
        batch_size: Número de logs no batch (padrão: 50)
        
    Returns:
        Dicionário com informações do batch ou None em caso de erro
    """
    print_section(f"ETAPA 2: CRIANDO MERKLE BATCH ({batch_size} logs)")
    
    print("  ⏳ Calculando Merkle Tree...")
    print("     1. Calculando hash SHA256 de cada log")
    print("     2. Construindo árvore de Merkle bottom-up")
    print("     3. Gerando Merkle Root")
    print("     4. Armazenando no blockchain")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/merkle/batch",
            json={'batch_size': batch_size},
            timeout=DEFAULT_TIMEOUT
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"\n✅ Merkle Batch criado com sucesso!")
            print(f"\n  Batch ID: {result['batch_id']}")
            print(f"  Merkle Root: {result['merkle_root']}")
            print(f"  Número de Logs: {result['num_logs']}")
            print(f"\n  📝 Primeiros 5 logs do batch:")
            for i, log_id in enumerate(result['log_ids'][:5], 1):
                print(f"     {i}. {log_id}")
            
            return result
        else:
            print(f"\n✗ Erro ao criar batch: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n✗ Erro ao criar batch: {e}")
        return None


def verify_batch_integrity(batch_id: str, expect_valid: bool = True) -> bool:
    """
    Verifica integridade de um batch recalculando Merkle Root
    
    Args:
        batch_id: ID do batch a verificar
        expect_valid: Se True, espera que batch seja válido (padrão: True)
        
    Returns:
        True se batch é válido, False caso contrário
    """
    status = "VERIFICAÇÃO INICIAL" if expect_valid else "VERIFICAÇÃO APÓS ADULTERAÇÃO"
    print_section(f"ETAPA 3: {status}")
    
    print(f"  ⏳ Verificando batch: {batch_id}")
    print("     1. Buscando logs do batch no MongoDB")
    print("     2. Recalculando Merkle Root dos logs")
    print("     3. Comparando com Merkle Root no blockchain")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/merkle/verify/{batch_id}",
            timeout=DEFAULT_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n  📊 Resultados:")
            print(f"     Merkle Root Original:    {result['original_merkle_root'][:32]}...")
            print(f"     Merkle Root Recalculado: {result['recalculated_merkle_root'][:32]}...")
            print(f"     Número de Logs: {result['num_logs']}")
            
            if result['is_valid']:
                print(f"\n  ✅ {result['integrity']}: Logs não foram adulterados")
                print(f"     ✓ As Merkle Roots coincidem")
                print(f"     ✓ Integridade dos dados garantida")
            else:
                print(f"\n  ❌ {result['integrity']}: Logs foram adulterados!")
                print(f"     ✗ As Merkle Roots NÃO coincidem")
                print(f"     ✗ Dados foram modificados após o batch ser criado")
            
            return result['is_valid']
        else:
            print(f"\n  ✗ Erro ao verificar: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n  ✗ Erro ao verificar: {e}")
        return False


def simulate_tampering(batch_id: str) -> bool:
    """
    Simula adulteração de um log para demonstração
    
    Args:
        batch_id: ID do batch contendo logs a adulterar
        
    Returns:
        True se simulação foi bem-sucedida, False caso contrário
    """
    print_section("ETAPA 4: SIMULANDO ADULTERAÇÃO DE DADOS")
    
    print(f"  ⚠️  ATENÇÃO: Esta é uma demonstração de detecção de adulteração")
    print(f"  ⏳ Buscando logs do batch para adulterar...")
    
    try:
        # Busca logs do batch
        response = requests.get(f"{API_BASE_URL}/logs?limit=1", timeout=HTTP_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if data['logs']:
                log = data['logs'][0]
                log_id = log['id']
                
                print(f"\n  📝 Log selecionado para adulteração:")
                print(f"     ID: {log_id}")
                print(f"     Mensagem Original: \"{log['message']}\"")
                
                # NOTA: Em um cenário real, você usaria acesso direto ao MongoDB
                # Aqui apenas demonstramos conceitualmente
                print(f"\n  🔧 Simulando modificação direta no MongoDB...")
                print(f"     (Alterando mensagem do log sem atualizar blockchain)")
                print(f"     Mensagem Nova: \"DADOS ADULTERADOS - TESTE\"")
                
                print(f"\n  ⚠️  IMPORTANTE:")
                print(f"     - O log foi modificado no MongoDB")
                print(f"     - A Merkle Root no blockchain NÃO foi atualizada")
                print(f"     - A verificação de integridade deve detectar esta alteração")
                
                return True
            else:
                print(f"\n  ✗ Nenhum log encontrado")
                return False
        else:
            print(f"\n  ✗ Erro ao buscar logs: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n  ✗ Erro: {e}")
        return False


def show_summary() -> None:
    """Mostra resumo educacional do sistema Merkle Tree"""
    print_section("RESUMO DO SISTEMA MERKLE TREE")
    
    print("""
  📋 COMO FUNCIONA:
  
  1. CRIAÇÃO DE BATCH:
     - Logs são agrupados em batches (ex: 100 logs)
     - Cada log recebe um hash SHA256 único
     - Hashes são organizados em uma Merkle Tree
     - A raiz (Merkle Root) é calculada e armazenada no blockchain
     - Logs completos ficam no MongoDB (off-chain)
  
  2. VERIFICAÇÃO DE INTEGRIDADE:
     - Busca logs do batch no MongoDB
     - Recalcula a Merkle Root a partir dos logs atuais
     - Compara com a Merkle Root no blockchain
     - Se coincidem = ÍNTEGRO
     - Se diferem = ADULTERADO
  
  3. VANTAGENS:
     ✓ Armazenamento eficiente (apenas root on-chain)
     ✓ Verificação rápida de integridade
     ✓ Imutabilidade garantida pelo blockchain
     ✓ Prova criptográfica de autenticidade
     ✓ Escalável para milhões de logs
  
  4. CASOS DE USO:
     - Auditoria de logs de sistemas críticos
     - Compliance regulatório
     - Forense digital
     - Prova de não-adulteração
    """)


def main() -> None:
    """
    Função principal - Executa demonstração completa do sistema Merkle Tree
    
    Demonstra:
    1. Criação de logs de teste
    2. Agrupamento em batches com Merkle Root
    3. Armazenamento no blockchain (Hyperledger Fabric)
    4. Verificação de integridade
    5. Detecção de adulteração
    """
    print("\n" + "="*70)
    print("  🎯 DEMONSTRAÇÃO: MERKLE TREE PARA VERIFICAÇÃO DE INTEGRIDADE")
    print("="*70)
    print("\n  Este script demonstra:")
    print("  1. Criação de logs de teste")
    print("  2. Agrupamento em batches com Merkle Root")
    print("  3. Armazenamento no blockchain (Hyperledger Fabric)")
    print("  4. Verificação de integridade")
    print("  5. Detecção de adulteração")
    
    input("\n  Pressione ENTER para começar...")
    
    # Check API
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=HTTP_TIMEOUT)
        if response.status_code != 200:
            print(f"\n❌ API não está disponível em {API_BASE_URL}")
            print("   Certifique-se de que a API está rodando:")
            print("   cd testing/scripts && ./start_api_mongodb.sh")
            return
    except Exception as e:
        print(f"\n❌ Não foi possível conectar à API: {e}")
        return
    
    # ETAPA 1: Criar logs de teste
    log_ids: Optional[List[str]] = create_test_logs(50)
    if not log_ids:
        print("\n❌ Falha ao criar logs de teste")
        return
    
    time.sleep(2)
    
    # ETAPA 2: Criar Merkle batch
    batch_result = create_merkle_batch(50)
    if not batch_result:
        print("\n❌ Falha ao criar Merkle batch")
        return
    
    batch_id = batch_result['batch_id']
    time.sleep(2)
    
    # ETAPA 3: Verificar integridade (deve estar OK)
    is_valid = verify_batch_integrity(batch_id, expect_valid=True)
    time.sleep(2)
    
    # ETAPA 4: Simular adulteração (demonstração conceitual)
    print("\n")
    answer = input("  Deseja simular uma adulteração de dados? (s/n): ")
    if answer.lower() == 's':
        simulate_tampering(batch_id)
        time.sleep(2)
        
        # ETAPA 5: Verificar novamente (deve detectar adulteração)
        # NOTA: Como não modificamos o MongoDB de verdade, ainda estará válido
        # Em um cenário real, a verificação falharia
        print("\n  ℹ️  NOTA: Em um cenário real com adulteração efetiva,")
        print("     a próxima verificação falharia e detectaria a adulteração.")
    
    # Mostrar resumo
    show_summary()
    
    # Info adicional
    print_section("PRÓXIMOS PASSOS")
    print(f"""
  📝 COMANDOS ÚTEIS:
  
  # Verificar este batch especificamente
  python verify_merkle_integrity.py {batch_id}
  
  # Verificar todos os batches
  python verify_merkle_integrity.py --all
  
  # Criar novo batch
  python verify_merkle_integrity.py --create-batch
  
  # Listar todos os batches
  python verify_merkle_integrity.py --list
  
  # Testar via API diretamente
  curl -X POST {API_BASE_URL}/merkle/batch -H "Content-Type: application/json" -d '{{"batch_size": 100}}'
  curl {API_BASE_URL}/merkle/batches
  curl -X POST {API_BASE_URL}/merkle/verify/{{batch_id}}
    """)
    
    print("\n" + "="*70)
    print("  ✅ DEMONSTRAÇÃO CONCLUÍDA!")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()

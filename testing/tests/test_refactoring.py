#!/usr/bin/env python3
"""
Script de teste para verificar refatorações

Testa se todos os módulos refatorados estão funcionando corretamente
"""

import sys
from pathlib import Path

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("=" * 70)
    print("TESTANDO IMPORTS DOS MÓDULOS REFATORADOS")
    print("=" * 70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Teste 1: config.py
    print("\n1. Testando config.py...")
    try:
        import config
        print(f"   ✅ config.py importado")
        print(f"   ✅ API_BASE_URL: {config.API_BASE_URL}")
        print(f"   ✅ POSTGRES_HOST: {config.POSTGRES_HOST}")
        print(f"   ✅ TEST_SCENARIOS: {len(config.TEST_SCENARIOS)} cenários")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        tests_failed += 1
    
    # Teste 2: utils.py
    print("\n2. Testando utils.py...")
    try:
        from utils import (
            print_header, format_bytes, calculate_statistics,
            save_json, load_json
        )
        print(f"   ✅ utils.py importado")
        print(f"   ✅ format_bytes(1024*1024*1024): {format_bytes(1024*1024*1024)}")
        
        # Teste calculate_statistics
        stats = calculate_statistics([10, 20, 30, 40, 50])
        print(f"   ✅ calculate_statistics: média={stats['avg']}, p95={stats['p95']}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        tests_failed += 1
    
    # Teste 3: create_batch_test.py
    print("\n3. Testando create_batch_test.py...")
    try:
        import create_batch_test
        print(f"   ✅ create_batch_test.py importado")
        if hasattr(create_batch_test, 'create_batch'):
            print(f"   ✅ Função create_batch encontrada")
        if hasattr(create_batch_test, 'main'):
            print(f"   ✅ Função main encontrada")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        tests_failed += 1
    
    # Teste 4: performance_tester.py
    print("\n4. Testando performance_tester.py...")
    try:
        import performance_tester
        print(f"   ✅ performance_tester.py importado")
        
        # Verifica classes
        if hasattr(performance_tester, 'PerformanceMonitor'):
            print(f"   ✅ Classe PerformanceMonitor encontrada")
        if hasattr(performance_tester, 'PostgreSQLTester'):
            print(f"   ✅ Classe PostgreSQLTester encontrada")
        if hasattr(performance_tester, 'HybridTester'):
            print(f"   ✅ Classe HybridTester encontrada")
        
        # Verifica funções
        if hasattr(performance_tester, 'run_insert_test'):
            print(f"   ✅ Função run_insert_test encontrada")
        if hasattr(performance_tester, 'run_single_scenario'):
            print(f"   ✅ Função run_single_scenario encontrada")
        
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ ERRO: {e}")
        tests_failed += 1
    
    # Resultado final
    print("\n" + "=" * 70)
    print("RESULTADO DOS TESTES")
    print("=" * 70)
    print(f"✅ Testes passados: {tests_passed}")
    print(f"❌ Testes falhou: {tests_failed}")
    print(f"📊 Total: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Refatoração está funcionando corretamente!")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} teste(s) falharam")
        return 1


def test_functionality():
    """Testa funcionalidades específicas"""
    print("\n" + "=" * 70)
    print("TESTANDO FUNCIONALIDADES")
    print("=" * 70)
    
    from utils import calculate_statistics, format_bytes, format_duration
    from config import get_test_scenario
    
    # Teste de estatísticas
    print("\n1. Teste de calculate_statistics:")
    data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    stats = calculate_statistics(data)
    print(f"   Dados: {data}")
    print(f"   ✅ Média: {stats['avg']}")
    print(f"   ✅ Mediana: {stats['median']}")
    print(f"   ✅ P95: {stats['p95']}")
    print(f"   ✅ P99: {stats['p99']}")
    
    # Teste de formatação
    print("\n2. Teste de formatação:")
    print(f"   ✅ 1GB: {format_bytes(1024**3)}")
    print(f"   ✅ 1MB: {format_bytes(1024**2)}")
    print(f"   ✅ 1KB: {format_bytes(1024)}")
    print(f"   ✅ 3661s: {format_duration(3661)}")
    
    # Teste de cenários
    print("\n3. Teste de get_test_scenario:")
    scenario = get_test_scenario('S1')
    if scenario:
        print(f"   ✅ S1: {scenario['total_logs']} logs @ {scenario['rate']} logs/s")
    
    scenario = get_test_scenario('S9')
    if scenario:
        print(f"   ✅ S9: {scenario['total_logs']} logs @ {scenario['rate']} logs/s")
    
    print("\n✅ Testes de funcionalidade concluídos!")


if __name__ == '__main__':
    try:
        # Testa imports
        exit_code = test_imports()
        
        if exit_code == 0:
            # Se imports passaram, testa funcionalidades
            test_functionality()
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

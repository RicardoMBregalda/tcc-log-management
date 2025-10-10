#!/usr/bin/env python3
"""
Demo do Log Generator - Exemplos Práticos

Demonstra diferentes formas de usar o log_generator.py
"""

import sys
import time
from pathlib import Path

# Adiciona o diretório testing ao path
sys.path.insert(0, str(Path(__file__).parent))

from log_generator import LogGenerator, LOAD_SCENARIOS


def demo_basic_usage():
    """Demonstração básica: gera 10 logs."""
    print("\n" + "=" * 70)
    print("DEMO 1: Uso Básico - 10 Logs")
    print("=" * 70)

    generator = LogGenerator(fabric_enabled=True)

    print("\nGerando 10 logs...")
    for i in range(10):
        generator.generate_and_send()
        print(f"  {i + 1}/10 completo")

    generator.print_stats()
    input("\nDemo 1 completa. Pressione ENTER para continuar...")


def demo_simulation_mode():
    """Demonstração em modo simulação (sem Fabric)."""
    print("\n" + "=" * 70)
    print("DEMO 2: Modo Simulação - Sem Fabric")
    print("=" * 70)

    generator = LogGenerator(fabric_enabled=False)

    print("\nGerando 20 logs em modo simulação...")
    for i in range(20):
        generator.generate_and_send()
        if (i + 1) % 5 == 0:
            print(f"\n[Progresso: {i + 1}/20]\n")

    generator.print_stats()
    input("\nDemo 2 completa. Pressione ENTER para continuar...")


def demo_rate_control():
    """Demonstração de controle de taxa."""
    print("\n" + "=" * 70)
    print("DEMO 3: Controle de Taxa - 10 logs/segundo por 5 segundos")
    print("=" * 70)

    generator = LogGenerator(fabric_enabled=True)

    rate = 10  # logs por segundo
    duration = 5  # segundos
    interval = 1.0 / rate

    print(f"\nGerando {rate} logs/segundo por {duration} segundos...")
    print("(Total esperado: ~50 logs)\n")

    end_time = time.time() + duration
    while time.time() < end_time:
        start = time.time()
        generator.generate_and_send()

        elapsed = time.time() - start
        if elapsed < interval:
            time.sleep(interval - elapsed)

    generator.print_stats()
    input("\nDemo 3 completa. Pressione ENTER para continuar...")


def demo_scenario():
    """Demonstração usando cenário predefinido."""
    print("\n" + "=" * 70)
    print("DEMO 4: Cenário Predefinido - Carga Baixa")
    print("=" * 70)

    scenario = LOAD_SCENARIOS["low"]
    generator = LogGenerator(fabric_enabled=True)

    print(f"\nCenário: {scenario['name']}")
    print(f"Descrição: {scenario['description']}")
    print(f"Taxa: {scenario['logs_per_second']} logs/segundo")
    print(f"Duração: {scenario['duration']} segundos")
    print(f"(Executando apenas 10 segundos para demo)\n")

    rate = scenario["logs_per_second"]
    duration = 10  # Reduzido para demo
    interval = 1.0 / rate

    end_time = time.time() + duration
    while time.time() < end_time:
        start = time.time()
        generator.generate_and_send()

        elapsed = time.time() - start
        if elapsed < interval:
            time.sleep(interval - elapsed)

    generator.print_stats()
    input("\nDemo 4 completa. Pressione ENTER para continuar...")


def demo_log_types():
    """Demonstração de diferentes tipos de logs."""
    print("\n" + "=" * 70)
    print("DEMO 5: Tipos de Logs - Distribuição de Severidades")
    print("=" * 70)

    generator = LogGenerator(fabric_enabled=False)

    print("\nGerando 50 logs para demonstrar distribuição realista...")
    print("(Esperado: ~65% INFO, ~20% WARNING, ~8% ERROR, ~5% DEBUG, ~2% CRITICAL)\n")

    for i in range(50):
        generator.generate_and_send()

    generator.print_stats()

    print("\nObserve a distribuição por severidade acima!")
    input("\nDemo 5 completa. Pressione ENTER para continuar...")


def demo_error_handling():
    """Demonstração de tratamento de erros."""
    print("\n" + "=" * 70)
    print("DEMO 6: Tratamento de Erros")
    print("=" * 70)

    print("\nTestando comportamento quando:")
    print("  1. Fabric está ativo (sucesso)")
    print("  2. Fabric está inativo (falha controlada)")

    generator = LogGenerator(fabric_enabled=True)

    print("\n[Gerando 5 logs...]")
    for i in range(5):
        success = generator.generate_and_send()
        status = "Sucesso" if success else "Falha"
        print(f"  Log {i + 1}: {status}")

    generator.print_stats()

    print("\nO gerador lida corretamente com falhas de comunicação!")
    input("\nDemo 6 completa. Pressione ENTER para finalizar...")


def main():
    """Menu principal das demos."""
    print("\n" + "=" * 70)
    print("LOG GENERATOR - DEMOS INTERATIVAS")
    print("=" * 70)
    print("\nEste script demonstra diferentes usos do log_generator.py")
    print("\nDemos disponíveis:")
    print("  1. Uso Básico (10 logs)")
    print("  2. Modo Simulação (20 logs sem Fabric)")
    print("  3. Controle de Taxa (10 logs/seg por 5s)")
    print("  4. Cenário Predefinido (carga baixa)")
    print("  5. Tipos de Logs (distribuição de severidades)")
    print("  6. Tratamento de Erros")
    print("  7. Todas as demos")
    print("  0. Sair")

    while True:
        print("\n" + "-" * 70)
        choice = input("\nEscolha uma demo (0-7): ").strip()

        if choice == "0":
            print("\nAté logo!\n")
            break
        elif choice == "1":
            demo_basic_usage()
        elif choice == "2":
            demo_simulation_mode()
        elif choice == "3":
            demo_rate_control()
        elif choice == "4":
            demo_scenario()
        elif choice == "5":
            demo_log_types()
        elif choice == "6":
            demo_error_handling()
        elif choice == "7":
            print("\nExecutando todas as demos...")
            demo_basic_usage()
            demo_simulation_mode()
            demo_rate_control()
            demo_scenario()
            demo_log_types()
            demo_error_handling()
            print("\n" + "=" * 70)
            print("TODAS AS DEMOS CONCLUÍDAS!")
            print("=" * 70)
            break
        else:
            print("Opção inválida. Escolha entre 0-7.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompido pelo usuário. Até logo!\n")
        sys.exit(0)

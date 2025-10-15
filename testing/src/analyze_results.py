#!/usr/bin/env python3
"""
Analisador de Resultados de Performance - TCC

Lê os resultados dos cenários de teste e gera relatórios comparativos
Suporta tanto o formato novo (cenários S1-S9) quanto o antigo

Refatorado para usar config.py e utils.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Adiciona o diretório pai ao path para importar config e utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports do projeto
from config import RESULTS_DIR, TEST_SCENARIOS
from utils import (
    load_json,
    save_json,
    print_header,
    print_section,
    format_number,
    get_timestamp
)


def load_scenario_results(results_dir: str = RESULTS_DIR) -> List[Dict[str, Any]]:
    """
    Carrega todos os resultados de cenários
    
    Args:
        results_dir: Diretório com resultados
        
    Returns:
        Lista de resultados de cenários
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        print(f"Erro: Diretório {results_dir} não encontrado")
        print("Execute os testes primeiro com: ./run_quick_test.sh")
        sys.exit(1)
    
    # Tenta carregar all_scenarios.json
    all_scenarios_file = results_path / 'all_scenarios.json'
    if all_scenarios_file.exists():
        return load_json(str(all_scenarios_file))
    
    # Caso contrário, carrega arquivos individuais
    scenario_files = sorted(results_path.glob('scenario_*.json'))
    if not scenario_files:
        print(f"Erro: Nenhum arquivo de resultado encontrado em {results_dir}")
        print("Execute os testes primeiro com: ./run_quick_test.sh")
        sys.exit(1)
    
    results = []
    for file in scenario_files:
        results.append(load_json(str(file)))
    
    return results


def load_results(filename: str = 'performance_results.json') -> Dict[str, Any]:
    """
    Carrega resultados do arquivo JSON (formato antigo)
    
    Args:
        filename: Nome do arquivo JSON
        
    Returns:
        Dicionário com resultados
    """
    try:
        return load_json(filename)
    except FileNotFoundError:
        print(f"Erro: Arquivo {filename} não encontrado")
        sys.exit(1)
    except Exception as e:
        print(f"Erro: Arquivo {filename} não é um JSON válido: {e}")
        sys.exit(1)


def generate_markdown_report(results: Dict[str, Any]) -> str:
    """
    Gera relatório em Markdown
    
    Args:
        results: Dicionário com resultados dos testes
        
    Returns:
        String com relatório em Markdown
    """
    report = []
    
    report.append("# Relatório de Performance - TCC Log Management\n")
    report.append(f"**Data/Hora:** {results['timestamp']}\n")
    report.append("---\n")
    
    # Separa resultados por arquitetura
    pg_insert: Optional[Dict[str, Any]] = None
    pg_query: Optional[Dict[str, Any]] = None
    hybrid_insert: Optional[Dict[str, Any]] = None
    hybrid_query: Optional[Dict[str, Any]] = None
    
    for test in results['tests']:
        if test['architecture'] == 'postgresql':
            if test['type'] == 'insert':
                pg_insert = test['results']
            else:
                pg_query = test['results']
        else:  # hybrid
            if test['type'] == 'insert':
                hybrid_insert = test['results']
            else:
                hybrid_query = test['results']
    
    # Tabela de Throughput
    report.append("## 1. Throughput (Operações/Segundo)\n")
    report.append("| Tipo de Operação | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |\n")
    report.append("|-----------------|------------|------------------------|------------|\n")
    
    if pg_insert and hybrid_insert:
        diff = ((hybrid_insert['throughput'] - pg_insert['throughput']) / pg_insert['throughput'] * 100)
        report.append(f"| **Inserção** | {pg_insert['throughput']:.2f} | {hybrid_insert['throughput']:.2f} | {diff:+.1f}% |\n")
    
    if pg_query and hybrid_query:
        diff = ((hybrid_query['throughput'] - pg_query['throughput']) / pg_query['throughput'] * 100)
        report.append(f"| **Consulta** | {pg_query['throughput']:.2f} | {hybrid_query['throughput']:.2f} | {diff:+.1f}% |\n")
    
    report.append("\n")
    
    # Tabela de Latência
    report.append("## 2. Latência (ms)\n")
    report.append("### 2.1. Inserção\n")
    report.append("| Métrica | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |\n")
    report.append("|---------|------------|------------------------|------------|\n")
    
    if pg_insert and hybrid_insert:
        for metric in ['avg', 'median', 'p95', 'p99', 'min', 'max']:
            pg_val = pg_insert['latency'][metric]
            hybrid_val = hybrid_insert['latency'][metric]
            diff = ((hybrid_val - pg_val) / pg_val * 100) if pg_val > 0 else 0
            metric_name = {
                'avg': 'Média',
                'median': 'Mediana',
                'p95': 'P95',
                'p99': 'P99',
                'min': 'Mínimo',
                'max': 'Máximo'
            }[metric]
            report.append(f"| {metric_name} | {pg_val:.2f} | {hybrid_val:.2f} | {diff:+.1f}% |\n")
    
    report.append("\n### 2.2. Consulta\n")
    report.append("| Métrica | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |\n")
    report.append("|---------|------------|------------------------|------------|\n")
    
    if pg_query and hybrid_query:
        for metric in ['avg', 'median', 'p95', 'p99', 'min', 'max']:
            pg_val = pg_query['latency'][metric]
            hybrid_val = hybrid_query['latency'][metric]
            diff = ((hybrid_val - pg_val) / pg_val * 100) if pg_val > 0 else 0
            metric_name = {
                'avg': 'Média',
                'median': 'Mediana',
                'p95': 'P95',
                'p99': 'P99',
                'min': 'Mínimo',
                'max': 'Máximo'
            }[metric]
            report.append(f"| {metric_name} | {pg_val:.2f} | {hybrid_val:.2f} | {diff:+.1f}% |\n")
    
    report.append("\n")
    
    # Tabela de Recursos
    report.append("## 3. Uso de Recursos\n")
    report.append("### 3.1. CPU (%)\n")
    report.append("| Operação | Métrica | PostgreSQL | Híbrido (Fabric+Mongo) |\n")
    report.append("|----------|---------|------------|------------------------|\n")
    
    if pg_insert and hybrid_insert:
        report.append(f"| Inserção | Média | {pg_insert['resources']['cpu']['avg']:.1f}% | {hybrid_insert['resources']['cpu']['avg']:.1f}% |\n")
        report.append(f"| Inserção | Máxima | {pg_insert['resources']['cpu']['max']:.1f}% | {hybrid_insert['resources']['cpu']['max']:.1f}% |\n")
    
    if pg_query and hybrid_query:
        report.append(f"| Consulta | Média | {pg_query['resources']['cpu']['avg']:.1f}% | {hybrid_query['resources']['cpu']['avg']:.1f}% |\n")
        report.append(f"| Consulta | Máxima | {pg_query['resources']['cpu']['max']:.1f}% | {hybrid_query['resources']['cpu']['max']:.1f}% |\n")
    
    report.append("\n### 3.2. Memória (%)\n")
    report.append("| Operação | Métrica | PostgreSQL | Híbrido (Fabric+Mongo) |\n")
    report.append("|----------|---------|------------|------------------------|\n")
    
    if pg_insert and hybrid_insert:
        report.append(f"| Inserção | Média | {pg_insert['resources']['memory']['avg']:.1f}% | {hybrid_insert['resources']['memory']['avg']:.1f}% |\n")
        report.append(f"| Inserção | Máxima | {pg_insert['resources']['memory']['max']:.1f}% | {hybrid_insert['resources']['memory']['max']:.1f}% |\n")
    
    if pg_query and hybrid_query:
        report.append(f"| Consulta | Média | {pg_query['resources']['memory']['avg']:.1f}% | {hybrid_query['resources']['memory']['avg']:.1f}% |\n")
        report.append(f"| Consulta | Máxima | {pg_query['resources']['memory']['max']:.1f}% | {hybrid_query['resources']['memory']['max']:.1f}% |\n")
    
    report.append("\n### 3.3. Disco (MB)\n")
    report.append("| Operação | Tipo | PostgreSQL | Híbrido (Fabric+Mongo) |\n")
    report.append("|----------|------|------------|------------------------|\n")
    
    if pg_insert and hybrid_insert:
        report.append(f"| Inserção | Leitura | {pg_insert['resources']['disk']['read_mb']:.2f} | {hybrid_insert['resources']['disk']['read_mb']:.2f} |\n")
        report.append(f"| Inserção | Escrita | {pg_insert['resources']['disk']['write_mb']:.2f} | {hybrid_insert['resources']['disk']['write_mb']:.2f} |\n")
    
    if pg_query and hybrid_query:
        report.append(f"| Consulta | Leitura | {pg_query['resources']['disk']['read_mb']:.2f} | {hybrid_query['resources']['disk']['read_mb']:.2f} |\n")
        report.append(f"| Consulta | Escrita | {pg_query['resources']['disk']['write_mb']:.2f} | {hybrid_query['resources']['disk']['write_mb']:.2f} |\n")
    
    report.append("\n")
    
    # Análise
    report.append("## 4. Análise e Conclusões\n")
    
    if pg_insert and hybrid_insert:
        throughput_diff = ((hybrid_insert['throughput'] - pg_insert['throughput']) / pg_insert['throughput'] * 100)
        latency_diff = ((hybrid_insert['latency']['avg'] - pg_insert['latency']['avg']) / pg_insert['latency']['avg'] * 100)
        
        report.append("### 4.1. Inserção de Logs\n")
        
        if throughput_diff < -10:
            report.append(f"- O sistema híbrido apresenta **throughput {abs(throughput_diff):.1f}% menor** devido ao overhead da sincronização com Fabric\n")
        elif throughput_diff > 10:
            report.append(f"- O sistema híbrido apresenta **throughput {throughput_diff:.1f}% maior** (resultado inesperado - verificar configurações)\n")
        else:
            report.append(f"- Throughput similar entre as arquiteturas ({throughput_diff:+.1f}%)\n")
        
        if latency_diff > 20:
            report.append(f"- Latência média **{latency_diff:.1f}% maior** no híbrido devido à gravação na blockchain\n")
        else:
            report.append(f"- Latência média similar ({latency_diff:+.1f}%)\n")
        
        report.append(f"- **Trade-off:** A arquitetura híbrida sacrifica {abs(throughput_diff):.1f}% de throughput em troca de imutabilidade e auditoria\n")
        report.append("\n")
    
    if pg_query and hybrid_query:
        throughput_diff = ((hybrid_query['throughput'] - pg_query['throughput']) / pg_query['throughput'] * 100)
        
        report.append("### 4.2. Consulta de Logs\n")
        
        if abs(throughput_diff) < 10:
            report.append(f"- Performance de consulta similar ({throughput_diff:+.1f}%) - ambas arquiteturas usam PostgreSQL para leitura\n")
        else:
            report.append(f"- Diferença de {throughput_diff:+.1f}% no throughput de consulta\n")
        
        report.append("- Consultas não são impactadas pela blockchain (somente escritas)\n")
        report.append("\n")
    
    report.append("### 4.3. Recomendações\n")
    report.append("- **PostgreSQL Tradicional:** Melhor para cenários que priorizam throughput máximo\n")
    report.append("- **Híbrido (Fabric+Mongo):** Ideal para cenários que necessitam auditoria, imutabilidade e rastreabilidade\n")
    report.append("- O overhead da blockchain é aceitável considerando os benefícios de governança e compliance\n")
    report.append("\n")
    
    report.append("---\n")
    report.append("*Relatório gerado automaticamente por analyze_results.py*\n")
    
    return ''.join(report)


def generate_csv_report(results: Dict[str, Any]) -> str:
    """
    Gera relatório em CSV
    
    Args:
        results: Dicionário com resultados dos testes
        
    Returns:
        String com relatório em CSV
    """
    csv = []
    
    csv.append("Arquitetura,Tipo,Throughput,Latencia_Avg,Latencia_Median,Latencia_P95,Latencia_P99,CPU_Avg,CPU_Max,Memory_Avg,Memory_Max,Disk_Read_MB,Disk_Write_MB\n")
    
    for test in results['tests']:
        arch = test['architecture']
        tipo = test['type']
        r = test['results']
        
        csv.append(f"{arch},{tipo},{r['throughput']:.2f},{r['latency']['avg']:.2f},{r['latency']['median']:.2f},{r['latency']['p95']:.2f},{r['latency']['p99']:.2f},{r['resources']['cpu']['avg']:.1f},{r['resources']['cpu']['max']:.1f},{r['resources']['memory']['avg']:.1f},{r['resources']['memory']['max']:.1f},{r['resources']['disk']['read_mb']:.2f},{r['resources']['disk']['write_mb']:.2f}\n")
    
    return ''.join(csv)


def main() -> None:
    """Gera relatórios a partir dos resultados JSON"""
    
    # Verifica se deve usar novo formato (cenários)
    if '--scenarios' in sys.argv or Path('results').exists():
        print("Analisando resultados de cenários...")
        analyze_scenarios()
        return
    
    # Formato antigo
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'performance_results.json'
    
    print(f"Carregando resultados de: {filename}")
    results = load_results(filename)
    
    # Gera relatório Markdown
    print("Gerando relatório Markdown...")
    markdown = generate_markdown_report(results)
    markdown_file = filename.replace('.json', '.md')
    with open(markdown_file, 'w') as f:
        f.write(markdown)
    print(f"Relatório Markdown salvo em: {markdown_file}")
    
    # Gera relatório CSV
    print("Gerando relatório CSV...")
    csv = generate_csv_report(results)
    csv_file = filename.replace('.json', '.csv')
    with open(csv_file, 'w') as f:
        f.write(csv)
    print(f"Relatório CSV salvo em: {csv_file}")
    
    print("\nRelatórios gerados com sucesso!")


def analyze_scenarios() -> None:
    """Analisa resultados dos cenários S1-S9"""
    results = load_scenario_results()
    
    print_header("ANÁLISE DE CENÁRIOS DE TESTE TCC")
    print(f"Total de resultados: {len(results)}\n")
    
    # Agrupa por cenário
    by_scenario: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        sid = r['scenario_id']
        if sid not in by_scenario:
            by_scenario[sid] = []
        by_scenario[sid].append(r)
    
    # Tabela resumo
    print_section("RESUMO POR CENÁRIO")
    print(f"{'Cenário':<10} {'Arq':<10} {'Throughput':<15} {'P95 (ms)':<12} {'CPU %':<10}")
    print("-" * 70)
    
    for sid in sorted(by_scenario.keys()):
        for r in sorted(by_scenario[sid], key=lambda x: x['architecture']):
            print(f"{sid:<10} {r['architecture']:<10} "
                  f"{r['execution']['actual_throughput_logs_per_second']:>8.1f} logs/s  "
                  f"{r['latency_insert_ms']['p95']:>8.2f}     "
                  f"{r['resources']['cpu']['avg']:>6.1f}")
    
    print("-" * 70)
    print()
    
    # Comparação lado a lado
    print("COMPARAÇÃO: HYBRID vs POSTGRESQL")
    print("-" * 70)
    print(f"{'Cenário':<10} {'Métrica':<20} {'Hybrid':<15} {'PostgreSQL':<15} {'Diff %':<10}")
    print("-" * 70)
    
    for sid in sorted(by_scenario.keys()):
        results_list = by_scenario[sid]
        hybrid = next((r for r in results_list if r['architecture'] == 'hybrid'), None)
        postgres = next((r for r in results_list if r['architecture'] == 'postgres'), None)
        
        if hybrid and postgres:
            # Throughput
            h_thr = hybrid['execution']['actual_throughput_logs_per_second']
            p_thr = postgres['execution']['actual_throughput_logs_per_second']
            diff_thr = ((h_thr - p_thr) / p_thr * 100) if p_thr > 0 else 0
            
            # Latência P95
            h_p95 = hybrid['latency_insert_ms']['p95']
            p_p95 = postgres['latency_insert_ms']['p95']
            diff_p95 = ((h_p95 - p_p95) / p_p95 * 100) if p_p95 > 0 else 0
            
            # CPU
            h_cpu = hybrid['resources']['cpu']['avg']
            p_cpu = postgres['resources']['cpu']['avg']
            diff_cpu = ((h_cpu - p_cpu) / p_cpu * 100) if p_cpu > 0 else 0
            
            print(f"{sid:<10} {'Throughput (logs/s)':<20} {h_thr:>8.1f}       {p_thr:>8.1f}       {diff_thr:>+6.1f}%")
            print(f"{'':<10} {'Latência P95 (ms)':<20} {h_p95:>8.2f}       {p_p95:>8.2f}       {diff_p95:>+6.1f}%")
            print(f"{'':<10} {'CPU Médio (%)':<20} {h_cpu:>8.1f}       {p_cpu:>8.1f}       {diff_cpu:>+6.1f}%")
            print("-" * 70)
    
    print()
    
    # Gera relatórios em arquivo
    generate_scenarios_markdown(results)
    generate_scenarios_csv(results)
    
    print("\n✓ Análise completa!")
    print("  - Relatório detalhado: results/scenarios_analysis.md")
    print("  - CSV para Excel: results/scenarios_analysis.csv")


def generate_scenarios_markdown(results: List[Dict[str, Any]]) -> None:
    """
    Gera relatório Markdown dos cenários
    
    Args:
        results: Lista de resultados de cenários
    """
    report = []
    
    report.append("# Análise de Cenários de Teste - TCC Log Management\n\n")
    report.append(f"**Data de Análise:** {get_timestamp()}\n\n")
    report.append("---\n\n")
    
    # Agrupa por cenário
    by_scenario: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        sid = r['scenario_id']
        if sid not in by_scenario:
            by_scenario[sid] = []
        by_scenario[sid].append(r)
    
    # Tabela resumo
    report.append("## Resumo Executivo\n\n")
    report.append("| Cenário | Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |\n")
    report.append("|---------|-------------|---------------------|----------|----------|----------|-------|-------|\n")
    
    for sid in sorted(by_scenario.keys()):
        for r in sorted(by_scenario[sid], key=lambda x: x['architecture']):
            report.append(f"| {sid} | {r['architecture'].upper()} | ")
            report.append(f"{r['execution']['actual_throughput_logs_per_second']:.1f} | ")
            report.append(f"{r['latency_insert_ms']['p50']:.2f} | ")
            report.append(f"{r['latency_insert_ms']['p95']:.2f} | ")
            report.append(f"{r['latency_insert_ms']['p99']:.2f} | ")
            report.append(f"{r['resources']['cpu']['avg']:.1f} | ")
            report.append(f"{r['resources']['memory']['avg']:.1f} |\n")
    
    report.append("\n")
    
    # Análise por cenário
    report.append("## Análise Detalhada por Cenário\n\n")
    
    for sid in sorted(by_scenario.keys()):
        results_list = by_scenario[sid]
        if not results_list:
            continue
        
        first = results_list[0]
        report.append(f"### {sid}: {first['scenario_name']}\n\n")
        report.append(f"**Configuração:**\n")
        report.append(f"- Volume: {first['config']['total_logs']:,} logs\n")
        report.append(f"- Taxa alvo: {first['config']['target_rate']} logs/segundo\n\n")
        
        hybrid = next((r for r in results_list if r['architecture'] == 'hybrid'), None)
        postgres = next((r for r in results_list if r['architecture'] == 'postgres'), None)
        
        if hybrid and postgres:
            report.append("**Comparação:**\n\n")
            
            # Throughput
            h_thr = hybrid['execution']['actual_throughput_logs_per_second']
            p_thr = postgres['execution']['actual_throughput_logs_per_second']
            diff_thr = ((h_thr - p_thr) / p_thr * 100) if p_thr > 0 else 0
            winner_thr = "Hybrid" if h_thr > p_thr else "PostgreSQL"
            
            report.append(f"1. **Throughput:** {winner_thr} é {abs(diff_thr):.1f}% {'mais rápido' if diff_thr >= 0 else 'mais lento'}\n")
            report.append(f"   - Hybrid: {h_thr:.1f} logs/s\n")
            report.append(f"   - PostgreSQL: {p_thr:.1f} logs/s\n\n")
            
            # Latência
            h_p95 = hybrid['latency_insert_ms']['p95']
            p_p95 = postgres['latency_insert_ms']['p95']
            diff_p95 = ((h_p95 - p_p95) / p_p95 * 100) if p_p95 > 0 else 0
            winner_lat = "PostgreSQL" if p_p95 < h_p95 else "Hybrid"
            
            report.append(f"2. **Latência P95:** {winner_lat} é {abs(diff_p95):.1f}% {'melhor' if winner_lat == 'PostgreSQL' else 'melhor'}\n")
            report.append(f"   - Hybrid: {h_p95:.2f} ms\n")
            report.append(f"   - PostgreSQL: {p_p95:.2f} ms\n\n")
            
            # Recursos
            h_cpu = hybrid['resources']['cpu']['avg']
            p_cpu = postgres['resources']['cpu']['avg']
            report.append(f"3. **Uso de CPU:**\n")
            report.append(f"   - Hybrid: {h_cpu:.1f}%\n")
            report.append(f"   - PostgreSQL: {p_cpu:.1f}%\n\n")
        
        report.append("---\n\n")
    
    # Conclusões
    report.append("## Conclusões\n\n")
    report.append("### Arquitetura Híbrida (MongoDB + Fabric)\n\n")
    report.append("**Vantagens:**\n")
    report.append("- ✅ Imutabilidade e auditoria via blockchain\n")
    report.append("- ✅ Merkle Tree para verificação de integridade\n")
    report.append("- ✅ Auto-batching reduz transações na blockchain\n\n")
    
    report.append("**Desvantagens:**\n")
    report.append("- ⚠️ Overhead de sincronização com Fabric\n")
    report.append("- ⚠️ Latência adicional para escrita\n\n")
    
    report.append("### PostgreSQL Tradicional\n\n")
    report.append("**Vantagens:**\n")
    report.append("- ✅ Throughput máximo\n")
    report.append("- ✅ Latência mínima\n")
    report.append("- ✅ Simplicidade operacional\n\n")
    
    report.append("**Desvantagens:**\n")
    report.append("- ⚠️ Sem imutabilidade garantida\n")
    report.append("- ⚠️ Sem trilha de auditoria distribuída\n\n")
    
    report.append("### Recomendações\n\n")
    report.append("- **Use Hybrid:** Quando auditoria, compliance e imutabilidade são críticos\n")
    report.append("- **Use PostgreSQL:** Quando throughput máximo é prioritário\n")
    report.append("- **Trade-off aceitável:** O overhead da blockchain é justificável pelos benefícios de governança\n\n")
    
    report.append("---\n")
    report.append("*Relatório gerado automaticamente por analyze_results.py*\n")
    
    # Salva arquivo
    output_file = Path('results') / 'scenarios_analysis.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(report))




def generate_scenarios_csv(results: List[Dict[str, Any]]) -> None:
    """
    Gera CSV dos cenários
    
    Args:
        results: Lista de resultados de cenários
    """
    csv = []
    
    csv.append("scenario_id,scenario_name,architecture,total_logs,target_rate,")
    csv.append("actual_throughput,total_time_seconds,")
    csv.append("latency_p50_ms,latency_p95_ms,latency_p99_ms,latency_avg_ms,")
    csv.append("cpu_avg,cpu_max,ram_avg,ram_max,")
    csv.append("disk_read_mb,disk_write_mb\n")
    
    for r in results:
        csv.append(f"{r['scenario_id']},\"{r['scenario_name']}\",{r['architecture']},")
        csv.append(f"{r['config']['total_logs']},{r['config']['target_rate']},")
        csv.append(f"{r['execution']['actual_throughput_logs_per_second']:.2f},")
        csv.append(f"{r['execution']['total_time_seconds']:.2f},")
        csv.append(f"{r['latency_insert_ms']['p50']:.2f},")
        csv.append(f"{r['latency_insert_ms']['p95']:.2f},")
        csv.append(f"{r['latency_insert_ms']['p99']:.2f},")
        csv.append(f"{r['latency_insert_ms']['avg']:.2f},")
        csv.append(f"{r['resources']['cpu']['avg']:.1f},")
        csv.append(f"{r['resources']['cpu']['max']:.1f},")
        csv.append(f"{r['resources']['memory']['avg']:.1f},")
        csv.append(f"{r['resources']['memory']['max']:.1f},")
        csv.append(f"{r['resources']['disk']['read_mb']:.2f},")
        csv.append(f"{r['resources']['disk']['write_mb']:.2f}\n")
    
    # Salva arquivo
    output_file = Path(RESULTS_DIR) / 'scenarios_analysis.csv'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(csv))


if __name__ == '__main__':
    main()

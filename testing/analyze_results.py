#!/usr/bin/env python3
"""
Analisador de Resultados de Performance

Lê os resultados dos testes e gera relatórios comparativos
"""

import json
import sys
from pathlib import Path


def load_results(filename='performance_results.json'):
    """Carrega resultados do arquivo JSON"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {filename} não encontrado")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Erro: Arquivo {filename} não é um JSON válido")
        sys.exit(1)


def generate_markdown_report(results):
    """Gera relatório em Markdown"""
    report = []
    
    report.append("# Relatório de Performance - TCC Log Management\n")
    report.append(f"**Data/Hora:** {results['timestamp']}\n")
    report.append("---\n")
    
    # Separa resultados por arquitetura
    pg_insert = None
    pg_query = None
    hybrid_insert = None
    hybrid_query = None
    
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


def generate_csv_report(results):
    """Gera relatório em CSV"""
    csv = []
    
    csv.append("Arquitetura,Tipo,Throughput,Latencia_Avg,Latencia_Median,Latencia_P95,Latencia_P99,CPU_Avg,CPU_Max,Memory_Avg,Memory_Max,Disk_Read_MB,Disk_Write_MB\n")
    
    for test in results['tests']:
        arch = test['architecture']
        tipo = test['type']
        r = test['results']
        
        csv.append(f"{arch},{tipo},{r['throughput']:.2f},{r['latency']['avg']:.2f},{r['latency']['median']:.2f},{r['latency']['p95']:.2f},{r['latency']['p99']:.2f},{r['resources']['cpu']['avg']:.1f},{r['resources']['cpu']['max']:.1f},{r['resources']['memory']['avg']:.1f},{r['resources']['memory']['max']:.1f},{r['resources']['disk']['read_mb']:.2f},{r['resources']['disk']['write_mb']:.2f}\n")
    
    return ''.join(csv)


def main():
    """Gera relatórios a partir dos resultados JSON"""
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


if __name__ == '__main__':
    main()

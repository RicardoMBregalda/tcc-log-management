#!/usr/bin/env python3
"""
Script de Verificação Completa - TCC Log Management

Este script verifica a integridade de todos os arquivos e dados
na pasta testing/, incluindo:
- Sintaxe de arquivos Python
- Validade de arquivos JSON e CSV
- Configurações
- Dependências
- Estrutura de diretórios

Autor: Verificação Automatizada
Data: 2025-10-16
"""

import sys
import json
import csv
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict
import py_compile


# ==================== CONFIGURAÇÃO ====================

TESTING_DIR = Path(__file__).parent
RESULTS = {
    'python_files': [],
    'json_files': [],
    'csv_files': [],
    'errors': [],
    'warnings': [],
    'success': []
}


# ==================== CORES ====================

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# ==================== FUNÇÕES DE IMPRESSÃO ====================

def print_header(text: str):
    """Imprime cabeçalho"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}")
    print(f"{text.center(70)}")
    print(f"{'=' * 70}{Colors.ENDC}")


def print_section(text: str):
    """Imprime seção"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-' * 70}{Colors.ENDC}")


def print_success(text: str):
    """Imprime sucesso"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Imprime erro"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    RESULTS['errors'].append(text)


def print_warning(text: str):
    """Imprime aviso"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    RESULTS['warnings'].append(text)


def print_info(text: str):
    """Imprime informação"""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


# ==================== VERIFICADORES ====================

def verify_python_files() -> Tuple[int, int]:
    """
    Verifica sintaxe de todos os arquivos Python
    
    Returns:
        (valid_count, error_count)
    """
    print_section("Verificando Arquivos Python")
    
    python_files = list(TESTING_DIR.rglob("*.py"))
    valid = 0
    errors = 0
    
    for py_file in python_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
            print_success(f"{py_file.relative_to(TESTING_DIR)}")
            RESULTS['python_files'].append({
                'file': str(py_file.relative_to(TESTING_DIR)),
                'status': 'valid'
            })
            valid += 1
        except py_compile.PyCompileError as e:
            print_error(f"{py_file.relative_to(TESTING_DIR)}: {e}")
            RESULTS['python_files'].append({
                'file': str(py_file.relative_to(TESTING_DIR)),
                'status': 'error',
                'error': str(e)
            })
            errors += 1
    
    print_info(f"\nTotal: {len(python_files)} arquivos | Válidos: {valid} | Erros: {errors}")
    return (valid, errors)


def verify_json_files() -> Tuple[int, int]:
    """
    Verifica validade de todos os arquivos JSON
    
    Returns:
        (valid_count, error_count)
    """
    print_section("Verificando Arquivos JSON")
    
    json_files = list(TESTING_DIR.rglob("*.json"))
    valid = 0
    errors = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print_success(f"{json_file.relative_to(TESTING_DIR)}")
                RESULTS['json_files'].append({
                    'file': str(json_file.relative_to(TESTING_DIR)),
                    'status': 'valid',
                    'keys': len(data.keys()) if isinstance(data, dict) else None,
                    'items': len(data) if isinstance(data, list) else None
                })
                valid += 1
        except json.JSONDecodeError as e:
            print_error(f"{json_file.relative_to(TESTING_DIR)}: {e}")
            RESULTS['json_files'].append({
                'file': str(json_file.relative_to(TESTING_DIR)),
                'status': 'error',
                'error': str(e)
            })
            errors += 1
        except Exception as e:
            print_error(f"{json_file.relative_to(TESTING_DIR)}: {e}")
            errors += 1
    
    print_info(f"\nTotal: {len(json_files)} arquivos | Válidos: {valid} | Erros: {errors}")
    return (valid, errors)


def verify_csv_files() -> Tuple[int, int]:
    """
    Verifica validade de todos os arquivos CSV
    
    Returns:
        (valid_count, error_count)
    """
    print_section("Verificando Arquivos CSV")
    
    csv_files = list(TESTING_DIR.rglob("*.csv"))
    valid = 0
    errors = 0
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                if len(rows) < 1:
                    print_warning(f"{csv_file.relative_to(TESTING_DIR)}: Arquivo vazio")
                    continue
                
                headers = rows[0]
                data_rows = len(rows) - 1
                
                print_success(f"{csv_file.relative_to(TESTING_DIR)} "
                            f"({data_rows} linhas, {len(headers)} colunas)")
                
                RESULTS['csv_files'].append({
                    'file': str(csv_file.relative_to(TESTING_DIR)),
                    'status': 'valid',
                    'rows': data_rows,
                    'columns': len(headers),
                    'headers': headers
                })
                valid += 1
        except Exception as e:
            print_error(f"{csv_file.relative_to(TESTING_DIR)}: {e}")
            RESULTS['csv_files'].append({
                'file': str(csv_file.relative_to(TESTING_DIR)),
                'status': 'error',
                'error': str(e)
            })
            errors += 1
    
    print_info(f"\nTotal: {len(csv_files)} arquivos | Válidos: {valid} | Erros: {errors}")
    return (valid, errors)


def verify_configuration_files():
    """Verifica arquivos de configuração"""
    print_section("Verificando Arquivos de Configuração")
    
    # Verificar config.py
    config_file = TESTING_DIR / "config.py"
    if config_file.exists():
        try:
            # Importar config para validar
            sys.path.insert(0, str(TESTING_DIR))
            import config
            
            # Verificar funções essenciais
            if hasattr(config, 'validate_config'):
                is_valid = config.validate_config()
                if is_valid:
                    print_success("config.py: Todas as configurações válidas")
                    RESULTS['success'].append("Configurações validadas com sucesso")
                else:
                    print_warning("config.py: Algumas configurações inválidas")
            else:
                print_success("config.py: Importado com sucesso")
            
            # Verificar cenários de teste
            if hasattr(config, 'TEST_SCENARIOS'):
                scenarios = config.TEST_SCENARIOS
                print_info(f"  Cenários de teste definidos: {len(scenarios)}")
                for scenario_id in scenarios:
                    print_info(f"    - {scenario_id}: {scenarios[scenario_id]['description']}")
        except Exception as e:
            print_error(f"config.py: Erro ao importar - {e}")
    else:
        print_error("config.py: Arquivo não encontrado")
    
    # Verificar utils.py
    utils_file = TESTING_DIR / "utils.py"
    if utils_file.exists():
        try:
            import utils
            print_success("utils.py: Importado com sucesso")
            
            # Listar funções disponíveis
            functions = [name for name in dir(utils) if not name.startswith('_') and callable(getattr(utils, name))]
            print_info(f"  Funções utilitárias disponíveis: {len(functions)}")
        except Exception as e:
            print_error(f"utils.py: Erro ao importar - {e}")
    else:
        print_error("utils.py: Arquivo não encontrado")
    
    # Verificar requirements.txt
    req_file = TESTING_DIR / "requirements.txt"
    if req_file.exists():
        try:
            with open(req_file, 'r') as f:
                requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                print_success(f"requirements.txt: {len(requirements)} dependências listadas")
                for req in requirements:
                    print_info(f"  - {req}")
        except Exception as e:
            print_error(f"requirements.txt: Erro ao ler - {e}")
    else:
        print_warning("requirements.txt: Arquivo não encontrado")


def verify_directory_structure():
    """Verifica estrutura de diretórios"""
    print_section("Verificando Estrutura de Diretórios")
    
    expected_dirs = [
        "src",
        "tests",
        "results",
        "scripts",
        "demos"
    ]
    
    for dir_name in expected_dirs:
        dir_path = TESTING_DIR / dir_name
        if dir_path.exists() and dir_path.is_dir():
            files_count = len(list(dir_path.rglob("*")))
            print_success(f"{dir_name}/: Existe ({files_count} arquivos)")
        else:
            print_warning(f"{dir_name}/: Diretório não encontrado")


def verify_scripts_executability():
    """Verifica se scripts shell são executáveis"""
    print_section("Verificando Scripts Shell")
    
    shell_scripts = list(TESTING_DIR.rglob("*.sh"))
    
    if not shell_scripts:
        print_info("Nenhum script shell encontrado")
        return
    
    for script in shell_scripts:
        is_executable = script.stat().st_mode & 0o111
        if is_executable:
            print_success(f"{script.relative_to(TESTING_DIR)}: Executável")
        else:
            print_warning(f"{script.relative_to(TESTING_DIR)}: Não é executável (use chmod +x)")


def generate_report():
    """Gera relatório final"""
    print_header("RELATÓRIO FINAL DE VERIFICAÇÃO")
    
    total_errors = len(RESULTS['errors'])
    total_warnings = len(RESULTS['warnings'])
    
    print(f"\n{Colors.BOLD}Resumo:{Colors.ENDC}")
    print(f"  Arquivos Python verificados: {len(RESULTS['python_files'])}")
    print(f"  Arquivos JSON verificados: {len(RESULTS['json_files'])}")
    print(f"  Arquivos CSV verificados: {len(RESULTS['csv_files'])}")
    
    if total_errors > 0:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ {total_errors} ERRO(S) ENCONTRADO(S):{Colors.ENDC}")
        for error in RESULTS['errors']:
            print(f"  {Colors.FAIL}- {error}{Colors.ENDC}")
    
    if total_warnings > 0:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ {total_warnings} AVISO(S):{Colors.ENDC}")
        for warning in RESULTS['warnings']:
            print(f"  {Colors.WARNING}- {warning}{Colors.ENDC}")
    
    if total_errors == 0 and total_warnings == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ TUDO OK! Nenhum erro ou aviso encontrado.{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{'═' * 70}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}{Colors.BOLD}  A PASTA TESTING ESTÁ ÍNTEGRA E VÁLIDA  {Colors.ENDC}")
        print(f"{Colors.OKGREEN}{'═' * 70}{Colors.ENDC}\n")
    elif total_errors == 0:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ Verificação concluída com avisos{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}✗ Verificação falhou - corrija os erros acima{Colors.ENDC}")
    
    # Salvar relatório JSON
    report_file = TESTING_DIR / "verification_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(RESULTS, f, indent=2, ensure_ascii=False)
        print(f"\n{Colors.OKBLUE}ℹ Relatório salvo em: {report_file.relative_to(TESTING_DIR.parent)}{Colors.ENDC}\n")
    except Exception as e:
        print_error(f"Erro ao salvar relatório: {e}")
    
    return total_errors


# ==================== MAIN ====================

def main():
    """Função principal"""
    print_header("VERIFICAÇÃO COMPLETA - PASTA TESTING")
    print(f"\n{Colors.OKBLUE}Diretório: {TESTING_DIR}{Colors.ENDC}\n")
    
    # Executar verificações
    verify_directory_structure()
    verify_python_files()
    verify_json_files()
    verify_csv_files()
    verify_configuration_files()
    verify_scripts_executability()
    
    # Gerar relatório
    exit_code = generate_report()
    
    sys.exit(1 if exit_code > 0 else 0)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Utilitários Comuns - TCC Log Management

Funções auxiliares reutilizáveis em todo o projeto
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


# ==================== FORMATAÇÃO E IMPRESSÃO ====================

def print_header(title: str, width: int = 70, char: str = "=") -> None:
    """
    Imprime cabeçalho formatado
    
    Args:
        title: Título do cabeçalho
        width: Largura total do cabeçalho
        char: Caractere para a linha
    """
    print("\n" + char * width)
    print(title.center(width))
    print(char * width)


def print_section(title: str, width: int = 70, char: str = "-") -> None:
    """
    Imprime seção formatada
    
    Args:
        title: Título da seção
        width: Largura total
        char: Caractere para a linha
    """
    print("\n" + char * width)
    print(f"  {title}")
    print(char * width)


def print_key_value(key: str, value: Any, indent: int = 0) -> None:
    """
    Imprime par chave-valor formatado
    
    Args:
        key: Nome da chave
        value: Valor a imprimir
        indent: Nível de indentação (espaços)
    """
    spaces = " " * indent
    print(f"{spaces}{key}: {value}")


def format_bytes(bytes_value: int, decimals: int = 2) -> str:
    """
    Formata bytes em unidade legível (KB, MB, GB)
    
    Args:
        bytes_value: Valor em bytes
        decimals: Número de casas decimais
        
    Returns:
        String formatada (ex: "123.45 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.{decimals}f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.{decimals}f} PB"


def format_duration(seconds: float) -> str:
    """
    Formata duração em formato legível
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "1h 23m 45s" ou "45.32s")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.0f}s"


def format_number(number: float, decimals: int = 2) -> str:
    """
    Formata número com separador de milhares
    
    Args:
        number: Número a formatar
        decimals: Casas decimais
        
    Returns:
        String formatada (ex: "1,234.56")
    """
    return f"{number:,.{decimals}f}"


# ==================== ARQUIVOS E DIRETÓRIOS ====================

def ensure_directory(directory: str) -> Path:
    """
    Garante que um diretório existe, criando se necessário
    
    Args:
        directory: Caminho do diretório
        
    Returns:
        Path object do diretório
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Dict, filepath: str, indent: int = 2) -> bool:
    """
    Salva dados em arquivo JSON
    
    Args:
        data: Dados a salvar
        filepath: Caminho do arquivo
        indent: Indentação JSON
        
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar JSON em {filepath}: {e}")
        return False


def load_json(filepath: str) -> Optional[Dict]:
    """
    Carrega dados de arquivo JSON
    
    Args:
        filepath: Caminho do arquivo
        
    Returns:
        Dicionário com dados ou None em caso de erro
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar {filepath}: {e}")
        return None


# ==================== TIMESTAMP E DATA ====================

def get_timestamp() -> str:
    """
    Retorna timestamp atual em formato ISO 8601 com microsegundos
    
    Returns:
        String timestamp (ex: "2025-10-14T12:34:56.123456Z")
    """
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def get_timestamp_filename() -> str:
    """
    Retorna timestamp para uso em nomes de arquivo
    
    Returns:
        String timestamp (ex: "20251014_123456")
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def get_readable_timestamp() -> str:
    """
    Retorna timestamp legível para relatórios
    
    Returns:
        String timestamp (ex: "2025-10-14 12:34:56")
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ==================== VALIDAÇÃO ====================

def validate_positive_int(value: Any, name: str = "valor") -> int:
    """
    Valida e converte para inteiro positivo
    
    Args:
        value: Valor a validar
        name: Nome do parâmetro (para mensagens de erro)
        
    Returns:
        Inteiro positivo validado
        
    Raises:
        ValueError: Se valor inválido
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError(f"{name} deve ser maior que 0, recebido: {value}")
        return int_value
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name} deve ser um inteiro positivo, recebido: {value}") from e


def validate_port(port: Any) -> int:
    """
    Valida número de porta
    
    Args:
        port: Porta a validar
        
    Returns:
        Porta validada
        
    Raises:
        ValueError: Se porta inválida
    """
    try:
        port_int = int(port)
        if not (1 <= port_int <= 65535):
            raise ValueError(f"Porta deve estar entre 1 e 65535, recebido: {port}")
        return port_int
    except (TypeError, ValueError) as e:
        raise ValueError(f"Porta inválida: {port}") from e


# ==================== ESTATÍSTICAS ====================

def calculate_percentile(values: list, percentile: float) -> float:
    """
    Calcula percentil de uma lista de valores
    
    Args:
        values: Lista de valores numéricos
        percentile: Percentil desejado (0-100)
        
    Returns:
        Valor do percentil
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    index = (percentile / 100) * (len(sorted_values) - 1)
    
    if index.is_integer():
        return sorted_values[int(index)]
    else:
        lower = sorted_values[int(index)]
        upper = sorted_values[int(index) + 1]
        fraction = index - int(index)
        return lower + (upper - lower) * fraction


def calculate_statistics(values: list) -> Dict[str, float]:
    """
    Calcula estatísticas básicas de uma lista
    
    Args:
        values: Lista de valores numéricos
        
    Returns:
        Dicionário com estatísticas (mean, median, min, max, p50, p95, p99)
    """
    if not values:
        return {
            'mean': 0.0,
            'median': 0.0,
            'min': 0.0,
            'max': 0.0,
            'p50': 0.0,
            'p95': 0.0,
            'p99': 0.0
        }
    
    import statistics
    
    return {
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'min': min(values),
        'max': max(values),
        'p50': calculate_percentile(values, 50),
        'p95': calculate_percentile(values, 95),
        'p99': calculate_percentile(values, 99)
    }


# ==================== RETRY E TRATAMENTO DE ERROS ====================

def retry_on_failure(func, max_attempts: int = 3, delay: float = 1.0, 
                    backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator para retry com backoff exponencial
    
    Args:
        func: Função a executar
        max_attempts: Número máximo de tentativas
        delay: Delay inicial em segundos
        backoff: Multiplicador de delay
        exceptions: Tupla de exceções para capturar
        
    Returns:
        Resultado da função ou lança exceção após tentativas esgotadas
    """
    def wrapper(*args, **kwargs):
        current_delay = delay
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_attempts:
                    raise
                print(f"⚠️  Tentativa {attempt}/{max_attempts} falhou: {e}")
                print(f"   Aguardando {current_delay:.1f}s antes de tentar novamente...")
                time.sleep(current_delay)
                current_delay *= backoff
    
    return wrapper


# ==================== PROGRESS TRACKING ====================

class ProgressTracker:
    """Rastreador simples de progresso"""
    
    def __init__(self, total: int, description: str = "Progresso"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, increment: int = 1) -> None:
        """Atualiza progresso"""
        self.current += increment
        self.print_progress()
    
    def print_progress(self) -> None:
        """Imprime barra de progresso"""
        if self.total == 0:
            return
        
        percent = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        
        # Estima tempo restante
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = format_duration(eta)
        else:
            eta_str = "calculando..."
        
        bar_length = 40
        filled = int(bar_length * self.current / self.total)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\r{self.description}: [{bar}] {percent:.1f}% "
              f"({self.current}/{self.total}) ETA: {eta_str}", end="", flush=True)
        
        if self.current >= self.total:
            print()  # Nova linha ao completar


if __name__ == "__main__":
    """Testes das funções utilitárias"""
    print_header("TESTES DE FUNÇÕES UTILITÁRIAS")
    
    # Teste formatação
    print_section("Formatação")
    print(f"Bytes: {format_bytes(1234567890)}")
    print(f"Duração: {format_duration(3665.5)}")
    print(f"Número: {format_number(1234567.89)}")
    
    # Teste estatísticas
    print_section("Estatísticas")
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    stats = calculate_statistics(values)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Teste progress tracker
    print_section("Progress Tracker")
    tracker = ProgressTracker(100, "Teste")
    for i in range(100):
        time.sleep(0.01)
        tracker.update()
    
    print_section("Testes concluídos!")

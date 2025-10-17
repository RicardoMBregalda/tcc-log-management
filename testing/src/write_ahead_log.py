#!/usr/bin/env python3
"""
Write-Ahead Log (WAL) Implementation
=====================================

Garante 0% de perda de dados escrevendo logs em arquivo ANTES de tentar MongoDB.

Conceito:
1. Log chega → Escreve no WAL (disco local) PRIMEIRO
2. Retorna sucesso para cliente (log garantido)
3. Background thread tenta inserir no MongoDB
4. Se sucesso → Remove do WAL
5. Se falha → Mantém no WAL para tentar depois

Vantagens:
- ✅ 0% de perda (logs persistidos em disco)
- ✅ Sobrevive a crash da API
- ✅ Sobrevive a downtime do MongoDB
- ✅ Recovery automático após reinicialização
"""

import json
import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import fcntl  # File locking


class WriteAheadLog:
    """
    Implementação de Write-Ahead Log para garantir durabilidade de logs.
    
    Arquitetura:
    - WAL ativo: logs_pending.wal (novos logs vão aqui)
    - WAL processado: logs_processed.wal (logs confirmados no MongoDB)
    - Thread de background: Processa WAL continuamente
    """
    
    def __init__(self, wal_dir: str = '/tmp/wal', check_interval: int = 5):
        """
        Inicializa WAL.
        
        Args:
            wal_dir: Diretório para armazenar WAL files
            check_interval: Intervalo (segundos) para processar WAL
        """
        self.wal_dir = Path(wal_dir)
        self.wal_dir.mkdir(parents=True, exist_ok=True)
        
        self.pending_file = self.wal_dir / 'logs_pending.wal'
        self.processed_file = self.wal_dir / 'logs_processed.wal'
        self.check_interval = check_interval
        
        # Lock para escrita concorrente
        self.write_lock = threading.Lock()
        
        # Flags
        self.running = False
        self.processor_thread = None
        
        # Estatísticas
        self.stats = {
            'total_written': 0,
            'total_processed': 0,
            'pending_count': 0,
            'last_error': None
        }
        
        # Recuperar logs pendentes ao iniciar
        self._recover_pending_logs()
    
    def _recover_pending_logs(self):
        """Conta logs pendentes ao iniciar"""
        if self.pending_file.exists():
            with open(self.pending_file, 'r') as f:
                self.stats['pending_count'] = sum(1 for _ in f)
            print(f"[WAL] Recuperados {self.stats['pending_count']} logs pendentes")
    
    def write(self, log_data: Dict) -> bool:
        """
        Escreve log no WAL.
        
        Esta operação DEVE ser rápida (< 1ms) e confiável.
        
        Args:
            log_data: Dados do log (dict)
            
        Returns:
            True se escrito com sucesso, False caso contrário
        """
        try:
            with self.write_lock:
                # Adicionar timestamp de entrada no WAL
                wal_entry = {
                    'wal_timestamp': datetime.utcnow().isoformat(),
                    'log_data': log_data
                }
                
                # Escrever em append mode (atomic)
                with open(self.pending_file, 'a') as f:
                    # Lock exclusivo para garantir atomicidade
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    f.write(json.dumps(wal_entry) + '\n')
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
                self.stats['total_written'] += 1
                self.stats['pending_count'] += 1
                
                return True
                
        except Exception as e:
            print(f"[WAL] ❌ Erro ao escrever: {e}")
            self.stats['last_error'] = str(e)
            return False
    
    def start_processor(self, insert_callback):
        """
        Inicia thread de processamento do WAL.
        
        Args:
            insert_callback: Função (log_data) -> bool para inserir no MongoDB
        """
        if self.running:
            print("[WAL] Processor já está rodando")
            return
        
        self.running = True
        self.insert_callback = insert_callback
        
        self.processor_thread = threading.Thread(
            target=self._process_wal_loop,
            daemon=True,
            name='WAL-Processor'
        )
        self.processor_thread.start()
        
        print(f"[WAL] ✅ Processor iniciado (intervalo: {self.check_interval}s)")
    
    def stop_processor(self):
        """Para o processor thread"""
        self.running = False
        if self.processor_thread:
            self.processor_thread.join(timeout=10)
        print("[WAL] Processor parado")
    
    def _process_wal_loop(self):
        """Loop principal do processor"""
        while self.running:
            try:
                self._process_pending_logs()
            except Exception as e:
                print(f"[WAL] ⚠️  Erro no processor loop: {e}")
                self.stats['last_error'] = str(e)
            
            time.sleep(self.check_interval)
    
    def _process_pending_logs(self):
        """
        Processa logs pendentes no WAL.
        
        Estratégia:
        1. Lê todos os logs pendentes
        2. Tenta inserir cada um no MongoDB
        3. Se sucesso → Move para processed
        4. Se falha → Deixa no pending para próxima tentativa
        """
        if not self.pending_file.exists():
            return
        
        temp_file = self.wal_dir / 'logs_temp.wal'
        failed_logs = []
        processed_count = 0
        
        try:
            # Ler logs pendentes
            with open(self.pending_file, 'r') as f:
                pending_logs = [line.strip() for line in f if line.strip()]
            
            if not pending_logs:
                return
            
            print(f"[WAL] Processando {len(pending_logs)} logs pendentes...")
            
            # Processar cada log
            for line in pending_logs:
                try:
                    wal_entry = json.loads(line)
                    log_data = wal_entry['log_data']
                    
                    # Tentar inserir no MongoDB
                    success = self.insert_callback(log_data)
                    
                    if success:
                        # Sucesso → Marcar como processado
                        processed_count += 1
                        self.stats['total_processed'] += 1
                        
                        # Registrar no arquivo de processados
                        with open(self.processed_file, 'a') as pf:
                            processed_entry = {
                                'wal_timestamp': wal_entry['wal_timestamp'],
                                'processed_timestamp': datetime.utcnow().isoformat(),
                                'log_id': log_data.get('id', 'unknown')
                            }
                            pf.write(json.dumps(processed_entry) + '\n')
                    else:
                        # Falha → Manter no pending
                        failed_logs.append(line)
                        
                except json.JSONDecodeError:
                    print(f"[WAL] ⚠️  Linha inválida no WAL, ignorando: {line[:100]}")
                    continue
                except Exception as e:
                    print(f"[WAL] ⚠️  Erro ao processar log: {e}")
                    failed_logs.append(line)
            
            # Atualizar arquivo pending com apenas os que falharam
            with self.write_lock:
                if failed_logs:
                    # Re-escrever pending com logs que falharam
                    with open(temp_file, 'w') as f:
                        f.write('\n'.join(failed_logs) + '\n')
                    temp_file.replace(self.pending_file)
                    self.stats['pending_count'] = len(failed_logs)
                else:
                    # Todos processados → Remover arquivo pending
                    if self.pending_file.exists():
                        self.pending_file.unlink()
                    self.stats['pending_count'] = 0
            
            if processed_count > 0:
                print(f"[WAL] ✅ {processed_count} logs processados com sucesso")
                if failed_logs:
                    print(f"[WAL] ⚠️  {len(failed_logs)} logs ainda pendentes")
            
        except Exception as e:
            print(f"[WAL] ❌ Erro ao processar WAL: {e}")
            self.stats['last_error'] = str(e)
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do WAL"""
        return {
            **self.stats,
            'pending_file_size': self.pending_file.stat().st_size if self.pending_file.exists() else 0,
            'processed_file_size': self.processed_file.stat().st_size if self.processed_file.exists() else 0,
            'processor_running': self.running
        }
    
    def force_process_now(self):
        """Força processamento imediato (para testes)"""
        print("[WAL] Forçando processamento imediato...")
        self._process_pending_logs()
    
    def clear_processed_history(self, older_than_days: int = 7):
        """
        Limpa logs processados antigos.
        
        Args:
            older_than_days: Remove logs processados há mais de N dias
        """
        if not self.processed_file.exists():
            return
        
        cutoff_time = datetime.utcnow().timestamp() - (older_than_days * 86400)
        temp_file = self.wal_dir / 'processed_temp.wal'
        kept_count = 0
        
        try:
            with open(self.processed_file, 'r') as f, open(temp_file, 'w') as tf:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        processed_ts = datetime.fromisoformat(entry['processed_timestamp'])
                        
                        if processed_ts.timestamp() >= cutoff_time:
                            tf.write(line)
                            kept_count += 1
                    except:
                        continue
            
            temp_file.replace(self.processed_file)
            print(f"[WAL] Histórico limpo. {kept_count} registros mantidos.")
            
        except Exception as e:
            print(f"[WAL] Erro ao limpar histórico: {e}")


# ==================== EXEMPLO DE USO ====================

if __name__ == '__main__':
    """
    Demonstração de uso do WAL
    """
    
    # Simular função de inserção no MongoDB
    mongodb_available = True
    
    def mock_mongo_insert(log_data: Dict) -> bool:
        """Simula inserção no MongoDB"""
        if not mongodb_available:
            print(f"  ❌ MongoDB indisponível, log {log_data['id']} NÃO inserido")
            return False
        
        # Simular sucesso
        print(f"  ✅ Log {log_data['id']} inserido no MongoDB")
        return True
    
    # Criar WAL
    print("=" * 70)
    print("DEMONSTRAÇÃO: Write-Ahead Log (WAL)")
    print("=" * 70)
    print()
    
    wal = WriteAheadLog(wal_dir='/tmp/demo_wal', check_interval=2)
    wal.start_processor(mock_mongo_insert)
    
    # Cenário 1: MongoDB disponível
    print("\n📝 CENÁRIO 1: MongoDB Disponível")
    print("-" * 70)
    
    for i in range(5):
        log_data = {
            'id': f'log-{i}',
            'message': f'Test log {i}',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        success = wal.write(log_data)
        print(f"{'✅' if success else '❌'} Log {i} escrito no WAL")
    
    print("\n⏳ Aguardando processamento (3s)...")
    time.sleep(3)
    
    print("\n📊 Estatísticas:")
    stats = wal.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Cenário 2: MongoDB indisponível
    print("\n\n💥 CENÁRIO 2: MongoDB Falha")
    print("-" * 70)
    
    mongodb_available = False
    
    for i in range(5, 10):
        log_data = {
            'id': f'log-{i}',
            'message': f'Test log {i}',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        success = wal.write(log_data)
        print(f"{'✅' if success else '❌'} Log {i} escrito no WAL (MongoDB indisponível)")
    
    print("\n⏳ Tentando processar (vai falhar)...")
    time.sleep(3)
    
    print("\n📊 Estatísticas:")
    stats = wal.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Cenário 3: MongoDB volta
    print("\n\n🔄 CENÁRIO 3: MongoDB Recupera")
    print("-" * 70)
    
    mongodb_available = True
    
    print("⏳ Aguardando processamento automático...")
    time.sleep(3)
    
    print("\n📊 Estatísticas Finais:")
    stats = wal.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Parar processor
    print("\n\n🛑 Parando WAL processor...")
    wal.stop_processor()
    
    print("\n✅ Demonstração concluída!")
    print(f"\nArquivos WAL em: {wal.wal_dir}")
    print(f"  - Pendentes: {wal.pending_file}")
    print(f"  - Processados: {wal.processed_file}")

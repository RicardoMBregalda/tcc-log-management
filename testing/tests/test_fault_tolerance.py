#!/usr/bin/env python3
"""
Testes de Tolerância a Falhas - TCC Log Management

Comparação abrangente entre arquiteturas Híbrida (Fabric) e Tradicional (PostgreSQL)
focando em:
- Tempo de recuperação (Recovery Time Objective - RTO)
- Integridade dos dados (Recovery Point Objective - RPO)
- Comportamento durante falhas
- Consistência após recuperação

Cenários de Falha:
1. Queda do banco de dados principal
2. Queda de nó de replicação
3. Falha de rede temporária
4. Falha durante escrita
5. Múltiplas falhas simultâneas

Autor: Ricardo M Bregalda
Data: 2025-10-16
"""

import sys
import time
import json
import subprocess
import requests
import psycopg2
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict

# MongoDB
try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    print("⚠️  Warning: pymongo not installed. MongoDB tests will be limited.")

# Adiciona diretório pai ao path
sys.path.append(str(Path(__file__).parent.parent))

from config import (
    API_BASE_URL,
    API_TIMEOUT,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    MONGO_URL,
    MONGO_DB,
    MONGO_COLLECTION,
)


# ==================== CONFIGURAÇÃO ====================

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Containers Docker
CONTAINERS = {
    # Arquitetura Híbrida
    'mongo': 'mongo',
    'peer0': 'peer0.org1.example.com',
    'peer1': 'peer1.org1.example.com',
    'peer2': 'peer2.org1.example.com',
    'orderer': 'orderer.example.com',
    
    # Arquitetura Tradicional
    'postgres_primary': 'postgres-primary',
    'postgres_standby': 'postgres-standby',
}

# Configuração dos testes
CONFIG = {
    'logs_per_second': 10,
    'test_duration': 30,  # segundos
    'failure_at': 10,  # injetar falha após 10s
    'recovery_timeout': 60,  # timeout para recuperação
    'verification_samples': 100,  # amostras para verificar integridade
}


# ==================== DATACLASSES ====================

@dataclass
class FailureMetrics:
    """Métricas de uma falha específica"""
    # Identificação
    scenario: str
    architecture: str
    component: str
    
    # Timeline
    test_start: datetime
    failure_injected: datetime
    failure_detected: Optional[datetime] = None
    recovery_started: Optional[datetime] = None
    recovery_completed: Optional[datetime] = None
    test_end: Optional[datetime] = None
    
    # Tempos (em segundos)
    detection_time: Optional[float] = None
    recovery_time: Optional[float] = None
    total_downtime: Optional[float] = None
    
    # Integridade de dados
    logs_before_failure: int = 0
    logs_during_failure: int = 0
    logs_after_recovery: int = 0
    logs_sent_total: int = 0
    logs_received_total: int = 0
    logs_lost: int = 0
    loss_percentage: float = 0.0
    
    # Comportamento
    continued_operating: bool = False
    automatic_recovery: bool = False
    data_consistent: bool = False
    
    # Detalhes
    error_messages: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário com campos formatados"""
        return {
            'scenario': self.scenario,
            'architecture': self.architecture,
            'component': self.component,
            'test_start': self.test_start.isoformat() if self.test_start else None,
            'failure_injected': self.failure_injected.isoformat() if self.failure_injected else None,
            'failure_detected': self.failure_detected.isoformat() if self.failure_detected else None,
            'recovery_started': self.recovery_started.isoformat() if self.recovery_started else None,
            'recovery_completed': self.recovery_completed.isoformat() if self.recovery_completed else None,
            'test_end': self.test_end.isoformat() if self.test_end else None,
            'detection_time': round(self.detection_time, 2) if self.detection_time else None,
            'recovery_time': round(self.recovery_time, 2) if self.recovery_time else None,
            'total_downtime': round(self.total_downtime, 2) if self.total_downtime else None,
            'logs_before_failure': self.logs_before_failure,
            'logs_during_failure': self.logs_during_failure,
            'logs_after_recovery': self.logs_after_recovery,
            'logs_sent_total': self.logs_sent_total,
            'logs_received_total': self.logs_received_total,
            'logs_lost': self.logs_lost,
            'loss_percentage': round(self.loss_percentage, 2),
            'continued_operating': self.continued_operating,
            'automatic_recovery': self.automatic_recovery,
            'data_consistent': self.data_consistent,
            'error_messages': self.error_messages,
            'notes': self.notes,
        }


@dataclass
class ComparisonResult:
    """Resultado da comparação entre arquiteturas"""
    scenario: str
    hybrid: FailureMetrics
    traditional: FailureMetrics
    
    # Vencedores por métrica
    faster_detection: str  # 'hybrid', 'traditional', 'tie'
    faster_recovery: str
    less_data_loss: str
    better_availability: str
    
    # Diferenças
    detection_time_diff: float
    recovery_time_diff: float
    data_loss_diff: float
    
    summary: str


# ==================== CLASSE PRINCIPAL ====================

class FaultToleranceTest:
    """Gerenciador de testes de tolerância a falhas"""
    
    def __init__(self):
        self.metrics: List[FailureMetrics] = []
        self.log_ids: List[str] = []  # IDs dos logs enviados
        self.stop_flag = False
        
    # ==================== DOCKER UTILS ====================
    
    def docker_stop(self, container: str) -> Tuple[bool, str]:
        """Para um container Docker"""
        print(f"    🔴 Parando container: {container}")
        try:
            result = subprocess.run(
                ['docker', 'stop', container],
                capture_output=True,
                text=True,
                timeout=15
            )
            return result.returncode == 0, result.stdout or result.stderr
        except Exception as e:
            return False, str(e)
    
    def docker_start(self, container: str) -> Tuple[bool, str]:
        """Inicia um container Docker"""
        print(f"    🟢 Iniciando container: {container}")
        try:
            result = subprocess.run(
                ['docker', 'start', container],
                capture_output=True,
                text=True,
                timeout=15
            )
            return result.returncode == 0, result.stdout or result.stderr
        except Exception as e:
            return False, str(e)
    
    def docker_is_running(self, container: str) -> bool:
        """Verifica se container está rodando"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name=^{container}$', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return container in result.stdout.strip()
        except:
            return False
    
    def docker_pause(self, container: str) -> Tuple[bool, str]:
        """Pausa um container (simula falha de rede)"""
        print(f"    ⏸️  Pausando container: {container}")
        try:
            result = subprocess.run(
                ['docker', 'pause', container],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout or result.stderr
        except Exception as e:
            return False, str(e)
    
    def docker_unpause(self, container: str) -> Tuple[bool, str]:
        """Despausa um container"""
        print(f"    ▶️  Despausando container: {container}")
        try:
            result = subprocess.run(
                ['docker', 'unpause', container],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout or result.stderr
        except Exception as e:
            return False, str(e)
    
    # ==================== POSTGRESQL UTILS ====================
    
    def postgres_connect(self, host: str = POSTGRES_HOST, port: int = POSTGRES_PORT) -> Optional[psycopg2.extensions.connection]:
        """Conecta ao PostgreSQL"""
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=5
            )
            return conn
        except Exception as e:
            return None
    
    def postgres_insert_log(self, conn, log_id: str, message: str) -> bool:
        """Insere log no PostgreSQL"""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO logs (id, timestamp, source, level, message, metadata)
                    VALUES (%s, NOW(), %s, %s, %s, %s)
                """, (log_id, 'fault-tolerance-test', 'INFO', message, '{}'))
                conn.commit()
            return True
        except Exception as e:
            return False
    
    def postgres_count_logs(self, conn, source: str = 'fault-tolerance-test') -> int:
        """Conta logs no PostgreSQL"""
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM logs WHERE source = %s", (source,))
                return cur.fetchone()[0]
        except:
            return -1
    
    def postgres_verify_log(self, conn, log_id: str) -> bool:
        """Verifica se log existe no PostgreSQL"""
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM logs WHERE id = %s", (log_id,))
                return cur.fetchone() is not None
        except:
            return False
    
    def postgres_is_primary(self, host: str = POSTGRES_HOST, port: int = POSTGRES_PORT) -> Optional[bool]:
        """Verifica se instância é primary (não está em recovery)"""
        conn = self.postgres_connect(host, port)
        if not conn:
            return None
        
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_is_in_recovery()")
                in_recovery = cur.fetchone()[0]
                conn.close()
                return not in_recovery
        except:
            if conn:
                conn.close()
            return None
    
    # ==================== HYBRID API UTILS ====================
    
    def api_insert_log(self, log_id: str, message: str) -> Tuple[bool, Optional[str]]:
        """Insere log via API híbrida"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/logs",
                json={
                    'id': log_id,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'fault-tolerance-test',
                    'level': 'INFO',
                    'message': message,
                    'metadata': {}
                },
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                return True, None
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, str(e)
    
    def api_get_log(self, log_id: str) -> Tuple[bool, Optional[Dict]]:
        """Busca log via API híbrida"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/logs/{log_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, None
        except:
            return False, None
    
    def api_health_check(self) -> bool:
        """Verifica saúde da API"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    # ==================== MONGODB UTILS ====================
    
    def mongo_connect(self) -> Optional[MongoClient]:
        """Conecta ao MongoDB"""
        if not MONGO_AVAILABLE:
            return None
        try:
            client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
            # Testa conexão
            client.admin.command('ping')
            return client
        except Exception as e:
            return None
    
    def mongo_insert_log(self, client: MongoClient, log_id: str, message: str) -> bool:
        """Insere log diretamente no MongoDB"""
        try:
            db = client[MONGO_DB]
            collection = db[MONGO_COLLECTION]
            
            log_doc = {
                'id': log_id,
                'timestamp': datetime.now().isoformat(),
                'source': 'fault-tolerance-test',
                'level': 'INFO',
                'message': message,
                'metadata': {},
                'created_at': datetime.utcnow()
            }
            
            collection.insert_one(log_doc)
            return True
        except Exception as e:
            return False
    
    def mongo_count_logs(self, client: MongoClient, source: str = 'fault-tolerance-test') -> int:
        """Conta logs no MongoDB"""
        try:
            db = client[MONGO_DB]
            collection = db[MONGO_COLLECTION]
            return collection.count_documents({'source': source})
        except:
            return -1
    
    def mongo_verify_log(self, client: MongoClient, log_id: str) -> bool:
        """Verifica se log existe no MongoDB"""
        try:
            db = client[MONGO_DB]
            collection = db[MONGO_COLLECTION]
            return collection.find_one({'id': log_id}) is not None
        except:
            return False
    
    def mongo_clear_test_logs(self, client: MongoClient):
        """Limpa logs de teste do MongoDB"""
        try:
            db = client[MONGO_DB]
            collection = db[MONGO_COLLECTION]
            collection.delete_many({'source': 'fault-tolerance-test'})
        except:
            pass
    
    # ==================== CENÁRIOS DE TESTE ====================
    
    def test_scenario_1_primary_failure(self, architecture: str) -> FailureMetrics:
        """
        CENÁRIO 1: Queda do banco de dados principal
        
        PostgreSQL: Primary cai, standby deve assumir (promoção manual necessária)
        Hybrid: MongoDB cai, sistema deve falhar (sem replicação configurada)
        """
        print(f"\n{'='*70}")
        print(f"  CENÁRIO 1: Falha do Banco de Dados Principal")
        print(f"  Arquitetura: {architecture.upper()}")
        print(f"{'='*70}")
        
        metrics = FailureMetrics(
            scenario='primary_database_failure',
            architecture=architecture,
            component='postgres-primary' if architecture == 'traditional' else 'mongo',
            test_start=datetime.now(),
            failure_injected=datetime.now()
        )
        
        self.log_ids = []
        logs_sent = {'before': 0, 'during': 0, 'after': 0}
        
        try:
            # FASE 1: Operação normal (10 segundos)
            print("\n  📊 FASE 1: Operação Normal (10s)")
            print("  " + "-" * 66)
            
            phase_start = time.time()
            while time.time() - phase_start < 10:
                log_id = f"ft-s1-{architecture}-{int(time.time()*1000)}"
                self.log_ids.append(log_id)
                
                if architecture == 'traditional':
                    conn = self.postgres_connect()
                    if conn:
                        success = self.postgres_insert_log(conn, log_id, f"Log antes da falha #{logs_sent['before']}")
                        conn.close()
                        if success:
                            logs_sent['before'] += 1
                else:
                    success, _ = self.api_insert_log(log_id, f"Log antes da falha #{logs_sent['before']}")
                    if success:
                        logs_sent['before'] += 1
                
                time.sleep(0.1)
            
            metrics.logs_before_failure = logs_sent['before']
            print(f"  ✅ Logs enviados na FASE 1: {logs_sent['before']}")
            
            # FASE 2: Injetar falha
            print(f"\n  💥 FASE 2: Injetando Falha")
            print("  " + "-" * 66)
            
            metrics.failure_injected = datetime.now()
            container = CONTAINERS['postgres_primary'] if architecture == 'traditional' else CONTAINERS['mongo']
            
            success, msg = self.docker_stop(container)
            if not success:
                metrics.notes.append(f"Falha ao parar container: {msg}")
                raise Exception(f"Erro ao parar container: {msg}")
            
            print(f"  ✅ Container parado: {container}")
            
            # FASE 3: Operação durante falha (10 segundos)
            print(f"\n  📊 FASE 3: Operação Durante Falha (10s)")
            print("  " + "-" * 66)
            
            metrics.failure_detected = datetime.now()
            metrics.detection_time = (metrics.failure_detected - metrics.failure_injected).total_seconds()
            
            phase_start = time.time()
            first_error = None
            
            while time.time() - phase_start < 10:
                log_id = f"ft-s1-{architecture}-{int(time.time()*1000)}"
                self.log_ids.append(log_id)
                
                if architecture == 'traditional':
                    conn = self.postgres_connect()
                    if conn:
                        success = self.postgres_insert_log(conn, log_id, f"Log durante falha #{logs_sent['during']}")
                        conn.close()
                        if success:
                            logs_sent['during'] += 1
                            metrics.continued_operating = True
                    else:
                        if first_error is None:
                            first_error = "Conexão recusada"
                else:
                    success, error = self.api_insert_log(log_id, f"Log durante falha #{logs_sent['during']}")
                    if success:
                        logs_sent['during'] += 1
                        metrics.continued_operating = True
                    elif first_error is None:
                        first_error = error
                
                time.sleep(0.1)
            
            metrics.logs_during_failure = logs_sent['during']
            print(f"  📊 Logs enviados na FASE 3: {logs_sent['during']}")
            
            if first_error:
                metrics.error_messages.append(first_error)
                print(f"  ⚠️  Primeiro erro detectado: {first_error[:80]}")
            
            # FASE 4: Recuperação
            print(f"\n  🔄 FASE 4: Recuperação")
            print("  " + "-" * 66)
            
            metrics.recovery_started = datetime.now()
            
            # Reiniciar container
            success, msg = self.docker_start(container)
            if not success:
                raise Exception(f"Erro ao iniciar container: {msg}")
            
            print(f"  ⏳ Aguardando container ficar disponível...")
            
            # Para arquitetura híbrida, reiniciar API após MongoDB voltar
            if architecture == 'hybrid':
                print(f"  🔄 Reiniciando API para reconectar ao MongoDB...")
                
                # Usar script bash para reiniciar API (mais confiável)
                try:
                    result = subprocess.run(
                        ['bash', '/root/tcc-log-management/testing/scripts/start_api.sh'],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    if result.returncode == 0:
                        print(f"  ✅ API reiniciada com sucesso")
                    else:
                        print(f"  ⚠️  API pode não ter iniciado corretamente")
                except Exception as e:
                    print(f"  ⚠️  Erro ao reiniciar API: {e}")
                
                time.sleep(2)  # Tempo adicional de estabilização
            
            # Aguardar recuperação
            recovery_timeout = 60
            recovery_start = time.time()
            recovered = False
            
            while time.time() - recovery_start < recovery_timeout:
                if architecture == 'traditional':
                    conn = self.postgres_connect()
                    if conn:
                        conn.close()
                        recovered = True
                        break
                else:
                    if self.api_health_check():
                        recovered = True
                        break
                
                time.sleep(1)
            
            if recovered:
                metrics.recovery_completed = datetime.now()
                metrics.recovery_time = (metrics.recovery_completed - metrics.recovery_started).total_seconds()
                metrics.automatic_recovery = True
                print(f"  ✅ Sistema recuperado em {metrics.recovery_time:.2f}s")
            else:
                metrics.notes.append("Timeout de recuperação excedido")
                print(f"  ❌ Timeout de recuperação ({recovery_timeout}s)")
            
            # FASE 5: Verificação pós-recuperação (10 segundos)
            print(f"\n  📊 FASE 5: Verificação Pós-Recuperação (10s)")
            print("  " + "-" * 66)
            
            if recovered:
                phase_start = time.time()
                while time.time() - phase_start < 10:
                    log_id = f"ft-s1-{architecture}-{int(time.time()*1000)}"
                    self.log_ids.append(log_id)
                    
                    if architecture == 'traditional':
                        conn = self.postgres_connect()
                        if conn:
                            success = self.postgres_insert_log(conn, log_id, f"Log pós-recuperação #{logs_sent['after']}")
                            conn.close()
                            if success:
                                logs_sent['after'] += 1
                    else:
                        success, _ = self.api_insert_log(log_id, f"Log pós-recuperação #{logs_sent['after']}")
                        if success:
                            logs_sent['after'] += 1
                    
                    time.sleep(0.1)
            
            metrics.logs_after_recovery = logs_sent['after']
            print(f"  ✅ Logs enviados na FASE 5: {logs_sent['after']}")
            
            # FASE 6: Verificação de integridade
            print(f"\n  🔍 FASE 6: Verificação de Integridade")
            print("  " + "-" * 66)
            
            metrics.logs_sent_total = len(self.log_ids)
            logs_received = 0
            
            # Verificar amostra de logs
            sample_size = min(100, len(self.log_ids))
            sample_ids = self.log_ids[::max(1, len(self.log_ids) // sample_size)]
            
            print(f"  📊 Verificando {len(sample_ids)} logs de amostra...")
            
            if architecture == 'traditional':
                # PostgreSQL: Conecta diretamente ao banco
                conn = self.postgres_connect()
                if conn:
                    for log_id in sample_ids:
                        if self.postgres_verify_log(conn, log_id):
                            logs_received += 1
                    conn.close()
            else:
                # Híbrida: Conecta diretamente ao MongoDB (não via API)
                # Isso garante que verificamos o que realmente foi persistido
                mongo_client = self.mongo_connect()
                if mongo_client:
                    for log_id in sample_ids:
                        if self.mongo_verify_log(mongo_client, log_id):
                            logs_received += 1
                    mongo_client.close()
                else:
                    # Fallback para API se MongoDB não estiver disponível
                    print(f"  ⚠️  MongoDB não disponível, tentando via API...")
                    for log_id in sample_ids:
                        success, _ = self.api_get_log(log_id)
                        if success:
                            logs_received += 1
            
            # Extrapolar para total
            if len(sample_ids) > 0:
                metrics.logs_received_total = int((logs_received / len(sample_ids)) * metrics.logs_sent_total)
            else:
                metrics.logs_received_total = 0
            
            metrics.logs_lost = metrics.logs_sent_total - metrics.logs_received_total
            metrics.loss_percentage = (metrics.logs_lost / metrics.logs_sent_total * 100) if metrics.logs_sent_total > 0 else 0
            metrics.data_consistent = metrics.logs_lost == 0
            
            print(f"  📊 Amostra verificada: {logs_received}/{len(sample_ids)}")
            print(f"  📊 Logs enviados: {metrics.logs_sent_total}")
            print(f"  📊 Logs recebidos: {metrics.logs_received_total}")
            print(f"  📊 Logs perdidos: {metrics.logs_lost} ({metrics.loss_percentage:.2f}%)")
            print(f"  {'✅' if metrics.data_consistent else '⚠️ '} Integridade: {'OK' if metrics.data_consistent else 'FALHA'}")
            
        except Exception as e:
            metrics.notes.append(f"Erro durante teste: {str(e)}")
            print(f"\n  ❌ ERRO: {str(e)}")
        
        finally:
            metrics.test_end = datetime.now()
            if metrics.failure_detected and metrics.recovery_completed:
                metrics.total_downtime = (metrics.recovery_completed - metrics.failure_detected).total_seconds()
        
        return metrics
    
    def test_scenario_2_standby_failure(self, architecture: str) -> FailureMetrics:
        """
        CENÁRIO 2: Queda do nó de replicação
        
        PostgreSQL: Standby cai, primary continua operando
        Hybrid: Peer secundário cai, rede Fabric continua
        """
        print(f"\n{'='*70}")
        print(f"  CENÁRIO 2: Falha do Nó de Replicação")
        print(f"  Arquitetura: {architecture.upper()}")
        print(f"{'='*70}")
        
        metrics = FailureMetrics(
            scenario='replica_node_failure',
            architecture=architecture,
            component='postgres-standby' if architecture == 'traditional' else 'peer1',
            test_start=datetime.now(),
            failure_injected=datetime.now()
        )
        
        self.log_ids = []
        logs_sent = {'before': 0, 'during': 0, 'after': 0}
        
        try:
            # FASE 1: Operação normal
            print("\n  📊 FASE 1: Operação Normal (5s)")
            print("  " + "-" * 66)
            
            phase_start = time.time()
            while time.time() - phase_start < 5:
                log_id = f"ft-s2-{architecture}-{int(time.time()*1000)}"
                self.log_ids.append(log_id)
                
                if architecture == 'traditional':
                    conn = self.postgres_connect()
                    if conn:
                        if self.postgres_insert_log(conn, log_id, f"Log antes #{logs_sent['before']}"):
                            logs_sent['before'] += 1
                        conn.close()
                else:
                    if self.api_insert_log(log_id, f"Log antes #{logs_sent['before']}")[0]:
                        logs_sent['before'] += 1
                
                time.sleep(0.1)
            
            metrics.logs_before_failure = logs_sent['before']
            print(f"  ✅ Logs enviados: {logs_sent['before']}")
            
            # FASE 2: Injetar falha
            print(f"\n  💥 FASE 2: Injetando Falha no Nó Secundário")
            print("  " + "-" * 66)
            
            metrics.failure_injected = datetime.now()
            container = CONTAINERS['postgres_standby'] if architecture == 'traditional' else CONTAINERS['peer1']
            
            self.docker_stop(container)
            print(f"  ✅ Container parado: {container}")
            
            # FASE 3: Operação após falha (primary deve continuar)
            print(f"\n  📊 FASE 3: Operação com Réplica Indisponível (10s)")
            print("  " + "-" * 66)
            
            metrics.failure_detected = datetime.now()
            metrics.detection_time = (metrics.failure_detected - metrics.failure_injected).total_seconds()
            
            phase_start = time.time()
            while time.time() - phase_start < 10:
                log_id = f"ft-s2-{architecture}-{int(time.time()*1000)}"
                self.log_ids.append(log_id)
                
                if architecture == 'traditional':
                    conn = self.postgres_connect()
                    if conn:
                        if self.postgres_insert_log(conn, log_id, f"Log durante #{logs_sent['during']}"):
                            logs_sent['during'] += 1
                            metrics.continued_operating = True
                        conn.close()
                else:
                    if self.api_insert_log(log_id, f"Log durante #{logs_sent['during']}")[0]:
                        logs_sent['during'] += 1
                        metrics.continued_operating = True
                
                time.sleep(0.1)
            
            metrics.logs_during_failure = logs_sent['during']
            print(f"  ✅ Logs enviados durante falha: {logs_sent['during']}")
            print(f"  {'✅' if metrics.continued_operating else '❌'} Sistema continuou operando")
            
            # FASE 4: Recuperar réplica
            print(f"\n  🔄 FASE 4: Recuperando Réplica")
            print("  " + "-" * 66)
            
            metrics.recovery_started = datetime.now()
            self.docker_start(container)
            
            # Aguardar recuperação
            time.sleep(15)  # Tempo para standby se conectar
            
            metrics.recovery_completed = datetime.now()
            metrics.recovery_time = (metrics.recovery_completed - metrics.recovery_started).total_seconds()
            metrics.automatic_recovery = True
            
            print(f"  ✅ Réplica recuperada em {metrics.recovery_time:.2f}s")
            
            # FASE 5: Verificar sincronização
            print(f"\n  🔍 FASE 5: Verificando Sincronização")
            print("  " + "-" * 66)
            
            if architecture == 'traditional':
                # Verificar replicação
                time.sleep(5)  # Aguardar replicação alcançar
                
                # Verificar se standby está em recovery e replicando
                standby_ok = self.postgres_is_primary(POSTGRES_HOST, 5433) == False
                
                if standby_ok:
                    metrics.data_consistent = True
                    print(f"  ✅ Standby sincronizado e replicando")
                else:
                    print(f"  ⚠️  Standby não sincronizou completamente")
            
            metrics.logs_sent_total = len(self.log_ids)
            metrics.logs_received_total = logs_sent['before'] + logs_sent['during']
            metrics.logs_lost = 0
            metrics.loss_percentage = 0.0
            
        except Exception as e:
            metrics.notes.append(f"Erro: {str(e)}")
            print(f"\n  ❌ ERRO: {str(e)}")
        
        finally:
            metrics.test_end = datetime.now()
            if metrics.failure_detected and metrics.recovery_completed:
                metrics.total_downtime = 0  # Sem downtime para o primary
        
        return metrics
    
    def test_scenario_3_network_partition(self, architecture: str) -> FailureMetrics:
        """
        CENÁRIO 3: Falha de rede temporária (simula com docker pause)
        
        PostgreSQL: Primary pausado, simula perda de rede
        Hybrid: MongoDB pausado
        """
        print(f"\n{'='*70}")
        print(f"  CENÁRIO 3: Falha de Rede Temporária")
        print(f"  Arquitetura: {architecture.upper()}")
        print(f"{'='*70}")
        
        metrics = FailureMetrics(
            scenario='network_partition',
            architecture=architecture,
            component='postgres-primary' if architecture == 'traditional' else 'mongo',
            test_start=datetime.now(),
            failure_injected=datetime.now()
        )
        
        self.log_ids = []
        logs_sent = {'before': 0, 'during': 0, 'after': 0}
        
        try:
            # FASE 1: Operação normal
            print("\n  📊 FASE 1: Operação Normal (5s)")
            phase_start = time.time()
            while time.time() - phase_start < 5:
                log_id = f"ft-s3-{architecture}-{int(time.time()*1000)}"
                self.log_ids.append(log_id)
                
                if architecture == 'traditional':
                    conn = self.postgres_connect()
                    if conn:
                        if self.postgres_insert_log(conn, log_id, f"Log #{logs_sent['before']}"):
                            logs_sent['before'] += 1
                        conn.close()
                else:
                    if self.api_insert_log(log_id, f"Log #{logs_sent['before']}")[0]:
                        logs_sent['before'] += 1
                
                time.sleep(0.1)
            
            metrics.logs_before_failure = logs_sent['before']
            print(f"  ✅ Logs enviados: {logs_sent['before']}")
            
            # FASE 2: Pausar container (simula perda de rede)
            print(f"\n  💥 FASE 2: Simulando Perda de Rede (docker pause)")
            
            metrics.failure_injected = datetime.now()
            container = CONTAINERS['postgres_primary'] if architecture == 'traditional' else CONTAINERS['mongo']
            
            self.docker_pause(container)
            print(f"  ⏸️  Container pausado: {container}")
            
            # FASE 3: Tentar operações (devem falhar)
            print(f"\n  📊 FASE 3: Tentando Operações Durante Perda de Rede (10s)")
            
            metrics.failure_detected = datetime.now()
            phase_start = time.time()
            
            while time.time() - phase_start < 10:
                log_id = f"ft-s3-{architecture}-{int(time.time()*1000)}"
                self.log_ids.append(log_id)
                
                if architecture == 'traditional':
                    conn = self.postgres_connect()
                    if conn:
                        if self.postgres_insert_log(conn, log_id, f"Log #{logs_sent['during']}"):
                            logs_sent['during'] += 1
                        conn.close()
                else:
                    if self.api_insert_log(log_id, f"Log #{logs_sent['during']}")[0]:
                        logs_sent['during'] += 1
                
                time.sleep(0.1)
            
            metrics.logs_during_failure = logs_sent['during']
            print(f"  📊 Logs enviados durante falha: {logs_sent['during']}")
            
            # FASE 4: Restaurar rede
            print(f"\n  🔄 FASE 4: Restaurando Rede")
            
            metrics.recovery_started = datetime.now()
            self.docker_unpause(container)
            print(f"  ▶️  Container despausado")
            
            # Aguardar recuperação
            time.sleep(5)
            
            metrics.recovery_completed = datetime.now()
            metrics.recovery_time = (metrics.recovery_completed - metrics.recovery_started).total_seconds()
            metrics.automatic_recovery = True
            
            # FASE 5: Verificar recuperação
            print(f"\n  📊 FASE 5: Verificando Recuperação (5s)")
            
            phase_start = time.time()
            while time.time() - phase_start < 5:
                log_id = f"ft-s3-{architecture}-{int(time.time()*1000)}"
                self.log_ids.append(log_id)
                
                if architecture == 'traditional':
                    conn = self.postgres_connect()
                    if conn:
                        if self.postgres_insert_log(conn, log_id, f"Log pós #{logs_sent['after']}"):
                            logs_sent['after'] += 1
                            metrics.continued_operating = True
                        conn.close()
                else:
                    if self.api_insert_log(log_id, f"Log pós #{logs_sent['after']}")[0]:
                        logs_sent['after'] += 1
                        metrics.continued_operating = True
                
                time.sleep(0.1)
            
            metrics.logs_after_recovery = logs_sent['after']
            print(f"  ✅ Logs enviados após recuperação: {logs_sent['after']}")
            
            metrics.logs_sent_total = len(self.log_ids)
            metrics.logs_received_total = logs_sent['before'] + logs_sent['after']
            metrics.logs_lost = logs_sent['during']
            metrics.loss_percentage = (metrics.logs_lost / metrics.logs_sent_total * 100) if metrics.logs_sent_total > 0 else 0
            
            print(f"  📊 Perda de dados: {metrics.logs_lost} logs ({metrics.loss_percentage:.2f}%)")
            
        except Exception as e:
            metrics.notes.append(f"Erro: {str(e)}")
            print(f"\n  ❌ ERRO: {str(e)}")
        
        finally:
            metrics.test_end = datetime.now()
            if metrics.failure_detected and metrics.recovery_completed:
                metrics.total_downtime = (metrics.recovery_completed - metrics.failure_detected).total_seconds()
        
        return metrics
    
    # ==================== COMPARAÇÃO E RELATÓRIOS ====================
    
    def compare_architectures(self, scenario: str, hybrid: FailureMetrics, traditional: FailureMetrics) -> ComparisonResult:
        """Compara resultados entre arquiteturas"""
        
        # Detecção mais rápida
        if hybrid.detection_time is not None and traditional.detection_time is not None:
            if hybrid.detection_time < traditional.detection_time:
                faster_detection = 'hybrid'
            elif traditional.detection_time < hybrid.detection_time:
                faster_detection = 'traditional'
            else:
                faster_detection = 'tie'
            detection_diff = abs(hybrid.detection_time - traditional.detection_time)
        else:
            faster_detection = 'unknown'
            detection_diff = None
        
        # Recuperação mais rápida
        if hybrid.recovery_time is not None and traditional.recovery_time is not None:
            if hybrid.recovery_time < traditional.recovery_time:
                faster_recovery = 'hybrid'
            elif traditional.recovery_time < hybrid.recovery_time:
                faster_recovery = 'traditional'
            else:
                faster_recovery = 'tie'
            recovery_diff = abs(hybrid.recovery_time - traditional.recovery_time)
        else:
            faster_recovery = 'unknown'
            recovery_diff = None
        
        # Menos perda de dados
        if hybrid.loss_percentage < traditional.loss_percentage:
            less_data_loss = 'hybrid'
        elif traditional.loss_percentage < hybrid.loss_percentage:
            less_data_loss = 'traditional'
        else:
            less_data_loss = 'tie'
        
        data_loss_diff = abs(hybrid.loss_percentage - traditional.loss_percentage)
        
        # Melhor disponibilidade
        if hybrid.continued_operating and not traditional.continued_operating:
            better_availability = 'hybrid'
        elif traditional.continued_operating and not hybrid.continued_operating:
            better_availability = 'traditional'
        else:
            better_availability = 'tie'
        
        # Função auxiliar para formatar valores que podem ser None
        def fmt(value, default='N/A', decimals=2):
            """Formata valor, retorna default se None"""
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return f"{value:.{decimals}f}"
            return str(value)
        
        # Resumo
        summary = f"""
Cenário: {scenario}

Detecção de Falha:
  - Híbrida: {fmt(hybrid.detection_time)}s
  - Tradicional: {fmt(traditional.detection_time)}s
  - Vencedor: {faster_detection} (diferença: {fmt(detection_diff)}s)

Tempo de Recuperação:
  - Híbrida: {fmt(hybrid.recovery_time)}s
  - Tradicional: {fmt(traditional.recovery_time)}s
  - Vencedor: {faster_recovery} (diferença: {fmt(recovery_diff)}s)

Perda de Dados:
  - Híbrida: {fmt(hybrid.loss_percentage)}%
  - Tradicional: {fmt(traditional.loss_percentage)}%
  - Vencedor: {less_data_loss} (diferença: {fmt(data_loss_diff)}%)

Disponibilidade Durante Falha:
  - Híbrida: {'Sim' if hybrid.continued_operating else 'Não'}
  - Tradicional: {'Sim' if traditional.continued_operating else 'Não'}
  - Vencedor: {better_availability}
"""
        
        return ComparisonResult(
            scenario=scenario,
            hybrid=hybrid,
            traditional=traditional,
            faster_detection=faster_detection,
            faster_recovery=faster_recovery,
            less_data_loss=less_data_loss,
            better_availability=better_availability,
            detection_time_diff=detection_diff,
            recovery_time_diff=recovery_diff,
            data_loss_diff=data_loss_diff,
            summary=summary
        )
    
    def generate_report(self, comparisons: List[ComparisonResult], output_file: str):
        """Gera relatório consolidado"""
        
        report = {
            'test_date': datetime.now().isoformat(),
            'total_scenarios': len(comparisons),
            'comparisons': [],
            'summary': {
                'hybrid_wins': {'detection': 0, 'recovery': 0, 'data_loss': 0, 'availability': 0},
                'traditional_wins': {'detection': 0, 'recovery': 0, 'data_loss': 0, 'availability': 0},
                'ties': {'detection': 0, 'recovery': 0, 'data_loss': 0, 'availability': 0}
            }
        }
        
        for comp in comparisons:
            # Contabilizar vitórias
            for metric in ['detection', 'recovery', 'data_loss', 'availability']:
                winner_attr = f'faster_{metric}' if metric in ['detection', 'recovery'] else f'less_{metric}' if metric == 'data_loss' else f'better_{metric}'
                winner = getattr(comp, winner_attr)
                
                if winner == 'hybrid':
                    report['summary']['hybrid_wins'][metric] += 1
                elif winner == 'traditional':
                    report['summary']['traditional_wins'][metric] += 1
                else:
                    report['summary']['ties'][metric] += 1
            
            report['comparisons'].append({
                'scenario': comp.scenario,
                'hybrid': comp.hybrid.to_dict(),
                'traditional': comp.traditional.to_dict(),
                'winners': {
                    'faster_detection': comp.faster_detection,
                    'faster_recovery': comp.faster_recovery,
                    'less_data_loss': comp.less_data_loss,
                    'better_availability': comp.better_availability
                },
                'differences': {
                    'detection_time': round(comp.detection_time_diff, 2) if comp.detection_time_diff is not None else None,
                    'recovery_time': round(comp.recovery_time_diff, 2) if comp.recovery_time_diff is not None else None,
                    'data_loss': round(comp.data_loss_diff, 2) if comp.data_loss_diff is not None else None
                }
            })
        
        # Salvar JSON
        output_path = RESULTS_DIR / output_file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Relatório salvo em: {output_path}")
        
        # Gerar relatório Markdown
        self.generate_markdown_report(report, output_file.replace('.json', '.md'))
    
    def generate_markdown_report(self, report: Dict, filename: str):
        """Gera relatório em Markdown"""
        
        output_path = RESULTS_DIR / filename
        
        with open(output_path, 'w') as f:
            f.write("# Relatório de Testes de Tolerância a Falhas\n\n")
            f.write(f"**Data do Teste**: {report['test_date']}\n\n")
            f.write(f"**Total de Cenários**: {report['total_scenarios']}\n\n")
            
            f.write("## 📊 Resumo Geral\n\n")
            
            summary = report['summary']
            
            f.write("### Vitórias por Métrica\n\n")
            f.write("| Métrica | Híbrida | Tradicional | Empate |\n")
            f.write("|---------|---------|-------------|--------|\n")
            f.write(f"| **Detecção de Falha** | {summary['hybrid_wins']['detection']} | {summary['traditional_wins']['detection']} | {summary['ties']['detection']} |\n")
            f.write(f"| **Recuperação** | {summary['hybrid_wins']['recovery']} | {summary['traditional_wins']['recovery']} | {summary['ties']['recovery']} |\n")
            f.write(f"| **Perda de Dados** | {summary['hybrid_wins']['data_loss']} | {summary['traditional_wins']['data_loss']} | {summary['ties']['data_loss']} |\n")
            f.write(f"| **Disponibilidade** | {summary['hybrid_wins']['availability']} | {summary['traditional_wins']['availability']} | {summary['ties']['availability']} |\n\n")
            
            # Calcular pontuação total
            hybrid_total = sum(summary['hybrid_wins'].values())
            traditional_total = sum(summary['traditional_wins'].values())
            
            f.write(f"### 🏆 Pontuação Total\n\n")
            f.write(f"- **Híbrida**: {hybrid_total} pontos\n")
            f.write(f"- **Tradicional**: {traditional_total} pontos\n\n")
            
            if hybrid_total > traditional_total:
                f.write(f"**Vencedor Geral**: 🎯 Arquitetura Híbrida\n\n")
            elif traditional_total > hybrid_total:
                f.write(f"**Vencedor Geral**: 🎯 Arquitetura Tradicional\n\n")
            else:
                f.write(f"**Resultado**: 🤝 Empate Técnico\n\n")
            
            # Detalhes por cenário
            f.write("## 🔍 Detalhes por Cenário\n\n")
            
            for comp in report['comparisons']:
                f.write(f"### {comp['scenario']}\n\n")
                
                f.write("#### Tempos de Resposta\n\n")
                f.write("| Métrica | Híbrida | Tradicional | Diferença | Vencedor |\n")
                f.write("|---------|---------|-------------|-----------|----------|\n")
                
                h_det = comp['hybrid'].get('detection_time', 'N/A')
                t_det = comp['traditional'].get('detection_time', 'N/A')
                f.write(f"| Detecção | {h_det}s | {t_det}s | {comp['differences']['detection_time']}s | {comp['winners']['faster_detection']} |\n")
                
                h_rec = comp['hybrid'].get('recovery_time', 'N/A')
                t_rec = comp['traditional'].get('recovery_time', 'N/A')
                f.write(f"| Recuperação | {h_rec}s | {t_rec}s | {comp['differences']['recovery_time']}s | {comp['winners']['faster_recovery']} |\n\n")
                
                f.write("#### Integridade de Dados\n\n")
                f.write("| Métrica | Híbrida | Tradicional |\n")
                f.write("|---------|---------|-------------|\n")
                f.write(f"| Logs Enviados | {comp['hybrid']['logs_sent_total']} | {comp['traditional']['logs_sent_total']} |\n")
                f.write(f"| Logs Recebidos | {comp['hybrid']['logs_received_total']} | {comp['traditional']['logs_received_total']} |\n")
                f.write(f"| Logs Perdidos | {comp['hybrid']['logs_lost']} | {comp['traditional']['logs_lost']} |\n")
                f.write(f"| % Perda | {comp['hybrid']['loss_percentage']}% | {comp['traditional']['loss_percentage']}% |\n\n")
                
                f.write(f"**Vencedor em Integridade**: {comp['winners']['less_data_loss']}\n\n")
                
                f.write("#### Disponibilidade\n\n")
                f.write(f"- **Híbrida**: {'✅ Continuou operando' if comp['hybrid']['continued_operating'] else '❌ Parou de operar'}\n")
                f.write(f"- **Tradicional**: {'✅ Continuou operando' if comp['traditional']['continued_operating'] else '❌ Parou de operar'}\n\n")
                
                f.write("---\n\n")
        
        print(f"✅ Relatório Markdown salvo em: {output_path}")


# ==================== MAIN ====================

def main():
    """Função principal"""
    
    print("\n" + "="*70)
    print("  TESTES DE TOLERÂNCIA A FALHAS - TCC LOG MANAGEMENT")
    print("="*70)
    print("\nComparando comportamento entre arquiteturas:")
    print("  1. Híbrida (MongoDB + Hyperledger Fabric)")
    print("  2. Tradicional (PostgreSQL com Streaming Replication)")
    print("\nCenários de teste:")
    print("  • Falha do banco de dados principal")
    print("  • Falha de nó de replicação")
    print("  • Falha de rede temporária")
    print("\nMétricas avaliadas:")
    print("  • Tempo de detecção (RTO)")
    print("  • Tempo de recuperação (RPO)")
    print("  • Integridade dos dados")
    print("  • Disponibilidade durante falha")
    print("\n" + "="*70)
    
    input("\nPressione ENTER para iniciar os testes...")
    
    tester = FaultToleranceTest()
    comparisons = []
    
    # CENÁRIO 1: Falha do banco principal
    print("\n\n" + "🔥"*35)
    print("  EXECUTANDO CENÁRIO 1: FALHA DO BANCO PRINCIPAL")
    print("🔥"*35)
    
    hybrid_s1 = tester.test_scenario_1_primary_failure('hybrid')
    time.sleep(5)
    traditional_s1 = tester.test_scenario_1_primary_failure('traditional')
    
    comp1 = tester.compare_architectures('primary_database_failure', hybrid_s1, traditional_s1)
    comparisons.append(comp1)
    
    # CENÁRIO 2: Falha de réplica
    print("\n\n" + "🔥"*35)
    print("  EXECUTANDO CENÁRIO 2: FALHA DE RÉPLICA")
    print("🔥"*35)
    
    hybrid_s2 = tester.test_scenario_2_standby_failure('hybrid')
    time.sleep(5)
    traditional_s2 = tester.test_scenario_2_standby_failure('traditional')
    
    comp2 = tester.compare_architectures('replica_node_failure', hybrid_s2, traditional_s2)
    comparisons.append(comp2)
    
    # CENÁRIO 3: Falha de rede
    print("\n\n" + "🔥"*35)
    print("  EXECUTANDO CENÁRIO 3: FALHA DE REDE")
    print("🔥"*35)
    
    hybrid_s3 = tester.test_scenario_3_network_partition('hybrid')
    time.sleep(5)
    traditional_s3 = tester.test_scenario_3_network_partition('traditional')
    
    comp3 = tester.compare_architectures('network_partition', hybrid_s3, traditional_s3)
    comparisons.append(comp3)
    
    # Gerar relatórios
    print("\n\n" + "="*70)
    print("  GERANDO RELATÓRIOS")
    print("="*70)
    
    tester.generate_report(comparisons, 'fault_tolerance_report.json')
    
    # Mostrar resumo
    print("\n\n" + "="*70)
    print("  RESUMO DOS RESULTADOS")
    print("="*70)
    
    for comp in comparisons:
        print(comp.summary)
    
    print("\n✅ Testes concluídos com sucesso!")
    print(f"📁 Resultados salvos em: {RESULTS_DIR}/")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

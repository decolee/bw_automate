#!/usr/bin/env python3
"""
REAL-TIME MONITORING ENGINE - BW AUTOMATE SYSTEM
Monitora mudanças em tempo real no código e executa análises automáticas
Implementa cache inteligente e otimizações de performance
"""

import os
import time
import json
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import hashlib
import pickle
import sqlite3
from queue import Queue, Empty
import sys

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
except ImportError:
    print("Installing watchdog for file monitoring...")
    os.system("pip install watchdog")
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

try:
    import psutil
except ImportError:
    print("Installing psutil for system monitoring...")
    os.system("pip install psutil")
    import psutil

try:
    import redis
except ImportError:
    print("Installing redis for caching...")
    os.system("pip install redis")
    import redis


@dataclass
class MonitoringEvent:
    """Evento de monitoramento em tempo real"""
    event_type: str
    file_path: str
    timestamp: datetime
    change_hash: str
    analysis_required: bool = True
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class PerformanceMetrics:
    """Métricas de performance do sistema"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    analysis_queue_size: int
    active_threads: int
    cache_hit_ratio: float
    average_analysis_time: float
    timestamp: datetime


class IntelligentCache:
    """Sistema de cache inteligente com múltiplos backends"""
    
    def __init__(self, cache_dir: str = None, use_redis: bool = False):
        self.cache_dir = Path(cache_dir or "/tmp/bw_automate_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.use_redis = use_redis
        self.redis_client = None
        self.sqlite_db = self.cache_dir / "cache.db"
        self.hit_count = 0
        self.miss_count = 0
        
        # Initialize SQLite cache
        self._init_sqlite_cache()
        
        # Try to connect to Redis
        if use_redis:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                self.redis_client.ping()
                print("✓ Redis cache connected")
            except:
                print("⚠ Redis not available, using SQLite cache")
                self.use_redis = False
    
    def _init_sqlite_cache(self):
        """Inicializa cache SQLite"""
        conn = sqlite3.connect(self.sqlite_db)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                expiry REAL,
                created_at REAL
            )
        ''')
        conn.commit()
        conn.close()
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera item do cache"""
        try:
            if self.use_redis and self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    self.hit_count += 1
                    return pickle.loads(data)
            
            # SQLite fallback
            conn = sqlite3.connect(self.sqlite_db)
            cursor = conn.execute(
                'SELECT value, expiry FROM cache WHERE key = ? AND expiry > ?',
                (key, time.time())
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                self.hit_count += 1
                return pickle.loads(row[0])
            
            self.miss_count += 1
            return None
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Armazena item no cache"""
        try:
            expiry = time.time() + ttl
            pickled_value = pickle.dumps(value)
            
            if self.use_redis and self.redis_client:
                self.redis_client.setex(key, ttl, pickled_value)
            
            # Always store in SQLite as backup
            conn = sqlite3.connect(self.sqlite_db)
            conn.execute(
                'INSERT OR REPLACE INTO cache (key, value, expiry, created_at) VALUES (?, ?, ?, ?)',
                (key, pickled_value, expiry, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Cache set error: {e}")
    
    def clear_expired(self):
        """Remove itens expirados do cache"""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            conn.execute('DELETE FROM cache WHERE expiry < ?', (time.time(),))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Cache cleanup error: {e}")
    
    @property
    def hit_ratio(self) -> float:
        """Taxa de acerto do cache"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0


class FileChangeHandler(FileSystemEventHandler):
    """Handler para mudanças em arquivos"""
    
    def __init__(self, monitor_engine):
        self.monitor_engine = monitor_engine
        self.last_processed = {}
        self.debounce_time = 2  # segundos
    
    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file_change(event.src_path, 'modified')
    
    def on_created(self, event):
        if not event.is_directory:
            self._handle_file_change(event.src_path, 'created')
    
    def _handle_file_change(self, file_path: str, event_type: str):
        """Processa mudança em arquivo com debounce"""
        now = time.time()
        
        # Debounce - evita múltiplos eventos para o mesmo arquivo
        if file_path in self.last_processed:
            if now - self.last_processed[file_path] < self.debounce_time:
                return
        
        self.last_processed[file_path] = now
        
        # Filtros de arquivos relevantes
        if not self._is_relevant_file(file_path):
            return
        
        # Calcula hash do arquivo
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = hashlib.md5(content).hexdigest()
        except:
            return
        
        # Cria evento de monitoramento
        event = MonitoringEvent(
            event_type=event_type,
            file_path=file_path,
            timestamp=datetime.now(),
            change_hash=file_hash,
            priority=self._get_file_priority(file_path)
        )
        
        self.monitor_engine.add_event(event)
    
    def _is_relevant_file(self, file_path: str) -> bool:
        """Verifica se arquivo é relevante para análise"""
        relevant_extensions = {'.py', '.sql', '.yaml', '.yml', '.json', '.cfg', '.ini'}
        return Path(file_path).suffix.lower() in relevant_extensions
    
    def _get_file_priority(self, file_path: str) -> int:
        """Determina prioridade baseada no tipo de arquivo"""
        path = Path(file_path)
        
        if 'dag' in path.name.lower() or 'airflow' in str(path).lower():
            return 1  # Alta prioridade para DAGs
        elif path.suffix == '.sql':
            return 1  # Alta prioridade para SQL
        elif path.suffix == '.py':
            return 2  # Média prioridade para Python
        else:
            return 3  # Baixa prioridade para outros


class RealTimeMonitoringEngine:
    """Engine principal de monitoramento em tempo real"""
    
    def __init__(self, project_root: str, output_dir: str = None):
        self.project_root = Path(project_root)
        self.output_dir = Path(output_dir or "monitoring_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuração de logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'monitoring.log'),
                logging.StreamHandler()
            ]
        )
        
        self.cache = IntelligentCache(self.output_dir / "cache")
        self.event_queue = Queue()
        self.analysis_queue = Queue()
        self.is_running = False
        self.threads = []
        self.observer = None
        
        # Métricas
        self.metrics = {
            'events_processed': 0,
            'analyses_completed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': None
        }
        
        # Pool de threads para análise
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Callbacks para eventos
        self.event_callbacks: List[Callable] = []
        self.analysis_callbacks: List[Callable] = []
    
    def add_event_callback(self, callback: Callable):
        """Adiciona callback para eventos"""
        self.event_callbacks.append(callback)
    
    def add_analysis_callback(self, callback: Callable):
        """Adiciona callback para análises completas"""
        self.analysis_callbacks.append(callback)
    
    def add_event(self, event: MonitoringEvent):
        """Adiciona evento à fila de processamento"""
        self.event_queue.put(event)
        logging.info(f"Event added: {event.event_type} - {event.file_path}")
    
    def start_monitoring(self):
        """Inicia monitoramento em tempo real"""
        if self.is_running:
            logging.warning("Monitoring already running")
            return
        
        self.is_running = True
        self.metrics['start_time'] = datetime.now()
        
        logging.info(f"Starting real-time monitoring of {self.project_root}")
        
        # Thread para processamento de eventos
        event_thread = threading.Thread(target=self._event_processor, daemon=True)
        event_thread.start()
        self.threads.append(event_thread)
        
        # Thread para análise
        analysis_thread = threading.Thread(target=self._analysis_processor, daemon=True)
        analysis_thread.start()
        self.threads.append(analysis_thread)
        
        # Thread para métricas de sistema
        metrics_thread = threading.Thread(target=self._metrics_collector, daemon=True)
        metrics_thread.start()
        self.threads.append(metrics_thread)
        
        # Thread para limpeza de cache
        cleanup_thread = threading.Thread(target=self._cache_cleanup, daemon=True)
        cleanup_thread.start()
        self.threads.append(cleanup_thread)
        
        # Configurar watchdog
        self.observer = Observer()
        handler = FileChangeHandler(self)
        self.observer.schedule(handler, str(self.project_root), recursive=True)
        self.observer.start()
        
        logging.info("✓ Real-time monitoring started successfully")
    
    def stop_monitoring(self):
        """Para monitoramento"""
        if not self.is_running:
            return
        
        logging.info("Stopping real-time monitoring...")
        self.is_running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Esperar threads terminarem
        for thread in self.threads:
            thread.join(timeout=5)
        
        self.executor.shutdown(wait=True)
        
        # Salvar métricas finais
        self._save_final_metrics()
        
        logging.info("✓ Real-time monitoring stopped")
    
    def _event_processor(self):
        """Processa eventos da fila"""
        while self.is_running:
            try:
                event = self.event_queue.get(timeout=1)
                self._process_event(event)
                self.metrics['events_processed'] += 1
                
                # Executa callbacks
                for callback in self.event_callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logging.error(f"Event callback error: {e}")
                
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Event processor error: {e}")
    
    def _process_event(self, event: MonitoringEvent):
        """Processa evento individual"""
        cache_key = f"file_analysis_{event.change_hash}"
        
        # Verifica cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logging.info(f"Cache hit for {event.file_path}")
            self.metrics['cache_hits'] += 1
            return cached_result
        
        self.metrics['cache_misses'] += 1
        
        # Adiciona à fila de análise se necessário
        if event.analysis_required:
            self.analysis_queue.put(event)
    
    def _analysis_processor(self):
        """Processa análises da fila"""
        while self.is_running:
            try:
                event = self.analysis_queue.get(timeout=1)
                
                # Executa análise em thread separada
                future = self.executor.submit(self._run_analysis, event)
                
                # Aguarda resultado com timeout
                try:
                    result = future.result(timeout=30)  # 30 segundos timeout
                    self._handle_analysis_result(event, result)
                    self.metrics['analyses_completed'] += 1
                except TimeoutError:
                    logging.warning(f"Analysis timeout for {event.file_path}")
                    future.cancel()
                
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Analysis processor error: {e}")
    
    def _run_analysis(self, event: MonitoringEvent) -> Dict[str, Any]:
        """Executa análise do arquivo"""
        try:
            # Importa componentes de análise
            sys.path.append(str(Path(__file__).parent))
            
            # Análise básica do arquivo
            file_path = Path(event.file_path)
            
            if not file_path.exists():
                return {'error': 'File not found', 'file_path': str(file_path)}
            
            analysis_result = {
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'modification_time': file_path.stat().st_mtime,
                'file_type': file_path.suffix,
                'analysis_timestamp': datetime.now().isoformat(),
                'tables_found': [],
                'sql_patterns': [],
                'issues_detected': []
            }
            
            # Análise específica por tipo de arquivo
            if file_path.suffix == '.py':
                analysis_result.update(self._analyze_python_file(file_path))
            elif file_path.suffix == '.sql':
                analysis_result.update(self._analyze_sql_file(file_path))
            elif file_path.suffix in ['.yaml', '.yml']:
                analysis_result.update(self._analyze_yaml_file(file_path))
            
            # Cache do resultado
            cache_key = f"file_analysis_{event.change_hash}"
            self.cache.set(cache_key, analysis_result, ttl=3600)
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"Analysis error for {event.file_path}: {e}")
            return {'error': str(e), 'file_path': event.file_path}
    
    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Análise específica para arquivos Python"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = {
                'line_count': len(content.splitlines()),
                'imports': [],
                'sql_patterns': [],
                'table_references': []
            }
            
            # Detecta padrões SQL básicos
            import re
            sql_patterns = [
                r'SELECT\s+.*\s+FROM\s+(\w+)',
                r'INSERT\s+INTO\s+(\w+)',
                r'UPDATE\s+(\w+)\s+SET',
                r'DELETE\s+FROM\s+(\w+)',
                r'CREATE\s+TABLE\s+(\w+)',
                r'DROP\s+TABLE\s+(\w+)'
            ]
            
            for pattern in sql_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    result['table_references'].extend(matches)
                    result['sql_patterns'].append({
                        'pattern': pattern,
                        'matches': matches
                    })
            
            # Detecta imports
            import_pattern = r'^import\s+(\S+)|^from\s+(\S+)\s+import'
            for match in re.finditer(import_pattern, content, re.MULTILINE):
                if match.group(1):
                    result['imports'].append(match.group(1))
                elif match.group(2):
                    result['imports'].append(match.group(2))
            
            return result
            
        except Exception as e:
            return {'error': f"Python analysis error: {e}"}
    
    def _analyze_sql_file(self, file_path: Path) -> Dict[str, Any]:
        """Análise específica para arquivos SQL"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = {
                'line_count': len(content.splitlines()),
                'table_references': [],
                'sql_operations': []
            }
            
            # Detecta operações SQL
            import re
            operations = {
                'SELECT': r'SELECT\s+.*?\s+FROM\s+(\w+)',
                'INSERT': r'INSERT\s+INTO\s+(\w+)',
                'UPDATE': r'UPDATE\s+(\w+)',
                'DELETE': r'DELETE\s+FROM\s+(\w+)',
                'CREATE': r'CREATE\s+TABLE\s+(\w+)',
                'DROP': r'DROP\s+TABLE\s+(\w+)'
            }
            
            for op_type, pattern in operations.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    result['table_references'].extend(matches)
                    result['sql_operations'].append({
                        'operation': op_type,
                        'tables': matches,
                        'count': len(matches)
                    })
            
            return result
            
        except Exception as e:
            return {'error': f"SQL analysis error: {e}"}
    
    def _analyze_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Análise específica para arquivos YAML"""
        try:
            import yaml
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = yaml.safe_load(content)
            
            result = {
                'line_count': len(content.splitlines()),
                'yaml_keys': list(data.keys()) if isinstance(data, dict) else [],
                'config_values': []
            }
            
            # Extrai configurações que podem conter nomes de tabelas
            if isinstance(data, dict):
                def extract_configs(obj, prefix=''):
                    configs = []
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            current_key = f"{prefix}.{key}" if prefix else key
                            if isinstance(value, str) and ('table' in key.lower() or 'sql' in key.lower()):
                                configs.append({'key': current_key, 'value': value})
                            elif isinstance(value, (dict, list)):
                                configs.extend(extract_configs(value, current_key))
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            configs.extend(extract_configs(item, f"{prefix}[{i}]"))
                    return configs
                
                result['config_values'] = extract_configs(data)
            
            return result
            
        except Exception as e:
            return {'error': f"YAML analysis error: {e}"}
    
    def _handle_analysis_result(self, event: MonitoringEvent, result: Dict[str, Any]):
        """Processa resultado da análise"""
        # Salva resultado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.output_dir / f"analysis_{timestamp}_{Path(event.file_path).name}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Executa callbacks
        for callback in self.analysis_callbacks:
            try:
                callback(event, result)
            except Exception as e:
                logging.error(f"Analysis callback error: {e}")
        
        logging.info(f"Analysis completed for {event.file_path}")
    
    def _metrics_collector(self):
        """Coleta métricas de sistema"""
        while self.is_running:
            try:
                metrics = PerformanceMetrics(
                    cpu_usage=psutil.cpu_percent(),
                    memory_usage=psutil.virtual_memory().percent,
                    disk_usage=psutil.disk_usage('/').percent,
                    analysis_queue_size=self.analysis_queue.qsize(),
                    active_threads=threading.active_count(),
                    cache_hit_ratio=self.cache.hit_ratio,
                    average_analysis_time=0.0,  # TODO: implementar
                    timestamp=datetime.now()
                )
                
                # Salva métricas
                metrics_file = self.output_dir / "performance_metrics.jsonl"
                with open(metrics_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(metrics), default=str) + '\n')
                
                time.sleep(30)  # Coleta a cada 30 segundos
                
            except Exception as e:
                logging.error(f"Metrics collection error: {e}")
                time.sleep(60)
    
    def _cache_cleanup(self):
        """Limpeza periódica do cache"""
        while self.is_running:
            try:
                self.cache.clear_expired()
                time.sleep(300)  # Limpeza a cada 5 minutos
            except Exception as e:
                logging.error(f"Cache cleanup error: {e}")
                time.sleep(600)
    
    def _save_final_metrics(self):
        """Salva métricas finais"""
        final_metrics = {
            'session_duration': str(datetime.now() - self.metrics['start_time']),
            'events_processed': self.metrics['events_processed'],
            'analyses_completed': self.metrics['analyses_completed'],
            'cache_hit_ratio': self.cache.hit_ratio,
            'final_timestamp': datetime.now().isoformat()
        }
        
        with open(self.output_dir / "final_metrics.json", 'w') as f:
            json.dump(final_metrics, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do monitoramento"""
        return {
            'is_running': self.is_running,
            'events_in_queue': self.event_queue.qsize(),
            'analyses_in_queue': self.analysis_queue.qsize(),
            'cache_hit_ratio': self.cache.hit_ratio,
            'uptime': str(datetime.now() - self.metrics['start_time']) if self.metrics['start_time'] else None,
            'events_processed': self.metrics['events_processed'],
            'analyses_completed': self.metrics['analyses_completed']
        }


# Exemplo de uso e teste
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BW Automate Real-Time Monitoring")
    parser.add_argument("project_root", help="Diretório raiz do projeto para monitorar")
    parser.add_argument("--output", "-o", help="Diretório de saída", default="monitoring_output")
    parser.add_argument("--duration", "-d", type=int, help="Duração em segundos (0 = infinito)", default=0)
    
    args = parser.parse_args()
    
    # Cria engine de monitoramento
    engine = RealTimeMonitoringEngine(args.project_root, args.output)
    
    # Callbacks de exemplo
    def on_event(event: MonitoringEvent):
        print(f"📁 Event: {event.event_type} - {Path(event.file_path).name}")
    
    def on_analysis(event: MonitoringEvent, result: Dict[str, Any]):
        tables = result.get('table_references', [])
        if tables:
            print(f"🔍 Found tables in {Path(event.file_path).name}: {tables}")
    
    engine.add_event_callback(on_event)
    engine.add_analysis_callback(on_analysis)
    
    try:
        # Inicia monitoramento
        engine.start_monitoring()
        
        print(f"🚀 Monitoring started for {args.project_root}")
        print("Press Ctrl+C to stop monitoring...")
        
        if args.duration > 0:
            print(f"⏱ Will run for {args.duration} seconds")
            time.sleep(args.duration)
        else:
            while True:
                status = engine.get_status()
                print(f"\r📊 Events: {status['events_processed']} | Analyses: {status['analyses_completed']} | Cache: {status['cache_hit_ratio']:.2%}", end='')
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitoring...")
    finally:
        engine.stop_monitoring()
        print("✅ Monitoring stopped successfully")
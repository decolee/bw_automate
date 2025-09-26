#!/usr/bin/env python3
"""
Debug Mode v2.0
===============

Modo debug avançado para o BW_AUTOMATE com capacidades de:
- Debugging interativo
- Profiling detalhado
- Análise step-by-step
- Dump de dados intermediários
- Visualização de fluxo
- Métricas em tempo real

Principais funcionalidades:
- Breakpoints programáticos
- Inspeção de variáveis
- Timeline de execução
- Memory profiling
- SQL query tracking
- Interactive debugging

Autor: BW_AUTOMATE v2.0
Data: 2025-09-20
"""

import os
import sys
import json
import time
import traceback
import inspect
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

# Importações opcionais
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import memory_profiler
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False

@dataclass
class DebugCheckpoint:
    """Checkpoint de debug"""
    name: str
    timestamp: str
    file_path: str
    line_number: int
    function_name: str
    variables: Dict[str, Any]
    memory_usage_mb: float
    execution_time_ms: float

@dataclass
class DebugSession:
    """Sessão de debug"""
    session_id: str
    start_time: str
    end_time: Optional[str]
    checkpoints: List[DebugCheckpoint]
    total_duration_ms: float
    peak_memory_mb: float
    error_occurred: bool
    error_details: Optional[Dict[str, Any]]

class DebugProfiler:
    """Profiler para modo debug"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checkpoints = []
        self.memory_snapshots = []
        self.sql_queries = []
        self.function_calls = []
    
    def checkpoint(self, name: str, context: Dict[str, Any] = None):
        """Cria checkpoint"""
        current_time = time.time()
        frame = inspect.currentframe().f_back
        
        checkpoint = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'elapsed_ms': (current_time - self.start_time) * 1000,
            'file': frame.f_code.co_filename,
            'line': frame.f_lineno,
            'function': frame.f_code.co_name,
            'context': context or {}
        }
        
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                checkpoint['memory_mb'] = process.memory_info().rss / 1024 / 1024
                checkpoint['cpu_percent'] = process.cpu_percent()
            except:
                checkpoint['memory_mb'] = 0
                checkpoint['cpu_percent'] = 0
        
        self.checkpoints.append(checkpoint)
        return checkpoint
    
    def get_summary(self):
        """Retorna resumo do profiling"""
        if not self.checkpoints:
            return {}
        
        total_time = self.checkpoints[-1]['elapsed_ms'] if self.checkpoints else 0
        
        return {
            'total_checkpoints': len(self.checkpoints),
            'total_time_ms': total_time,
            'peak_memory_mb': max(cp.get('memory_mb', 0) for cp in self.checkpoints),
            'avg_memory_mb': sum(cp.get('memory_mb', 0) for cp in self.checkpoints) / len(self.checkpoints),
            'checkpoints': self.checkpoints
        }

class DebugMode:
    """
    Modo debug avançado para BW_AUTOMATE
    """
    
    def __init__(self, 
                 debug_dir: str = "BW_AUTOMATE/debug",
                 config: Dict[str, Any] = None):
        """
        Inicializa modo debug
        
        Args:
            debug_dir: Diretório para arquivos de debug
            config: Configurações de debug
        """
        self.debug_dir = Path(debug_dir)
        self.config = config or {}
        
        # Configurações padrão
        self.default_config = {
            'enabled': True,
            'verbose_logging': True,
            'save_intermediate_data': True,
            'memory_profiling': True,
            'sql_query_tracking': True,
            'function_call_tracking': True,
            'interactive_mode': False,
            'breakpoints_enabled': True,
            'max_variable_size_kb': 100,
            'auto_checkpoint_interval_ms': 1000
        }
        
        # Merge configurações
        self.settings = {**self.default_config, **self.config}
        
        # Estado do debug
        self.is_active = self.settings['enabled']
        self.session_id = f"debug_{int(time.time() * 1000)}"
        self.start_time = time.time()
        self.profiler = DebugProfiler()
        
        # Dados de debug
        self.checkpoints: List[DebugCheckpoint] = []
        self.variable_dumps: Dict[str, Any] = {}
        self.sql_queries: List[Dict[str, Any]] = []
        self.function_timeline: List[Dict[str, Any]] = []
        self.breakpoints: List[str] = []
        
        # Thread-safe
        self.lock = threading.Lock()
        
        # Cria diretório
        if self.is_active:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            self._setup_debug_logging()
            self.debug_log(f"Debug mode iniciado: {self.session_id}")
    
    def _setup_debug_logging(self):
        """Configura logging de debug"""
        debug_log_file = self.debug_dir / f"debug_{self.session_id}.log"
        
        self.debug_logger = logging.getLogger(f"DEBUG_{self.session_id}")
        self.debug_logger.setLevel(logging.DEBUG)
        
        # Remove handlers existentes
        for handler in self.debug_logger.handlers[:]:
            self.debug_logger.removeHandler(handler)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(debug_log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.debug_logger.addHandler(file_handler)
        
        # Handler para console se verboso
        if self.settings['verbose_logging']:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '🐛 %(asctime)s | DEBUG | %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.debug_logger.addHandler(console_handler)
    
    def debug_log(self, message: str, **kwargs):
        """Log de debug"""
        if not self.is_active:
            return
        
        if kwargs:
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} | {context}"
        
        self.debug_logger.debug(message)
    
    def checkpoint(self, name: str, **context):
        """Cria checkpoint de debug"""
        if not self.is_active:
            return
        
        with self.lock:
            current_time = time.time()
            frame = inspect.currentframe().f_back
            
            # Captura variáveis locais (limitado)
            variables = {}
            if frame and self.settings['save_intermediate_data']:
                local_vars = frame.f_locals
                for var_name, var_value in local_vars.items():
                    if not var_name.startswith('_'):
                        try:
                            # Limita tamanho da variável
                            var_str = str(var_value)
                            if len(var_str) <= self.settings['max_variable_size_kb'] * 1024:
                                variables[var_name] = var_str[:1000]  # Limita output
                        except:
                            variables[var_name] = "<não serializável>"
            
            # Memoria atual
            memory_usage = 0
            if PSUTIL_AVAILABLE:
                try:
                    process = psutil.Process()
                    memory_usage = process.memory_info().rss / 1024 / 1024
                except:
                    pass
            
            checkpoint = DebugCheckpoint(
                name=name,
                timestamp=datetime.now().isoformat(),
                file_path=frame.f_code.co_filename if frame else "unknown",
                line_number=frame.f_lineno if frame else 0,
                function_name=frame.f_code.co_name if frame else "unknown",
                variables=variables,
                memory_usage_mb=memory_usage,
                execution_time_ms=(current_time - self.start_time) * 1000
            )
            
            self.checkpoints.append(checkpoint)
            self.profiler.checkpoint(name, context)
            
            self.debug_log(
                f"Checkpoint: {name}",
                file=os.path.basename(checkpoint.file_path),
                line=checkpoint.line_number,
                memory_mb=round(memory_usage, 2),
                elapsed_ms=round(checkpoint.execution_time_ms, 2)
            )
            
            # Auto-save se muitos checkpoints
            if len(self.checkpoints) % 10 == 0:
                self._auto_save_session()
    
    def breakpoint(self, condition: Union[bool, Callable] = True, message: str = ""):
        """Breakpoint programático"""
        if not self.is_active or not self.settings['breakpoints_enabled']:
            return
        
        # Avalia condição
        should_break = condition
        if callable(condition):
            try:
                should_break = condition()
            except:
                should_break = False
        
        if should_break:
            frame = inspect.currentframe().f_back
            location = f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}"
            
            self.debug_log(f"BREAKPOINT ATINGIDO: {location} - {message}")
            
            if self.settings['interactive_mode']:
                self._interactive_debug(frame)
            else:
                self.checkpoint(f"breakpoint_{location}", message=message)
    
    def _interactive_debug(self, frame):
        """Modo debug interativo"""
        print(f"\n🔍 BREAKPOINT DEBUG MODE")
        print(f"Arquivo: {frame.f_code.co_filename}")
        print(f"Linha: {frame.f_lineno}")
        print(f"Função: {frame.f_code.co_name}")
        print("\nComandos disponíveis:")
        print("  vars - Lista variáveis locais")
        print("  eval <expr> - Avalia expressão")
        print("  continue - Continua execução")
        print("  quit - Sai do programa")
        
        while True:
            try:
                cmd = input("\n(debug) ").strip()
                
                if cmd == "continue" or cmd == "c":
                    break
                elif cmd == "quit" or cmd == "q":
                    sys.exit(0)
                elif cmd == "vars" or cmd == "v":
                    for name, value in frame.f_locals.items():
                        if not name.startswith('_'):
                            print(f"  {name} = {repr(value)}")
                elif cmd.startswith("eval ") or cmd.startswith("e "):
                    expr = cmd.split(" ", 1)[1]
                    try:
                        result = eval(expr, frame.f_globals, frame.f_locals)
                        print(f"  => {repr(result)}")
                    except Exception as e:
                        print(f"  Erro: {e}")
                elif cmd == "help" or cmd == "h":
                    print("Comandos: vars, eval <expr>, continue, quit")
                else:
                    print("Comando não reconhecido. Digite 'help' para ajuda.")
            
            except (EOFError, KeyboardInterrupt):
                break
    
    def track_sql_query(self, query: str, file_path: str, line_number: int, **context):
        """Rastreia query SQL"""
        if not self.is_active or not self.settings['sql_query_tracking']:
            return
        
        with self.lock:
            query_info = {
                'query': query,
                'file_path': file_path,
                'line_number': line_number,
                'timestamp': datetime.now().isoformat(),
                'execution_time_ms': (time.time() - self.start_time) * 1000,
                'context': context
            }
            
            self.sql_queries.append(query_info)
            
            self.debug_log(
                f"SQL Query tracked",
                file=os.path.basename(file_path),
                line=line_number,
                query_length=len(query)
            )
    
    def track_function_call(self, func_name: str, args: List[Any] = None, kwargs: Dict[str, Any] = None):
        """Rastreia chamada de função"""
        if not self.is_active or not self.settings['function_call_tracking']:
            return
        
        with self.lock:
            frame = inspect.currentframe().f_back
            
            call_info = {
                'function_name': func_name,
                'file_path': frame.f_code.co_filename,
                'line_number': frame.f_lineno,
                'timestamp': datetime.now().isoformat(),
                'execution_time_ms': (time.time() - self.start_time) * 1000,
                'args_count': len(args) if args else 0,
                'kwargs_count': len(kwargs) if kwargs else 0
            }
            
            self.function_timeline.append(call_info)
            
            self.debug_log(
                f"Function call: {func_name}",
                file=os.path.basename(frame.f_code.co_filename),
                line=frame.f_lineno,
                args=len(args) if args else 0
            )
    
    def dump_variable(self, var_name: str, var_value: Any, context: str = ""):
        """Faz dump de variável para análise"""
        if not self.is_active or not self.settings['save_intermediate_data']:
            return
        
        with self.lock:
            timestamp = datetime.now().isoformat()
            
            # Tenta serializar a variável
            try:
                if hasattr(var_value, 'to_dict'):
                    serialized = var_value.to_dict()
                elif hasattr(var_value, '__dict__'):
                    serialized = var_value.__dict__
                else:
                    serialized = str(var_value)
            except:
                serialized = f"<não serializável: {type(var_value).__name__}>"
            
            dump_info = {
                'variable_name': var_name,
                'variable_type': type(var_value).__name__,
                'timestamp': timestamp,
                'context': context,
                'value': serialized
            }
            
            # Salva em arquivo separado se grande
            if len(str(serialized)) > 10000:
                dump_file = self.debug_dir / f"var_dump_{var_name}_{int(time.time())}.json"
                with open(dump_file, 'w', encoding='utf-8') as f:
                    json.dump(dump_info, f, indent=2, ensure_ascii=False, default=str)
                
                self.variable_dumps[f"{var_name}_{timestamp}"] = f"saved_to_file:{dump_file}"
            else:
                self.variable_dumps[f"{var_name}_{timestamp}"] = dump_info
            
            self.debug_log(
                f"Variable dumped: {var_name}",
                type=type(var_value).__name__,
                size_chars=len(str(serialized)),
                context=context
            )
    
    def analyze_performance_bottleneck(self) -> Dict[str, Any]:
        """Analisa gargalos de performance"""
        if not self.checkpoints:
            return {}
        
        analysis = {
            'total_execution_time_ms': self.checkpoints[-1].execution_time_ms,
            'checkpoint_count': len(self.checkpoints),
            'memory_analysis': {
                'peak_memory_mb': max(cp.memory_usage_mb for cp in self.checkpoints),
                'avg_memory_mb': sum(cp.memory_usage_mb for cp in self.checkpoints) / len(self.checkpoints),
                'memory_growth': self.checkpoints[-1].memory_usage_mb - self.checkpoints[0].memory_usage_mb
            },
            'time_analysis': {
                'slowest_checkpoint': None,
                'fastest_checkpoint': None,
                'avg_checkpoint_interval_ms': 0
            }
        }
        
        # Analisa intervalos entre checkpoints
        intervals = []
        for i in range(1, len(self.checkpoints)):
            interval = self.checkpoints[i].execution_time_ms - self.checkpoints[i-1].execution_time_ms
            intervals.append({
                'checkpoint': self.checkpoints[i].name,
                'interval_ms': interval
            })
        
        if intervals:
            slowest = max(intervals, key=lambda x: x['interval_ms'])
            fastest = min(intervals, key=lambda x: x['interval_ms'])
            
            analysis['time_analysis']['slowest_checkpoint'] = slowest
            analysis['time_analysis']['fastest_checkpoint'] = fastest
            analysis['time_analysis']['avg_checkpoint_interval_ms'] = sum(i['interval_ms'] for i in intervals) / len(intervals)
        
        self.debug_log(
            "Performance analysis completed",
            total_time_ms=analysis['total_execution_time_ms'],
            peak_memory_mb=analysis['memory_analysis']['peak_memory_mb'],
            checkpoints=len(self.checkpoints)
        )
        
        return analysis
    
    def _auto_save_session(self):
        """Auto-salva sessão de debug"""
        try:
            session_file = self.debug_dir / f"session_{self.session_id}.json"
            session_data = {
                'session_id': self.session_id,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'current_time': datetime.now().isoformat(),
                'settings': self.settings,
                'checkpoints_count': len(self.checkpoints),
                'sql_queries_count': len(self.sql_queries),
                'function_calls_count': len(self.function_timeline),
                'profiler_summary': self.profiler.get_summary()
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            self.debug_log(f"Erro ao auto-salvar sessão: {e}")
    
    def export_debug_report(self, output_path: str = None) -> str:
        """Exporta relatório completo de debug"""
        if not output_path:
            output_path = self.debug_dir / f"debug_report_{self.session_id}.json"
        
        # Performance analysis
        performance_analysis = self.analyze_performance_bottleneck()
        
        report = {
            'session_info': {
                'session_id': self.session_id,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_duration_ms': (time.time() - self.start_time) * 1000,
                'settings': self.settings
            },
            'checkpoints': [asdict(cp) for cp in self.checkpoints],
            'sql_queries': self.sql_queries,
            'function_timeline': self.function_timeline,
            'variable_dumps': self.variable_dumps,
            'performance_analysis': performance_analysis,
            'profiler_summary': self.profiler.get_summary(),
            'system_info': self._get_system_info()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self.debug_log(f"Debug report exported: {output_path}")
        return str(output_path)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Coleta informações do sistema"""
        info = {
            'python_version': sys.version,
            'platform': sys.platform
        }
        
        if PSUTIL_AVAILABLE:
            try:
                info.update({
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                    'memory_available_gb': psutil.virtual_memory().available / 1024 / 1024 / 1024
                })
            except:
                pass
        
        return info
    
    def finalize(self):
        """Finaliza sessão de debug"""
        if not self.is_active:
            return
        
        self.debug_log(
            "Debug session finalizada",
            total_checkpoints=len(self.checkpoints),
            total_duration_ms=(time.time() - self.start_time) * 1000,
            sql_queries=len(self.sql_queries)
        )
        
        # Export final report
        report_path = self.export_debug_report()
        
        # Performance summary
        performance = self.analyze_performance_bottleneck()
        
        print(f"\n🐛 DEBUG SESSION SUMMARY")
        print(f"Session ID: {self.session_id}")
        print(f"Total Duration: {performance.get('total_execution_time_ms', 0):.2f}ms")
        print(f"Checkpoints: {len(self.checkpoints)}")
        print(f"Peak Memory: {performance.get('memory_analysis', {}).get('peak_memory_mb', 0):.2f}MB")
        print(f"SQL Queries Tracked: {len(self.sql_queries)}")
        print(f"Debug Report: {report_path}")
        
        return report_path

# Context manager para debug automático
class debug_session:
    """Context manager para sessão de debug"""
    
    def __init__(self, name: str = "debug_session", **config):
        self.name = name
        self.config = config
        self.debug_mode = None
    
    def __enter__(self):
        self.debug_mode = DebugMode(config=self.config)
        self.debug_mode.checkpoint(f"start_{self.name}")
        return self.debug_mode
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.debug_mode.debug_log(
                f"Exception in debug session: {exc_type.__name__}: {exc_val}"
            )
        
        self.debug_mode.checkpoint(f"end_{self.name}")
        self.debug_mode.finalize()

# Decorador para debug automático
def debug_function(checkpoint_name: str = None):
    """Decorador para debug automático de funções"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = checkpoint_name or f"function_{func.__name__}"
            
            debug_mode = DebugMode()
            debug_mode.checkpoint(f"start_{name}")
            debug_mode.track_function_call(func.__name__, args, kwargs)
            
            try:
                result = func(*args, **kwargs)
                debug_mode.checkpoint(f"end_{name}")
                return result
            except Exception as e:
                debug_mode.debug_log(f"Exception in {func.__name__}: {e}")
                raise
            finally:
                debug_mode.finalize()
        
        return wrapper
    return decorator
#!/usr/bin/env python3
"""
Advanced Logger v2.0
====================

Sistema de logging avançado para o BW_AUTOMATE com:
- Logs estruturados
- Múltiplos formatos de saída
- Contexto detalhado
- Performance tracking
- Logs de auditoria
- Integração com debug

Principais funcionalidades:
- Logs coloridos no console
- Rotação automática de arquivos
- Filtragem por contexto
- Métricas de performance
- Export de logs para análise

Autor: BW_AUTOMATE v2.0
Data: 2025-09-20
"""

import logging
import logging.handlers
import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
import inspect
import traceback

@dataclass
class LogContext:
    """Contexto de um log entry"""
    file_path: str
    function_name: str
    line_number: int
    module_name: str
    thread_id: str
    timestamp: str
    execution_time_ms: Optional[float] = None

@dataclass
class PerformanceMetric:
    """Métrica de performance"""
    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    memory_usage_mb: float
    context: Dict[str, Any]

class ColoredFormatter(logging.Formatter):
    """Formatter colorido para console"""
    
    # Códigos de cor ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Ciano
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarelo
        'ERROR': '\033[31m',      # Vermelho
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Formata log com cores"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Adiciona cor ao nível
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)

class ContextFilter(logging.Filter):
    """Filtro que adiciona contexto aos logs"""
    
    def filter(self, record):
        """Adiciona informações de contexto"""
        frame = inspect.currentframe()
        
        # Busca frame do código que chamou o log
        while frame:
            filename = frame.f_code.co_filename
            if 'advanced_logger.py' not in filename and 'logging' not in filename:
                record.source_file = os.path.basename(filename)
                record.source_function = frame.f_code.co_name
                record.source_line = frame.f_lineno
                break
            frame = frame.f_back
        
        # Adiciona thread ID
        record.thread_id = threading.current_thread().ident
        
        return True

class AdvancedLogger:
    """
    Sistema de logging avançado para BW_AUTOMATE
    """
    
    def __init__(self, 
                 name: str = "BW_AUTOMATE",
                 log_dir: str = "BW_AUTOMATE/logs",
                 config: Dict[str, Any] = None):
        """
        Inicializa o logger avançado
        
        Args:
            name: Nome do logger
            log_dir: Diretório de logs
            config: Configurações do logger
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.config = config or {}
        
        # Configurações padrão
        self.default_config = {
            'log_level': 'INFO',
            'console_enabled': True,
            'file_enabled': True,
            'colored_console': True,
            'max_file_size_mb': 10,
            'backup_count': 5,
            'json_format': False,
            'performance_tracking': True,
            'audit_enabled': True,
            'context_enabled': True
        }
        
        # Merge configurações
        self.settings = {**self.default_config, **self.config}
        
        # Cria diretório de logs
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializa loggers
        self._setup_loggers()
        
        # Performance tracking
        self.performance_metrics: List[PerformanceMetric] = []
        self.operation_stack: List[Dict[str, Any]] = []
        
        # Audit trail
        self.audit_events: List[Dict[str, Any]] = []
        
        self.logger.info(f"AdvancedLogger inicializado: {name}")
    
    def _setup_loggers(self):
        """Configura os loggers"""
        
        # Logger principal
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, self.settings['log_level']))
        
        # Remove handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler para console
        if self.settings['console_enabled']:
            console_handler = logging.StreamHandler()
            
            if self.settings['colored_console']:
                console_formatter = ColoredFormatter(
                    '%(asctime)s | %(levelname)s | %(source_file)s:%(source_line)d | %(message)s'
                )
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)s | %(source_file)s:%(source_line)d | %(message)s'
                )
            
            console_handler.setFormatter(console_formatter)
            console_handler.addFilter(ContextFilter())
            self.logger.addHandler(console_handler)
        
        # Handler para arquivo
        if self.settings['file_enabled']:
            file_path = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
            
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self.settings['max_file_size_mb'] * 1024 * 1024,
                backupCount=self.settings['backup_count'],
                encoding='utf-8'
            )
            
            if self.settings['json_format']:
                file_formatter = self._create_json_formatter()
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s | %(levelname)s | %(thread_id)s | %(source_file)s:%(source_line)d | %(source_function)s | %(message)s'
                )
            
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(ContextFilter())
            self.logger.addHandler(file_handler)
        
        # Logger de performance
        if self.settings['performance_tracking']:
            self.perf_logger = logging.getLogger(f"{self.name}.performance")
            perf_file = self.log_dir / f"{self.name}_performance_{datetime.now().strftime('%Y%m%d')}.log"
            
            perf_handler = logging.FileHandler(perf_file, encoding='utf-8')
            perf_formatter = logging.Formatter('%(asctime)s | %(message)s')
            perf_handler.setFormatter(perf_formatter)
            self.perf_logger.addHandler(perf_handler)
            self.perf_logger.setLevel(logging.INFO)
        
        # Logger de auditoria
        if self.settings['audit_enabled']:
            self.audit_logger = logging.getLogger(f"{self.name}.audit")
            audit_file = self.log_dir / f"{self.name}_audit_{datetime.now().strftime('%Y%m%d')}.log"
            
            audit_handler = logging.FileHandler(audit_file, encoding='utf-8')
            audit_formatter = logging.Formatter('%(asctime)s | %(message)s')
            audit_handler.setFormatter(audit_formatter)
            self.audit_logger.addHandler(audit_handler)
            self.audit_logger.setLevel(logging.INFO)
    
    def _create_json_formatter(self):
        """Cria formatter JSON"""
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': self.formatTime(record),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.name,
                    'thread_id': getattr(record, 'thread_id', None),
                    'source': {
                        'file': getattr(record, 'source_file', None),
                        'function': getattr(record, 'source_function', None),
                        'line': getattr(record, 'source_line', None)
                    }
                }
                
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                
                return json.dumps(log_entry, ensure_ascii=False)
        
        return JSONFormatter()
    
    def debug(self, message: str, **kwargs):
        """Log de debug com contexto"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de info com contexto"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de warning com contexto"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de error com contexto"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log de critical com contexto"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log com contexto adicional"""
        
        # Adiciona contexto se habilitado
        if self.settings['context_enabled'] and kwargs:
            context_str = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} | {context_str}"
        
        self.logger.log(level, message)
    
    def log_sql_analysis(self, 
                        file_path: str, 
                        statements_found: int, 
                        tables_found: int, 
                        execution_time_ms: float):
        """Log específico para análise SQL"""
        
        self.info(
            "Análise SQL concluída",
            file=file_path,
            sql_statements=statements_found,
            tables_found=tables_found,
            duration_ms=execution_time_ms
        )
        
        # Log de performance
        if self.settings['performance_tracking']:
            perf_data = {
                'operation': 'sql_analysis',
                'file_path': file_path,
                'statements_found': statements_found,
                'tables_found': tables_found,
                'duration_ms': execution_time_ms
            }
            self.perf_logger.info(json.dumps(perf_data, ensure_ascii=False))
    
    def log_table_matching(self, 
                          table_name: str, 
                          match_found: bool, 
                          confidence: float, 
                          match_type: str):
        """Log específico para matching de tabelas"""
        
        status = "MATCH" if match_found else "NO_MATCH"
        
        self.debug(
            f"Table matching: {status}",
            table=table_name,
            confidence=confidence,
            match_type=match_type
        )
        
        # Auditoria
        if self.settings['audit_enabled']:
            audit_data = {
                'event': 'table_matching',
                'table_name': table_name,
                'match_found': match_found,
                'confidence': confidence,
                'match_type': match_type,
                'timestamp': datetime.now().isoformat()
            }
            self.audit_logger.info(json.dumps(audit_data, ensure_ascii=False))
    
    def log_file_processing(self, 
                           file_path: str, 
                           lines_count: int, 
                           processing_time_ms: float, 
                           status: str = "SUCCESS"):
        """Log específico para processamento de arquivos"""
        
        self.info(
            f"Arquivo processado: {status}",
            file=file_path,
            lines=lines_count,
            duration_ms=processing_time_ms
        )
    
    def start_operation(self, operation_name: str, **context) -> str:
        """Inicia tracking de uma operação"""
        
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        operation_data = {
            'id': operation_id,
            'name': operation_name,
            'start_time': time.time(),
            'context': context
        }
        
        self.operation_stack.append(operation_data)
        
        self.debug(f"Operação iniciada: {operation_name}", operation_id=operation_id, **context)
        
        return operation_id
    
    def end_operation(self, operation_id: str, status: str = "SUCCESS", **result_context):
        """Finaliza tracking de uma operação"""
        
        # Busca operação na stack
        operation = None
        for i, op in enumerate(self.operation_stack):
            if op['id'] == operation_id:
                operation = self.operation_stack.pop(i)
                break
        
        if not operation:
            self.warning(f"Operação não encontrada: {operation_id}")
            return
        
        end_time = time.time()
        duration_ms = (end_time - operation['start_time']) * 1000
        
        self.info(
            f"Operação finalizada: {operation['name']} - {status}",
            operation_id=operation_id,
            duration_ms=round(duration_ms, 2),
            **result_context
        )
        
        # Adiciona métrica de performance
        if self.settings['performance_tracking']:
            try:
                import psutil
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
            except:
                memory_usage = 0
            
            metric = PerformanceMetric(
                operation=operation['name'],
                start_time=operation['start_time'],
                end_time=end_time,
                duration_ms=duration_ms,
                memory_usage_mb=memory_usage,
                context={**operation['context'], **result_context}
            )
            
            self.performance_metrics.append(metric)
            
            # Log performance
            perf_data = asdict(metric)
            self.perf_logger.info(json.dumps(perf_data, ensure_ascii=False, default=str))
    
    def log_validation_result(self, 
                             validation_name: str, 
                             is_valid: bool, 
                             message: str, 
                             **details):
        """Log específico para resultados de validação"""
        
        level = logging.INFO if is_valid else logging.ERROR
        status = "PASS" if is_valid else "FAIL"
        
        self._log_with_context(
            level,
            f"Validação {validation_name}: {status} - {message}",
            **details
        )
        
        # Auditoria de validação
        if self.settings['audit_enabled']:
            audit_data = {
                'event': 'validation',
                'validation_name': validation_name,
                'is_valid': is_valid,
                'message': message,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            self.audit_logger.info(json.dumps(audit_data, ensure_ascii=False))
    
    def log_configuration_change(self, 
                                config_key: str, 
                                old_value: Any, 
                                new_value: Any, 
                                source: str = "unknown"):
        """Log para mudanças de configuração"""
        
        self.info(
            f"Configuração alterada: {config_key}",
            old_value=old_value,
            new_value=new_value,
            source=source
        )
        
        # Auditoria
        if self.settings['audit_enabled']:
            audit_data = {
                'event': 'configuration_change',
                'config_key': config_key,
                'old_value': str(old_value),
                'new_value': str(new_value),
                'source': source,
                'timestamp': datetime.now().isoformat()
            }
            self.audit_logger.info(json.dumps(audit_data, ensure_ascii=False))
    
    def log_exception(self, 
                     exception: Exception, 
                     context: str = "", 
                     **additional_context):
        """Log detalhado de exceções"""
        
        exc_type = type(exception).__name__
        exc_message = str(exception)
        exc_traceback = traceback.format_exc()
        
        self.error(
            f"Exceção capturada: {exc_type} - {exc_message}",
            context=context,
            **additional_context
        )
        
        # Log completo em arquivo
        full_error_data = {
            'exception_type': exc_type,
            'exception_message': exc_message,
            'traceback': exc_traceback,
            'context': context,
            'additional_context': additional_context,
            'timestamp': datetime.now().isoformat()
        }
        
        error_file = self.log_dir / f"{self.name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(full_error_data, ensure_ascii=False, indent=2) + "\n")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Retorna resumo de performance"""
        
        if not self.performance_metrics:
            return {}
        
        operations = {}
        for metric in self.performance_metrics:
            op_name = metric.operation
            if op_name not in operations:
                operations[op_name] = {
                    'count': 0,
                    'total_duration_ms': 0,
                    'min_duration_ms': float('inf'),
                    'max_duration_ms': 0,
                    'avg_memory_mb': 0
                }
            
            op_stats = operations[op_name]
            op_stats['count'] += 1
            op_stats['total_duration_ms'] += metric.duration_ms
            op_stats['min_duration_ms'] = min(op_stats['min_duration_ms'], metric.duration_ms)
            op_stats['max_duration_ms'] = max(op_stats['max_duration_ms'], metric.duration_ms)
            op_stats['avg_memory_mb'] = (op_stats['avg_memory_mb'] + metric.memory_usage_mb) / 2
        
        # Calcula médias
        for op_stats in operations.values():
            op_stats['avg_duration_ms'] = op_stats['total_duration_ms'] / op_stats['count']
        
        return {
            'operations': operations,
            'total_operations': len(self.performance_metrics),
            'total_duration_ms': sum(m.duration_ms for m in self.performance_metrics),
            'analysis_period': {
                'start': min(m.start_time for m in self.performance_metrics),
                'end': max(m.end_time for m in self.performance_metrics)
            }
        }
    
    def export_logs_summary(self, output_path: str) -> str:
        """Exporta resumo dos logs para análise"""
        
        summary = {
            'logger_info': {
                'name': self.name,
                'log_level': self.settings['log_level'],
                'export_timestamp': datetime.now().isoformat()
            },
            'performance_summary': self.get_performance_summary(),
            'audit_events_count': len(self.audit_events),
            'log_files': [
                str(f) for f in self.log_dir.glob(f"{self.name}_*.log")
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        self.info(f"Resumo de logs exportado: {output_path}")
        return output_path
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Remove logs antigos"""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        for log_file in self.log_dir.glob(f"{self.name}_*.log*"):
            try:
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_date < cutoff_date:
                    log_file.unlink()
                    removed_count += 1
            except Exception as e:
                self.warning(f"Erro ao remover log antigo {log_file}: {e}")
        
        if removed_count > 0:
            self.info(f"Limpeza de logs: {removed_count} arquivos removidos")
    
    def set_context(self, **context):
        """Define contexto global para logs subsequentes"""
        
        # Adiciona filtro de contexto customizado
        class CustomContextFilter(logging.Filter):
            def __init__(self, context_data):
                self.context_data = context_data
            
            def filter(self, record):
                for key, value in self.context_data.items():
                    setattr(record, f"ctx_{key}", value)
                return True
        
        context_filter = CustomContextFilter(context)
        self.logger.addFilter(context_filter)
        
        self.debug("Contexto global definido", **context)
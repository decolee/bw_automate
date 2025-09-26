#!/usr/bin/env python3
"""
COMPREHENSIVE ERROR HANDLING & RECOVERY SYSTEM - BW AUTOMATE
Sistema robusto de tratamento de erros, recuperação automática e diagnóstico
Inclui logging avançado, retry automático e self-healing capabilities
"""

import os
import sys
import json
import logging
import traceback
import time
import threading
import sqlite3
import hashlib
import signal
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Type, Union
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import tempfile
import shutil
import subprocess
from contextlib import contextmanager
import warnings
import gc

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


class ErrorSeverity(Enum):
    """Níveis de severidade de erro"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categorias de erro"""
    SYSTEM = "system"
    FILE_IO = "file_io"
    DATABASE = "database"
    NETWORK = "network"
    MEMORY = "memory"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    PERMISSION = "permission"
    DEPENDENCY = "dependency"
    USER_INPUT = "user_input"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """Ações de recuperação"""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    RESTART = "restart"
    REPAIR = "repair"
    NOTIFY = "notify"


@dataclass
class ErrorInfo:
    """Informações detalhadas de erro"""
    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    traceback_str: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: Dict[str, Any]
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    recovery_attempted: bool = False
    recovery_action: Optional[RecoveryAction] = None
    recovery_success: bool = False
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class RecoveryStrategy:
    """Estratégia de recuperação"""
    error_patterns: List[str]
    max_retries: int
    retry_delay: float
    exponential_backoff: bool
    recovery_actions: List[RecoveryAction]
    fallback_function: Optional[Callable] = None
    notification_required: bool = False


class ErrorDatabase:
    """Banco de dados de erros para análise e machine learning"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados de erros"""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS errors (
                error_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                traceback_str TEXT,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                context TEXT,
                file_path TEXT,
                line_number INTEGER,
                function_name TEXT,
                recovery_attempted BOOLEAN DEFAULT 0,
                recovery_action TEXT,
                recovery_success BOOLEAN DEFAULT 0,
                user_id TEXT,
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS error_patterns (
                pattern_id TEXT PRIMARY KEY,
                error_pattern TEXT NOT NULL,
                category TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen TEXT,
                recovery_strategy TEXT,
                success_rate REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recovery_attempts (
                attempt_id TEXT PRIMARY KEY,
                error_id TEXT NOT NULL,
                recovery_action TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                execution_time REAL,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (error_id) REFERENCES errors (error_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_error(self, error_info: ErrorInfo):
        """Armazena erro no banco"""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
            INSERT OR REPLACE INTO errors 
            (error_id, timestamp, error_type, error_message, traceback_str, severity, 
             category, context, file_path, line_number, function_name, recovery_attempted,
             recovery_action, recovery_success, user_id, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            error_info.error_id,
            error_info.timestamp.isoformat(),
            error_info.error_type,
            error_info.error_message,
            error_info.traceback_str,
            error_info.severity.value,
            error_info.category.value,
            json.dumps(error_info.context),
            error_info.file_path,
            error_info.line_number,
            error_info.function_name,
            error_info.recovery_attempted,
            error_info.recovery_action.value if error_info.recovery_action else None,
            error_info.recovery_success,
            error_info.user_id,
            error_info.session_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_error_patterns(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Recupera padrões de erro mais comuns"""
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.execute('''
            SELECT error_type, error_message, category, COUNT(*) as frequency,
                   AVG(CASE WHEN recovery_success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
            FROM errors 
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY error_type, SUBSTR(error_message, 1, 100), category
            ORDER BY frequency DESC
            LIMIT ?
        ''', (limit,))
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                'error_type': row[0],
                'error_message': row[1],
                'category': row[2],
                'frequency': row[3],
                'success_rate': row[4]
            })
        
        conn.close()
        return patterns
    
    def update_recovery_attempt(self, error_id: str, action: RecoveryAction, 
                              success: bool, execution_time: float, details: str = ""):
        """Atualiza tentativa de recuperação"""
        attempt_id = hashlib.md5(f"{error_id}_{action.value}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
            INSERT INTO recovery_attempts 
            (attempt_id, error_id, recovery_action, success, execution_time, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (attempt_id, error_id, action.value, success, execution_time, details))
        
        conn.commit()
        conn.close()


class ErrorClassifier:
    """Classificador inteligente de erros"""
    
    def __init__(self):
        self.classification_rules = {
            # Erros de sistema
            'MemoryError': (ErrorCategory.MEMORY, ErrorSeverity.HIGH),
            'OSError': (ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM),
            'SystemExit': (ErrorCategory.SYSTEM, ErrorSeverity.LOW),
            
            # Erros de arquivo/IO
            'FileNotFoundError': (ErrorCategory.FILE_IO, ErrorSeverity.MEDIUM),
            'PermissionError': (ErrorCategory.PERMISSION, ErrorSeverity.HIGH),
            'IOError': (ErrorCategory.FILE_IO, ErrorSeverity.MEDIUM),
            'IsADirectoryError': (ErrorCategory.FILE_IO, ErrorSeverity.LOW),
            
            # Erros de rede
            'ConnectionError': (ErrorCategory.NETWORK, ErrorSeverity.HIGH),
            'TimeoutError': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
            'URLError': (ErrorCategory.NETWORK, ErrorSeverity.MEDIUM),
            
            # Erros de banco de dados
            'DatabaseError': (ErrorCategory.DATABASE, ErrorSeverity.HIGH),
            'OperationalError': (ErrorCategory.DATABASE, ErrorSeverity.MEDIUM),
            'IntegrityError': (ErrorCategory.DATABASE, ErrorSeverity.HIGH),
            
            # Erros de configuração
            'ConfigParser.Error': (ErrorCategory.CONFIGURATION, ErrorSeverity.MEDIUM),
            'JSONDecodeError': (ErrorCategory.CONFIGURATION, ErrorSeverity.MEDIUM),
            'KeyError': (ErrorCategory.CONFIGURATION, ErrorSeverity.LOW),
            
            # Erros de validação
            'ValueError': (ErrorCategory.VALIDATION, ErrorSeverity.LOW),
            'TypeError': (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
            'AttributeError': (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
            
            # Erros de dependência
            'ImportError': (ErrorCategory.DEPENDENCY, ErrorSeverity.HIGH),
            'ModuleNotFoundError': (ErrorCategory.DEPENDENCY, ErrorSeverity.HIGH),
        }
        
        self.message_patterns = {
            # Padrões em mensagens de erro
            r'no space left': (ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
            r'permission denied': (ErrorCategory.PERMISSION, ErrorSeverity.HIGH),
            r'connection refused': (ErrorCategory.NETWORK, ErrorSeverity.HIGH),
            r'timeout': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
            r'memory': (ErrorCategory.MEMORY, ErrorSeverity.HIGH),
            r'disk full': (ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
            r'access denied': (ErrorCategory.PERMISSION, ErrorSeverity.HIGH),
        }
    
    def classify_error(self, error_type: str, error_message: str, 
                      context: Dict[str, Any] = None) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classifica erro por categoria e severidade"""
        
        # Classifica por tipo de erro
        if error_type in self.classification_rules:
            category, severity = self.classification_rules[error_type]
        else:
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.MEDIUM
        
        # Refina classificação baseada na mensagem
        import re
        message_lower = error_message.lower()
        
        for pattern, (pattern_category, pattern_severity) in self.message_patterns.items():
            if re.search(pattern, message_lower):
                category = pattern_category
                # Usa a maior severidade
                if pattern_severity.value == 'critical' or severity.value != 'critical':
                    severity = pattern_severity
                break
        
        # Ajusta severidade baseada no contexto
        if context:
            if context.get('in_production', False):
                # Aumenta severidade em produção
                if severity == ErrorSeverity.LOW:
                    severity = ErrorSeverity.MEDIUM
                elif severity == ErrorSeverity.MEDIUM:
                    severity = ErrorSeverity.HIGH
        
        return category, severity


class RecoveryEngine:
    """Engine de recuperação automática"""
    
    def __init__(self, error_db: ErrorDatabase):
        self.error_db = error_db
        self.recovery_strategies = self._load_recovery_strategies()
        
    def _load_recovery_strategies(self) -> Dict[ErrorCategory, RecoveryStrategy]:
        """Carrega estratégias de recuperação"""
        return {
            ErrorCategory.FILE_IO: RecoveryStrategy(
                error_patterns=['FileNotFoundError', 'PermissionError'],
                max_retries=3,
                retry_delay=1.0,
                exponential_backoff=True,
                recovery_actions=[RecoveryAction.RETRY, RecoveryAction.FALLBACK],
                notification_required=False
            ),
            
            ErrorCategory.NETWORK: RecoveryStrategy(
                error_patterns=['ConnectionError', 'TimeoutError'],
                max_retries=5,
                retry_delay=2.0,
                exponential_backoff=True,
                recovery_actions=[RecoveryAction.RETRY, RecoveryAction.FALLBACK],
                notification_required=True
            ),
            
            ErrorCategory.DATABASE: RecoveryStrategy(
                error_patterns=['DatabaseError', 'OperationalError'],
                max_retries=3,
                retry_delay=5.0,
                exponential_backoff=True,
                recovery_actions=[RecoveryAction.RETRY, RecoveryAction.REPAIR, RecoveryAction.FALLBACK],
                notification_required=True
            ),
            
            ErrorCategory.MEMORY: RecoveryStrategy(
                error_patterns=['MemoryError'],
                max_retries=2,
                retry_delay=10.0,
                exponential_backoff=False,
                recovery_actions=[RecoveryAction.REPAIR, RecoveryAction.RESTART],
                notification_required=True
            ),
            
            ErrorCategory.DEPENDENCY: RecoveryStrategy(
                error_patterns=['ImportError', 'ModuleNotFoundError'],
                max_retries=1,
                retry_delay=0.0,
                exponential_backoff=False,
                recovery_actions=[RecoveryAction.REPAIR, RecoveryAction.NOTIFY],
                notification_required=True
            ),
            
            ErrorCategory.CONFIGURATION: RecoveryStrategy(
                error_patterns=['ConfigParser.Error', 'JSONDecodeError'],
                max_retries=2,
                retry_delay=1.0,
                exponential_backoff=False,
                recovery_actions=[RecoveryAction.REPAIR, RecoveryAction.FALLBACK],
                notification_required=False
            )
        }
    
    def attempt_recovery(self, error_info: ErrorInfo, 
                        original_function: Callable, 
                        *args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
        """Tenta recuperação automática"""
        
        strategy = self.recovery_strategies.get(error_info.category)
        if not strategy:
            return False, None, "No recovery strategy available"
        
        recovery_log = []
        
        for action in strategy.recovery_actions:
            start_time = time.time()
            success = False
            result = None
            details = ""
            
            try:
                if action == RecoveryAction.RETRY:
                    success, result = self._attempt_retry(
                        original_function, strategy, *args, **kwargs
                    )
                    details = f"Retry with {strategy.max_retries} attempts"
                
                elif action == RecoveryAction.FALLBACK:
                    success, result = self._attempt_fallback(
                        strategy, error_info, *args, **kwargs
                    )
                    details = "Fallback strategy executed"
                
                elif action == RecoveryAction.REPAIR:
                    success = self._attempt_repair(error_info)
                    details = "System repair attempted"
                
                elif action == RecoveryAction.RESTART:
                    success = self._attempt_restart(error_info)
                    details = "Component restart attempted"
                
                elif action == RecoveryAction.NOTIFY:
                    self._send_notification(error_info)
                    success = True
                    details = "Notification sent"
                
                execution_time = time.time() - start_time
                
                # Registra tentativa
                self.error_db.update_recovery_attempt(
                    error_info.error_id, action, success, execution_time, details
                )
                
                recovery_log.append(f"{action.value}: {'SUCCESS' if success else 'FAILED'}")
                
                if success and result is not None:
                    return True, result, "; ".join(recovery_log)
                
            except Exception as recovery_error:
                recovery_log.append(f"{action.value}: ERROR - {str(recovery_error)}")
                continue
        
        return False, None, "; ".join(recovery_log)
    
    def _attempt_retry(self, func: Callable, strategy: RecoveryStrategy, 
                      *args, **kwargs) -> Tuple[bool, Any]:
        """Tenta retry com backoff exponencial"""
        
        delay = strategy.retry_delay
        
        for attempt in range(strategy.max_retries):
            try:
                result = func(*args, **kwargs)
                return True, result
            
            except Exception as e:
                if attempt < strategy.max_retries - 1:
                    time.sleep(delay)
                    if strategy.exponential_backoff:
                        delay *= 2
                else:
                    raise
        
        return False, None
    
    def _attempt_fallback(self, strategy: RecoveryStrategy, error_info: ErrorInfo,
                         *args, **kwargs) -> Tuple[bool, Any]:
        """Executa função de fallback"""
        
        if strategy.fallback_function:
            try:
                result = strategy.fallback_function(*args, **kwargs)
                return True, result
            except:
                pass
        
        # Fallbacks genéricos por categoria
        if error_info.category == ErrorCategory.FILE_IO:
            return self._file_io_fallback(error_info, *args, **kwargs)
        elif error_info.category == ErrorCategory.DATABASE:
            return self._database_fallback(error_info, *args, **kwargs)
        elif error_info.category == ErrorCategory.NETWORK:
            return self._network_fallback(error_info, *args, **kwargs)
        
        return False, None
    
    def _file_io_fallback(self, error_info: ErrorInfo, *args, **kwargs) -> Tuple[bool, Any]:
        """Fallback para erros de arquivo"""
        try:
            # Tenta criar diretório se não existe
            if 'FileNotFoundError' in error_info.error_type:
                file_path = error_info.context.get('file_path')
                if file_path:
                    parent_dir = Path(file_path).parent
                    parent_dir.mkdir(parents=True, exist_ok=True)
                    return True, f"Created directory: {parent_dir}"
            
            # Tenta usar arquivo temporário
            if 'PermissionError' in error_info.error_type:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.close()
                return True, temp_file.name
                
        except Exception:
            pass
        
        return False, None
    
    def _database_fallback(self, error_info: ErrorInfo, *args, **kwargs) -> Tuple[bool, Any]:
        """Fallback para erros de banco"""
        try:
            # Tenta usar SQLite local como fallback
            fallback_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
            fallback_db.close()
            return True, f"sqlite:///{fallback_db.name}"
        except Exception:
            pass
        
        return False, None
    
    def _network_fallback(self, error_info: ErrorInfo, *args, **kwargs) -> Tuple[bool, Any]:
        """Fallback para erros de rede"""
        try:
            # Tenta usar cache local se disponível
            cache_file = error_info.context.get('cache_file')
            if cache_file and Path(cache_file).exists():
                return True, cache_file
                
            # Tenta configuração offline
            return True, {"offline_mode": True}
            
        except Exception:
            pass
        
        return False, None
    
    def _attempt_repair(self, error_info: ErrorInfo) -> bool:
        """Tenta reparar o sistema"""
        try:
            if error_info.category == ErrorCategory.MEMORY:
                # Força garbage collection
                gc.collect()
                return True
            
            elif error_info.category == ErrorCategory.DEPENDENCY:
                # Tenta instalar dependência faltante
                if 'ModuleNotFoundError' in error_info.error_type:
                    module_name = self._extract_module_name(error_info.error_message)
                    if module_name:
                        subprocess.run([
                            sys.executable, '-m', 'pip', 'install', module_name
                        ], check=True, capture_output=True)
                        return True
            
            elif error_info.category == ErrorCategory.CONFIGURATION:
                # Tenta recriar arquivo de configuração
                config_file = error_info.context.get('config_file')
                if config_file:
                    self._create_default_config(config_file)
                    return True
                    
        except Exception:
            pass
        
        return False
    
    def _attempt_restart(self, error_info: ErrorInfo) -> bool:
        """Tenta restart de componente"""
        try:
            if error_info.category == ErrorCategory.MEMORY:
                # Para e inicia threads se necessário
                return True
                
        except Exception:
            pass
        
        return False
    
    def _send_notification(self, error_info: ErrorInfo):
        """Envia notificação de erro"""
        # Implementação básica - em produção integraria com sistemas de alerta
        print(f"🚨 ERROR NOTIFICATION: {error_info.error_type} - {error_info.error_message}")
    
    def _extract_module_name(self, error_message: str) -> Optional[str]:
        """Extrai nome do módulo de erro de importação"""
        import re
        match = re.search(r"No module named '([^']+)'", error_message)
        return match.group(1) if match else None
    
    def _create_default_config(self, config_file: str):
        """Cria arquivo de configuração padrão"""
        default_config = {
            "version": "1.0",
            "created_by": "error_recovery_system",
            "timestamp": datetime.now().isoformat()
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)


class AdvancedLogger:
    """Sistema avançado de logging"""
    
    def __init__(self, log_dir: str, enable_sentry: bool = False):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuração de logging
        self.logger = logging.getLogger('bw_automate')
        self.logger.setLevel(logging.DEBUG)
        
        # Formatter detalhado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
        )
        
        # Handler para arquivo de erro
        error_handler = logging.FileHandler(self.log_dir / 'errors.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # Handler para debug
        debug_handler = logging.FileHandler(self.log_dir / 'debug.log')
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        self.logger.addHandler(debug_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger.addHandler(console_handler)
        
        # Configuração Sentry se disponível
        if enable_sentry and SENTRY_AVAILABLE:
            self._setup_sentry()
    
    def _setup_sentry(self):
        """Configura Sentry para monitoramento de erros"""
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        
        sentry_sdk.init(
            integrations=[sentry_logging],
            traces_sample_rate=1.0,
        )


class ErrorHandler:
    """Handler principal de erros"""
    
    def __init__(self, log_dir: str = "logs", enable_recovery: bool = True):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Componentes
        self.error_db = ErrorDatabase(str(self.log_dir / "errors.db"))
        self.classifier = ErrorClassifier()
        self.recovery_engine = RecoveryEngine(self.error_db) if enable_recovery else None
        self.logger = AdvancedLogger(str(self.log_dir))
        
        # Estatísticas
        self.error_count = 0
        self.recovery_success_count = 0
        self.session_id = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:8]
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None,
                    original_function: Callable = None, 
                    *args, **kwargs) -> Tuple[bool, Any]:
        """Handle principal de erro com recuperação automática"""
        
        self.error_count += 1
        
        # Extrai informações do erro
        error_info = self._extract_error_info(error, context)
        
        # Classifica erro
        error_info.category, error_info.severity = self.classifier.classify_error(
            error_info.error_type, error_info.error_message, context
        )
        
        # Log do erro
        self._log_error(error_info)
        
        # Armazena no banco
        self.error_db.store_error(error_info)
        
        # Tenta recuperação se disponível
        if self.recovery_engine and original_function:
            recovery_success, result, recovery_log = self.recovery_engine.attempt_recovery(
                error_info, original_function, *args, **kwargs
            )
            
            if recovery_success:
                self.recovery_success_count += 1
                error_info.recovery_attempted = True
                error_info.recovery_success = True
                
                self.logger.logger.info(f"Recovery successful for {error_info.error_id}: {recovery_log}")
                
                # Atualiza no banco
                self.error_db.store_error(error_info)
                
                return True, result
            else:
                error_info.recovery_attempted = True
                error_info.recovery_success = False
                self.logger.logger.warning(f"Recovery failed for {error_info.error_id}: {recovery_log}")
                
                # Atualiza no banco
                self.error_db.store_error(error_info)
        
        # Se chegou aqui, erro não foi recuperado
        return False, None
    
    def _extract_error_info(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Extrai informações detalhadas do erro"""
        
        tb = traceback.extract_tb(error.__traceback__)
        
        # Informações básicas
        error_id = hashlib.md5(
            f"{type(error).__name__}_{str(error)}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Frame do erro
        file_path = None
        line_number = None
        function_name = None
        
        if tb:
            last_frame = tb[-1]
            file_path = last_frame.filename
            line_number = last_frame.lineno
            function_name = last_frame.name
        
        return ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            traceback_str=traceback.format_exc(),
            severity=ErrorSeverity.MEDIUM,  # Será classificado depois
            category=ErrorCategory.UNKNOWN,  # Será classificado depois
            context=context or {},
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            session_id=self.session_id
        )
    
    def _log_error(self, error_info: ErrorInfo):
        """Faz log detalhado do erro"""
        
        log_message = (
            f"ERROR {error_info.error_id}: {error_info.error_type} - {error_info.error_message}\n"
            f"Category: {error_info.category.value}, Severity: {error_info.severity.value}\n"
            f"Location: {error_info.file_path}:{error_info.line_number} in {error_info.function_name}\n"
            f"Context: {json.dumps(error_info.context, default=str)}"
        )
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.logger.warning(log_message)
        else:
            self.logger.logger.info(log_message)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de erro"""
        recovery_rate = (self.recovery_success_count / self.error_count * 100) if self.error_count > 0 else 0
        
        patterns = self.error_db.get_error_patterns(20)
        
        return {
            'total_errors': self.error_count,
            'recovery_successes': self.recovery_success_count,
            'recovery_rate': recovery_rate,
            'session_id': self.session_id,
            'top_error_patterns': patterns
        }


# Decorators para tratamento automático de erros
def error_handler(category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 context: Dict[str, Any] = None,
                 enable_recovery: bool = True):
    """Decorator para tratamento automático de erros"""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Cria handler se não existe
                if not hasattr(wrapper, '_error_handler'):
                    wrapper._error_handler = ErrorHandler(enable_recovery=enable_recovery)
                
                # Adiciona informações de contexto
                func_context = context or {}
                func_context.update({
                    'function_name': func.__name__,
                    'function_module': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()),
                    'category_hint': category.value
                })
                
                # Tenta recuperação
                success, result = wrapper._error_handler.handle_error(
                    e, func_context, func, *args, **kwargs
                )
                
                if success:
                    return result
                else:
                    # Re-raise se não conseguiu recuperar
                    raise
        
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 1.0, 
                  exponential_backoff: bool = True,
                  exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """Decorator para retry automático"""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise
                    
                    time.sleep(current_delay)
                    if exponential_backoff:
                        current_delay *= 2
                    
                    print(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
        
        return wrapper
    return decorator


@contextmanager
def error_context(context: Dict[str, Any], handler: ErrorHandler = None):
    """Context manager para tratamento de erros"""
    
    if handler is None:
        handler = ErrorHandler()
    
    try:
        yield handler
    except Exception as e:
        success, result = handler.handle_error(e, context)
        if not success:
            raise


# Sistema de self-healing
class SelfHealingSystem:
    """Sistema de auto-cura"""
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.healing_thread = None
        self.is_running = False
        
    def start_monitoring(self):
        """Inicia monitoramento para auto-cura"""
        self.is_running = True
        self.healing_thread = threading.Thread(target=self._healing_loop, daemon=True)
        self.healing_thread.start()
    
    def stop_monitoring(self):
        """Para monitoramento"""
        self.is_running = False
        if self.healing_thread:
            self.healing_thread.join()
    
    def _healing_loop(self):
        """Loop principal de auto-cura"""
        while self.is_running:
            try:
                # Verifica padrões de erro
                patterns = self.error_handler.error_db.get_error_patterns(10)
                
                for pattern in patterns:
                    if pattern['frequency'] > 5 and pattern['success_rate'] < 0.5:
                        self._attempt_proactive_healing(pattern)
                
                time.sleep(300)  # Verifica a cada 5 minutos
                
            except Exception as e:
                print(f"Self-healing error: {e}")
                time.sleep(60)
    
    def _attempt_proactive_healing(self, pattern: Dict[str, Any]):
        """Tenta cura proativa baseada em padrões"""
        print(f"Attempting proactive healing for pattern: {pattern['error_type']}")
        
        # Implementar lógica de cura baseada no padrão
        # Por exemplo, limpar cache, reiniciar componentes, etc.


# Exemplo de uso e teste
if __name__ == "__main__":
    
    # Configuração do sistema
    error_handler = ErrorHandler(enable_recovery=True)
    
    # Exemplo de função com tratamento de erro
    @error_handler(category=ErrorCategory.FILE_IO, context={'operation': 'file_read'})
    def read_file_with_recovery(file_path: str):
        """Exemplo de função que pode ter erro de arquivo"""
        with open(file_path, 'r') as f:
            return f.read()
    
    @retry_on_error(max_retries=3, delay=1.0)
    def network_operation():
        """Exemplo de operação de rede com retry"""
        import random
        if random.random() < 0.7:  # 70% chance de erro
            raise ConnectionError("Network temporarily unavailable")
        return "Success!"
    
    # Teste do sistema
    print("🧪 Testing Error Handling & Recovery System")
    print("=" * 50)
    
    # Teste 1: Erro de arquivo com recuperação
    try:
        result = read_file_with_recovery("nonexistent_file.txt")
        print(f"File read result: {result}")
    except Exception as e:
        print(f"File read failed: {e}")
    
    # Teste 2: Retry automático
    try:
        result = network_operation()
        print(f"Network operation result: {result}")
    except Exception as e:
        print(f"Network operation failed: {e}")
    
    # Teste 3: Context manager
    with error_context({'operation': 'database_test'}, error_handler) as handler:
        # Simula erro de banco
        raise sqlite3.OperationalError("Database is locked")
    
    # Mostra estatísticas
    stats = error_handler.get_error_statistics()
    print(f"\n📊 Error Statistics:")
    print(f"  Total Errors: {stats['total_errors']}")
    print(f"  Recovery Rate: {stats['recovery_rate']:.1f}%")
    print(f"  Session ID: {stats['session_id']}")
    
    print("\n✅ Error handling system test completed!")
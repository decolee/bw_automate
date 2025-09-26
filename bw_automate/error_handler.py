#!/usr/bin/env python3
"""
BW_AUTOMATE - Error Handler Module
=================================

Sistema robusto de tratamento de erros, logging e recuperação para o BW_AUTOMATE.

Autor: Assistant Claude
Data: 2025-09-20
"""

import sys
import os
import traceback
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
from datetime import datetime
import json


class BWError(Exception):
    """Erro base do BW_AUTOMATE"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "BW_GENERIC"
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)


class ValidationError(BWError):
    """Erro de validação de dados"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        super().__init__(message, "BW_VALIDATION", details)


class ConfigurationError(BWError):
    """Erro de configuração"""
    def __init__(self, message: str, config_key: str = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        super().__init__(message, "BW_CONFIG", details)


class FileOperationError(BWError):
    """Erro de operação de arquivo"""
    def __init__(self, message: str, file_path: str = None, operation: str = None):
        details = {}
        if file_path:
            details['file_path'] = file_path
        if operation:
            details['operation'] = operation
        super().__init__(message, "BW_FILE_OP", details)


class DependencyError(BWError):
    """Erro de dependência faltando"""
    def __init__(self, message: str, missing_package: str = None):
        details = {}
        if missing_package:
            details['missing_package'] = missing_package
        super().__init__(message, "BW_DEPENDENCY", details)


class AnalysisError(BWError):
    """Erro durante análise de código"""
    def __init__(self, message: str, file_path: str = None, line_number: int = None):
        details = {}
        if file_path:
            details['file_path'] = file_path
        if line_number:
            details['line_number'] = line_number
        super().__init__(message, "BW_ANALYSIS", details)


class ErrorHandler:
    """Gerenciador central de erros do BW_AUTOMATE"""
    
    def __init__(self, log_file: str = None, verbose: bool = False):
        self.verbose = verbose
        self.errors_log = []
        self.warnings_log = []
        
        # Configura logging
        self.setup_logging(log_file)
    
    def setup_logging(self, log_file: str = None):
        """Configura sistema de logging"""
        self.logger = logging.getLogger('BW_AUTOMATE_ERRORS')
        self.logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Remove handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler se especificado
        if log_file:
            try:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception:
                pass  # Falha silenciosa se não conseguir criar arquivo de log
    
    def handle_error(self, 
                    error: Exception, 
                    context: str = None,
                    critical: bool = False,
                    raise_error: bool = True) -> Optional[Dict]:
        """
        Trata erro de forma centralizada
        
        Args:
            error: Exceção capturada
            context: Contexto onde o erro ocorreu
            critical: Se é erro crítico que para execução
            raise_error: Se deve re-levantar o erro
            
        Returns:
            Dicionário com informações do erro ou None
        """
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc() if self.verbose else None,
            'critical': critical
        }
        
        # Adiciona detalhes específicos do BW_AUTOMATE
        if isinstance(error, BWError):
            error_info.update({
                'error_code': error.error_code,
                'details': error.details
            })
        
        # Log do erro
        log_message = f"[{context or 'UNKNOWN'}] {error_info['type']}: {error_info['message']}"
        
        if critical:
            self.logger.critical(log_message)
        else:
            self.logger.error(log_message)
        
        # Armazena erro
        self.errors_log.append(error_info)
        
        # Se verbose, imprime traceback
        if self.verbose:
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Re-levanta erro se solicitado
        if raise_error:
            raise error
        
        return error_info
    
    def handle_warning(self, message: str, context: str = None):
        """Trata warning"""
        warning_info = {
            'message': message,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        self.warnings_log.append(warning_info)
        self.logger.warning(f"[{context or 'UNKNOWN'}] {message}")
    
    def get_error_summary(self) -> Dict:
        """Retorna resumo de erros e warnings"""
        return {
            'total_errors': len(self.errors_log),
            'total_warnings': len(self.warnings_log),
            'critical_errors': len([e for e in self.errors_log if e.get('critical', False)]),
            'errors': self.errors_log[-10:],  # Últimos 10 erros
            'warnings': self.warnings_log[-10:]  # Últimos 10 warnings
        }
    
    def save_error_log(self, file_path: str):
        """Salva log de erros em arquivo JSON"""
        try:
            error_report = {
                'timestamp': datetime.now().isoformat(),
                'summary': self.get_error_summary(),
                'all_errors': self.errors_log,
                'all_warnings': self.warnings_log
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(error_report, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar log de erros: {e}")


# Instância global do error handler
error_handler = ErrorHandler()


def safe_execute(func: Callable, 
                *args, 
                context: str = None,
                default_return: Any = None,
                log_errors: bool = True,
                **kwargs) -> Any:
    """
    Executa função de forma segura com tratamento de erro
    
    Args:
        func: Função a executar
        *args: Argumentos posicionais
        context: Contexto para logging
        default_return: Valor retornado em caso de erro
        log_errors: Se deve logar erros
        **kwargs: Argumentos nomeados
        
    Returns:
        Resultado da função ou default_return em caso de erro
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            error_handler.handle_error(
                e, 
                context=context or func.__name__,
                raise_error=False
            )
        return default_return


def retry_on_error(max_retries: int = 3, 
                   delay: float = 1.0,
                   backoff_factor: float = 2.0,
                   exceptions: tuple = (Exception,)):
    """
    Decorator para retry automático em caso de erro
    
    Args:
        max_retries: Número máximo de tentativas
        delay: Delay inicial entre tentativas
        backoff_factor: Fator de multiplicação do delay
        exceptions: Tupla de exceções para retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        error_handler.handle_warning(
                            f"Tentativa {attempt + 1} falhou para {func.__name__}: {e}. "
                            f"Tentando novamente em {current_delay}s...",
                            context="RETRY"
                        )
                        
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        # Última tentativa falhou
                        error_handler.handle_error(
                            e,
                            context=f"{func.__name__}_RETRY_FAILED",
                            raise_error=True
                        )
            
            # Nunca deveria chegar aqui, mas por segurança
            raise last_exception
        
        return wrapper
    return decorator


def validate_input(validation_func: Callable, 
                  error_message: str = None,
                  field_name: str = None):
    """
    Decorator para validação de entrada
    
    Args:
        validation_func: Função que retorna True se válida
        error_message: Mensagem de erro customizada
        field_name: Nome do campo sendo validado
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Valida argumentos
            for i, arg in enumerate(args):
                if not validation_func(arg):
                    raise ValidationError(
                        error_message or f"Validação falhou para argumento {i}",
                        field=field_name or f"arg_{i}",
                        value=arg
                    )
            
            # Valida kwargs
            for key, value in kwargs.items():
                if not validation_func(value):
                    raise ValidationError(
                        error_message or f"Validação falhou para {key}",
                        field=field_name or key,
                        value=value
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """Decorator para logar tempo de execução"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            error_handler.logger.info(
                f"{func.__name__} executado em {execution_time:.2f}s"
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_handler.handle_error(
                e,
                context=f"{func.__name__}_TIMED ({execution_time:.2f}s)",
                raise_error=True
            )
    
    return wrapper


# Validadores comuns
def is_valid_file_path(path: str) -> bool:
    """Valida se é um caminho de arquivo válido"""
    return isinstance(path, str) and len(path.strip()) > 0


def is_valid_directory(path: str) -> bool:
    """Valida se é um diretório válido"""
    return isinstance(path, str) and os.path.isdir(path)


def is_valid_excel_file(path: str) -> bool:
    """Valida se é um arquivo Excel válido"""
    return (isinstance(path, str) and 
            os.path.isfile(path) and 
            path.lower().endswith(('.xlsx', '.xls')))


def is_valid_config(config: Dict) -> bool:
    """Valida configuração básica"""
    return isinstance(config, dict) and len(config) > 0


# Context managers para tratamento de erro
class ErrorContext:
    """Context manager para captura de erros em blocos de código"""
    
    def __init__(self, context_name: str, critical: bool = False):
        self.context_name = context_name
        self.critical = critical
        self.errors = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback_obj):
        if exc_value:
            error_info = error_handler.handle_error(
                exc_value,
                context=self.context_name,
                critical=self.critical,
                raise_error=False
            )
            self.errors.append(error_info)
            
            # Suprime erro se não for crítico
            return not self.critical
        return False


if __name__ == "__main__":
    # Teste do sistema de tratamento de erros
    print("🛡️ BW_AUTOMATE Error Handler - Teste")
    print("=" * 40)
    
    # Teste de erro básico
    try:
        raise ValidationError("Teste de validação", field="test_field", value="invalid")
    except BWError as e:
        print(f"✅ Erro capturado: {e.error_code} - {e.message}")
    
    # Teste de context manager
    with ErrorContext("TESTE_CONTEXT") as ctx:
        error_handler.handle_warning("Teste de warning", "TEST")
    
    print(f"✅ Warnings: {len(error_handler.warnings_log)}")
    
    # Teste de execução segura
    result = safe_execute(
        lambda x: x / 0,
        10,
        context="DIVISION_TEST",
        default_return="ERRO"
    )
    print(f"✅ Execução segura: {result}")
    
    # Resumo de erros
    summary = error_handler.get_error_summary()
    print(f"✅ Resumo: {summary['total_errors']} erros, {summary['total_warnings']} warnings")
    
    print("\n🎯 Sistema de tratamento de erros funcionando!")
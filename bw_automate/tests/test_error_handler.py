#!/usr/bin/env python3
"""
BW_AUTOMATE - Testes para Error Handler
======================================

Testes unitários para o módulo error_handler.py

Autor: Assistant Claude
Data: 2025-09-20
"""

import unittest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from error_handler import (
    BWError, ValidationError, ConfigurationError, 
    FileOperationError, DependencyError, AnalysisError,
    ErrorHandler, safe_execute, retry_on_error,
    validate_input, ErrorContext
)


class TestBWErrors(unittest.TestCase):
    """Testes para classes de erro customizadas"""
    
    def test_bw_error_basic(self):
        """Testa erro básico BWError"""
        error = BWError("Teste de erro", "TEST_CODE", {"key": "value"})
        
        self.assertEqual(error.message, "Teste de erro")
        self.assertEqual(error.error_code, "TEST_CODE")
        self.assertEqual(error.details["key"], "value")
        self.assertIsNotNone(error.timestamp)
    
    def test_validation_error(self):
        """Testa ValidationError"""
        error = ValidationError("Campo inválido", field="test_field", value="invalid")
        
        self.assertEqual(error.error_code, "BW_VALIDATION")
        self.assertEqual(error.details["field"], "test_field")
        self.assertEqual(error.details["value"], "invalid")
    
    def test_configuration_error(self):
        """Testa ConfigurationError"""
        error = ConfigurationError("Config inválida", config_key="invalid_key")
        
        self.assertEqual(error.error_code, "BW_CONFIG")
        self.assertEqual(error.details["config_key"], "invalid_key")
    
    def test_file_operation_error(self):
        """Testa FileOperationError"""
        error = FileOperationError("Erro de arquivo", file_path="/test/path", operation="read")
        
        self.assertEqual(error.error_code, "BW_FILE_OP")
        self.assertEqual(error.details["file_path"], "/test/path")
        self.assertEqual(error.details["operation"], "read")
    
    def test_dependency_error(self):
        """Testa DependencyError"""
        error = DependencyError("Pacote faltando", missing_package="test_package")
        
        self.assertEqual(error.error_code, "BW_DEPENDENCY")
        self.assertEqual(error.details["missing_package"], "test_package")
    
    def test_analysis_error(self):
        """Testa AnalysisError"""
        error = AnalysisError("Erro na análise", file_path="/test.py", line_number=42)
        
        self.assertEqual(error.error_code, "BW_ANALYSIS")
        self.assertEqual(error.details["file_path"], "/test.py")
        self.assertEqual(error.details["line_number"], 42)


class TestErrorHandler(unittest.TestCase):
    """Testes para ErrorHandler"""
    
    def setUp(self):
        """Configura teste"""
        self.error_handler = ErrorHandler(verbose=True)
    
    def test_error_handler_creation(self):
        """Testa criação do ErrorHandler"""
        self.assertIsNotNone(self.error_handler)
        self.assertEqual(len(self.error_handler.errors_log), 0)
        self.assertEqual(len(self.error_handler.warnings_log), 0)
    
    def test_handle_error(self):
        """Testa tratamento de erro"""
        test_error = ValueError("Teste de erro")
        
        # Teste sem re-levantar erro
        error_info = self.error_handler.handle_error(
            test_error, 
            context="TEST_CONTEXT",
            raise_error=False
        )
        
        self.assertIsNotNone(error_info)
        self.assertEqual(error_info['type'], 'ValueError')
        self.assertEqual(error_info['message'], 'Teste de erro')
        self.assertEqual(error_info['context'], 'TEST_CONTEXT')
        self.assertEqual(len(self.error_handler.errors_log), 1)
    
    def test_handle_warning(self):
        """Testa tratamento de warning"""
        self.error_handler.handle_warning("Teste de warning", "TEST_CONTEXT")
        
        self.assertEqual(len(self.error_handler.warnings_log), 1)
        warning = self.error_handler.warnings_log[0]
        self.assertEqual(warning['message'], "Teste de warning")
        self.assertEqual(warning['context'], "TEST_CONTEXT")
    
    def test_get_error_summary(self):
        """Testa geração de resumo de erros"""
        # Adiciona alguns erros e warnings
        self.error_handler.handle_error(
            ValueError("Erro 1"), 
            context="TEST", 
            raise_error=False
        )
        self.error_handler.handle_warning("Warning 1", "TEST")
        
        summary = self.error_handler.get_error_summary()
        
        self.assertEqual(summary['total_errors'], 1)
        self.assertEqual(summary['total_warnings'], 1)
        self.assertEqual(summary['critical_errors'], 0)
    
    def test_save_error_log(self):
        """Testa salvamento de log de erros"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            log_file = f.name
        
        try:
            # Adiciona erro
            self.error_handler.handle_error(
                ValueError("Teste"), 
                context="TEST", 
                raise_error=False
            )
            
            # Salva log
            self.error_handler.save_error_log(log_file)
            
            # Verifica se arquivo foi criado e contém dados válidos
            self.assertTrue(os.path.exists(log_file))
            
            with open(log_file, 'r') as f:
                data = json.load(f)
            
            self.assertIn('timestamp', data)
            self.assertIn('summary', data)
            self.assertIn('all_errors', data)
            
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)


class TestSafeExecute(unittest.TestCase):
    """Testes para safe_execute"""
    
    def test_safe_execute_success(self):
        """Testa execução bem-sucedida"""
        result = safe_execute(lambda x: x * 2, 5)
        self.assertEqual(result, 10)
    
    def test_safe_execute_error(self):
        """Testa execução com erro"""
        result = safe_execute(
            lambda x: x / 0, 
            5,
            default_return="ERRO",
            log_errors=False
        )
        self.assertEqual(result, "ERRO")
    
    def test_safe_execute_with_context(self):
        """Testa execução com contexto"""
        result = safe_execute(
            lambda: 1/0,
            context="DIVISION_TEST",
            default_return=None,
            log_errors=False
        )
        self.assertIsNone(result)


class TestRetryDecorator(unittest.TestCase):
    """Testes para decorator retry_on_error"""
    
    def test_retry_success_first_try(self):
        """Testa sucesso na primeira tentativa"""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 1)
    
    def test_retry_success_after_retries(self):
        """Testa sucesso após algumas tentativas"""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = test_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_retry_failure_max_retries(self):
        """Testa falha após máximo de tentativas"""
        call_count = 0
        
        @retry_on_error(max_retries=2, delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")
        
        with self.assertRaises(ValueError):
            test_func()
        
        self.assertEqual(call_count, 3)  # 1 tentativa inicial + 2 retries


class TestValidateInputDecorator(unittest.TestCase):
    """Testes para decorator validate_input"""
    
    def test_validate_input_success(self):
        """Testa validação bem-sucedida"""
        @validate_input(lambda x: isinstance(x, int))
        def test_func(value):
            return value * 2
        
        result = test_func(5)
        self.assertEqual(result, 10)
    
    def test_validate_input_failure(self):
        """Testa falha na validação"""
        @validate_input(lambda x: isinstance(x, int))
        def test_func(value):
            return value * 2
        
        with self.assertRaises(ValidationError):
            test_func("not an int")


class TestErrorContext(unittest.TestCase):
    """Testes para ErrorContext"""
    
    def test_error_context_no_error(self):
        """Testa context sem erro"""
        with ErrorContext("TEST_CONTEXT") as ctx:
            result = 2 + 2
        
        self.assertEqual(len(ctx.errors), 0)
    
    def test_error_context_with_error(self):
        """Testa context com erro"""
        with ErrorContext("TEST_CONTEXT") as ctx:
            raise ValueError("Test error")
        
        self.assertEqual(len(ctx.errors), 1)
    
    def test_error_context_critical(self):
        """Testa context com erro crítico"""
        with self.assertRaises(ValueError):
            with ErrorContext("TEST_CONTEXT", critical=True) as ctx:
                raise ValueError("Critical error")


if __name__ == '__main__':
    # Executa os testes
    unittest.main(verbosity=2)
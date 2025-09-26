#!/usr/bin/env python3
"""
BW_AUTOMATE - Testes para Utils
==============================

Testes unitários para o módulo utils.py

Autor: Assistant Claude
Data: 2025-09-20
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import (
    OptionalImport, SafeLogger, safe_import_check, 
    get_missing_dependencies, validate_python_version,
    ensure_directory, memory_usage_mb, format_bytes,
    PerformanceMonitor
)


class TestOptionalImport(unittest.TestCase):
    """Testes para OptionalImport"""
    
    def test_available_module(self):
        """Testa módulo disponível"""
        # Testa com módulo built-in que sempre existe
        opt_import = OptionalImport('os')
        self.assertTrue(opt_import.available)
        self.assertIsNotNone(opt_import.module)
    
    def test_unavailable_module(self):
        """Testa módulo não disponível"""
        opt_import = OptionalImport('nonexistent_module_xyz')
        self.assertFalse(opt_import.available)
        
        with self.assertRaises(ImportError):
            _ = opt_import.module
    
    def test_error_message(self):
        """Testa mensagem de erro customizada"""
        custom_msg = "Instale o módulo XYZ"
        opt_import = OptionalImport('nonexistent_module', error_msg=custom_msg)
        
        with self.assertRaises(ImportError) as cm:
            _ = opt_import.module
        
        self.assertIn(custom_msg, str(cm.exception))


class TestSafeLogger(unittest.TestCase):
    """Testes para SafeLogger"""
    
    def test_logger_creation(self):
        """Testa criação do logger"""
        logger = SafeLogger('test')
        self.assertIsNotNone(logger)
    
    def test_logging_methods(self):
        """Testa métodos de logging"""
        logger = SafeLogger('test')
        
        # Não deve gerar exceção
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")


class TestUtilityFunctions(unittest.TestCase):
    """Testes para funções utilitárias"""
    
    def test_validate_python_version(self):
        """Testa validação de versão Python"""
        # Versão atual sempre deve ser >= 3.0
        self.assertTrue(validate_python_version((3, 0)))
        
        # Versão futura deve falhar
        self.assertFalse(validate_python_version((99, 0)))
    
    def test_ensure_directory(self):
        """Testa criação de diretório"""
        import tempfile
        import shutil
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, 'test_subdir')
            result_path = ensure_directory(test_path)
            
            self.assertTrue(os.path.exists(result_path))
            self.assertTrue(os.path.isdir(result_path))
    
    def test_format_bytes(self):
        """Testa formatação de bytes"""
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.0 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.0 GB")
    
    def test_memory_usage_mb(self):
        """Testa medição de uso de memória"""
        memory = memory_usage_mb()
        
        # Deve retornar um número positivo ou -1 se psutil não disponível
        self.assertTrue(isinstance(memory, float))
        self.assertTrue(memory > 0 or memory == -1.0)
    
    def test_safe_import_check(self):
        """Testa verificação de imports"""
        deps = safe_import_check()
        
        self.assertIsInstance(deps, dict)
        self.assertIn('matplotlib', deps)
        self.assertIn('pandas', deps)  # pandas está no requirements base
    
    def test_get_missing_dependencies(self):
        """Testa listagem de dependências faltando"""
        missing = get_missing_dependencies()
        
        self.assertIsInstance(missing, list)
        # Lista pode estar vazia se todas dependências estão instaladas


class TestPerformanceMonitor(unittest.TestCase):
    """Testes para PerformanceMonitor"""
    
    def test_monitor_creation(self):
        """Testa criação do monitor"""
        monitor = PerformanceMonitor()
        self.assertIsNotNone(monitor)
        self.assertIsNone(monitor.start_time)
    
    def test_monitor_start(self):
        """Testa início do monitoramento"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        self.assertIsNotNone(monitor.start_time)
    
    def test_checkpoint(self):
        """Testa checkpoint de tempo"""
        monitor = PerformanceMonitor()
        monitor.start()
        monitor.checkpoint('test')
        
        self.assertIn('test', monitor.checkpoints)
        self.assertGreater(monitor.checkpoints['test'], 0)
    
    def test_report(self):
        """Testa geração de relatório"""
        monitor = PerformanceMonitor()
        
        # Relatório vazio
        empty_report = monitor.report()
        self.assertEqual(empty_report, {})
        
        # Relatório com dados
        monitor.start()
        monitor.checkpoint('test')
        report = monitor.report()
        
        self.assertIn('total_time_seconds', report)
        self.assertIn('memory_usage_mb', report)
        self.assertIn('checkpoints', report)


if __name__ == '__main__':
    # Executa os testes
    unittest.main(verbosity=2)
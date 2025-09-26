#!/usr/bin/env python3
"""
UNIVERSAL TESTING & VALIDATION FRAMEWORK - BW AUTOMATE
Framework completo de testes que funciona em qualquer ambiente
Inclui testes unitários, de integração, performance, segurança e validação end-to-end
"""

import os
import sys
import json
import time
import logging
import subprocess
import tempfile
import sqlite3
import threading
import multiprocessing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Type, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import traceback
import hashlib
import psutil
from unittest.mock import Mock, patch
import warnings

try:
    import pytest
except ImportError:
    print("Installing pytest...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest', 'pytest-cov', 'pytest-html'], check=True)
    import pytest

try:
    import coverage
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'coverage'], check=True)
    import coverage

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'], check=True)
    import requests


class TestType(Enum):
    """Tipos de teste"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    END_TO_END = "end_to_end"
    SMOKE = "smoke"
    REGRESSION = "regression"
    LOAD = "load"
    STRESS = "stress"


class TestStatus(Enum):
    """Status do teste"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"


class TestSeverity(Enum):
    """Severidade do teste"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TestCase:
    """Caso de teste"""
    test_id: str
    name: str
    description: str
    test_type: TestType
    severity: TestSeverity
    function: Callable
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    timeout: float = 300.0  # 5 minutos
    retry_count: int = 0
    dependencies: List[str] = None
    tags: List[str] = None
    expected_result: Any = None
    test_data: Dict[str, Any] = None


@dataclass
class TestResult:
    """Resultado do teste"""
    test_id: str
    test_name: str
    status: TestStatus
    execution_time: float
    start_time: datetime
    end_time: datetime
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    output: str = ""
    assertions_count: int = 0
    coverage_percentage: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    actual_result: Any = None
    artifacts: List[str] = None


@dataclass
class TestSuite:
    """Conjunto de testes"""
    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase]
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    parallel_execution: bool = False
    max_workers: int = 4


@dataclass
class TestSession:
    """Sessão de testes"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    execution_time: float = 0.0
    coverage_percentage: float = 0.0
    test_results: List[TestResult] = None


class TestValidator:
    """Validador de testes"""
    
    def __init__(self):
        self.validation_rules = {
            'function_exists': self._validate_function_exists,
            'has_docstring': self._validate_has_docstring,
            'proper_naming': self._validate_proper_naming,
            'has_assertions': self._validate_has_assertions,
            'timeout_reasonable': self._validate_timeout_reasonable,
            'dependencies_valid': self._validate_dependencies_valid
        }
    
    def validate_test_case(self, test_case: TestCase) -> Tuple[bool, List[str]]:
        """Valida um caso de teste"""
        errors = []
        
        for rule_name, rule_function in self.validation_rules.items():
            try:
                is_valid, error_msg = rule_function(test_case)
                if not is_valid:
                    errors.append(f"{rule_name}: {error_msg}")
            except Exception as e:
                errors.append(f"{rule_name}: Validation error - {e}")
        
        return len(errors) == 0, errors
    
    def _validate_function_exists(self, test_case: TestCase) -> Tuple[bool, str]:
        """Valida se função existe e é chamável"""
        if not callable(test_case.function):
            return False, "Test function is not callable"
        return True, ""
    
    def _validate_has_docstring(self, test_case: TestCase) -> Tuple[bool, str]:
        """Valida se função tem docstring"""
        if not test_case.function.__doc__:
            return False, "Test function should have a docstring"
        return True, ""
    
    def _validate_proper_naming(self, test_case: TestCase) -> Tuple[bool, str]:
        """Valida convenção de nomenclatura"""
        if not test_case.name.startswith('test_'):
            return False, "Test name should start with 'test_'"
        return True, ""
    
    def _validate_has_assertions(self, test_case: TestCase) -> Tuple[bool, str]:
        """Valida se função tem assertions (análise estática básica)"""
        import inspect
        source = inspect.getsource(test_case.function)
        
        assertion_keywords = ['assert', 'assertEqual', 'assertTrue', 'assertFalse', 'assertIn']
        has_assertions = any(keyword in source for keyword in assertion_keywords)
        
        if not has_assertions:
            return False, "Test function should contain assertions"
        return True, ""
    
    def _validate_timeout_reasonable(self, test_case: TestCase) -> Tuple[bool, str]:
        """Valida se timeout é razoável"""
        if test_case.timeout <= 0:
            return False, "Timeout must be positive"
        if test_case.timeout > 3600:  # 1 hora
            return False, "Timeout seems too high (>1 hour)"
        return True, ""
    
    def _validate_dependencies_valid(self, test_case: TestCase) -> Tuple[bool, str]:
        """Valida se dependências são válidas"""
        if test_case.dependencies:
            for dep in test_case.dependencies:
                if not isinstance(dep, str):
                    return False, f"Dependency must be string: {dep}"
        return True, ""


class TestAssertion:
    """Sistema de assertions customizado"""
    
    def __init__(self):
        self.assertion_count = 0
    
    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert que valores são iguais"""
        self.assertion_count += 1
        if actual != expected:
            raise AssertionError(f"Expected {expected}, got {actual}. {message}")
    
    def assert_not_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert que valores são diferentes"""
        self.assertion_count += 1
        if actual == expected:
            raise AssertionError(f"Expected values to be different, both are {actual}. {message}")
    
    def assert_true(self, condition: bool, message: str = ""):
        """Assert que condição é verdadeira"""
        self.assertion_count += 1
        if not condition:
            raise AssertionError(f"Expected True, got {condition}. {message}")
    
    def assert_false(self, condition: bool, message: str = ""):
        """Assert que condição é falsa"""
        self.assertion_count += 1
        if condition:
            raise AssertionError(f"Expected False, got {condition}. {message}")
    
    def assert_in(self, item: Any, container: Any, message: str = ""):
        """Assert que item está no container"""
        self.assertion_count += 1
        if item not in container:
            raise AssertionError(f"Expected {item} to be in {container}. {message}")
    
    def assert_not_in(self, item: Any, container: Any, message: str = ""):
        """Assert que item não está no container"""
        self.assertion_count += 1
        if item in container:
            raise AssertionError(f"Expected {item} not to be in {container}. {message}")
    
    def assert_is_none(self, value: Any, message: str = ""):
        """Assert que valor é None"""
        self.assertion_count += 1
        if value is not None:
            raise AssertionError(f"Expected None, got {value}. {message}")
    
    def assert_is_not_none(self, value: Any, message: str = ""):
        """Assert que valor não é None"""
        self.assertion_count += 1
        if value is None:
            raise AssertionError(f"Expected non-None value, got None. {message}")
    
    def assert_raises(self, expected_exception: Type[Exception], callable_obj: Callable, *args, **kwargs):
        """Assert que função levanta exceção específica"""
        self.assertion_count += 1
        try:
            callable_obj(*args, **kwargs)
            raise AssertionError(f"Expected {expected_exception.__name__} to be raised")
        except expected_exception:
            pass  # Esperado
        except Exception as e:
            raise AssertionError(f"Expected {expected_exception.__name__}, got {type(e).__name__}: {e}")
    
    def assert_performance(self, callable_obj: Callable, max_time: float, *args, **kwargs):
        """Assert que função executa dentro do tempo limite"""
        self.assertion_count += 1
        start_time = time.time()
        try:
            result = callable_obj(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > max_time:
                raise AssertionError(f"Function took {execution_time:.3f}s, expected max {max_time}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            raise AssertionError(f"Function failed after {execution_time:.3f}s: {e}")


class TestExecutor:
    """Executor de testes"""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger = self._setup_logging()
        self.test_db = self._setup_database()
        
        # Estatísticas de sistema
        self.process = psutil.Process()
    
    def _setup_logging(self):
        """Configura logging para testes"""
        logger = logging.getLogger('test_executor')
        logger.setLevel(logging.DEBUG)
        
        handler = logging.FileHandler(self.output_dir / 'test_execution.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_database(self):
        """Configura banco de dados de testes"""
        db_path = self.output_dir / 'test_results.db'
        conn = sqlite3.connect(db_path)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_tests INTEGER DEFAULT 0,
                passed_tests INTEGER DEFAULT 0,
                failed_tests INTEGER DEFAULT 0,
                skipped_tests INTEGER DEFAULT 0,
                error_tests INTEGER DEFAULT 0,
                execution_time REAL DEFAULT 0.0,
                coverage_percentage REAL DEFAULT 0.0
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                test_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                status TEXT NOT NULL,
                execution_time REAL NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                error_message TEXT,
                traceback TEXT,
                output TEXT,
                assertions_count INTEGER DEFAULT 0,
                coverage_percentage REAL DEFAULT 0.0,
                memory_usage REAL DEFAULT 0.0,
                cpu_usage REAL DEFAULT 0.0,
                FOREIGN KEY (session_id) REFERENCES test_sessions (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return str(db_path)
    
    def execute_test_case(self, test_case: TestCase, session_id: str) -> TestResult:
        """Executa um caso de teste individual"""
        
        start_time = datetime.now()
        start_memory = self.process.memory_info().rss
        
        result = TestResult(
            test_id=test_case.test_id,
            test_name=test_case.name,
            status=TestStatus.RUNNING,
            execution_time=0.0,
            start_time=start_time,
            end_time=start_time,
            artifacts=[]
        )
        
        try:
            self.logger.info(f"Starting test: {test_case.name}")
            
            # Setup
            if test_case.setup_function:
                test_case.setup_function()
            
            # Captura de output
            output_capture = []
            
            # Execução com timeout
            test_thread = threading.Thread(
                target=self._run_test_with_assertions,
                args=(test_case, result, output_capture)
            )
            
            test_thread.start()
            test_thread.join(timeout=test_case.timeout)
            
            if test_thread.is_alive():
                result.status = TestStatus.TIMEOUT
                result.error_message = f"Test timed out after {test_case.timeout} seconds"
                # Note: We can't actually kill the thread in Python, but we mark it as timeout
            
            # Teardown
            if test_case.teardown_function:
                try:
                    test_case.teardown_function()
                except Exception as e:
                    self.logger.warning(f"Teardown failed for {test_case.name}: {e}")
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.traceback = traceback.format_exc()
            self.logger.error(f"Test {test_case.name} error: {e}")
        
        # Finalização
        end_time = datetime.now()
        result.end_time = end_time
        result.execution_time = (end_time - start_time).total_seconds()
        
        # Métricas de sistema
        end_memory = self.process.memory_info().rss
        result.memory_usage = (end_memory - start_memory) / 1024 / 1024  # MB
        result.cpu_usage = self.process.cpu_percent()
        
        self.logger.info(f"Test {test_case.name} completed: {result.status.value}")
        
        # Salva resultado no banco
        self._save_test_result(result, session_id)
        
        return result
    
    def _run_test_with_assertions(self, test_case: TestCase, result: TestResult, output_capture: List[str]):
        """Executa teste com captura de assertions"""
        
        # Cria contexto de assertions
        assertions = TestAssertion()
        
        try:
            # Prepara argumentos do teste
            test_kwargs = {
                'assert_equal': assertions.assert_equal,
                'assert_not_equal': assertions.assert_not_equal,
                'assert_true': assertions.assert_true,
                'assert_false': assertions.assert_false,
                'assert_in': assertions.assert_in,
                'assert_not_in': assertions.assert_not_in,
                'assert_is_none': assertions.assert_is_none,
                'assert_is_not_none': assertions.assert_is_not_none,
                'assert_raises': assertions.assert_raises,
                'assert_performance': assertions.assert_performance,
            }
            
            if test_case.test_data:
                test_kwargs.update(test_case.test_data)
            
            # Executa o teste
            if hasattr(test_case.function, '__code__') and test_case.function.__code__.co_argcount > 0:
                # Função aceita argumentos
                actual_result = test_case.function(**test_kwargs)
            else:
                # Função sem argumentos
                actual_result = test_case.function()
            
            result.actual_result = actual_result
            result.assertions_count = assertions.assertion_count
            
            # Verifica resultado esperado
            if test_case.expected_result is not None:
                if actual_result != test_case.expected_result:
                    result.status = TestStatus.FAILED
                    result.error_message = f"Expected {test_case.expected_result}, got {actual_result}"
                else:
                    result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.PASSED
                
        except AssertionError as e:
            result.status = TestStatus.FAILED
            result.error_message = str(e)
            result.assertions_count = assertions.assertion_count
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.traceback = traceback.format_exc()
            result.assertions_count = assertions.assertion_count
    
    def execute_test_suite(self, test_suite: TestSuite) -> TestSession:
        """Executa uma suíte de testes"""
        
        session_id = hashlib.md5(f"{test_suite.suite_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        session = TestSession(
            session_id=session_id,
            start_time=datetime.now(),
            total_tests=len(test_suite.test_cases),
            test_results=[]
        )
        
        self.logger.info(f"Starting test suite: {test_suite.name} (Session: {session_id})")
        
        # Setup da suíte
        if test_suite.setup_function:
            try:
                test_suite.setup_function()
            except Exception as e:
                self.logger.error(f"Suite setup failed: {e}")
                return session
        
        try:
            if test_suite.parallel_execution:
                # Execução paralela
                session.test_results = self._execute_parallel(test_suite, session_id)
            else:
                # Execução sequencial
                session.test_results = self._execute_sequential(test_suite, session_id)
                
        finally:
            # Teardown da suíte
            if test_suite.teardown_function:
                try:
                    test_suite.teardown_function()
                except Exception as e:
                    self.logger.error(f"Suite teardown failed: {e}")
        
        # Finalização da sessão
        session.end_time = datetime.now()
        session.execution_time = (session.end_time - session.start_time).total_seconds()
        
        # Contabiliza resultados
        for result in session.test_results:
            if result.status == TestStatus.PASSED:
                session.passed_tests += 1
            elif result.status == TestStatus.FAILED:
                session.failed_tests += 1
            elif result.status == TestStatus.SKIPPED:
                session.skipped_tests += 1
            else:
                session.error_tests += 1
        
        # Salva sessão no banco
        self._save_test_session(session)
        
        self.logger.info(f"Test suite completed: {session.passed_tests}/{session.total_tests} passed")
        
        return session
    
    def _execute_sequential(self, test_suite: TestSuite, session_id: str) -> List[TestResult]:
        """Executa testes sequencialmente"""
        results = []
        
        for test_case in test_suite.test_cases:
            result = self.execute_test_case(test_case, session_id)
            results.append(result)
            
            # Para execução se teste crítico falhar
            if (test_case.severity == TestSeverity.CRITICAL and 
                result.status in [TestStatus.FAILED, TestStatus.ERROR]):
                self.logger.warning(f"Critical test failed, stopping suite execution")
                break
        
        return results
    
    def _execute_parallel(self, test_suite: TestSuite, session_id: str) -> List[TestResult]:
        """Executa testes em paralelo"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        with ThreadPoolExecutor(max_workers=test_suite.max_workers) as executor:
            # Submete todos os testes
            future_to_test = {
                executor.submit(self.execute_test_case, test_case, session_id): test_case
                for test_case in test_suite.test_cases
            }
            
            # Coleta resultados conforme completam
            for future in as_completed(future_to_test):
                result = future.result()
                results.append(result)
        
        # Ordena resultados pela ordem original dos testes
        test_order = {test.test_id: i for i, test in enumerate(test_suite.test_cases)}
        results.sort(key=lambda r: test_order.get(r.test_id, 999))
        
        return results
    
    def _save_test_result(self, result: TestResult, session_id: str):
        """Salva resultado no banco"""
        conn = sqlite3.connect(self.test_db)
        
        conn.execute('''
            INSERT INTO test_results 
            (test_id, session_id, test_name, status, execution_time, start_time, end_time,
             error_message, traceback, output, assertions_count, coverage_percentage,
             memory_usage, cpu_usage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.test_id, session_id, result.test_name, result.status.value,
            result.execution_time, result.start_time.isoformat(), result.end_time.isoformat(),
            result.error_message, result.traceback, result.output, result.assertions_count,
            result.coverage_percentage, result.memory_usage, result.cpu_usage
        ))
        
        conn.commit()
        conn.close()
    
    def _save_test_session(self, session: TestSession):
        """Salva sessão no banco"""
        conn = sqlite3.connect(self.test_db)
        
        conn.execute('''
            INSERT OR REPLACE INTO test_sessions 
            (session_id, start_time, end_time, total_tests, passed_tests, failed_tests,
             skipped_tests, error_tests, execution_time, coverage_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.session_id, session.start_time.isoformat(),
            session.end_time.isoformat() if session.end_time else None,
            session.total_tests, session.passed_tests, session.failed_tests,
            session.skipped_tests, session.error_tests, session.execution_time,
            session.coverage_percentage
        ))
        
        conn.commit()
        conn.close()


class BWAutomateTestSuite:
    """Suíte de testes específica para BW_AUTOMATE"""
    
    def __init__(self, bw_automate_path: str):
        self.bw_automate_path = Path(bw_automate_path)
        self.test_cases = []
        self._build_test_cases()
    
    def _build_test_cases(self):
        """Constrói casos de teste para BW_AUTOMATE"""
        
        # Testes unitários básicos
        self.test_cases.extend([
            TestCase(
                test_id="unit_001",
                name="test_bw_automate_import",
                description="Test BW_AUTOMATE modules can be imported",
                test_type=TestType.UNIT,
                severity=TestSeverity.CRITICAL,
                function=self._test_bw_automate_import
            ),
            
            TestCase(
                test_id="unit_002",
                name="test_config_loading",
                description="Test configuration loading functionality",
                test_type=TestType.UNIT,
                severity=TestSeverity.HIGH,
                function=self._test_config_loading
            ),
            
            TestCase(
                test_id="unit_003",
                name="test_sql_pattern_extraction",
                description="Test SQL pattern extraction",
                test_type=TestType.UNIT,
                severity=TestSeverity.HIGH,
                function=self._test_sql_pattern_extraction
            ),
        ])
        
        # Testes de integração
        self.test_cases.extend([
            TestCase(
                test_id="integration_001",
                name="test_end_to_end_analysis",
                description="Test complete analysis workflow",
                test_type=TestType.INTEGRATION,
                severity=TestSeverity.CRITICAL,
                function=self._test_end_to_end_analysis,
                timeout=120.0
            ),
            
            TestCase(
                test_id="integration_002",
                name="test_report_generation",
                description="Test report generation",
                test_type=TestType.INTEGRATION,
                severity=TestSeverity.HIGH,
                function=self._test_report_generation
            ),
        ])
        
        # Testes de performance
        self.test_cases.extend([
            TestCase(
                test_id="performance_001",
                name="test_large_file_processing",
                description="Test processing of large files",
                test_type=TestType.PERFORMANCE,
                severity=TestSeverity.MEDIUM,
                function=self._test_large_file_processing,
                timeout=300.0
            ),
            
            TestCase(
                test_id="performance_002",
                name="test_memory_usage",
                description="Test memory usage under load",
                test_type=TestType.PERFORMANCE,
                severity=TestSeverity.MEDIUM,
                function=self._test_memory_usage
            ),
        ])
        
        # Testes de segurança
        self.test_cases.extend([
            TestCase(
                test_id="security_001",
                name="test_sql_injection_detection",
                description="Test SQL injection detection",
                test_type=TestType.SECURITY,
                severity=TestSeverity.HIGH,
                function=self._test_sql_injection_detection
            ),
            
            TestCase(
                test_id="security_002",
                name="test_file_path_validation",
                description="Test file path validation security",
                test_type=TestType.SECURITY,
                severity=TestSeverity.HIGH,
                function=self._test_file_path_validation
            ),
        ])
    
    # Implementação dos testes
    def _test_bw_automate_import(self, **kwargs):
        """Testa importação dos módulos principais"""
        assert_true = kwargs['assert_true']
        assert_is_not_none = kwargs['assert_is_not_none']
        
        # Adiciona path do BW_AUTOMATE
        sys.path.insert(0, str(self.bw_automate_path))
        
        try:
            # Testa importações principais
            import run_analysis
            assert_is_not_none(run_analysis, "run_analysis module should be importable")
            
            import airflow_table_mapper
            assert_is_not_none(airflow_table_mapper, "airflow_table_mapper module should be importable")
            
            import sql_pattern_extractor
            assert_is_not_none(sql_pattern_extractor, "sql_pattern_extractor module should be importable")
            
            # Testa classe principal
            assert_true(hasattr(run_analysis, 'BWAutomate'), "BWAutomate class should exist")
            
            return True
            
        except ImportError as e:
            raise AssertionError(f"Failed to import BW_AUTOMATE modules: {e}")
        finally:
            sys.path.pop(0)
    
    def _test_config_loading(self, **kwargs):
        """Testa carregamento de configuração"""
        assert_true = kwargs['assert_true']
        assert_is_not_none = kwargs['assert_is_not_none']
        
        # Cria arquivo de configuração temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "version": "test",
                "analysis": {
                    "source_dirs": ["test"],
                    "file_patterns": ["*.py"]
                }
            }
            json.dump(test_config, f)
            config_file = f.name
        
        try:
            sys.path.insert(0, str(self.bw_automate_path))
            import run_analysis
            
            # Testa carregamento
            bw = run_analysis.BWAutomate(config_path=config_file)
            assert_is_not_none(bw, "BWAutomate instance should be created")
            
            return True
            
        finally:
            os.unlink(config_file)
            sys.path.pop(0)
    
    def _test_sql_pattern_extraction(self, **kwargs):
        """Testa extração de padrões SQL"""
        assert_equal = kwargs['assert_equal']
        assert_true = kwargs['assert_true']
        
        sys.path.insert(0, str(self.bw_automate_path))
        
        try:
            import sql_pattern_extractor
            
            # Código de teste com SQL
            test_code = '''
def test_function():
    query = "SELECT * FROM users WHERE id = 1"
    cursor.execute("INSERT INTO products (name) VALUES (?)", (name,))
    return query
'''
            
            extractor = sql_pattern_extractor.AdvancedSQLExtractor()
            patterns = extractor.extract_sql_patterns(test_code, "test.py")
            
            assert_true(len(patterns) > 0, "Should extract SQL patterns")
            
            # Verifica se encontrou as tabelas
            table_names = [p.get('table_name', '') for p in patterns]
            assert_true('users' in table_names or 'products' in table_names, 
                       "Should find table names in SQL")
            
            return len(patterns)
            
        finally:
            sys.path.pop(0)
    
    def _test_end_to_end_analysis(self, **kwargs):
        """Teste end-to-end de análise completa"""
        assert_true = kwargs['assert_true']
        assert_is_not_none = kwargs['assert_is_not_none']
        
        # Cria projeto de teste temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Cria arquivo Python com SQL
            test_file = temp_path / "test_dag.py"
            test_content = '''
from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator

def create_dag():
    dag = DAG('test_dag')
    
    task = PostgresOperator(
        task_id='test_task',
        sql="SELECT * FROM test_table",
        dag=dag
    )
    
    return dag
'''
            test_file.write_text(test_content)
            
            # Executa análise
            sys.path.insert(0, str(self.bw_automate_path))
            
            try:
                import run_analysis
                
                bw = run_analysis.BWAutomate()
                results = bw.analyze_project(project_root=str(temp_path))
                
                assert_is_not_none(results, "Analysis should return results")
                assert_true('total_files' in results, "Results should contain file count")
                assert_true(results['total_files'] > 0, "Should analyze at least one file")
                
                return results
                
            finally:
                sys.path.pop(0)
    
    def _test_report_generation(self, **kwargs):
        """Testa geração de relatórios"""
        assert_true = kwargs['assert_true']
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Simula resultados de análise
            mock_results = {
                'total_files': 1,
                'total_tables': 2,
                'tables': [
                    {'name': 'test_table', 'file': 'test.py', 'line': 5}
                ]
            }
            
            sys.path.insert(0, str(self.bw_automate_path))
            
            try:
                import enhanced_report_generator
                
                generator = enhanced_report_generator.AdvancedReportGenerator()
                report_path = generator.generate_html_report(mock_results, temp_dir)
                
                assert_true(os.path.exists(report_path), "HTML report should be generated")
                
                # Verifica conteúdo básico
                with open(report_path, 'r') as f:
                    content = f.read()
                    assert_true('test_table' in content, "Report should contain table names")
                
                return report_path
                
            finally:
                sys.path.pop(0)
    
    def _test_large_file_processing(self, **kwargs):
        """Testa processamento de arquivos grandes"""
        assert_performance = kwargs['assert_performance']
        
        # Cria arquivo grande temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Gera arquivo com muitas linhas
            for i in range(10000):
                f.write(f'# Line {i}\n')
                if i % 100 == 0:
                    f.write(f'query_{i} = "SELECT * FROM table_{i}"\n')
            
            large_file = f.name
        
        try:
            sys.path.insert(0, str(self.bw_automate_path))
            import sql_pattern_extractor
            
            def process_large_file():
                with open(large_file, 'r') as f:
                    content = f.read()
                
                extractor = sql_pattern_extractor.AdvancedSQLExtractor()
                return extractor.extract_sql_patterns(content, large_file)
            
            # Deve processar em menos de 30 segundos
            results = assert_performance(process_large_file, 30.0)
            
            return len(results)
            
        finally:
            os.unlink(large_file)
            sys.path.pop(0)
    
    def _test_memory_usage(self, **kwargs):
        """Testa uso de memória"""
        assert_true = kwargs['assert_true']
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Executa operação que pode consumir memória
        sys.path.insert(0, str(self.bw_automate_path))
        
        try:
            import run_analysis
            
            # Simula análise múltipla
            for i in range(10):
                bw = run_analysis.BWAutomate()
                # Simula processamento
                large_data = ['test'] * 1000
                del large_data
            
            final_memory = process.memory_info().rss
            memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
            
            # Verifica se não houve vazamento excessivo (limite: 100MB)
            assert_true(memory_increase < 100, f"Memory increase too high: {memory_increase:.1f}MB")
            
            return memory_increase
            
        finally:
            sys.path.pop(0)
    
    def _test_sql_injection_detection(self, **kwargs):
        """Testa detecção de SQL injection"""
        assert_true = kwargs['assert_true']
        assert_false = kwargs['assert_false']
        
        # Códigos de teste
        safe_code = '''
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
'''
        
        unsafe_code = '''
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)
'''
        
        sys.path.insert(0, str(self.bw_automate_path))
        
        try:
            # Implementação básica de detecção
            def has_sql_injection_risk(code):
                # Padrões básicos de risco
                risk_patterns = [
                    r'f".*SELECT.*{.*}"',  # f-string com SQL
                    r'".*SELECT.*"\s*\+',  # concatenação de string
                    r'%.*SELECT',  # formatação com %
                ]
                
                import re
                for pattern in risk_patterns:
                    if re.search(pattern, code, re.IGNORECASE):
                        return True
                return False
            
            assert_false(has_sql_injection_risk(safe_code), 
                        "Safe code should not trigger injection detection")
            assert_true(has_sql_injection_risk(unsafe_code), 
                       "Unsafe code should trigger injection detection")
            
            return True
            
        finally:
            sys.path.pop(0)
    
    def _test_file_path_validation(self, **kwargs):
        """Testa validação de caminhos de arquivo"""
        assert_true = kwargs['assert_true']
        assert_false = kwargs['assert_false']
        
        def is_safe_path(file_path):
            """Validação básica de caminho seguro"""
            dangerous_patterns = ['../', '..\\', '/etc/', '/root/', 'C:\\Windows\\']
            
            for pattern in dangerous_patterns:
                if pattern in file_path:
                    return False
            
            return True
        
        # Testa caminhos seguros
        safe_paths = [
            'project/file.py',
            './local/file.py',
            'data/analysis.json'
        ]
        
        for path in safe_paths:
            assert_true(is_safe_path(path), f"Safe path should be valid: {path}")
        
        # Testa caminhos perigosos
        dangerous_paths = [
            '../../../etc/passwd',
            '..\\..\\Windows\\System32',
            '/etc/shadow',
            '/root/.ssh/id_rsa'
        ]
        
        for path in dangerous_paths:
            assert_false(is_safe_path(path), f"Dangerous path should be invalid: {path}")
        
        return True
    
    def get_test_suite(self) -> TestSuite:
        """Retorna suíte de testes completa"""
        return TestSuite(
            suite_id="bw_automate_main",
            name="BW_AUTOMATE Main Test Suite",
            description="Complete test suite for BW_AUTOMATE system",
            test_cases=self.test_cases,
            parallel_execution=False,  # Evita conflitos de importação
            max_workers=2
        )


class TestReporter:
    """Gerador de relatórios de teste"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_html_report(self, session: TestSession, output_file: str = None) -> str:
        """Gera relatório HTML dos testes"""
        
        if output_file is None:
            output_file = self.output_dir / f"test_report_{session.session_id}.html"
        
        # Calcula estatísticas
        success_rate = (session.passed_tests / session.total_tests * 100) if session.total_tests > 0 else 0
        
        # Template HTML
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>BW_AUTOMATE Test Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric h3 {{ margin: 0; color: #2c3e50; }}
        .metric .value {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
        .failed .value {{ color: #e74c3c; }}
        .test-results {{ margin: 20px 0; }}
        .test-case {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .test-case.passed {{ background: #d5f4e6; }}
        .test-case.failed {{ background: #ffeaea; }}
        .test-case.error {{ background: #fff3cd; }}
        .test-details {{ margin-top: 10px; font-size: 12px; color: #666; }}
        .error-message {{ background: #f8f8f8; padding: 10px; border-left: 4px solid #e74c3c; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 BW_AUTOMATE Test Report</h1>
        <p>Session: {session.session_id}</p>
        <p>Execution Time: {session.start_time} - {session.end_time}</p>
        <p>Duration: {session.execution_time:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <div class="value">{session.total_tests}</div>
        </div>
        <div class="metric">
            <h3>Passed</h3>
            <div class="value">{session.passed_tests}</div>
        </div>
        <div class="metric failed">
            <h3>Failed</h3>
            <div class="value">{session.failed_tests}</div>
        </div>
        <div class="metric failed">
            <h3>Errors</h3>
            <div class="value">{session.error_tests}</div>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <div class="value">{success_rate:.1f}%</div>
        </div>
    </div>
    
    <h2>Test Results</h2>
    <div class="test-results">
'''
        
        # Adiciona resultados individuais
        for result in session.test_results:
            status_class = result.status.value
            
            html_content += f'''
        <div class="test-case {status_class}">
            <h3>{result.test_name}</h3>
            <div class="test-details">
                <strong>Status:</strong> {result.status.value.upper()} | 
                <strong>Time:</strong> {result.execution_time:.3f}s | 
                <strong>Assertions:</strong> {result.assertions_count} |
                <strong>Memory:</strong> {result.memory_usage:.1f}MB
            </div>
'''
            
            if result.error_message:
                html_content += f'''
            <div class="error-message">
                <strong>Error:</strong> {result.error_message}
            </div>
'''
            
            html_content += '        </div>\n'
        
        html_content += '''
    </div>
</body>
</html>
'''
        
        # Salva arquivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_file)
    
    def generate_json_report(self, session: TestSession, output_file: str = None) -> str:
        """Gera relatório JSON dos testes"""
        
        if output_file is None:
            output_file = self.output_dir / f"test_report_{session.session_id}.json"
        
        # Converte para dicionário serializável
        report_data = asdict(session)
        
        # Converte enums e datetime para string
        def convert_for_json(obj):
            if hasattr(obj, 'value'):  # Enum
                return obj.value
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Processa recursivamente
        def process_dict(d):
            if isinstance(d, dict):
                return {k: process_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [process_dict(item) for item in d]
            else:
                return convert_for_json(d)
        
        processed_data = process_dict(report_data)
        
        # Salva arquivo
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        return str(output_file)


# CLI Interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="BW_AUTOMATE Universal Testing Framework")
    parser.add_argument("--bw-path", default=".", help="Path to BW_AUTOMATE installation")
    parser.add_argument("--output-dir", default="test_results", help="Output directory for test results")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--test-type", choices=[t.value for t in TestType], 
                       help="Run only specific test type")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML report")
    parser.add_argument("--json-report", action="store_true", help="Generate JSON report")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🧪 BW_AUTOMATE Universal Testing Framework")
    print("=" * 50)
    
    # Inicializa componentes
    test_suite_builder = BWAutomateTestSuite(args.bw_path)
    test_suite = test_suite_builder.get_test_suite()
    
    # Filtra testes por tipo se especificado
    if args.test_type:
        test_type = TestType(args.test_type)
        test_suite.test_cases = [tc for tc in test_suite.test_cases if tc.test_type == test_type]
        print(f"Running {len(test_suite.test_cases)} {test_type.value} tests")
    
    # Configura execução paralela
    if args.parallel:
        test_suite.parallel_execution = True
        print("Parallel execution enabled")
    
    # Executa testes
    executor = TestExecutor(args.output_dir)
    session = executor.execute_test_suite(test_suite)
    
    # Mostra resultados
    print(f"\n📊 Test Results:")
    print(f"  Total: {session.total_tests}")
    print(f"  Passed: {session.passed_tests} ✅")
    print(f"  Failed: {session.failed_tests} ❌")
    print(f"  Errors: {session.error_tests} ⚠️")
    print(f"  Success Rate: {(session.passed_tests/session.total_tests*100):.1f}%")
    print(f"  Execution Time: {session.execution_time:.2f} seconds")
    
    # Gera relatórios
    reporter = TestReporter(args.output_dir)
    
    if args.html_report:
        html_file = reporter.generate_html_report(session)
        print(f"  HTML Report: {html_file}")
    
    if args.json_report:
        json_file = reporter.generate_json_report(session)
        print(f"  JSON Report: {json_file}")
    
    # Exit code baseado nos resultados
    if session.failed_tests > 0 or session.error_tests > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
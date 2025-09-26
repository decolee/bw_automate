#!/usr/bin/env python3
"""
INTEGRATED PYTHON ANALYZER - BW AUTOMATE
Sistema integrado para análise 100% completa de código Python
Combina todos os analisadores para cobertura total
"""

import os
import sys
import json
import ast
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import concurrent.futures
import time

# Import local analyzers
try:
    from COMPLETE_PYTHON_CODE_ANALYZER import CompletePythonAnalyzer, PythonAnalysisResult
    from ADVANCED_PYTHON_FEATURES_ANALYZER import AdvancedPythonFeaturesAnalyzer, AdvancedFeatureUsage
    from enhanced_sql_analyzer import EnhancedSQLAnalyzer
    from airflow_table_mapper import PostgreSQLTableMapper
except ImportError as e:
    print(f"Warning: Could not import local analyzers: {e}")
    print("Some features may not be available")


class AnalysisScope(Enum):
    """Escopo da análise"""
    BASIC = "basic"                    # Análise básica AST
    ADVANCED = "advanced"              # Recursos Python avançados
    SQL_DATABASE = "sql_database"      # Análise SQL e banco de dados
    COMPLETE = "complete"              # Análise completa
    ENTERPRISE = "enterprise"          # Análise enterprise com tudo


@dataclass
class CodeComplexityMetrics:
    """Métricas de complexidade de código"""
    cyclomatic_complexity: float
    cognitive_complexity: float
    halstead_difficulty: float
    halstead_effort: float
    maintainability_index: float
    lines_of_code: int
    logical_lines_of_code: int
    comment_lines: int
    blank_lines: int
    code_to_comment_ratio: float


@dataclass
class SecurityAnalysis:
    """Análise de segurança"""
    vulnerabilities: List[Dict[str, Any]]
    security_score: float
    sql_injection_risks: List[Dict[str, Any]]
    hardcoded_secrets: List[Dict[str, Any]]
    insecure_functions: List[Dict[str, Any]]
    file_system_access: List[Dict[str, Any]]
    network_access: List[Dict[str, Any]]


@dataclass
class PerformanceAnalysis:
    """Análise de performance"""
    performance_issues: List[Dict[str, Any]]
    performance_score: float
    database_efficiency: Dict[str, Any]
    memory_concerns: List[Dict[str, Any]]
    cpu_intensive_operations: List[Dict[str, Any]]
    io_operations: List[Dict[str, Any]]
    optimization_suggestions: List[Dict[str, Any]]


@dataclass
class DependencyAnalysis:
    """Análise de dependências"""
    internal_dependencies: Dict[str, List[str]]
    external_dependencies: Dict[str, str]
    circular_dependencies: List[Tuple[str, str]]
    unused_imports: List[str]
    missing_dependencies: List[str]
    dependency_tree: Dict[str, Any]
    dependency_risk_score: float


@dataclass
class ComprehensiveAnalysisResult:
    """Resultado completo da análise integrada"""
    # Informações básicas
    project_path: str
    analysis_timestamp: str
    analysis_scope: AnalysisScope
    total_files_analyzed: int
    analysis_duration_seconds: float
    
    # Resultados dos analisadores
    basic_analysis: Optional[PythonAnalysisResult] = None
    advanced_features: List[AdvancedFeatureUsage] = field(default_factory=list)
    sql_analysis: Optional[Dict[str, Any]] = None
    
    # Métricas integradas
    complexity_metrics: Optional[CodeComplexityMetrics] = None
    security_analysis: Optional[SecurityAnalysis] = None
    performance_analysis: Optional[PerformanceAnalysis] = None
    dependency_analysis: Optional[DependencyAnalysis] = None
    
    # Scores e qualidade
    overall_quality_score: float = 0.0
    maintainability_score: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0
    
    # Recomendações
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Relatórios específicos
    database_usage_report: Dict[str, Any] = field(default_factory=dict)
    compatibility_report: Dict[str, Any] = field(default_factory=dict)
    technology_stack: List[str] = field(default_factory=list)


class IntegratedPythonAnalyzer:
    """
    Analisador Python integrado - Sistema completo de análise
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Inicializa o analisador integrado"""
        self.config = config or {}
        self.setup_logging()
        
        # Initialize component analyzers
        self.basic_analyzer = None
        self.advanced_analyzer = None
        self.sql_analyzer = None
        self.table_mapper = None
        
        self._initialize_analyzers()
        
        # Security patterns
        self.security_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'cursor\.execute\s*\(\s*["\'].*\+.*["\']',
                r'raw\s*\(\s*["\'].*%.*["\']'
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ],
            'insecure_functions': [
                r'\beval\s*\(',
                r'\bexec\s*\(',
                r'\binput\s*\(',
                r'pickle\.loads',
                r'yaml\.load\(',
                r'subprocess\.shell'
            ],
            'file_system': [
                r'open\s*\(',
                r'file\s*\(',
                r'os\.remove',
                r'os\.unlink',
                r'shutil\.',
                r'pathlib\.'
            ],
            'network_access': [
                r'urllib\.',
                r'requests\.',
                r'http\.',
                r'socket\.',
                r'ftp\.',
                r'smtp\.'
            ]
        }
        
        # Performance patterns
        self.performance_patterns = {
            'inefficient_loops': [
                r'for.*in.*range\(len\(',
                r'while.*len\('
            ],
            'string_concatenation': [
                r'\+\s*["\']',
                r'["\'].*\+.*["\']'
            ],
            'repeated_calculations': [
                r'for.*in.*:.*math\.',
                r'while.*:.*len\('
            ]
        }
        
    def setup_logging(self):
        """Configura logging"""
        logging.basicConfig(
            level=self.config.get('log_level', logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def _initialize_analyzers(self):
        """Inicializa os analisadores componentes"""
        try:
            self.basic_analyzer = CompletePythonAnalyzer(self.config)
            self.logger.info("Initialized basic Python analyzer")
        except Exception as e:
            self.logger.warning(f"Could not initialize basic analyzer: {e}")
            
        try:
            self.advanced_analyzer = AdvancedPythonFeaturesAnalyzer(self.config)
            self.logger.info("Initialized advanced features analyzer")
        except Exception as e:
            self.logger.warning(f"Could not initialize advanced analyzer: {e}")
            
        try:
            self.sql_analyzer = EnhancedSQLAnalyzer(self.config)
            self.logger.info("Initialized SQL analyzer")
        except Exception as e:
            self.logger.warning(f"Could not initialize SQL analyzer: {e}")
            
        try:
            self.table_mapper = PostgreSQLTableMapper()
            self.logger.info("Initialized table mapper")
        except Exception as e:
            self.logger.warning(f"Could not initialize table mapper: {e}")
    
    def analyze_project(self, project_path: str, scope: AnalysisScope = AnalysisScope.COMPLETE) -> ComprehensiveAnalysisResult:
        """
        Executa análise completa do projeto
        
        Args:
            project_path: Caminho do projeto
            scope: Escopo da análise
            
        Returns:
            Resultado completo da análise
        """
        start_time = time.time()
        self.logger.info(f"Starting {scope.value} analysis of {project_path}")
        
        # Find Python files
        python_files = self._find_python_files(project_path)
        self.logger.info(f"Found {len(python_files)} Python files")
        
        # Initialize result
        result = ComprehensiveAnalysisResult(
            project_path=project_path,
            analysis_timestamp=datetime.now().isoformat(),
            analysis_scope=scope,
            total_files_analyzed=len(python_files),
            analysis_duration_seconds=0.0
        )
        
        # Execute analyses based on scope
        if scope in [AnalysisScope.BASIC, AnalysisScope.COMPLETE, AnalysisScope.ENTERPRISE]:
            result.basic_analysis = self._run_basic_analysis(project_path)
            
        if scope in [AnalysisScope.ADVANCED, AnalysisScope.COMPLETE, AnalysisScope.ENTERPRISE]:
            result.advanced_features = self._run_advanced_analysis(python_files)
            
        if scope in [AnalysisScope.SQL_DATABASE, AnalysisScope.COMPLETE, AnalysisScope.ENTERPRISE]:
            result.sql_analysis = self._run_sql_analysis(python_files)
            
        if scope in [AnalysisScope.ENTERPRISE]:
            # Enterprise-specific analyses
            result.complexity_metrics = self._analyze_complexity(python_files)
            result.security_analysis = self._analyze_security(python_files)
            result.performance_analysis = self._analyze_performance(python_files)
            result.dependency_analysis = self._analyze_dependencies(project_path, python_files)
            
        # Calculate integrated scores
        result = self._calculate_integrated_scores(result)
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)
        
        # Generate specialized reports
        result.database_usage_report = self._generate_database_report(result)
        result.compatibility_report = self._generate_compatibility_report(result)
        result.technology_stack = self._detect_technology_stack(project_path)
        
        # Calculate duration
        result.analysis_duration_seconds = time.time() - start_time
        
        self.logger.info(f"Analysis completed in {result.analysis_duration_seconds:.2f} seconds")
        
        return result
    
    def _find_python_files(self, project_path: str) -> List[str]:
        """Encontra todos os arquivos Python no projeto"""
        python_files = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip virtual environments and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                '__pycache__', 'venv', 'env', '.venv', '.env', 
                'node_modules', '.git', '.pytest_cache'
            ]]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    python_files.append(os.path.join(root, file))
                    
        return python_files
    
    def _run_basic_analysis(self, project_path: str) -> Optional[PythonAnalysisResult]:
        """Executa análise básica"""
        if not self.basic_analyzer:
            return None
            
        try:
            self.logger.info("Running basic analysis...")
            return self.basic_analyzer.analyze_project(project_path)
        except Exception as e:
            self.logger.error(f"Basic analysis failed: {e}")
            return None
    
    def _run_advanced_analysis(self, python_files: List[str]) -> List[AdvancedFeatureUsage]:
        """Executa análise de recursos avançados"""
        if not self.advanced_analyzer:
            return []
            
        all_features = []
        
        try:
            self.logger.info("Running advanced features analysis...")
            
            # Use thread pool for parallel processing
            max_workers = min(4, len(python_files))
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self.advanced_analyzer.analyze_file, file_path): file_path
                    for file_path in python_files
                }
                
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        features = future.result()
                        all_features.extend(features)
                    except Exception as e:
                        self.logger.error(f"Advanced analysis failed for {file_path}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Advanced analysis failed: {e}")
            
        return all_features
    
    def _run_sql_analysis(self, python_files: List[str]) -> Optional[Dict[str, Any]]:
        """Executa análise SQL"""
        if not self.sql_analyzer and not self.table_mapper:
            return None
            
        sql_results = {
            'tables_analyzed': 0,
            'sql_statements': 0,
            'database_operations': [],
            'table_mappings': {},
            'sql_quality_issues': []
        }
        
        try:
            self.logger.info("Running SQL analysis...")
            
            for file_path in python_files:
                try:
                    # SQL analyzer
                    if self.sql_analyzer:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        sql_analysis = self.sql_analyzer.analyze_sql_content(content, file_path)
                        if sql_analysis:
                            sql_results['sql_statements'] += len(sql_analysis.get('statements', []))
                            sql_results['sql_quality_issues'].extend(sql_analysis.get('issues', []))
                    
                    # Table mapper
                    if self.table_mapper:
                        file_analysis = self.table_mapper.analyze_file(file_path)
                        if file_analysis:
                            sql_results['tables_analyzed'] += len(file_analysis.tables_read) + len(file_analysis.tables_written)
                            sql_results['table_mappings'][file_path] = {
                                'tables_read': [t.name for t in file_analysis.tables_read],
                                'tables_written': [t.name for t in file_analysis.tables_written]
                            }
                            
                except Exception as e:
                    self.logger.error(f"SQL analysis failed for {file_path}: {e}")
                    
        except Exception as e:
            self.logger.error(f"SQL analysis failed: {e}")
            
        return sql_results
    
    def _analyze_complexity(self, python_files: List[str]) -> CodeComplexityMetrics:
        """Analisa complexidade do código"""
        total_loc = 0
        total_logical_loc = 0
        total_comments = 0
        total_blank = 0
        total_cyclomatic = 0
        total_cognitive = 0
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                loc = len(lines)
                blank_lines = sum(1 for line in lines if not line.strip())
                comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
                logical_lines = loc - blank_lines - comment_lines
                
                total_loc += loc
                total_logical_loc += logical_lines
                total_comments += comment_lines
                total_blank += blank_lines
                
                # Calculate cyclomatic complexity (simplified)
                content = ''.join(lines)
                tree = ast.parse(content)
                cyclomatic = self._calculate_cyclomatic_complexity(tree)
                cognitive = self._calculate_cognitive_complexity(tree)
                
                total_cyclomatic += cyclomatic
                total_cognitive += cognitive
                
            except Exception as e:
                self.logger.error(f"Complexity analysis failed for {file_path}: {e}")
        
        # Calculate averages and metrics
        avg_cyclomatic = total_cyclomatic / len(python_files) if python_files else 0
        avg_cognitive = total_cognitive / len(python_files) if python_files else 0
        code_to_comment_ratio = total_logical_loc / max(total_comments, 1)
        
        # Simplified Halstead metrics
        halstead_difficulty = avg_cognitive * 2  # Simplified
        halstead_effort = halstead_difficulty * total_logical_loc
        
        # Maintainability index (simplified Microsoft formula)
        maintainability = max(0, 171 - 5.2 * avg_cyclomatic - 0.23 * avg_cognitive - 16.2 * 1)
        
        return CodeComplexityMetrics(
            cyclomatic_complexity=avg_cyclomatic,
            cognitive_complexity=avg_cognitive,
            halstead_difficulty=halstead_difficulty,
            halstead_effort=halstead_effort,
            maintainability_index=maintainability,
            lines_of_code=total_loc,
            logical_lines_of_code=total_logical_loc,
            comment_lines=total_comments,
            blank_lines=total_blank,
            code_to_comment_ratio=code_to_comment_ratio
        )
    
    def _analyze_security(self, python_files: List[str]) -> SecurityAnalysis:
        """Analisa aspectos de segurança"""
        vulnerabilities = []
        sql_injection_risks = []
        hardcoded_secrets = []
        insecure_functions = []
        file_system_access = []
        network_access = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.splitlines()
                
                for line_num, line in enumerate(lines, 1):
                    # Check for SQL injection risks
                    for pattern in self.security_patterns['sql_injection']:
                        if re.search(pattern, line, re.IGNORECASE):
                            sql_injection_risks.append({
                                'file': file_path,
                                'line': line_num,
                                'code': line.strip(),
                                'risk': 'SQL injection vulnerability'
                            })
                    
                    # Check for hardcoded secrets
                    for pattern in self.security_patterns['hardcoded_secrets']:
                        if re.search(pattern, line, re.IGNORECASE):
                            hardcoded_secrets.append({
                                'file': file_path,
                                'line': line_num,
                                'code': line.strip(),
                                'risk': 'Hardcoded secret detected'
                            })
                    
                    # Check for insecure functions
                    for pattern in self.security_patterns['insecure_functions']:
                        if re.search(pattern, line, re.IGNORECASE):
                            insecure_functions.append({
                                'file': file_path,
                                'line': line_num,
                                'code': line.strip(),
                                'risk': 'Potentially insecure function'
                            })
                    
                    # Check for file system access
                    for pattern in self.security_patterns['file_system']:
                        if re.search(pattern, line, re.IGNORECASE):
                            file_system_access.append({
                                'file': file_path,
                                'line': line_num,
                                'code': line.strip(),
                                'access_type': 'File system operation'
                            })
                    
                    # Check for network access
                    for pattern in self.security_patterns['network_access']:
                        if re.search(pattern, line, re.IGNORECASE):
                            network_access.append({
                                'file': file_path,
                                'line': line_num,
                                'code': line.strip(),
                                'access_type': 'Network operation'
                            })
                            
            except Exception as e:
                self.logger.error(f"Security analysis failed for {file_path}: {e}")
        
        # Compile all vulnerabilities
        vulnerabilities.extend(sql_injection_risks)
        vulnerabilities.extend([{**secret, 'type': 'hardcoded_secret'} for secret in hardcoded_secrets])
        vulnerabilities.extend([{**func, 'type': 'insecure_function'} for func in insecure_functions])
        
        # Calculate security score (0-100)
        total_issues = len(vulnerabilities)
        security_score = max(0, 100 - (total_issues * 10))
        
        return SecurityAnalysis(
            vulnerabilities=vulnerabilities,
            security_score=security_score,
            sql_injection_risks=sql_injection_risks,
            hardcoded_secrets=hardcoded_secrets,
            insecure_functions=insecure_functions,
            file_system_access=file_system_access,
            network_access=network_access
        )
    
    def _analyze_performance(self, python_files: List[str]) -> PerformanceAnalysis:
        """Analisa aspectos de performance"""
        performance_issues = []
        memory_concerns = []
        cpu_intensive_operations = []
        io_operations = []
        optimization_suggestions = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.splitlines()
                
                for line_num, line in enumerate(lines, 1):
                    # Check for inefficient loops
                    for pattern in self.performance_patterns['inefficient_loops']:
                        if re.search(pattern, line):
                            performance_issues.append({
                                'file': file_path,
                                'line': line_num,
                                'code': line.strip(),
                                'issue': 'Inefficient loop pattern',
                                'suggestion': 'Consider using enumerate() or direct iteration'
                            })
                    
                    # Check for string concatenation in loops
                    if 'for ' in line and '+=' in line and any(quote in line for quote in ['"', "'"]):
                        performance_issues.append({
                            'file': file_path,
                            'line': line_num,
                            'code': line.strip(),
                            'issue': 'String concatenation in loop',
                            'suggestion': 'Use list.append() and join() instead'
                        })
                    
                    # Memory concerns
                    if any(pattern in line.lower() for pattern in ['list(range(', 'range(10000', 'range(100000']):
                        memory_concerns.append({
                            'file': file_path,
                            'line': line_num,
                            'code': line.strip(),
                            'concern': 'Large range/list creation'
                        })
                    
                    # CPU intensive operations
                    if any(pattern in line.lower() for pattern in ['time.sleep', 'threading.', 'multiprocessing.']):
                        cpu_intensive_operations.append({
                            'file': file_path,
                            'line': line_num,
                            'code': line.strip(),
                            'operation': 'Threading/processing operation'
                        })
                    
                    # I/O operations
                    if any(pattern in line.lower() for pattern in ['open(', 'read()', 'write(', 'requests.']):
                        io_operations.append({
                            'file': file_path,
                            'line': line_num,
                            'code': line.strip(),
                            'operation': 'I/O operation'
                        })
                        
            except Exception as e:
                self.logger.error(f"Performance analysis failed for {file_path}: {e}")
        
        # Generate optimization suggestions
        if performance_issues:
            optimization_suggestions.append({
                'category': 'Loop optimization',
                'description': 'Several inefficient loop patterns detected',
                'priority': 'high',
                'impact': 'performance'
            })
        
        if memory_concerns:
            optimization_suggestions.append({
                'category': 'Memory optimization',
                'description': 'Large data structure creation detected',
                'priority': 'medium',
                'impact': 'memory'
            })
        
        # Calculate performance score
        total_issues = len(performance_issues) + len(memory_concerns)
        performance_score = max(0, 100 - (total_issues * 5))
        
        return PerformanceAnalysis(
            performance_issues=performance_issues,
            performance_score=performance_score,
            database_efficiency={'analyzed': False},  # Would need SQL analysis integration
            memory_concerns=memory_concerns,
            cpu_intensive_operations=cpu_intensive_operations,
            io_operations=io_operations,
            optimization_suggestions=optimization_suggestions
        )
    
    def _analyze_dependencies(self, project_path: str, python_files: List[str]) -> DependencyAnalysis:
        """Analisa dependências do projeto"""
        internal_deps = {}
        external_deps = {}
        all_imports = set()
        file_imports = {}
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                file_imports[file_path] = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name
                            all_imports.add(module_name)
                            file_imports[file_path].append(module_name)
                            
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_name = node.module
                            all_imports.add(module_name)
                            file_imports[file_path].append(module_name)
                            
            except Exception as e:
                self.logger.error(f"Dependency analysis failed for {file_path}: {e}")
        
        # Separate internal vs external dependencies
        project_modules = set()
        for file_path in python_files:
            rel_path = os.path.relpath(file_path, project_path)
            module_path = rel_path.replace(os.sep, '.').replace('.py', '')
            project_modules.add(module_path)
        
        for module in all_imports:
            if any(module.startswith(pm) for pm in project_modules):
                # Internal dependency
                if module not in internal_deps:
                    internal_deps[module] = []
            else:
                # External dependency
                external_deps[module] = "unknown_version"
        
        # Build internal dependency mappings
        for file_path, imports in file_imports.items():
            rel_path = os.path.relpath(file_path, project_path)
            module_path = rel_path.replace(os.sep, '.').replace('.py', '')
            
            internal_deps[module_path] = [
                imp for imp in imports 
                if any(imp.startswith(pm) for pm in project_modules)
            ]
        
        # Detect circular dependencies (simplified)
        circular_deps = []
        for module, deps in internal_deps.items():
            for dep in deps:
                if dep in internal_deps and module in internal_deps[dep]:
                    circular_deps.append((module, dep))
        
        # Calculate dependency risk score
        risk_factors = len(circular_deps) * 20 + len(external_deps) * 2
        dependency_risk_score = min(100, risk_factors)
        
        return DependencyAnalysis(
            internal_dependencies=internal_deps,
            external_dependencies=external_deps,
            circular_dependencies=circular_deps,
            unused_imports=[],  # Would need more sophisticated analysis
            missing_dependencies=[],  # Would need import resolution
            dependency_tree=internal_deps,
            dependency_risk_score=dependency_risk_score
        )
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calcula complexidade ciclomática"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
                
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calcula complexidade cognitiva (simplificada)"""
        complexity = 0
        nesting_level = 0
        
        class CognitiveVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 0
                self.nesting = 0
                
            def visit_If(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
                
            def visit_For(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
                
            def visit_While(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
        
        visitor = CognitiveVisitor()
        visitor.visit(tree)
        return visitor.complexity
    
    def _calculate_integrated_scores(self, result: ComprehensiveAnalysisResult) -> ComprehensiveAnalysisResult:
        """Calcula scores integrados"""
        scores = []
        
        # Basic analysis score
        if result.basic_analysis:
            scores.append(result.basic_analysis.code_quality_score)
        
        # Security score
        if result.security_analysis:
            scores.append(result.security_analysis.security_score)
            result.security_score = result.security_analysis.security_score
        
        # Performance score
        if result.performance_analysis:
            scores.append(result.performance_analysis.performance_score)
            result.performance_score = result.performance_analysis.performance_score
        
        # Maintainability score
        if result.complexity_metrics:
            result.maintainability_score = result.complexity_metrics.maintainability_index
            scores.append(result.maintainability_score)
        
        # Overall quality score
        result.overall_quality_score = sum(scores) / len(scores) if scores else 0.0
        
        return result
    
    def _generate_recommendations(self, result: ComprehensiveAnalysisResult) -> List[Dict[str, Any]]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        # Security recommendations
        if result.security_analysis and result.security_analysis.vulnerabilities:
            recommendations.append({
                'category': 'Security',
                'priority': 'critical',
                'title': 'Security vulnerabilities detected',
                'description': f'Found {len(result.security_analysis.vulnerabilities)} security issues',
                'action': 'Review and fix security vulnerabilities',
                'impact': 'high'
            })
        
        # Performance recommendations
        if result.performance_analysis and result.performance_analysis.performance_issues:
            recommendations.append({
                'category': 'Performance',
                'priority': 'high',
                'title': 'Performance optimizations available',
                'description': f'Found {len(result.performance_analysis.performance_issues)} performance issues',
                'action': 'Optimize inefficient code patterns',
                'impact': 'medium'
            })
        
        # Complexity recommendations
        if result.complexity_metrics and result.complexity_metrics.cyclomatic_complexity > 10:
            recommendations.append({
                'category': 'Code Quality',
                'priority': 'medium',
                'title': 'High code complexity detected',
                'description': f'Average cyclomatic complexity: {result.complexity_metrics.cyclomatic_complexity:.1f}',
                'action': 'Refactor complex functions and classes',
                'impact': 'medium'
            })
        
        # Dependency recommendations
        if result.dependency_analysis and result.dependency_analysis.circular_dependencies:
            recommendations.append({
                'category': 'Architecture',
                'priority': 'high',
                'title': 'Circular dependencies detected',
                'description': f'Found {len(result.dependency_analysis.circular_dependencies)} circular dependencies',
                'action': 'Refactor to eliminate circular dependencies',
                'impact': 'high'
            })
        
        return recommendations
    
    def _generate_database_report(self, result: ComprehensiveAnalysisResult) -> Dict[str, Any]:
        """Gera relatório de uso de banco de dados"""
        if not result.sql_analysis:
            return {}
        
        return {
            'total_sql_statements': result.sql_analysis.get('sql_statements', 0),
            'tables_analyzed': result.sql_analysis.get('tables_analyzed', 0),
            'database_operations': result.sql_analysis.get('database_operations', []),
            'table_mappings': result.sql_analysis.get('table_mappings', {}),
            'quality_issues': result.sql_analysis.get('sql_quality_issues', [])
        }
    
    def _generate_compatibility_report(self, result: ComprehensiveAnalysisResult) -> Dict[str, Any]:
        """Gera relatório de compatibilidade"""
        if not result.advanced_features:
            return {'minimum_python_version': '3.6'}
        
        # Use advanced analyzer's compatibility report
        if self.advanced_analyzer:
            return self.advanced_analyzer.generate_compatibility_report(result.advanced_features)
        
        return {'minimum_python_version': '3.6'}
    
    def _detect_technology_stack(self, project_path: str) -> List[str]:
        """Detecta stack tecnológico do projeto"""
        stack = []
        
        # Check for common Python frameworks
        try:
            requirements_files = ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile']
            
            for req_file in requirements_files:
                req_path = os.path.join(project_path, req_file)
                if os.path.exists(req_path):
                    with open(req_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    
                    frameworks = {
                        'django': 'Django',
                        'flask': 'Flask',
                        'fastapi': 'FastAPI',
                        'airflow': 'Apache Airflow',
                        'pandas': 'Pandas',
                        'numpy': 'NumPy',
                        'sqlalchemy': 'SQLAlchemy',
                        'psycopg2': 'PostgreSQL',
                        'pymongo': 'MongoDB',
                        'requests': 'Requests',
                        'pytest': 'PyTest',
                        'jupyter': 'Jupyter'
                    }
                    
                    for keyword, framework in frameworks.items():
                        if keyword in content and framework not in stack:
                            stack.append(framework)
        
        except Exception as e:
            self.logger.error(f"Technology stack detection failed: {e}")
        
        return stack
    
    def export_results(self, result: ComprehensiveAnalysisResult, output_path: str):
        """Exporta resultados para arquivo JSON"""
        try:
            # Convert to dict and handle non-serializable objects
            result_dict = asdict(result)
            
            # Convert enums and other objects
            self._clean_dict_for_json(result_dict)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Results exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
    
    def _clean_dict_for_json(self, obj):
        """Limpa dicionário para serialização JSON"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if hasattr(value, 'value'):  # Enum
                    obj[key] = value.value
                elif isinstance(value, (dict, list)):
                    self._clean_dict_for_json(value)
                elif not isinstance(value, (str, int, float, bool, type(None))):
                    obj[key] = str(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if hasattr(item, 'value'):  # Enum
                    obj[i] = item.value
                elif isinstance(item, (dict, list)):
                    self._clean_dict_for_json(item)
                elif not isinstance(item, (str, int, float, bool, type(None))):
                    obj[i] = str(item)


def main():
    """Função principal para teste"""
    analyzer = IntegratedPythonAnalyzer({
        'log_level': logging.INFO,
        'enable_parallel_processing': True
    })
    
    # Analyze current directory
    current_dir = os.path.dirname(__file__)
    result = analyzer.analyze_project(current_dir, AnalysisScope.COMPLETE)
    
    print(f"Analysis Results for {current_dir}")
    print(f"Total files analyzed: {result.total_files_analyzed}")
    print(f"Analysis duration: {result.analysis_duration_seconds:.2f} seconds")
    print(f"Overall quality score: {result.overall_quality_score:.1f}/100")
    
    if result.recommendations:
        print("\nTop Recommendations:")
        for rec in result.recommendations[:3]:
            print(f"- {rec['title']} ({rec['priority']} priority)")
    
    # Export results
    output_path = os.path.join(current_dir, 'analysis_results.json')
    analyzer.export_results(result, output_path)
    print(f"\nDetailed results exported to: {output_path}")


if __name__ == "__main__":
    main()
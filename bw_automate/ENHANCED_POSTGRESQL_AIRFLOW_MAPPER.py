#!/usr/bin/env python3
"""
🚁 ENHANCED POSTGRESQL AIRFLOW MAPPER
Sistema avançado para mapear PostgreSQL em ambientes complexos:
- Códigos Python standalone
- DAGs Airflow chamando Pythons
- Chains de parâmetros entre arquivos
- Decorators, classes e funções interconectadas
"""

import ast
import re
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import networkx as nx

@dataclass
class ParameterFlow:
    """Fluxo de parâmetros entre arquivos"""
    source_file: str
    target_file: str
    parameter_name: str
    parameter_value: Any
    flow_type: str  # 'function_call', 'import', 'dag_task', 'decorator'
    line_number: int = 0
    confidence: float = 1.0

@dataclass
class TableReference:
    """Referência a uma tabela encontrada"""
    table_name: str
    schema: Optional[str] = None
    file_path: str = ""
    line_number: int = 0
    column_number: int = 0
    context_type: str = ""  # 'sql_string', 'orm_class', 'decorator', 'function_call', 'dag_param'
    context_details: Dict[str, Any] = field(default_factory=dict)
    operation_type: str = ""  
    confidence: float = 1.0
    raw_content: str = ""
    parameter_chain: List[str] = field(default_factory=list)  # Chain de parâmetros que levou à tabela
    
    def __post_init__(self):
        # Normaliza nome da tabela
        self.table_name = self.table_name.strip('"\'`').lower()
        if self.schema:
            self.schema = self.schema.strip('"\'`').lower()

@dataclass
class DAGWorkflow:
    """Workflow de DAG do Airflow"""
    dag_file: str
    dag_id: str
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    task_dependencies: List[Tuple[str, str]] = field(default_factory=list)
    python_callables: List[str] = field(default_factory=list)
    parameters_passed: Dict[str, Any] = field(default_factory=dict)

class EnhancedPostgreSQLAirflowMapper:
    """Mapeador avançado para PostgreSQL em ambientes Python + Airflow"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.table_references: List[TableReference] = []
        self.parameter_flows: List[ParameterFlow] = []
        self.dag_workflows: List[DAGWorkflow] = []
        self.analyzed_files: Set[str] = set()
        self.dependency_graph = nx.DiGraph()
        
        # Padrões para detecção
        self.sql_patterns = self._initialize_sql_patterns()
        self.orm_patterns = self._initialize_orm_patterns()
        self.decorator_patterns = self._initialize_decorator_patterns()
        self.airflow_patterns = self._initialize_airflow_patterns()
        
        # Cache para análise de parâmetros
        self.function_definitions: Dict[str, Dict] = {}
        self.variable_assignments: Dict[str, Dict] = {}
        self.import_mappings: Dict[str, Set[str]] = defaultdict(set)
        
    def _setup_logging(self):
        """Setup logging para debugging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def _initialize_sql_patterns(self) -> List[Dict]:
        """Padrões SQL melhorados para diferentes contextos"""
        return [
            # CREATE TABLE (mais específico)
            {
                'pattern': r'(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'CREATE',
                'confidence': 0.99
            },
            # DROP TABLE
            {
                'pattern': r'(?i)DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'DROP',
                'confidence': 0.99
            },
            # SELECT FROM com schema
            {
                'pattern': r'(?i)SELECT\s+.*?\bFROM\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'SELECT',
                'confidence': 0.98
            },
            # SELECT FROM sem schema
            {
                'pattern': r'(?i)SELECT\s+.*?\bFROM\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|$|,|\))',
                'table_group': 1,
                'schema_group': None,
                'operation': 'SELECT',
                'confidence': 0.90
            },
            # INSERT INTO
            {
                'pattern': r'(?i)INSERT\s+INTO\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'INSERT',
                'confidence': 0.95
            },
            # UPDATE
            {
                'pattern': r'(?i)UPDATE\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)\s+SET',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'UPDATE',
                'confidence': 0.95
            },
            # DELETE FROM
            {
                'pattern': r'(?i)DELETE\s+FROM\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'DELETE',
                'confidence': 0.95
            },
            # JOIN patterns
            {
                'pattern': r'(?i)(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)\s+',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'JOIN',
                'confidence': 0.85
            },
            # Tabelas em variáveis Python (ex: table_name = "users")
            {
                'pattern': r'(?:table_name|table|tbl)\s*=\s*["\'](?:(\w+)\.)?(\w+)["\']',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'VARIABLE',
                'confidence': 0.80
            }
        ]
    
    def _initialize_orm_patterns(self) -> List[Dict]:
        """Padrões ORM expandidos"""
        return [
            # SQLAlchemy Table
            {
                'pattern': r'Table\s*\(\s*["\'](\w+)["\']',
                'table_group': 1,
                'context': 'sqlalchemy_table',
                'confidence': 0.95
            },
            # SQLAlchemy __tablename__
            {
                'pattern': r'__tablename__\s*=\s*["\'](\w+)["\']',
                'table_group': 1,
                'context': 'sqlalchemy_model',
                'confidence': 0.98
            },
            # Django Meta class
            {
                'pattern': r'db_table\s*=\s*["\'](\w+)["\']',
                'table_group': 1,
                'context': 'django_model',
                'confidence': 0.95
            },
            # Peewee Model
            {
                'pattern': r'table_name\s*=\s*["\'](\w+)["\']',
                'table_group': 1,
                'context': 'peewee_model',
                'confidence': 0.90
            },
            # Raw SQL execution
            {
                'pattern': r'(?:execute|executemany|cursor\.execute)\s*\(\s*["\']([^"\']*)["\']',
                'sql_group': 1,
                'context': 'raw_sql_execution',
                'confidence': 0.85
            },
            # Pandas read_sql
            {
                'pattern': r'pd\.read_sql\s*\(\s*["\']([^"\']*)["\']',
                'sql_group': 1,
                'context': 'pandas_sql',
                'confidence': 0.90
            }
        ]
    
    def _initialize_decorator_patterns(self) -> List[Dict]:
        """Padrões de decorators expandidos"""
        return [
            # @table decorator
            {
                'pattern': r'@table\s*\(\s*["\'](\w+)["\']',
                'table_group': 1,
                'confidence': 0.90
            },
            # @database_table
            {
                'pattern': r'@database_table\s*\(\s*["\'](\w+)["\']',
                'table_group': 1,
                'confidence': 0.90
            },
            # Custom decorators
            {
                'pattern': r'@\w*(?:table|db|database)\w*\s*\(\s*["\'](\w+)["\']',
                'table_group': 1,
                'confidence': 0.80
            },
            # Airflow task decorators with table parameters
            {
                'pattern': r'@task\s*\([^)]*table\s*=\s*["\'](\w+)["\']',
                'table_group': 1,
                'confidence': 0.85
            }
        ]
    
    def _initialize_airflow_patterns(self) -> List[Dict]:
        """Padrões específicos do Airflow"""
        return [
            # DAG definition
            {
                'pattern': r'DAG\s*\(\s*["\'](\w+)["\']',
                'dag_group': 1,
                'confidence': 0.99
            },
            # PythonOperator
            {
                'pattern': r'PythonOperator\s*\([^)]*python_callable\s*=\s*(\w+)',
                'callable_group': 1,
                'confidence': 0.95
            },
            # BashOperator with Python scripts
            {
                'pattern': r'BashOperator\s*\([^)]*bash_command\s*=\s*["\']python3?\s+([^"\']+\.py)',
                'script_group': 1,
                'confidence': 0.90
            },
            # Task dependencies
            {
                'pattern': r'(\w+)\s*>>\s*(\w+)',
                'source_task': 1,
                'target_task': 2,
                'confidence': 0.95
            },
            # XCom push/pull com tabelas
            {
                'pattern': r'xcom_(?:push|pull)\s*\([^)]*["\']table["\'].*?["\'](\w+)["\']',
                'table_group': 1,
                'confidence': 0.80
            }
        ]
    
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Análise completa do projeto com foco em Airflow + Python"""
        start_time = time.time()
        project_path = Path(project_path)
        
        self.logger.info(f"🚁 Iniciando análise avançada Airflow+PostgreSQL em {project_path}")
        
        # Encontra todos os arquivos Python
        python_files = list(project_path.rglob("*.py"))
        self.logger.info(f"📁 Encontrados {len(python_files)} arquivos Python")
        
        # Primeira passada: Mapeia estrutura básica
        self._first_pass_analysis(python_files)
        
        # Segunda passada: Análise detalhada com contexto
        self._second_pass_analysis(python_files)
        
        # Terceira passada: Rastreamento de parâmetros
        self._parameter_flow_analysis()
        
        # Quarta passada: Workflows de DAG
        self._dag_workflow_analysis()
        
        # Constrói mapa final
        analysis_time = time.time() - start_time
        results = self._build_enhanced_comprehensive_map(analysis_time)
        
        return results
    
    def _first_pass_analysis(self, python_files: List[Path]):
        """Primeira passada: mapeia funções, classes e imports"""
        self.logger.info("🔍 Primeira passada: mapeando estrutura...")
        
        for file_path in python_files:
            try:
                self._analyze_file_structure(str(file_path))
            except Exception as e:
                self.logger.error(f"❌ Erro na primeira passada {file_path}: {e}")
    
    def _second_pass_analysis(self, python_files: List[Path]):
        """Segunda passada: análise detalhada com contexto"""
        self.logger.info("🔍 Segunda passada: análise detalhada...")
        
        for file_path in python_files:
            try:
                self._analyze_file_detailed(str(file_path))
            except Exception as e:
                self.logger.error(f"❌ Erro na segunda passada {file_path}: {e}")
    
    def _analyze_file_structure(self, file_path: str):
        """Analisa estrutura básica do arquivo"""
        if file_path in self.analyzed_files:
            return
            
        try:
            # Tenta diferentes encodings
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return
            
            if not content.strip():
                return
            
            # Parse AST para estrutura
            try:
                tree = ast.parse(content)
                self._extract_file_structure(tree, file_path)
            except SyntaxError:
                # Tenta extrair informações básicas mesmo com erro de sintaxe
                self._extract_basic_info_no_ast(content, file_path)
            
        except Exception as e:
            self.logger.debug(f"Erro na análise de estrutura {file_path}: {e}")
    
    def _extract_file_structure(self, tree: ast.AST, file_path: str):
        """Extrai estrutura do arquivo usando AST"""
        
        class StructureExtractor(ast.NodeVisitor):
            def __init__(self, mapper, file_path):
                self.mapper = mapper
                self.file_path = file_path
                
            def visit_FunctionDef(self, node):
                # Mapeia definições de função
                func_info = {
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'line': node.lineno,
                    'file': self.file_path
                }
                
                if self.file_path not in self.mapper.function_definitions:
                    self.mapper.function_definitions[self.file_path] = {}
                self.mapper.function_definitions[self.file_path][node.name] = func_info
                
                self.generic_visit(node)
            
            def visit_Assign(self, node):
                # Mapeia atribuições de variáveis
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_info = {
                            'name': target.id,
                            'line': node.lineno,
                            'file': self.file_path
                        }
                        
                        if hasattr(node.value, 's'):  # String literal
                            var_info['value'] = node.value.s
                        elif hasattr(node.value, 'n'):  # Number literal
                            var_info['value'] = node.value.n
                        
                        if self.file_path not in self.mapper.variable_assignments:
                            self.mapper.variable_assignments[self.file_path] = {}
                        self.mapper.variable_assignments[self.file_path][target.id] = var_info
                
                self.generic_visit(node)
            
            def visit_Import(self, node):
                # Mapeia imports
                for alias in node.names:
                    self.mapper.import_mappings[self.file_path].add(alias.name)
                
            def visit_ImportFrom(self, node):
                # Mapeia from imports
                if node.module:
                    for alias in node.names:
                        self.mapper.import_mappings[self.file_path].add(f"{node.module}.{alias.name}")
        
        extractor = StructureExtractor(self, file_path)
        extractor.visit(tree)
    
    def _extract_basic_info_no_ast(self, content: str, file_path: str):
        """Extrai informações básicas sem AST (para arquivos com erro de sintaxe)"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Detecta definições de função
            func_match = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', line.strip())
            if func_match:
                func_name = func_match.group(1)
                func_info = {
                    'name': func_name,
                    'args': [arg.strip() for arg in func_match.group(2).split(',') if arg.strip()],
                    'line': line_num,
                    'file': file_path
                }
                
                if file_path not in self.function_definitions:
                    self.function_definitions[file_path] = {}
                self.function_definitions[file_path][func_name] = func_info
            
            # Detecta imports
            import_match = re.match(r'(?:from\s+(\S+)\s+)?import\s+(.+)', line.strip())
            if import_match:
                module = import_match.group(1)
                imports = import_match.group(2)
                
                for imp in imports.split(','):
                    imp = imp.strip()
                    if module:
                        self.import_mappings[file_path].add(f"{module}.{imp}")
                    else:
                        self.import_mappings[file_path].add(imp)
    
    def _analyze_file_detailed(self, file_path: str):
        """Análise detalhada do arquivo"""
        try:
            content = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None or not content.strip():
                return
            
            # Análises de padrões SQL/ORM
            self._analyze_sql_patterns(content, file_path)
            self._analyze_orm_patterns(content, file_path)
            self._analyze_decorator_patterns(content, file_path)
            
            # Análise específica do Airflow
            if self._is_airflow_file(content):
                self._analyze_airflow_patterns(content, file_path)
            
            # AST analysis para contexto avançado
            try:
                tree = ast.parse(content)
                self._analyze_advanced_ast(tree, file_path, content)
            except SyntaxError:
                pass
                
        except Exception as e:
            self.logger.debug(f"Erro na análise detalhada {file_path}: {e}")
    
    def _is_airflow_file(self, content: str) -> bool:
        """Verifica se é um arquivo do Airflow"""
        airflow_indicators = [
            'from airflow',
            'import airflow',
            'DAG(',
            'PythonOperator',
            'BashOperator',
            '@dag',
            '@task'
        ]
        
        return any(indicator in content for indicator in airflow_indicators)
    
    def _analyze_sql_patterns(self, content: str, file_path: str):
        """Análise de padrões SQL com contexto melhorado"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.sql_patterns:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    table_group = pattern_info['table_group']
                    schema_group = pattern_info.get('schema_group')
                    operation = pattern_info.get('operation', 'UNKNOWN')
                    
                    table_name = match.group(table_group) if match.group(table_group) else ""
                    schema = match.group(schema_group) if schema_group and match.group(schema_group) else None
                    
                    # Filtros para evitar falsos positivos
                    if (table_name and len(table_name) > 1 and 
                        table_name.lower() not in ['if', 'not', 'exists', 'from', 'to', 'set', 'where', 'and', 'or', 'as', 'on']):
                        
                        # Detecta cadeia de parâmetros
                        param_chain = self._trace_parameter_chain(file_path, line_num, table_name)
                        
                        ref = TableReference(
                            table_name=table_name,
                            schema=schema.rstrip('.') if schema else None,
                            file_path=file_path,
                            line_number=line_num,
                            column_number=match.start(),
                            context_type='sql_string',
                            operation_type=operation,
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip(),
                            parameter_chain=param_chain,
                            context_details={
                                'full_match': match.group(0),
                                'pattern_used': pattern,
                                'surrounding_context': self._get_surrounding_context(lines, line_num)
                            }
                        )
                        self.table_references.append(ref)
    
    def _analyze_orm_patterns(self, content: str, file_path: str):
        """Análise de padrões ORM expandida"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.orm_patterns:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    if 'table_group' in pattern_info:
                        # Padrão direto de tabela
                        table_name = match.group(pattern_info['table_group'])
                        
                        # Detecta cadeia de parâmetros
                        param_chain = self._trace_parameter_chain(file_path, line_num, table_name)
                        
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            column_number=match.start(),
                            context_type='orm_pattern',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip(),
                            parameter_chain=param_chain,
                            context_details={
                                'orm_context': pattern_info['context'],
                                'full_match': match.group(0)
                            }
                        )
                        self.table_references.append(ref)
                    
                    elif 'sql_group' in pattern_info:
                        # SQL dentro de execute() ou pandas
                        sql_content = match.group(pattern_info['sql_group'])
                        self._extract_tables_from_embedded_sql(sql_content, file_path, line_num, pattern_info['context'])
    
    def _analyze_decorator_patterns(self, content: str, file_path: str):
        """Análise de decorators expandida"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.decorator_patterns:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    # Detecta cadeia de parâmetros
                    param_chain = self._trace_parameter_chain(file_path, line_num, table_name)
                    
                    ref = TableReference(
                        table_name=table_name,
                        file_path=file_path,
                        line_number=line_num,
                        column_number=match.start(),
                        context_type='decorator',
                        confidence=pattern_info['confidence'],
                        raw_content=line.strip(),
                        parameter_chain=param_chain,
                        context_details={
                            'decorator_type': 'table_decorator',
                            'full_match': match.group(0),
                            'next_function': self._get_next_function(lines, line_num)
                        }
                    )
                    self.table_references.append(ref)
    
    def _analyze_airflow_patterns(self, content: str, file_path: str):
        """Análise específica de padrões Airflow"""
        lines = content.split('\n')
        
        # Extrai informações de DAG
        dag_info = self._extract_dag_info(content, file_path)
        if dag_info:
            self.dag_workflows.append(dag_info)
        
        # Procura por operadores que chamam Python
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.airflow_patterns:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    if 'callable_group' in pattern_info:
                        # PythonOperator callable
                        callable_name = match.group(pattern_info['callable_group'])
                        self._trace_python_callable(callable_name, file_path, line_num)
                    
                    elif 'script_group' in pattern_info:
                        # Script Python chamado via Bash
                        script_path = match.group(pattern_info['script_group'])
                        self._trace_python_script(script_path, file_path, line_num)
                    
                    elif 'table_group' in pattern_info:
                        # Tabela passada via XCom
                        table_name = match.group(pattern_info['table_group'])
                        
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='dag_param',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip(),
                            context_details={
                                'airflow_context': 'xcom_parameter',
                                'full_match': match.group(0)
                            }
                        )
                        self.table_references.append(ref)
    
    def _analyze_advanced_ast(self, tree: ast.AST, file_path: str, content: str):
        """Análise AST avançada para rastreamento de parâmetros"""
        
        class AdvancedASTAnalyzer(ast.NodeVisitor):
            def __init__(self, mapper, file_path, content):
                self.mapper = mapper
                self.file_path = file_path
                self.content = content
                self.current_function = None
                self.current_class = None
            
            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                
                # Procura por __tablename__ e similares
                for child in node.body:
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                if target.id in ['__tablename__', 'table_name', '_table_name']:
                                    if isinstance(child.value, ast.Constant):
                                        table_name = child.value.value
                                        if isinstance(table_name, str):
                                            param_chain = self.mapper._trace_parameter_chain(
                                                self.file_path, child.lineno, table_name
                                            )
                                            
                                            ref = TableReference(
                                                table_name=table_name,
                                                file_path=self.file_path,
                                                line_number=child.lineno,
                                                context_type='orm_class',
                                                confidence=0.95,
                                                parameter_chain=param_chain,
                                                context_details={
                                                    'class_name': self.current_class,
                                                    'attribute': target.id
                                                }
                                            )
                                            self.mapper.table_references.append(ref)
                
                self.generic_visit(node)
                self.current_class = old_class
            
            def visit_FunctionDef(self, node):
                old_function = self.current_function
                self.current_function = node.name
                
                # Analisa parâmetros da função que podem ser tabelas
                for arg in node.args.args:
                    if 'table' in arg.arg.lower():
                        # Este parâmetro pode ser um nome de tabela
                        param_info = {
                            'function': node.name,
                            'parameter': arg.arg,
                            'line': node.lineno,
                            'file': self.file_path,
                            'type': 'table_parameter'
                        }
                        # Adiciona ao mapeamento de fluxo de parâmetros
                        # (será usado na análise de fluxo)
                
                self.generic_visit(node)
                self.current_function = old_function
            
            def visit_Call(self, node):
                # Analisa chamadas de função que podem passar tabelas
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    # Funções que tipicamente recebem nomes de tabela
                    table_functions = [
                        'Table', 'create_table', 'drop_table', 'truncate_table',
                        'select_from', 'insert_into', 'update_table', 'delete_from',
                        'read_sql', 'to_sql', 'execute', 'executemany'
                    ]
                    
                    if func_name in table_functions and node.args:
                        for i, arg in enumerate(node.args):
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                # Argumento literal de string pode ser tabela
                                table_name = arg.value
                                param_chain = self.mapper._trace_parameter_chain(
                                    self.file_path, node.lineno, table_name
                                )
                                
                                ref = TableReference(
                                    table_name=table_name,
                                    file_path=self.file_path,
                                    line_number=node.lineno,
                                    context_type='function_call',
                                    confidence=0.85,
                                    parameter_chain=param_chain,
                                    context_details={
                                        'function_name': func_name,
                                        'argument_position': i,
                                        'class_context': self.current_class,
                                        'function_context': self.current_function
                                    }
                                )
                                self.mapper.table_references.append(ref)
                            
                            elif isinstance(arg, ast.Name):
                                # Argumento variável - rastreia origem
                                var_name = arg.id
                                self.mapper._trace_variable_origin(
                                    var_name, self.file_path, node.lineno, func_name
                                )
                
                self.generic_visit(node)
        
        analyzer = AdvancedASTAnalyzer(self, file_path, content)
        analyzer.visit(tree)
    
    def _trace_parameter_chain(self, file_path: str, line_num: int, value: str) -> List[str]:
        """Rastreia cadeia de parâmetros que levou a um valor"""
        chain = []
        
        # Verifica se o valor é uma variável conhecida no arquivo
        if file_path in self.variable_assignments:
            for var_name, var_info in self.variable_assignments[file_path].items():
                if var_info.get('value') == value:
                    chain.append(f"variable:{var_name}")
                    break
        
        # Verifica se vem de uma função
        if file_path in self.function_definitions:
            for func_name, func_info in self.function_definitions[file_path].items():
                if abs(func_info['line'] - line_num) < 20:  # Proximidade de linha
                    chain.append(f"function:{func_name}")
                    break
        
        # Verifica imports relacionados
        for imported in self.import_mappings.get(file_path, set()):
            if 'table' in imported.lower() or 'db' in imported.lower():
                chain.append(f"import:{imported}")
        
        return chain
    
    def _trace_variable_origin(self, var_name: str, file_path: str, line_num: int, context: str):
        """Rastreia origem de uma variável"""
        # Procura definição da variável no arquivo atual
        if file_path in self.variable_assignments:
            if var_name in self.variable_assignments[file_path]:
                var_info = self.variable_assignments[file_path][var_name]
                if 'value' in var_info and isinstance(var_info['value'], str):
                    # Variável contém string - pode ser tabela
                    table_name = var_info['value']
                    param_chain = [f"variable:{var_name}"]
                    
                    ref = TableReference(
                        table_name=table_name,
                        file_path=file_path,
                        line_number=line_num,
                        context_type='variable_reference',
                        confidence=0.75,
                        parameter_chain=param_chain,
                        context_details={
                            'variable_name': var_name,
                            'variable_definition_line': var_info['line'],
                            'context_function': context
                        }
                    )
                    self.table_references.append(ref)
    
    def _trace_python_callable(self, callable_name: str, dag_file: str, line_num: int):
        """Rastreia callable Python usado em DAG"""
        # Procura definição da função no mesmo arquivo
        if dag_file in self.function_definitions:
            if callable_name in self.function_definitions[dag_file]:
                func_info = self.function_definitions[dag_file][callable_name]
                
                # Cria fluxo de parâmetro DAG -> função
                flow = ParameterFlow(
                    source_file=dag_file,
                    target_file=dag_file,  # Mesmo arquivo
                    parameter_name=callable_name,
                    parameter_value=func_info,
                    flow_type='dag_task',
                    line_number=line_num,
                    confidence=0.95
                )
                self.parameter_flows.append(flow)
        
        # Procura em outros arquivos (import)
        for file_path, imports in self.import_mappings.items():
            if callable_name in imports or any(callable_name in imp for imp in imports):
                flow = ParameterFlow(
                    source_file=dag_file,
                    target_file=file_path,
                    parameter_name=callable_name,
                    parameter_value=None,
                    flow_type='imported_callable',
                    line_number=line_num,
                    confidence=0.80
                )
                self.parameter_flows.append(flow)
    
    def _trace_python_script(self, script_path: str, dag_file: str, line_num: int):
        """Rastreia script Python chamado via bash"""
        # Normaliza path do script
        if not script_path.startswith('/'):
            # Path relativo - tenta resolver
            dag_dir = Path(dag_file).parent
            full_script_path = dag_dir / script_path
        else:
            full_script_path = Path(script_path)
        
        if full_script_path.exists():
            flow = ParameterFlow(
                source_file=dag_file,
                target_file=str(full_script_path),
                parameter_name='bash_script',
                parameter_value=script_path,
                flow_type='bash_callable',
                line_number=line_num,
                confidence=0.85
            )
            self.parameter_flows.append(flow)
    
    def _extract_dag_info(self, content: str, file_path: str) -> Optional[DAGWorkflow]:
        """Extrai informações de DAG do Airflow"""
        dag_id_match = re.search(r'DAG\s*\(\s*["\'](\w+)["\']', content)
        if not dag_id_match:
            return None
        
        dag_id = dag_id_match.group(1)
        
        dag_workflow = DAGWorkflow(
            dag_file=file_path,
            dag_id=dag_id
        )
        
        # Extrai tasks
        task_patterns = [
            r'(\w+)\s*=\s*PythonOperator',
            r'(\w+)\s*=\s*BashOperator',
            r'@task[^)]*\)\s*def\s+(\w+)',
        ]
        
        for pattern in task_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                task_name = match.group(1)
                dag_workflow.tasks.append({
                    'name': task_name,
                    'type': 'python' if 'Python' in pattern else 'bash',
                    'line': content[:match.start()].count('\n') + 1
                })
        
        # Extrai dependências
        dep_matches = re.finditer(r'(\w+)\s*>>\s*(\w+)', content)
        for match in dep_matches:
            source_task = match.group(1)
            target_task = match.group(2)
            dag_workflow.task_dependencies.append((source_task, target_task))
        
        return dag_workflow
    
    def _get_surrounding_context(self, lines: List[str], line_num: int, context_size: int = 3) -> List[str]:
        """Obtém contexto ao redor de uma linha"""
        start = max(0, line_num - context_size - 1)
        end = min(len(lines), line_num + context_size)
        return lines[start:end]
    
    def _get_next_function(self, lines: List[str], decorator_line: int) -> Optional[str]:
        """Obtém próxima função após um decorator"""
        for i in range(decorator_line, min(len(lines), decorator_line + 5)):
            if i < len(lines):
                match = re.match(r'\s*def\s+(\w+)', lines[i])
                if match:
                    return match.group(1)
        return None
    
    def _extract_tables_from_embedded_sql(self, sql_content: str, file_path: str, line_num: int, context: str):
        """Extrai tabelas de SQL embarcado"""
        for pattern_info in self.sql_patterns:
            pattern = pattern_info['pattern']
            matches = re.finditer(pattern, sql_content)
            
            for match in matches:
                table_group = pattern_info['table_group']
                schema_group = pattern_info.get('schema_group')
                operation = pattern_info.get('operation', 'UNKNOWN')
                
                table_name = match.group(table_group) if match.group(table_group) else ""
                schema = match.group(schema_group) if schema_group and match.group(schema_group) else None
                
                if (table_name and len(table_name) > 1 and 
                    table_name.lower() not in ['if', 'not', 'exists', 'from', 'to', 'set', 'where', 'and', 'or']):
                    
                    param_chain = self._trace_parameter_chain(file_path, line_num, table_name)
                    
                    ref = TableReference(
                        table_name=table_name,
                        schema=schema.rstrip('.') if schema else None,
                        file_path=file_path,
                        line_number=line_num,
                        context_type='embedded_sql',
                        operation_type=operation,
                        confidence=pattern_info['confidence'] * 0.9,
                        raw_content=sql_content,
                        parameter_chain=param_chain,
                        context_details={
                            'embedding_context': context,
                            'extraction_method': 'from_embedded_sql'
                        }
                    )
                    self.table_references.append(ref)
    
    def _parameter_flow_analysis(self):
        """Análise de fluxo de parâmetros entre arquivos"""
        self.logger.info("🔗 Analisando fluxo de parâmetros...")
        
        # Constrói grafo de dependências
        for flow in self.parameter_flows:
            self.dependency_graph.add_edge(
                flow.source_file, 
                flow.target_file,
                parameter=flow.parameter_name,
                flow_type=flow.flow_type,
                confidence=flow.confidence
            )
        
        # Propaga referências de tabela através do grafo
        self._propagate_table_references()
    
    def _propagate_table_references(self):
        """Propaga referências de tabela através das dependências"""
        # Para cada arquivo que tem tabelas
        files_with_tables = defaultdict(list)
        for ref in self.table_references:
            files_with_tables[ref.file_path].append(ref)
        
        # Propaga através das dependências
        for source_file in files_with_tables:
            if source_file in self.dependency_graph:
                # Arquivos que dependem deste
                for target_file in self.dependency_graph.successors(source_file):
                    edge_data = self.dependency_graph.get_edge_data(source_file, target_file)
                    
                    # Cria referências indiretas
                    for table_ref in files_with_tables[source_file]:
                        indirect_ref = TableReference(
                            table_name=table_ref.table_name,
                            schema=table_ref.schema,
                            file_path=target_file,
                            line_number=0,  # Não específico
                            context_type='propagated_reference',
                            confidence=table_ref.confidence * 0.7,
                            parameter_chain=table_ref.parameter_chain + [f"propagated_from:{source_file}"],
                            context_details={
                                'original_file': source_file,
                                'propagation_type': edge_data.get('flow_type', 'unknown'),
                                'propagation_parameter': edge_data.get('parameter', 'unknown')
                            }
                        )
                        self.table_references.append(indirect_ref)
    
    def _dag_workflow_analysis(self):
        """Análise de workflows de DAG"""
        self.logger.info("🚁 Analisando workflows de DAG...")
        
        for dag_workflow in self.dag_workflows:
            # Para cada task no DAG, tenta mapear suas operações
            for task in dag_workflow.tasks:
                task_name = task['name']
                
                # Procura por referências de tabela relacionadas a esta task
                task_tables = []
                for ref in self.table_references:
                    # Se a referência está no mesmo arquivo e próxima ao task
                    if ref.file_path == dag_workflow.dag_file:
                        # Verifica se está relacionada ao task
                        if (task_name.lower() in ref.raw_content.lower() or
                            abs(ref.line_number - task.get('line', 0)) < 10):
                            task_tables.append(ref)
                
                # Adiciona tabelas ao contexto do task
                task['tables_referenced'] = [
                    {'table': ref.table_name, 'schema': ref.schema, 'operation': ref.operation_type}
                    for ref in task_tables
                ]
    
    def _build_enhanced_comprehensive_map(self, analysis_time: float) -> Dict[str, Any]:
        """Constrói mapa abrangente com análise avançada"""
        
        # Agrupa referências por tabela
        tables_map = defaultdict(list)
        for ref in self.table_references:
            full_table_name = f"{ref.schema}.{ref.table_name}" if ref.schema else ref.table_name
            tables_map[full_table_name].append(ref)
        
        # Calcula estatísticas
        total_tables = len(tables_map)
        total_references = len(self.table_references)
        files_with_tables = len(set(ref.file_path for ref in self.table_references))
        
        # Estatísticas por tipo de contexto
        context_breakdown = defaultdict(int)
        operation_breakdown = defaultdict(int)
        parameter_chain_stats = defaultdict(int)
        
        for ref in self.table_references:
            context_breakdown[ref.context_type] += 1
            operation_breakdown[ref.operation_type] += 1
            
            # Estatísticas de cadeia de parâmetros
            for chain_item in ref.parameter_chain:
                parameter_chain_stats[chain_item] += 1
        
        # Análise de DAGs
        dag_analysis = {
            'total_dags': len(self.dag_workflows),
            'total_tasks': sum(len(dag.tasks) for dag in self.dag_workflows),
            'total_dependencies': sum(len(dag.task_dependencies) for dag in self.dag_workflows),
            'dags': [
                {
                    'dag_id': dag.dag_id,
                    'file': dag.dag_file,
                    'tasks_count': len(dag.tasks),
                    'dependencies_count': len(dag.task_dependencies),
                    'tasks': dag.tasks,
                    'dependencies': dag.task_dependencies
                }
                for dag in self.dag_workflows
            ]
        }
        
        # Análise de fluxo de parâmetros
        parameter_flow_analysis = {
            'total_flows': len(self.parameter_flows),
            'flow_types': dict(defaultdict(int)),
            'cross_file_dependencies': len(self.dependency_graph.edges()),
            'files_in_dependency_graph': len(self.dependency_graph.nodes()),
            'flows': [
                {
                    'source_file': flow.source_file,
                    'target_file': flow.target_file,
                    'parameter': flow.parameter_name,
                    'flow_type': flow.flow_type,
                    'confidence': flow.confidence
                }
                for flow in self.parameter_flows
            ]
        }
        
        # Conta tipos de fluxo
        for flow in self.parameter_flows:
            parameter_flow_analysis['flow_types'][flow.flow_type] += 1
        
        # Identifica esquemas
        schemas = set()
        for ref in self.table_references:
            if ref.schema:
                schemas.add(ref.schema)
        
        # Tabelas mais referenciadas
        most_referenced = sorted(
            tables_map.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        return {
            'analysis_summary': {
                'analysis_time_seconds': round(analysis_time, 2),
                'files_analyzed': len(self.analyzed_files),
                'files_with_table_references': files_with_tables,
                'total_table_references': total_references,
                'unique_tables_found': total_tables,
                'schemas_found': list(schemas),
                'airflow_dags_found': len(self.dag_workflows),
                'parameter_flows_detected': len(self.parameter_flows)
            },
            'tables_discovered': {
                table_name: {
                    'reference_count': len(refs),
                    'files': list(set(ref.file_path for ref in refs)),
                    'contexts': list(set(ref.context_type for ref in refs)),
                    'operations': list(set(ref.operation_type for ref in refs)),
                    'schemas': list(set(ref.schema for ref in refs if ref.schema)),
                    'average_confidence': sum(ref.confidence for ref in refs) / len(refs),
                    'parameter_chains': [ref.parameter_chain for ref in refs if ref.parameter_chain],
                    'references': [
                        {
                            'file': ref.file_path,
                            'line': ref.line_number,
                            'context': ref.context_type,
                            'operation': ref.operation_type,
                            'confidence': ref.confidence,
                            'parameter_chain': ref.parameter_chain,
                            'raw_content': ref.raw_content[:100] + '...' if len(ref.raw_content) > 100 else ref.raw_content
                        }
                        for ref in refs
                    ]
                }
                for table_name, refs in tables_map.items()
            },
            'airflow_analysis': dag_analysis,
            'parameter_flow_analysis': parameter_flow_analysis,
            'statistics': {
                'context_breakdown': dict(context_breakdown),
                'operation_breakdown': dict(operation_breakdown),
                'parameter_chain_stats': dict(parameter_chain_stats),
                'most_referenced_tables': [
                    {
                        'table': table_name,
                        'references': len(refs),
                        'files': len(set(ref.file_path for ref in refs)),
                        'contexts': list(set(ref.context_type for ref in refs))
                    }
                    for table_name, refs in most_referenced
                ],
                'confidence_distribution': self._calculate_confidence_distribution()
            },
            'detailed_references': [
                {
                    'table_name': ref.table_name,
                    'schema': ref.schema,
                    'file_path': ref.file_path,
                    'line_number': ref.line_number,
                    'context_type': ref.context_type,
                    'operation_type': ref.operation_type,
                    'confidence': ref.confidence,
                    'parameter_chain': ref.parameter_chain,
                    'raw_content': ref.raw_content,
                    'context_details': ref.context_details
                }
                for ref in self.table_references
            ]
        }
    
    def _calculate_confidence_distribution(self) -> Dict[str, int]:
        """Calcula distribuição de confiança"""
        distribution = {
            'high (>= 0.9)': 0,
            'medium (0.7-0.9)': 0,
            'low (< 0.7)': 0
        }
        
        for ref in self.table_references:
            if ref.confidence >= 0.9:
                distribution['high (>= 0.9)'] += 1
            elif ref.confidence >= 0.7:
                distribution['medium (0.7-0.9)'] += 1
            else:
                distribution['low (< 0.7)'] += 1
        
        return distribution
    
    def generate_enhanced_reports(self, results: Dict[str, Any], output_dir: str = "."):
        """Gera relatórios melhorados com análise Airflow"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Relatório principal JSON
        main_report = output_path / "enhanced_postgresql_airflow_analysis.json"
        with open(main_report, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Relatório de DAGs específico
        if results['airflow_analysis']['total_dags'] > 0:
            dag_report = output_path / "airflow_dags_analysis.json"
            with open(dag_report, 'w', encoding='utf-8') as f:
                json.dump(results['airflow_analysis'], f, indent=2, ensure_ascii=False)
        
        # Relatório de fluxo de parâmetros
        param_flow_report = output_path / "parameter_flow_analysis.json"
        with open(param_flow_report, 'w', encoding='utf-8') as f:
            json.dump(results['parameter_flow_analysis'], f, indent=2, ensure_ascii=False)
        
        # Relatório resumo em texto
        self._generate_enhanced_text_summary(results, output_path / "enhanced_analysis_summary.txt")
        
        self.logger.info(f"📄 Relatórios melhorados salvos em: {output_path}")
    
    def _generate_enhanced_text_summary(self, results: Dict[str, Any], output_file: Path):
        """Gera resumo em texto com análise Airflow"""
        summary = results['analysis_summary']
        airflow = results['airflow_analysis']
        param_flow = results['parameter_flow_analysis']
        stats = results['statistics']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("🚁 ANÁLISE AVANÇADA POSTGRESQL + AIRFLOW\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"📊 RESUMO GERAL:\n")
            f.write(f"   Arquivos analisados: {summary['files_analyzed']}\n")
            f.write(f"   Tabelas únicas encontradas: {summary['unique_tables_found']}\n")
            f.write(f"   Total de referências: {summary['total_table_references']}\n")
            f.write(f"   Esquemas encontrados: {len(summary['schemas_found'])}\n")
            f.write(f"   DAGs Airflow encontradas: {summary['airflow_dags_found']}\n")
            f.write(f"   Fluxos de parâmetros: {summary['parameter_flows_detected']}\n")
            f.write(f"   Tempo de análise: {summary['analysis_time_seconds']}s\n\n")
            
            if airflow['total_dags'] > 0:
                f.write(f"🚁 ANÁLISE DE DAGs AIRFLOW:\n")
                f.write(f"   Total de DAGs: {airflow['total_dags']}\n")
                f.write(f"   Total de tasks: {airflow['total_tasks']}\n")
                f.write(f"   Dependências mapeadas: {airflow['total_dependencies']}\n\n")
                
                for dag in airflow['dags']:
                    f.write(f"   📋 DAG: {dag['dag_id']}\n")
                    f.write(f"      Arquivo: {dag['file']}\n")
                    f.write(f"      Tasks: {dag['tasks_count']}\n")
                    f.write(f"      Dependências: {dag['dependencies_count']}\n")
                    
                    # Lista tasks com tabelas
                    for task in dag['tasks']:
                        if 'tables_referenced' in task and task['tables_referenced']:
                            f.write(f"      Task '{task['name']}' → Tabelas: ")
                            table_names = [t['table'] for t in task['tables_referenced']]
                            f.write(f"{', '.join(table_names)}\n")
                    f.write("\n")
            
            if param_flow['total_flows'] > 0:
                f.write(f"🔗 ANÁLISE DE FLUXO DE PARÂMETROS:\n")
                f.write(f"   Total de fluxos: {param_flow['total_flows']}\n")
                f.write(f"   Dependências cross-file: {param_flow['cross_file_dependencies']}\n")
                f.write(f"   Arquivos no grafo: {param_flow['files_in_dependency_graph']}\n\n")
                
                f.write(f"   Tipos de fluxo:\n")
                for flow_type, count in param_flow['flow_types'].items():
                    f.write(f"      {flow_type}: {count}\n")
                f.write("\n")
            
            f.write(f"🏆 TABELAS MAIS REFERENCIADAS:\n")
            for item in stats['most_referenced_tables'][:10]:
                f.write(f"   • {item['table']}: {item['references']} refs em {item['files']} arquivos\n")
                f.write(f"     Contextos: {', '.join(item['contexts'])}\n")
            f.write("\n")
            
            f.write(f"📈 DISTRIBUIÇÃO POR CONTEXTO:\n")
            for context, count in stats['context_breakdown'].items():
                f.write(f"   • {context}: {count}\n")
            f.write("\n")
            
            if stats['parameter_chain_stats']:
                f.write(f"🔗 CADEIAS DE PARÂMETROS MAIS COMUNS:\n")
                sorted_chains = sorted(stats['parameter_chain_stats'].items(), key=lambda x: x[1], reverse=True)
                for chain, count in sorted_chains[:10]:
                    f.write(f"   • {chain}: {count} ocorrências\n")
                f.write("\n")

def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced PostgreSQL Airflow Mapper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("project_path", help="Caminho do projeto Python")
    parser.add_argument("--output", "-o", default="enhanced_airflow_analysis", 
                       help="Diretório de saída")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"❌ Caminho não encontrado: {args.project_path}")
        return
    
    print("🚁 Iniciando análise avançada PostgreSQL + Airflow...")
    
    mapper = EnhancedPostgreSQLAirflowMapper()
    results = mapper.analyze_project(args.project_path)
    
    # Gera relatórios
    mapper.generate_enhanced_reports(results, args.output)
    
    # Mostra resumo
    summary = results['analysis_summary']
    airflow = results['airflow_analysis']
    
    print(f"\n📊 Análise completa:")
    print(f"   📁 Arquivos analisados: {summary['files_analyzed']}")
    print(f"   🗃️ Tabelas encontradas: {summary['unique_tables_found']}")
    print(f"   📊 Total de referências: {summary['total_table_references']}")
    print(f"   🚁 DAGs Airflow: {summary['airflow_dags_found']}")
    print(f"   🔗 Fluxos de parâmetros: {summary['parameter_flows_detected']}")
    print(f"   ⏱️ Tempo de análise: {summary['analysis_time_seconds']}s")
    
    if airflow['total_dags'] > 0:
        print(f"\n🚁 Análise Airflow:")
        print(f"   📋 DAGs encontradas: {airflow['total_dags']}")
        print(f"   ⚙️ Tasks mapeadas: {airflow['total_tasks']}")
        
        for dag in airflow['dags']:
            print(f"   • {dag['dag_id']}: {dag['tasks_count']} tasks")
    
    print(f"\n📄 Relatórios salvos em: {args.output}/")

if __name__ == "__main__":
    main()
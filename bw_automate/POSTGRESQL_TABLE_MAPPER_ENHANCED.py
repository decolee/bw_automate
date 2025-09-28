#!/usr/bin/env python3
"""
🗃️ POSTGRESQL TABLE MAPPER - ENHANCED VERSION
Sistema ULTRA-COMPLETO para mapear tabelas PostgreSQL em códigos Python
Detecta TODOS os padrões possíveis: ORMs, migrações, configs, variáveis, etc.
"""

import ast
import re
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

@dataclass
class TableReference:
    """Referência a uma tabela encontrada"""
    table_name: str
    schema: Optional[str] = None
    file_path: str = ""
    line_number: int = 0
    column_number: int = 0
    context_type: str = ""  
    context_details: Dict[str, Any] = field(default_factory=dict)
    operation_type: str = ""  
    confidence: float = 1.0  
    raw_content: str = ""
    
    def __post_init__(self):
        # Normaliza nome da tabela
        self.table_name = self.table_name.strip('"\'`').lower()
        if self.schema:
            self.schema = self.schema.strip('"\'`').lower()

class PostgreSQLTableMapperEnhanced:
    """Mapeador ULTRA-COMPLETO de tabelas PostgreSQL"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.table_references: List[TableReference] = []
        self.analyzed_files: Set[str] = set()
        
        # Padrões para detecção
        self.sql_patterns = self._initialize_sql_patterns()
        self.orm_patterns = self._initialize_enhanced_orm_patterns()
        self.decorator_patterns = self._initialize_decorator_patterns()
        self.config_patterns = self._initialize_config_patterns()
        
    def _setup_logging(self):
        """Setup logging para debugging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def _initialize_sql_patterns(self) -> List[Dict]:
        """Padrões SQL expandidos"""
        return [
            # CREATE TABLE
            {
                'pattern': r'(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2, 'schema_group': 1, 'operation': 'CREATE', 'confidence': 0.99
            },
            # DROP TABLE
            {
                'pattern': r'(?i)DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2, 'schema_group': 1, 'operation': 'DROP', 'confidence': 0.99
            },
            # SELECT FROM
            {
                'pattern': r'(?i)SELECT\s+.*?\bFROM\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)',
                'table_group': 2, 'schema_group': 1, 'operation': 'SELECT', 'confidence': 0.98
            },
            {
                'pattern': r'(?i)SELECT\s+.*?\bFROM\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|$|,)',
                'table_group': 1, 'schema_group': None, 'operation': 'SELECT', 'confidence': 0.90
            },
            # INSERT INTO
            {
                'pattern': r'(?i)INSERT\s+INTO\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)',
                'table_group': 2, 'schema_group': 1, 'operation': 'INSERT', 'confidence': 0.98
            },
            {
                'pattern': r'(?i)INSERT\s+INTO\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|\()',
                'table_group': 1, 'schema_group': None, 'operation': 'INSERT', 'confidence': 0.95
            },
            # UPDATE
            {
                'pattern': r'(?i)UPDATE\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)\s+SET',
                'table_group': 2, 'schema_group': 1, 'operation': 'UPDATE', 'confidence': 0.98
            },
            {
                'pattern': r'(?i)UPDATE\s+(?:["\']?)(\w+)(?:["\']?)\s+SET',
                'table_group': 1, 'schema_group': None, 'operation': 'UPDATE', 'confidence': 0.95
            },
            # DELETE FROM
            {
                'pattern': r'(?i)DELETE\s+FROM\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)',
                'table_group': 2, 'schema_group': 1, 'operation': 'DELETE', 'confidence': 0.98
            },
            {
                'pattern': r'(?i)DELETE\s+FROM\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|$)',
                'table_group': 1, 'schema_group': None, 'operation': 'DELETE', 'confidence': 0.95
            },
            # JOIN patterns
            {
                'pattern': r'(?i)JOIN\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)\s+',
                'table_group': 2, 'schema_group': 1, 'operation': 'JOIN', 'confidence': 0.85
            },
            # COPY
            {
                'pattern': r'(?i)COPY\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)\s+(?:FROM|TO)',
                'table_group': 2, 'schema_group': 1, 'operation': 'COPY', 'confidence': 0.90
            },
            # TRUNCATE
            {
                'pattern': r'(?i)TRUNCATE\s+TABLE\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2, 'schema_group': 1, 'operation': 'TRUNCATE', 'confidence': 0.95
            },
            # ALTER TABLE
            {
                'pattern': r'(?i)ALTER\s+TABLE\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2, 'schema_group': 1, 'operation': 'ALTER', 'confidence': 0.95
            }
        ]
    
    def _initialize_enhanced_orm_patterns(self) -> List[Dict]:
        """Padrões ORM ULTRA-EXPANDIDOS"""
        return [
            # === SQLALCHEMY ===
            {'pattern': r'Table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'sqlalchemy_table', 'confidence': 0.95},
            {'pattern': r'__tablename__\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'sqlalchemy_model', 'confidence': 0.98},
            
            # === DJANGO ===
            {'pattern': r'db_table\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'django_model', 'confidence': 0.95},
            
            # === PEEWEE ===
            {'pattern': r'table_name\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'peewee_model', 'confidence': 0.90},
            
            # === TORTOISE ORM ===
            {'pattern': r'table\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'tortoise_model', 'confidence': 0.90},
            
            # === PONY ORM ===
            {'pattern': r'_table_\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'pony_model', 'confidence': 0.90},
            
            # === SQLMODEL (FastAPI) ===
            {'pattern': r'__tablename__\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'sqlmodel', 'confidence': 0.95},
            
            # === PANDAS OPERATIONS ===
            {'pattern': r'read_sql\s*\(\s*["\']([^"\']*SELECT[^"\']*FROM\s+(\w+)[^"\']*)["\']', 'table_group': 2, 'context': 'pandas_read_sql', 'confidence': 0.85},
            {'pattern': r'read_sql_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'pandas_read_table', 'confidence': 0.90},
            {'pattern': r'to_sql\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'pandas_to_sql', 'confidence': 0.90},
            {'pattern': r'read_sql_query\s*\(\s*["\']([^"\']*FROM\s+(\w+)[^"\']*)["\']', 'table_group': 2, 'context': 'pandas_query', 'confidence': 0.85},
            
            # === MIGRATION OPERATIONS ===
            {'pattern': r'create_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'migration_create', 'confidence': 0.95},
            {'pattern': r'drop_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'migration_drop', 'confidence': 0.95},
            {'pattern': r'rename_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'migration_rename', 'confidence': 0.95},
            {'pattern': r'op\.create_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'alembic_create', 'confidence': 0.95},
            {'pattern': r'op\.drop_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'alembic_drop', 'confidence': 0.95},
            {'pattern': r'op\.rename_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'alembic_rename', 'confidence': 0.95},
            
            # === DATABASE OPERATIONS ===
            {'pattern': r'copy_from\s*\([^,]*["\'](\w+)["\']', 'table_group': 1, 'context': 'copy_from', 'confidence': 0.90},
            {'pattern': r'copy_to\s*\([^,]*["\'](\w+)["\']', 'table_group': 1, 'context': 'copy_to', 'confidence': 0.90},
            {'pattern': r'copy_expert\s*\([^,]*["\']([^"\']*(\w+)[^"\']*)["\']', 'table_group': 2, 'context': 'copy_expert', 'confidence': 0.85},
            
            # === ASYNC OPERATIONS ===
            {'pattern': r'fetch\s*\(\s*["\']([^"\']*FROM\s+(\w+)[^"\']*)["\']', 'table_group': 2, 'context': 'async_fetch', 'confidence': 0.85},
            {'pattern': r'execute\s*\(\s*["\']([^"\']*FROM\s+(\w+)[^"\']*)["\']', 'table_group': 2, 'context': 'async_execute', 'confidence': 0.85},
            {'pattern': r'executemany\s*\(\s*["\']([^"\']*INTO\s+(\w+)[^"\']*)["\']', 'table_group': 2, 'context': 'async_executemany', 'confidence': 0.85},
            
            # === SPECIFIC LIBRARIES ===
            {'pattern': r'db\.query\s*\(\s*["\']([^"\']*FROM\s+(\w+)[^"\']*)["\']', 'table_group': 2, 'context': 'records_query', 'confidence': 0.80},
            {'pattern': r'db\[["\'](\w+)["\']\]', 'table_group': 1, 'context': 'dataset_table', 'confidence': 0.85},
            
            # === RAW SQL EXECUTION ===
            {'pattern': r'cursor\.execute\s*\(\s*["\']([^"\']*)["\']', 'sql_group': 1, 'context': 'cursor_execute', 'confidence': 0.85},
            {'pattern': r'execute\s*\(\s*["\']([^"\']*)["\']', 'sql_group': 1, 'context': 'raw_execute', 'confidence': 0.80}
        ]
    
    def _initialize_decorator_patterns(self) -> List[Dict]:
        """Padrões de decorators"""
        return [
            {'pattern': r'@table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'confidence': 0.95},
            {'pattern': r'@db_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'confidence': 0.90}
        ]
    
    def _initialize_config_patterns(self) -> List[Dict]:
        """Padrões de configuração"""
        return [
            # Dicionários de configuração
            {'pattern': r'["\'](\w+)["\']:\s*["\'](\w+_\w+)["\']', 'table_group': 2, 'confidence': 0.60},
            # Constantes
            {'pattern': r'([A-Z_]+_TABLE)\s*=\s*["\'](\w+)["\']', 'table_group': 2, 'confidence': 0.70},
            # Listas de tabelas
            {'pattern': r'\[\s*["\'](\w+_\w+)["\']', 'table_group': 1, 'confidence': 0.50},
            # Variables with table in name
            {'pattern': r'(\w*table\w*)\s*=\s*["\'](\w+)["\']', 'table_group': 2, 'confidence': 0.65}
        ]
    
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analisa projeto completo"""
        start_time = time.time()
        project_path = Path(project_path)
        
        if project_path.is_file():
            python_files = [project_path]
        else:
            python_files = list(project_path.rglob("*.py"))
        
        self.logger.info(f"🗃️ Iniciando mapeamento ULTRA-COMPLETO de tabelas PostgreSQL em {project_path}")
        self.logger.info(f"📁 Encontrados {len(python_files)} arquivos Python")
        
        # Analisa cada arquivo
        for file_path in python_files:
            try:
                self._analyze_file(str(file_path))
            except Exception as e:
                self.logger.warning(f"Erro ao analisar {file_path}: {e}")
                continue
        
        analysis_time = time.time() - start_time
        return self._generate_enhanced_report(analysis_time)
    
    def _analyze_file(self, file_path: str):
        """Análise ULTRA-COMPLETA de arquivo"""
        if file_path in self.analyzed_files:
            return
            
        self.analyzed_files.add(file_path)
        
        # Tenta diferentes encodings
        content = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if content is None:
            self.logger.warning(f"Não foi possível ler o arquivo {file_path}")
            return
        
        try:
            # Parse AST
            tree = ast.parse(content)
            
            # TODAS as análises possíveis
            self._analyze_ast_nodes(tree, file_path)
            self._analyze_sql_strings(content, file_path)
            self._analyze_orm_patterns(content, file_path)
            self._analyze_decorators(content, file_path)
            self._analyze_configuration_patterns(content, file_path)
            self._analyze_variable_assignments(tree, file_path)
            self._analyze_function_calls(tree, file_path)
            self._analyze_string_literals(tree, file_path)
            
        except SyntaxError as e:
            # Arquivo com erro de sintaxe - análise por regex
            self.logger.warning(f"Erro de sintaxe em {file_path}, usando análise de texto: {e}")
            self._analyze_sql_strings(content, file_path)
            self._analyze_orm_patterns(content, file_path)
            self._analyze_decorators(content, file_path)
            self._analyze_configuration_patterns(content, file_path)
    
    def _analyze_ast_nodes(self, tree: ast.AST, file_path: str):
        """Análise de nós AST"""
        class TableVisitor(ast.NodeVisitor):
            def __init__(self, mapper, file_path):
                self.mapper = mapper
                self.file_path = file_path
                self.current_class = None
            
            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class
            
            def visit_Assign(self, node):
                # Detecta assignments como __tablename__ = 'users'
                for target in node.targets:
                    if (isinstance(target, ast.Name) and 
                        target.id in ['__tablename__', 'table_name', '_table_', 'db_table'] and
                        isinstance(node.value, ast.Constant) and 
                        isinstance(node.value.value, str)):
                        
                        ref = TableReference(
                            table_name=node.value.value,
                            file_path=self.file_path,
                            line_number=node.lineno,
                            context_type='orm_class',
                            confidence=0.95,
                            context_details={'class_context': self.current_class, 'attribute': target.id}
                        )
                        self.mapper.table_references.append(ref)
                
                self.generic_visit(node)
        
        visitor = TableVisitor(self, file_path)
        visitor.visit(tree)
    
    def _analyze_sql_strings(self, content: str, file_path: str):
        """Análise de strings SQL"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.sql_patterns:
                matches = re.finditer(pattern_info['pattern'], line)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    schema = match.group(pattern_info['schema_group']) if pattern_info.get('schema_group') else None
                    
                    if table_name and len(table_name) > 1:
                        ref = TableReference(
                            table_name=table_name,
                            schema=schema,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='sql_string',
                            operation_type=pattern_info['operation'],
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip()
                        )
                        self.table_references.append(ref)
    
    def _analyze_orm_patterns(self, content: str, file_path: str):
        """Análise de padrões ORM"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.orm_patterns:
                matches = re.finditer(pattern_info['pattern'], line)
                
                for match in matches:
                    if 'table_group' in pattern_info:
                        table_name = match.group(pattern_info['table_group'])
                        
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='orm_pattern',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip(),
                            context_details={'orm_context': pattern_info['context']}
                        )
                        self.table_references.append(ref)
                    
                    elif 'sql_group' in pattern_info:
                        sql_content = match.group(pattern_info['sql_group'])
                        self._extract_tables_from_sql(sql_content, file_path, line_num, pattern_info['context'])
    
    def _analyze_decorators(self, content: str, file_path: str):
        """Análise de decorators"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.decorator_patterns:
                matches = re.finditer(pattern_info['pattern'], line)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    ref = TableReference(
                        table_name=table_name,
                        file_path=file_path,
                        line_number=line_num,
                        context_type='decorator',
                        confidence=pattern_info['confidence'],
                        raw_content=line.strip()
                    )
                    self.table_references.append(ref)
    
    def _analyze_configuration_patterns(self, content: str, file_path: str):
        """Análise de padrões de configuração"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('#'):
                continue
                
            for pattern_info in self.config_patterns:
                matches = re.finditer(pattern_info['pattern'], line, re.IGNORECASE)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    if (table_name and len(table_name) > 3 and 
                        '_' in table_name and not table_name.isupper()):
                        
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='configuration',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip()
                        )
                        self.table_references.append(ref)
    
    def _analyze_variable_assignments(self, tree: ast.AST, file_path: str):
        """Análise de assignments de variáveis"""
        class VariableVisitor(ast.NodeVisitor):
            def __init__(self, mapper, file_path):
                self.mapper = mapper
                self.file_path = file_path
                
            def visit_Assign(self, node):
                if (len(node.targets) == 1 and 
                    isinstance(node.targets[0], ast.Name) and
                    isinstance(node.value, ast.Constant) and
                    isinstance(node.value.value, str)):
                    
                    var_name = node.targets[0].id
                    value = node.value.value
                    
                    if ('table' in var_name.lower() and '_' in value and len(value) > 3):
                        ref = TableReference(
                            table_name=value,
                            file_path=self.file_path,
                            line_number=node.lineno,
                            context_type='variable_assignment',
                            confidence=0.75,
                            context_details={'variable_name': var_name}
                        )
                        self.mapper.table_references.append(ref)
                
                self.generic_visit(node)
            
            def visit_Dict(self, node):
                for key, value in zip(node.keys, node.values):
                    if (isinstance(value, ast.Constant) and 
                        isinstance(value.value, str) and
                        '_' in value.value and len(value.value) > 3):
                        
                        ref = TableReference(
                            table_name=value.value,
                            file_path=self.file_path,
                            line_number=node.lineno,
                            context_type='dictionary_mapping',
                            confidence=0.60
                        )
                        self.mapper.table_references.append(ref)
                
                self.generic_visit(node)
        
        visitor = VariableVisitor(self, file_path)
        visitor.visit(tree)
    
    def _analyze_function_calls(self, tree: ast.AST, file_path: str):
        """Análise de chamadas de função"""
        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self, mapper, file_path):
                self.mapper = mapper
                self.file_path = file_path
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    table_functions = [
                        'Table', 'create_table', 'drop_table', 'read_sql_table',
                        'to_sql', 'copy_from', 'copy_to'
                    ]
                    
                    if func_name in table_functions and node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                            ref = TableReference(
                                table_name=first_arg.value,
                                file_path=self.file_path,
                                line_number=node.lineno,
                                context_type='function_call',
                                confidence=0.85,
                                context_details={'function_name': func_name}
                            )
                            self.mapper.table_references.append(ref)
                
                self.generic_visit(node)
        
        visitor = FunctionVisitor(self, file_path)
        visitor.visit(tree)
    
    def _analyze_string_literals(self, tree: ast.AST, file_path: str):
        """Análise de literais de string"""
        class StringVisitor(ast.NodeVisitor):
            def __init__(self, mapper, file_path):
                self.mapper = mapper
                self.file_path = file_path
                
            def visit_Constant(self, node):
                if isinstance(node.value, str) and '_' in node.value:
                    # Procura por padrões de tabela em strings
                    if (len(node.value) > 3 and 
                        node.value.count('_') >= 1 and
                        node.value.islower() and
                        not ' ' in node.value):
                        
                        # Score baseado em características
                        score = 0.20
                        if 'table' in node.value: score += 0.20
                        if node.value.endswith('s'): score += 0.10  # Plural
                        if any(word in node.value for word in ['user', 'product', 'order', 'data']): score += 0.15
                        
                        if score > 0.30:
                            ref = TableReference(
                                table_name=node.value,
                                file_path=self.file_path,
                                line_number=node.lineno,
                                context_type='string_literal',
                                confidence=score
                            )
                            self.mapper.table_references.append(ref)
                
                self.generic_visit(node)
        
        visitor = StringVisitor(self, file_path)
        visitor.visit(tree)
    
    def _extract_tables_from_sql(self, sql_content: str, file_path: str, line_num: int, context: str = 'embedded_sql'):
        """Extrai tabelas de conteúdo SQL"""
        for pattern_info in self.sql_patterns:
            matches = re.finditer(pattern_info['pattern'], sql_content)
            
            for match in matches:
                table_name = match.group(pattern_info['table_group'])
                schema = match.group(pattern_info['schema_group']) if pattern_info.get('schema_group') else None
                
                if table_name and len(table_name) > 1:
                    ref = TableReference(
                        table_name=table_name,
                        schema=schema,
                        file_path=file_path,
                        line_number=line_num,
                        context_type=context,
                        operation_type=pattern_info['operation'],
                        confidence=pattern_info['confidence'] * 0.9,
                        raw_content=sql_content[:100]
                    )
                    self.table_references.append(ref)
    
    def _generate_enhanced_report(self, analysis_time: float) -> Dict[str, Any]:
        """Gera relatório ULTRA-COMPLETO"""
        # Estatísticas básicas
        total_references = len(self.table_references)
        unique_tables = len(set(ref.table_name for ref in self.table_references))
        files_with_tables = len(set(ref.file_path for ref in self.table_references))
        
        # Agrupamentos
        tables_map = defaultdict(list)
        context_breakdown = defaultdict(int)
        operation_breakdown = defaultdict(int)
        confidence_breakdown = defaultdict(int)
        
        for ref in self.table_references:
            tables_map[ref.table_name].append(ref)
            context_breakdown[ref.context_type] += 1
            operation_breakdown[ref.operation_type] += 1
            
            # Breakdown de confiança
            conf_range = 'high' if ref.confidence >= 0.8 else 'medium' if ref.confidence >= 0.5 else 'low'
            confidence_breakdown[conf_range] += 1
        
        # Top tabelas
        most_referenced = sorted(
            [(table, len(refs)) for table, refs in tables_map.items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        
        # Esquemas
        schemas = set(ref.schema for ref in self.table_references if ref.schema)
        
        return {
            'analysis_summary': {
                'analysis_time_seconds': round(analysis_time, 2),
                'files_analyzed': len(self.analyzed_files),
                'files_with_table_references': files_with_tables,
                'total_table_references': total_references,
                'unique_tables_found': unique_tables,
                'schemas_found': list(schemas),
                'detection_patterns': len(self.sql_patterns) + len(self.orm_patterns) + len(self.decorator_patterns) + len(self.config_patterns)
            },
            'statistics': {
                'context_breakdown': dict(context_breakdown),
                'operation_breakdown': dict(operation_breakdown),
                'confidence_breakdown': dict(confidence_breakdown),
                'most_referenced_tables': [{'table': table, 'references': count} for table, count in most_referenced]
            },
            'tables_discovered': {
                table_name: {
                    'reference_count': len(refs),
                    'files': list(set(ref.file_path for ref in refs)),
                    'contexts': list(set(ref.context_type for ref in refs)),
                    'operations': list(set(ref.operation_type for ref in refs if ref.operation_type)),
                    'average_confidence': sum(ref.confidence for ref in refs) / len(refs),
                    'references': [
                        {
                            'file': ref.file_path,
                            'line': ref.line_number,
                            'context': ref.context_type,
                            'operation': ref.operation_type,
                            'confidence': ref.confidence,
                            'raw_content': ref.raw_content[:100] + '...' if len(ref.raw_content) > 100 else ref.raw_content
                        }
                        for ref in refs
                    ]
                }
                for table_name, refs in tables_map.items()
            }
        }

def main():
    """Função principal para execução via CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mapeador ULTRA-COMPLETO de tabelas PostgreSQL')
    parser.add_argument('path', help='Caminho para analisar')
    parser.add_argument('--output', '-o', default='postgresql_enhanced_map.json', help='Arquivo de saída')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verboso')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Analisa o projeto
    mapper = PostgreSQLTableMapperEnhanced()
    results = mapper.analyze_project(args.path)
    
    # Salva resultados
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Mostra resumo
    summary = results['analysis_summary']
    print(f"\n📊 Análise ULTRA-COMPLETA:")
    print(f"   📁 Arquivos analisados: {summary['files_analyzed']}")
    print(f"   🗃️ Tabelas encontradas: {summary['unique_tables_found']}")
    print(f"   📊 Total de referências: {summary['total_table_references']}")
    print(f"   🔍 Padrões de detecção: {summary['detection_patterns']}")
    print(f"   ⏱️ Tempo de análise: {summary['analysis_time_seconds']}s")
    
    if results['tables_discovered']:
        print(f"\n🏆 Top 5 tabelas mais referenciadas:")
        for item in results['statistics']['most_referenced_tables'][:5]:
            print(f"   • {item['table']}: {item['references']} referências")
    
    print(f"\n📄 Relatório ULTRA-COMPLETO salvo em: {args.output}")

if __name__ == "__main__":
    main()
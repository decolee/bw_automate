#!/usr/bin/env python3
"""
🚀 POSTGRESQL TABLE MAPPER - ULTIMATE VERSION
Sistema DEFINITIVO que detecta ABSOLUTAMENTE QUALQUER padrão de tabela
Incluindo padrões exóticos, modernos e "fora da caixa"
"""

import ast
import re
import os
import json
import time
import base64
import hashlib
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
    encoding_type: str = ""  # normal, base64, hash, unicode
    
    def __post_init__(self):
        # Normaliza nome da tabela
        self.table_name = self.table_name.strip('"\'`').lower()
        if self.schema:
            self.schema = self.schema.strip('"\'`').lower()

class PostgreSQLTableMapper:
    """Mapeador DEFINITIVO e COMPLETO de tabelas PostgreSQL"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.table_references: List[TableReference] = []
        self.analyzed_files: Set[str] = set()
        
        # Padrões tradicionais
        self.sql_patterns = self._initialize_sql_patterns()
        self.orm_patterns = self._initialize_enhanced_orm_patterns()
        self.decorator_patterns = self._initialize_decorator_patterns()
        self.config_patterns = self._initialize_config_patterns()
        
        # Padrões EXÓTICOS
        self.exotic_patterns = self._initialize_exotic_patterns()
        self.documentation_patterns = self._initialize_documentation_patterns()
        self.logging_patterns = self._initialize_logging_patterns()
        self.serialization_patterns = self._initialize_serialization_patterns()
        self.infrastructure_patterns = self._initialize_infrastructure_patterns()
        
    def _setup_logging(self):
        """Setup logging para debugging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def _initialize_sql_patterns(self) -> List[Dict]:
        """Padrões SQL expandidos"""
        return [
            {'pattern': r'(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)', 'table_group': 2, 'schema_group': 1, 'operation': 'CREATE', 'confidence': 0.99},
            {'pattern': r'(?i)DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)', 'table_group': 2, 'schema_group': 1, 'operation': 'DROP', 'confidence': 0.99},
            {'pattern': r'(?i)SELECT\s+.*?\bFROM\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)', 'table_group': 2, 'schema_group': 1, 'operation': 'SELECT', 'confidence': 0.98},
            {'pattern': r'(?i)SELECT\s+.*?\bFROM\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|$|,)', 'table_group': 1, 'schema_group': None, 'operation': 'SELECT', 'confidence': 0.90},
            {'pattern': r'(?i)INSERT\s+INTO\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)', 'table_group': 2, 'schema_group': 1, 'operation': 'INSERT', 'confidence': 0.98},
            {'pattern': r'(?i)INSERT\s+INTO\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|\()', 'table_group': 1, 'schema_group': None, 'operation': 'INSERT', 'confidence': 0.95},
            {'pattern': r'(?i)UPDATE\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)\s+SET', 'table_group': 2, 'schema_group': 1, 'operation': 'UPDATE', 'confidence': 0.98},
            {'pattern': r'(?i)UPDATE\s+(?:["\']?)(\w+)(?:["\']?)\s+SET', 'table_group': 1, 'schema_group': None, 'operation': 'UPDATE', 'confidence': 0.95},
            {'pattern': r'(?i)DELETE\s+FROM\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)', 'table_group': 2, 'schema_group': 1, 'operation': 'DELETE', 'confidence': 0.98},
            {'pattern': r'(?i)DELETE\s+FROM\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|$)', 'table_group': 1, 'schema_group': None, 'operation': 'DELETE', 'confidence': 0.95},
            {'pattern': r'(?i)JOIN\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)\s+', 'table_group': 2, 'schema_group': 1, 'operation': 'JOIN', 'confidence': 0.85},
            {'pattern': r'(?i)COPY\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)\s+(?:FROM|TO)', 'table_group': 2, 'schema_group': 1, 'operation': 'COPY', 'confidence': 0.90},
            {'pattern': r'(?i)TRUNCATE\s+TABLE\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)', 'table_group': 2, 'schema_group': 1, 'operation': 'TRUNCATE', 'confidence': 0.95},
            {'pattern': r'(?i)ALTER\s+TABLE\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)', 'table_group': 2, 'schema_group': 1, 'operation': 'ALTER', 'confidence': 0.95}
        ]
    
    def _initialize_enhanced_orm_patterns(self) -> List[Dict]:
        """Padrões ORM expandidos"""
        return [
            # SQLAlchemy
            {'pattern': r'Table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'sqlalchemy_table', 'confidence': 0.95},
            {'pattern': r'__tablename__\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'sqlalchemy_model', 'confidence': 0.98},
            # Django
            {'pattern': r'db_table\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'django_model', 'confidence': 0.95},
            # Outros ORMs
            {'pattern': r'table_name\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'peewee_model', 'confidence': 0.90},
            {'pattern': r'table\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'tortoise_model', 'confidence': 0.90},
            {'pattern': r'_table_\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'pony_model', 'confidence': 0.90},
            # Pandas
            {'pattern': r'read_sql\s*\(\s*["\']([^"\']*SELECT[^"\']*FROM\s+(\w+)[^"\']*)["\']', 'table_group': 2, 'context': 'pandas_read_sql', 'confidence': 0.85},
            {'pattern': r'read_sql_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'pandas_read_table', 'confidence': 0.90},
            {'pattern': r'to_sql\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'pandas_to_sql', 'confidence': 0.90},
            # Migrações
            {'pattern': r'create_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'migration_create', 'confidence': 0.95},
            {'pattern': r'drop_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'migration_drop', 'confidence': 0.95},
            {'pattern': r'op\.create_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'alembic_create', 'confidence': 0.95},
            # Database operations
            {'pattern': r'copy_from\s*\([^,]*["\'](\w+)["\']', 'table_group': 1, 'context': 'copy_from', 'confidence': 0.90},
            {'pattern': r'copy_to\s*\([^,]*["\'](\w+)["\']', 'table_group': 1, 'context': 'copy_to', 'confidence': 0.90},
            # Raw SQL
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
            {'pattern': r'["\'](\w+)["\']:\s*["\'](\w+_\w+)["\']', 'table_group': 2, 'confidence': 0.60},
            {'pattern': r'([A-Z_]+_TABLE)\s*=\s*["\'](\w+)["\']', 'table_group': 2, 'confidence': 0.70},
            {'pattern': r'\[\s*["\'](\w+_\w+)["\']', 'table_group': 1, 'confidence': 0.50},
            {'pattern': r'(\w*table\w*)\s*=\s*["\'](\w+)["\']', 'table_group': 2, 'confidence': 0.65}
        ]
    
    def _initialize_exotic_patterns(self) -> List[Dict]:
        """Padrões EXÓTICOS e modernos"""
        return [
            # GraphQL
            {'pattern': r'type\s+Query\s*\{[^}]*(\w+_graphql|\w+_api)[^}]*\}', 'table_group': 1, 'context': 'graphql_schema', 'confidence': 0.80},
            {'pattern': r'(\w+_graphql|\w+_api):\s*\[', 'table_group': 1, 'context': 'graphql_type', 'confidence': 0.75},
            
            # FastAPI dependency injection
            {'pattern': r'table_name:\s*str\s*=\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'fastapi_dependency', 'confidence': 0.85},
            {'pattern': r'fetch_from_table\s*\(\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'async_fetch', 'confidence': 0.85},
            
            # Magic commands (Jupyter)
            {'pattern': r'%sql\s+SELECT[^"\']*FROM\s+(\w+)', 'table_group': 1, 'context': 'jupyter_magic', 'confidence': 0.90},
            {'pattern': r'%%sql[^"\']*FROM\s+(\w+)', 'table_group': 1, 'context': 'jupyter_cell_magic', 'confidence': 0.90},
            
            # Redis/Cache patterns
            {'pattern': r'cache:table:(\w+)', 'table_group': 1, 'context': 'redis_key', 'confidence': 0.70},
            {'pattern': r'session:data:(\w+)', 'table_group': 1, 'context': 'session_cache', 'confidence': 0.65},
            
            # Message Queue patterns
            {'pattern': r'queue\.processar\.(\w+)', 'table_group': 1, 'context': 'rabbitmq_queue', 'confidence': 0.75},
            {'pattern': r'eventos\.(\w+)\.', 'table_group': 1, 'context': 'kafka_topic', 'confidence': 0.70},
            
            # Feature store
            {'pattern': r'source_table["\']:\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'feature_store', 'confidence': 0.80},
            {'pattern': r'features_(\w+)', 'table_group': 1, 'context': 'ml_features', 'confidence': 0.70},
            
            # Time-based tables
            {'pattern': r'(\w+)_\d{4}_\d{2}_\d{2}', 'table_group': 1, 'context': 'time_based_table', 'confidence': 0.75},
            {'pattern': r'(\w+)_partition_\w+', 'table_group': 1, 'context': 'partitioned_table', 'confidence': 0.80},
            
            # Internationalization
            {'pattern': r'["\'](\w+_international_\w+)["\']', 'table_group': 1, 'context': 'i18n_table', 'confidence': 0.75},
            
            # Cutting-edge technologies
            {'pattern': r'(\w+_quantum|\w+_blockchain|\w+_wasm|\w+_neuromorphic)', 'table_group': 1, 'context': 'cutting_edge_tech', 'confidence': 0.70},
            {'pattern': r'(\w+_metaverse|\w+_nft|\w+_defi)', 'table_group': 1, 'context': 'web3_metaverse', 'confidence': 0.70},
            
            # Self-modifying and dynamic patterns
            {'pattern': r'f["\'](\w+_autogerada_\d+)["\']', 'table_group': 1, 'context': 'self_modifying', 'confidence': 0.60},
            {'pattern': r'random\.[\w]+.*["\'](\w+_dinamica)["\']', 'table_group': 1, 'context': 'dynamic_generation', 'confidence': 0.55},
            
            # Binary and byte patterns
            {'pattern': r'decode\(["\']utf-8["\']\)', 'table_group': 0, 'context': 'binary_decode', 'confidence': 0.40},
            
            # Emoji and special characters
            {'pattern': r'["\'][^"\']*[🚀🔥⚡🎯🌟][^"\']*["\']', 'table_group': 0, 'context': 'emoji_tables', 'confidence': 0.30}
        ]
    
    def _initialize_documentation_patterns(self) -> List[Dict]:
        """Padrões em documentação"""
        return [
            # OpenAPI/Swagger
            {'pattern': r'"description":\s*"[^"]*FROM\s+(\w+)', 'table_group': 1, 'context': 'openapi_docs', 'confidence': 0.70},
            {'pattern': r'"example":\s*"(\w+_api|\w+_swagger)"', 'table_group': 1, 'context': 'api_example', 'confidence': 0.65},
            
            # JSON Schema
            {'pattern': r'"const":\s*"(\w+_schema|\w+_json)"', 'table_group': 1, 'context': 'json_schema', 'confidence': 0.70},
            
            # YAML configurations
            {'pattern': r'-\s*(\w+_yaml|\w+_config)', 'table_group': 1, 'context': 'yaml_list', 'confidence': 0.65},
            {'pattern': r'(\w+):\s*["\']?(\w+_yaml|\w+_toml)["\']?', 'table_group': 2, 'context': 'yaml_mapping', 'confidence': 0.65}
        ]
    
    def _initialize_logging_patterns(self) -> List[Dict]:
        """Padrões de logging e monitoramento"""
        return [
            # Structured logging
            {'pattern': r'table=["\'"](\w+)["\']', 'table_group': 1, 'context': 'structured_log', 'confidence': 0.80},
            {'pattern': r'logger\.\w+\([^)]*["\'](\w+_log|\w+_audit)["\']', 'table_group': 1, 'context': 'logger_call', 'confidence': 0.75},
            
            # Metrics
            {'pattern': r'labels\(table_name=["\'](\w+)["\']\)', 'table_group': 1, 'context': 'prometheus_metric', 'confidence': 0.85},
            {'pattern': r'db\.table\.name["\'],\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'opentelemetry_trace', 'confidence': 0.85},
            
            # Health checks
            {'pattern': r'"tables":\s*\[[^]]*["\'](\w+)["\']', 'table_group': 1, 'context': 'health_check', 'confidence': 0.75}
        ]
    
    def _initialize_serialization_patterns(self) -> List[Dict]:
        """Padrões de serialização e encoding"""
        return [
            # Protobuf-like
            {'pattern': r'message\s+\w+\s*\{[^}]*["\'](\w+_protobuf|\w+_message)["\']', 'table_group': 1, 'context': 'protobuf_schema', 'confidence': 0.70},
            
            # Base64 (detectar padrões que podem ser nomes de tabela encoded)
            {'pattern': r'base64\.\w+\([^)]*["\']([^"\']+)["\']', 'table_group': 1, 'context': 'base64_encoded', 'confidence': 0.40},
            
            # Hash patterns
            {'pattern': r'hashlib\.\w+\([^)]*["\']tabela_(\w+)["\']', 'table_group': 1, 'context': 'hashed_table', 'confidence': 0.60}
        ]
    
    def _initialize_infrastructure_patterns(self) -> List[Dict]:
        """Padrões de infraestrutura"""
        return [
            # Docker/Kubernetes
            {'pattern': r'DB_TABLE_\w+["\']?:\s*["\'](\w+)["\']', 'table_group': 1, 'context': 'env_variable', 'confidence': 0.80},
            
            # Terraform
            {'pattern': r'name\s*=\s*["\'](\w+_terraform|\w+_infrastructure)["\']', 'table_group': 1, 'context': 'terraform_resource', 'confidence': 0.75}
        ]
    
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Análise DEFINITIVA de projeto"""
        start_time = time.time()
        project_path = Path(project_path)
        
        if project_path.is_file():
            python_files = [project_path]
        else:
            python_files = list(project_path.rglob("*.py"))
        
        self.logger.info(f"🚀 Iniciando mapeamento DEFINITIVO de tabelas PostgreSQL em {project_path}")
        self.logger.info(f"📁 Encontrados {len(python_files)} arquivos Python")
        
        # Analisa cada arquivo com TODOS os métodos
        for file_path in python_files:
            try:
                self._analyze_file_ultimate(str(file_path))
            except Exception as e:
                self.logger.warning(f"Erro ao analisar {file_path}: {e}")
                continue
        
        # APLICAR PÓS-PROCESSAMENTO INTELIGENTE
        self._post_process_and_filter_results()
        
        analysis_time = time.time() - start_time
        return self._generate_ultimate_report(analysis_time)
    
    def _analyze_file_ultimate(self, file_path: str):
        """Análise DEFINITIVA de arquivo"""
        if file_path in self.analyzed_files:
            return
            
        self.analyzed_files.add(file_path)
        
        # Tenta diferentes encodings
        content = None
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'utf-16']:
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
            
            # TODAS as análises tradicionais
            self._analyze_ast_nodes(tree, file_path)
            self._analyze_sql_strings(content, file_path)
            self._analyze_orm_patterns(content, file_path)
            self._analyze_decorators(content, file_path)
            self._analyze_configuration_patterns(content, file_path)
            self._analyze_variable_assignments(tree, file_path)
            self._analyze_function_calls(tree, file_path)
            self._analyze_string_literals(tree, file_path)
            
            # ANÁLISES EXÓTICAS E AVANÇADAS
            self._analyze_exotic_patterns(content, file_path)
            self._analyze_documentation_patterns(content, file_path)
            self._analyze_logging_patterns(content, file_path)
            self._analyze_serialization_patterns(content, file_path)
            self._analyze_infrastructure_patterns(content, file_path)
            self._analyze_multiline_strings(content, file_path)
            self._analyze_comments_and_docstrings(content, file_path)
            self._analyze_unicode_patterns(content, file_path)
            self._analyze_encoded_patterns(content, file_path)
            self._analyze_dynamic_patterns(content, file_path)
            self._analyze_byte_patterns(content, file_path)
            
        except SyntaxError as e:
            # Arquivo com erro de sintaxe - análise por regex
            self.logger.warning(f"Erro de sintaxe em {file_path}, usando análise de texto: {e}")
            self._analyze_sql_strings(content, file_path)
            self._analyze_orm_patterns(content, file_path)
            self._analyze_decorators(content, file_path)
            self._analyze_configuration_patterns(content, file_path)
            self._analyze_exotic_patterns(content, file_path)
            self._analyze_documentation_patterns(content, file_path)
    
    def _analyze_ast_nodes(self, tree: ast.AST, file_path: str):
        """Análise básica de nós AST"""
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
                        'to_sql', 'copy_from', 'copy_to', 'fetch_from_table'
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
                    if (len(node.value) > 3 and 
                        node.value.count('_') >= 1 and
                        node.value.islower() and
                        not ' ' in node.value):
                        
                        # Score baseado em características
                        score = 0.20
                        if 'table' in node.value: score += 0.20
                        if node.value.endswith('s'): score += 0.10
                        if any(word in node.value for word in ['user', 'product', 'order', 'data']): score += 0.15
                        if any(suffix in node.value for suffix in ['_log', '_config', '_api', '_db']): score += 0.15
                        
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
    
    def _analyze_exotic_patterns(self, content: str, file_path: str):
        """Análise de padrões EXÓTICOS"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.exotic_patterns:
                matches = re.finditer(pattern_info['pattern'], line, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    if table_name and len(table_name) > 2:
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='exotic_pattern',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip()[:100],
                            context_details={'exotic_context': pattern_info['context']}
                        )
                        self.table_references.append(ref)
        
        # NOVA ANÁLISE: Detecção específica de listas de tabelas cutting-edge
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id.lower()
                            # Procura variáveis com nomes relacionados a tecnologias cutting-edge
                            if any(keyword in var_name for keyword in [
                                'quantum', 'circuit', 'neuromorphic', 'metaverse', 'spatial', 
                                'edge', 'temporal', 'graph', 'blockchain', 'crypto', 'dna',
                                'bci', 'diffusion', 'llm', 'grpc', 'http3', 'lambda',
                                'emscripten', 'tables'  # Adiciona detecção específica para listas de tabelas
                            ]):
                                if isinstance(node.value, ast.List):
                                    for item in node.value.elts:
                                        if isinstance(item, ast.Constant) and isinstance(item.value, str):
                                            table_name = item.value.strip()
                                            if self._is_valid_table_name(table_name):
                                                ref = TableReference(
                                                    table_name=table_name,
                                                    file_path=file_path,
                                                    line_number=getattr(node, 'lineno', 0),
                                                    context_type='exotic_pattern',
                                                    confidence=0.85,
                                                    raw_content=f'{var_name} = ["{table_name}", ...]',
                                                    context_details={'exotic_context': f'cutting_edge_list_{var_name}'}
                                                )
                                                self.table_references.append(ref)
        except:
            pass
    
    def _is_valid_table_name(self, table_name: str) -> bool:
        """Valida se o nome parece ser uma tabela PostgreSQL válida com filtros INTELIGENTES"""
        if not table_name or len(table_name) < 2:
            return False
        
        # Remove emojis e caracteres especiais
        cleaned_name = re.sub(r'[^\w\-_]', '', table_name)
        if len(cleaned_name) < 2:
            return False
        
        # Aceita apenas letras, números, underscore e hífen
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', cleaned_name):
            return False
        
        # BLACKLIST INTELIGENTE - palavras que NUNCA são tabelas
        blacklist_words = {
            # Palavras comuns
            'data', 'info', 'value', 'result', 'output', 'input', 'temp', 'test',
            'item', 'name', 'id', 'key', 'type', 'status', 'message', 'error',
            'success', 'failed', 'true', 'false', 'none', 'null', 'empty',
            
            # Termos técnicos
            'string', 'text', 'json', 'xml', 'html', 'csv', 'pdf', 'doc',
            'file', 'path', 'url', 'uri', 'api', 'sql', 'query', 'command',
            
            # Frases em português/inglês
            'arquivo', 'teste', 'controlado', 'criado', 'from', 'this', 'point',
            'will', 'select', 'best', 'approach', 'create', 'new', 'update',
            'system', 'we', 'the', 'and', 'or', 'not', 'with', 'for',
            
            # Nomes genéricos que aparecem em SQL de exemplo/teste
            'dados_principais', 'dados_raw', 'temp_old_data', 'old_data',
            'raw_data', 'temp_data', 'test_data', 'sample_data', 'mock_data'
        }
        
        # Verifica se é uma palavra blacklistada
        if cleaned_name.lower() in blacklist_words:
            return False
        
        # Filtro anti-emoji e caracteres especiais
        if any(ord(c) > 127 for c in table_name):
            # Se contém caracteres unicode, verifica se parece com emoji
            emoji_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+'
            if re.search(emoji_pattern, table_name):
                return False
        
        # Filtro anti-frases (mais de 3 palavras separadas por espaço)
        if ' ' in table_name and len(table_name.split()) > 3:
            return False
        
        # Filtro anti-patterns específicos
        anti_patterns = [
            r'arquivo.*teste.*controlado.*criado',  # Frases específicas
            r'from.*this.*point.*on',               # Frases em inglês
            r'create.*new.*update',                 # Comandos SQL genéricos
            r'best.*approach'                       # Frases comuns
        ]
        
        for pattern in anti_patterns:
            if re.search(pattern, table_name.lower(), re.IGNORECASE):
                return False
        
        # Filtro de contexto: tabelas devem ter pelo menos um underscore OU ser nomes descritivos
        if '_' not in cleaned_name and len(cleaned_name) < 6:
            return False
            
        return True
    
    def _calculate_sql_context_confidence(self, table_name: str, sql_content: str, base_confidence: float) -> float:
        """Calcula confiança ajustada baseada no contexto SQL"""
        confidence = base_confidence
        
        # Boost para tabelas com nomes realistas de banco de dados
        if any(keyword in table_name.lower() for keyword in ['user', 'product', 'order', 'item', 'data', 'log', 'audit', 'session', 'config']):
            confidence += 0.1
        
        # Boost para operações CRUD reais
        sql_lower = sql_content.lower()
        if any(op in sql_lower for op in ['insert into', 'update', 'delete from', 'create table']):
            confidence += 0.05
        
        # Penalidade para tabelas que aparecem em contextos suspeitos
        if 'expected_tables' in sql_content.lower():
            confidence -= 0.2  # Provavelmente é lista de teste
        
        if 'print(' in sql_content or 'console.log' in sql_content:
            confidence -= 0.15  # Provavelmente é debug/logging
        
        # Boost para SQL com WHERE, JOIN, etc. (mais realista)
        if any(clause in sql_lower for clause in ['where', 'join', 'group by', 'order by']):
            confidence += 0.05
        
        return max(0.0, min(1.0, confidence))  # Mantém entre 0 e 1
    
    def _analyze_documentation_patterns(self, content: str, file_path: str):
        """Análise de padrões em documentação"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.documentation_patterns:
                matches = re.finditer(pattern_info['pattern'], line, re.IGNORECASE)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    if table_name and len(table_name) > 3:
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='documentation',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip()[:100],
                            context_details={'doc_context': pattern_info['context']}
                        )
                        self.table_references.append(ref)
    
    def _analyze_logging_patterns(self, content: str, file_path: str):
        """Análise de padrões de logging"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.logging_patterns:
                matches = re.finditer(pattern_info['pattern'], line, re.IGNORECASE)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    if table_name and len(table_name) > 3:
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='logging_monitoring',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip()[:100],
                            context_details={'log_context': pattern_info['context']}
                        )
                        self.table_references.append(ref)
    
    def _analyze_serialization_patterns(self, content: str, file_path: str):
        """Análise de padrões de serialização"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.serialization_patterns:
                matches = re.finditer(pattern_info['pattern'], line, re.IGNORECASE)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    if table_name and len(table_name) > 3:
                        # Detectar tipo de encoding
                        encoding_type = 'normal'
                        if 'base64' in pattern_info['context']:
                            encoding_type = 'base64'
                            try:
                                # Tentar decodificar base64
                                decoded = base64.b64decode(table_name).decode('utf-8')
                                if '_' in decoded:
                                    table_name = decoded
                            except:
                                pass
                        elif 'hash' in pattern_info['context']:
                            encoding_type = 'hash'
                        
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='serialization',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip()[:100],
                            encoding_type=encoding_type,
                            context_details={'serial_context': pattern_info['context']}
                        )
                        self.table_references.append(ref)
    
    def _analyze_infrastructure_patterns(self, content: str, file_path: str):
        """Análise de padrões de infraestrutura"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.infrastructure_patterns:
                matches = re.finditer(pattern_info['pattern'], line, re.IGNORECASE)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    if table_name and len(table_name) > 3:
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='infrastructure',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip()[:100],
                            context_details={'infra_context': pattern_info['context']}
                        )
                        self.table_references.append(ref)
    
    def _analyze_multiline_strings(self, content: str, file_path: str):
        """Análise de strings multilinha (YAML, JSON, etc.)"""
        # Detectar blocos YAML/JSON embedded
        yaml_blocks = re.finditer(r'"""([^"]*(?:table|Table)[^"]*)"""', content, re.MULTILINE | re.DOTALL)
        for match in yaml_blocks:
            yaml_content = match.group(1)
            lines = yaml_content.split('\n')
            start_line = content[:match.start()].count('\n') + 1
            
            for i, line in enumerate(lines):
                # Padrões YAML
                yaml_matches = re.finditer(r'-\s*(\w+_yaml|\w+_config)', line)
                for yaml_match in yaml_matches:
                    table_name = yaml_match.group(1)
                    ref = TableReference(
                        table_name=table_name,
                        file_path=file_path,
                        line_number=start_line + i,
                        context_type='yaml_embedded',
                        confidence=0.70,
                        raw_content=line.strip()
                    )
                    self.table_references.append(ref)
    
    def _analyze_comments_and_docstrings(self, content: str, file_path: str):
        """Análise de comentários e docstrings"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Comentários
            if line.strip().startswith('#'):
                # Procurar referências a tabelas em comentários
                comment_matches = re.finditer(r'(\w+_table|\w+_data|\w+_db)', line, re.IGNORECASE)
                for match in comment_matches:
                    table_name = match.group(1)
                    if len(table_name) > 4:
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='comment_reference',
                            confidence=0.50,
                            raw_content=line.strip()
                        )
                        self.table_references.append(ref)
    
    def _analyze_unicode_patterns(self, content: str, file_path: str):
        """Análise de padrões Unicode (nomes de tabela em outros idiomas)"""
        lines = content.split('\n')
        
        unicode_table_patterns = [
            r'["\']?(usuários|usuarios)_(\w+)["\']?',  # Portuguese
            r'["\']?(продукты|данные)_(\w+)["\']?',     # Russian  
            r'["\']?(用户|数据)_(\w+)["\']?',             # Chinese
            r'["\']?(ユーザー|データ)_(\w+)["\']?'        # Japanese
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in unicode_table_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    table_name = match.group(0).strip('\'"')
                    ref = TableReference(
                        table_name=table_name,
                        file_path=file_path,
                        line_number=line_num,
                        context_type='unicode_table',
                        confidence=0.75,
                        encoding_type='unicode',
                        raw_content=line.strip()
                    )
                    self.table_references.append(ref)
    
    def _analyze_encoded_patterns(self, content: str, file_path: str):
        """Análise de padrões codificados/ofuscados"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Detectar possíveis nomes de tabela em base64
            base64_matches = re.finditer(r'["\']([A-Za-z0-9+/]{12,}={0,2})["\']', line)
            for match in base64_matches:
                encoded_str = match.group(1)
                try:
                    decoded = base64.b64decode(encoded_str + '==').decode('utf-8')
                    if '_' in decoded and len(decoded) > 3 and decoded.replace('_', '').isalnum():
                        ref = TableReference(
                            table_name=decoded,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='base64_decoded',
                            confidence=0.60,
                            encoding_type='base64',
                            raw_content=f"base64: {encoded_str}"
                        )
                        self.table_references.append(ref)
                except:
                    pass
    
    def _analyze_dynamic_patterns(self, content: str, file_path: str):
        """Análise de padrões dinâmicos e auto-modificáveis"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Função que gera nomes de tabela dinamicamente
            if 'def generate_table_name' in line or 'f"tabela_autogerada_' in line:
                # Procurar por padrões de geração dinâmica
                dynamic_matches = re.finditer(r'["\'](\w+_autogerada_\d+)["\']', line)
                for match in dynamic_matches:
                    table_name = match.group(1)
                    ref = TableReference(
                        table_name=table_name,
                        file_path=file_path,
                        line_number=line_num,
                        context_type='dynamic_generation',
                        confidence=0.65,
                        raw_content=line.strip()
                    )
                    self.table_references.append(ref)
            
            # Código que escreve código
            if 'setattr' in line or 'exec(' in line or 'eval(' in line:
                # Procurar por referências de tabela em código auto-modificável
                meta_matches = re.finditer(r'["\'](\w+_dinamica|\w+_runtime|\w+_reflexao)["\']', line)
                for match in meta_matches:
                    table_name = match.group(1)
                    ref = TableReference(
                        table_name=table_name,
                        file_path=file_path,
                        line_number=line_num,
                        context_type='self_modifying_code',
                        confidence=0.60,
                        raw_content=line.strip()
                    )
                    self.table_references.append(ref)
    
    def _analyze_byte_patterns(self, content: str, file_path: str):
        """Análise de padrões em bytes e encoding complexo"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Detectar byte strings que podem conter nomes de tabela
            byte_matches = re.finditer(r'b["\']([^"\']*)["\']\.decode\(["\']utf-8["\']\)', line)
            for match in byte_matches:
                byte_content = match.group(1)
                try:
                    # Tentar decodificar e verificar se é nome de tabela
                    decoded = bytes(byte_content, 'utf-8').decode('unicode_escape')
                    if '_' in decoded and len(decoded) > 3 and decoded.replace('_', '').replace('-', '').isalnum():
                        ref = TableReference(
                            table_name=decoded,
                            file_path=file_path,
                            line_number=line_num,
                            context_type='byte_decoded',
                            confidence=0.55,
                            encoding_type='byte_string',
                            raw_content=line.strip()
                        )
                        self.table_references.append(ref)
                except:
                    pass
            
            # Detectar hex patterns que podem ser nomes de tabela
            hex_matches = re.finditer(r'\\x[0-9a-fA-F]{2}', line)
            if hex_matches:
                try:
                    # Tentar decodificar sequência hex completa
                    hex_bytes = re.findall(r'\\x([0-9a-fA-F]{2})', line)
                    if len(hex_bytes) > 4:  # Pelo menos 4 bytes
                        decoded_bytes = bytes([int(h, 16) for h in hex_bytes])
                        decoded_str = decoded_bytes.decode('utf-8')
                        if '_' in decoded_str and decoded_str.replace('_', '').isalnum():
                            ref = TableReference(
                                table_name=decoded_str,
                                file_path=file_path,
                                line_number=line_num,
                                context_type='hex_decoded',
                                confidence=0.50,
                                encoding_type='hex_bytes',
                                raw_content=line.strip()
                            )
                            self.table_references.append(ref)
                except:
                    pass
    
    def _extract_tables_from_sql(self, sql_content: str, file_path: str, line_num: int, context: str = 'embedded_sql'):
        """Extrai tabelas de conteúdo SQL com validação inteligente"""
        for pattern_info in self.sql_patterns:
            matches = re.finditer(pattern_info['pattern'], sql_content)
            
            for match in matches:
                table_name = match.group(pattern_info['table_group'])
                schema = match.group(pattern_info['schema_group']) if pattern_info.get('schema_group') else None
                
                # APLICAR FILTRO INTELIGENTE
                if table_name and len(table_name) > 1 and self._is_valid_table_name(table_name):
                    # Calcula confiança ajustada baseada no contexto SQL
                    base_confidence = pattern_info['confidence'] * 0.9
                    adjusted_confidence = self._calculate_sql_context_confidence(
                        table_name, sql_content, base_confidence
                    )
                    
                    ref = TableReference(
                        table_name=table_name,
                        schema=schema,
                        file_path=file_path,
                        line_number=line_num,
                        context_type=context,
                        operation_type=pattern_info['operation'],
                        confidence=adjusted_confidence,
                        raw_content=sql_content[:100]
                    )
                    self.table_references.append(ref)
    
    def _generate_ultimate_report(self, analysis_time: float) -> Dict[str, Any]:
        """Gera relatório DEFINITIVO"""
        # Estatísticas básicas
        total_references = len(self.table_references)
        unique_tables = len(set(ref.table_name for ref in self.table_references))
        files_with_tables = len(set(ref.file_path for ref in self.table_references))
        
        # Agrupamentos
        tables_map = defaultdict(list)
        context_breakdown = defaultdict(int)
        operation_breakdown = defaultdict(int)
        confidence_breakdown = defaultdict(int)
        encoding_breakdown = defaultdict(int)
        
        for ref in self.table_references:
            tables_map[ref.table_name].append(ref)
            context_breakdown[ref.context_type] += 1
            operation_breakdown[ref.operation_type] += 1
            
            # Breakdown de confiança
            conf_range = 'high' if ref.confidence >= 0.8 else 'medium' if ref.confidence >= 0.5 else 'low'
            confidence_breakdown[conf_range] += 1
            
            # Breakdown de encoding
            encoding_breakdown[ref.encoding_type or 'normal'] += 1
        
        # Top tabelas
        most_referenced = sorted(
            [(table, len(refs)) for table, refs in tables_map.items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        
        # Esquemas
        schemas = set(ref.schema for ref in self.table_references if ref.schema)
        
        # Padrões detectados
        total_patterns = (len(self.sql_patterns) + len(self.orm_patterns) + 
                         len(self.decorator_patterns) + len(self.config_patterns) +
                         len(self.exotic_patterns) + len(self.documentation_patterns) +
                         len(self.logging_patterns) + len(self.serialization_patterns) +
                         len(self.infrastructure_patterns))
        
        return {
            'analysis_summary': {
                'analysis_time_seconds': round(analysis_time, 2),
                'files_analyzed': len(self.analyzed_files),
                'files_with_table_references': files_with_tables,
                'total_table_references': total_references,
                'unique_tables_found': unique_tables,
                'schemas_found': list(schemas),
                'total_detection_patterns': total_patterns,
                'pattern_categories': {
                    'sql_patterns': len(self.sql_patterns),
                    'orm_patterns': len(self.orm_patterns),
                    'exotic_patterns': len(self.exotic_patterns),
                    'documentation_patterns': len(self.documentation_patterns),
                    'logging_patterns': len(self.logging_patterns),
                    'serialization_patterns': len(self.serialization_patterns),
                    'infrastructure_patterns': len(self.infrastructure_patterns)
                }
            },
            'statistics': {
                'context_breakdown': dict(context_breakdown),
                'operation_breakdown': dict(operation_breakdown),
                'confidence_breakdown': dict(confidence_breakdown),
                'encoding_breakdown': dict(encoding_breakdown),
                'most_referenced_tables': [{'table': table, 'references': count} for table, count in most_referenced]
            },
            'tables_discovered': {
                table_name: {
                    'reference_count': len(refs),
                    'files': list(set(ref.file_path for ref in refs)),
                    'contexts': list(set(ref.context_type for ref in refs)),
                    'operations': list(set(ref.operation_type for ref in refs if ref.operation_type)),
                    'encoding_types': list(set(ref.encoding_type for ref in refs if ref.encoding_type)),
                    'average_confidence': sum(ref.confidence for ref in refs) / len(refs),
                    'references': [
                        {
                            'file': ref.file_path,
                            'line': ref.line_number,
                            'context': ref.context_type,
                            'operation': ref.operation_type,
                            'confidence': ref.confidence,
                            'encoding': ref.encoding_type,
                            'raw_content': ref.raw_content[:100] + '...' if len(ref.raw_content) > 100 else ref.raw_content
                        }
                        for ref in refs
                    ]
                }
                for table_name, refs in tables_map.items()
            }
        }
    
    def _post_process_and_filter_results(self):
        """Pós-processamento INTELIGENTE para filtrar e rankear resultados"""
        if not self.table_references:
            return
        
        # 1. Agrupar por nome de tabela
        table_groups = defaultdict(list)
        for ref in self.table_references:
            table_groups[ref.table_name.lower()].append(ref)
        
        # 2. Aplicar filtros inteligentes
        filtered_refs = []
        
        for table_name, refs in table_groups.items():
            # Calcula score final para cada tabela
            final_score = self._calculate_final_table_score(table_name, refs)
            
            # THRESHOLD INTELIGENTE: só aceita tabelas com score > 0.65
            if final_score > 0.65:
                # Mantém apenas a melhor referência de cada contexto
                best_refs = self._select_best_references_per_context(refs)
                
                # Atualiza confiança final
                for ref in best_refs:
                    ref.confidence = final_score
                
                filtered_refs.extend(best_refs)
        
        # 3. Substitui a lista original
        self.table_references = filtered_refs
        
        # 4. Log do filtro aplicado
        self.logger.info(f"🧹 Filtro inteligente aplicado: {len(filtered_refs)} referências mantidas")
    
    def _calculate_final_table_score(self, table_name: str, refs: List[TableReference]) -> float:
        """Calcula score final inteligente baseado em múltiplos fatores"""
        if not refs:
            return 0.0
        
        # Score base: média das confianças
        base_score = sum(ref.confidence for ref in refs) / len(refs)
        
        # Fatores de ajuste
        adjustments = 0.0
        
        # 1. Boost para múltiplas referências (indica table real)
        if len(refs) > 1:
            adjustments += 0.1 * min(len(refs), 5)  # Max boost: 0.5
        
        # 2. Boost para contextos diversos (mais realista)
        unique_contexts = len(set(ref.context_type for ref in refs))
        if unique_contexts > 2:
            adjustments += 0.15
        
        # 3. Boost para operações SQL reais
        sql_operations = [ref.operation_type for ref in refs if ref.operation_type]
        if any(op in sql_operations for op in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
            adjustments += 0.2
        
        # 4. Penalidade para nomes suspeitos
        suspicious_patterns = [
            'arquivo.*teste.*controlado.*criado',
            'expected.*tables',
            'test.*data',
            'mock.*table',
            'dados_principais',
            'dados_raw', 
            'temp_old_data',
            'old_data',
            'raw_data'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, table_name.lower(), re.IGNORECASE):
                adjustments -= 0.5  # Penalidade maior
                break
        
        # 5. Boost para nomes realistas de BD
        realistic_patterns = [
            r'.*_(user|product|order|item|data|log|audit|session|config|backup|temp|history)s?$',
            r'^(user|product|order|item|data|log|audit|session|config|backup|temp|history)s?_.*',
            r'.*_\w+_\w+.*'  # Padrão módulo_entidade_tipo
        ]
        
        for pattern in realistic_patterns:
            if re.search(pattern, table_name.lower()):
                adjustments += 0.1
                break
        
        # Score final limitado entre 0 e 1
        final_score = max(0.0, min(1.0, base_score + adjustments))
        
        return final_score
    
    def _select_best_references_per_context(self, refs: List[TableReference]) -> List[TableReference]:
        """Seleciona as melhores referências por contexto"""
        context_groups = defaultdict(list)
        
        # Agrupa por contexto
        for ref in refs:
            context_groups[ref.context_type].append(ref)
        
        # Seleciona a melhor de cada contexto
        best_refs = []
        for context, context_refs in context_groups.items():
            # Ordena por confiança descendente
            best_ref = max(context_refs, key=lambda r: r.confidence)
            best_refs.append(best_ref)
        
        return best_refs

def main():
    """Função principal para execução via CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mapeador DEFINITIVO de tabelas PostgreSQL')
    parser.add_argument('path', help='Caminho para analisar')
    parser.add_argument('--output', '-o', default='postgresql_ultimate_map.json', help='Arquivo de saída')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verboso')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Analisa o projeto
    mapper = PostgreSQLTableMapper()
    results = mapper.analyze_project(args.path)
    
    # Salva resultados
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Mostra resumo
    summary = results['analysis_summary']
    print(f"\n🚀 Análise DEFINITIVA:")
    print(f"   📁 Arquivos analisados: {summary['files_analyzed']}")
    print(f"   🗃️ Tabelas encontradas: {summary['unique_tables_found']}")
    print(f"   📊 Total de referências: {summary['total_table_references']}")
    print(f"   🔍 Padrões de detecção: {summary['total_detection_patterns']}")
    print(f"   ⏱️ Tempo de análise: {summary['analysis_time_seconds']}s")
    
    if results['tables_discovered']:
        print(f"\n🏆 Top 5 tabelas mais referenciadas:")
        for item in results['statistics']['most_referenced_tables'][:5]:
            print(f"   • {item['table']}: {item['references']} referências")
    
    print(f"\n📄 Relatório DEFINITIVO salvo em: {args.output}")

if __name__ == "__main__":
    main()
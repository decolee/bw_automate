#!/usr/bin/env python3
"""
🗃️ POSTGRESQL TABLE MAPPER
Sistema completo para mapear tabelas PostgreSQL em códigos Python
Detecta: classes, decorators, arquivos externos, SQL embarcado, ORMs
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
    context_type: str = ""  # 'sql_string', 'orm_class', 'decorator', 'function_call'
    context_details: Dict[str, Any] = field(default_factory=dict)
    operation_type: str = ""  # 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER'
    confidence: float = 1.0  # 0.0 a 1.0
    raw_content: str = ""
    
    def __post_init__(self):
        # Normaliza nome da tabela
        self.table_name = self.table_name.strip('"\'`').lower()
        if self.schema:
            self.schema = self.schema.strip('"\'`').lower()

@dataclass
class CrossFileMapping:
    """Mapeamento entre arquivos"""
    source_file: str
    target_file: str
    reference_type: str  # 'import', 'inheritance', 'composition'
    table_references: List[TableReference] = field(default_factory=list)

class PostgreSQLTableMapper:
    """Mapeador completo de tabelas PostgreSQL"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.table_references: List[TableReference] = []
        self.cross_file_mappings: List[CrossFileMapping] = []
        self.analyzed_files: Set[str] = set()
        
        # Padrões para detecção de tabelas
        self.sql_patterns = self._initialize_sql_patterns()
        self.orm_patterns = self._initialize_orm_patterns()
        self.decorator_patterns = self._initialize_decorator_patterns()
        
    def _setup_logging(self):
        """Setup logging para debugging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def _initialize_sql_patterns(self) -> List[Dict]:
        """Inicializa padrões para SQL embarcado"""
        return [
            # CREATE TABLE (mais específico para evitar capturar IF)
            {
                'pattern': r'(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'CREATE',
                'confidence': 0.99
            },
            # DROP TABLE (mais específico)
            {
                'pattern': r'(?i)DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'DROP',
                'confidence': 0.99
            },
            # TRUNCATE TABLE
            {
                'pattern': r'(?i)TRUNCATE\s+TABLE\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'TRUNCATE',
                'confidence': 0.95
            },
            # SELECT FROM (com schema específico)
            {
                'pattern': r'(?i)SELECT\s+.*?\bFROM\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'SELECT',
                'confidence': 0.98
            },
            # SELECT FROM (sem schema)
            {
                'pattern': r'(?i)SELECT\s+.*?\bFROM\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|$|,)',
                'table_group': 1,
                'schema_group': None,
                'operation': 'SELECT',
                'confidence': 0.90
            },
            # INSERT INTO (com schema)
            {
                'pattern': r'(?i)INSERT\s+INTO\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'INSERT',
                'confidence': 0.98
            },
            # INSERT INTO (sem schema)
            {
                'pattern': r'(?i)INSERT\s+INTO\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|\()',
                'table_group': 1,
                'schema_group': None,
                'operation': 'INSERT',
                'confidence': 0.95
            },
            # UPDATE (com schema)
            {
                'pattern': r'(?i)UPDATE\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)\s+SET',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'UPDATE',
                'confidence': 0.98
            },
            # UPDATE (sem schema)
            {
                'pattern': r'(?i)UPDATE\s+(?:["\']?)(\w+)(?:["\']?)\s+SET',
                'table_group': 1,
                'schema_group': None,
                'operation': 'UPDATE',
                'confidence': 0.95
            },
            # DELETE FROM (com schema)
            {
                'pattern': r'(?i)DELETE\s+FROM\s+(?:["\']?)(\w+)\.(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'DELETE',
                'confidence': 0.98
            },
            # DELETE FROM (sem schema)
            {
                'pattern': r'(?i)DELETE\s+FROM\s+(?:["\']?)(\w+)(?:["\']?)(?:\s|$)',
                'table_group': 1,
                'schema_group': None,
                'operation': 'DELETE',
                'confidence': 0.95
            },
            # ALTER TABLE
            {
                'pattern': r'(?i)ALTER\s+TABLE\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'ALTER',
                'confidence': 0.95
            },
            # COPY (PostgreSQL específico)
            {
                'pattern': r'(?i)COPY\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)\s+(?:FROM|TO)',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'COPY',
                'confidence': 0.90
            },
            # JOIN patterns
            {
                'pattern': r'(?i)JOIN\s+(?:["\']?)(?:(\w+)\.)?(\w+)(?:["\']?)\s+',
                'table_group': 2,
                'schema_group': 1,
                'operation': 'JOIN',
                'confidence': 0.85
            }
        ]
    
    def _initialize_orm_patterns(self) -> List[Dict]:
        """Inicializa padrões para ORMs (SQLAlchemy, Django, etc.)"""
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
            # Raw SQL methods
            {
                'pattern': r'(execute|executemany|cursor\.execute)\s*\(\s*["\']([^"\']*)["\']',
                'sql_group': 2,
                'context': 'raw_sql_execution',
                'confidence': 0.85
            }
        ]
    
    def _initialize_decorator_patterns(self) -> List[Dict]:
        """Inicializa padrões para decorators"""
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
            # Custom decorators com table
            {
                'pattern': r'@\w*table\w*\s*\(\s*["\'](\w+)["\']',
                'table_group': 1,
                'confidence': 0.80
            }
        ]
    
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analisa projeto completo mapeando todas as tabelas"""
        start_time = time.time()
        project_path = Path(project_path)
        
        self.logger.info(f"🗃️ Iniciando mapeamento de tabelas PostgreSQL em {project_path}")
        
        # Encontra todos os arquivos Python
        python_files = list(project_path.rglob("*.py"))
        self.logger.info(f"📁 Encontrados {len(python_files)} arquivos Python")
        
        # Analisa cada arquivo
        for file_path in python_files:
            try:
                self._analyze_file(str(file_path))
            except Exception as e:
                self.logger.error(f"❌ Erro ao analisar {file_path}: {e}")
        
        # Analisa dependências entre arquivos
        self._analyze_cross_file_dependencies(python_files)
        
        # Constrói mapa final
        analysis_time = time.time() - start_time
        results = self._build_comprehensive_map(analysis_time)
        
        return results
    
    def _analyze_file(self, file_path: str):
        """Analisa um arquivo Python específico com tratamento robusto de erros"""
        if file_path in self.analyzed_files:
            return
        
        self.analyzed_files.add(file_path)
        
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
                self.logger.warning(f"Não foi possível ler arquivo {file_path} - encoding não suportado")
                return
            
            # Verifica se arquivo não está vazio
            if not content.strip():
                self.logger.debug(f"Arquivo vazio ignorado: {file_path}")
                return
            
            # Análises que não dependem de AST (mais robustas)
            try:
                self._analyze_sql_strings(content, file_path)
                self._analyze_orm_patterns(content, file_path)
                self._analyze_decorators(content, file_path)
            except Exception as e:
                self.logger.warning(f"Erro na análise de strings em {file_path}: {e}")
            
            # Parse AST com tratamento de erro específico
            try:
                tree = ast.parse(content)
                self._analyze_ast_structures(tree, file_path)
                self._analyze_imports_and_references(tree, file_path)
            except SyntaxError as e:
                self.logger.debug(f"Erro de sintaxe em {file_path} (linha {e.lineno}): {e.msg}")
                # Continua análise sem AST
            except Exception as e:
                self.logger.warning(f"Erro no parse AST de {file_path}: {e}")
            
        except FileNotFoundError:
            self.logger.error(f"Arquivo não encontrado: {file_path}")
        except PermissionError:
            self.logger.error(f"Sem permissão para ler arquivo: {file_path}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao analisar {file_path}: {e}")
    
    def _analyze_sql_strings(self, content: str, file_path: str):
        """Analisa strings SQL embarcadas"""
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
                        table_name.lower() not in ['if', 'not', 'exists', 'from', 'to', 'set', 'where', 'and', 'or']):
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
                            context_details={
                                'full_match': match.group(0),
                                'pattern_used': pattern
                            }
                        )
                        self.table_references.append(ref)
    
    def _analyze_ast_structures(self, tree: ast.AST, file_path: str):
        """Analisa estruturas AST para encontrar referências"""
        
        class TableVisitor(ast.NodeVisitor):
            def __init__(self, mapper, file_path):
                self.mapper = mapper
                self.file_path = file_path
                self.current_class = None
                
            def visit_ClassDef(self, node):
                old_class = self.current_class
                self.current_class = node.name
                
                # Procura por __tablename__ ou table_name
                for child in node.body:
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                if target.id in ['__tablename__', 'table_name', '_table_name']:
                                    if isinstance(child.value, ast.Constant):
                                        table_name = child.value.value
                                        if isinstance(table_name, str):
                                            ref = TableReference(
                                                table_name=table_name,
                                                file_path=self.file_path,
                                                line_number=child.lineno,
                                                context_type='orm_class',
                                                confidence=0.95,
                                                context_details={
                                                    'class_name': self.current_class,
                                                    'attribute': target.id
                                                }
                                            )
                                            self.mapper.table_references.append(ref)
                
                self.generic_visit(node)
                self.current_class = old_class
            
            def visit_Call(self, node):
                # Procura por chamadas de função que podem referenciar tabelas
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    # Funções comuns que recebem nomes de tabela
                    table_functions = [
                        'Table', 'create_table', 'drop_table', 'truncate_table',
                        'select_from', 'insert_into', 'update_table', 'delete_from'
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
                                context_details={
                                    'function_name': func_name,
                                    'class_context': self.current_class
                                }
                            )
                            self.mapper.table_references.append(ref)
                
                self.generic_visit(node)
        
        visitor = TableVisitor(self, file_path)
        visitor.visit(tree)
    
    def _analyze_orm_patterns(self, content: str, file_path: str):
        """Analisa padrões específicos de ORMs"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.orm_patterns:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    if 'table_group' in pattern_info:
                        # Padrão direto de tabela
                        table_name = match.group(pattern_info['table_group'])
                        
                        ref = TableReference(
                            table_name=table_name,
                            file_path=file_path,
                            line_number=line_num,
                            column_number=match.start(),
                            context_type='orm_pattern',
                            confidence=pattern_info['confidence'],
                            raw_content=line.strip(),
                            context_details={
                                'orm_context': pattern_info['context'],
                                'full_match': match.group(0)
                            }
                        )
                        self.table_references.append(ref)
                    
                    elif 'sql_group' in pattern_info:
                        # SQL dentro de execute()
                        sql_content = match.group(pattern_info['sql_group'])
                        self._extract_tables_from_sql(sql_content, file_path, line_num)
    
    def _analyze_decorators(self, content: str, file_path: str):
        """Analisa decorators que podem referenciar tabelas"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_info in self.decorator_patterns:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    table_name = match.group(pattern_info['table_group'])
                    
                    ref = TableReference(
                        table_name=table_name,
                        file_path=file_path,
                        line_number=line_num,
                        column_number=match.start(),
                        context_type='decorator',
                        confidence=pattern_info['confidence'],
                        raw_content=line.strip(),
                        context_details={
                            'decorator_type': 'table_decorator',
                            'full_match': match.group(0)
                        }
                    )
                    self.table_references.append(ref)
    
    def _analyze_imports_and_references(self, tree: ast.AST, file_path: str):
        """Analisa imports e referências entre arquivos"""
        
        class ImportVisitor(ast.NodeVisitor):
            def __init__(self, mapper, file_path):
                self.mapper = mapper
                self.file_path = file_path
                self.imports = []
                
            def visit_Import(self, node):
                for alias in node.names:
                    self.imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
                
            def visit_ImportFrom(self, node):
                for alias in node.names:
                    self.imports.append({
                        'type': 'from_import',
                        'module': node.module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
        
        visitor = ImportVisitor(self, file_path)
        visitor.visit(tree)
        
        # Armazena imports para análise cross-file posterior
        if hasattr(self, '_file_imports'):
            self._file_imports[file_path] = visitor.imports
        else:
            self._file_imports = {file_path: visitor.imports}
    
    def _extract_tables_from_sql(self, sql_content: str, file_path: str, line_num: int):
        """Extrai tabelas de conteúdo SQL"""
        for pattern_info in self.sql_patterns:
            pattern = pattern_info['pattern']
            matches = re.finditer(pattern, sql_content)
            
            for match in matches:
                table_group = pattern_info['table_group']
                schema_group = pattern_info.get('schema_group')
                operation = pattern_info.get('operation', 'UNKNOWN')
                
                table_name = match.group(table_group) if match.group(table_group) else ""
                schema = match.group(schema_group) if schema_group and match.group(schema_group) else None
                
                # Filtros para evitar falsos positivos
                if (table_name and len(table_name) > 1 and 
                    table_name.lower() not in ['if', 'not', 'exists', 'from', 'to', 'set', 'where', 'and', 'or']):
                    ref = TableReference(
                        table_name=table_name,
                        schema=schema.rstrip('.') if schema else None,
                        file_path=file_path,
                        line_number=line_num,
                        context_type='embedded_sql',
                        operation_type=operation,
                        confidence=pattern_info['confidence'] * 0.9,  # Ligeiramente menor confiança
                        raw_content=sql_content,
                        context_details={
                            'extraction_method': 'from_execute_call'
                        }
                    )
                    self.table_references.append(ref)
    
    def _analyze_cross_file_dependencies(self, python_files: List[Path]):
        """Analisa dependências entre arquivos e propaga referências de tabelas"""
        if not hasattr(self, '_file_imports'):
            return
        
        # Mapa de arquivo para tabelas referenciadas
        file_tables = {}
        for ref in self.table_references:
            if ref.file_path not in file_tables:
                file_tables[ref.file_path] = set()
            file_tables[ref.file_path].add(f"{ref.schema}.{ref.table_name}" if ref.schema else ref.table_name)
        
        for file_path, imports in self._file_imports.items():
            for import_info in imports:
                # Tenta encontrar arquivo correspondente ao import
                module_name = import_info.get('module', '')
                if module_name:
                    target_file = self._resolve_import_to_file(module_name, python_files)
                    if target_file:
                        target_file_str = str(target_file)
                        
                        # Cria mapeamento cross-file
                        mapping = CrossFileMapping(
                            source_file=file_path,
                            target_file=target_file_str,
                            reference_type=import_info['type']
                        )
                        
                        # Se o arquivo target tem tabelas, adiciona ao mapeamento
                        if target_file_str in file_tables:
                            target_tables = file_tables[target_file_str]
                            # Cria referências indiretas
                            for table_name in target_tables:
                                # Parse table name
                                if '.' in table_name:
                                    schema, table = table_name.split('.', 1)
                                else:
                                    schema, table = None, table_name
                                
                                indirect_ref = TableReference(
                                    table_name=table,
                                    schema=schema,
                                    file_path=file_path,
                                    line_number=import_info.get('line', 0),
                                    context_type='cross_file_reference',
                                    confidence=0.75,  # Menor confiança para referências indiretas
                                    context_details={
                                        'imported_from': target_file_str,
                                        'import_type': import_info['type'],
                                        'imported_name': import_info.get('name', module_name)
                                    }
                                )
                                mapping.table_references.append(indirect_ref)
                        
                        self.cross_file_mappings.append(mapping)
    
    def _resolve_import_to_file(self, module_name: str, python_files: List[Path]) -> Optional[Path]:
        """Resolve nome do módulo para arquivo correspondente"""
        # Converte nome do módulo para path
        module_path = module_name.replace('.', '/')
        
        for file_path in python_files:
            # Verifica se o arquivo corresponde ao módulo
            if str(file_path).endswith(f"{module_path}.py"):
                return file_path
            elif str(file_path).endswith(f"{module_path}/__init__.py"):
                return file_path
        
        return None
    
    def _build_comprehensive_map(self, analysis_time: float) -> Dict[str, Any]:
        """Constrói mapa abrangente das descobertas"""
        
        # Agrupa referências por tabela
        tables_map = defaultdict(list)
        for ref in self.table_references:
            full_table_name = f"{ref.schema}.{ref.table_name}" if ref.schema else ref.table_name
            tables_map[full_table_name].append(ref)
        
        # Calcula estatísticas
        total_tables = len(tables_map)
        total_references = len(self.table_references)
        files_with_tables = len(set(ref.file_path for ref in self.table_references))
        
        # Identifica tabelas mais referenciadas
        most_referenced = sorted(
            tables_map.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        # Agrupa por tipo de contexto
        context_breakdown = defaultdict(int)
        operation_breakdown = defaultdict(int)
        for ref in self.table_references:
            context_breakdown[ref.context_type] += 1
            operation_breakdown[ref.operation_type] += 1
        
        # Identifica esquemas
        schemas = set()
        for ref in self.table_references:
            if ref.schema:
                schemas.add(ref.schema)
        
        return {
            'analysis_summary': {
                'analysis_time_seconds': round(analysis_time, 2),
                'files_analyzed': len(self.analyzed_files),
                'files_with_table_references': files_with_tables,
                'total_table_references': total_references,
                'unique_tables_found': total_tables,
                'schemas_found': list(schemas),
                'cross_file_mappings': len(self.cross_file_mappings)
            },
            'tables_discovered': {
                table_name: {
                    'reference_count': len(refs),
                    'files': list(set(ref.file_path for ref in refs)),
                    'contexts': list(set(ref.context_type for ref in refs)),
                    'operations': list(set(ref.operation_type for ref in refs)),
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
            },
            'statistics': {
                'context_breakdown': dict(context_breakdown),
                'operation_breakdown': dict(operation_breakdown),
                'most_referenced_tables': [
                    {
                        'table': table_name,
                        'references': len(refs),
                        'files': len(set(ref.file_path for ref in refs))
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
                    'raw_content': ref.raw_content,
                    'context_details': ref.context_details
                }
                for ref in self.table_references
            ],
            'cross_file_analysis': [
                {
                    'source_file': mapping.source_file,
                    'target_file': mapping.target_file,
                    'reference_type': mapping.reference_type,
                    'tables_involved': len(mapping.table_references)
                }
                for mapping in self.cross_file_mappings
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
    
    def generate_table_map_report(self, output_file: str = "postgresql_table_map.json"):
        """Gera relatório detalhado do mapeamento"""
        if not self.table_references:
            self.logger.warning("Nenhuma referência de tabela encontrada para gerar relatório")
            return
        
        # Constrói relatório sem análise prévia (para casos de uso direto)
        results = self._build_comprehensive_map(0)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📄 Relatório salvo em: {output_file}")
        
        # Gera resumo em texto
        summary_file = output_file.replace('.json', '_summary.txt')
        self._generate_text_summary(results, summary_file)
    
    def _generate_text_summary(self, results: Dict[str, Any], output_file: str):
        """Gera resumo em texto legível"""
        summary = results['analysis_summary']
        tables = results['tables_discovered']
        stats = results['statistics']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("🗃️ MAPEAMENTO DE TABELAS POSTGRESQL\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"📊 RESUMO DA ANÁLISE:\n")
            f.write(f"   Arquivos analisados: {summary['files_analyzed']}\n")
            f.write(f"   Arquivos com tabelas: {summary['files_with_table_references']}\n")
            f.write(f"   Total de referências: {summary['total_table_references']}\n")
            f.write(f"   Tabelas únicas: {summary['unique_tables_found']}\n")
            f.write(f"   Esquemas encontrados: {len(summary['schemas_found'])}\n\n")
            
            f.write(f"🏆 TABELAS MAIS REFERENCIADAS:\n")
            for item in stats['most_referenced_tables'][:5]:
                f.write(f"   {item['table']}: {item['references']} refs em {item['files']} arquivos\n")
            f.write("\n")
            
            f.write(f"📈 DISTRIBUIÇÃO POR CONTEXTO:\n")
            for context, count in stats['context_breakdown'].items():
                f.write(f"   {context}: {count}\n")
            f.write("\n")
            
            f.write(f"🔧 DISTRIBUIÇÃO POR OPERAÇÃO:\n")
            for operation, count in stats['operation_breakdown'].items():
                if operation != "UNKNOWN":
                    f.write(f"   {operation}: {count}\n")
            f.write("\n")
            
            f.write(f"📋 TABELAS ENCONTRADAS:\n")
            for table_name, table_info in tables.items():
                f.write(f"\n   📄 {table_name}:\n")
                f.write(f"      Referências: {table_info['reference_count']}\n")
                f.write(f"      Arquivos: {len(table_info['files'])}\n")
                f.write(f"      Contextos: {', '.join(table_info['contexts'])}\n")
                operations = set(table_info['operations']) - {'UNKNOWN', ''}
                f.write(f"      Operações: {', '.join(operations) if operations else 'Nenhuma'}\n")
                f.write(f"      Confiança média: {table_info['average_confidence']:.2f}\n")
        
        self.logger.info(f"📄 Resumo salvo em: {output_file}")

def main():
    """Função principal para testar o mapeador"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mapeador de Tabelas PostgreSQL")
    parser.add_argument("project_path", help="Caminho do projeto Python")
    parser.add_argument("--output", "-o", default="postgresql_table_map.json", 
                       help="Arquivo de saída")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"❌ Caminho não encontrado: {args.project_path}")
        return
    
    print("🗃️ Iniciando mapeamento de tabelas PostgreSQL...")
    
    mapper = PostgreSQLTableMapper()
    results = mapper.analyze_project(args.project_path)
    
    # Salva resultados
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Mostra resumo
    summary = results['analysis_summary']
    print(f"\n📊 Análise completa:")
    print(f"   📁 Arquivos analisados: {summary['files_analyzed']}")
    print(f"   🗃️ Tabelas encontradas: {summary['unique_tables_found']}")
    print(f"   📊 Total de referências: {summary['total_table_references']}")
    print(f"   ⏱️ Tempo de análise: {summary['analysis_time_seconds']}s")
    
    if results['tables_discovered']:
        print(f"\n🏆 Top 5 tabelas mais referenciadas:")
        for item in results['statistics']['most_referenced_tables'][:5]:
            print(f"   • {item['table']}: {item['references']} referências")
    
    print(f"\n📄 Relatório detalhado salvo em: {args.output}")

if __name__ == "__main__":
    main()
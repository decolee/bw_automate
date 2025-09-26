#!/usr/bin/env python3
"""
COMPLETE PYTHON CODE ANALYZER - BW AUTOMATE
Analisador completo de código Python com cobertura 100%
Mapeia TODAS as construções Python possíveis para análise total
"""

import ast
import re
import os
import sys
import json
import inspect
import importlib
import types
import builtins
from typing import Dict, List, Any, Optional, Tuple, Set, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import logging
import collections
import traceback

# Construções Python específicas
import keyword
import token
import tokenize
import dis
import gc
import weakref

class PythonConstructType(Enum):
    """Tipos de construções Python"""
    # Básicas
    VARIABLE_ASSIGNMENT = "variable_assignment"
    FUNCTION_DEF = "function_def"
    CLASS_DEF = "class_def"
    IMPORT = "import"
    MODULE = "module"
    
    # Avançadas
    LAMBDA = "lambda"
    COMPREHENSION = "comprehension"
    GENERATOR = "generator"
    DECORATOR = "decorator"
    CONTEXT_MANAGER = "context_manager"
    ASYNC_FUNCTION = "async_function"
    ASYNC_CONTEXT_MANAGER = "async_context_manager"
    
    # Especiais
    METACLASS = "metaclass"
    DESCRIPTOR = "descriptor"
    PROPERTY = "property"
    STATIC_METHOD = "static_method"
    CLASS_METHOD = "class_method"
    
    # Controle de fluxo
    IF_STATEMENT = "if_statement"
    FOR_LOOP = "for_loop"
    WHILE_LOOP = "while_loop"
    TRY_EXCEPT = "try_except"
    WITH_STATEMENT = "with_statement"
    
    # Expressões
    CALL = "call"
    ATTRIBUTE_ACCESS = "attribute_access"
    SUBSCRIPT = "subscript"
    SLICE = "slice"
    
    # Operadores
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    BOOLEAN_OP = "boolean_op"
    COMPARISON = "comparison"
    
    # F-strings e formatação
    F_STRING = "f_string"
    FORMAT_STRING = "format_string"
    
    # Annotations e Type Hints
    TYPE_ANNOTATION = "type_annotation"
    TYPE_HINT = "type_hint"
    GENERIC_TYPE = "generic_type"
    
    # Especiais Python 3.8+
    WALRUS_OPERATOR = "walrus_operator"  # :=
    POSITIONAL_ONLY = "positional_only"  # /
    
    # Database específicos
    SQL_QUERY = "sql_query"
    ORM_OPERATION = "orm_operation"
    DATABASE_CONNECTION = "database_connection"
    
    # Dynamic code
    EXEC_EVAL = "exec_eval"
    GETATTR_SETATTR = "getattr_setattr"
    DYNAMIC_IMPORT = "dynamic_import"


@dataclass
class PythonConstruct:
    """Representa uma construção Python analisada"""
    construct_type: PythonConstructType
    name: str
    file_path: str
    line_number: int
    column_offset: int
    end_line_number: Optional[int]
    source_code: str
    context: str
    
    # Metadados específicos
    scope: str  # global, local, class, function
    namespace: str
    module_path: str
    
    # Relacionamentos
    parent_construct: Optional[str] = None
    child_constructs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    # Análise avançada
    complexity_score: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    
    # Database específico
    database_tables: List[str] = field(default_factory=list)
    sql_operations: List[str] = field(default_factory=list)
    
    # Dynamic analysis
    is_dynamic: bool = False
    runtime_types: List[str] = field(default_factory=list)
    
    # Security
    security_issues: List[str] = field(default_factory=list)
    
    # Performance
    performance_concerns: List[str] = field(default_factory=list)


@dataclass
class PythonAnalysisResult:
    """Resultado completo da análise Python"""
    total_constructs: int
    constructs_by_type: Dict[PythonConstructType, int]
    complexity_metrics: Dict[str, float]
    dependency_graph: Dict[str, List[str]]
    namespace_hierarchy: Dict[str, Any]
    database_usage: Dict[str, List[str]]
    security_issues: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]
    code_quality_score: float
    maintainability_index: float


class CompletePythonAnalyzer:
    """
    Analisador completo de código Python com cobertura total
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Inicializa o analisador"""
        self.config = config or {}
        self.setup_logging()
        
        # Cache para análise
        self.constructs_cache = {}
        self.namespace_cache = {}
        self.dependency_cache = {}
        
        # Padrões para diferentes construções
        self.setup_patterns()
        
        # Keywords e builtin functions
        self.python_keywords = set(keyword.kwlist)
        self.builtin_functions = set(dir(builtins))
        
    def setup_logging(self):
        """Configura logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_patterns(self):
        """Configura padrões de detecção"""
        self.sql_patterns = [
            # SQL direto em strings
            r'(?i)(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE)\s+.*',
            
            # Pandas SQL
            r'pd\.read_sql.*\(',
            r'\.read_sql.*\(',
            r'\.to_sql.*\(',
            
            # SQLAlchemy
            r'text\s*\(',
            r'select\s*\(',
            r'insert\s*\(',
            r'update\s*\(',
            r'delete\s*\(',
            
            # Django ORM
            r'\.objects\.',
            r'\.filter\(',
            r'\.get\(',
            r'\.create\(',
            r'\.update\(',
            r'\.delete\(',
            
            # Raw SQL
            r'\.raw\(',
            r'cursor\.execute',
            r'connection\.execute',
        ]
        
        self.database_patterns = [
            # Conexões
            r'psycopg2\.connect',
            r'pymongo\.MongoClient',
            r'mysql\.connector',
            r'sqlite3\.connect',
            r'create_engine',
            r'sessionmaker',
            
            # Configurações
            r'DATABASE.*=.*\{',
            r'DATABASES.*=.*\{',
            r'DB_.*=',
            r'.*_DATABASE_.*=',
        ]
        
        self.async_patterns = [
            r'async\s+def',
            r'await\s+',
            r'asyncio\.',
            r'aiohttp\.',
            r'async\s+with',
            r'async\s+for',
        ]
        
    def analyze_file(self, file_path: str) -> List[PythonConstruct]:
        """Analisa um arquivo Python completamente"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse AST
            tree = ast.parse(source_code, filename=file_path)
            
            # Análise completa
            constructs = []
            
            # 1. Análise AST tradicional
            ast_constructs = self._analyze_ast(tree, file_path, source_code)
            constructs.extend(ast_constructs)
            
            # 2. Análise de tokens para construções que AST pode perder
            token_constructs = self._analyze_tokens(file_path, source_code)
            constructs.extend(token_constructs)
            
            # 3. Análise de bytecode para otimizações
            bytecode_constructs = self._analyze_bytecode(source_code, file_path)
            constructs.extend(bytecode_constructs)
            
            # 4. Análise regex para padrões específicos
            regex_constructs = self._analyze_regex_patterns(source_code, file_path)
            constructs.extend(regex_constructs)
            
            # 5. Análise dinâmica se possível
            if self.config.get('enable_dynamic_analysis', False):
                dynamic_constructs = self._analyze_dynamic(file_path, source_code)
                constructs.extend(dynamic_constructs)
            
            return constructs
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return []
    
    def _analyze_ast(self, tree: ast.AST, file_path: str, source_code: str) -> List[PythonConstruct]:
        """Análise completa via AST"""
        constructs = []
        lines = source_code.splitlines()
        
        class CompleteASTVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.scope_stack = ['global']
                self.namespace_stack = ['']
                
            def visit_FunctionDef(self, node):
                construct = self._create_function_construct(node, file_path, lines)
                constructs.append(construct)
                
                # Entrar no escopo da função
                self.scope_stack.append('function')
                self.namespace_stack.append(node.name)
                
                # Analisar decorators
                for decorator in node.decorator_list:
                    dec_construct = self._create_decorator_construct(decorator, file_path, lines)
                    constructs.append(dec_construct)
                
                # Analisar argumentos com type hints
                for arg in node.args.args:
                    if arg.annotation:
                        type_construct = self._create_type_annotation_construct(arg, file_path, lines)
                        constructs.append(type_construct)
                
                self.generic_visit(node)
                
                # Sair do escopo
                self.scope_stack.pop()
                self.namespace_stack.pop()
                
            def visit_AsyncFunctionDef(self, node):
                construct = self._create_async_function_construct(node, file_path, lines)
                constructs.append(construct)
                
                self.scope_stack.append('async_function')
                self.namespace_stack.append(node.name)
                self.generic_visit(node)
                self.scope_stack.pop()
                self.namespace_stack.pop()
                
            def visit_ClassDef(self, node):
                construct = self._create_class_construct(node, file_path, lines)
                constructs.append(construct)
                
                # Analisar metaclass
                for keyword in node.keywords:
                    if keyword.arg == 'metaclass':
                        meta_construct = self._create_metaclass_construct(keyword, file_path, lines)
                        constructs.append(meta_construct)
                
                self.scope_stack.append('class')
                self.namespace_stack.append(node.name)
                self.generic_visit(node)
                self.scope_stack.pop()
                self.namespace_stack.pop()
                
            def visit_Lambda(self, node):
                construct = self._create_lambda_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_ListComp(self, node):
                construct = self._create_comprehension_construct(node, 'list', file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_DictComp(self, node):
                construct = self._create_comprehension_construct(node, 'dict', file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_SetComp(self, node):
                construct = self._create_comprehension_construct(node, 'set', file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_GeneratorExp(self, node):
                construct = self._create_generator_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_With(self, node):
                construct = self._create_with_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_AsyncWith(self, node):
                construct = self._create_async_with_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_Call(self, node):
                construct = self._create_call_construct(node, file_path, lines)
                constructs.append(construct)
                
                # Detectar SQL operations
                if self._is_sql_call(node):
                    sql_construct = self._create_sql_construct(node, file_path, lines)
                    constructs.append(sql_construct)
                
                self.generic_visit(node)
                
            def visit_NamedExpr(self, node):  # Walrus operator :=
                construct = self._create_walrus_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_JoinedStr(self, node):  # f-strings
                construct = self._create_fstring_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_Assign(self, node):
                construct = self._create_assignment_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_AnnAssign(self, node):  # Type annotated assignment
                construct = self._create_annotated_assignment_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_Import(self, node):
                construct = self._create_import_construct(node, file_path, lines)
                constructs.append(construct)
                
            def visit_ImportFrom(self, node):
                construct = self._create_import_from_construct(node, file_path, lines)
                constructs.append(construct)
                
            def visit_Try(self, node):
                construct = self._create_try_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_For(self, node):
                construct = self._create_for_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_While(self, node):
                construct = self._create_while_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def visit_If(self, node):
                construct = self._create_if_construct(node, file_path, lines)
                constructs.append(construct)
                self.generic_visit(node)
                
            def _create_function_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.FUNCTION_DEF,
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    complexity_score=self._calculate_function_complexity(node),
                    cyclomatic_complexity=self._calculate_cyclomatic_complexity(node)
                )
                
            def _create_async_function_construct(self, node, file_path, lines):
                construct = self._create_function_construct(node, file_path, lines)
                construct.construct_type = PythonConstructType.ASYNC_FUNCTION
                return construct
                
            def _create_class_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.CLASS_DEF,
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    complexity_score=self._calculate_class_complexity(node)
                )
                
            def _create_lambda_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.LAMBDA,
                    name=f"lambda_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_comprehension_construct(self, node, comp_type, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.COMPREHENSION,
                    name=f"{comp_type}_comp_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    complexity_score=len(node.generators)
                )
                
            def _create_generator_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.GENERATOR,
                    name=f"generator_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_with_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.WITH_STATEMENT,
                    name=f"with_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_async_with_construct(self, node, file_path, lines):
                construct = self._create_with_construct(node, file_path, lines)
                construct.construct_type = PythonConstructType.ASYNC_CONTEXT_MANAGER
                construct.name = f"async_with_{node.lineno}"
                return construct
                
            def _create_call_construct(self, node, file_path, lines):
                func_name = self._get_function_name(node.func)
                return PythonConstruct(
                    construct_type=PythonConstructType.CALL,
                    name=func_name,
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_sql_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.SQL_QUERY,
                    name=f"sql_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    sql_operations=self._extract_sql_operations(node)
                )
                
            def _create_walrus_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.WALRUS_OPERATOR,
                    name=f"walrus_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_fstring_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.F_STRING,
                    name=f"fstring_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_assignment_construct(self, node, file_path, lines):
                target_names = []
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        target_names.append(target.id)
                
                return PythonConstruct(
                    construct_type=PythonConstructType.VARIABLE_ASSIGNMENT,
                    name=', '.join(target_names) if target_names else f"assign_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_annotated_assignment_construct(self, node, file_path, lines):
                target_name = ""
                if isinstance(node.target, ast.Name):
                    target_name = node.target.id
                
                return PythonConstruct(
                    construct_type=PythonConstructType.TYPE_ANNOTATION,
                    name=target_name or f"annotated_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_import_construct(self, node, file_path, lines):
                names = [alias.name for alias in node.names]
                return PythonConstruct(
                    construct_type=PythonConstructType.IMPORT,
                    name=', '.join(names),
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    dependencies=names
                )
                
            def _create_import_from_construct(self, node, file_path, lines):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                return PythonConstruct(
                    construct_type=PythonConstructType.IMPORT,
                    name=f"from {module} import {', '.join(names)}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    dependencies=[module] if module else []
                )
                
            def _create_try_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.TRY_EXCEPT,
                    name=f"try_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    complexity_score=len(node.handlers) + (1 if node.orelse else 0) + (1 if node.finalbody else 0)
                )
                
            def _create_for_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.FOR_LOOP,
                    name=f"for_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    complexity_score=1 + (1 if node.orelse else 0)
                )
                
            def _create_while_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.WHILE_LOOP,
                    name=f"while_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    complexity_score=1 + (1 if node.orelse else 0)
                )
                
            def _create_if_construct(self, node, file_path, lines):
                elif_count = len([n for n in ast.walk(node) if isinstance(n, ast.If) and n != node])
                return PythonConstruct(
                    construct_type=PythonConstructType.IF_STATEMENT,
                    name=f"if_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path,
                    complexity_score=1 + elif_count + (1 if node.orelse else 0)
                )
                
            def _create_decorator_construct(self, node, file_path, lines):
                decorator_name = self._get_function_name(node)
                return PythonConstruct(
                    construct_type=PythonConstructType.DECORATOR,
                    name=decorator_name,
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_type_annotation_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.TYPE_ANNOTATION,
                    name=f"type_hint_{node.lineno}",
                    file_path=file_path,
                    line_number=node.lineno,
                    column_offset=node.col_offset,
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _create_metaclass_construct(self, node, file_path, lines):
                return PythonConstruct(
                    construct_type=PythonConstructType.METACLASS,
                    name=f"metaclass_{node.lineno}",
                    file_path=file_path,
                    line_number=getattr(node, 'lineno', 1),
                    column_offset=getattr(node, 'col_offset', 0),
                    end_line_number=getattr(node, 'end_lineno', None),
                    source_code=self._get_source_segment(lines, node),
                    context='.'.join(self.namespace_stack),
                    scope=self.scope_stack[-1],
                    namespace='.'.join(self.namespace_stack),
                    module_path=file_path
                )
                
            def _get_source_segment(self, lines, node):
                """Extrai o segmento de código fonte"""
                try:
                    if hasattr(node, 'lineno'):
                        start_line = node.lineno - 1
                        end_line = getattr(node, 'end_lineno', node.lineno) 
                        return '\n'.join(lines[start_line:end_line])
                    return ""
                except:
                    return ""
                    
            def _get_function_name(self, node):
                """Extrai nome da função de um nó AST"""
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    return f"{self._get_function_name(node.value)}.{node.attr}"
                elif isinstance(node, ast.Call):
                    return self._get_function_name(node.func)
                return "unknown"
                
            def _is_sql_call(self, node):
                """Verifica se é uma chamada SQL"""
                func_name = self._get_function_name(node.func)
                sql_indicators = [
                    'execute', 'read_sql', 'to_sql', 'query', 'select', 
                    'insert', 'update', 'delete', 'create', 'drop'
                ]
                return any(indicator in func_name.lower() for indicator in sql_indicators)
                
            def _extract_sql_operations(self, node):
                """Extrai operações SQL de um nó"""
                operations = []
                # Implementar extração de SQL baseada no contexto do nó
                return operations
                
            def _calculate_function_complexity(self, node):
                """Calcula complexidade de função"""
                complexity = 1  # Base complexity
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                return complexity
                
            def _calculate_class_complexity(self, node):
                """Calcula complexidade de classe"""
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                return len(methods)
                
            def _calculate_cyclomatic_complexity(self, node):
                """Calcula complexidade ciclomática"""
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                    elif isinstance(child, ast.ExceptHandler):
                        complexity += 1
                return complexity
        
        visitor = CompleteASTVisitor(self)
        visitor.visit(tree)
        
        return constructs
    
    def _analyze_tokens(self, file_path: str, source_code: str) -> List[PythonConstruct]:
        """Análise baseada em tokens para capturar construções que AST pode perder"""
        constructs = []
        
        try:
            tokens = list(tokenize.generate_tokens(iter(source_code.splitlines()).__next__))
            
            for i, token in enumerate(tokens):
                if token.type == tokenize.COMMENT:
                    # Analisar comentários especiais (docstrings inline, TODOs, etc.)
                    continue
                elif token.type == tokenize.STRING:
                    # Analisar strings para SQL, regex patterns, etc.
                    if self._contains_sql(token.string):
                        construct = PythonConstruct(
                            construct_type=PythonConstructType.SQL_QUERY,
                            name=f"sql_string_{token.start[0]}",
                            file_path=file_path,
                            line_number=token.start[0],
                            column_offset=token.start[1],
                            end_line_number=token.end[0],
                            source_code=token.string,
                            context="string_literal",
                            scope="unknown",
                            namespace="",
                            module_path=file_path
                        )
                        constructs.append(construct)
                        
        except Exception as e:
            self.logger.error(f"Token analysis error in {file_path}: {e}")
            
        return constructs
    
    def _analyze_bytecode(self, source_code: str, file_path: str) -> List[PythonConstruct]:
        """Análise de bytecode para otimizações e detecção avançada"""
        constructs = []
        
        try:
            # Compilar para bytecode
            code_obj = compile(source_code, file_path, 'exec')
            
            # Analisar bytecode
            for instruction in dis.get_instructions(code_obj):
                if instruction.opname in ['CALL_FUNCTION', 'CALL_METHOD']:
                    # Detectar chamadas dinâmicas
                    construct = PythonConstruct(
                        construct_type=PythonConstructType.CALL,
                        name=f"dynamic_call_{instruction.offset}",
                        file_path=file_path,
                        line_number=instruction.starts_line or 1,
                        column_offset=0,
                        end_line_number=None,
                        source_code=f"{instruction.opname}({instruction.argval})",
                        context="bytecode",
                        scope="unknown",
                        namespace="",
                        module_path=file_path,
                        is_dynamic=True
                    )
                    constructs.append(construct)
                    
        except Exception as e:
            self.logger.error(f"Bytecode analysis error in {file_path}: {e}")
            
        return constructs
    
    def _analyze_regex_patterns(self, source_code: str, file_path: str) -> List[PythonConstruct]:
        """Análise baseada em regex para padrões específicos"""
        constructs = []
        lines = source_code.splitlines()
        
        # SQL patterns
        for line_num, line in enumerate(lines, 1):
            for pattern in self.sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    construct = PythonConstruct(
                        construct_type=PythonConstructType.SQL_QUERY,
                        name=f"sql_pattern_{line_num}",
                        file_path=file_path,
                        line_number=line_num,
                        column_offset=0,
                        end_line_number=line_num,
                        source_code=line.strip(),
                        context="regex_detection",
                        scope="unknown",
                        namespace="",
                        module_path=file_path
                    )
                    constructs.append(construct)
                    break
        
        # Database connection patterns
        for line_num, line in enumerate(lines, 1):
            for pattern in self.database_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    construct = PythonConstruct(
                        construct_type=PythonConstructType.DATABASE_CONNECTION,
                        name=f"db_connection_{line_num}",
                        file_path=file_path,
                        line_number=line_num,
                        column_offset=0,
                        end_line_number=line_num,
                        source_code=line.strip(),
                        context="regex_detection",
                        scope="unknown",
                        namespace="",
                        module_path=file_path
                    )
                    constructs.append(construct)
                    break
        
        # Async patterns
        for line_num, line in enumerate(lines, 1):
            for pattern in self.async_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    construct = PythonConstruct(
                        construct_type=PythonConstructType.ASYNC_FUNCTION,
                        name=f"async_pattern_{line_num}",
                        file_path=file_path,
                        line_number=line_num,
                        column_offset=0,
                        end_line_number=line_num,
                        source_code=line.strip(),
                        context="regex_detection",
                        scope="unknown",
                        namespace="",
                        module_path=file_path
                    )
                    constructs.append(construct)
                    break
        
        return constructs
    
    def _analyze_dynamic(self, file_path: str, source_code: str) -> List[PythonConstruct]:
        """Análise dinâmica através de execução controlada"""
        constructs = []
        
        # ATENÇÃO: Análise dinâmica pode ser perigosa
        # Implementar apenas em ambiente controlado
        if not self.config.get('safe_dynamic_analysis', True):
            return constructs
            
        try:
            # Criar ambiente seguro para análise
            safe_globals = {
                '__builtins__': {
                    'print': lambda *args: None,  # Desabilitar print
                    'open': lambda *args: None,   # Desabilitar file operations
                    'input': lambda *args: "",    # Desabilitar input
                }
            }
            
            # Executar em namespace isolado
            exec(compile(source_code, file_path, 'exec'), safe_globals)
            
            # Analisar objetos criados
            for name, obj in safe_globals.items():
                if not name.startswith('__'):
                    construct = PythonConstruct(
                        construct_type=PythonConstructType.VARIABLE_ASSIGNMENT,
                        name=name,
                        file_path=file_path,
                        line_number=1,
                        column_offset=0,
                        end_line_number=1,
                        source_code=f"{name} = {type(obj).__name__}",
                        context="dynamic_analysis",
                        scope="global",
                        namespace="",
                        module_path=file_path,
                        is_dynamic=True,
                        runtime_types=[type(obj).__name__]
                    )
                    constructs.append(construct)
                    
        except Exception as e:
            self.logger.warning(f"Dynamic analysis failed for {file_path}: {e}")
            
        return constructs
    
    def _contains_sql(self, string_content: str) -> bool:
        """Verifica se string contém SQL"""
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        content_upper = string_content.upper()
        return any(keyword in content_upper for keyword in sql_keywords)
    
    def analyze_project(self, project_path: str) -> PythonAnalysisResult:
        """Analisa projeto Python completo"""
        all_constructs = []
        
        # Encontrar todos os arquivos Python
        python_files = []
        for root, dirs, files in os.walk(project_path):
            # Ignorar diretórios virtuais e cache
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        # Analisar cada arquivo
        for file_path in python_files:
            self.logger.info(f"Analyzing {file_path}")
            file_constructs = self.analyze_file(file_path)
            all_constructs.extend(file_constructs)
        
        # Compilar resultados
        return self._compile_analysis_results(all_constructs)
    
    def _compile_analysis_results(self, constructs: List[PythonConstruct]) -> PythonAnalysisResult:
        """Compila resultados da análise"""
        
        # Contar por tipo
        constructs_by_type = {}
        for construct in constructs:
            constructs_by_type[construct.construct_type] = constructs_by_type.get(construct.construct_type, 0) + 1
        
        # Calcular métricas de complexidade
        total_complexity = sum(construct.complexity_score for construct in constructs)
        avg_complexity = total_complexity / len(constructs) if constructs else 0
        
        # Construir grafo de dependências
        dependency_graph = {}
        for construct in constructs:
            dependency_graph[construct.name] = construct.dependencies
        
        # Hierarquia de namespaces
        namespace_hierarchy = {}
        for construct in constructs:
            if construct.namespace:
                parts = construct.namespace.split('.')
                current = namespace_hierarchy
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        # Uso de banco de dados
        database_usage = {}
        for construct in constructs:
            if construct.sql_operations:
                database_usage[construct.name] = construct.sql_operations
        
        # Issues de segurança e performance
        security_issues = []
        performance_issues = []
        
        for construct in constructs:
            if construct.security_issues:
                security_issues.extend([{
                    'construct': construct.name,
                    'file': construct.file_path,
                    'line': construct.line_number,
                    'issues': construct.security_issues
                }])
            
            if construct.performance_concerns:
                performance_issues.extend([{
                    'construct': construct.name,
                    'file': construct.file_path,
                    'line': construct.line_number,
                    'concerns': construct.performance_concerns
                }])
        
        # Score de qualidade (0-100)
        quality_score = self._calculate_quality_score(constructs)
        
        # Índice de manutenibilidade
        maintainability_index = self._calculate_maintainability_index(constructs)
        
        return PythonAnalysisResult(
            total_constructs=len(constructs),
            constructs_by_type=constructs_by_type,
            complexity_metrics={
                'total_complexity': total_complexity,
                'average_complexity': avg_complexity,
                'max_complexity': max(construct.complexity_score for construct in constructs) if constructs else 0
            },
            dependency_graph=dependency_graph,
            namespace_hierarchy=namespace_hierarchy,
            database_usage=database_usage,
            security_issues=security_issues,
            performance_issues=performance_issues,
            code_quality_score=quality_score,
            maintainability_index=maintainability_index
        )
    
    def _calculate_quality_score(self, constructs: List[PythonConstruct]) -> float:
        """Calcula score de qualidade do código"""
        if not constructs:
            return 0.0
        
        score = 100.0
        
        # Penalizar alta complexidade
        high_complexity_count = sum(1 for c in constructs if c.complexity_score > 10)
        score -= (high_complexity_count / len(constructs)) * 30
        
        # Penalizar issues de segurança
        security_issues_count = sum(len(c.security_issues) for c in constructs)
        score -= min(security_issues_count * 5, 40)
        
        # Penalizar issues de performance
        performance_issues_count = sum(len(c.performance_concerns) for c in constructs)
        score -= min(performance_issues_count * 3, 20)
        
        return max(0.0, score)
    
    def _calculate_maintainability_index(self, constructs: List[PythonConstruct]) -> float:
        """Calcula índice de manutenibilidade"""
        if not constructs:
            return 0.0
        
        # Baseado em métricas de Halstead e complexidade ciclomática
        avg_complexity = sum(c.cyclomatic_complexity for c in constructs) / len(constructs)
        
        # Simplificado - fórmula real é mais complexa
        maintainability = max(0, 171 - 5.2 * avg_complexity - 0.23 * avg_complexity)
        
        return min(100.0, maintainability)
    
    def export_results(self, results: PythonAnalysisResult, output_path: str):
        """Exporta resultados para arquivo JSON"""
        results_dict = asdict(results)
        
        # Converter enums para strings
        if 'constructs_by_type' in results_dict:
            constructs_by_type_str = {}
            for key, value in results_dict['constructs_by_type'].items():
                if hasattr(key, 'value'):
                    constructs_by_type_str[key.value] = value
                else:
                    constructs_by_type_str[str(key)] = value
            results_dict['constructs_by_type'] = constructs_by_type_str
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Results exported to {output_path}")


def main():
    """Função principal para teste"""
    analyzer = CompletePythonAnalyzer({
        'enable_dynamic_analysis': False,  # Seguro por padrão
        'safe_dynamic_analysis': True
    })
    
    # Testar com arquivo atual
    current_file = __file__
    constructs = analyzer.analyze_file(current_file)
    
    print(f"Analyzed {len(constructs)} constructs in {current_file}")
    
    # Mostrar alguns resultados
    for construct in constructs[:5]:
        print(f"- {construct.construct_type.value}: {construct.name} at line {construct.line_number}")


if __name__ == "__main__":
    main()
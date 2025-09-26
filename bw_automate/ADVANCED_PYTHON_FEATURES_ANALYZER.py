#!/usr/bin/env python3
"""
ADVANCED PYTHON FEATURES ANALYZER - BW AUTOMATE
Análise avançada de recursos Python específicos que sistemas básicos perdem
Foco em construções modernas, padrões avançados e otimizações
"""

import ast
import re
import os
import sys
import json
import inspect
import types
import keyword
import builtins
from typing import Dict, List, Any, Optional, Tuple, Set, Union, get_type_hints
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import logging
import importlib
import pkgutil
import dis
import tokenize

# Python 3.8+ features
try:
    from typing import TypedDict, Literal, Final, Protocol
except ImportError:
    TypedDict = dict
    Literal = None
    Final = None
    Protocol = None

# Python 3.9+ features
try:
    from functools import singledispatch, singledispatchmethod
except ImportError:
    singledispatch = None
    singledispatchmethod = None

# Python 3.10+ features
try:
    from types import UnionType
except ImportError:
    UnionType = None


class AdvancedPythonFeature(Enum):
    """Recursos Python avançados"""
    # Type hints avançados
    UNION_TYPE = "union_type"                    # Union[int, str] ou int | str
    GENERIC_TYPE = "generic_type"                # List[T], Dict[K, V]
    TYPED_DICT = "typed_dict"                    # TypedDict
    LITERAL_TYPE = "literal_type"               # Literal["yes", "no"]
    FINAL_TYPE = "final_type"                   # Final[int]
    PROTOCOL = "protocol"                        # typing.Protocol
    TYPE_ALIAS = "type_alias"                   # MyType = Union[int, str]
    
    # Pattern matching (Python 3.10+)
    MATCH_STATEMENT = "match_statement"          # match/case
    CASE_PATTERN = "case_pattern"               # case patterns
    GUARD_PATTERN = "guard_pattern"             # case x if condition
    
    # Decorators avançados
    SINGLEDISPATCH = "singledispatch"           # @singledispatch
    SINGLEDISPATCH_METHOD = "singledispatch_method"  # @singledispatchmethod
    PROPERTY_DECORATOR = "property_decorator"    # @property
    CACHED_PROPERTY = "cached_property"         # @cached_property
    LRU_CACHE = "lru_cache"                     # @lru_cache
    
    # Context managers avançados
    CONTEXTLIB_MANAGER = "contextlib_manager"   # @contextmanager
    ASYNC_CONTEXT_MANAGER = "async_context_manager"  # @asynccontextmanager
    SUPPRESS_CONTEXT = "suppress_context"       # contextlib.suppress
    
    # Metaclasses e descritores
    METACLASS = "metaclass"                     # class Meta(type)
    DESCRIPTOR = "descriptor"                   # __get__, __set__
    PROPERTY_DESCRIPTOR = "property_descriptor" # property()
    SLOT_DESCRIPTOR = "__slots__"               # __slots__
    
    # Geradores avançados
    GENERATOR_EXPRESSION = "generator_expression"  # (x for x in iterable)
    YIELD_FROM = "yield_from"                   # yield from
    ASYNC_GENERATOR = "async_generator"         # async def + yield
    
    # Corrotinas e async
    ASYNC_FUNCTION = "async_function"           # async def
    AWAIT_EXPRESSION = "await_expression"       # await
    ASYNC_COMPREHENSION = "async_comprehension" # [x async for x in ...]
    ASYNC_WITH = "async_with"                   # async with
    ASYNC_FOR = "async_for"                     # async for
    
    # Anotações de função avançadas
    POSITIONAL_ONLY = "positional_only"        # def func(a, /, b)
    KEYWORD_ONLY = "keyword_only"              # def func(a, *, b)
    VARIABLE_ANNOTATION = "variable_annotation" # var: int = 5
    
    # Expressões avançadas
    WALRUS_OPERATOR = "walrus_operator"        # :=
    F_STRING_EXPRESSION = "f_string_expression" # f"{expr=}"
    F_STRING_FORMAT_SPEC = "f_string_format_spec" # f"{x:.2f}"
    
    # Operadores especiais
    MATRIX_MULTIPLICATION = "matrix_multiplication"  # @
    FLOOR_DIVISION = "floor_division"           # //
    POWER_OPERATOR = "power_operator"          # **
    
    # Recursos dinâmicos
    EXEC_DYNAMIC = "exec_dynamic"              # exec()
    EVAL_DYNAMIC = "eval_dynamic"              # eval()
    GETATTR_DYNAMIC = "getattr_dynamic"        # getattr()
    SETATTR_DYNAMIC = "setattr_dynamic"        # setattr()
    HASATTR_DYNAMIC = "hasattr_dynamic"        # hasattr()
    DELATTR_DYNAMIC = "delattr_dynamic"        # delattr()
    
    # Import avançados
    DYNAMIC_IMPORT = "dynamic_import"          # importlib.import_module
    RELATIVE_IMPORT = "relative_import"        # from .module import
    STAR_IMPORT = "star_import"                # from module import *
    
    # Recursos de classe avançados
    CLASS_DECORATOR = "class_decorator"        # @decorator class
    DATACLASS = "dataclass"                    # @dataclass
    ATTRS_CLASS = "attrs_class"                # @attr.s
    PYDANTIC_MODEL = "pydantic_model"          # BaseModel
    
    # Encoding e bytes
    BYTE_STRING = "byte_string"                # b"string"
    RAW_STRING = "raw_string"                  # r"string"
    UNICODE_ESCAPE = "unicode_escape"          # \u, \U, \N
    
    # Recursos especiais de Python
    ELLIPSIS = "ellipsis"                      # ...
    NONE_TYPE = "none_type"                    # None
    NOTIMPLEMENTED = "notimplemented"          # NotImplemented
    
    # Weak references
    WEAK_REFERENCE = "weak_reference"          # weakref
    
    # Memory management
    GARBAGE_COLLECTION = "garbage_collection"  # gc module
    
    # Introspection
    INSPECT_MODULE = "inspect_module"          # inspect module usage
    TYPE_CHECKING = "type_checking"            # TYPE_CHECKING
    
    # Exception handling avançado
    EXCEPTION_CHAINING = "exception_chaining"  # raise ... from
    EXCEPTION_GROUP = "exception_group"        # ExceptionGroup (3.11+)
    
    # Structural pattern matching (3.10+)
    SEQUENCE_PATTERN = "sequence_pattern"      # case [a, b, *rest]
    MAPPING_PATTERN = "mapping_pattern"        # case {"key": value}
    CLASS_PATTERN = "class_pattern"            # case Point(x, y)
    AS_PATTERN = "as_pattern"                  # case pattern as name
    OR_PATTERN = "or_pattern"                  # case A() | B()


@dataclass
class AdvancedFeatureUsage:
    """Uso de recurso Python avançado"""
    feature_type: AdvancedPythonFeature
    name: str
    file_path: str
    line_number: int
    column_offset: int
    end_line_number: Optional[int]
    source_code: str
    context: str
    
    # Detalhes específicos do recurso
    feature_details: Dict[str, Any] = field(default_factory=dict)
    
    # Análise de complexidade
    complexity_impact: int = 0
    maintenance_risk: str = "low"  # low, medium, high
    
    # Compatibilidade
    min_python_version: str = "3.6"
    requires_typing_extensions: bool = False
    
    # Performance implications
    performance_impact: str = "neutral"  # positive, neutral, negative
    memory_impact: str = "neutral"
    
    # Relacionamentos
    dependencies: List[str] = field(default_factory=list)
    related_features: List[str] = field(default_factory=list)


class AdvancedPythonFeaturesAnalyzer:
    """
    Analisador de recursos Python avançados
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Inicializa o analisador"""
        self.config = config or {}
        self.setup_logging()
        
        # Python version compatibility mapping
        self.version_features = {
            "3.6": ["variable_annotation", "f_string_expression"],
            "3.7": ["dataclass", "contextvars"],
            "3.8": ["walrus_operator", "positional_only", "typed_dict", "literal_type", "final_type", "protocol"],
            "3.9": ["union_type", "generic_builtins"],
            "3.10": ["match_statement", "case_pattern", "union_operator"],
            "3.11": ["exception_group", "tomllib"],
            "3.12": ["type_params", "buffer_protocol"]
        }
        
        # Patterns for advanced features
        self.setup_advanced_patterns()
        
    def setup_logging(self):
        """Configura logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def setup_advanced_patterns(self):
        """Configura padrões para recursos avançados"""
        
        # Decorator patterns
        self.decorator_patterns = {
            'singledispatch': r'@singledispatch',
            'singledispatchmethod': r'@singledispatchmethod',
            'property': r'@property',
            'cached_property': r'@cached_property',
            'lru_cache': r'@lru_cache',
            'dataclass': r'@dataclass',
            'contextmanager': r'@contextmanager',
            'asynccontextmanager': r'@asynccontextmanager'
        }
        
        # Type hint patterns
        self.type_hint_patterns = {
            'union': r'Union\[.*?\]|.*?\s*\|\s*.*?',
            'generic': r'(List|Dict|Set|Tuple|Optional)\[.*?\]',
            'literal': r'Literal\[.*?\]',
            'final': r'Final\[.*?\]',
            'typed_dict': r'class.*?\(TypedDict\)',
            'protocol': r'class.*?\(Protocol\)'
        }
        
        # Advanced syntax patterns
        self.syntax_patterns = {
            'walrus': r':=',
            'f_string_expr': r'f["\'].*?{.*?=.*?}.*?["\']',
            'positional_only': r'def\s+\w+\([^)]*?/[^)]*?\)',
            'keyword_only': r'def\s+\w+\([^)]*?\*[^)]*?\)',
            'yield_from': r'yield\s+from',
            'async_comprehension': r'\[.*?async\s+for.*?\]|\{.*?async\s+for.*?\}|\(.*?async\s+for.*?\)',
            'match_statement': r'match\s+.*?:',
            'case_pattern': r'case\s+.*?:'
        }
        
    def analyze_file(self, file_path: str) -> List[AdvancedFeatureUsage]:
        """Analisa recursos avançados em um arquivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            features = []
            
            # 1. AST analysis for structural features
            ast_features = self._analyze_ast_advanced(source_code, file_path)
            features.extend(ast_features)
            
            # 2. Regex analysis for syntax patterns
            regex_features = self._analyze_regex_patterns(source_code, file_path)
            features.extend(regex_features)
            
            # 3. Token analysis for special syntax
            token_features = self._analyze_tokens_advanced(source_code, file_path)
            features.extend(token_features)
            
            # 4. Import analysis
            import_features = self._analyze_imports_advanced(source_code, file_path)
            features.extend(import_features)
            
            # 5. Type hint analysis
            type_features = self._analyze_type_hints_advanced(source_code, file_path)
            features.extend(type_features)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error analyzing advanced features in {file_path}: {e}")
            return []
    
    def _analyze_ast_advanced(self, source_code: str, file_path: str) -> List[AdvancedFeatureUsage]:
        """Análise AST para recursos avançados"""
        features = []
        
        try:
            tree = ast.parse(source_code)
            lines = source_code.splitlines()
            
            class AdvancedASTVisitor(ast.NodeVisitor):
                def __init__(self, analyzer):
                    self.analyzer = analyzer
                    
                def visit_FunctionDef(self, node):
                    # Positional-only parameters
                    if hasattr(node.args, 'posonlyargs') and node.args.posonlyargs:
                        feature = AdvancedFeatureUsage(
                            feature_type=AdvancedPythonFeature.POSITIONAL_ONLY,
                            name=f"{node.name}_positional_only",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_offset=node.col_offset,
                            end_line_number=getattr(node, 'end_lineno', None),
                            source_code=self._get_source(lines, node),
                            context="function_definition",
                            min_python_version="3.8",
                            feature_details={"args": [arg.arg for arg in node.args.posonlyargs]}
                        )
                        features.append(feature)
                    
                    # Keyword-only parameters
                    if node.args.kwonlyargs:
                        feature = AdvancedFeatureUsage(
                            feature_type=AdvancedPythonFeature.KEYWORD_ONLY,
                            name=f"{node.name}_keyword_only",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_offset=node.col_offset,
                            end_line_number=getattr(node, 'end_lineno', None),
                            source_code=self._get_source(lines, node),
                            context="function_definition",
                            feature_details={"args": [arg.arg for arg in node.args.kwonlyargs]}
                        )
                        features.append(feature)
                    
                    # Analyze decorators
                    for decorator in node.decorator_list:
                        dec_feature = self._analyze_decorator(decorator, lines, file_path)
                        if dec_feature:
                            features.append(dec_feature)
                    
                    self.generic_visit(node)
                    
                def visit_AsyncFunctionDef(self, node):
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.ASYNC_FUNCTION,
                        name=node.name,
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        end_line_number=getattr(node, 'end_lineno', None),
                        source_code=self._get_source(lines, node),
                        context="async_function",
                        min_python_version="3.5"
                    )
                    features.append(feature)
                    self.generic_visit(node)
                    
                def visit_ClassDef(self, node):
                    # Metaclass detection
                    for keyword in node.keywords:
                        if keyword.arg == 'metaclass':
                            feature = AdvancedFeatureUsage(
                                feature_type=AdvancedPythonFeature.METACLASS,
                                name=f"{node.name}_metaclass",
                                file_path=file_path,
                                line_number=node.lineno,
                                column_offset=node.col_offset,
                                end_line_number=getattr(node, 'end_lineno', None),
                                source_code=self._get_source(lines, node),
                                context="class_definition",
                                maintenance_risk="high",
                                complexity_impact=3
                            )
                            features.append(feature)
                    
                    # Check for dataclass, TypedDict, Protocol
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            if base.id in ['TypedDict']:
                                feature = AdvancedFeatureUsage(
                                    feature_type=AdvancedPythonFeature.TYPED_DICT,
                                    name=node.name,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    column_offset=node.col_offset,
                                    end_line_number=getattr(node, 'end_lineno', None),
                                    source_code=self._get_source(lines, node),
                                    context="typed_dict_class",
                                    min_python_version="3.8",
                                    requires_typing_extensions=True
                                )
                                features.append(feature)
                            elif base.id in ['Protocol']:
                                feature = AdvancedFeatureUsage(
                                    feature_type=AdvancedPythonFeature.PROTOCOL,
                                    name=node.name,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    column_offset=node.col_offset,
                                    end_line_number=getattr(node, 'end_lineno', None),
                                    source_code=self._get_source(lines, node),
                                    context="protocol_class",
                                    min_python_version="3.8",
                                    requires_typing_extensions=True
                                )
                                features.append(feature)
                    
                    self.generic_visit(node)
                    
                def visit_NamedExpr(self, node):  # Walrus operator
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.WALRUS_OPERATOR,
                        name=f"walrus_{node.lineno}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        end_line_number=getattr(node, 'end_lineno', None),
                        source_code=self._get_source(lines, node),
                        context="named_expression",
                        min_python_version="3.8",
                        performance_impact="positive"
                    )
                    features.append(feature)
                    self.generic_visit(node)
                    
                def visit_Await(self, node):
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.AWAIT_EXPRESSION,
                        name=f"await_{node.lineno}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        end_line_number=getattr(node, 'end_lineno', None),
                        source_code=self._get_source(lines, node),
                        context="await_expression",
                        min_python_version="3.5"
                    )
                    features.append(feature)
                    self.generic_visit(node)
                    
                def visit_AsyncWith(self, node):
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.ASYNC_WITH,
                        name=f"async_with_{node.lineno}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        end_line_number=getattr(node, 'end_lineno', None),
                        source_code=self._get_source(lines, node),
                        context="async_context_manager",
                        min_python_version="3.5"
                    )
                    features.append(feature)
                    self.generic_visit(node)
                    
                def visit_AsyncFor(self, node):
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.ASYNC_FOR,
                        name=f"async_for_{node.lineno}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        end_line_number=getattr(node, 'end_lineno', None),
                        source_code=self._get_source(lines, node),
                        context="async_for_loop",
                        min_python_version="3.6"
                    )
                    features.append(feature)
                    self.generic_visit(node)
                    
                def visit_YieldFrom(self, node):
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.YIELD_FROM,
                        name=f"yield_from_{node.lineno}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        end_line_number=getattr(node, 'end_lineno', None),
                        source_code=self._get_source(lines, node),
                        context="generator",
                        min_python_version="3.3",
                        performance_impact="positive"
                    )
                    features.append(feature)
                    self.generic_visit(node)
                    
                def visit_AnnAssign(self, node):  # Variable annotation
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.VARIABLE_ANNOTATION,
                        name=f"annotation_{node.lineno}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        end_line_number=getattr(node, 'end_lineno', None),
                        source_code=self._get_source(lines, node),
                        context="variable_annotation",
                        min_python_version="3.6"
                    )
                    features.append(feature)
                    self.generic_visit(node)
                    
                def visit_MatMult(self, node):  # @ operator
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.MATRIX_MULTIPLICATION,
                        name=f"matmult_{node.lineno}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_offset=node.col_offset,
                        end_line_number=getattr(node, 'end_lineno', None),
                        source_code=self._get_source(lines, node),
                        context="matrix_operation",
                        min_python_version="3.5"
                    )
                    features.append(feature)
                    self.generic_visit(node)
                    
                # Python 3.10+ features
                if hasattr(ast, 'Match'):
                    def visit_Match(self, node):
                        feature = AdvancedFeatureUsage(
                            feature_type=AdvancedPythonFeature.MATCH_STATEMENT,
                            name=f"match_{node.lineno}",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_offset=node.col_offset,
                            end_line_number=getattr(node, 'end_lineno', None),
                            source_code=self._get_source(lines, node),
                            context="pattern_matching",
                            min_python_version="3.10",
                            complexity_impact=2
                        )
                        features.append(feature)
                        self.generic_visit(node)
                
                def _get_source(self, lines, node):
                    """Get source code for node"""
                    try:
                        if hasattr(node, 'lineno'):
                            start = node.lineno - 1
                            end = getattr(node, 'end_lineno', node.lineno)
                            return '\n'.join(lines[start:end])
                    except:
                        pass
                    return ""
                    
                def _analyze_decorator(self, decorator, lines, file_path):
                    """Analyze specific decorator"""
                    decorator_name = self._get_decorator_name(decorator)
                    
                    feature_map = {
                        'singledispatch': AdvancedPythonFeature.SINGLEDISPATCH,
                        'singledispatchmethod': AdvancedPythonFeature.SINGLEDISPATCH_METHOD,
                        'property': AdvancedPythonFeature.PROPERTY_DECORATOR,
                        'cached_property': AdvancedPythonFeature.CACHED_PROPERTY,
                        'lru_cache': AdvancedPythonFeature.LRU_CACHE,
                        'dataclass': AdvancedPythonFeature.DATACLASS,
                        'contextmanager': AdvancedPythonFeature.CONTEXTLIB_MANAGER,
                        'asynccontextmanager': AdvancedPythonFeature.ASYNC_CONTEXT_MANAGER
                    }
                    
                    if decorator_name in feature_map:
                        return AdvancedFeatureUsage(
                            feature_type=feature_map[decorator_name],
                            name=decorator_name,
                            file_path=file_path,
                            line_number=decorator.lineno,
                            column_offset=decorator.col_offset,
                            end_line_number=getattr(decorator, 'end_lineno', None),
                            source_code=self._get_source(lines, decorator),
                            context="decorator",
                            feature_details={"decorator": decorator_name}
                        )
                    return None
                    
                def _get_decorator_name(self, decorator):
                    """Get decorator name"""
                    if isinstance(decorator, ast.Name):
                        return decorator.id
                    elif isinstance(decorator, ast.Attribute):
                        return decorator.attr
                    elif isinstance(decorator, ast.Call):
                        return self._get_decorator_name(decorator.func)
                    return "unknown"
            
            visitor = AdvancedASTVisitor(self)
            visitor.visit(tree)
            
        except Exception as e:
            self.logger.error(f"AST analysis error: {e}")
            
        return features
    
    def _analyze_regex_patterns(self, source_code: str, file_path: str) -> List[AdvancedFeatureUsage]:
        """Análise baseada em regex para padrões sintáticos"""
        features = []
        lines = source_code.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # F-string expressions
            if re.search(self.syntax_patterns['f_string_expr'], line):
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.F_STRING_EXPRESSION,
                    name=f"f_string_expr_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line.strip(),
                    context="f_string_expression",
                    min_python_version="3.8"
                )
                features.append(feature)
            
            # Walrus operator
            if ':=' in line:
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.WALRUS_OPERATOR,
                    name=f"walrus_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=line.find(':='),
                    end_line_number=line_num,
                    source_code=line.strip(),
                    context="walrus_operator",
                    min_python_version="3.8"
                )
                features.append(feature)
        
        return features
    
    def _analyze_tokens_advanced(self, source_code: str, file_path: str) -> List[AdvancedFeatureUsage]:
        """Análise de tokens para sintaxe especial"""
        features = []
        
        try:
            tokens = list(tokenize.generate_tokens(iter(source_code.splitlines()).__next__))
            
            for i, token in enumerate(tokens):
                # Matrix multiplication operator @
                if token.type == tokenize.OP and token.string == '@':
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.MATRIX_MULTIPLICATION,
                        name=f"matmult_{token.start[0]}",
                        file_path=file_path,
                        line_number=token.start[0],
                        column_offset=token.start[1],
                        end_line_number=token.end[0],
                        source_code=token.string,
                        context="matrix_operator",
                        min_python_version="3.5"
                    )
                    features.append(feature)
                
                # Ellipsis
                elif token.type == tokenize.OP and token.string == '...':
                    feature = AdvancedFeatureUsage(
                        feature_type=AdvancedPythonFeature.ELLIPSIS,
                        name=f"ellipsis_{token.start[0]}",
                        file_path=file_path,
                        line_number=token.start[0],
                        column_offset=token.start[1],
                        end_line_number=token.end[0],
                        source_code=token.string,
                        context="ellipsis",
                        min_python_version="3.0"
                    )
                    features.append(feature)
                
        except Exception as e:
            self.logger.error(f"Token analysis error: {e}")
        
        return features
    
    def _analyze_imports_advanced(self, source_code: str, file_path: str) -> List[AdvancedFeatureUsage]:
        """Análise de imports avançados"""
        features = []
        lines = source_code.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Star imports
            if re.match(r'from\s+\w+.*\s+import\s+\*', line):
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.STAR_IMPORT,
                    name=f"star_import_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line,
                    context="star_import",
                    maintenance_risk="high"
                )
                features.append(feature)
            
            # Relative imports
            elif re.match(r'from\s+\.', line):
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.RELATIVE_IMPORT,
                    name=f"relative_import_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line,
                    context="relative_import"
                )
                features.append(feature)
            
            # Dynamic imports
            elif 'importlib' in line and 'import_module' in line:
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.DYNAMIC_IMPORT,
                    name=f"dynamic_import_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line,
                    context="dynamic_import",
                    complexity_impact=2
                )
                features.append(feature)
        
        return features
    
    def _analyze_type_hints_advanced(self, source_code: str, file_path: str) -> List[AdvancedFeatureUsage]:
        """Análise de type hints avançados"""
        features = []
        lines = source_code.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Union types (old style)
            if re.search(r'Union\[.*?\]', line):
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.UNION_TYPE,
                    name=f"union_type_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line.strip(),
                    context="union_type",
                    min_python_version="3.5"
                )
                features.append(feature)
            
            # Union types (new style Python 3.10+)
            elif re.search(r'\w+\s*\|\s*\w+', line) and not re.search(r'["\'].*\|.*["\']', line):
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.UNION_TYPE,
                    name=f"union_operator_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line.strip(),
                    context="union_operator",
                    min_python_version="3.10"
                )
                features.append(feature)
            
            # Generic types
            elif re.search(r'(List|Dict|Set|Tuple|Optional)\[.*?\]', line):
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.GENERIC_TYPE,
                    name=f"generic_type_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line.strip(),
                    context="generic_type",
                    min_python_version="3.5"
                )
                features.append(feature)
            
            # Literal types
            elif re.search(r'Literal\[.*?\]', line):
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.LITERAL_TYPE,
                    name=f"literal_type_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line.strip(),
                    context="literal_type",
                    min_python_version="3.8",
                    requires_typing_extensions=True
                )
                features.append(feature)
            
            # Final types
            elif re.search(r'Final\[.*?\]', line):
                feature = AdvancedFeatureUsage(
                    feature_type=AdvancedPythonFeature.FINAL_TYPE,
                    name=f"final_type_{line_num}",
                    file_path=file_path,
                    line_number=line_num,
                    column_offset=0,
                    end_line_number=line_num,
                    source_code=line.strip(),
                    context="final_type",
                    min_python_version="3.8",
                    requires_typing_extensions=True
                )
                features.append(feature)
        
        return features
    
    def generate_compatibility_report(self, features: List[AdvancedFeatureUsage]) -> Dict[str, Any]:
        """Gera relatório de compatibilidade"""
        version_usage = {}
        typing_extensions_needed = False
        
        for feature in features:
            version = feature.min_python_version
            if version not in version_usage:
                version_usage[version] = []
            version_usage[version].append(feature.feature_type.value)
            
            if feature.requires_typing_extensions:
                typing_extensions_needed = True
        
        # Determine minimum Python version needed
        versions = list(version_usage.keys())
        min_version = max(versions) if versions else "3.6"
        
        return {
            "minimum_python_version": min_version,
            "requires_typing_extensions": typing_extensions_needed,
            "version_breakdown": version_usage,
            "total_advanced_features": len(features),
            "high_maintenance_risk": len([f for f in features if f.maintenance_risk == "high"]),
            "performance_positive": len([f for f in features if f.performance_impact == "positive"]),
            "performance_negative": len([f for f in features if f.performance_impact == "negative"])
        }
    
    def export_analysis(self, features: List[AdvancedFeatureUsage], output_path: str):
        """Exporta análise para arquivo JSON"""
        
        # Convert features to dict
        features_dict = [asdict(feature) for feature in features]
        
        # Convert enums to strings
        for feature_dict in features_dict:
            if 'feature_type' in feature_dict:
                feature_dict['feature_type'] = feature_dict['feature_type'].value
        
        # Generate compatibility report
        compatibility = self.generate_compatibility_report(features)
        
        result = {
            "analysis_timestamp": str(datetime.now()),
            "total_features": len(features),
            "features": features_dict,
            "compatibility_report": compatibility,
            "feature_summary": self._generate_feature_summary(features)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Advanced features analysis exported to {output_path}")
    
    def _generate_feature_summary(self, features: List[AdvancedFeatureUsage]) -> Dict[str, int]:
        """Gera resumo de recursos por tipo"""
        summary = {}
        for feature in features:
            feature_type = feature.feature_type.value
            summary[feature_type] = summary.get(feature_type, 0) + 1
        return summary


def main():
    """Função principal para teste"""
    analyzer = AdvancedPythonFeaturesAnalyzer()
    
    # Test with current file
    current_file = __file__
    features = analyzer.analyze_file(current_file)
    
    print(f"Found {len(features)} advanced Python features in {current_file}")
    
    for feature in features[:10]:  # Show first 10
        print(f"- {feature.feature_type.value}: {feature.name} at line {feature.line_number}")
    
    # Generate compatibility report
    compatibility = analyzer.generate_compatibility_report(features)
    print(f"\nCompatibility Report:")
    print(f"Minimum Python version: {compatibility['minimum_python_version']}")
    print(f"Requires typing_extensions: {compatibility['requires_typing_extensions']}")


if __name__ == "__main__":
    main()
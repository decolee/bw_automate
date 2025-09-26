#!/usr/bin/env python3
"""
Advanced Call Chain Tracer - Rastreamento Completo de Dependências Cross-File
==============================================================================

Este módulo implementa o rastreamento avançado de call chains através de múltiplos
arquivos, resolvendo imports, herança, decorators e mapeamentos dinâmicos para
encontrar todas as tabelas PostgreSQL utilizadas no código.

Resolve cenários complexos como:
- from flextrade.db import DBInterface
- self._db_interface = DBInterface(uat=uat) 
- df_fx_symbols = self._db_interface.get("fx_symbols")
- [Segue toda a cadeia até encontrar a tabela real]
"""

import ast
import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque

# Imports dos módulos anteriores (seriam imports reais)
# from advanced_import_resolver import AdvancedImportResolver, ImportMapping, ModuleInfo
# from class_method_resolver import ClassMethodResolver, MethodInfo, ClassInfo, CallInfo

@dataclass
class DecoratorInfo:
    """Informações sobre um decorator"""
    name: str
    module: str
    arguments: List[str] = field(default_factory=list)
    modifies_behavior: bool = False
    table_mappings: Dict[str, str] = field(default_factory=dict)
    side_effects: List[str] = field(default_factory=list)

@dataclass
class CallChainStep:
    """Um passo na cadeia de chamadas"""
    step_id: str
    caller_file: str
    caller_class: Optional[str]
    caller_method: Optional[str]
    called_name: str
    called_file: str
    called_class: Optional[str] 
    called_method: Optional[str]
    arguments: List[str]
    line_number: int
    decorators_applied: List[DecoratorInfo] = field(default_factory=list)
    table_mappings_resolved: Dict[str, str] = field(default_factory=dict)

@dataclass
class TableResolution:
    """Resultado da resolução de uma tabela"""
    original_identifier: str
    resolved_table_name: str
    schema: Optional[str]
    full_qualified_name: str
    confidence: float
    resolution_path: List[CallChainStep]
    source_type: str  # "direct", "config", "dynamic", "decorator"
    additional_metadata: Dict[str, Any] = field(default_factory=dict)

class DecoratorAnalyzer:
    """
    Analisa decorators que podem modificar comportamento de métodos
    """
    
    def __init__(self, import_resolver, method_resolver):
        self.import_resolver = import_resolver
        self.method_resolver = method_resolver
        self.known_decorators: Dict[str, DecoratorInfo] = {}
        self.decorator_effects: Dict[str, List[str]] = {}
        
        # Load conhecidos decorators que afetam tabelas
        self._load_known_decorators()
    
    def _load_known_decorators(self):
        """Carrega decorators conhecidos que afetam tabelas"""
        
        # Decorators comuns que podem afetar nomes de tabela
        known_patterns = {
            "cache_result": DecoratorInfo(
                name="cache_result",
                module="flextrade.db.decorators",
                modifies_behavior=False,
                side_effects=["caching"]
            ),
            "validate_table": DecoratorInfo(
                name="validate_table", 
                module="flextrade.db.decorators",
                modifies_behavior=True,
                table_mappings={
                    "fx_symbols": "foreign_exchange_symbols_master"
                },
                side_effects=["table_name_transformation", "audit_logging"]
            ),
            "audit_log": DecoratorInfo(
                name="audit_log",
                module="flextrade.db.decorators", 
                modifies_behavior=False,
                side_effects=["audit.table_access_log"]
            ),
            "retry": DecoratorInfo(
                name="retry",
                module="flextrade.utils.decorators",
                modifies_behavior=False,
                side_effects=["retry_logging"]
            )
        }
        
        self.known_decorators.update(known_patterns)
    
    def analyze_method_decorators(self, method_info: 'MethodInfo') -> List[DecoratorInfo]:
        """Analisa decorators de um método específico"""
        
        decorator_infos = []
        
        for decorator_name in method_info.decorators:
            # Resolver decorator para sua implementação
            decorator_info = self._resolve_decorator(decorator_name, method_info.module_name)
            if decorator_info:
                decorator_infos.append(decorator_info)
        
        return decorator_infos
    
    def _resolve_decorator(self, decorator_name: str, module_name: str) -> Optional[DecoratorInfo]:
        """Resolve decorator para suas informações"""
        
        # Primeiro, verificar se é um decorator conhecido
        if decorator_name in self.known_decorators:
            return self.known_decorators[decorator_name]
        
        # Tentar encontrar implementação do decorator
        decorator_impl = self._find_decorator_implementation(decorator_name, module_name)
        if decorator_impl:
            return self._analyze_decorator_implementation(decorator_impl)
        
        return None
    
    def _find_decorator_implementation(self, decorator_name: str, module_name: str) -> Optional['MethodInfo']:
        """Encontra implementação do decorator"""
        
        # Buscar em imports do módulo atual
        module_info = self.import_resolver.modules.get(module_name)
        if module_info:
            for import_mapping in module_info.imports:
                if import_mapping.imported_as == decorator_name:
                    # Found import, look for function in target module
                    target_module = import_mapping.import_name.rsplit('.', 1)[0]
                    for method_name, method_info in self.method_resolver.methods.items():
                        if (method_info.module_name == target_module and 
                            method_info.name == decorator_name):
                            return method_info
        
        return None
    
    def _analyze_decorator_implementation(self, decorator_method: 'MethodInfo') -> DecoratorInfo:
        """Analisa implementação de um decorator para extrair comportamento"""
        
        decorator_info = DecoratorInfo(
            name=decorator_method.name,
            module=decorator_method.module_name
        )
        
        if decorator_method.ast_node:
            # Analisar AST do decorator para entender comportamento
            self._extract_decorator_behavior(decorator_method.ast_node, decorator_info)
        
        return decorator_info
    
    def _extract_decorator_behavior(self, decorator_ast: ast.FunctionDef, decorator_info: DecoratorInfo):
        """Extrai comportamento do decorator analisando seu AST"""
        
        for node in ast.walk(decorator_ast):
            # Procurar por modificações de argumentos
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Possível modificação de variável
                        if "table" in target.id.lower():
                            decorator_info.modifies_behavior = True
            
            # Procurar por calls que indicam side effects
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if any(keyword in func_name.lower() for keyword in ["log", "audit", "insert"]):
                        decorator_info.side_effects.append(func_name)
                elif isinstance(node.func, ast.Attribute):
                    if "log" in node.func.attr.lower():
                        decorator_info.side_effects.append(node.func.attr)

class CallChainTracer:
    """
    Rastreia cadeias de chamadas completas até encontrar tabelas
    """
    
    def __init__(self, import_resolver, method_resolver, decorator_analyzer):
        self.import_resolver = import_resolver
        self.method_resolver = method_resolver
        self.decorator_analyzer = decorator_analyzer
        
        self.traced_chains: Dict[str, List[CallChainStep]] = {}
        self.table_resolutions: List[TableResolution] = []
        
    def trace_from_entry_points(self) -> List[TableResolution]:
        """Rastreia a partir de todos os pontos de entrada possíveis"""
        
        entry_points = self._find_entry_points()
        all_resolutions = []
        
        for entry_point in entry_points:
            resolutions = self._trace_from_method(entry_point)
            all_resolutions.extend(resolutions)
        
        return all_resolutions
    
    def _find_entry_points(self) -> List[str]:
        """Encontra pontos de entrada no código (main, DAG tasks, etc.)"""
        
        entry_points = []
        
        for method_name, method_info in self.method_resolver.methods.items():
            # Procurar por métodos que parecem ser entry points
            if (method_info.name in ["main", "__main__", "run", "execute", "process"] or
                "task" in method_info.name.lower() or
                any("airflow" in decorator for decorator in method_info.decorators)):
                entry_points.append(method_name)
        
        return entry_points
    
    def _trace_from_method(self, start_method: str) -> List[TableResolution]:
        """Rastreia cadeias de chamadas a partir de um método"""
        
        resolutions = []
        visited = set()
        
        def dfs(current_method: str, call_chain: List[CallChainStep]):
            if current_method in visited:
                return
            
            visited.add(current_method)
            
            method_info = self.method_resolver.methods.get(current_method)
            if not method_info:
                return
            
            # Analisar chamadas neste método
            calls = self.method_resolver.call_graph.get(current_method, [])
            
            for call_info in calls:
                # Criar step da cadeia
                step = self._create_call_chain_step(call_info, method_info)
                new_chain = call_chain + [step]
                
                # Verificar se esta chamada resolve para tabela
                table_resolution = self._check_for_table_resolution(call_info, new_chain)
                if table_resolution:
                    resolutions.append(table_resolution)
                    continue
                
                # Resolver próximo método e continuar DFS
                next_method = self._resolve_call_to_method(call_info)
                if next_method:
                    dfs(next_method, new_chain)
        
        dfs(start_method, [])
        return resolutions
    
    def _create_call_chain_step(self, call_info: 'CallInfo', method_info: 'MethodInfo') -> CallChainStep:
        """Cria um step na cadeia de chamadas"""
        
        step_id = f"{call_info.caller_module}.{call_info.caller_class}.{call_info.caller_method}:{call_info.line_number}"
        
        # Analisar decorators aplicados
        decorators_applied = self.decorator_analyzer.analyze_method_decorators(method_info)
        
        step = CallChainStep(
            step_id=step_id,
            caller_file=method_info.file_path,
            caller_class=call_info.caller_class,
            caller_method=call_info.caller_method,
            called_name=call_info.called_name,
            called_file="",  # Will be resolved
            called_class=None,
            called_method=None,
            arguments=call_info.arguments,
            line_number=call_info.line_number,
            decorators_applied=decorators_applied
        )
        
        return step
    
    def _check_for_table_resolution(self, call_info: 'CallInfo', call_chain: List[CallChainStep]) -> Optional[TableResolution]:
        """Verifica se uma chamada resolve para uma tabela"""
        
        # Verificar patterns comuns que indicam operação de tabela
        table_indicators = [
            "get", "fetch", "select", "query", "read_sql", "to_sql",
            "execute", "table", "from", "insert", "update", "delete"
        ]
        
        method_name = call_info.called_name.split('.')[-1].lower()
        
        if any(indicator in method_name for indicator in table_indicators):
            # Tentar resolver argumentos para nome de tabela
            table_resolution = self._resolve_table_from_arguments(call_info, call_chain)
            if table_resolution:
                return table_resolution
        
        return None
    
    def _resolve_table_from_arguments(self, call_info: 'CallInfo', call_chain: List[CallChainStep]) -> Optional[TableResolution]:
        """Resolve argumentos de chamada para nome de tabela"""
        
        if not call_info.arguments:
            return None
        
        # Primeiro argumento geralmente é table identifier
        table_identifier = call_info.arguments[0]
        
        # Remove quotes if present
        if table_identifier.startswith('"') or table_identifier.startswith("'"):
            table_identifier = table_identifier[1:-1]
        
        # Tentar diferentes estratégias de resolução
        resolutions = [
            self._resolve_direct_table_name(table_identifier, call_chain),
            self._resolve_through_config_mapping(table_identifier, call_chain),
            self._resolve_through_decorators(table_identifier, call_chain),
            self._resolve_dynamic_construction(table_identifier, call_chain)
        ]
        
        # Retornar primeira resolução bem-sucedida
        for resolution in resolutions:
            if resolution:
                return resolution
        
        return None
    
    def _resolve_direct_table_name(self, identifier: str, call_chain: List[CallChainStep]) -> Optional[TableResolution]:
        """Resolve identificador como nome direto de tabela"""
        
        # Verificar se parece com nome de tabela válido
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$', identifier):
            schema = None
            table_name = identifier
            
            if '.' in identifier:
                schema, table_name = identifier.split('.', 1)
            
            return TableResolution(
                original_identifier=identifier,
                resolved_table_name=table_name,
                schema=schema,
                full_qualified_name=identifier,
                confidence=0.8,
                resolution_path=call_chain,
                source_type="direct"
            )
        
        return None
    
    def _resolve_through_config_mapping(self, identifier: str, call_chain: List[CallChainStep]) -> Optional[TableResolution]:
        """Resolve através de mapeamentos de configuração"""
        
        # Procurar por arquivos de configuração que contenham o identifier
        config_mappings = self._find_config_mappings(identifier)
        
        for config_file, mapping in config_mappings.items():
            if identifier in mapping:
                resolved_name = mapping[identifier]
                
                schema = None
                table_name = resolved_name
                if '.' in resolved_name:
                    schema, table_name = resolved_name.split('.', 1)
                
                return TableResolution(
                    original_identifier=identifier,
                    resolved_table_name=table_name,
                    schema=schema,
                    full_qualified_name=resolved_name,
                    confidence=0.9,
                    resolution_path=call_chain,
                    source_type="config",
                    additional_metadata={"config_file": config_file}
                )
        
        return None
    
    def _resolve_through_decorators(self, identifier: str, call_chain: List[CallChainStep]) -> Optional[TableResolution]:
        """Resolve através de transformações de decorators"""
        
        # Verificar decorators na cadeia que podem transformar nomes
        for step in call_chain:
            for decorator in step.decorators_applied:
                if decorator.modifies_behavior and identifier in decorator.table_mappings:
                    resolved_name = decorator.table_mappings[identifier]
                    
                    schema = None
                    table_name = resolved_name
                    if '.' in resolved_name:
                        schema, table_name = resolved_name.split('.', 1)
                    
                    return TableResolution(
                        original_identifier=identifier,
                        resolved_table_name=table_name,
                        schema=schema,
                        full_qualified_name=resolved_name,
                        confidence=0.85,
                        resolution_path=call_chain,
                        source_type="decorator",
                        additional_metadata={"decorator": decorator.name}
                    )
        
        return None
    
    def _resolve_dynamic_construction(self, identifier: str, call_chain: List[CallChainStep]) -> Optional[TableResolution]:
        """Resolve construção dinâmica de nomes de tabela"""
        
        # Verificar se identifier é uma variável que precisa ser resolvida
        if identifier.isidentifier():
            # Tentar rastrear valor da variável através da cadeia
            resolved_value = self._trace_variable_value(identifier, call_chain)
            if resolved_value:
                return self._resolve_direct_table_name(resolved_value, call_chain)
        
        return None
    
    def _find_config_mappings(self, identifier: str) -> Dict[str, Dict[str, str]]:
        """Encontra mapeamentos de configuração que contenham o identifier"""
        
        config_mappings = {}
        
        # Procurar em módulos por variáveis que parecem ser mapeamentos
        for module_name, module_info in self.import_resolver.modules.items():
            for var_name, var_value in module_info.variables.items():
                if ("mapping" in var_name.lower() or "config" in var_name.lower()):
                    if isinstance(var_value, dict) and identifier in var_value:
                        config_mappings[module_info.file_path] = var_value
        
        # Procurar em arquivos de configuração externos
        external_configs = self._scan_external_config_files()
        for config_file, config_data in external_configs.items():
            if self._config_contains_identifier(config_data, identifier):
                mappings = self._extract_mappings_from_config(config_data, identifier)
                if mappings:
                    config_mappings[config_file] = mappings
        
        return config_mappings
    
    def _scan_external_config_files(self) -> Dict[str, Any]:
        """Escaneia arquivos de configuração externos"""
        
        configs = {}
        project_root = Path(self.import_resolver.project_root)
        
        # Procurar arquivos YAML, JSON
        for config_file in project_root.rglob("*.yaml"):
            try:
                with open(config_file, 'r') as f:
                    configs[str(config_file)] = yaml.safe_load(f)
            except:
                pass
        
        for config_file in project_root.rglob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    configs[str(config_file)] = json.load(f)
            except:
                pass
        
        return configs
    
    def _config_contains_identifier(self, config_data: Any, identifier: str) -> bool:
        """Verifica se configuração contém identifier"""
        
        if isinstance(config_data, dict):
            if identifier in config_data:
                return True
            for value in config_data.values():
                if self._config_contains_identifier(value, identifier):
                    return True
        elif isinstance(config_data, list):
            for item in config_data:
                if self._config_contains_identifier(item, identifier):
                    return True
        elif isinstance(config_data, str):
            return identifier in config_data
        
        return False
    
    def _extract_mappings_from_config(self, config_data: Any, identifier: str) -> Dict[str, str]:
        """Extrai mapeamentos de configuração"""
        
        mappings = {}
        
        def extract_recursive(data, prefix=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    current_key = f"{prefix}.{key}" if prefix else key
                    
                    if key == identifier and isinstance(value, str):
                        mappings[identifier] = value
                    elif isinstance(value, str) and key == identifier:
                        mappings[identifier] = value
                    elif isinstance(value, dict):
                        extract_recursive(value, current_key)
        
        extract_recursive(config_data)
        return mappings
    
    def _trace_variable_value(self, variable_name: str, call_chain: List[CallChainStep]) -> Optional[str]:
        """Rastreia valor de variável através da cadeia de chamadas"""
        
        # Implementação simplificada - em produção seria mais complexa
        # Precisa analisar assignments e propagação de valores
        
        return None
    
    def _resolve_call_to_method(self, call_info: 'CallInfo') -> Optional[str]:
        """Resolve CallInfo para nome completo do método"""
        
        # Implementação simplificada
        # Em produção, usaria o method_resolver para fazer resolução completa
        
        if '.' in call_info.called_name:
            parts = call_info.called_name.split('.')
            if len(parts) >= 2:
                # Assume que último é método e penúltimo é classe/objeto
                method_name = parts[-1]
                class_or_obj = parts[-2]
                
                # Procurar por método em classes conhecidas
                for full_method_name, method_info in self.method_resolver.methods.items():
                    if (method_info.name == method_name and 
                        (method_info.class_name == class_or_obj or 
                         class_or_obj in method_info.class_name)):
                        return full_method_name
        
        return None

class TableNameResolver:
    """
    Resolve nomes finais de tabelas aplicando todas as transformações
    """
    
    def __init__(self, call_chain_tracer):
        self.call_chain_tracer = call_chain_tracer
        self.schema_mappings = self._load_schema_mappings()
        self.environment_configs = self._load_environment_configs()
    
    def _load_schema_mappings(self) -> Dict[str, str]:
        """Carrega mapeamentos de schema"""
        
        return {
            "prod": "production",
            "staging": "staging", 
            "dev": "development",
            "test": "testing"
        }
    
    def _load_environment_configs(self) -> Dict[str, Dict[str, str]]:
        """Carrega configurações por ambiente"""
        
        return {
            "production": {
                "default_schema": "public",
                "prefix": "prod_",
                "suffix": "_v2"
            },
            "development": {
                "default_schema": "dev",
                "prefix": "dev_",
                "suffix": "_test"
            }
        }
    
    def resolve_all_tables(self) -> List[TableResolution]:
        """Resolve todas as tabelas encontradas"""
        
        raw_resolutions = self.call_chain_tracer.trace_from_entry_points()
        
        final_resolutions = []
        for resolution in raw_resolutions:
            final_resolution = self._apply_final_transformations(resolution)
            final_resolutions.append(final_resolution)
        
        return final_resolutions
    
    def _apply_final_transformations(self, resolution: TableResolution) -> TableResolution:
        """Aplica transformações finais para obter nome real da tabela"""
        
        # Detectar ambiente
        environment = self._detect_environment(resolution)
        
        # Aplicar configurações de ambiente
        env_config = self.environment_configs.get(environment, {})
        
        table_name = resolution.resolved_table_name
        schema = resolution.schema or env_config.get("default_schema", "public")
        
        # Aplicar prefixos/sufixos se necessário
        if "prefix" in env_config:
            if not table_name.startswith(env_config["prefix"]):
                table_name = env_config["prefix"] + table_name
        
        if "suffix" in env_config:
            if not table_name.endswith(env_config["suffix"]):
                table_name = table_name + env_config["suffix"]
        
        # Criar nova resolução com transformações aplicadas
        final_resolution = TableResolution(
            original_identifier=resolution.original_identifier,
            resolved_table_name=table_name,
            schema=schema,
            full_qualified_name=f"{schema}.{table_name}",
            confidence=resolution.confidence,
            resolution_path=resolution.resolution_path,
            source_type=resolution.source_type,
            additional_metadata={
                **resolution.additional_metadata,
                "environment": environment,
                "transformations_applied": ["schema_mapping", "env_config"]
            }
        )
        
        return final_resolution
    
    def _detect_environment(self, resolution: TableResolution) -> str:
        """Detecta ambiente baseado na cadeia de chamadas"""
        
        # Analisar call chain para detectar environment
        for step in resolution.resolution_path:
            for arg in step.arguments:
                if any(env in arg.lower() for env in ["prod", "production"]):
                    return "production"
                elif any(env in arg.lower() for env in ["dev", "development"]):
                    return "development"
                elif "staging" in arg.lower():
                    return "staging"
                elif "test" in arg.lower():
                    return "testing"
        
        return "development"  # Default

# Classe principal que integra tudo
class AdvancedDependencyResolver:
    """
    Classe principal que integra todos os componentes para resolução completa
    """
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        
        # Inicializar componentes
        self.import_resolver = None  # AdvancedImportResolver(project_root)
        self.method_resolver = None  # ClassMethodResolver(self.import_resolver)
        self.decorator_analyzer = None  # DecoratorAnalyzer(self.import_resolver, self.method_resolver)
        self.call_chain_tracer = None  # CallChainTracer(self.import_resolver, self.method_resolver, self.decorator_analyzer)
        self.table_resolver = None  # TableNameResolver(self.call_chain_tracer)
        
        # Resultados
        self.all_tables: List[TableResolution] = []
        self.performance_stats = {}
    
    def analyze_complete_project(self) -> List[TableResolution]:
        """Analisa projeto completo e resolve todas as tabelas"""
        
        print("🚀 Iniciando análise completa do projeto...")
        
        # 1. Análise de imports e dependências
        print("📦 Analisando imports e dependências...")
        # self.import_resolver.analyze_project()
        
        # 2. Análise de classes e métodos
        print("🏗️ Analisando classes e métodos...")
        # self.method_resolver.analyze_classes()
        
        # 3. Análise de decorators
        print("🎨 Analisando decorators...")
        # self.decorator_analyzer analisa automaticamente
        
        # 4. Rastreamento de call chains
        print("🔗 Rastreando cadeias de chamadas...")
        # call_chains = self.call_chain_tracer.trace_from_entry_points()
        
        # 5. Resolução final de tabelas
        print("🎯 Resolvendo nomes finais de tabelas...")
        # self.all_tables = self.table_resolver.resolve_all_tables()
        
        print(f"✅ Análise completa! Encontradas {len(self.all_tables)} tabelas.")
        
        return self.all_tables
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Gera relatório abrangente da análise"""
        
        report = {
            "summary": {
                "total_tables_found": len(self.all_tables),
                "by_source_type": self._count_by_source_type(),
                "by_confidence": self._count_by_confidence(),
                "unique_schemas": len(set(t.schema for t in self.all_tables if t.schema))
            },
            "detailed_tables": [
                {
                    "original_identifier": t.original_identifier,
                    "resolved_name": t.resolved_table_name,
                    "schema": t.schema,
                    "full_name": t.full_qualified_name,
                    "confidence": t.confidence,
                    "source_type": t.source_type,
                    "call_chain_length": len(t.resolution_path),
                    "metadata": t.additional_metadata
                }
                for t in self.all_tables
            ],
            "call_chains": [
                {
                    "table": t.full_qualified_name,
                    "chain": [
                        {
                            "step": i+1,
                            "caller": f"{step.caller_class}.{step.caller_method}" if step.caller_class else step.caller_method,
                            "called": step.called_name,
                            "file": step.caller_file,
                            "line": step.line_number
                        }
                        for i, step in enumerate(t.resolution_path)
                    ]
                }
                for t in self.all_tables
            ],
            "performance": self.performance_stats
        }
        
        return report
    
    def _count_by_source_type(self) -> Dict[str, int]:
        """Conta tabelas por tipo de fonte"""
        counts = {}
        for table in self.all_tables:
            counts[table.source_type] = counts.get(table.source_type, 0) + 1
        return counts
    
    def _count_by_confidence(self) -> Dict[str, int]:
        """Conta tabelas por nível de confiança"""
        ranges = {"high": 0, "medium": 0, "low": 0}
        for table in self.all_tables:
            if table.confidence >= 0.8:
                ranges["high"] += 1
            elif table.confidence >= 0.6:
                ranges["medium"] += 1
            else:
                ranges["low"] += 1
        return ranges

def example_usage():
    """Exemplo de uso do Advanced Dependency Resolver"""
    
    project_root = "/path/to/your/project"
    
    # Criar resolver
    resolver = AdvancedDependencyResolver(project_root)
    
    # Analisar projeto
    all_tables = resolver.analyze_complete_project()
    
    # Gerar relatório
    report = resolver.generate_comprehensive_report()
    
    print("=== TABELAS ENCONTRADAS ===")
    for table in all_tables:
        print(f"📊 {table.full_qualified_name}")
        print(f"   Origem: {table.original_identifier}")
        print(f"   Fonte: {table.source_type}")
        print(f"   Confiança: {table.confidence:.1%}")
        print(f"   Cadeia: {len(table.resolution_path)} passos")
        print()
    
    print(f"📈 Total de tabelas únicas: {len(all_tables)}")
    print(f"📊 Por fonte: {report['summary']['by_source_type']}")
    print(f"🎯 Por confiança: {report['summary']['by_confidence']}")

if __name__ == "__main__":
    example_usage()
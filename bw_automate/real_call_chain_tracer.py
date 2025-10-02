#!/usr/bin/env python3
"""
BW_AUTOMATE - Real Call Chain Tracer
=====================================

Rastreador REAL de call chains que funciona como "Ctrl+Click" do IDE.
Segue imports, decorators, classes, self.methods até encontrar a tabela final.

Cenário Real:
    main_dag.py: self._db_interface.get("fx_symbols")
    → DBInterface imported from flextrade.db
    → DBInterface.get() calls get_symbol_data()
    → get_symbol_data() calls fetch_symbol_data()
    → fetch_symbol_data() has SQL: "FROM staging.fx_symbol_master"
    ✅ ENCONTRADO: staging.fx_symbol_master

Autor: BW_AUTOMATE Team
Data: 2025-10-01
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging


@dataclass
class CallChainStep:
    """Um passo na call chain"""
    file_path: str
    function_name: str
    line_number: int
    code_snippet: str
    step_type: str  # 'IMPORT', 'METHOD_CALL', 'FUNCTION_CALL', 'SQL_FOUND'


@dataclass
class TableDiscovery:
    """Tabela descoberta através de call chain"""
    table_name: str
    schema: Optional[str]
    full_chain: List[CallChainStep]
    confidence: float
    sql_context: str


class RealCallChainTracer:
    """
    Traçador real de call chains
    """

    def __init__(self, repo_root: str):
        """
        Inicializa o traçador

        Args:
            repo_root: Raiz do repositório
        """
        self.repo_root = Path(repo_root)

        # Índices globais
        self.file_asts: Dict[str, ast.Module] = {}
        self.file_contents: Dict[str, str] = {}

        # Mapeamento de imports
        self.module_to_file: Dict[str, str] = {}  # "flextrade.db" -> "/path/to/file.py"
        self.import_map: Dict[str, Dict[str, str]] = {}  # file -> {alias: real_name}

        # Mapeamento de classes e funções
        self.class_definitions: Dict[str, Tuple[str, ast.ClassDef]] = {}  # class_name -> (file, node)
        self.function_definitions: Dict[str, List[Tuple[str, ast.FunctionDef]]] = defaultdict(list)  # func_name -> [(file, node)]

        # Resultados
        self.discovered_tables: List[TableDiscovery] = []

        self.logger = logging.getLogger('RealCallChainTracer')
        logging.basicConfig(level=logging.INFO)

    def analyze_repository(self) -> List[TableDiscovery]:
        """
        Analisa repositório completo

        Returns:
            Lista de tabelas descobertas
        """
        self.logger.info(f"🔍 Analisando repositório: {self.repo_root}")

        # Fase 1: Indexa todos os arquivos
        self.logger.info("📁 Fase 1: Indexando arquivos...")
        self._index_all_files()

        # Fase 2: Encontra pontos de entrada (chamadas iniciais)
        self.logger.info("🎯 Fase 2: Encontrando pontos de entrada...")
        entry_points = self._find_entry_points()
        self.logger.info(f"   Encontrados {len(entry_points)} pontos de entrada")

        # Fase 3: Rastreia cada call chain
        self.logger.info("🔗 Fase 3: Rastreando call chains...")
        for file_path, call_node, context in entry_points:
            self._trace_call_chain(file_path, call_node, context, [])

        # Fase 4: Deduplicação
        self.logger.info("🧹 Fase 4: Deduplicando descobertas...")
        deduplicated = self._deduplicate_discoveries()

        self.logger.info(f"✅ Análise concluída!")
        self.logger.info(f"   Total de descobertas: {len(self.discovered_tables)}")
        self.logger.info(f"   Tabelas únicas: {len(deduplicated)}")

        return deduplicated

    def _deduplicate_discoveries(self) -> List[TableDiscovery]:
        """
        Remove descobertas duplicadas, mantendo a de menor profundidade (call chain mais curta)

        Returns:
            Lista de descobertas únicas
        """
        # Agrupa por (table_name, schema)
        discoveries_by_table = {}

        for discovery in self.discovered_tables:
            key = (discovery.table_name, discovery.schema)

            if key not in discoveries_by_table:
                discoveries_by_table[key] = discovery
            else:
                # Mantém a discovery com call chain mais curta (mais direta)
                existing = discoveries_by_table[key]
                if len(discovery.full_chain) < len(existing.full_chain):
                    discoveries_by_table[key] = discovery

        # Retorna lista ordenada por nome de tabela
        unique_discoveries = sorted(
            discoveries_by_table.values(),
            key=lambda d: (d.schema or '', d.table_name)
        )

        return unique_discoveries

    def _index_all_files(self):
        """Indexa todos os arquivos Python"""
        py_files = list(self.repo_root.rglob("*.py"))

        for file_path in py_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(file_path))

                self.file_asts[str(file_path)] = tree
                self.file_contents[str(file_path)] = content

                # Indexa módulo
                rel_path = file_path.relative_to(self.repo_root)
                if file_path.name == '__init__.py':
                    module_name = str(rel_path.parent).replace(os.sep, '.')
                else:
                    module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')

                self.module_to_file[module_name] = str(file_path)

                # Indexa imports
                self._index_imports(tree, str(file_path))

                # Indexa classes
                self._index_classes(tree, str(file_path))

                # Indexa funções
                self._index_functions(tree, str(file_path))

            except Exception as e:
                self.logger.warning(f"Erro ao parsear {file_path}: {e}")

    def _index_imports(self, tree: ast.Module, file_path: str):
        """Indexa imports de um arquivo"""
        if file_path not in self.import_map:
            self.import_map[file_path] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        # alias.asname é o "as", alias.name é o nome original
                        name = alias.asname if alias.asname else alias.name
                        self.import_map[file_path][name] = {
                            'module': node.module,
                            'original': alias.name
                        }

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.import_map[file_path][name] = {
                        'module': alias.name,
                        'original': alias.name
                    }

    def _index_classes(self, tree: ast.Module, file_path: str):
        """Indexa classes de um arquivo"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.class_definitions[node.name] = (file_path, node)

    def _index_functions(self, tree: ast.Module, file_path: str):
        """Indexa funções de um arquivo"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.function_definitions[node.name].append((file_path, node))

    def _find_entry_points(self) -> List[Tuple[str, ast.Call, str]]:
        """
        Encontra pontos de entrada (chamadas que podem levar a tabelas)

        Returns:
            Lista de (file_path, call_node, context)
        """
        entry_points = []

        for file_path, tree in self.file_asts.items():
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Detecta padrões como:
                    # - self._db_interface.get("table")
                    # - db.query("SELECT...")
                    # - fetch_data("key")

                    func_name = self._get_call_name(node)

                    # Padrões suspeitos
                    suspicious_patterns = [
                        'get', 'fetch', 'query', 'execute', 'read_sql',
                        'select', 'insert', 'update', 'delete'
                    ]

                    if any(pattern in func_name.lower() for pattern in suspicious_patterns):
                        context = self._get_node_context(node, file_path)
                        entry_points.append((file_path, node, context))

        return entry_points

    def _trace_call_chain(self,
                         file_path: str,
                         call_node: ast.Call,
                         context: str,
                         chain: List[CallChainStep],
                         depth: int = 0,
                         max_depth: int = 20):
        """
        Traça uma call chain completa

        Args:
            file_path: Arquivo atual
            call_node: Nó de chamada
            context: Contexto da chamada
            chain: Chain acumulada
            depth: Profundidade atual
            max_depth: Profundidade máxima
        """
        if depth >= max_depth:
            return

        # Passo atual
        func_name = self._get_call_name(call_node)
        step = CallChainStep(
            file_path=file_path,
            function_name=func_name,
            line_number=call_node.lineno if hasattr(call_node, 'lineno') else 0,
            code_snippet=context[:100],
            step_type='METHOD_CALL'
        )

        new_chain = chain + [step]

        # Verifica se já encontrou SQL aqui
        tables = self._check_for_sql_in_context(context)
        if tables:
            for table_name, schema in tables:
                discovery = TableDiscovery(
                    table_name=table_name,
                    schema=schema,
                    full_chain=new_chain,
                    confidence=95.0,
                    sql_context=context[:200]
                )
                self.discovered_tables.append(discovery)
                self._log_discovery(discovery)
            return  # Encontrou! Para aqui

        # Extrai argumentos (ex: "fx_symbols")
        args = self._extract_arguments(call_node)

        # Resolve onde está definida a função/método
        target_locations = self._resolve_call_target(func_name, file_path)

        # Para cada possível localização
        for target_file, target_node in target_locations:
            # Busca SQL dentro da função target
            tables = self._search_sql_in_function(target_node, target_file, args)

            if tables:
                for table_name, schema, sql_context in tables:
                    discovery = TableDiscovery(
                        table_name=table_name,
                        schema=schema,
                        full_chain=new_chain,
                        confidence=90.0,
                        sql_context=sql_context[:200]
                    )
                    self.discovered_tables.append(discovery)
                    self._log_discovery(discovery)
            else:
                # Não achou SQL, continua rastreando chamadas dentro
                self._trace_calls_in_function(target_file, target_node, new_chain, depth + 1)

    def _get_call_name(self, call_node: ast.Call) -> str:
        """Extrai nome completo de uma chamada"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            parts = []
            node = call_node.func
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                parts.append(node.id)
            return '.'.join(reversed(parts))
        return ""

    def _get_node_context(self, node: ast.AST, file_path: str) -> str:
        """Pega contexto (linha) de um nó"""
        if hasattr(node, 'lineno'):
            lines = self.file_contents[file_path].split('\n')
            if node.lineno <= len(lines):
                return lines[node.lineno - 1].strip()
        return ""

    def _extract_arguments(self, call_node: ast.Call) -> List[str]:
        """Extrai argumentos de uma chamada"""
        args = []
        for arg in call_node.args:
            if isinstance(arg, ast.Constant):
                args.append(str(arg.value))
            elif isinstance(arg, ast.Str):
                args.append(arg.s)
        return args

    def _resolve_call_target(self, func_name: str, current_file: str) -> List[Tuple[str, ast.AST]]:
        """
        Resolve onde uma função/método está definida

        Args:
            func_name: Nome da função (pode ser "obj.method")
            current_file: Arquivo atual

        Returns:
            Lista de (file_path, function_node)
        """
        targets = []

        # Caso 1: self.method or self._attr.method
        if 'self.' in func_name or func_name.startswith('_'):
            # Procura na classe atual
            targets.extend(self._find_in_current_class(func_name, current_file))

        # Caso 2: Nome simples (pode ser import)
        parts = func_name.split('.')
        first_part = parts[0]

        # Verifica se é import
        if current_file in self.import_map and first_part in self.import_map[current_file]:
            import_info = self.import_map[current_file][first_part]
            module_name = import_info['module']

            # Se importou uma classe
            if len(parts) > 1:
                class_name = import_info['original']
                method_name = parts[-1]

                if class_name in self.class_definitions:
                    class_file, class_node = self.class_definitions[class_name]
                    # Procura método na classe
                    for item in class_node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == method_name:
                            targets.append((class_file, item))

            # Se importou uma função diretamente
            else:
                func_actual_name = import_info['original']
                if func_actual_name in self.function_definitions:
                    targets.extend(self.function_definitions[func_actual_name])

        # Caso 3: Busca direta por nome
        if not targets and parts[-1] in self.function_definitions:
            targets.extend(self.function_definitions[parts[-1]])

        return targets

    def _find_in_current_class(self, method_name: str, file_path: str) -> List[Tuple[str, ast.AST]]:
        """Encontra método na classe atual"""
        # Simplificado - procura todas as classes do arquivo
        targets = []

        tree = self.file_asts.get(file_path)
        if not tree:
            return targets

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if method_name.endswith(item.name) or item.name in method_name:
                            targets.append((file_path, item))

        return targets

    def _search_sql_in_function(self,
                                func_node: ast.FunctionDef,
                                file_path: str,
                                args: List[str]) -> List[Tuple[str, Optional[str], str]]:
        """
        Busca SQL dentro de uma função

        Args:
            func_node: Nó da função
            file_path: Arquivo
            args: Argumentos passados na chamada

        Returns:
            Lista de (table_name, schema, sql_context)
        """
        tables = []

        # Pega código da função
        func_code = ast.get_source_segment(self.file_contents[file_path], func_node)
        if not func_code:
            return tables

        # Procura SQL
        sql_patterns = [
            r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
            r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
            r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
            r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
        ]

        for pattern in sql_patterns:
            matches = re.finditer(pattern, func_code, re.IGNORECASE)
            for match in matches:
                table_full = match.group(1)
                if '.' in table_full:
                    schema, table = table_full.split('.', 1)
                    tables.append((table, schema, func_code))
                else:
                    tables.append((table_full, None, func_code))

        # Procura dicionários de mapeamento (ex: table_mapping = {...})
        # Se temos argumentos específicos, procura por eles
        # Se não temos (args vazios ou são variáveis), extrai TODOS os valores do dict
        dict_args = args if args else [None]

        for arg in dict_args:
            if arg:
                # Tem argumento específico - procura pela chave
                dict_patterns = [
                    # "fx_symbols": "staging.fx_symbol_master"
                    rf'["\']' + re.escape(arg) + rf'["\']\s*:\s*["\']([^"\']+)["\']',
                    # 'fx_symbols': 'staging.fx_symbol_master'
                    rf"[']" + re.escape(arg) + rf"[']\s*:\s*[']([^']+)[']",
                ]
            else:
                # Sem argumento específico - pega TODOS os valores do dict
                dict_patterns = [
                    # Qualquer chave/valor
                    r'["\'][^"\']+["\']\s*:\s*["\']([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)["\']',
                ]

            for dict_pattern in dict_patterns:
                matches = re.finditer(dict_pattern, func_code)
                for match in matches:
                    table_full = match.group(1)

                    # Verifica se parece com schema.table
                    if '.' in table_full and not table_full.startswith('.'):
                        parts = table_full.split('.')
                        if len(parts) == 2:
                            schema, table = parts
                            # Valida que não é um método ou atributo Python
                            if not any(keyword in table_full for keyword in ['self.', 'cls.', 'super.']):
                                tables.append((table, schema, func_code))
                    else:
                        # Tabela sem schema
                        if table_full and not any(c in table_full for c in [' ', '(', ')', '{', '}']):
                            tables.append((table_full, None, func_code))

        return tables

    def _trace_calls_in_function(self,
                                 file_path: str,
                                 func_node: ast.FunctionDef,
                                 chain: List[CallChainStep],
                                 depth: int):
        """Rastreia chamadas dentro de uma função"""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                context = self._get_node_context(node, file_path)
                self._trace_call_chain(file_path, node, context, chain, depth)

    def _check_for_sql_in_context(self, context: str) -> List[Tuple[str, Optional[str]]]:
        """Verifica se há SQL direto no contexto"""
        tables = []

        patterns = [
            r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
            r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                table_full = match.group(1)
                if '.' in table_full:
                    schema, table = table_full.split('.', 1)
                    tables.append((table, schema))
                else:
                    tables.append((table_full, None))

        return tables

    def _log_discovery(self, discovery: TableDiscovery):
        """Log de tabela descoberta"""
        self.logger.info(f"✅ DESCOBERTO: {discovery.schema}.{discovery.table_name}" if discovery.schema else f"✅ DESCOBERTO: {discovery.table_name}")
        self.logger.info(f"   Call chain ({len(discovery.full_chain)} passos):")
        for i, step in enumerate(discovery.full_chain, 1):
            self.logger.info(f"   {i}. {os.path.basename(step.file_path)}:{step.line_number} -> {step.function_name}")

    def export_results(self, output_file: str):
        """Exporta resultados"""
        import json

        results = {
            'total_discoveries': len(self.discovered_tables),
            'discoveries': [
                {
                    'table': discovery.table_name,
                    'schema': discovery.schema,
                    'confidence': discovery.confidence,
                    'chain_length': len(discovery.full_chain),
                    'chain': [
                        {
                            'step': i,
                            'file': os.path.basename(step.file_path),
                            'function': step.function_name,
                            'line': step.line_number
                        }
                        for i, step in enumerate(discovery.full_chain, 1)
                    ]
                }
                for discovery in self.discovered_tables
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self.logger.info(f"📄 Resultados exportados para: {output_file}")


def main():
    """Teste"""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python real_call_chain_tracer.py <repo_dir>")
        sys.exit(1)

    repo_dir = sys.argv[1]

    tracer = RealCallChainTracer(repo_dir)
    discoveries = tracer.analyze_repository()

    tracer.export_results("call_chain_discoveries.json")

    print(f"\n✅ Análise concluída!")
    print(f"📊 Total de tabelas descobertas: {len(discoveries)}")


if __name__ == "__main__":
    main()

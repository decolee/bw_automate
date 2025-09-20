#!/usr/bin/env python3
"""
Airflow PostgreSQL Table Mapper
===============================

Ferramenta completa para análise e mapeamento de tabelas PostgreSQL em códigos Python do Airflow.
Identifica tabelas de origem (leitura) e destino (escrita), mapeando fluxo completo de dados.

Autor: Assistant Claude
Data: 2025-09-20
"""

import re
import ast
import os
import json
import pandas as pd
import logging
from typing import Dict, List, Set, Tuple, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from fuzzywuzzy import fuzz
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class TableReference:
    """Representa uma referência a uma tabela no código"""
    name: str
    schema: Optional[str]
    operation: str  # READ, WRITE, CREATE, UPDATE, DELETE, etc.
    line_number: int
    context: str
    confidence: float  # Score de confiança do match (0-100)
    is_dynamic: bool = False  # Se o nome da tabela é construído dinamicamente
    is_temporary: bool = False  # Se é uma tabela temporária


@dataclass
class FileAnalysis:
    """Resultado da análise de um arquivo Python"""
    file_path: str
    dag_id: Optional[str]
    tables_read: List[TableReference]
    tables_written: List[TableReference]
    dependencies: List[str]
    observations: List[str]
    analysis_timestamp: str


class PostgreSQLTableMapper:
    """
    Classe principal para mapeamento de tabelas PostgreSQL em códigos Python do Airflow
    """
    
    def __init__(self, config_path: str = None):
        """
        Inicializa o mapeador de tabelas
        
        Args:
            config_path: Caminho para arquivo de configuração JSON
        """
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        # Padrões regex para identificar operações SQL
        self.sql_patterns = {
            'read': [
                r'(?i)FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)WITH\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+AS',
                r'(?i)read_sql.*["\']([^"\']+)["\']',
                r'(?i)read_sql_table.*["\']([^"\']+)["\']',
                r'(?i)read_sql_query.*FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
            ],
            'write': [
                r'(?i)INTO\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)CREATE\s+(?:TEMP\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)TRUNCATE\s+(?:TABLE\s+)?([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)to_sql.*["\']([^"\']+)["\']',
                r'(?i)\.to_sql\(\s*["\']([^"\']+)["\']',
            ],
            'alter': [
                r'(?i)ALTER\s+TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
                r'(?i)DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*\.?[a-zA-Z_][a-zA-Z0-9_]*)',
            ]
        }
        
        # Padrões para identificar tabelas temporárias
        self.temp_patterns = [
            r'(?i)temp_',
            r'(?i)tmp_',
            r'(?i)staging_',
            r'(?i)_temp',
            r'(?i)_tmp',
            r'(?i)CREATE\s+TEMP\s+TABLE',
        ]
        
        # Schemas comuns
        self.common_schemas = ['public', 'staging', 'reports', 'analytics', 'temp', 'logs']
        
        # Lista oficial de tabelas (será carregada do arquivo XLSX)
        self.official_tables = set()
        self.schema_table_map = {}
        
        # Resultados da análise
        self.analysis_results = []
        self.dependency_graph = nx.DiGraph()
        
    def _load_config(self, config_path: str) -> Dict:
        """Carrega configurações do arquivo JSON"""
        default_config = {
            "fuzzy_match_threshold": 80,
            "include_temp_tables": True,
            "schemas_to_analyze": ["public", "staging", "reports", "analytics"],
            "file_extensions": [".py"],
            "exclude_patterns": ["__pycache__", ".git", "node_modules"],
            "log_level": "INFO"
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('BW_AUTOMATE/airflow_mapper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_official_tables(self, xlsx_path: str) -> None:
        """
        Carrega a lista oficial de tabelas do arquivo XLSX
        
        Args:
            xlsx_path: Caminho para o arquivo XLSX com a lista de tabelas
        """
        try:
            df = pd.read_excel(xlsx_path)
            
            # Tenta identificar as colunas relevantes
            possible_table_cols = ['table_name', 'nome_tabela', 'tabela', 'name']
            possible_schema_cols = ['schema', 'schema_name', 'esquema']
            
            table_col = None
            schema_col = None
            
            for col in df.columns:
                if any(keyword in col.lower() for keyword in possible_table_cols):
                    table_col = col
                if any(keyword in col.lower() for keyword in possible_schema_cols):
                    schema_col = col
            
            if not table_col:
                # Se não encontrar, usa a primeira coluna
                table_col = df.columns[0]
                self.logger.warning(f"Coluna de tabela não identificada. Usando '{table_col}'")
            
            # Carrega as tabelas
            for _, row in df.iterrows():
                table_name = str(row[table_col]).strip()
                schema_name = str(row[schema_col]).strip() if schema_col else 'public'
                
                if table_name and table_name != 'nan':
                    self.official_tables.add(table_name.lower())
                    if schema_name not in self.schema_table_map:
                        self.schema_table_map[schema_name] = set()
                    self.schema_table_map[schema_name].add(table_name.lower())
            
            self.logger.info(f"Carregadas {len(self.official_tables)} tabelas oficiais do arquivo {xlsx_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar tabelas oficiais: {e}")
            raise
    
    def extract_dag_id(self, content: str, file_path: str) -> Optional[str]:
        """
        Extrai o ID da DAG do código Python
        
        Args:
            content: Conteúdo do arquivo
            file_path: Caminho do arquivo
            
        Returns:
            ID da DAG se encontrado
        """
        patterns = [
            r'dag_id\s*=\s*["\']([^"\']+)["\']',
            r'DAG\s*\(\s*["\']([^"\']+)["\']',
            r'dag\s*=\s*DAG\s*\(\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Se não encontrar, tenta usar o nome do arquivo
        file_name = Path(file_path).stem
        if 'dag' in file_name.lower():
            return file_name
        
        return None
    
    def extract_table_references(self, content: str, file_path: str) -> Tuple[List[TableReference], List[TableReference]]:
        """
        Extrai referências de tabelas do código Python
        
        Args:
            content: Conteúdo do arquivo
            file_path: Caminho do arquivo
            
        Returns:
            Tupla com (tabelas_leitura, tabelas_escrita)
        """
        read_tables = []
        write_tables = []
        
        lines = content.split('\n')
        
        # Processa cada linha
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower().strip()
            
            # Pula comentários e linhas vazias
            if line_lower.startswith('#') or not line_lower:
                continue
            
            # Extrai tabelas de leitura
            for pattern in self.sql_patterns['read']:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    table_name = match.group(1).strip('"`\'')
                    table_ref = self._create_table_reference(
                        table_name, 'READ', line_num, line.strip(), content
                    )
                    if table_ref:
                        read_tables.append(table_ref)
            
            # Extrai tabelas de escrita
            for pattern in self.sql_patterns['write']:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    table_name = match.group(1).strip('"`\'')
                    operation = self._determine_write_operation(line)
                    table_ref = self._create_table_reference(
                        table_name, operation, line_num, line.strip(), content
                    )
                    if table_ref:
                        write_tables.append(table_ref)
            
            # Extrai tabelas de alteração
            for pattern in self.sql_patterns['alter']:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    table_name = match.group(1).strip('"`\'')
                    operation = self._determine_alter_operation(line)
                    table_ref = self._create_table_reference(
                        table_name, operation, line_num, line.strip(), content
                    )
                    if table_ref:
                        write_tables.append(table_ref)
        
        # Remove duplicatas mantendo o primeiro encontrado
        read_tables = self._remove_duplicate_references(read_tables)
        write_tables = self._remove_duplicate_references(write_tables)
        
        return read_tables, write_tables
    
    def _create_table_reference(self, table_name: str, operation: str, line_num: int, context: str, full_content: str) -> Optional[TableReference]:
        """
        Cria uma referência de tabela com validação
        
        Args:
            table_name: Nome da tabela
            operation: Tipo de operação
            line_num: Número da linha
            context: Contexto da linha
            full_content: Conteúdo completo do arquivo
            
        Returns:
            TableReference se válida, None caso contrário
        """
        if not table_name or len(table_name) < 2:
            return None
        
        # Separa schema e tabela
        schema, table = self._parse_table_name(table_name)
        
        # Verifica se é tabela temporária
        is_temp = any(re.search(pattern, table_name, re.IGNORECASE) for pattern in self.temp_patterns)
        
        # Verifica se é dinâmica (contém variáveis)
        is_dynamic = bool(re.search(r'\{|\$|\%', table_name))
        
        # Calcula confiança baseada no match com tabelas oficiais
        confidence = self._calculate_confidence(table_name)
        
        return TableReference(
            name=table.lower(),
            schema=schema,
            operation=operation,
            line_number=line_num,
            context=context[:200],  # Limita contexto
            confidence=confidence,
            is_dynamic=is_dynamic,
            is_temporary=is_temp
        )
    
    def _parse_table_name(self, table_name: str) -> Tuple[Optional[str], str]:
        """
        Separa schema e nome da tabela
        
        Args:
            table_name: Nome completo da tabela
            
        Returns:
            Tupla com (schema, tabela)
        """
        if '.' in table_name:
            parts = table_name.split('.')
            if len(parts) == 2:
                return parts[0].lower(), parts[1].lower()
        
        return None, table_name.lower()
    
    def _determine_write_operation(self, line: str) -> str:
        """Determina o tipo de operação de escrita"""
        line_lower = line.lower()
        if 'insert' in line_lower:
            return 'INSERT'
        elif 'update' in line_lower:
            return 'UPDATE'
        elif 'create' in line_lower:
            return 'CREATE'
        elif 'truncate' in line_lower:
            return 'TRUNCATE'
        elif 'delete' in line_lower:
            return 'DELETE'
        elif 'to_sql' in line_lower:
            return 'WRITE'
        else:
            return 'WRITE'
    
    def _determine_alter_operation(self, line: str) -> str:
        """Determina o tipo de operação de alteração"""
        line_lower = line.lower()
        if 'drop' in line_lower:
            return 'DROP'
        elif 'alter' in line_lower:
            return 'ALTER'
        else:
            return 'ALTER'
    
    def _calculate_confidence(self, table_name: str) -> float:
        """
        Calcula a confiança do match com tabelas oficiais
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Score de confiança (0-100)
        """
        if not self.official_tables:
            return 50.0  # Confiança média se não há lista oficial
        
        table_clean = table_name.lower().split('.')[-1]  # Remove schema
        
        # Match exato
        if table_clean in self.official_tables:
            return 100.0
        
        # Fuzzy match
        max_ratio = 0
        for official_table in self.official_tables:
            ratio = fuzz.ratio(table_clean, official_table)
            max_ratio = max(max_ratio, ratio)
        
        return float(max_ratio)
    
    def _remove_duplicate_references(self, references: List[TableReference]) -> List[TableReference]:
        """Remove referências duplicadas baseado no nome da tabela"""
        seen = set()
        unique_refs = []
        
        for ref in references:
            key = (ref.name, ref.schema, ref.operation)
            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)
        
        return unique_refs
    
    def extract_dependencies(self, content: str, file_path: str) -> List[str]:
        """
        Extrai dependências entre arquivos/DAGs
        
        Args:
            content: Conteúdo do arquivo
            file_path: Caminho do arquivo
            
        Returns:
            Lista de dependências identificadas
        """
        dependencies = []
        
        # Padrões para identificar dependências
        dependency_patterns = [
            r'depends_on_past\s*=\s*True',
            r'wait_for_downstream\s*=\s*True',
            r'ExternalTaskSensor.*dag_id\s*=\s*["\']([^"\']+)["\']',
            r'TriggerDagRunOperator.*trigger_dag_id\s*=\s*["\']([^"\']+)["\']',
            r'from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import',
        ]
        
        for pattern in dependency_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 0:
                    dependencies.append(match.group(1))
        
        return dependencies
    
    def analyze_file(self, file_path: str) -> FileAnalysis:
        """
        Analisa um arquivo Python do Airflow
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Resultado da análise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extrai informações básicas
            dag_id = self.extract_dag_id(content, file_path)
            read_tables, write_tables = self.extract_table_references(content, file_path)
            dependencies = self.extract_dependencies(content, file_path)
            
            # Gera observações
            observations = []
            
            # Verifica tabelas temporárias
            temp_tables = [t for t in read_tables + write_tables if t.is_temporary]
            if temp_tables:
                observations.append(f"Detectadas {len(temp_tables)} tabelas temporárias")
            
            # Verifica tabelas dinâmicas
            dynamic_tables = [t for t in read_tables + write_tables if t.is_dynamic]
            if dynamic_tables:
                observations.append(f"Detectadas {len(dynamic_tables)} tabelas com nomes dinâmicos")
            
            # Verifica matches com baixa confiança
            low_confidence = [t for t in read_tables + write_tables if t.confidence < self.config['fuzzy_match_threshold']]
            if low_confidence:
                observations.append(f"{len(low_confidence)} tabelas com baixa confiança de match")
            
            return FileAnalysis(
                file_path=file_path,
                dag_id=dag_id,
                tables_read=read_tables,
                tables_written=write_tables,
                dependencies=dependencies,
                observations=observations,
                analysis_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar arquivo {file_path}: {e}")
            raise
    
    def analyze_directory(self, directory_path: str) -> List[FileAnalysis]:
        """
        Analisa todos os arquivos Python em um diretório
        
        Args:
            directory_path: Caminho do diretório
            
        Returns:
            Lista de análises de arquivos
        """
        results = []
        
        for root, dirs, files in os.walk(directory_path):
            # Remove diretórios excluídos
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.config['exclude_patterns'])]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.config['file_extensions']):
                    file_path = os.path.join(root, file)
                    try:
                        analysis = self.analyze_file(file_path)
                        results.append(analysis)
                        self.logger.info(f"Analisado: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Erro ao analisar {file_path}: {e}")
        
        self.analysis_results = results
        return results
    
    def build_dependency_graph(self, analyses: List[FileAnalysis]) -> nx.DiGraph:
        """
        Constrói grafo de dependências entre DAGs/arquivos
        
        Args:
            analyses: Lista de análises de arquivos
            
        Returns:
            Grafo de dependências
        """
        self.dependency_graph = nx.DiGraph()
        
        # Adiciona nós para cada arquivo/DAG
        for analysis in analyses:
            node_id = analysis.dag_id or analysis.file_path
            self.dependency_graph.add_node(node_id, analysis=analysis)
        
        # Adiciona arestas baseadas em dependências
        for analysis in analyses:
            source = analysis.dag_id or analysis.file_path
            for dep in analysis.dependencies:
                if self.dependency_graph.has_node(dep):
                    self.dependency_graph.add_edge(dep, source)
        
        return self.dependency_graph
    
    def generate_comprehensive_report(self, output_dir: str = "BW_AUTOMATE/reports") -> Dict[str, str]:
        """
        Gera relatório completo da análise
        
        Args:
            output_dir: Diretório de saída dos relatórios
            
        Returns:
            Dicionário com caminhos dos arquivos gerados
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        reports = {}
        
        # 1. Relatório JSON detalhado
        json_path = f"{output_dir}/detailed_analysis_{timestamp}.json"
        self._generate_json_report(json_path)
        reports['json'] = json_path
        
        # 2. Relatório CSV para análise
        csv_path = f"{output_dir}/table_mappings_{timestamp}.csv"
        self._generate_csv_report(csv_path)
        reports['csv'] = csv_path
        
        # 3. Matriz de dependências
        deps_path = f"{output_dir}/dependency_matrix_{timestamp}.csv"
        self._generate_dependency_matrix(deps_path)
        reports['dependencies'] = deps_path
        
        # 4. Relatório de inventário
        inventory_path = f"{output_dir}/table_inventory_{timestamp}.json"
        self._generate_inventory_report(inventory_path)
        reports['inventory'] = inventory_path
        
        # 5. Visualização do fluxo de dados
        flow_path = f"{output_dir}/data_flow_diagram_{timestamp}.png"
        self._generate_flow_diagram(flow_path)
        reports['flow_diagram'] = flow_path
        
        # 6. Relatório executivo
        exec_path = f"{output_dir}/executive_summary_{timestamp}.html"
        self._generate_executive_report(exec_path)
        reports['executive'] = exec_path
        
        self.logger.info(f"Relatórios gerados em: {output_dir}")
        return reports
    
    def _generate_json_report(self, file_path: str) -> None:
        """Gera relatório JSON detalhado"""
        report_data = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_files_analyzed": len(self.analysis_results),
                "official_tables_loaded": len(self.official_tables),
                "config": self.config
            },
            "files_analysis": [asdict(analysis) for analysis in self.analysis_results],
            "summary_statistics": self._calculate_summary_stats()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    def _generate_csv_report(self, file_path: str) -> None:
        """Gera relatório CSV para análise em planilhas"""
        rows = []
        
        for analysis in self.analysis_results:
            file_name = os.path.basename(analysis.file_path)
            
            # Adiciona tabelas de leitura
            for table in analysis.tables_read:
                rows.append({
                    'arquivo': file_name,
                    'dag_id': analysis.dag_id,
                    'tabela': table.name,
                    'schema': table.schema or 'public',
                    'operacao': table.operation,
                    'tipo': 'READ',
                    'linha': table.line_number,
                    'confianca': table.confidence,
                    'temporaria': table.is_temporary,
                    'dinamica': table.is_dynamic,
                    'contexto': table.context
                })
            
            # Adiciona tabelas de escrita
            for table in analysis.tables_written:
                rows.append({
                    'arquivo': file_name,
                    'dag_id': analysis.dag_id,
                    'tabela': table.name,
                    'schema': table.schema or 'public',
                    'operacao': table.operation,
                    'tipo': 'WRITE',
                    'linha': table.line_number,
                    'confianca': table.confidence,
                    'temporaria': table.is_temporary,
                    'dinamica': table.is_dynamic,
                    'contexto': table.context
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(file_path, index=False, encoding='utf-8')
    
    def _generate_dependency_matrix(self, file_path: str) -> None:
        """Gera matriz de dependências"""
        if not self.dependency_graph:
            self.build_dependency_graph(self.analysis_results)
        
        nodes = list(self.dependency_graph.nodes())
        matrix = pd.DataFrame(0, index=nodes, columns=nodes)
        
        for source, target in self.dependency_graph.edges():
            matrix.loc[source, target] = 1
        
        matrix.to_csv(file_path, encoding='utf-8')
    
    def _generate_inventory_report(self, file_path: str) -> None:
        """Gera relatório de inventário de tabelas"""
        found_tables = set()
        table_usage = {}
        
        for analysis in self.analysis_results:
            for table in analysis.tables_read + analysis.tables_written:
                table_key = f"{table.schema or 'public'}.{table.name}"
                found_tables.add(table.name)
                
                if table_key not in table_usage:
                    table_usage[table_key] = {
                        'read_count': 0,
                        'write_count': 0,
                        'files': set(),
                        'confidence': table.confidence
                    }
                
                if table.operation == 'READ':
                    table_usage[table_key]['read_count'] += 1
                else:
                    table_usage[table_key]['write_count'] += 1
                
                table_usage[table_key]['files'].add(os.path.basename(analysis.file_path))
        
        # Converte sets para listas para serialização JSON
        for table_key in table_usage:
            table_usage[table_key]['files'] = list(table_usage[table_key]['files'])
        
        inventory = {
            "tables_found_in_code": len(found_tables),
            "tables_in_official_list": len(self.official_tables),
            "tables_not_in_official_list": list(found_tables - self.official_tables),
            "official_tables_not_found": list(self.official_tables - found_tables),
            "table_usage_details": table_usage
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
    
    def _generate_flow_diagram(self, file_path: str) -> None:
        """Gera diagrama de fluxo de dados"""
        if not self.dependency_graph:
            self.build_dependency_graph(self.analysis_results)
        
        plt.figure(figsize=(15, 10))
        
        # Configura layout do grafo
        pos = nx.spring_layout(self.dependency_graph, k=3, iterations=50)
        
        # Desenha nós
        nx.draw_networkx_nodes(self.dependency_graph, pos, 
                             node_color='lightblue', 
                             node_size=1000,
                             alpha=0.7)
        
        # Desenha arestas
        nx.draw_networkx_edges(self.dependency_graph, pos,
                             edge_color='gray',
                             arrows=True,
                             arrowsize=20,
                             alpha=0.6)
        
        # Adiciona labels
        labels = {node: node.replace('_', '\n') if len(node) > 15 else node 
                 for node in self.dependency_graph.nodes()}
        nx.draw_networkx_labels(self.dependency_graph, pos, labels, font_size=8)
        
        plt.title("Fluxo de Dependências entre DAGs", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_executive_report(self, file_path: str) -> None:
        """Gera relatório executivo em HTML"""
        stats = self._calculate_summary_stats()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório Executivo - Mapeamento de Tabelas Airflow</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 8px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background-color: #e9e9e9; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .alert {{ background-color: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Relatório Executivo - Mapeamento de Tabelas PostgreSQL</h1>
                <p>Análise de códigos Python do Airflow</p>
                <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <div class="section">
                <h2>Métricas Principais</h2>
                <div class="metric">
                    <strong>{stats['total_files']}</strong><br>
                    Arquivos Analisados
                </div>
                <div class="metric">
                    <strong>{stats['total_tables_found']}</strong><br>
                    Tabelas Encontradas
                </div>
                <div class="metric">
                    <strong>{stats['read_operations']}</strong><br>
                    Operações de Leitura
                </div>
                <div class="metric">
                    <strong>{stats['write_operations']}</strong><br>
                    Operações de Escrita
                </div>
            </div>
            
            <div class="section">
                <h2>Alertas e Observações</h2>
                <div class="alert">
                    <strong>Tabelas não encontradas na lista oficial:</strong> {stats['tables_not_in_official']}
                </div>
                <div class="alert">
                    <strong>Tabelas oficiais não utilizadas:</strong> {stats['official_tables_unused']}
                </div>
                <div class="alert">
                    <strong>Tabelas temporárias detectadas:</strong> {stats['temp_tables']}
                </div>
            </div>
            
            <div class="section">
                <h2>Top 10 Tabelas Mais Utilizadas</h2>
                <table>
                    <tr><th>Tabela</th><th>Leituras</th><th>Escritas</th><th>Total</th></tr>
                    {self._generate_top_tables_html(stats.get('top_tables', []))}
                </table>
            </div>
        </body>
        </html>
        """
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_top_tables_html(self, top_tables: List[Dict]) -> str:
        """Gera HTML para tabela de top tabelas"""
        html = ""
        for table in top_tables[:10]:
            html += f"<tr><td>{table['name']}</td><td>{table['reads']}</td><td>{table['writes']}</td><td>{table['total']}</td></tr>"
        return html
    
    def _calculate_summary_stats(self) -> Dict:
        """Calcula estatísticas resumidas da análise"""
        total_read_ops = sum(len(a.tables_read) for a in self.analysis_results)
        total_write_ops = sum(len(a.tables_written) for a in self.analysis_results)
        
        all_found_tables = set()
        table_counts = {}
        temp_tables = 0
        
        for analysis in self.analysis_results:
            for table in analysis.tables_read + analysis.tables_written:
                all_found_tables.add(table.name)
                
                if table.name not in table_counts:
                    table_counts[table.name] = {'reads': 0, 'writes': 0}
                
                if table.operation == 'READ':
                    table_counts[table.name]['reads'] += 1
                else:
                    table_counts[table.name]['writes'] += 1
                
                if table.is_temporary:
                    temp_tables += 1
        
        # Top tabelas
        top_tables = []
        for table_name, counts in table_counts.items():
            total = counts['reads'] + counts['writes']
            top_tables.append({
                'name': table_name,
                'reads': counts['reads'],
                'writes': counts['writes'],
                'total': total
            })
        
        top_tables.sort(key=lambda x: x['total'], reverse=True)
        
        return {
            'total_files': len(self.analysis_results),
            'total_tables_found': len(all_found_tables),
            'read_operations': total_read_ops,
            'write_operations': total_write_ops,
            'tables_not_in_official': len(all_found_tables - self.official_tables),
            'official_tables_unused': len(self.official_tables - all_found_tables),
            'temp_tables': temp_tables,
            'top_tables': top_tables
        }


def main():
    """Função principal para execução via linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Airflow PostgreSQL Table Mapper')
    parser.add_argument('--source-dir', required=True, help='Diretório com códigos Python do Airflow')
    parser.add_argument('--tables-xlsx', required=True, help='Arquivo XLSX com lista de tabelas')
    parser.add_argument('--config', help='Arquivo de configuração JSON')
    parser.add_argument('--output-dir', default='BW_AUTOMATE/reports', help='Diretório de saída dos relatórios')
    
    args = parser.parse_args()
    
    # Inicializa o mapeador
    mapper = PostgreSQLTableMapper(args.config)
    
    # Carrega tabelas oficiais
    mapper.load_official_tables(args.tables_xlsx)
    
    # Analisa diretório
    results = mapper.analyze_directory(args.source_dir)
    
    # Gera relatórios
    reports = mapper.generate_comprehensive_report(args.output_dir)
    
    print(f"\nAnálise concluída!")
    print(f"Arquivos analisados: {len(results)}")
    print(f"Relatórios gerados em: {args.output_dir}")
    print(f"Arquivos de relatório:")
    for report_type, file_path in reports.items():
        print(f"  - {report_type}: {file_path}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Table Mapper Engine
==================

Engine principal para mapeamento e conciliação de tabelas PostgreSQL.
Implementa fuzzy matching, análise de dependências e mapeamento de fluxo de dados.

Autor: Assistant Claude
Data: 2025-09-20
"""

import pandas as pd
import networkx as nx
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from fuzzywuzzy import fuzz, process
import logging
from collections import defaultdict, Counter
import json
import re
from datetime import datetime


@dataclass
class TableMatch:
    """Representa um match entre tabela encontrada e tabela oficial"""
    found_table: str
    official_table: str
    schema: Optional[str]
    match_score: float
    match_type: str  # EXACT, FUZZY, SCHEMA_MATCH, NO_MATCH
    confidence_level: str  # HIGH, MEDIUM, LOW


@dataclass
class DataFlowEdge:
    """Representa uma aresta no fluxo de dados"""
    source_table: str
    target_table: str
    operation: str
    dag_id: str
    file_path: str
    confidence: float


@dataclass
class TableUsageStats:
    """Estatísticas de uso de uma tabela"""
    table_name: str
    schema: Optional[str]
    read_count: int
    write_count: int
    create_count: int
    update_count: int
    delete_count: int
    files_using: Set[str]
    dags_using: Set[str]
    first_seen: str
    last_seen: str
    is_official: bool
    confidence_avg: float


class TableMappingEngine:
    """
    Engine principal para mapeamento e análise de tabelas PostgreSQL
    """
    
    def __init__(self, config: Dict = None):
        """
        Inicializa o engine de mapeamento
        
        Args:
            config: Configurações do engine
        """
        self.config = config or {}
        self.setup_logging()
        
        # Dados carregados
        self.official_tables = {}  # schema.table -> metadata
        self.found_tables = {}     # table_name -> TableUsageStats
        self.table_matches = []    # Lista de TableMatch
        
        # Grafos de análise
        self.data_flow_graph = nx.DiGraph()
        self.dependency_graph = nx.DiGraph()
        self.table_lineage_graph = nx.DiGraph()
        
        # Métricas de qualidade
        self.quality_metrics = {}
        
        # Configurações de matching
        self.fuzzy_threshold = self.config.get('fuzzy_match_threshold', 80)
        self.schema_priority = self.config.get('schema_priority', ['public', 'staging', 'reports'])
        
    def setup_logging(self):
        """Configura logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_official_tables(self, xlsx_path: str, table_col: str = None, schema_col: str = None) -> None:
        """
        Carrega lista oficial de tabelas do PostgreSQL
        
        Args:
            xlsx_path: Caminho do arquivo XLSX
            table_col: Nome da coluna com nomes das tabelas
            schema_col: Nome da coluna com schemas
        """
        try:
            df = pd.read_excel(xlsx_path)
            
            # Auto-detecta colunas se não especificadas
            if not table_col:
                table_col = self._detect_table_column(df)
            if not schema_col:
                schema_col = self._detect_schema_column(df)
            
            # Processa cada linha
            for _, row in df.iterrows():
                table_name = str(row[table_col]).strip()
                schema_name = str(row[schema_col]).strip() if schema_col else 'public'
                
                if table_name and table_name != 'nan':
                    full_name = f"{schema_name}.{table_name}"
                    self.official_tables[full_name.lower()] = {
                        'table_name': table_name.lower(),
                        'schema': schema_name.lower(),
                        'full_name': full_name.lower(),
                        'metadata': dict(row) if len(df.columns) > 2 else {}
                    }
            
            self.logger.info(f"Carregadas {len(self.official_tables)} tabelas oficiais")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar tabelas oficiais: {e}")
            raise
    
    def _detect_table_column(self, df: pd.DataFrame) -> str:
        """Auto-detecta coluna de nomes de tabelas"""
        candidates = ['table_name', 'nome_tabela', 'tabela', 'name', 'table']
        
        for col in df.columns:
            if any(candidate in col.lower() for candidate in candidates):
                return col
        
        # Se não encontrar, usa a primeira coluna
        return df.columns[0]
    
    def _detect_schema_column(self, df: pd.DataFrame) -> Optional[str]:
        """Auto-detecta coluna de schemas"""
        candidates = ['schema', 'schema_name', 'esquema', 'namespace']
        
        for col in df.columns:
            if any(candidate in col.lower() for candidate in candidates):
                return col
        
        return None
    
    def process_analysis_results(self, analysis_results: List[Any]) -> None:
        """
        Processa resultados da análise de arquivos para construir estatísticas
        
        Args:
            analysis_results: Lista de FileAnalysis objects
        """
        self.found_tables = {}
        
        for analysis in analysis_results:
            file_name = analysis.file_path
            dag_id = analysis.dag_id or "unknown"
            
            # Processa tabelas de leitura
            for table_ref in analysis.tables_read:
                self._update_table_stats(table_ref, 'READ', file_name, dag_id)
            
            # Processa tabelas de escrita
            for table_ref in analysis.tables_written:
                self._update_table_stats(table_ref, 'WRITE', file_name, dag_id)
        
        self.logger.info(f"Processadas estatísticas para {len(self.found_tables)} tabelas únicas")
    
    def _update_table_stats(self, table_ref: Any, operation_type: str, file_name: str, dag_id: str) -> None:
        """
        Atualiza estatísticas de uso de uma tabela
        
        Args:
            table_ref: Referência da tabela
            operation_type: Tipo de operação (READ/WRITE)
            file_name: Nome do arquivo
            dag_id: ID da DAG
        """
        table_key = f"{table_ref.schema or 'public'}.{table_ref.name}"
        
        if table_key not in self.found_tables:
            self.found_tables[table_key] = TableUsageStats(
                table_name=table_ref.name,
                schema=table_ref.schema or 'public',
                read_count=0,
                write_count=0,
                create_count=0,
                update_count=0,
                delete_count=0,
                files_using=set(),
                dags_using=set(),
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
                is_official=table_key.lower() in self.official_tables,
                confidence_avg=table_ref.confidence
            )
        
        stats = self.found_tables[table_key]
        
        # Atualiza contadores baseado na operação
        if operation_type == 'READ':
            stats.read_count += 1
        elif table_ref.operation in ['INSERT', 'WRITE']:
            stats.write_count += 1
        elif table_ref.operation == 'CREATE':
            stats.create_count += 1
        elif table_ref.operation == 'UPDATE':
            stats.update_count += 1
        elif table_ref.operation == 'DELETE':
            stats.delete_count += 1
        else:
            stats.write_count += 1  # Default para write
        
        # Atualiza metadados
        stats.files_using.add(file_name)
        stats.dags_using.add(dag_id)
        stats.last_seen = datetime.now().isoformat()
        
        # Atualiza média de confiança
        current_confidence = stats.confidence_avg or 0
        new_confidence = (current_confidence + table_ref.confidence) / 2
        stats.confidence_avg = new_confidence
    
    def perform_table_matching(self) -> List[TableMatch]:
        """
        Realiza matching entre tabelas encontradas e lista oficial
        
        Returns:
            Lista de matches encontrados
        """
        self.table_matches = []
        
        for found_table_key, stats in self.found_tables.items():
            found_name = stats.table_name
            found_schema = stats.schema
            
            # Busca match exato primeiro
            exact_match = self._find_exact_match(found_name, found_schema)
            if exact_match:
                self.table_matches.append(exact_match)
                continue
            
            # Busca fuzzy match
            fuzzy_match = self._find_fuzzy_match(found_name, found_schema)
            if fuzzy_match:
                self.table_matches.append(fuzzy_match)
                continue
            
            # Sem match encontrado
            no_match = TableMatch(
                found_table=found_name,
                official_table="",
                schema=found_schema,
                match_score=0.0,
                match_type="NO_MATCH",
                confidence_level="LOW"
            )
            self.table_matches.append(no_match)
        
        self.logger.info(f"Realizado matching para {len(self.table_matches)} tabelas")
        return self.table_matches
    
    def _find_exact_match(self, table_name: str, schema: str) -> Optional[TableMatch]:
        """Busca match exato"""
        full_name = f"{schema}.{table_name}".lower()
        
        if full_name in self.official_tables:
            return TableMatch(
                found_table=table_name,
                official_table=self.official_tables[full_name]['table_name'],
                schema=schema,
                match_score=100.0,
                match_type="EXACT",
                confidence_level="HIGH"
            )
        
        return None
    
    def _find_fuzzy_match(self, table_name: str, schema: str) -> Optional[TableMatch]:
        """Busca fuzzy match"""
        # Prepara lista de tabelas oficiais para comparação
        official_names = []
        for full_name, metadata in self.official_tables.items():
            # Prioriza tabelas do mesmo schema
            if metadata['schema'] == schema:
                official_names.append((metadata['table_name'], full_name, 1.1))  # Boost para mesmo schema
            else:
                official_names.append((metadata['table_name'], full_name, 1.0))
        
        if not official_names:
            return None
        
        # Busca melhor match
        best_match = None
        best_score = 0
        
        for official_name, full_name, boost in official_names:
            score = fuzz.ratio(table_name.lower(), official_name.lower()) * boost
            
            if score > best_score and score >= self.fuzzy_threshold:
                best_score = score
                best_match = (official_name, full_name)
        
        if best_match:
            confidence_level = "HIGH" if best_score >= 90 else "MEDIUM" if best_score >= self.fuzzy_threshold else "LOW"
            
            return TableMatch(
                found_table=table_name,
                official_table=best_match[0],
                schema=self.official_tables[best_match[1]]['schema'],
                match_score=best_score / 1.1,  # Normaliza o boost
                match_type="FUZZY",
                confidence_level=confidence_level
            )
        
        return None
    
    def build_data_flow_graph(self, analysis_results: List[Any]) -> nx.DiGraph:
        """
        Constrói grafo de fluxo de dados baseado nas análises
        
        Args:
            analysis_results: Lista de análises de arquivos
            
        Returns:
            Grafo direcionado do fluxo de dados
        """
        self.data_flow_graph = nx.DiGraph()
        
        for analysis in analysis_results:
            dag_id = analysis.dag_id or "unknown"
            file_path = analysis.file_path
            
            # Adiciona nós para todas as tabelas
            all_tables = set()
            
            for table_ref in analysis.tables_read:
                table_name = f"{table_ref.schema or 'public'}.{table_ref.name}"
                all_tables.add(table_name)
                
                # Adiciona nó se não existir
                if not self.data_flow_graph.has_node(table_name):
                    self.data_flow_graph.add_node(table_name, 
                                                 type='table',
                                                 schema=table_ref.schema or 'public',
                                                 table_name=table_ref.name)
            
            for table_ref in analysis.tables_written:
                table_name = f"{table_ref.schema or 'public'}.{table_ref.name}"
                all_tables.add(table_name)
                
                if not self.data_flow_graph.has_node(table_name):
                    self.data_flow_graph.add_node(table_name,
                                                 type='table',
                                                 schema=table_ref.schema or 'public',
                                                 table_name=table_ref.name)
            
            # Adiciona nó para o processo (DAG/arquivo)
            process_node = f"process_{dag_id}"
            if not self.data_flow_graph.has_node(process_node):
                self.data_flow_graph.add_node(process_node,
                                             type='process',
                                             dag_id=dag_id,
                                             file_path=file_path)
            
            # Adiciona arestas: tabela_leitura -> processo -> tabela_escrita
            for read_table in analysis.tables_read:
                read_table_name = f"{read_table.schema or 'public'}.{read_table.name}"
                self.data_flow_graph.add_edge(read_table_name, process_node,
                                            operation='READ',
                                            confidence=read_table.confidence)
            
            for write_table in analysis.tables_written:
                write_table_name = f"{write_table.schema or 'public'}.{write_table.name}"
                self.data_flow_graph.add_edge(process_node, write_table_name,
                                            operation=write_table.operation,
                                            confidence=write_table.confidence)
        
        self.logger.info(f"Grafo de fluxo de dados: {self.data_flow_graph.number_of_nodes()} nós, {self.data_flow_graph.number_of_edges()} arestas")
        return self.data_flow_graph
    
    def build_table_lineage_graph(self) -> nx.DiGraph:
        """
        Constrói grafo de linhagem de dados (tabela -> tabela)
        
        Returns:
            Grafo de linhagem
        """
        self.table_lineage_graph = nx.DiGraph()
        
        # Identifica transformações diretas tabela -> tabela
        process_nodes = [n for n, d in self.data_flow_graph.nodes(data=True) if d.get('type') == 'process']
        
        for process_node in process_nodes:
            # Encontra tabelas de entrada e saída para este processo
            input_tables = [n for n in self.data_flow_graph.predecessors(process_node)]
            output_tables = [n for n in self.data_flow_graph.successors(process_node)]
            
            # Cria arestas diretas entre tabelas de entrada e saída
            for input_table in input_tables:
                for output_table in output_tables:
                    if not self.table_lineage_graph.has_edge(input_table, output_table):
                        self.table_lineage_graph.add_edge(input_table, output_table,
                                                        processes=[process_node])
                    else:
                        # Adiciona processo à lista de processos que fazem esta transformação
                        self.table_lineage_graph[input_table][output_table]['processes'].append(process_node)
        
        self.logger.info(f"Grafo de linhagem: {self.table_lineage_graph.number_of_nodes()} nós, {self.table_lineage_graph.number_of_edges()} arestas")
        return self.table_lineage_graph
    
    def analyze_data_quality(self) -> Dict[str, Any]:
        """
        Analisa qualidade dos dados e mapeamentos
        
        Returns:
            Métricas de qualidade
        """
        total_found = len(self.found_tables)
        total_official = len(self.official_tables)
        
        # Analisa matches
        exact_matches = sum(1 for m in self.table_matches if m.match_type == "EXACT")
        fuzzy_matches = sum(1 for m in self.table_matches if m.match_type == "FUZZY")
        no_matches = sum(1 for m in self.table_matches if m.match_type == "NO_MATCH")
        
        # Tabelas oficiais não utilizadas
        found_table_names = {stats.table_name for stats in self.found_tables.values()}
        official_table_names = {meta['table_name'] for meta in self.official_tables.values()}
        unused_official = official_table_names - found_table_names
        
        # Tabelas não oficiais
        unofficial_tables = {name for name in found_table_names if name not in official_table_names}
        
        # Analisa confiança média
        confidences = [stats.confidence_avg for stats in self.found_tables.values() if stats.confidence_avg]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Analisa cobertura por schema
        schema_coverage = defaultdict(lambda: {'found': 0, 'official': 0})
        
        for stats in self.found_tables.values():
            schema_coverage[stats.schema]['found'] += 1
        
        for meta in self.official_tables.values():
            schema_coverage[meta['schema']]['official'] += 1
        
        self.quality_metrics = {
            'total_tables_found': total_found,
            'total_official_tables': total_official,
            'exact_matches': exact_matches,
            'fuzzy_matches': fuzzy_matches,
            'no_matches': no_matches,
            'match_rate': ((exact_matches + fuzzy_matches) / total_found * 100) if total_found > 0 else 0,
            'unused_official_tables': len(unused_official),
            'unofficial_tables': len(unofficial_tables),
            'unofficial_table_names': list(unofficial_tables),
            'unused_official_table_names': list(unused_official),
            'average_confidence': avg_confidence,
            'high_confidence_tables': sum(1 for c in confidences if c >= 80),
            'low_confidence_tables': sum(1 for c in confidences if c < 50),
            'schema_coverage': dict(schema_coverage),
            'data_flow_complexity': {
                'total_nodes': self.data_flow_graph.number_of_nodes(),
                'total_edges': self.data_flow_graph.number_of_edges(),
                'average_degree': sum(dict(self.data_flow_graph.degree()).values()) / self.data_flow_graph.number_of_nodes() if self.data_flow_graph.number_of_nodes() > 0 else 0
            }
        }
        
        return self.quality_metrics
    
    def identify_critical_tables(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Identifica tabelas críticas baseado em uso e conectividade
        
        Args:
            top_n: Número de tabelas críticas a retornar
            
        Returns:
            Lista de tabelas críticas com métricas
        """
        critical_tables = []
        
        for table_key, stats in self.found_tables.items():
            total_usage = stats.read_count + stats.write_count
            dag_count = len(stats.dags_using)
            file_count = len(stats.files_using)
            
            # Calcula score de criticidade
            usage_score = min(total_usage / 10, 10) * 10  # Normaliza uso (max 100)
            connectivity_score = min(dag_count / 5, 10) * 10  # Normaliza conectividade (max 100)
            diversity_score = min(file_count / 3, 10) * 10  # Normaliza diversidade (max 100)
            
            criticality_score = (usage_score + connectivity_score + diversity_score) / 3
            
            critical_tables.append({
                'table_name': stats.table_name,
                'schema': stats.schema,
                'full_name': table_key,
                'total_usage': total_usage,
                'read_count': stats.read_count,
                'write_count': stats.write_count,
                'dag_count': dag_count,
                'file_count': file_count,
                'criticality_score': criticality_score,
                'is_official': stats.is_official,
                'confidence': stats.confidence_avg
            })
        
        # Ordena por score de criticidade
        critical_tables.sort(key=lambda x: x['criticality_score'], reverse=True)
        
        return critical_tables[:top_n]
    
    def detect_orphaned_tables(self) -> List[str]:
        """
        Detecta tabelas órfãs (apenas leitura ou apenas escrita)
        
        Returns:
            Lista de tabelas órfãs
        """
        orphaned = []
        
        for table_key, stats in self.found_tables.items():
            # Tabela só de leitura (possível tabela de referência)
            if stats.read_count > 0 and stats.write_count == 0 and stats.create_count == 0:
                orphaned.append(f"{table_key} (read-only)")
            
            # Tabela só de escrita (possível tabela de log/auditoria)
            elif stats.write_count > 0 and stats.read_count == 0:
                orphaned.append(f"{table_key} (write-only)")
        
        return orphaned
    
    def generate_mapping_summary(self) -> Dict[str, Any]:
        """
        Gera resumo completo do mapeamento
        
        Returns:
            Dicionário com resumo completo
        """
        quality_metrics = self.analyze_data_quality()
        critical_tables = self.identify_critical_tables()
        orphaned_tables = self.detect_orphaned_tables()
        
        # Estatísticas por tipo de operação
        operation_stats = {
            'total_reads': sum(stats.read_count for stats in self.found_tables.values()),
            'total_writes': sum(stats.write_count for stats in self.found_tables.values()),
            'total_creates': sum(stats.create_count for stats in self.found_tables.values()),
            'total_updates': sum(stats.update_count for stats in self.found_tables.values()),
            'total_deletes': sum(stats.delete_count for stats in self.found_tables.values())
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'quality_metrics': quality_metrics,
            'operation_statistics': operation_stats,
            'critical_tables': critical_tables,
            'orphaned_tables': orphaned_tables,
            'table_matches_summary': {
                'exact_matches': [asdict(m) for m in self.table_matches if m.match_type == "EXACT"],
                'fuzzy_matches': [asdict(m) for m in self.table_matches if m.match_type == "FUZZY"],
                'no_matches': [asdict(m) for m in self.table_matches if m.match_type == "NO_MATCH"]
            },
            'schema_analysis': self._analyze_schemas(),
            'recommendations': self._generate_recommendations()
        }
    
    def _analyze_schemas(self) -> Dict[str, Any]:
        """Analisa distribuição e uso por schema"""
        schema_stats = defaultdict(lambda: {
            'tables_found': 0,
            'tables_official': 0,
            'total_operations': 0,
            'dags_using': set()
        })
        
        for stats in self.found_tables.values():
            schema = stats.schema
            schema_stats[schema]['tables_found'] += 1
            schema_stats[schema]['total_operations'] += (stats.read_count + stats.write_count)
            schema_stats[schema]['dags_using'].update(stats.dags_using)
        
        for meta in self.official_tables.values():
            schema = meta['schema']
            schema_stats[schema]['tables_official'] += 1
        
        # Converte sets para contadores
        for schema in schema_stats:
            schema_stats[schema]['dags_using'] = len(schema_stats[schema]['dags_using'])
        
        return dict(schema_stats)
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        # Recomendações baseadas em qualidade de dados
        if self.quality_metrics.get('match_rate', 0) < 80:
            recommendations.append("Taxa de match baixa - revisar nomenclatura de tabelas ou atualizar lista oficial")
        
        if self.quality_metrics.get('unofficial_tables', 0) > 0:
            recommendations.append(f"Encontradas {self.quality_metrics['unofficial_tables']} tabelas não oficiais - verificar se devem ser adicionadas à lista oficial")
        
        if self.quality_metrics.get('unused_official_tables', 0) > 10:
            recommendations.append("Muitas tabelas oficiais não utilizadas - considerar limpeza da lista oficial")
        
        # Recomendações baseadas em uso
        high_usage_unofficial = [
            stats.table_name for stats in self.found_tables.values()
            if not stats.is_official and (stats.read_count + stats.write_count) > 5
        ]
        
        if high_usage_unofficial:
            recommendations.append(f"Tabelas não oficiais com alto uso: {', '.join(high_usage_unofficial[:5])} - considerar oficialização")
        
        return recommendations
    
    def export_results(self, output_dir: str) -> Dict[str, str]:
        """
        Exporta todos os resultados para arquivos
        
        Args:
            output_dir: Diretório de saída
            
        Returns:
            Dicionário com caminhos dos arquivos gerados
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files_created = {}
        
        # 1. Resumo completo (JSON)
        summary_path = f"{output_dir}/mapping_summary_{timestamp}.json"
        summary = self.generate_mapping_summary()
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        files_created['summary'] = summary_path
        
        # 2. Tabelas encontradas (CSV)
        tables_path = f"{output_dir}/found_tables_{timestamp}.csv"
        tables_data = []
        for table_key, stats in self.found_tables.items():
            tables_data.append({
                'full_name': table_key,
                'table_name': stats.table_name,
                'schema': stats.schema,
                'read_count': stats.read_count,
                'write_count': stats.write_count,
                'create_count': stats.create_count,
                'update_count': stats.update_count,
                'delete_count': stats.delete_count,
                'total_usage': stats.read_count + stats.write_count,
                'files_count': len(stats.files_using),
                'dags_count': len(stats.dags_using),
                'is_official': stats.is_official,
                'confidence_avg': stats.confidence_avg,
                'first_seen': stats.first_seen,
                'last_seen': stats.last_seen
            })
        
        pd.DataFrame(tables_data).to_csv(tables_path, index=False)
        files_created['tables'] = tables_path
        
        # 3. Matches (CSV)
        matches_path = f"{output_dir}/table_matches_{timestamp}.csv"
        matches_data = [asdict(match) for match in self.table_matches]
        pd.DataFrame(matches_data).to_csv(matches_path, index=False)
        files_created['matches'] = matches_path
        
        return files_created


# Exemplo de uso
if __name__ == "__main__":
    # Inicializa o engine
    engine = TableMappingEngine()
    
    # Simula carregamento de dados (seria substituído por dados reais)
    print("Engine de mapeamento de tabelas inicializado")
    print("Use o script principal 'run_analysis.py' para execução completa")
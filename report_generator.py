#!/usr/bin/env python3
"""
Advanced Report Generator
========================

Gerador avançado de relatórios com visualizações, dashboards e exportação em múltiplos formatos.
Suporte para relatórios executivos, técnicos e dashboards interativos.

Autor: Assistant Claude
Data: 2025-09-20
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from jinja2 import Template
import base64
from io import BytesIO
import logging


class AdvancedReportGenerator:
    """
    Gerador avançado de relatórios para análise de tabelas PostgreSQL
    """
    
    def __init__(self, output_dir: str = "BW_AUTOMATE/reports"):
        """
        Inicializa o gerador de relatórios
        
        Args:
            output_dir: Diretório de saída dos relatórios
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configura estilo dos gráficos
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Templates HTML
        self.templates = self._load_templates()
        
        # Configurações de cores
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#F18F01',
            'warning': '#C73E1D',
            'info': '#6A994E',
            'light': '#F8F9FA',
            'dark': '#343A40'
        }
        
        # Métricas acumuladas
        self.metrics_history = []
        
        self.logger = logging.getLogger(__name__)
    
    def _load_templates(self) -> Dict[str, str]:
        """Carrega templates HTML para relatórios"""
        templates = {}
        
        # Template do dashboard executivo
        templates['executive_dashboard'] = '''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard Executivo - Mapeamento de Tabelas</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                {{ custom_css }}
            </style>
        </head>
        <body>
            <div class="container-fluid">
                {{ header }}
                {{ summary_cards }}
                {{ charts }}
                {{ tables }}
                {{ recommendations }}
                {{ footer }}
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        '''
        
        # Template do relatório técnico
        templates['technical_report'] = '''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório Técnico - Análise de Tabelas PostgreSQL</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css" rel="stylesheet">
            <style>
                {{ custom_css }}
            </style>
        </head>
        <body>
            <div class="container">
                {{ technical_content }}
            </div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-core.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/plugins/autoloader/prism-autoloader.min.js"></script>
        </body>
        </html>
        '''
        
        return templates
    
    def generate_executive_dashboard(self, 
                                   mapping_summary: Dict[str, Any],
                                   table_stats: Dict[str, Any],
                                   flow_graph: Any = None) -> str:
        """
        Gera dashboard executivo interativo
        
        Args:
            mapping_summary: Resumo do mapeamento
            table_stats: Estatísticas das tabelas
            flow_graph: Grafo de fluxo de dados
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{self.output_dir}/executive_dashboard_{timestamp}.html"
        
        # Gera componentes do dashboard
        header = self._generate_header("Dashboard Executivo", mapping_summary)
        summary_cards = self._generate_summary_cards(mapping_summary)
        charts = self._generate_executive_charts(mapping_summary, table_stats)
        tables = self._generate_summary_tables(mapping_summary)
        recommendations = self._generate_recommendations_section(mapping_summary)
        footer = self._generate_footer()
        
        # CSS customizado
        custom_css = self._generate_custom_css()
        
        # Compila template
        template = Template(self.templates['executive_dashboard'])
        html_content = template.render(
            custom_css=custom_css,
            header=header,
            summary_cards=summary_cards,
            charts=charts,
            tables=tables,
            recommendations=recommendations,
            footer=footer
        )
        
        # Salva arquivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Dashboard executivo gerado: {output_path}")
        return output_path
    
    def generate_technical_report(self, 
                                analysis_results: List[Any],
                                mapping_summary: Dict[str, Any],
                                sql_analysis: Dict[str, Any] = None) -> str:
        """
        Gera relatório técnico detalhado
        
        Args:
            analysis_results: Resultados da análise de arquivos
            mapping_summary: Resumo do mapeamento
            sql_analysis: Análise SQL detalhada
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{self.output_dir}/technical_report_{timestamp}.html"
        
        # Gera seções técnicas
        sections = []
        
        # 1. Sumário Executivo
        sections.append(self._generate_technical_summary(mapping_summary))
        
        # 2. Metodologia
        sections.append(self._generate_methodology_section())
        
        # 3. Análise por Arquivo
        sections.append(self._generate_file_analysis_section(analysis_results))
        
        # 4. Análise SQL Detalhada
        if sql_analysis:
            sections.append(self._generate_sql_analysis_section(sql_analysis))
        
        # 5. Mapeamento de Tabelas
        sections.append(self._generate_table_mapping_section(mapping_summary))
        
        # 6. Fluxo de Dados
        sections.append(self._generate_data_flow_section(mapping_summary))
        
        # 7. Recomendações Técnicas
        sections.append(self._generate_technical_recommendations(mapping_summary))
        
        # 8. Apêndices
        sections.append(self._generate_appendices(analysis_results, mapping_summary))
        
        technical_content = '\n'.join(sections)
        custom_css = self._generate_technical_css()
        
        # Compila template
        template = Template(self.templates['technical_report'])
        html_content = template.render(
            custom_css=custom_css,
            technical_content=technical_content
        )
        
        # Salva arquivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Relatório técnico gerado: {output_path}")
        return output_path
    
    def generate_data_lineage_visualization(self, lineage_graph: Any) -> str:
        """
        Gera visualização interativa da linhagem de dados
        
        Args:
            lineage_graph: Grafo de linhagem
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{self.output_dir}/data_lineage_{timestamp}.html"
        
        if not lineage_graph or lineage_graph.number_of_nodes() == 0:
            self.logger.warning("Grafo de linhagem vazio")
            return ""
        
        # Calcula layout do grafo
        pos = nx.spring_layout(lineage_graph, k=3, iterations=50)
        
        # Prepara dados para Plotly
        edge_x = []
        edge_y = []
        
        for edge in lineage_graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Cria traço das arestas
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Prepara dados dos nós
        node_x = []
        node_y = []
        node_text = []
        node_info = []
        node_colors = []
        
        for node in lineage_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Determina cor baseada no tipo ou schema
            if '.' in node:
                schema = node.split('.')[0]
                if schema == 'public':
                    color = self.colors['primary']
                elif schema == 'staging':
                    color = self.colors['warning']
                elif schema == 'reports':
                    color = self.colors['success']
                else:
                    color = self.colors['secondary']
            else:
                color = self.colors['info']
            
            node_colors.append(color)
            
            # Informações do nó
            adjacencies = list(lineage_graph.neighbors(node))
            node_info.append(f"Tabela: {node}<br>Conexões: {len(adjacencies)}")
            node_text.append(node.split('.')[-1])  # Apenas nome da tabela
        
        # Cria traço dos nós
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            hovertext=node_info,
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=30,
                color=node_colors,
                line=dict(width=2, color='white')
            )
        )
        
        # Cria figura
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title="Linhagem de Dados - Fluxo entre Tabelas",
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[
                    dict(
                        text="Visualização interativa da linhagem de dados",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor='left', yanchor='bottom',
                        font=dict(color='gray', size=12)
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white'
            )
        )
        
        # Salva visualização
        fig.write_html(output_path)
        
        self.logger.info(f"Visualização de linhagem gerada: {output_path}")
        return output_path
    
    def generate_interactive_table_explorer(self, 
                                          found_tables: Dict[str, Any],
                                          matches: List[Any]) -> str:
        """
        Gera explorador interativo de tabelas
        
        Args:
            found_tables: Tabelas encontradas
            matches: Matches entre tabelas
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{self.output_dir}/table_explorer_{timestamp}.html"
        
        # Prepara dados para tabela interativa
        table_data = []
        
        for table_key, stats in found_tables.items():
            # Encontra match correspondente
            match_info = next((m for m in matches if m.found_table == stats.table_name), None)
            
            table_data.append({
                'Nome': stats.table_name,
                'Schema': stats.schema,
                'Leituras': stats.read_count,
                'Escritas': stats.write_count,
                'Total': stats.read_count + stats.write_count,
                'DAGs': len(stats.dags_using),
                'Arquivos': len(stats.files_using),
                'Oficial': 'Sim' if stats.is_official else 'Não',
                'Confiança': f"{stats.confidence_avg:.1f}%",
                'Match': match_info.match_type if match_info else 'N/A',
                'Score Match': f"{match_info.match_score:.1f}" if match_info else 'N/A'
            })
        
        df = pd.DataFrame(table_data)
        
        # Cria tabela interativa com Plotly
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df.columns),
                fill_color=self.colors['primary'],
                font=dict(color='white', size=12),
                align="left"
            ),
            cells=dict(
                values=[df[col] for col in df.columns],
                fill_color='white',
                align="left",
                font=dict(size=11)
            )
        )])
        
        fig.update_layout(
            title="Explorador Interativo de Tabelas",
            height=600
        )
        
        # Adiciona filtros e funcionalidades JavaScript
        html_template = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Explorador de Tabelas</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container-fluid mt-3">
                <h1>Explorador Interativo de Tabelas</h1>
                <div class="row mb-3">
                    <div class="col-md-4">
                        <input type="text" class="form-control" id="searchInput" placeholder="Buscar tabelas...">
                    </div>
                    <div class="col-md-4">
                        <select class="form-select" id="schemaFilter">
                            <option value="">Todos os schemas</option>
                            {self._generate_schema_options(df)}
                        </select>
                    </div>
                    <div class="col-md-4">
                        <select class="form-select" id="officialFilter">
                            <option value="">Todas as tabelas</option>
                            <option value="Sim">Apenas oficiais</option>
                            <option value="Não">Apenas não oficiais</option>
                        </select>
                    </div>
                </div>
                <div id="tableDiv"></div>
            </div>
            
            <script>
                {fig.to_html(include_plotlyjs=False, div_id="tableDiv")}
                
                // Adiciona funcionalidades de filtro
                document.getElementById('searchInput').addEventListener('input', filterTable);
                document.getElementById('schemaFilter').addEventListener('change', filterTable);
                document.getElementById('officialFilter').addEventListener('change', filterTable);
                
                function filterTable() {{
                    // Implementar lógica de filtro
                    console.log('Filtros aplicados');
                }}
            </script>
        </body>
        </html>
        '''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        self.logger.info(f"Explorador de tabelas gerado: {output_path}")
        return output_path
    
    def generate_comparison_report(self, 
                                 current_analysis: Dict[str, Any],
                                 previous_analysis: Dict[str, Any] = None) -> str:
        """
        Gera relatório de comparação entre análises
        
        Args:
            current_analysis: Análise atual
            previous_analysis: Análise anterior (opcional)
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{self.output_dir}/comparison_report_{timestamp}.html"
        
        if not previous_analysis:
            # Se não há análise anterior, gera relatório baseline
            return self._generate_baseline_report(current_analysis, output_path)
        
        # Calcula diferenças
        differences = self._calculate_differences(current_analysis, previous_analysis)
        
        # Gera visualizações de comparação
        comparison_charts = self._generate_comparison_charts(differences)
        
        # Monta relatório HTML
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório de Comparação</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div class="container">
                <h1>Relatório de Comparação de Análises</h1>
                <p class="text-muted">Comparação entre análises realizadas em diferentes momentos</p>
                
                {self._generate_comparison_summary(differences)}
                {comparison_charts}
                {self._generate_change_details(differences)}
            </div>
        </body>
        </html>
        '''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Relatório de comparação gerado: {output_path}")
        return output_path
    
    def export_to_powerbi(self, mapping_summary: Dict[str, Any]) -> str:
        """
        Exporta dados em formato compatível com Power BI
        
        Args:
            mapping_summary: Resumo do mapeamento
            
        Returns:
            Caminho do arquivo Excel gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{self.output_dir}/powerbi_export_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Resumo Executivo
            summary_data = self._prepare_powerbi_summary(mapping_summary)
            summary_data.to_excel(writer, sheet_name='Resumo_Executivo', index=False)
            
            # Sheet 2: Tabelas Encontradas
            if 'table_usage_details' in mapping_summary:
                tables_data = self._prepare_powerbi_tables(mapping_summary['table_usage_details'])
                tables_data.to_excel(writer, sheet_name='Tabelas_Encontradas', index=False)
            
            # Sheet 3: Matches
            if 'table_matches_summary' in mapping_summary:
                matches_data = self._prepare_powerbi_matches(mapping_summary['table_matches_summary'])
                matches_data.to_excel(writer, sheet_name='Matches_Tabelas', index=False)
            
            # Sheet 4: Métricas de Qualidade
            quality_data = self._prepare_powerbi_quality(mapping_summary.get('quality_metrics', {}))
            quality_data.to_excel(writer, sheet_name='Metricas_Qualidade', index=False)
        
        self.logger.info(f"Arquivo Power BI gerado: {output_path}")
        return output_path
    
    # Métodos auxiliares para geração de componentes HTML
    
    def _generate_header(self, title: str, summary: Dict[str, Any]) -> str:
        """Gera cabeçalho do relatório"""
        return f'''
        <div class="row mb-4">
            <div class="col-12">
                <div class="bg-primary text-white p-4 rounded">
                    <h1 class="mb-0">{title}</h1>
                    <p class="mb-0">Análise de Mapeamento de Tabelas PostgreSQL - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
        </div>
        '''
    
    def _generate_summary_cards(self, summary: Dict[str, Any]) -> str:
        """Gera cards de resumo"""
        quality_metrics = summary.get('quality_metrics', {})
        
        cards = []
        
        # Card 1: Tabelas Encontradas
        cards.append(f'''
        <div class="col-md-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h4 class="card-title">{quality_metrics.get('total_tables_found', 0)}</h4>
                            <p class="card-text">Tabelas Encontradas</p>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-table fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        ''')
        
        # Card 2: Taxa de Match
        match_rate = quality_metrics.get('match_rate', 0)
        card_color = 'success' if match_rate >= 80 else 'warning' if match_rate >= 60 else 'danger'
        
        cards.append(f'''
        <div class="col-md-3">
            <div class="card bg-{card_color} text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h4 class="card-title">{match_rate:.1f}%</h4>
                            <p class="card-text">Taxa de Match</p>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-check-circle fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        ''')
        
        # Card 3: Operações Totais
        operations = summary.get('operation_statistics', {})
        total_ops = sum(operations.values()) if operations else 0
        
        cards.append(f'''
        <div class="col-md-3">
            <div class="card bg-info text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h4 class="card-title">{total_ops:,}</h4>
                            <p class="card-text">Operações Totais</p>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-cogs fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        ''')
        
        # Card 4: Confiança Média
        avg_confidence = quality_metrics.get('average_confidence', 0)
        
        cards.append(f'''
        <div class="col-md-3">
            <div class="card bg-secondary text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h4 class="card-title">{avg_confidence:.1f}%</h4>
                            <p class="card-text">Confiança Média</p>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-shield-alt fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        ''')
        
        return f'<div class="row mb-4">{"".join(cards)}</div>'
    
    def _generate_executive_charts(self, summary: Dict[str, Any], table_stats: Dict[str, Any]) -> str:
        """Gera gráficos para dashboard executivo"""
        charts_html = '<div class="row mb-4">'
        
        # Gráfico 1: Distribuição de Matches
        match_chart = self._create_match_distribution_chart(summary)
        charts_html += f'<div class="col-md-6">{match_chart}</div>'
        
        # Gráfico 2: Top Tabelas por Uso
        usage_chart = self._create_table_usage_chart(summary)
        charts_html += f'<div class="col-md-6">{usage_chart}</div>'
        
        charts_html += '</div>'
        
        # Segunda linha de gráficos
        charts_html += '<div class="row mb-4">'
        
        # Gráfico 3: Distribuição por Schema
        schema_chart = self._create_schema_distribution_chart(summary)
        charts_html += f'<div class="col-md-6">{schema_chart}</div>'
        
        # Gráfico 4: Operações por Tipo
        operations_chart = self._create_operations_chart(summary)
        charts_html += f'<div class="col-md-6">{operations_chart}</div>'
        
        charts_html += '</div>'
        
        return charts_html
    
    def _create_match_distribution_chart(self, summary: Dict[str, Any]) -> str:
        """Cria gráfico de distribuição de matches"""
        quality_metrics = summary.get('quality_metrics', {})
        
        labels = ['Matches Exatos', 'Matches Fuzzy', 'Sem Match']
        values = [
            quality_metrics.get('exact_matches', 0),
            quality_metrics.get('fuzzy_matches', 0),
            quality_metrics.get('no_matches', 0)
        ]
        colors = [self.colors['success'], self.colors['warning'], self.colors['warning']]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=0.3
        )])
        
        fig.update_layout(
            title="Distribuição de Matches",
            height=400
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="match_chart")
    
    def _create_table_usage_chart(self, summary: Dict[str, Any]) -> str:
        """Cria gráfico de uso de tabelas"""
        critical_tables = summary.get('critical_tables', [])[:10]
        
        if not critical_tables:
            return '<div class="alert alert-info">Dados de uso de tabelas não disponíveis</div>'
        
        table_names = [t['table_name'] for t in critical_tables]
        usage_counts = [t['total_usage'] for t in critical_tables]
        
        fig = go.Figure(data=[go.Bar(
            x=usage_counts,
            y=table_names,
            orientation='h',
            marker_color=self.colors['primary']
        )])
        
        fig.update_layout(
            title="Top 10 Tabelas por Uso",
            xaxis_title="Número de Operações",
            height=400
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="usage_chart")
    
    def _create_schema_distribution_chart(self, summary: Dict[str, Any]) -> str:
        """Cria gráfico de distribuição por schema"""
        schema_analysis = summary.get('schema_analysis', {})
        
        if not schema_analysis:
            return '<div class="alert alert-info">Dados de schema não disponíveis</div>'
        
        schemas = list(schema_analysis.keys())
        found_counts = [schema_analysis[s]['tables_found'] for s in schemas]
        official_counts = [schema_analysis[s]['tables_official'] for s in schemas]
        
        fig = go.Figure(data=[
            go.Bar(name='Encontradas', x=schemas, y=found_counts),
            go.Bar(name='Oficiais', x=schemas, y=official_counts)
        ])
        
        fig.update_layout(
            title="Distribuição de Tabelas por Schema",
            barmode='group',
            height=400
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="schema_chart")
    
    def _create_operations_chart(self, summary: Dict[str, Any]) -> str:
        """Cria gráfico de operações por tipo"""
        operations = summary.get('operation_statistics', {})
        
        if not operations:
            return '<div class="alert alert-info">Dados de operações não disponíveis</div>'
        
        labels = list(operations.keys())
        values = list(operations.values())
        
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color=[self.colors['primary'], self.colors['secondary'], 
                         self.colors['success'], self.colors['warning'], self.colors['info']][:len(labels)]
        )])
        
        fig.update_layout(
            title="Operações por Tipo",
            yaxis_title="Número de Operações",
            height=400
        )
        
        return fig.to_html(include_plotlyjs=False, div_id="operations_chart")
    
    def _generate_custom_css(self) -> str:
        """Gera CSS customizado"""
        return '''
        .card {
            border: none;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        
        .table th {
            background-color: #f8f9fa;
            border-top: none;
        }
        
        .alert {
            border: none;
            border-radius: 0.5rem;
        }
        
        .progress {
            height: 1rem;
        }
        
        .badge {
            font-size: 0.8em;
        }
        '''
    
    def _generate_recommendations_section(self, summary: Dict[str, Any]) -> str:
        """Gera seção de recomendações"""
        recommendations = summary.get('recommendations', [])
        
        if not recommendations:
            return ''
        
        rec_html = '''
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-lightbulb"></i> Recomendações</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
        '''
        
        for rec in recommendations:
            rec_html += f'<li class="list-group-item"><i class="fas fa-arrow-right text-primary me-2"></i>{rec}</li>'
        
        rec_html += '''
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        '''
        
        return rec_html
    
    def _generate_footer(self) -> str:
        """Gera rodapé do relatório"""
        return f'''
        <div class="row mt-5">
            <div class="col-12">
                <hr>
                <div class="text-center text-muted">
                    <p>Relatório gerado automaticamente pelo BW_AUTOMATE em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                    <p><small>Ferramenta de Mapeamento de Tabelas PostgreSQL para Airflow</small></p>
                </div>
            </div>
        </div>
        '''
    
    # Métodos auxiliares para preparação de dados
    
    def _prepare_powerbi_summary(self, summary: Dict[str, Any]) -> pd.DataFrame:
        """Prepara dados de resumo para Power BI"""
        quality_metrics = summary.get('quality_metrics', {})
        operations = summary.get('operation_statistics', {})
        
        data = {
            'Métrica': [
                'Total de Tabelas Encontradas',
                'Total de Tabelas Oficiais',
                'Taxa de Match (%)',
                'Matches Exatos',
                'Matches Fuzzy',
                'Sem Match',
                'Tabelas Não Oficiais',
                'Confiança Média (%)',
                'Total de Leituras',
                'Total de Escritas'
            ],
            'Valor': [
                quality_metrics.get('total_tables_found', 0),
                quality_metrics.get('total_official_tables', 0),
                quality_metrics.get('match_rate', 0),
                quality_metrics.get('exact_matches', 0),
                quality_metrics.get('fuzzy_matches', 0),
                quality_metrics.get('no_matches', 0),
                quality_metrics.get('unofficial_tables', 0),
                quality_metrics.get('average_confidence', 0),
                operations.get('total_reads', 0),
                operations.get('total_writes', 0)
            ]
        }
        
        return pd.DataFrame(data)
    
    def _generate_schema_options(self, df: pd.DataFrame) -> str:
        """Gera opções de schema para filtro"""
        schemas = df['Schema'].unique()
        options = []
        for schema in sorted(schemas):
            options.append(f'<option value="{schema}">{schema}</option>')
        return '\n'.join(options)
    
    # Métodos para relatório técnico (implementação básica)
    
    def _generate_technical_summary(self, summary: Dict[str, Any]) -> str:
        """Gera sumário técnico"""
        return f'''
        <section id="summary">
            <h2>1. Sumário Executivo</h2>
            <p>Este relatório apresenta a análise detalhada do mapeamento de tabelas PostgreSQL 
            encontradas nos códigos Python do Airflow.</p>
            
            <h3>Principais Achados</h3>
            <ul>
                <li>Total de tabelas identificadas: {summary.get('quality_metrics', {}).get('total_tables_found', 0)}</li>
                <li>Taxa de match com tabelas oficiais: {summary.get('quality_metrics', {}).get('match_rate', 0):.1f}%</li>
                <li>Confiança média das identificações: {summary.get('quality_metrics', {}).get('average_confidence', 0):.1f}%</li>
            </ul>
        </section>
        '''
    
    def _generate_methodology_section(self) -> str:
        """Gera seção de metodologia"""
        return '''
        <section id="methodology">
            <h2>2. Metodologia</h2>
            <h3>Processo de Análise</h3>
            <ol>
                <li><strong>Extração de Código:</strong> Análise de arquivos Python (.py) usando regex e AST</li>
                <li><strong>Identificação SQL:</strong> Detecção de padrões SQL em strings, pandas e SQLAlchemy</li>
                <li><strong>Extração de Tabelas:</strong> Parsing de nomes de tabelas usando sqlparse e regex</li>
                <li><strong>Matching:</strong> Comparação com lista oficial usando algoritmos exatos e fuzzy</li>
                <li><strong>Análise de Fluxo:</strong> Construção de grafos de dependência e linhagem</li>
            </ol>
        </section>
        '''
    
    def _generate_file_analysis_section(self, analysis_results: List[Any]) -> str:
        """Gera seção de análise por arquivo"""
        html = '<section id="file-analysis"><h2>3. Análise por Arquivo</h2>'
        
        for analysis in analysis_results[:10]:  # Limita a 10 para não ficar muito longo
            html += f'''
            <h4>{os.path.basename(analysis.file_path)}</h4>
            <ul>
                <li>DAG ID: {analysis.dag_id or 'N/A'}</li>
                <li>Tabelas de leitura: {len(analysis.tables_read)}</li>
                <li>Tabelas de escrita: {len(analysis.tables_written)}</li>
            </ul>
            '''
        
        html += '</section>'
        return html
    
    # Outros métodos auxiliares seriam implementados de forma similar...
    
    def _generate_sql_analysis_section(self, sql_analysis: Dict[str, Any]) -> str:
        """Placeholder para análise SQL"""
        return '<section id="sql-analysis"><h2>4. Análise SQL Detalhada</h2><p>Seção em desenvolvimento.</p></section>'
    
    def _generate_table_mapping_section(self, summary: Dict[str, Any]) -> str:
        """Placeholder para mapeamento de tabelas"""
        return '<section id="table-mapping"><h2>5. Mapeamento de Tabelas</h2><p>Seção em desenvolvimento.</p></section>'
    
    def _generate_data_flow_section(self, summary: Dict[str, Any]) -> str:
        """Placeholder para fluxo de dados"""
        return '<section id="data-flow"><h2>6. Fluxo de Dados</h2><p>Seção em desenvolvimento.</p></section>'
    
    def _generate_technical_recommendations(self, summary: Dict[str, Any]) -> str:
        """Placeholder para recomendações técnicas"""
        return '<section id="tech-recommendations"><h2>7. Recomendações Técnicas</h2><p>Seção em desenvolvimento.</p></section>'
    
    def _generate_appendices(self, analysis_results: List[Any], summary: Dict[str, Any]) -> str:
        """Placeholder para apêndices"""
        return '<section id="appendices"><h2>8. Apêndices</h2><p>Seção em desenvolvimento.</p></section>'
    
    def _generate_technical_css(self) -> str:
        """CSS para relatório técnico"""
        return self._generate_custom_css()


# Exemplo de uso
if __name__ == "__main__":
    generator = AdvancedReportGenerator()
    print("Gerador de relatórios avançados inicializado")
    print("Use o script principal para gerar relatórios completos")
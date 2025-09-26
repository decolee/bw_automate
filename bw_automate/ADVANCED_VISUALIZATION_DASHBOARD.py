#!/usr/bin/env python3
"""
ADVANCED VISUALIZATION DASHBOARD - BW AUTOMATE SYSTEM
Dashboard interativo avançado com visualizações em tempo real
Suporte a múltiplos formatos de saída e análises dinâmicas
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import threading
import time
import logging

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.figure_factory as ff
except ImportError:
    print("Installing plotly for visualizations...")
    os.system("pip install plotly")
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.figure_factory as ff

try:
    import dash
    from dash import dcc, html, Input, Output, callback, dash_table
    import dash_bootstrap_components as dbc
except ImportError:
    print("Installing dash for interactive dashboard...")
    os.system("pip install dash dash-bootstrap-components")
    import dash
    from dash import dcc, html, Input, Output, callback, dash_table
    import dash_bootstrap_components as dbc

try:
    import networkx as nx
except ImportError:
    print("Installing networkx for graph analysis...")
    os.system("pip install networkx")
    import networkx as nx

try:
    from wordcloud import WordCloud
except ImportError:
    print("Installing wordcloud for text visualization...")
    os.system("pip install wordcloud")
    from wordcloud import WordCloud

try:
    import seaborn as sns
    import matplotlib.pyplot as plt
    plt.style.use('dark_background')
except ImportError:
    print("Installing seaborn and matplotlib...")
    os.system("pip install seaborn matplotlib")
    import seaborn as sns
    import matplotlib.pyplot as plt
    plt.style.use('dark_background')


class DataProcessor:
    """Processador de dados para visualizações"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.cache = {}
        self.last_update = {}
    
    def load_analysis_results(self, force_reload: bool = False) -> Dict[str, Any]:
        """Carrega resultados de análises"""
        cache_key = "analysis_results"
        
        if not force_reload and cache_key in self.cache:
            # Verifica se cache ainda é válido (5 minutos)
            if datetime.now() - self.last_update.get(cache_key, datetime.min) < timedelta(minutes=5):
                return self.cache[cache_key]
        
        results = {
            'tables': [],
            'files': [],
            'dependencies': [],
            'metrics': [],
            'issues': [],
            'sql_patterns': [],
            'performance': []
        }
        
        # Carrega dados de análises
        for json_file in self.data_dir.glob("**/*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'tables_found' in data:
                    results['tables'].extend(data.get('tables_found', []))
                
                if 'file_path' in data:
                    file_info = {
                        'path': data['file_path'],
                        'size': data.get('file_size', 0),
                        'type': data.get('file_type', ''),
                        'modification_time': data.get('modification_time', 0),
                        'tables_count': len(data.get('table_references', [])),
                        'issues_count': len(data.get('issues_detected', []))
                    }
                    results['files'].append(file_info)
                
                if 'sql_patterns' in data:
                    results['sql_patterns'].extend(data.get('sql_patterns', []))
                
                if 'issues_detected' in data:
                    results['issues'].extend(data.get('issues_detected', []))
                    
            except Exception as e:
                logging.error(f"Error loading {json_file}: {e}")
        
        # Carrega métricas de performance
        metrics_file = self.data_dir / "performance_metrics.jsonl"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        metric = json.loads(line.strip())
                        results['performance'].append(metric)
            except Exception as e:
                logging.error(f"Error loading performance metrics: {e}")
        
        # Cache os resultados
        self.cache[cache_key] = results
        self.last_update[cache_key] = datetime.now()
        
        return results
    
    def get_table_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera estatísticas de tabelas"""
        tables = data.get('tables', [])
        
        if not tables:
            return {'total': 0, 'unique': 0, 'most_common': []}
        
        # Conta ocorrências de tabelas
        table_counts = {}
        for table in tables:
            table_name = table if isinstance(table, str) else table.get('name', 'unknown')
            table_counts[table_name] = table_counts.get(table_name, 0) + 1
        
        # Top 10 tabelas mais utilizadas
        most_common = sorted(table_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total': len(tables),
            'unique': len(table_counts),
            'most_common': most_common,
            'distribution': table_counts
        }
    
    def get_file_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera estatísticas de arquivos"""
        files = data.get('files', [])
        
        if not files:
            return {'total': 0, 'by_type': {}, 'avg_size': 0}
        
        # Agrupa por tipo
        by_type = {}
        total_size = 0
        
        for file_info in files:
            file_type = file_info.get('type', 'unknown')
            by_type[file_type] = by_type.get(file_type, 0) + 1
            total_size += file_info.get('size', 0)
        
        return {
            'total': len(files),
            'by_type': by_type,
            'avg_size': total_size / len(files) if files else 0,
            'total_size': total_size
        }
    
    def get_dependency_graph(self, data: Dict[str, Any]) -> nx.DiGraph:
        """Cria grafo de dependências"""
        G = nx.DiGraph()
        
        # Adiciona nós e arestas baseado nos dados
        files = data.get('files', [])
        
        for file_info in files:
            file_path = file_info.get('path', '')
            file_name = Path(file_path).name
            
            # Adiciona nó do arquivo
            G.add_node(file_name, 
                      path=file_path,
                      size=file_info.get('size', 0),
                      tables_count=file_info.get('tables_count', 0))
            
            # TODO: Adicionar lógica de dependências baseada em imports/references
        
        return G


class VisualizationEngine:
    """Engine de visualizações avançadas"""
    
    def __init__(self, data_processor: DataProcessor):
        self.data_processor = data_processor
        self.color_palette = px.colors.qualitative.Set3
    
    def create_table_distribution_chart(self, data: Dict[str, Any]) -> go.Figure:
        """Gráfico de distribuição de tabelas"""
        stats = self.data_processor.get_table_statistics(data)
        
        if not stats['most_common']:
            return go.Figure().add_annotation(text="Nenhuma tabela encontrada")
        
        tables, counts = zip(*stats['most_common'])
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(tables),
                y=list(counts),
                marker_color=self.color_palette[:len(tables)],
                text=list(counts),
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Top 10 Tabelas Mais Utilizadas",
            xaxis_title="Tabelas",
            yaxis_title="Frequência de Uso",
            template="plotly_dark",
            height=500
        )
        
        return fig
    
    def create_file_type_pie_chart(self, data: Dict[str, Any]) -> go.Figure:
        """Gráfico pizza de tipos de arquivo"""
        stats = self.data_processor.get_file_statistics(data)
        
        if not stats['by_type']:
            return go.Figure().add_annotation(text="Nenhum arquivo encontrado")
        
        labels = list(stats['by_type'].keys())
        values = list(stats['by_type'].values())
        
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker_colors=self.color_palette[:len(labels)]
            )
        ])
        
        fig.update_layout(
            title="Distribuição por Tipo de Arquivo",
            template="plotly_dark",
            height=400
        )
        
        return fig
    
    def create_performance_timeline(self, data: Dict[str, Any]) -> go.Figure:
        """Timeline de performance do sistema"""
        performance_data = data.get('performance', [])
        
        if not performance_data:
            return go.Figure().add_annotation(text="Dados de performance não disponíveis")
        
        df = pd.DataFrame(performance_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=['CPU Usage (%)', 'Memory Usage (%)', 'Cache Hit Ratio (%)'],
            vertical_spacing=0.08
        )
        
        # CPU Usage
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['cpu_usage'],
                mode='lines+markers',
                name='CPU',
                line=dict(color='#ff6b6b')
            ),
            row=1, col=1
        )
        
        # Memory Usage
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['memory_usage'],
                mode='lines+markers',
                name='Memory',
                line=dict(color='#4ecdc4')
            ),
            row=2, col=1
        )
        
        # Cache Hit Ratio
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['cache_hit_ratio'] * 100,
                mode='lines+markers',
                name='Cache Hit',
                line=dict(color='#45b7d1')
            ),
            row=3, col=1
        )
        
        fig.update_layout(
            title="Performance do Sistema em Tempo Real",
            template="plotly_dark",
            height=800,
            showlegend=False
        )
        
        return fig
    
    def create_dependency_network(self, data: Dict[str, Any]) -> go.Figure:
        """Rede de dependências entre arquivos"""
        G = self.data_processor.get_dependency_graph(data)
        
        if len(G.nodes()) == 0:
            return go.Figure().add_annotation(text="Grafo de dependências vazio")
        
        # Layout do grafo
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Arestas
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Nós
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            # Tamanho baseado na quantidade de tabelas
            tables_count = G.nodes[node].get('tables_count', 0)
            node_size.append(max(10, tables_count * 5 + 10))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=node_size,
                color='#45b7d1',
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>%{text}</b><extra></extra>'
        )
        
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title="Rede de Dependências entre Arquivos",
            showlegend=False,
            template="plotly_dark",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=600
        )
        
        return fig
    
    def create_sql_patterns_heatmap(self, data: Dict[str, Any]) -> go.Figure:
        """Heatmap de padrões SQL"""
        sql_patterns = data.get('sql_patterns', [])
        
        if not sql_patterns:
            return go.Figure().add_annotation(text="Nenhum padrão SQL encontrado")
        
        # Agrupa padrões por tipo
        pattern_matrix = {}
        files = set()
        
        for pattern in sql_patterns:
            pattern_type = pattern.get('pattern', 'unknown')
            file_path = pattern.get('file', 'unknown')
            count = len(pattern.get('matches', []))
            
            if pattern_type not in pattern_matrix:
                pattern_matrix[pattern_type] = {}
            pattern_matrix[pattern_type][file_path] = count
            files.add(file_path)
        
        # Converte para matriz
        pattern_types = list(pattern_matrix.keys())
        files = list(files)
        
        matrix = []
        for pattern_type in pattern_types:
            row = []
            for file_path in files:
                count = pattern_matrix[pattern_type].get(file_path, 0)
                row.append(count)
            matrix.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=[Path(f).name for f in files],
            y=pattern_types,
            colorscale='Viridis',
            text=matrix,
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Heatmap de Padrões SQL por Arquivo",
            template="plotly_dark",
            height=400
        )
        
        return fig
    
    def create_issues_breakdown(self, data: Dict[str, Any]) -> go.Figure:
        """Breakdown de issues detectados"""
        issues = data.get('issues', [])
        
        if not issues:
            return go.Figure().add_annotation(text="Nenhum issue detectado")
        
        # Agrupa issues por severidade e tipo
        severity_counts = {}
        type_counts = {}
        
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            issue_type = issue.get('type', 'unknown')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        # Subplots para severidade e tipo
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['Por Severidade', 'Por Tipo'],
            specs=[[{"type": "pie"}, {"type": "pie"}]]
        )
        
        # Gráfico de severidade
        if severity_counts:
            fig.add_trace(
                go.Pie(
                    labels=list(severity_counts.keys()),
                    values=list(severity_counts.values()),
                    name="Severidade"
                ),
                row=1, col=1
            )
        
        # Gráfico de tipo
        if type_counts:
            fig.add_trace(
                go.Pie(
                    labels=list(type_counts.keys()),
                    values=list(type_counts.values()),
                    name="Tipo"
                ),
                row=1, col=2
            )
        
        fig.update_layout(
            title="Breakdown de Issues Detectados",
            template="plotly_dark",
            height=400
        )
        
        return fig


class InteractiveDashboard:
    """Dashboard interativo principal"""
    
    def __init__(self, data_dir: str, port: int = 8050):
        self.data_dir = Path(data_dir)
        self.port = port
        self.data_processor = DataProcessor(data_dir)
        self.viz_engine = VisualizationEngine(self.data_processor)
        self.app = None
        self.server_thread = None
        
        # Configuração do app Dash
        self.setup_dashboard()
    
    def setup_dashboard(self):
        """Configura o dashboard Dash"""
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.themes.DARKLY],
            suppress_callback_exceptions=True
        )
        
        self.app.title = "BW Automate - Advanced Analytics Dashboard"
        
        # Layout principal
        self.app.layout = self.create_layout()
        
        # Callbacks
        self.setup_callbacks()
    
    def create_layout(self):
        """Cria layout principal do dashboard"""
        return dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("🚀 BW Automate Analytics Dashboard", 
                           className="text-center mb-4 text-primary"),
                    html.Hr()
                ])
            ]),
            
            # Controles
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Controles", className="card-title"),
                            dbc.ButtonGroup([
                                dbc.Button("🔄 Atualizar", id="refresh-btn", color="primary", size="sm"),
                                dbc.Button("📊 Exportar", id="export-btn", color="success", size="sm"),
                                dbc.Button("⚙️ Configurações", id="config-btn", color="info", size="sm")
                            ]),
                            html.Hr(),
                            html.Div(id="last-update", className="text-muted small")
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Métricas principais
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id="total-tables", children="0", className="text-primary"),
                            html.P("Tabelas Únicas", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id="total-files", children="0", className="text-success"),
                            html.P("Arquivos Analisados", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id="total-issues", children="0", className="text-warning"),
                            html.P("Issues Detectados", className="card-text")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4(id="cache-ratio", children="0%", className="text-info"),
                            html.P("Cache Hit Ratio", className="card-text")
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Tabs para diferentes visualizações
            dbc.Card([
                dbc.CardHeader([
                    dbc.Tabs([
                        dbc.Tab(label="📈 Visão Geral", tab_id="overview"),
                        dbc.Tab(label="🗃️ Tabelas", tab_id="tables"),
                        dbc.Tab(label="📁 Arquivos", tab_id="files"),
                        dbc.Tab(label="⚡ Performance", tab_id="performance"),
                        dbc.Tab(label="🔍 SQL Patterns", tab_id="sql"),
                        dbc.Tab(label="🛠️ Issues", tab_id="issues"),
                        dbc.Tab(label="🕸️ Dependências", tab_id="dependencies")
                    ], id="main-tabs", active_tab="overview")
                ]),
                dbc.CardBody([
                    html.Div(id="tab-content")
                ])
            ]),
            
            # Footer
            html.Hr(),
            html.Footer([
                html.P("BW Automate System - Advanced Analytics Dashboard", 
                      className="text-center text-muted")
            ])
            
        ], fluid=True)
    
    def setup_callbacks(self):
        """Configura callbacks do dashboard"""
        
        @self.app.callback(
            [Output("tab-content", "children"),
             Output("total-tables", "children"),
             Output("total-files", "children"),
             Output("total-issues", "children"),
             Output("cache-ratio", "children"),
             Output("last-update", "children")],
            [Input("main-tabs", "active_tab"),
             Input("refresh-btn", "n_clicks")]
        )
        def update_dashboard(active_tab, refresh_clicks):
            # Carrega dados
            data = self.data_processor.load_analysis_results(force_reload=bool(refresh_clicks))
            
            # Calcula métricas
            table_stats = self.data_processor.get_table_statistics(data)
            file_stats = self.data_processor.get_file_statistics(data)
            issues_count = len(data.get('issues', []))
            
            # Performance data
            performance_data = data.get('performance', [])
            cache_ratio = "0%"
            if performance_data:
                latest_perf = performance_data[-1]
                cache_ratio = f"{latest_perf.get('cache_hit_ratio', 0) * 100:.1f}%"
            
            # Timestamp da última atualização
            last_update = f"Última atualização: {datetime.now().strftime('%H:%M:%S')}"
            
            # Conteúdo baseado na tab ativa
            if active_tab == "overview":
                content = self.create_overview_tab(data)
            elif active_tab == "tables":
                content = self.create_tables_tab(data)
            elif active_tab == "files":
                content = self.create_files_tab(data)
            elif active_tab == "performance":
                content = self.create_performance_tab(data)
            elif active_tab == "sql":
                content = self.create_sql_tab(data)
            elif active_tab == "issues":
                content = self.create_issues_tab(data)
            elif active_tab == "dependencies":
                content = self.create_dependencies_tab(data)
            else:
                content = html.Div("Conteúdo não encontrado")
            
            return (content, 
                   str(table_stats['unique']),
                   str(file_stats['total']),
                   str(issues_count),
                   cache_ratio,
                   last_update)
    
    def create_overview_tab(self, data: Dict[str, Any]) -> html.Div:
        """Tab de visão geral"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=self.viz_engine.create_table_distribution_chart(data))
                ], width=6),
                dbc.Col([
                    dcc.Graph(figure=self.viz_engine.create_file_type_pie_chart(data))
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=self.viz_engine.create_issues_breakdown(data))
                ], width=12)
            ])
        ])
    
    def create_tables_tab(self, data: Dict[str, Any]) -> html.Div:
        """Tab de análise de tabelas"""
        table_stats = self.data_processor.get_table_statistics(data)
        
        # Tabela com estatísticas
        table_data = []
        for table_name, count in table_stats.get('most_common', []):
            table_data.append({
                'Tabela': table_name,
                'Frequência': count,
                'Percentual': f"{(count / table_stats['total'] * 100):.1f}%"
            })
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=self.viz_engine.create_table_distribution_chart(data))
                ], width=8),
                dbc.Col([
                    html.H5("Estatísticas"),
                    html.P(f"Total de referências: {table_stats['total']}"),
                    html.P(f"Tabelas únicas: {table_stats['unique']}"),
                    html.P(f"Média por arquivo: {table_stats['total'] / max(1, len(data.get('files', []))):.1f}")
                ], width=4)
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("Top Tabelas por Uso"),
                    dash_table.DataTable(
                        data=table_data,
                        columns=[
                            {'name': 'Tabela', 'id': 'Tabela'},
                            {'name': 'Frequência', 'id': 'Frequência'},
                            {'name': '%', 'id': 'Percentual'}
                        ],
                        style_cell={'textAlign': 'left'},
                        style_data={'backgroundColor': '#2b2b2b', 'color': 'white'},
                        style_header={'backgroundColor': '#1e1e1e', 'color': 'white', 'fontWeight': 'bold'}
                    )
                ])
            ])
        ])
    
    def create_files_tab(self, data: Dict[str, Any]) -> html.Div:
        """Tab de análise de arquivos"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=self.viz_engine.create_file_type_pie_chart(data))
                ], width=6),
                dbc.Col([
                    html.H5("Estatísticas de Arquivos"),
                    # TODO: Adicionar mais estatísticas de arquivos
                ], width=6)
            ])
        ])
    
    def create_performance_tab(self, data: Dict[str, Any]) -> html.Div:
        """Tab de performance"""
        return html.Div([
            dcc.Graph(figure=self.viz_engine.create_performance_timeline(data))
        ])
    
    def create_sql_tab(self, data: Dict[str, Any]) -> html.Div:
        """Tab de padrões SQL"""
        return html.Div([
            dcc.Graph(figure=self.viz_engine.create_sql_patterns_heatmap(data))
        ])
    
    def create_issues_tab(self, data: Dict[str, Any]) -> html.Div:
        """Tab de issues"""
        return html.Div([
            dcc.Graph(figure=self.viz_engine.create_issues_breakdown(data))
        ])
    
    def create_dependencies_tab(self, data: Dict[str, Any]) -> html.Div:
        """Tab de dependências"""
        return html.Div([
            dcc.Graph(figure=self.viz_engine.create_dependency_network(data))
        ])
    
    def start_server(self, debug: bool = False):
        """Inicia servidor do dashboard"""
        def run_server():
            self.app.run_server(debug=debug, port=self.port, host='0.0.0.0')
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        print(f"🌐 Dashboard started at http://localhost:{self.port}")
        print("Press Ctrl+C to stop")
    
    def stop_server(self):
        """Para servidor do dashboard"""
        # O Dash não tem um método direto para parar o servidor
        # A thread é daemon, então ela será encerrada quando o programa principal terminar
        pass


# Gerador de relatórios estáticos
class StaticReportGenerator:
    """Gerador de relatórios estáticos em HTML"""
    
    def __init__(self, data_processor: DataProcessor, viz_engine: VisualizationEngine):
        self.data_processor = data_processor
        self.viz_engine = viz_engine
    
    def generate_html_report(self, output_path: str, data: Dict[str, Any]):
        """Gera relatório HTML completo"""
        
        # Cria todas as visualizações
        charts = {
            'table_distribution': self.viz_engine.create_table_distribution_chart(data),
            'file_types': self.viz_engine.create_file_type_pie_chart(data),
            'performance': self.viz_engine.create_performance_timeline(data),
            'sql_patterns': self.viz_engine.create_sql_patterns_heatmap(data),
            'issues': self.viz_engine.create_issues_breakdown(data),
            'dependencies': self.viz_engine.create_dependency_network(data)
        }
        
        # Template HTML
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>BW Automate - Relatório de Análise</title>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background-color: #1e1e1e; color: white; }
                .container { max-width: 1200px; }
                .chart-container { margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="text-center my-4">🚀 BW Automate - Relatório de Análise</h1>
                <p class="text-center text-muted">Gerado em: {timestamp}</p>
                
                <div class="row">
                    <div class="col-md-6 chart-container">
                        <div id="table-distribution"></div>
                    </div>
                    <div class="col-md-6 chart-container">
                        <div id="file-types"></div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12 chart-container">
                        <div id="performance"></div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6 chart-container">
                        <div id="sql-patterns"></div>
                    </div>
                    <div class="col-md-6 chart-container">
                        <div id="issues"></div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12 chart-container">
                        <div id="dependencies"></div>
                    </div>
                </div>
            </div>
            
            <script>
                // Renderiza gráficos
                {scripts}
            </script>
        </body>
        </html>
        """
        
        # Gera scripts para cada gráfico
        scripts = []
        for chart_id, figure in charts.items():
            chart_json = figure.to_json()
            scripts.append(f"Plotly.newPlot('{chart_id.replace('_', '-')}', {chart_json});")
        
        # Substitui placeholders
        html_content = html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            scripts='\n'.join(scripts)
        )
        
        # Salva arquivo
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Relatório HTML gerado: {output_path}")


# Exemplo de uso
if __name__ == "__main__":
    import argparse
    import webbrowser
    
    parser = argparse.ArgumentParser(description="BW Automate Advanced Visualization Dashboard")
    parser.add_argument("data_dir", help="Diretório com dados de análise")
    parser.add_argument("--port", "-p", type=int, default=8050, help="Porta do dashboard")
    parser.add_argument("--static", "-s", help="Gerar relatório HTML estático")
    parser.add_argument("--no-browser", action="store_true", help="Não abrir browser automaticamente")
    
    args = parser.parse_args()
    
    # Cria dashboard
    dashboard = InteractiveDashboard(args.data_dir, args.port)
    
    if args.static:
        # Modo relatório estático
        data_processor = DataProcessor(args.data_dir)
        viz_engine = VisualizationEngine(data_processor)
        report_generator = StaticReportGenerator(data_processor, viz_engine)
        
        data = data_processor.load_analysis_results()
        report_generator.generate_html_report(args.static, data)
        
        if not args.no_browser:
            webbrowser.open(f"file://{Path(args.static).absolute()}")
    else:
        # Modo dashboard interativo
        dashboard.start_server(debug=False)
        
        if not args.no_browser:
            time.sleep(2)  # Aguarda servidor iniciar
            webbrowser.open(f"http://localhost:{args.port}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping dashboard...")
            dashboard.stop_server()
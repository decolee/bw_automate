#!/usr/bin/env python3
"""
Enhanced Report Generator v2.0
===============================

Gerador de relatórios aprimorado com análises mais detalhadas,
visualizações interativas e explicações compreensivas.

Principais melhorias:
- Relatórios mais explicativos
- Análises de tendências
- Recomendações inteligentes
- Visualizações interativas aprimoradas
- Detecção de anomalias
- Métricas de qualidade de dados

Autor: BW_AUTOMATE v2.0
Data: 2025-09-20
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path

# Importações opcionais com fallback
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly não disponível - gráficos interativos desabilitados")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib/Seaborn não disponível - gráficos estáticos desabilitados")

class EnhancedReportGenerator:
    """
    Gerador de relatórios aprimorado com análises detalhadas
    """
    
    def __init__(self, output_dir: str = "BW_AUTOMATE/reports"):
        """
        Inicializa o gerador de relatórios
        
        Args:
            output_dir: Diretório de saída dos relatórios
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurações de estilo
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'success': '#F18F01',
            'warning': '#C73E1D',
            'info': '#5D737E',
            'light': '#F5F5F5',
            'dark': '#2C3E50'
        }
        
        self.setup_logging()
        
    def setup_logging(self):
        """Configura logging para o gerador"""
        self.logger = logging.getLogger('EnhancedReportGenerator')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def generate_comprehensive_analysis_report(self, 
                                             analysis_results: List[Any],
                                             mapping_summary: Dict[str, Any],
                                             sql_analysis: Dict[str, Any],
                                             performance_metrics: Dict[str, Any] = None) -> str:
        """
        Gera relatório abrangente com análises detalhadas
        
        Args:
            analysis_results: Resultados da análise de arquivos
            mapping_summary: Resumo do mapeamento de tabelas
            sql_analysis: Análise SQL detalhada
            performance_metrics: Métricas de performance (opcional)
            
        Returns:
            Caminho do arquivo de relatório gerado
        """
        self.logger.info("Gerando relatório abrangente...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.output_dir / f"comprehensive_analysis_{timestamp}.html"
        
        # Prepara dados para análise
        data_summary = self._prepare_data_summary(analysis_results, mapping_summary, sql_analysis)
        quality_analysis = self._analyze_data_quality(analysis_results, mapping_summary)
        trend_analysis = self._analyze_trends(analysis_results, sql_analysis)
        recommendations = self._generate_smart_recommendations(data_summary, quality_analysis)
        
        # Gera visualizações
        charts_html = self._generate_enhanced_charts(data_summary, quality_analysis)
        
        # Constrói HTML do relatório
        html_content = self._build_comprehensive_html(
            data_summary=data_summary,
            quality_analysis=quality_analysis,
            trend_analysis=trend_analysis,
            recommendations=recommendations,
            charts_html=charts_html,
            performance_metrics=performance_metrics
        )
        
        # Salva relatório
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Relatório abrangente gerado: {report_path}")
        return str(report_path)
    
    def _prepare_data_summary(self, analysis_results: List[Any], 
                            mapping_summary: Dict[str, Any], 
                            sql_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara resumo dos dados para análise"""
        
        # Coleta estatísticas básicas
        total_files = len(analysis_results)
        total_tables_found = len(mapping_summary.get('found_tables', []))
        total_sql_statements = len(sql_analysis.get('statements', []))
        
        # Análise por schema
        schema_stats = {}
        table_by_schema = {}
        
        for table_info in mapping_summary.get('found_tables', []):
            schema = table_info.get('schema', 'public')
            if schema not in schema_stats:
                schema_stats[schema] = {'read': 0, 'write': 0, 'total': 0}
                table_by_schema[schema] = set()
            
            operation = table_info.get('operation', 'READ')
            if operation.upper() in ['READ', 'SELECT']:
                schema_stats[schema]['read'] += 1
            elif operation.upper() in ['WRITE', 'INSERT', 'UPDATE', 'DELETE']:
                schema_stats[schema]['write'] += 1
            
            schema_stats[schema]['total'] += 1
            table_by_schema[schema].add(table_info.get('name', ''))
        
        # Análise de complexidade SQL
        sql_complexity = {
            'simple': 0,  # SELECT/INSERT básicos
            'medium': 0,  # JOINs, WHERE complexos
            'complex': 0,  # CTEs, subqueries, window functions
            'very_complex': 0  # Múltiplas CTEs, funções avançadas
        }
        
        for stmt in sql_analysis.get('statements', []):
            content = stmt.get('content', '').upper()
            complexity_score = 0
            
            # Pontuação baseada em padrões SQL
            if 'WITH' in content:
                complexity_score += 3
            if 'JOIN' in content:
                complexity_score += 2
            if 'WINDOW' in content or 'OVER(' in content:
                complexity_score += 3
            if 'CASE WHEN' in content:
                complexity_score += 1
            if content.count('SELECT') > 1:  # Subqueries
                complexity_score += 2
            
            if complexity_score >= 6:
                sql_complexity['very_complex'] += 1
            elif complexity_score >= 4:
                sql_complexity['complex'] += 1
            elif complexity_score >= 2:
                sql_complexity['medium'] += 1
            else:
                sql_complexity['simple'] += 1
        
        # Análise temporal
        file_dates = []
        for analysis in analysis_results:
            if hasattr(analysis, 'analysis_timestamp'):
                try:
                    file_dates.append(pd.to_datetime(analysis.analysis_timestamp))
                except:
                    pass
        
        temporal_analysis = {
            'analysis_period': {
                'start': min(file_dates).strftime('%Y-%m-%d') if file_dates else 'N/A',
                'end': max(file_dates).strftime('%Y-%m-%d') if file_dates else 'N/A',
                'span_days': (max(file_dates) - min(file_dates)).days if len(file_dates) > 1 else 0
            }
        }
        
        return {
            'overview': {
                'total_files_analyzed': total_files,
                'total_tables_found': total_tables_found,
                'total_sql_statements': total_sql_statements,
                'unique_schemas': len(schema_stats),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'schema_breakdown': schema_stats,
            'tables_by_schema': {k: list(v) for k, v in table_by_schema.items()},
            'sql_complexity_analysis': sql_complexity,
            'temporal_analysis': temporal_analysis,
            'quality_metrics': mapping_summary.get('quality_metrics', {})
        }
    
    def _analyze_data_quality(self, analysis_results: List[Any], 
                            mapping_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa qualidade dos dados encontrados"""
        
        quality_issues = []
        quality_score = 100.0
        
        # Verifica problemas comuns
        found_tables = mapping_summary.get('found_tables', [])
        
        # 1. Tabelas sem schema definido
        tables_without_schema = [t for t in found_tables if not t.get('schema') or t.get('schema') == 'unknown']
        if tables_without_schema:
            issue_pct = len(tables_without_schema) / len(found_tables) * 100
            quality_issues.append({
                'type': 'missing_schema',
                'severity': 'medium',
                'description': f'{len(tables_without_schema)} tabelas ({issue_pct:.1f}%) sem schema definido',
                'impact': 'Pode indicar problemas de organização ou detecção',
                'recommendation': 'Verifique a estrutura dos schemas e padrões de nomenclatura'
            })
            quality_score -= min(issue_pct * 0.5, 15)
        
        # 2. Baixa confiança no matching
        low_confidence_matches = [t for t in found_tables if t.get('confidence', 100) < 70]
        if low_confidence_matches:
            issue_pct = len(low_confidence_matches) / len(found_tables) * 100
            quality_issues.append({
                'type': 'low_confidence_matching',
                'severity': 'high',
                'description': f'{len(low_confidence_matches)} tabelas ({issue_pct:.1f}%) com baixa confiança no matching',
                'impact': 'Pode indicar tabelas não catalogadas ou nomenclatura inconsistente',
                'recommendation': 'Revisar catálogo de tabelas e padrões de nomenclatura'
            })
            quality_score -= min(issue_pct * 0.8, 25)
        
        # 3. Muitas tabelas temporárias
        temp_tables = [t for t in found_tables if t.get('is_temporary', False)]
        if temp_tables:
            temp_pct = len(temp_tables) / len(found_tables) * 100
            if temp_pct > 20:  # Mais de 20% são temporárias
                quality_issues.append({
                    'type': 'high_temp_table_usage',
                    'severity': 'medium',
                    'description': f'{len(temp_tables)} tabelas temporárias ({temp_pct:.1f}% do total)',
                    'impact': 'Alto uso de tabelas temporárias pode indicar problemas de design',
                    'recommendation': 'Considere consolidar processamento ou usar views'
                })
                quality_score -= min((temp_pct - 20) * 0.3, 10)
        
        # 4. Diversidade de schemas
        unique_schemas = len(set(t.get('schema', 'public') for t in found_tables))
        if unique_schemas > 10:
            quality_issues.append({
                'type': 'schema_proliferation',
                'severity': 'low',
                'description': f'{unique_schemas} schemas diferentes encontrados',
                'impact': 'Muitos schemas podem dificultar a governança',
                'recommendation': 'Considere consolidar schemas relacionados'
            })
            quality_score -= min((unique_schemas - 10) * 0.5, 5)
        
        # 5. Análise de padrões de nomes
        table_names = [t.get('name', '') for t in found_tables if t.get('name')]
        naming_patterns = {
            'snake_case': sum(1 for name in table_names if '_' in name and name.islower()),
            'camelCase': sum(1 for name in table_names if any(c.isupper() for c in name[1:]) and '_' not in name),
            'mixed': 0
        }
        naming_patterns['mixed'] = len(table_names) - naming_patterns['snake_case'] - naming_patterns['camelCase']
        
        if naming_patterns['mixed'] > len(table_names) * 0.1:  # Mais de 10% com padrões mistos
            quality_issues.append({
                'type': 'inconsistent_naming',
                'severity': 'medium',
                'description': f'Padrões de nomenclatura inconsistentes detectados',
                'impact': 'Dificulta manutenção e compreensão do código',
                'recommendation': 'Estabelecer e seguir padrão de nomenclatura único'
            })
            quality_score -= 8
        
        # Classificação final da qualidade
        if quality_score >= 90:
            quality_level = 'Excelente'
            quality_color = 'success'
        elif quality_score >= 75:
            quality_level = 'Boa'
            quality_color = 'info'
        elif quality_score >= 60:
            quality_level = 'Regular'
            quality_color = 'warning'
        else:
            quality_level = 'Ruim'
            quality_color = 'danger'
        
        return {
            'overall_score': round(quality_score, 1),
            'quality_level': quality_level,
            'quality_color': quality_color,
            'issues_found': quality_issues,
            'issue_count_by_severity': {
                'high': len([i for i in quality_issues if i['severity'] == 'high']),
                'medium': len([i for i in quality_issues if i['severity'] == 'medium']),
                'low': len([i for i in quality_issues if i['severity'] == 'low'])
            },
            'naming_analysis': naming_patterns,
            'recommendations_count': len(quality_issues)
        }
    
    def _analyze_trends(self, analysis_results: List[Any], 
                       sql_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa tendências nos dados"""
        
        # Análise de tendências de uso por tipo de operação
        operations_trend = {}
        tables_usage_trend = {}
        
        for analysis in analysis_results:
            if hasattr(analysis, 'tables_read'):
                for table in analysis.tables_read:
                    table_name = f"{table.schema}.{table.name}" if table.schema else table.name
                    tables_usage_trend[table_name] = tables_usage_trend.get(table_name, 0) + 1
                    operations_trend['read'] = operations_trend.get('read', 0) + 1
            
            if hasattr(analysis, 'tables_written'):
                for table in analysis.tables_written:
                    table_name = f"{table.schema}.{table.name}" if table.schema else table.name
                    tables_usage_trend[table_name] = tables_usage_trend.get(table_name, 0) + 1
                    operations_trend['write'] = operations_trend.get('write', 0) + 1
        
        # Top tabelas mais usadas
        most_used_tables = sorted(tables_usage_trend.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Análise de complexidade SQL ao longo do tempo
        sql_statements = sql_analysis.get('statements', [])
        complexity_over_time = []
        
        for stmt in sql_statements:
            complexity_score = self._calculate_sql_complexity_score(stmt.get('content', ''))
            complexity_over_time.append({
                'file': stmt.get('file_path', 'unknown'),
                'complexity': complexity_score
            })
        
        return {
            'operations_distribution': operations_trend,
            'most_used_tables': most_used_tables,
            'table_usage_stats': {
                'total_unique_tables': len(tables_usage_trend),
                'avg_usage_per_table': np.mean(list(tables_usage_trend.values())) if tables_usage_trend else 0,
                'max_usage': max(tables_usage_trend.values()) if tables_usage_trend else 0
            },
            'sql_complexity_trends': complexity_over_time
        }
    
    def _calculate_sql_complexity_score(self, sql_content: str) -> int:
        """Calcula score de complexidade SQL"""
        content = sql_content.upper()
        score = 0
        
        # Padrões que aumentam complexidade
        complexity_patterns = {
            'WITH': 3,  # CTEs
            'JOIN': 2,  # Joins
            'WINDOW': 3,  # Window functions
            'CASE WHEN': 1,  # Case statements
            'UNION': 2,  # Union operations
            'EXISTS': 2,  # Exists subqueries
            'GROUP BY': 1,  # Grouping
            'ORDER BY': 1,  # Ordering
            'HAVING': 2   # Having clauses
        }
        
        for pattern, points in complexity_patterns.items():
            score += content.count(pattern) * points
        
        # Subqueries (aproximação)
        score += max(0, content.count('SELECT') - 1) * 2
        
        return score
    
    def _generate_smart_recommendations(self, data_summary: Dict[str, Any], 
                                      quality_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera recomendações inteligentes baseadas na análise"""
        
        recommendations = []
        
        # Recomendações baseadas na qualidade
        for issue in quality_analysis.get('issues_found', []):
            recommendations.append({
                'category': 'Qualidade de Dados',
                'priority': issue['severity'],
                'title': issue['description'],
                'description': issue['impact'],
                'action': issue['recommendation'],
                'type': 'quality_improvement'
            })
        
        # Recomendações baseadas em complexidade SQL
        sql_complexity = data_summary.get('sql_complexity_analysis', {})
        complex_queries = sql_complexity.get('complex', 0) + sql_complexity.get('very_complex', 0)
        total_queries = sum(sql_complexity.values())
        
        if total_queries > 0 and complex_queries / total_queries > 0.3:
            recommendations.append({
                'category': 'Performance',
                'priority': 'medium',
                'title': f'{complex_queries} queries complexas detectadas ({complex_queries/total_queries*100:.1f}%)',
                'description': 'Alto número de queries complexas pode impactar performance',
                'action': 'Considere otimizar queries complexas, criar views ou procedures',
                'type': 'performance_optimization'
            })
        
        # Recomendações baseadas em schemas
        unique_schemas = data_summary['overview']['unique_schemas']
        if unique_schemas > 5:
            recommendations.append({
                'category': 'Arquitetura',
                'priority': 'low',
                'title': f'{unique_schemas} schemas diferentes em uso',
                'description': 'Muitos schemas podem indicar falta de padronização',
                'action': 'Revisar arquitetura de dados e consolidar schemas relacionados',
                'type': 'architecture_review'
            })
        
        # Recomendações baseadas em uso de tabelas
        schema_stats = data_summary.get('schema_breakdown', {})
        for schema, stats in schema_stats.items():
            read_write_ratio = stats['read'] / max(stats['write'], 1)
            
            if read_write_ratio > 10:  # Muito mais leitura que escrita
                recommendations.append({
                    'category': 'Otimização',
                    'priority': 'low',
                    'title': f'Schema "{schema}" com alto ratio leitura/escrita ({read_write_ratio:.1f})',
                    'description': 'Considere estratégias de cache ou materialização',
                    'action': 'Implementar cache, views materializadas ou réplicas de leitura',
                    'type': 'caching_strategy'
                })
        
        # Ordena recomendações por prioridade
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return recommendations[:15]  # Limita a 15 recomendações
    
    def _generate_enhanced_charts(self, data_summary: Dict[str, Any], 
                                quality_analysis: Dict[str, Any]) -> str:
        """Gera gráficos interativos aprimorados"""
        
        if not PLOTLY_AVAILABLE:
            return "<p>Gráficos interativos não disponíveis (Plotly não instalado)</p>"
        
        charts_html = ""
        
        # 1. Gráfico de distribuição por schema
        schema_data = data_summary.get('schema_breakdown', {})
        if schema_data:
            schemas = list(schema_data.keys())
            reads = [schema_data[s]['read'] for s in schemas]
            writes = [schema_data[s]['write'] for s in schemas]
            
            fig = go.Figure(data=[
                go.Bar(name='Leituras', x=schemas, y=reads, marker_color=self.colors['primary']),
                go.Bar(name='Escritas', x=schemas, y=writes, marker_color=self.colors['secondary'])
            ])
            
            fig.update_layout(
                title='Distribuição de Operações por Schema',
                xaxis_title='Schema',
                yaxis_title='Número de Operações',
                barmode='group',
                template='plotly_white'
            )
            
            charts_html += f'<div id="schema-chart">{fig.to_html(div_id="schema-chart", include_plotlyjs=False)}</div>'
        
        # 2. Gráfico de complexidade SQL
        sql_complexity = data_summary.get('sql_complexity_analysis', {})
        if sql_complexity:
            labels = ['Simples', 'Médio', 'Complexo', 'Muito Complexo']
            values = [
                sql_complexity.get('simple', 0),
                sql_complexity.get('medium', 0),
                sql_complexity.get('complex', 0),
                sql_complexity.get('very_complex', 0)
            ]
            
            colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
            
            fig = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values,
                marker_colors=colors,
                textinfo='label+percent+value'
            )])
            
            fig.update_layout(
                title='Distribuição de Complexidade SQL',
                template='plotly_white'
            )
            
            charts_html += f'<div id="complexity-chart">{fig.to_html(div_id="complexity-chart", include_plotlyjs=False)}</div>'
        
        # 3. Gauge de qualidade
        quality_score = quality_analysis.get('overall_score', 0)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = quality_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Score de Qualidade dos Dados"},
            delta = {'reference': 80, 'increasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(template='plotly_white')
        charts_html += f'<div id="quality-gauge">{fig.to_html(div_id="quality-gauge", include_plotlyjs=False)}</div>'
        
        return charts_html
    
    def _build_comprehensive_html(self, **kwargs) -> str:
        """Constrói HTML completo do relatório"""
        
        data_summary = kwargs.get('data_summary', {})
        quality_analysis = kwargs.get('quality_analysis', {})
        trend_analysis = kwargs.get('trend_analysis', {})
        recommendations = kwargs.get('recommendations', [])
        charts_html = kwargs.get('charts_html', '')
        performance_metrics = kwargs.get('performance_metrics', {})
        
        overview = data_summary.get('overview', {})
        
        # Inicia HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>BW_AUTOMATE - Relatório Abrangente</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                .header-bg {{ background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']}); }}
                .metric-card {{ transition: transform 0.2s; }}
                .metric-card:hover {{ transform: translateY(-5px); }}
                .quality-score {{ font-size: 2.5rem; font-weight: bold; }}
                .recommendation-card {{ border-left: 4px solid; }}
                .recommendation-high {{ border-left-color: #dc3545; }}
                .recommendation-medium {{ border-left-color: #ffc107; }}
                .recommendation-low {{ border-left-color: #28a745; }}
                .chart-container {{ margin: 20px 0; }}
                .section-divider {{ border-top: 3px solid {self.colors['primary']}; margin: 30px 0; }}
            </style>
        </head>
        <body>
            <!-- Header -->
            <div class="header-bg text-white py-5">
                <div class="container">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1 class="display-4 mb-0"><i class="fas fa-chart-line me-3"></i>BW_AUTOMATE</h1>
                            <p class="lead mb-0">Relatório Abrangente de Análise PostgreSQL/Airflow</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="bg-white bg-opacity-20 rounded p-3">
                                <h5 class="mb-1">Análise Realizada em:</h5>
                                <p class="mb-0">{datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """
        
        # Seção de Métricas Principais
        html += f"""
            <!-- Métricas Principais -->
            <div class="container my-5">
                <h2 class="mb-4"><i class="fas fa-tachometer-alt me-2"></i>Resumo Executivo</h2>
                <div class="row g-4">
                    <div class="col-md-3">
                        <div class="card metric-card h-100 border-0 shadow">
                            <div class="card-body text-center">
                                <i class="fas fa-file-code fa-3x text-primary mb-3"></i>
                                <h3 class="card-title">{overview.get('total_files_analyzed', 0)}</h3>
                                <p class="card-text">Arquivos Analisados</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card h-100 border-0 shadow">
                            <div class="card-body text-center">
                                <i class="fas fa-database fa-3x text-success mb-3"></i>
                                <h3 class="card-title">{overview.get('total_tables_found', 0)}</h3>
                                <p class="card-text">Tabelas Identificadas</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card h-100 border-0 shadow">
                            <div class="card-body text-center">
                                <i class="fas fa-code fa-3x text-warning mb-3"></i>
                                <h3 class="card-title">{overview.get('total_sql_statements', 0)}</h3>
                                <p class="card-text">Statements SQL</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card metric-card h-100 border-0 shadow">
                            <div class="card-body text-center">
                                <i class="fas fa-layer-group fa-3x text-info mb-3"></i>
                                <h3 class="card-title">{overview.get('unique_schemas', 0)}</h3>
                                <p class="card-text">Schemas Únicos</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """
        
        # Seção de Qualidade
        quality_score = quality_analysis.get('overall_score', 0)
        quality_level = quality_analysis.get('quality_level', 'N/A')
        quality_color = quality_analysis.get('quality_color', 'secondary')
        
        html += f"""
            <!-- Análise de Qualidade -->
            <div class="section-divider"></div>
            <div class="container my-5">
                <h2 class="mb-4"><i class="fas fa-medal me-2"></i>Análise de Qualidade dos Dados</h2>
                <div class="row">
                    <div class="col-md-4">
                        <div class="card border-0 shadow text-center">
                            <div class="card-body">
                                <div class="quality-score text-{quality_color}">{quality_score}%</div>
                                <h5 class="mt-2">Qualidade: {quality_level}</h5>
                                <div class="progress mt-3">
                                    <div class="progress-bar bg-{quality_color}" style="width: {quality_score}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <div class="card border-0 shadow">
                            <div class="card-body">
                                <h6 class="card-title">Problemas Identificados por Severidade</h6>
                                <div class="row text-center">
                                    <div class="col-4">
                                        <div class="text-danger">
                                            <i class="fas fa-exclamation-triangle fa-2x"></i>
                                            <h4>{quality_analysis.get('issue_count_by_severity', {}).get('high', 0)}</h4>
                                            <small>Alto</small>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="text-warning">
                                            <i class="fas fa-exclamation-circle fa-2x"></i>
                                            <h4>{quality_analysis.get('issue_count_by_severity', {}).get('medium', 0)}</h4>
                                            <small>Médio</small>
                                        </div>
                                    </div>
                                    <div class="col-4">
                                        <div class="text-info">
                                            <i class="fas fa-info-circle fa-2x"></i>
                                            <h4>{quality_analysis.get('issue_count_by_severity', {}).get('low', 0)}</h4>
                                            <small>Baixo</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """
        
        # Seção de Gráficos
        if charts_html:
            html += f"""
                <!-- Visualizações -->
                <div class="section-divider"></div>
                <div class="container my-5">
                    <h2 class="mb-4"><i class="fas fa-chart-bar me-2"></i>Análises Visuais</h2>
                    <div class="chart-container">
                        {charts_html}
                    </div>
                </div>
            """
        
        # Seção de Recomendações
        if recommendations:
            html += f"""
                <!-- Recomendações -->
                <div class="section-divider"></div>
                <div class="container my-5">
                    <h2 class="mb-4"><i class="fas fa-lightbulb me-2"></i>Recomendações Inteligentes</h2>
                    <div class="row">
            """
            
            for i, rec in enumerate(recommendations):
                priority_class = f"recommendation-{rec['priority']}"
                priority_icon = {
                    'high': 'fas fa-exclamation-triangle text-danger',
                    'medium': 'fas fa-exclamation-circle text-warning', 
                    'low': 'fas fa-info-circle text-info'
                }.get(rec['priority'], 'fas fa-info-circle')
                
                html += f"""
                    <div class="col-md-6 mb-3">
                        <div class="card recommendation-card {priority_class} border-0 shadow h-100">
                            <div class="card-body">
                                <div class="d-flex align-items-start">
                                    <i class="{priority_icon} fa-lg me-3 mt-1"></i>
                                    <div>
                                        <h6 class="card-title mb-2">{rec['title']}</h6>
                                        <p class="card-text small text-muted mb-2">{rec['description']}</p>
                                        <p class="card-text"><strong>Ação:</strong> {rec['action']}</p>
                                        <span class="badge bg-secondary">{rec['category']}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                """
            
            html += "</div></div>"
        
        # Seção de Detalhes Técnicos
        html += f"""
            <!-- Detalhes Técnicos -->
            <div class="section-divider"></div>
            <div class="container my-5">
                <h2 class="mb-4"><i class="fas fa-cogs me-2"></i>Detalhes Técnicos</h2>
                <div class="row">
                    <div class="col-md-6">
                        <div class="card border-0 shadow">
                            <div class="card-header bg-primary text-white">
                                <h5 class="mb-0">Distribuição por Schema</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Schema</th>
                                                <th>Leituras</th>
                                                <th>Escritas</th>
                                                <th>Total</th>
                                            </tr>
                                        </thead>
                                        <tbody>
        """
        
        for schema, stats in data_summary.get('schema_breakdown', {}).items():
            html += f"""
                                            <tr>
                                                <td><code>{schema}</code></td>
                                                <td>{stats.get('read', 0)}</td>
                                                <td>{stats.get('write', 0)}</td>
                                                <td><strong>{stats.get('total', 0)}</strong></td>
                                            </tr>
            """
        
        html += """
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card border-0 shadow">
                            <div class="card-header bg-success text-white">
                                <h5 class="mb-0">Análise de Complexidade SQL</h5>
                            </div>
                            <div class="card-body">
        """
        
        sql_complexity = data_summary.get('sql_complexity_analysis', {})
        complexity_labels = {'simple': 'Simples', 'medium': 'Médio', 'complex': 'Complexo', 'very_complex': 'Muito Complexo'}
        
        for level, count in sql_complexity.items():
            label = complexity_labels.get(level, level)
            html += f"""
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span>{label}:</span>
                                    <span class="badge bg-primary">{count}</span>
                                </div>
            """
        
        html += """
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """
        
        # Footer
        html += f"""
            <!-- Footer -->
            <footer class="bg-dark text-white py-4 mt-5">
                <div class="container">
                    <div class="row">
                        <div class="col-md-6">
                            <h5>BW_AUTOMATE v2.0</h5>
                            <p>Sistema avançado de análise PostgreSQL/Airflow</p>
                        </div>
                        <div class="col-md-6 text-end">
                            <p>Relatório gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
                            <small>Tempo total de análise: {overview.get('total_files_analyzed', 0)} arquivos processados</small>
                        </div>
                    </div>
                </div>
            </footer>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        
        return html
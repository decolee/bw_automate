#!/usr/bin/env python3
"""
BW_AUTOMATE - Integrated Analyzer v3.5
=======================================

Sistema integrado que combina:
1. Deep Code Analyzer - Rastreamento de call chains
2. Enhanced Matcher - Matching avançado
3. PostgreSQL Table Mapper - Análise SQL
4. Performance Optimizer - Otimização para repos grandes

Objetivo: Taxa de match e confiança máxima possível

Autor: BW_AUTOMATE Team
Data: 2025-10-01
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

# Importa componentes
try:
    from deep_code_analyzer import DeepCodeAnalyzer
    from enhanced_matcher import EnhancedMatcher, MatchResult
    from airflow_table_mapper import PostgreSQLTableMapper
    from real_call_chain_tracer import RealCallChainTracer
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os módulos estão no diretório")


@dataclass
class IntegratedResult:
    """Resultado integrado da análise"""
    file_path: str
    dag_id: Optional[str]
    tables_found: List[Dict]
    call_chains: List[Dict]
    match_quality: Dict[str, float]
    recommendations: List[str]


class IntegratedAnalyzer:
    """
    Analisador integrado com todas as melhorias
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o analisador integrado

        Args:
            config_path: Caminho para configuração
        """
        self.config = self._load_config(config_path)
        self.setup_logging()

        # Componentes
        self.deep_analyzer = None
        self.enhanced_matcher = None
        self.table_mapper = None
        self.real_tracer = None

        # Resultados
        self.results = []
        self.statistics = {}

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Carrega configurações"""
        default_config = {
            "deep_analysis_enabled": False,  # DEPRECATED: Use real_tracer_enabled instead
            "real_tracer_enabled": True,
            "max_call_depth": 20,
            "min_confidence_threshold": 60.0,
            "enable_semantic_matching": True,
            "enable_context_matching": True,
            "cache_enabled": True,
            "parallel_processing": False,  # Implementar depois
            "batch_size": 100,
        }

        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def setup_logging(self):
        """Configura logging"""
        self.logger = logging.getLogger('IntegratedAnalyzer')
        self.logger.setLevel(logging.INFO)

    def analyze_repository(self,
                          source_dir: str,
                          tables_xlsx: str,
                          output_dir: str = "results") -> Dict[str, Any]:
        """
        Análise completa e integrada do repositório

        Args:
            source_dir: Diretório com código Python
            tables_xlsx: Arquivo com tabelas oficiais
            output_dir: Diretório para resultados

        Returns:
            Dicionário com resultados completos

        Raises:
            ValueError: Se inputs forem inválidos
            FileNotFoundError: Se arquivos/diretórios não existirem
        """
        # Validação de inputs
        self._validate_inputs(source_dir, tables_xlsx, output_dir)

        self.logger.info("="*80)
        self.logger.info("🚀 INICIANDO ANÁLISE INTEGRADA v3.5")
        self.logger.info("="*80)

        start_time = datetime.now()

        # FASE 1: Carrega tabelas oficiais
        self.logger.info("\n📊 FASE 1: Carregando tabelas oficiais...")
        official_tables = self._load_official_tables(tables_xlsx)
        self.logger.info(f"   ✅ {len(official_tables)} schemas carregados")

        # FASE 2: Análise tradicional (base)
        self.logger.info("\n📝 FASE 2: Análise tradicional de SQL...")
        self.table_mapper = PostgreSQLTableMapper()
        self.table_mapper.load_official_tables(tables_xlsx)
        traditional_results = self.table_mapper.analyze_directory(source_dir)
        self.logger.info(f"   ✅ {len(traditional_results)} arquivos analisados")

        # FASE 3: Análise profunda (deep code) - DEPRECATED
        if self.config['deep_analysis_enabled']:
            self.logger.warning("\n⚠️  AVISO: deep_analysis_enabled está DEPRECATED")
            self.logger.warning("   Use real_tracer_enabled para análise de call chains")
            self.logger.info("\n🔍 FASE 3: Análise profunda (deep code - DEPRECATED)...")
            self.deep_analyzer = DeepCodeAnalyzer(source_dir)
            deep_results = self.deep_analyzer.analyze_repository()
            self.logger.info(f"   ✅ {deep_results['statistics']['call_chains_resolved']} call chains resolvidas")
        else:
            deep_results = {'table_references': []}

        # FASE 3: Real Call Chain Tracer
        self.logger.info("\n🎯 FASE 3: Real Call Chain Tracing (imports + self + dictionaries)...")
        real_tracer_results = {'discoveries': []}
        if self.config['real_tracer_enabled']:
            try:
                self.real_tracer = RealCallChainTracer(source_dir)
                discovered = self.real_tracer.analyze_repository()
                real_tracer_results = {
                    'discoveries': discovered,
                    'total': len(discovered)
                }
                self.logger.info(f"   ✅ {real_tracer_results['total']} tabelas descobertas via call chains reais")
            except Exception as e:
                self.logger.warning(f"   ⚠️ Real tracer falhou: {e}")
                import traceback
                traceback.print_exc()
        else:
            self.logger.info("   ⏭️ Real tracer desabilitado")

        # FASE 4: Enhanced matching
        self.logger.info("\n🎯 FASE 4: Enhanced matching com múltiplas estratégias...")
        self.enhanced_matcher = EnhancedMatcher(official_tables)
        matched_results = self._perform_enhanced_matching(traditional_results, deep_results, real_tracer_results)
        self.logger.info(f"   ✅ Match rate: {matched_results['match_rate']:.1f}%")
        self.logger.info(f"   ✅ Confiança média: {matched_results['avg_confidence']:.1f}%")

        # FASE 5: Consolidação e qualidade
        self.logger.info("\n📈 FASE 5: Consolidação e análise de qualidade...")
        final_results = self._consolidate_results(traditional_results, deep_results, matched_results, real_tracer_results)

        # FASE 6: Geração de relatórios
        self.logger.info("\n📄 FASE 6: Gerando relatórios aprimorados...")
        os.makedirs(output_dir, exist_ok=True)
        self._generate_enhanced_reports(final_results, output_dir)

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        self.logger.info("\n" + "="*80)
        self.logger.info(f"✅ ANÁLISE CONCLUÍDA EM {elapsed:.2f}s")
        self.logger.info("="*80)

        return final_results

    def _validate_inputs(self, source_dir: str, tables_xlsx: str, output_dir: str):
        """
        Valida inputs antes de iniciar análise

        Args:
            source_dir: Diretório de código
            tables_xlsx: Arquivo Excel com tabelas
            output_dir: Diretório de saída

        Raises:
            ValueError: Se inputs inválidos
            FileNotFoundError: Se arquivos/diretórios não existem
        """
        # Valida source_dir
        if not source_dir:
            raise ValueError("source_dir não pode ser vazio")

        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Diretório não encontrado: {source_dir}")

        if not source_path.is_dir():
            raise ValueError(f"source_dir deve ser um diretório: {source_dir}")

        # Conta arquivos Python
        py_files = list(source_path.rglob("*.py"))
        if len(py_files) == 0:
            raise ValueError(f"Nenhum arquivo Python encontrado em: {source_dir}")

        self.logger.info(f"✓ Validado: {len(py_files)} arquivos Python em {source_dir}")

        # Valida tables_xlsx
        if not tables_xlsx:
            raise ValueError("tables_xlsx não pode ser vazio")

        tables_path = Path(tables_xlsx)
        if not tables_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {tables_xlsx}")

        if not tables_path.is_file():
            raise ValueError(f"tables_xlsx deve ser um arquivo: {tables_xlsx}")

        if not tables_xlsx.endswith(('.xlsx', '.xls')):
            raise ValueError(f"tables_xlsx deve ser um arquivo Excel (.xlsx/.xls): {tables_xlsx}")

        self.logger.info(f"✓ Validado: {tables_xlsx}")

        # Valida output_dir (cria se não existir)
        if not output_dir:
            raise ValueError("output_dir não pode ser vazio")

        output_path = Path(output_dir)
        if output_path.exists() and not output_path.is_dir():
            raise ValueError(f"output_dir existe mas não é um diretório: {output_dir}")

        self.logger.info(f"✓ Validado: {output_dir}")

    def _load_official_tables(self, xlsx_path: str) -> Dict[str, Set[str]]:
        """
        Carrega tabelas oficiais do Excel

        Args:
            xlsx_path: Caminho do arquivo

        Returns:
            Dict com {schema: set(tabelas)}
        """
        import pandas as pd

        df = pd.read_excel(xlsx_path)

        # Identifica colunas
        table_col = None
        schema_col = None

        for col in df.columns:
            if 'table' in col.lower() or 'tabela' in col.lower():
                table_col = col
            if 'schema' in col.lower() or 'esquema' in col.lower():
                schema_col = col

        if not table_col:
            table_col = df.columns[0]

        # Organiza por schema
        tables_by_schema = defaultdict(set)

        for _, row in df.iterrows():
            table_name = str(row[table_col]).strip()
            schema = str(row[schema_col]).strip() if schema_col else 'public'

            if table_name and table_name != 'nan':
                tables_by_schema[schema].add(table_name.lower())

        return dict(tables_by_schema)

    def _perform_enhanced_matching(self,
                                   traditional_results: List,
                                   deep_results: Dict,
                                   real_tracer_results: Dict = None) -> Dict[str, Any]:
        """
        Executa enhanced matching em todos os resultados

        Args:
            traditional_results: Resultados da análise tradicional
            deep_results: Resultados da análise profunda
            real_tracer_results: Resultados do real call chain tracer

        Returns:
            Dicionário com resultados do matching
        """
        all_found_tables = []

        # Coleta tabelas da análise tradicional
        for file_result in traditional_results:
            for table_ref in file_result.tables_read + file_result.tables_written:
                all_found_tables.append((table_ref.name, table_ref.schema))

        # Coleta tabelas da análise profunda
        for table_ref in deep_results.get('table_references', []):
            all_found_tables.append((table_ref.table_name, table_ref.schema))

        # Coleta tabelas do real tracer
        if real_tracer_results:
            for discovery in real_tracer_results.get('discoveries', []):
                all_found_tables.append((discovery.table_name, discovery.schema))

        # Remove duplicatas
        unique_tables = list(set(all_found_tables))

        self.logger.info(f"   Processando {len(unique_tables)} tabelas únicas...")

        # Executa matching
        match_results = self.enhanced_matcher.batch_match(unique_tables)

        # Calcula estatísticas
        stats = self.enhanced_matcher.get_statistics(match_results)

        # Log detalhado dos match types
        self.logger.info(f"   ")
        self.logger.info(f"   Match types:")
        for match_type, count in stats['match_types'].items():
            self.logger.info(f"      • {match_type}: {count}")

        return {
            'match_results': match_results,
            'statistics': stats,
            'match_rate': stats['match_rate'],
            'avg_confidence': stats['average_confidence']
        }

    def _consolidate_results(self,
                            traditional_results: List,
                            deep_results: Dict,
                            matched_results: Dict,
                            real_tracer_results: Dict = None) -> Dict[str, Any]:
        """
        Consolida todos os resultados

        Args:
            traditional_results: Resultados tradicionais
            deep_results: Resultados deep code analyzer
            matched_results: Resultados enhanced matching
            real_tracer_results: Resultados real call chain tracer
            deep_results: Resultados profundos
            matched_results: Resultados do matching

        Returns:
            Resultados consolidados
        """
        consolidated = {
            'summary': {
                'total_files': len(traditional_results),
                'total_tables_found': len(matched_results['match_results']),
                'matched_tables': matched_results['statistics']['matched_tables'],
                'match_rate': matched_results['match_rate'],
                'avg_confidence': matched_results['avg_confidence'],
                'deep_call_chains': deep_results.get('statistics', {}).get('call_chains_resolved', 0),
                'real_tracer_discoveries': real_tracer_results.get('total', 0) if real_tracer_results else 0
            },
            'files': [],
            'tables': {},
            'match_details': matched_results,
            'real_tracer_details': real_tracer_results if real_tracer_results else {},
            'recommendations': []
        }

        # Consolida por arquivo
        for file_result in traditional_results:
            file_data = {
                'path': file_result.file_path,
                'dag_id': file_result.dag_id,
                'tables_read': [],
                'tables_written': [],
                'observations': file_result.observations
            }

            # Adiciona tabelas com match aprimorado
            for table_ref in file_result.tables_read:
                match = matched_results['match_results'].get((table_ref.name, table_ref.schema))
                file_data['tables_read'].append({
                    'found': table_ref.name,
                    'matched': match.official_table if match else None,
                    'confidence': match.confidence if match else 0,
                    'match_type': match.match_type if match else 'NO_MATCH',
                    'line': table_ref.line_number,
                    'context': table_ref.context[:100]
                })

            for table_ref in file_result.tables_written:
                match = matched_results['match_results'].get((table_ref.name, table_ref.schema))
                file_data['tables_written'].append({
                    'found': table_ref.name,
                    'matched': match.official_table if match else None,
                    'confidence': match.confidence if match else 0,
                    'match_type': match.match_type if match else 'NO_MATCH',
                    'line': table_ref.line_number,
                    'context': table_ref.context[:100]
                })

            consolidated['files'].append(file_data)

        # Gera recomendações
        consolidated['recommendations'] = self._generate_recommendations(consolidated)

        return consolidated

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []

        match_rate = results['summary']['match_rate']
        avg_conf = results['summary']['avg_confidence']

        if match_rate < 70:
            recommendations.append(
                "⚠️  Taxa de match abaixo de 70% - Revisar nomenclatura de tabelas "
                "ou atualizar lista oficial"
            )

        if avg_conf < 80:
            recommendations.append(
                "⚠️  Confiança média abaixo de 80% - Considerar padronização "
                "de nomes de tabelas no código"
            )

        if match_rate >= 90 and avg_conf >= 90:
            recommendations.append(
                "✅ Excelente qualidade de mapeamento! "
                "Código bem estruturado e nomenclatura consistente"
            )

        return recommendations

    def _generate_enhanced_reports(self, results: Dict, output_dir: str):
        """Gera relatórios aprimorados"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. JSON completo
        json_path = f"{output_dir}/integrated_analysis_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        self.logger.info(f"   ✅ JSON: {json_path}")

        # 2. CSV resumido
        import pandas as pd

        rows = []
        for file_data in results['files']:
            for table in file_data['tables_read'] + file_data['tables_written']:
                rows.append({
                    'arquivo': os.path.basename(file_data['path']),
                    'dag_id': file_data['dag_id'],
                    'tabela_encontrada': table['found'],
                    'tabela_oficial': table['matched'],
                    'confianca': f"{table['confidence']:.1f}%",
                    'match_type': table['match_type'],
                    'linha': table['line']
                })

        df = pd.DataFrame(rows)
        csv_path = f"{output_dir}/enhanced_mapping_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        self.logger.info(f"   ✅ CSV: {csv_path}")

        # 3. Relatório HTML aprimorado
        html_path = f"{output_dir}/enhanced_report_{timestamp}.html"
        self._generate_html_report(results, html_path)
        self.logger.info(f"   ✅ HTML: {html_path}")

    def _generate_html_report(self, results: Dict, output_path: str):
        """Gera relatório HTML aprimorado"""
        summary = results['summary']

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>BW_AUTOMATE v3.5 - Relatório Integrado</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
        h1 {{ margin: 0; font-size: 32px; }}
        .subtitle {{ margin-top: 10px; opacity: 0.9; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
        .metric-value {{ font-size: 36px; font-weight: bold; color: #667eea; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .section {{ margin: 30px 0; }}
        .section-title {{ font-size: 24px; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }}
        .recommendation {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 10px 0; border-radius: 4px; }}
        .success {{ background: #d4edda; border-left-color: #28a745; }}
        .warning {{ background: #fff3cd; border-left-color: #ffc107; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .confidence-high {{ color: #28a745; font-weight: bold; }}
        .confidence-med {{ color: #ffc107; font-weight: bold; }}
        .confidence-low {{ color: #dc3545; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 BW_AUTOMATE v3.5</h1>
            <div class="subtitle">Relatório Integrado de Análise - Enhanced Matching & Deep Code Analysis</div>
        </div>

        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{summary['total_files']}</div>
                <div class="metric-label">Arquivos Analisados</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary['total_tables_found']}</div>
                <div class="metric-label">Tabelas Encontradas</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary['match_rate']:.1f}%</div>
                <div class="metric-label">Taxa de Match</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary['avg_confidence']:.1f}%</div>
                <div class="metric-label">Confiança Média</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">💡 Recomendações</div>
            {"".join(f'<div class="recommendation {"success" if "✅" in rec else "warning"}">{rec}</div>' for rec in results['recommendations'])}
        </div>

        <div class="section">
            <div class="section-title">📊 Detalhamento por Match Type</div>
            <table>
                <tr>
                    <th>Match Type</th>
                    <th>Quantidade</th>
                    <th>Descrição</th>
                </tr>
                {"".join(f'<tr><td>{mt}</td><td>{count}</td><td>{self._get_match_description(mt)}</td></tr>'
                         for mt, count in results['match_details']['statistics']['match_types'].items())}
            </table>
        </div>

        <div class="section">
            <div class="section-title">📝 Análise por Arquivo</div>
            <p>Total: {len(results['files'])} arquivos processados</p>
        </div>
    </div>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    def _get_match_description(self, match_type: str) -> str:
        """Retorna descrição de um match type"""
        descriptions = {
            'EXACT': 'Match exato - 100% confiança',
            'EXACT_WITH_SCHEMA': 'Match exato com schema - 100% confiança',
            'CASE_INSENSITIVE': 'Match ignorando case - 95% confiança',
            'IMPLICIT_SCHEMA': 'Match com schema implícito - 90% confiança',
            'FUZZY': 'Match fuzzy - 75-85% confiança',
            'PATTERN': 'Match por padrão - 70% confiança',
            'SEMANTIC': 'Match semântico - 65% confiança',
            'CONTEXT': 'Match contextual - 60% confiança',
            'NO_MATCH': 'Sem match encontrado'
        }
        return descriptions.get(match_type, 'Desconhecido')


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='BW_AUTOMATE Integrated Analyzer v3.5')
    parser.add_argument('--source-dir', required=True, help='Diretório com código')
    parser.add_argument('--tables-xlsx', required=True, help='Arquivo Excel com tabelas')
    parser.add_argument('--output-dir', default='results_integrated', help='Diretório de saída')
    parser.add_argument('--config', help='Arquivo de configuração')

    args = parser.parse_args()

    analyzer = IntegratedAnalyzer(args.config)
    results = analyzer.analyze_repository(
        source_dir=args.source_dir,
        tables_xlsx=args.tables_xlsx,
        output_dir=args.output_dir
    )

    print("\n✅ Análise concluída!")
    print(f"📊 Match rate: {results['summary']['match_rate']:.1f}%")
    print(f"🔍 Confiança média: {results['summary']['avg_confidence']:.1f}%")


if __name__ == "__main__":
    main()

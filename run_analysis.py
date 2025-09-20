#!/usr/bin/env python3
"""
BW_AUTOMATE - Script Principal de Execução
==========================================

Script principal para execução completa da análise e mapeamento de tabelas PostgreSQL
em códigos Python do Airflow. Integra todos os módulos e gera relatórios completos.

Uso:
    python run_analysis.py --source-dir /path/to/airflow/dags --tables-xlsx /path/to/tables.xlsx

Autor: Assistant Claude
Data: 2025-09-20
"""

import argparse
import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Importa módulos do BW_AUTOMATE
try:
    from airflow_table_mapper import PostgreSQLTableMapper
    from sql_pattern_extractor import AdvancedSQLExtractor
    from table_mapper_engine import TableMappingEngine
    from report_generator import AdvancedReportGenerator
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os módulos estão no mesmo diretório")
    sys.exit(1)


class BWAutomate:
    """
    Classe principal do BW_AUTOMATE - orquestra toda a análise
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o BW_AUTOMATE
        
        Args:
            config_path: Caminho do arquivo de configuração
        """
        self.config = self._load_config(config_path)
        self.setup_logging()
        
        # Inicializa componentes
        self.table_mapper = PostgreSQLTableMapper(config_path)
        self.sql_extractor = AdvancedSQLExtractor()
        self.mapping_engine = TableMappingEngine(self.config)
        self.report_generator = AdvancedReportGenerator(
            output_dir=self.config.get('output_dir', 'BW_AUTOMATE/reports')
        )
        
        # Resultados da análise
        self.analysis_results = []
        self.sql_analysis = {}
        self.mapping_summary = {}
        self.generated_reports = {}
        
        self.logger.info("BW_AUTOMATE inicializado com sucesso")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Carrega configurações"""
        default_config = {
            "fuzzy_match_threshold": 80,
            "include_temp_tables": True,
            "schemas_to_analyze": ["public", "staging", "reports", "analytics"],
            "file_extensions": [".py"],
            "exclude_patterns": ["__pycache__", ".git", "node_modules", ".venv"],
            "log_level": "INFO",
            "output_dir": "BW_AUTOMATE/reports",
            "generate_executive_dashboard": True,
            "generate_technical_report": True,
            "generate_lineage_visualization": True,
            "generate_table_explorer": True,
            "export_to_powerbi": True,
            "max_files_to_analyze": 1000,
            "enable_advanced_sql_analysis": True
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Erro ao carregar configuração: {e}")
        
        return default_config
    
    def setup_logging(self):
        """Configura sistema de logging"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        
        # Cria diretório de logs
        log_dir = "BW_AUTOMATE/logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Configura formatação
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler para arquivo
        file_handler = logging.FileHandler(
            f"{log_dir}/bw_automate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Configura logger principal
        self.logger = logging.getLogger('BW_AUTOMATE')
        self.logger.setLevel(log_level)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Evita duplicação de logs
        self.logger.propagate = False
    
    def run_complete_analysis(self, 
                            source_dir: str, 
                            tables_xlsx: str,
                            output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa análise completa
        
        Args:
            source_dir: Diretório com códigos Python do Airflow
            tables_xlsx: Arquivo XLSX com lista de tabelas oficiais
            output_dir: Diretório de saída (opcional)
            
        Returns:
            Dicionário com resumo da execução e caminhos dos arquivos gerados
        """
        start_time = datetime.now()
        self.logger.info("=== INICIANDO ANÁLISE COMPLETA BW_AUTOMATE ===")
        
        try:
            # Fase 1: Validação de entrada
            self._validate_inputs(source_dir, tables_xlsx)
            
            # Fase 2: Carregamento de tabelas oficiais
            self._load_official_tables(tables_xlsx)
            
            # Fase 3: Análise de arquivos Python
            self._analyze_python_files(source_dir)
            
            # Fase 4: Análise SQL avançada (se habilitada)
            if self.config.get('enable_advanced_sql_analysis', True):
                self._perform_advanced_sql_analysis()
            
            # Fase 5: Mapeamento e matching de tabelas
            self._perform_table_mapping()
            
            # Fase 6: Construção de grafos de dependência
            self._build_dependency_graphs()
            
            # Fase 7: Análise de qualidade de dados
            self._analyze_data_quality()
            
            # Fase 8: Geração de relatórios
            self._generate_all_reports(output_dir)
            
            # Fase 9: Sumário final
            execution_summary = self._generate_execution_summary(start_time)
            
            self.logger.info("=== ANÁLISE COMPLETA FINALIZADA COM SUCESSO ===")
            return execution_summary
            
        except Exception as e:
            self.logger.error(f"Erro durante análise: {e}", exc_info=True)
            raise
    
    def _validate_inputs(self, source_dir: str, tables_xlsx: str):
        """Valida arquivos de entrada"""
        self.logger.info("Validando arquivos de entrada...")
        
        if not os.path.exists(source_dir):
            raise FileNotFoundError(f"Diretório de origem não encontrado: {source_dir}")
        
        if not os.path.exists(tables_xlsx):
            raise FileNotFoundError(f"Arquivo de tabelas não encontrado: {tables_xlsx}")
        
        if not tables_xlsx.endswith(('.xlsx', '.xls')):
            raise ValueError("Arquivo de tabelas deve ser um Excel (.xlsx ou .xls)")
        
        # Verifica se há arquivos Python no diretório
        python_files = list(Path(source_dir).rglob("*.py"))
        if not python_files:
            raise ValueError(f"Nenhum arquivo Python encontrado em: {source_dir}")
        
        self.logger.info(f"Validação concluída: {len(python_files)} arquivos Python encontrados")
    
    def _load_official_tables(self, tables_xlsx: str):
        """Carrega lista oficial de tabelas"""
        self.logger.info("Carregando lista oficial de tabelas...")
        
        # Carrega no mapper principal
        self.table_mapper.load_official_tables(tables_xlsx)
        
        # Carrega no engine de mapeamento
        self.mapping_engine.load_official_tables(tables_xlsx)
        
        self.logger.info("Lista oficial de tabelas carregada com sucesso")
    
    def _analyze_python_files(self, source_dir: str):
        """Analisa arquivos Python"""
        self.logger.info("Iniciando análise de arquivos Python...")
        
        # Limita número de arquivos se configurado
        max_files = self.config.get('max_files_to_analyze', 1000)
        
        # Executa análise
        self.analysis_results = self.table_mapper.analyze_directory(source_dir)
        
        if len(self.analysis_results) > max_files:
            self.logger.warning(f"Limitando análise a {max_files} arquivos")
            self.analysis_results = self.analysis_results[:max_files]
        
        self.logger.info(f"Análise concluída: {len(self.analysis_results)} arquivos processados")
    
    def _perform_advanced_sql_analysis(self):
        """Executa análise SQL avançada"""
        self.logger.info("Executando análise SQL avançada...")
        
        all_sql_statements = []
        
        for analysis in self.analysis_results:
            try:
                with open(analysis.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                statements = self.sql_extractor.extract_sql_statements(content, analysis.file_path)
                all_sql_statements.extend(statements)
                
            except Exception as e:
                self.logger.warning(f"Erro na análise SQL de {analysis.file_path}: {e}")
        
        # Analisa complexidade
        self.sql_analysis = self.sql_extractor.analyze_sql_complexity(all_sql_statements)
        self.sql_analysis['statements'] = all_sql_statements
        
        self.logger.info(f"Análise SQL concluída: {len(all_sql_statements)} statements encontrados")
    
    def _perform_table_mapping(self):
        """Executa mapeamento de tabelas"""
        self.logger.info("Executando mapeamento de tabelas...")
        
        # Processa resultados da análise
        self.mapping_engine.process_analysis_results(self.analysis_results)
        
        # Executa matching
        matches = self.mapping_engine.perform_table_matching()
        
        self.logger.info(f"Mapeamento concluído: {len(matches)} matches realizados")
    
    def _build_dependency_graphs(self):
        """Constrói grafos de dependência"""
        self.logger.info("Construindo grafos de dependência...")
        
        # Constrói grafo de fluxo de dados
        data_flow_graph = self.mapping_engine.build_data_flow_graph(self.analysis_results)
        
        # Constrói grafo de linhagem
        lineage_graph = self.mapping_engine.build_table_lineage_graph()
        
        # Constrói grafo de dependências de DAGs
        dag_dependency_graph = self.table_mapper.build_dependency_graph(self.analysis_results)
        
        self.logger.info("Grafos de dependência construídos com sucesso")
    
    def _analyze_data_quality(self):
        """Analisa qualidade dos dados"""
        self.logger.info("Analisando qualidade dos dados...")
        
        # Gera resumo do mapeamento
        self.mapping_summary = self.mapping_engine.generate_mapping_summary()
        
        self.logger.info("Análise de qualidade concluída")
    
    def _generate_all_reports(self, output_dir: Optional[str]):
        """Gera todos os relatórios"""
        self.logger.info("Gerando relatórios...")
        
        if output_dir:
            self.report_generator.output_dir = output_dir
        
        # Relatório executivo/dashboard
        if self.config.get('generate_executive_dashboard', True):
            try:
                dashboard_path = self.report_generator.generate_executive_dashboard(
                    self.mapping_summary,
                    self.mapping_engine.found_tables
                )
                self.generated_reports['executive_dashboard'] = dashboard_path
            except Exception as e:
                self.logger.error(f"Erro ao gerar dashboard executivo: {e}")
        
        # Relatório técnico
        if self.config.get('generate_technical_report', True):
            try:
                technical_path = self.report_generator.generate_technical_report(
                    self.analysis_results,
                    self.mapping_summary,
                    self.sql_analysis
                )
                self.generated_reports['technical_report'] = technical_path
            except Exception as e:
                self.logger.error(f"Erro ao gerar relatório técnico: {e}")
        
        # Visualização de linhagem
        if self.config.get('generate_lineage_visualization', True):
            try:
                lineage_path = self.report_generator.generate_data_lineage_visualization(
                    self.mapping_engine.table_lineage_graph
                )
                if lineage_path:
                    self.generated_reports['lineage_visualization'] = lineage_path
            except Exception as e:
                self.logger.error(f"Erro ao gerar visualização de linhagem: {e}")
        
        # Explorador de tabelas
        if self.config.get('generate_table_explorer', True):
            try:
                explorer_path = self.report_generator.generate_interactive_table_explorer(
                    self.mapping_engine.found_tables,
                    self.mapping_engine.table_matches
                )
                self.generated_reports['table_explorer'] = explorer_path
            except Exception as e:
                self.logger.error(f"Erro ao gerar explorador de tabelas: {e}")
        
        # Export para Power BI
        if self.config.get('export_to_powerbi', True):
            try:
                powerbi_path = self.report_generator.export_to_powerbi(self.mapping_summary)
                self.generated_reports['powerbi_export'] = powerbi_path
            except Exception as e:
                self.logger.error(f"Erro ao exportar para Power BI: {e}")
        
        # Relatórios básicos do mapper
        try:
            basic_reports = self.table_mapper.generate_comprehensive_report(
                self.report_generator.output_dir
            )
            self.generated_reports.update(basic_reports)
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatórios básicos: {e}")
        
        # Resultados do engine de mapeamento
        try:
            engine_reports = self.mapping_engine.export_results(
                self.report_generator.output_dir
            )
            self.generated_reports.update(engine_reports)
        except Exception as e:
            self.logger.error(f"Erro ao exportar resultados do engine: {e}")
        
        self.logger.info(f"Relatórios gerados: {len(self.generated_reports)} arquivos")
    
    def _generate_execution_summary(self, start_time: datetime) -> Dict[str, Any]:
        """Gera resumo da execução"""
        end_time = datetime.now()
        execution_time = end_time - start_time
        
        summary = {
            'execution_info': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'execution_time_seconds': execution_time.total_seconds(),
                'execution_time_formatted': str(execution_time),
                'version': '1.0.0',
                'config_used': self.config
            },
            'analysis_summary': {
                'files_analyzed': len(self.analysis_results),
                'tables_found': len(self.mapping_engine.found_tables) if hasattr(self.mapping_engine, 'found_tables') else 0,
                'sql_statements_found': len(self.sql_analysis.get('statements', [])),
                'official_tables_loaded': len(self.table_mapper.official_tables),
            },
            'quality_metrics': self.mapping_summary.get('quality_metrics', {}),
            'generated_reports': self.generated_reports,
            'recommendations': self.mapping_summary.get('recommendations', [])
        }
        
        # Salva resumo da execução
        summary_path = f"{self.report_generator.output_dir}/execution_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        self.generated_reports['execution_summary'] = summary_path
        
        return summary
    
    def print_execution_summary(self, summary: Dict[str, Any]):
        """Imprime resumo da execução no console"""
        print("\n" + "="*80)
        print("🎯 BW_AUTOMATE - RESUMO DA EXECUÇÃO")
        print("="*80)
        
        exec_info = summary['execution_info']
        analysis_summary = summary['analysis_summary']
        quality_metrics = summary['quality_metrics']
        
        print(f"⏱️  Tempo de execução: {exec_info['execution_time_formatted']}")
        print(f"📁 Arquivos analisados: {analysis_summary['files_analyzed']}")
        print(f"🗃️  Tabelas encontradas: {analysis_summary['tables_found']}")
        print(f"📊 Statements SQL: {analysis_summary['sql_statements_found']}")
        print(f"📋 Tabelas oficiais: {analysis_summary['official_tables_loaded']}")
        
        if quality_metrics:
            print(f"✅ Taxa de match: {quality_metrics.get('match_rate', 0):.1f}%")
            print(f"🔍 Confiança média: {quality_metrics.get('average_confidence', 0):.1f}%")
        
        print(f"\n📑 Relatórios gerados: {len(self.generated_reports)}")
        for report_type, file_path in self.generated_reports.items():
            print(f"   • {report_type}: {file_path}")
        
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recomendações ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"   {i}. {rec}")
            if len(recommendations) > 5:
                print(f"   ... e mais {len(recommendations) - 5} recomendações")
        
        print("\n" + "="*80)
        print("✨ Análise concluída com sucesso!")
        print("="*80 + "\n")


def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description='BW_AUTOMATE - Mapeamento de Tabelas PostgreSQL em códigos Airflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Análise básica
  python run_analysis.py --source-dir /path/to/airflow/dags --tables-xlsx /path/to/tables.xlsx

  # Com configuração customizada
  python run_analysis.py --source-dir ./dags --tables-xlsx ./tables.xlsx --config ./config.json

  # Especificando diretório de saída
  python run_analysis.py --source-dir ./dags --tables-xlsx ./tables.xlsx --output-dir ./results

Para mais informações, consulte o README.md
        """
    )
    
    parser.add_argument(
        '--source-dir',
        required=True,
        help='Diretório com códigos Python do Airflow'
    )
    
    parser.add_argument(
        '--tables-xlsx',
        required=True,
        help='Arquivo XLSX com lista de tabelas PostgreSQL'
    )
    
    parser.add_argument(
        '--config',
        help='Arquivo de configuração JSON (opcional)'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Diretório de saída dos relatórios (opcional)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso (debug)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='BW_AUTOMATE 1.0.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Inicializa BW_AUTOMATE
        bw_automate = BWAutomate(args.config)
        
        if args.verbose:
            bw_automate.config['log_level'] = 'DEBUG'
            bw_automate.setup_logging()
        
        # Executa análise completa
        summary = bw_automate.run_complete_analysis(
            source_dir=args.source_dir,
            tables_xlsx=args.tables_xlsx,
            output_dir=args.output_dir
        )
        
        # Imprime resumo
        bw_automate.print_execution_summary(summary)
        
        # Retorna código de sucesso
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n❌ Execução interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
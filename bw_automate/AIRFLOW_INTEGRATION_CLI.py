#!/usr/bin/env python3
"""
🚁 AIRFLOW INTEGRATION CLI
CLI específico para análise PostgreSQL em ambientes Airflow
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import enhanced mapper
try:
    from ENHANCED_POSTGRESQL_AIRFLOW_MAPPER import EnhancedPostgreSQLAirflowMapper
    from POSTGRESQL_TABLE_MAPPER import PostgreSQLTableMapper
except ImportError as e:
    print(f"⚠️  Módulo não encontrado: {e}")
    sys.exit(1)

class AirflowIntegrationCLI:
    """CLI integrado para análise PostgreSQL + Airflow"""
    
    def __init__(self):
        self.version = "1.0.0"
    
    def show_banner(self):
        """Mostra banner específico do Airflow"""
        print("🚁 " + "="*60)
        print("🚁 BW_AUTOMATE - AIRFLOW POSTGRESQL ANALYZER")
        print("🚁 " + "="*60)
        print(f"📦 Versão: {self.version}")
        print("🎯 Especializado em:")
        print("   ✅ Análise de códigos Python standalone")
        print("   ✅ DAGs Airflow chamando Pythons")
        print("   ✅ Chains de parâmetros entre arquivos")
        print("   ✅ Decorators, classes e funções interconectadas")
        print()
    
    def analyze_project_enhanced(self, project_path: str, output_dir: str = ".", mode: str = "full") -> Dict[str, Any]:
        """Executa análise com mapper avançado"""
        print("🚁 Iniciando análise avançada (Airflow + PostgreSQL)...")
        
        if mode == "full":
            mapper = EnhancedPostgreSQLAirflowMapper()
            results = mapper.analyze_project(project_path)
            mapper.generate_enhanced_reports(results, output_dir)
        else:
            # Modo simples - só PostgreSQL
            mapper = PostgreSQLTableMapper()
            results = mapper.analyze_project(project_path)
            
            # Salva resultado
            output_file = Path(output_dir) / "postgresql_simple_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def show_analysis_summary(self, results: Dict[str, Any], mode: str = "full"):
        """Mostra resumo da análise"""
        summary = results.get('analysis_summary', {})
        
        print(f"\n📊 RESUMO DA ANÁLISE:")
        print(f"   📁 Arquivos analisados: {summary.get('files_analyzed', 0)}")
        print(f"   🗃️ Tabelas encontradas: {summary.get('unique_tables_found', 0)}")
        print(f"   📊 Total de referências: {summary.get('total_table_references', 0)}")
        print(f"   📂 Esquemas: {len(summary.get('schemas_found', []))}")
        print(f"   ⏱️ Tempo: {summary.get('analysis_time_seconds', 0)}s")
        
        if mode == "full":
            print(f"   🚁 DAGs Airflow: {summary.get('airflow_dags_found', 0)}")
            print(f"   🔗 Fluxos de parâmetros: {summary.get('parameter_flows_detected', 0)}")
            
            # Detalhes de DAGs se houver
            airflow_analysis = results.get('airflow_analysis', {})
            if airflow_analysis.get('total_dags', 0) > 0:
                print(f"\n🚁 DETALHES AIRFLOW:")
                print(f"   📋 Total de DAGs: {airflow_analysis['total_dags']}")
                print(f"   ⚙️ Total de tasks: {airflow_analysis['total_tasks']}")
                
                for dag in airflow_analysis.get('dags', [])[:5]:  # Top 5
                    print(f"   • {dag['dag_id']}: {dag['tasks_count']} tasks")
        
        # Top tabelas
        if 'statistics' in results:
            most_ref = results['statistics'].get('most_referenced_tables', [])
            if most_ref:
                print(f"\n🏆 TOP 5 TABELAS:")
                for item in most_ref[:5]:
                    print(f"   • {item['table']}: {item['references']} refs")
    
    def generate_comparison_report(self, project_path: str, output_dir: str = "."):
        """Gera relatório comparativo entre análise simples e avançada"""
        print("📊 Gerando relatório comparativo...")
        
        # Análise simples
        print("   🔸 Executando análise simples...")
        simple_results = self.analyze_project_enhanced(project_path, output_dir, mode="simple")
        
        # Análise avançada
        print("   🔸 Executando análise avançada...")
        enhanced_results = self.analyze_project_enhanced(project_path, output_dir, mode="full")
        
        # Comparação
        comparison = {
            "analysis_comparison": {
                "simple_analysis": {
                    "tables_found": simple_results.get('analysis_summary', {}).get('unique_tables_found', 0),
                    "references": simple_results.get('analysis_summary', {}).get('total_table_references', 0),
                    "time": simple_results.get('analysis_summary', {}).get('analysis_time_seconds', 0)
                },
                "enhanced_analysis": {
                    "tables_found": enhanced_results.get('analysis_summary', {}).get('unique_tables_found', 0),
                    "references": enhanced_results.get('analysis_summary', {}).get('total_table_references', 0),
                    "airflow_dags": enhanced_results.get('analysis_summary', {}).get('airflow_dags_found', 0),
                    "parameter_flows": enhanced_results.get('analysis_summary', {}).get('parameter_flows_detected', 0),
                    "time": enhanced_results.get('analysis_summary', {}).get('analysis_time_seconds', 0)
                }
            },
            "enhancement_benefits": {
                "additional_tables_found": enhanced_results.get('analysis_summary', {}).get('unique_tables_found', 0) - simple_results.get('analysis_summary', {}).get('unique_tables_found', 0),
                "additional_references": enhanced_results.get('analysis_summary', {}).get('total_table_references', 0) - simple_results.get('analysis_summary', {}).get('total_table_references', 0),
                "airflow_features_detected": enhanced_results.get('analysis_summary', {}).get('airflow_dags_found', 0) > 0,
                "parameter_tracking": enhanced_results.get('analysis_summary', {}).get('parameter_flows_detected', 0) > 0
            }
        }
        
        # Salva comparação
        comparison_file = Path(output_dir) / "analysis_comparison.json"
        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        
        # Mostra resumo da comparação
        print(f"\n📊 COMPARAÇÃO DE RESULTADOS:")
        simple = comparison["analysis_comparison"]["simple_analysis"]
        enhanced = comparison["analysis_comparison"]["enhanced_analysis"]
        benefits = comparison["enhancement_benefits"]
        
        print(f"   📋 ANÁLISE SIMPLES:")
        print(f"      Tabelas: {simple['tables_found']}")
        print(f"      Referências: {simple['references']}")
        print(f"      Tempo: {simple['time']:.2f}s")
        
        print(f"   📋 ANÁLISE AVANÇADA:")
        print(f"      Tabelas: {enhanced['tables_found']} (+{benefits['additional_tables_found']})")
        print(f"      Referências: {enhanced['references']} (+{benefits['additional_references']})")
        print(f"      DAGs Airflow: {enhanced['airflow_dags']}")
        print(f"      Fluxos parâmetros: {enhanced['parameter_flows']}")
        print(f"      Tempo: {enhanced['time']:.2f}s")
        
        print(f"\n🎯 BENEFÍCIOS DA ANÁLISE AVANÇADA:")
        if benefits['additional_tables_found'] > 0:
            print(f"   ✅ +{benefits['additional_tables_found']} tabelas adicionais encontradas")
        if benefits['additional_references'] > 0:
            print(f"   ✅ +{benefits['additional_references']} referências adicionais")
        if benefits['airflow_features_detected']:
            print(f"   ✅ Recursos Airflow detectados")
        if benefits['parameter_tracking']:
            print(f"   ✅ Rastreamento de parâmetros ativo")
        
        print(f"\n📄 Relatório comparativo: {comparison_file}")
        
        return comparison

def main():
    """Função principal do CLI Airflow"""
    parser = argparse.ArgumentParser(
        description="BW_AUTOMATE - Airflow PostgreSQL Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s analyze /path/to/project
  %(prog)s analyze /path/to/project --mode enhanced
  %(prog)s analyze /path/to/project --output /custom/output
  %(prog)s compare /path/to/project
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando analyze
    analyze_parser = subparsers.add_parser('analyze', help='Executa análise PostgreSQL')
    analyze_parser.add_argument('project_path', help='Caminho do projeto')
    analyze_parser.add_argument('--mode', '-m', 
                              choices=['simple', 'enhanced', 'full'],
                              default='enhanced',
                              help='Modo de análise (default: enhanced)')
    analyze_parser.add_argument('--output', '-o', 
                               default='./airflow_analysis_results',
                               help='Diretório de saída')
    
    # Comando compare
    compare_parser = subparsers.add_parser('compare', help='Compara análise simples vs avançada')
    compare_parser.add_argument('project_path', help='Caminho do projeto')
    compare_parser.add_argument('--output', '-o', 
                               default='./comparison_results',
                               help='Diretório de saída')
    
    # Comando demo
    demo_parser = subparsers.add_parser('demo', help='Demonstração com projeto exemplo')
    demo_parser.add_argument('--output', '-o', 
                           default='./demo_results',
                           help='Diretório de saída')
    
    args = parser.parse_args()
    
    # Inicializa CLI
    cli = AirflowIntegrationCLI()
    cli.show_banner()
    
    if args.command == 'analyze':
        # Valida projeto
        if not os.path.exists(args.project_path):
            print(f"❌ Projeto não encontrado: {args.project_path}")
            sys.exit(1)
        
        # Cria diretório de output
        os.makedirs(args.output, exist_ok=True)
        
        # Executa análise
        try:
            results = cli.analyze_project_enhanced(args.project_path, args.output, args.mode)
            cli.show_analysis_summary(results, args.mode)
            
            print(f"\n✅ Análise concluída!")
            print(f"📁 Resultados em: {args.output}")
            
        except Exception as e:
            print(f"❌ Erro durante análise: {e}")
            sys.exit(1)
    
    elif args.command == 'compare':
        # Valida projeto
        if not os.path.exists(args.project_path):
            print(f"❌ Projeto não encontrado: {args.project_path}")
            sys.exit(1)
        
        # Cria diretório de output
        os.makedirs(args.output, exist_ok=True)
        
        # Executa comparação
        try:
            comparison = cli.generate_comparison_report(args.project_path, args.output)
            
            print(f"\n✅ Comparação concluída!")
            print(f"📁 Resultados em: {args.output}")
            
        except Exception as e:
            print(f"❌ Erro durante comparação: {e}")
            sys.exit(1)
    
    elif args.command == 'demo':
        # Demo com projeto atual
        current_project = "/home/dev/code/labcom_etiquetas"
        
        if os.path.exists(current_project):
            print(f"🎬 Executando demo com projeto: {current_project}")
            os.makedirs(args.output, exist_ok=True)
            
            try:
                results = cli.analyze_project_enhanced(current_project, args.output, "full")
                cli.show_analysis_summary(results, "full")
                
                print(f"\n🎬 Demo concluída!")
                print(f"📁 Resultados em: {args.output}")
                
            except Exception as e:
                print(f"❌ Erro no demo: {e}")
        else:
            print(f"❌ Projeto demo não encontrado: {current_project}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
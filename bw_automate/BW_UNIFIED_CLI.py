#!/usr/bin/env python3
"""
🚀 BW_AUTOMATE - UNIFIED CLI
Sistema integrado para análise completa de código Python
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import all analysis modules
try:
    from POSTGRESQL_TABLE_MAPPER import PostgreSQLTableMapper
    from PRODUCTION_READY_ANALYZER import ProductionReadyAnalyzer
    from REAL_ML_ANALYZER import RealMLAnalyzer
    from REAL_PERFORMANCE_PROFILER import RealPerformanceProfiler
except ImportError as e:
    print(f"⚠️  Módulo não encontrado: {e}")
    print("⚠️  Alguns recursos podem não estar disponíveis")

class BWUnifiedCLI:
    """CLI unificado para todos os analisadores BW_AUTOMATE"""
    
    def __init__(self):
        self.version = "3.0.0"
        self.available_analyzers = self._detect_available_analyzers()
    
    def _detect_available_analyzers(self) -> Dict[str, bool]:
        """Detecta quais analisadores estão disponíveis"""
        analyzers = {
            'postgresql': False,
            'production': False,
            'ml': False,
            'performance': False
        }
        
        try:
            from POSTGRESQL_TABLE_MAPPER import PostgreSQLTableMapper
            analyzers['postgresql'] = True
        except ImportError:
            pass
        
        try:
            from PRODUCTION_READY_ANALYZER import ProductionReadyAnalyzer
            analyzers['production'] = True
        except ImportError:
            pass
            
        try:
            from REAL_ML_ANALYZER import RealMLAnalyzer
            analyzers['ml'] = True
        except ImportError:
            pass
            
        try:
            from REAL_PERFORMANCE_PROFILER import RealPerformanceProfiler
            analyzers['performance'] = True
        except ImportError:
            pass
        
        return analyzers
    
    def show_banner(self):
        """Mostra banner do sistema"""
        print("🚀 " + "="*60)
        print("🚀 BW_AUTOMATE - UNIFIED ANALYSIS SYSTEM")
        print("🚀 " + "="*60)
        print(f"📦 Versão: {self.version}")
        print("📋 Analisadores disponíveis:")
        
        for analyzer, available in self.available_analyzers.items():
            status = "✅" if available else "❌"
            print(f"   {status} {analyzer.capitalize()} Analyzer")
        print()
    
    def analyze_postgresql(self, project_path: str, output_dir: str = ".") -> Dict[str, Any]:
        """Executa análise PostgreSQL"""
        if not self.available_analyzers['postgresql']:
            raise RuntimeError("PostgreSQL Analyzer não disponível")
        
        print("🗃️ Iniciando análise PostgreSQL...")
        mapper = PostgreSQLTableMapper()
        
        start_time = time.time()
        results = mapper.analyze_project(project_path)
        analysis_time = time.time() - start_time
        
        # Salva resultados
        output_file = Path(output_dir) / "postgresql_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Análise PostgreSQL concluída em {analysis_time:.2f}s")
        print(f"📄 Resultados salvos em: {output_file}")
        
        return results
    
    def analyze_production(self, project_path: str, output_dir: str = ".") -> Dict[str, Any]:
        """Executa análise de produção"""
        if not self.available_analyzers['production']:
            raise RuntimeError("Production Analyzer não disponível")
        
        print("🏭 Iniciando análise de produção...")
        analyzer = ProductionReadyAnalyzer()
        
        start_time = time.time()
        results = analyzer.analyze_project(project_path)
        analysis_time = time.time() - start_time
        
        # Salva resultados
        output_file = Path(output_dir) / "production_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Análise de produção concluída em {analysis_time:.2f}s")
        print(f"📄 Resultados salvos em: {output_file}")
        
        return results
    
    def analyze_ml(self, project_path: str, output_dir: str = ".") -> Dict[str, Any]:
        """Executa análise ML"""
        if not self.available_analyzers['ml']:
            raise RuntimeError("ML Analyzer não disponível")
        
        print("🤖 Iniciando análise ML...")
        analyzer = RealMLAnalyzer()
        
        start_time = time.time()
        results = analyzer.analyze_project(project_path)
        analysis_time = time.time() - start_time
        
        # Salva resultados
        output_file = Path(output_dir) / "ml_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Análise ML concluída em {analysis_time:.2f}s")
        print(f"📄 Resultados salvos em: {output_file}")
        
        return results
    
    def analyze_performance(self, project_path: str, output_dir: str = ".") -> Dict[str, Any]:
        """Executa análise de performance"""
        if not self.available_analyzers['performance']:
            raise RuntimeError("Performance Analyzer não disponível")
        
        print("⚡ Iniciando análise de performance...")
        profiler = RealPerformanceProfiler()
        
        start_time = time.time()
        results = profiler.profile_project(project_path)
        analysis_time = time.time() - start_time
        
        # Salva resultados
        output_file = Path(output_dir) / "performance_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Análise de performance concluída em {analysis_time:.2f}s")
        print(f"📄 Resultados salvos em: {output_file}")
        
        return results
    
    def analyze_all(self, project_path: str, output_dir: str = ".") -> Dict[str, Any]:
        """Executa TODAS as análises disponíveis"""
        print("🚀 Iniciando análise COMPLETA...")
        
        # Cria diretório de output
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Executa todas as análises disponíveis
        all_results = {}
        total_start = time.time()
        
        if self.available_analyzers['postgresql']:
            try:
                all_results['postgresql'] = self.analyze_postgresql(project_path, output_dir)
            except Exception as e:
                print(f"❌ Erro na análise PostgreSQL: {e}")
                all_results['postgresql'] = {"error": str(e)}
        
        if self.available_analyzers['production']:
            try:
                all_results['production'] = self.analyze_production(project_path, output_dir)
            except Exception as e:
                print(f"❌ Erro na análise de produção: {e}")
                all_results['production'] = {"error": str(e)}
        
        if self.available_analyzers['ml']:
            try:
                all_results['ml'] = self.analyze_ml(project_path, output_dir)
            except Exception as e:
                print(f"❌ Erro na análise ML: {e}")
                all_results['ml'] = {"error": str(e)}
        
        if self.available_analyzers['performance']:
            try:
                all_results['performance'] = self.analyze_performance(project_path, output_dir)
            except Exception as e:
                print(f"❌ Erro na análise de performance: {e}")
                all_results['performance'] = {"error": str(e)}
        
        total_time = time.time() - total_start
        
        # Gera relatório consolidado
        consolidated_report = {
            "analysis_summary": {
                "project_path": project_path,
                "total_analysis_time": total_time,
                "analyzers_executed": len([k for k, v in all_results.items() if "error" not in v]),
                "analyzers_failed": len([k for k, v in all_results.items() if "error" in v]),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "results": all_results
        }
        
        # Salva relatório consolidado
        consolidated_file = output_path / "consolidated_analysis.json"
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 ANÁLISE COMPLETA FINALIZADA!")
        print(f"⏱️  Tempo total: {total_time:.2f}s")
        print(f"📊 Analisadores executados: {len([k for k, v in all_results.items() if 'error' not in v])}")
        print(f"📄 Relatório consolidado: {consolidated_file}")
        
        return consolidated_report
    
    def generate_summary_report(self, analysis_results: Dict[str, Any], output_dir: str = "."):
        """Gera relatório resumo executivo"""
        
        summary = {
            "executive_summary": {
                "project_analyzed": analysis_results.get("analysis_summary", {}).get("project_path", "Unknown"),
                "analysis_date": analysis_results.get("analysis_summary", {}).get("timestamp", "Unknown"),
                "total_analysis_time": analysis_results.get("analysis_summary", {}).get("total_analysis_time", 0)
            },
            "key_findings": {},
            "recommendations": []
        }
        
        # Extrai insights de cada analisador
        results = analysis_results.get("results", {})
        
        if "postgresql" in results and "error" not in results["postgresql"]:
            pg_data = results["postgresql"]
            pg_summary = pg_data.get("analysis_summary", {})
            
            summary["key_findings"]["database"] = {
                "total_tables_found": pg_summary.get("unique_tables_found", 0),
                "total_references": pg_summary.get("total_table_references", 0),
                "schemas_detected": len(pg_summary.get("schemas_found", [])),
                "files_with_db_operations": pg_summary.get("files_with_table_references", 0)
            }
            
            # Recomendações baseadas em PostgreSQL
            if pg_summary.get("unique_tables_found", 0) > 50:
                summary["recommendations"].append("Considere modularizar operações de banco em serviços separados")
            
            if len(pg_summary.get("schemas_found", [])) > 5:
                summary["recommendations"].append("Alto número de esquemas detectados - revisar arquitetura de dados")
        
        if "production" in results and "error" not in results["production"]:
            prod_data = results["production"]
            prod_summary = prod_data.get("summary", {})
            
            summary["key_findings"]["code_quality"] = {
                "overall_score": prod_summary.get("overall_quality_score", 0),
                "total_files": prod_summary.get("total_files", 0),
                "avg_complexity": prod_summary.get("average_complexity", 0),
                "technical_debt": prod_summary.get("technical_debt_level", "Unknown")
            }
            
            # Recomendações de qualidade
            if prod_summary.get("overall_quality_score", 100) < 70:
                summary["recommendations"].append("Score de qualidade baixo - priorizar refatoração")
        
        # Salva relatório executivo
        summary_file = Path(output_dir) / "executive_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Relatório executivo gerado: {summary_file}")
        return summary

def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description="BW_AUTOMATE - Sistema Unificado de Análise de Código Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s analyze /path/to/project --type all
  %(prog)s analyze /path/to/project --type postgresql
  %(prog)s analyze /path/to/project --type production
  %(prog)s analyze /path/to/project --output /output/dir
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando analyze
    analyze_parser = subparsers.add_parser('analyze', help='Executa análise do projeto')
    analyze_parser.add_argument('project_path', help='Caminho do projeto a ser analisado')
    analyze_parser.add_argument('--type', '-t', 
                              choices=['all', 'postgresql', 'production', 'ml', 'performance'],
                              default='all',
                              help='Tipo de análise a executar (default: all)')
    analyze_parser.add_argument('--output', '-o', 
                               default='./bw_automate_results',
                               help='Diretório de saída dos resultados')
    analyze_parser.add_argument('--summary', '-s', 
                               action='store_true',
                               help='Gera relatório executivo resumido')
    
    # Comando info
    info_parser = subparsers.add_parser('info', help='Mostra informações do sistema')
    
    args = parser.parse_args()
    
    # Inicializa CLI
    cli = BWUnifiedCLI()
    cli.show_banner()
    
    if args.command == 'analyze':
        # Valida caminho do projeto
        if not os.path.exists(args.project_path):
            print(f"❌ Erro: Projeto não encontrado em {args.project_path}")
            sys.exit(1)
        
        # Cria diretório de output
        os.makedirs(args.output, exist_ok=True)
        
        # Executa análise
        try:
            if args.type == 'all':
                results = cli.analyze_all(args.project_path, args.output)
            elif args.type == 'postgresql':
                results = cli.analyze_postgresql(args.project_path, args.output)
            elif args.type == 'production':
                results = cli.analyze_production(args.project_path, args.output)
            elif args.type == 'ml':
                results = cli.analyze_ml(args.project_path, args.output)
            elif args.type == 'performance':
                results = cli.analyze_performance(args.project_path, args.output)
            
            # Gera relatório executivo se solicitado
            if args.summary and args.type == 'all':
                cli.generate_summary_report(results, args.output)
            
            print(f"\n✅ Análise concluída com sucesso!")
            print(f"📁 Resultados disponíveis em: {args.output}")
            
        except Exception as e:
            print(f"❌ Erro durante análise: {e}")
            sys.exit(1)
    
    elif args.command == 'info':
        print("📋 Informações detalhadas dos analisadores:")
        for analyzer, available in cli.available_analyzers.items():
            status = "Disponível ✅" if available else "Não disponível ❌"
            print(f"   • {analyzer.capitalize()}: {status}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
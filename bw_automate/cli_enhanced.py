#!/usr/bin/env python3
"""
BW_AUTOMATE - Enhanced CLI Interface
===================================

Interface de linha de comando aprimorada com Rich, progress bars,
e visualizações coloridas para o BW_AUTOMATE.

Autor: Assistant Claude
Data: 2025-09-20
"""

import sys
import os
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import argparse
from datetime import datetime

# Imports seguros para Rich
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.text import Text
    from rich.tree import Tree
    from rich.syntax import Syntax
    from rich.rule import Rule
    from rich.columns import Columns
    from rich.align import Align
    from rich.layout import Layout
    from rich.live import Live
    from rich.prompt import Prompt, Confirm
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback para console básico
    class Console:
        def print(self, *args, **kwargs): 
            print(*args)
        def rule(self, *args, **kwargs): 
            print("=" * 50)

try:
    from utils import SafeLogger, get_missing_dependencies
    from error_handler import ErrorHandler
    from performance_optimizer import memory_manager, PerformanceMetrics
except ImportError:
    # Fallbacks simples se módulos não estiverem disponíveis
    class SafeLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    def get_missing_dependencies(): return []
    
    class ErrorHandler:
        def __init__(self): pass
    
    class memory_manager:
        @staticmethod
        def get_memory_report(): return {"current_memory_mb": -1}


class BWConsole:
    """Console aprimorado para BW_AUTOMATE"""
    
    def __init__(self, use_rich: bool = None):
        self.use_rich = use_rich if use_rich is not None else RICH_AVAILABLE
        
        if self.use_rich:
            self.console = Console()
        else:
            self.console = Console()  # Fallback console
        
        self.logger = SafeLogger("BWConsole")
        
        # Configurações de estilo
        self.colors = {
            'primary': '#2E86AB',
            'success': '#28a745',
            'warning': '#ffc107', 
            'error': '#dc3545',
            'info': '#17a2b8',
            'secondary': '#6c757d'
        }
    
    def print_banner(self):
        """Imprime banner do BW_AUTOMATE"""
        if self.use_rich:
            banner_text = """
██████╗ ██╗    ██╗     █████╗ ██╗   ██╗████████╗ ██████╗ ███╗   ███╗ █████╗ ████████╗███████╗
██╔══██╗██║    ██║    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝██╔════╝
██████╔╝██║ █╗ ██║    ███████║██║   ██║   ██║   ██║   ██║██╔████╔██║███████║   ██║   █████╗  
██╔══██╗██║███╗██║    ██╔══██║██║   ██║   ██║   ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██╔══╝  
██████╔╝╚███╔███╔╝    ██║  ██║╚██████╔╝   ██║   ╚██████╔╝██║ ╚═╝ ██║██║  ██║   ██║   ███████╗
╚═════╝  ╚══╝╚══╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
            """
            
            panel = Panel(
                Align.center(Text(banner_text, style="bold blue")),
                title="🚀 BW_AUTOMATE v1.1.0",
                subtitle="PostgreSQL Table Mapping for Apache Airflow",
                border_style="blue",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print("🚀 BW_AUTOMATE v1.1.0")
            print("PostgreSQL Table Mapping for Apache Airflow")
            print("=" * 60)
    
    def print_system_info(self):
        """Imprime informações do sistema"""
        if self.use_rich:
            table = Table(title="Informações do Sistema", border_style="cyan")
            table.add_column("Item", style="cyan", no_wrap=True)
            table.add_column("Valor", style="white")
            
            # Informações básicas
            table.add_row("🐍 Python", f"{sys.version.split()[0]}")
            table.add_row("💻 Sistema", f"{sys.platform}")
            table.add_row("📁 Diretório", f"{os.getcwd()}")
            
            # Informações de memória
            memory_info = memory_manager.get_memory_report()
            if memory_info["current_memory_mb"] > 0:
                table.add_row("🧠 Memória", f"{memory_info['current_memory_mb']:.1f} MB")
            
            # Dependências
            missing_deps = get_missing_dependencies()
            if missing_deps:
                table.add_row("📦 Dependências", f"❌ {len(missing_deps)} faltando", style="red")
            else:
                table.add_row("📦 Dependências", "✅ Todas disponíveis", style="green")
            
            self.console.print(table)
        else:
            print("\n📊 Informações do Sistema:")
            print(f"🐍 Python: {sys.version.split()[0]}")
            print(f"💻 Sistema: {sys.platform}")
            print(f"📁 Diretório: {os.getcwd()}")
    
    def create_progress_tracker(self, description: str = "Processando...") -> Any:
        """Cria um tracker de progresso"""
        if self.use_rich:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console
            )
        else:
            return SimpleProgressTracker(description)
    
    def print_analysis_summary(self, summary: Dict[str, Any]):
        """Imprime resumo da análise"""
        if self.use_rich:
            # Cria layout em colunas
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body"),
                Layout(name="footer", size=3)
            )
            
            # Header
            layout["header"].update(
                Panel(
                    Align.center("📊 RESUMO DA ANÁLISE"),
                    style="bold green"
                )
            )
            
            # Body com métricas
            metrics_table = self._create_metrics_table(summary)
            layout["body"].update(metrics_table)
            
            # Footer com status
            exec_info = summary.get('execution_info', {})
            footer_text = f"⏱️ Tempo: {exec_info.get('execution_time_formatted', 'N/A')} | 🧠 Memória: {memory_manager.get_memory_report()['current_memory_mb']:.1f}MB"
            layout["footer"].update(
                Panel(Align.center(footer_text), style="dim")
            )
            
            self.console.print(layout)
        else:
            self._print_simple_summary(summary)
    
    def _create_metrics_table(self, summary: Dict[str, Any]) -> Table:
        """Cria tabela de métricas"""
        table = Table(title="Métricas Principais", border_style="green")
        table.add_column("Métrica", style="cyan", no_wrap=True)
        table.add_column("Valor", justify="right", style="white")
        table.add_column("Status", justify="center")
        
        analysis_summary = summary.get('analysis_summary', {})
        quality_metrics = summary.get('quality_metrics', {})
        
        # Adiciona métricas
        table.add_row(
            "📁 Arquivos Analisados",
            str(analysis_summary.get('files_analyzed', 0)),
            "✅" if analysis_summary.get('files_analyzed', 0) > 0 else "❌"
        )
        
        table.add_row(
            "🗃️ Tabelas Encontradas", 
            str(analysis_summary.get('tables_found', 0)),
            "✅" if analysis_summary.get('tables_found', 0) > 0 else "❌"
        )
        
        match_rate = quality_metrics.get('match_rate', 0)
        table.add_row(
            "🎯 Taxa de Match",
            f"{match_rate:.1f}%",
            "✅" if match_rate >= 80 else "⚠️" if match_rate >= 60 else "❌"
        )
        
        confidence = quality_metrics.get('average_confidence', 0)
        table.add_row(
            "🔍 Confiança Média",
            f"{confidence:.1f}%",
            "✅" if confidence >= 80 else "⚠️" if confidence >= 60 else "❌"
        )
        
        return table
    
    def _print_simple_summary(self, summary: Dict[str, Any]):
        """Versão simples do resumo para quando Rich não está disponível"""
        print("\n📊 RESUMO DA ANÁLISE")
        print("=" * 40)
        
        analysis_summary = summary.get('analysis_summary', {})
        quality_metrics = summary.get('quality_metrics', {})
        
        print(f"📁 Arquivos analisados: {analysis_summary.get('files_analyzed', 0)}")
        print(f"🗃️ Tabelas encontradas: {analysis_summary.get('tables_found', 0)}")
        print(f"🎯 Taxa de match: {quality_metrics.get('match_rate', 0):.1f}%")
        print(f"🔍 Confiança média: {quality_metrics.get('average_confidence', 0):.1f}%")
    
    def print_file_tree(self, reports: Dict[str, str]):
        """Imprime árvore de arquivos gerados"""
        if self.use_rich:
            tree = Tree("📁 Relatórios Gerados", style="bold blue")
            
            for report_type, file_path in reports.items():
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                size_str = self._format_file_size(file_size)
                
                # Emoji baseado no tipo de relatório
                emoji = {
                    'executive_dashboard': '📊',
                    'technical_report': '📋',
                    'table_explorer': '🔍',
                    'powerbi_export': '📈',
                    'lineage_visualization': '🌐'
                }.get(report_type, '📄')
                
                tree.add(f"{emoji} {file_name} [dim]({size_str})[/dim]")
            
            self.console.print(tree)
        else:
            print("\n📁 Relatórios Gerados:")
            for report_type, file_path in reports.items():
                print(f"  📄 {os.path.basename(file_path)}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formata tamanho de arquivo"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def print_recommendations(self, recommendations: List[str]):
        """Imprime recomendações"""
        if not recommendations:
            return
        
        if self.use_rich:
            panel = Panel(
                "\n".join([f"💡 {rec}" for rec in recommendations]),
                title="💡 Recomendações",
                border_style="yellow",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print("\n💡 Recomendações:")
            for rec in recommendations:
                print(f"  💡 {rec}")
    
    def print_error(self, error: str, context: str = None):
        """Imprime erro"""
        if self.use_rich:
            error_text = f"❌ {error}"
            if context:
                error_text += f"\n📍 Contexto: {context}"
            
            panel = Panel(
                error_text,
                title="❌ Erro",
                border_style="red",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print(f"\n❌ Erro: {error}")
            if context:
                print(f"📍 Contexto: {context}")
    
    def print_warning(self, warning: str):
        """Imprime warning"""
        if self.use_rich:
            panel = Panel(
                f"⚠️ {warning}",
                title="⚠️ Aviso",
                border_style="yellow",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print(f"\n⚠️ Aviso: {warning}")
    
    def print_success(self, message: str):
        """Imprime mensagem de sucesso"""
        if self.use_rich:
            panel = Panel(
                f"✅ {message}",
                title="✅ Sucesso",
                border_style="green",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print(f"\n✅ {message}")
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Confirma ação com o usuário"""
        if self.use_rich:
            return Confirm.ask(f"❓ {message}", default=default, console=self.console)
        else:
            response = input(f"❓ {message} ({'s/N' if not default else 'S/n'}): ").lower()
            if not response:
                return default
            return response.startswith('s')
    
    def prompt_input(self, message: str, default: str = None) -> str:
        """Solicita entrada do usuário"""
        if self.use_rich:
            return Prompt.ask(f"📝 {message}", default=default, console=self.console)
        else:
            prompt = f"📝 {message}"
            if default:
                prompt += f" [{default}]"
            prompt += ": "
            
            response = input(prompt)
            return response or default or ""


class SimpleProgressTracker:
    """Tracker de progresso simples quando Rich não está disponível"""
    
    def __init__(self, description: str):
        self.description = description
        self.start_time = time.time()
        self.last_update = 0
    
    def __enter__(self):
        print(f"🔄 {self.description}")
        return self
    
    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        print(f"✅ Concluído em {elapsed:.1f}s")
    
    def add_task(self, description: str, total: int = 100):
        """Adiciona uma task"""
        return SimpleTask(description, total)
    
    def update(self, task_id, advance: int = 1, **kwargs):
        """Atualiza progresso"""
        pass  # Simplificado


class SimpleTask:
    """Task simples para progress tracker básico"""
    
    def __init__(self, description: str, total: int):
        self.description = description
        self.total = total
        self.completed = 0
    
    def update(self, advance: int = 1):
        """Atualiza progresso"""
        self.completed += advance
        if self.completed % max(1, self.total // 10) == 0:  # Mostra a cada 10%
            percent = (self.completed / self.total) * 100
            print(f"  📊 {self.description}: {percent:.0f}%")


def create_enhanced_argument_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos aprimorado"""
    parser = argparse.ArgumentParser(
        description='🚀 BW_AUTOMATE - Mapeamento Avançado de Tabelas PostgreSQL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🎯 Exemplos de Uso:

  # Análise básica
  bw_automate --source-dir ./dags --tables-xlsx ./tables.xlsx

  # Com configuração customizada e output detalhado
  bw_automate --source-dir ./airflow/dags \\
              --tables-xlsx ./schema/tables.xlsx \\
              --config ./config.json \\
              --output-dir ./reports \\
              --verbose

  # Análise com filtros específicos
  bw_automate --source-dir ./dags \\
              --tables-xlsx ./tables.xlsx \\
              --schemas public,staging \\
              --max-files 500

  # Modo interativo
  bw_automate --interactive

📚 Para mais informações: https://github.com/decolee/bw_automate
        """
    )
    
    # Argumentos principais
    parser.add_argument(
        '--source-dir', 
        required=False,
        help='📁 Diretório com códigos Python do Airflow'
    )
    
    parser.add_argument(
        '--tables-xlsx',
        required=False, 
        help='📊 Arquivo XLSX com lista de tabelas PostgreSQL'
    )
    
    # Argumentos opcionais
    parser.add_argument(
        '--config',
        help='⚙️ Arquivo de configuração JSON'
    )
    
    parser.add_argument(
        '--output-dir',
        help='📁 Diretório de saída dos relatórios'
    )
    
    parser.add_argument(
        '--schemas',
        help='🗃️ Schemas para analisar (separados por vírgula)'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        help='📊 Máximo de arquivos para analisar'
    )
    
    # Flags
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='🔍 Modo verboso (debug)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='🔇 Modo silencioso'
    )
    
    parser.add_argument(
        '--no-rich',
        action='store_true',
        help='🎨 Desabilita Rich formatting'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='🤝 Modo interativo'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='🚀 BW_AUTOMATE v1.1.0'
    )
    
    # Comandos especiais
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='🔍 Verificar dependências'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='✅ Validar instalação'
    )
    
    return parser


def run_interactive_mode(console: BWConsole):
    """Executa modo interativo"""
    console.print_banner()
    console.console.print("\n🤝 Modo Interativo do BW_AUTOMATE", style="bold cyan")
    console.console.rule()
    
    # Solicita informações básicas
    source_dir = console.prompt_input(
        "Diretório com códigos Python do Airflow",
        default="./dags"
    )
    
    tables_xlsx = console.prompt_input(
        "Arquivo XLSX com tabelas PostgreSQL", 
        default="./tables.xlsx"
    )
    
    # Valida entradas
    if not os.path.exists(source_dir):
        console.print_error(f"Diretório não encontrado: {source_dir}")
        return False
    
    if not os.path.exists(tables_xlsx):
        console.print_error(f"Arquivo não encontrado: {tables_xlsx}")
        return False
    
    # Configurações opcionais
    use_config = console.confirm_action("Usar arquivo de configuração customizado?")
    config_file = None
    if use_config:
        config_file = console.prompt_input("Caminho do arquivo de configuração")
    
    output_dir = console.prompt_input(
        "Diretório de saída dos relatórios",
        default="./reports"
    )
    
    console.print_success("Configuração concluída! Iniciando análise...")
    
    return {
        'source_dir': source_dir,
        'tables_xlsx': tables_xlsx,
        'config': config_file,
        'output_dir': output_dir
    }


if __name__ == "__main__":
    # Teste da interface CLI aprimorada
    console = BWConsole()
    
    console.print_banner()
    console.print_system_info()
    
    # Simula relatórios
    fake_reports = {
        'executive_dashboard': './reports/dashboard.html',
        'technical_report': './reports/technical.html',
        'powerbi_export': './reports/data.xlsx'
    }
    
    console.print_file_tree(fake_reports)
    
    console.print_recommendations([
        "Considere otimizar consultas com baixa performance",
        "Tabelas não oficiais detectadas - revisar nomenclatura"
    ])
    
    console.print_success("Interface CLI aprimorada funcionando!")
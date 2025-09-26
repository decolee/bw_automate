#!/usr/bin/env python3
"""
BW_AUTOMATE - Utilities Module
=============================

Módulo de utilitários para gerenciamento de dependências, imports opcionais,
e funções auxiliares do BW_AUTOMATE.

Autor: Assistant Claude
Data: 2025-09-20
"""

import sys
import os
import logging
import importlib
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
import warnings


class OptionalImport:
    """Gerenciador de imports opcionais"""
    
    def __init__(self, module_name: str, package_name: str = None, error_msg: str = None):
        self.module_name = module_name
        self.package_name = package_name or module_name
        self.error_msg = error_msg or f"Para usar esta funcionalidade, instale: pip install {package_name}"
        self._module = None
        self._available = None
    
    @property
    def available(self) -> bool:
        """Verifica se o módulo está disponível"""
        if self._available is None:
            try:
                self._module = importlib.import_module(self.module_name)
                self._available = True
            except ImportError:
                self._available = False
        return self._available
    
    @property
    def module(self) -> Any:
        """Retorna o módulo importado ou levanta erro informativo"""
        if not self.available:
            raise ImportError(self.error_msg)
        return self._module
    
    def __getattr__(self, name: str) -> Any:
        """Permite acesso direto aos atributos do módulo"""
        return getattr(self.module, name)


# Imports opcionais para BW_AUTOMATE
matplotlib = OptionalImport('matplotlib.pyplot', 'matplotlib', 
                           'Para gerar gráficos, instale: pip install matplotlib')
seaborn = OptionalImport('seaborn', 'seaborn',
                        'Para gráficos avançados, instale: pip install seaborn')
plotly = OptionalImport('plotly.graph_objects', 'plotly',
                       'Para visualizações interativas, instale: pip install plotly')
networkx = OptionalImport('networkx', 'networkx',
                         'Para análise de grafos, instale: pip install networkx')
fuzzywuzzy = OptionalImport('fuzzywuzzy.fuzz', 'fuzzywuzzy[speedup]',
                           'Para matching fuzzy, instale: pip install fuzzywuzzy[speedup]')
sqlparse = OptionalImport('sqlparse', 'sqlparse',
                         'Para parsing SQL, instale: pip install sqlparse')
psycopg2 = OptionalImport('psycopg2', 'psycopg2-binary',
                         'Para conectar PostgreSQL, instale: pip install psycopg2-binary')
tqdm = OptionalImport('tqdm', 'tqdm',
                     'Para barras de progresso, instale: pip install tqdm')
rich = OptionalImport('rich.console', 'rich',
                     'Para output colorido, instale: pip install rich')


def requires_module(*modules: OptionalImport):
    """Decorator para funções que requerem módulos opcionais"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            missing_modules = []
            for module in modules:
                if not module.available:
                    missing_modules.append(module.package_name)
            
            if missing_modules:
                error_msg = f"Módulos necessários não encontrados: {', '.join(missing_modules)}\n"
                error_msg += f"Instale com: pip install {' '.join(missing_modules)}"
                raise ImportError(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SafeLogger:
    """Logger seguro que não falha se logging não estiver configurado"""
    
    def __init__(self, name: str = 'BW_AUTOMATE'):
        try:
            self.logger = logging.getLogger(name)
        except Exception:
            self.logger = None
    
    def _log(self, level: str, message: str, *args, **kwargs):
        """Log seguro"""
        try:
            if self.logger and hasattr(self.logger, level):
                getattr(self.logger, level)(message, *args, **kwargs)
            else:
                # Fallback para print se logging falhar
                print(f"[{level.upper()}] {message}")
        except Exception:
            # Silencioso se tudo falhar
            pass
    
    def debug(self, message: str, *args, **kwargs):
        self._log('debug', message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        self._log('info', message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self._log('warning', message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self._log('error', message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self._log('critical', message, *args, **kwargs)


def safe_import_check() -> Dict[str, bool]:
    """
    Verifica disponibilidade de todas as dependências opcionais
    
    Returns:
        Dicionário com status de cada dependência
    """
    dependencies = {
        'matplotlib': matplotlib.available,
        'seaborn': seaborn.available,
        'plotly': plotly.available,
        'networkx': networkx.available,
        'fuzzywuzzy': fuzzywuzzy.available,
        'sqlparse': sqlparse.available,
        'psycopg2': psycopg2.available,
        'tqdm': tqdm.available,
        'rich': rich.available
    }
    return dependencies


def get_missing_dependencies() -> List[str]:
    """
    Retorna lista de dependências faltando
    
    Returns:
        Lista de nomes de pacotes para instalar
    """
    missing = []
    deps_check = safe_import_check()
    
    # Mapeia módulos para nomes de pacotes
    package_map = {
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn', 
        'plotly': 'plotly',
        'networkx': 'networkx',
        'fuzzywuzzy': 'fuzzywuzzy[speedup]',
        'sqlparse': 'sqlparse',
        'psycopg2': 'psycopg2-binary',
        'tqdm': 'tqdm',
        'rich': 'rich'
    }
    
    for module, available in deps_check.items():
        if not available:
            missing.append(package_map.get(module, module))
    
    return missing


def validate_python_version(min_version: tuple = (3, 8)) -> bool:
    """
    Valida versão do Python
    
    Args:
        min_version: Versão mínima requerida
        
    Returns:
        True se versão é adequada
    """
    current_version = sys.version_info[:2]
    return current_version >= min_version


def setup_warnings():
    """Configura warnings para serem menos verbosos"""
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
    warnings.filterwarnings('ignore', category=UserWarning, module='seaborn')


def ensure_directory(path: str) -> str:
    """
    Garante que diretório existe
    
    Args:
        path: Caminho do diretório
        
    Returns:
        Caminho absoluto do diretório
    """
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def safe_file_operation(operation: Callable, *args, **kwargs) -> Any:
    """
    Executa operação de arquivo com tratamento de erro
    
    Args:
        operation: Função a executar
        *args, **kwargs: Argumentos para a função
        
    Returns:
        Resultado da operação ou None se falhar
    """
    try:
        return operation(*args, **kwargs)
    except (IOError, OSError, PermissionError) as e:
        logger = SafeLogger()
        logger.error(f"Erro em operação de arquivo: {e}")
        return None
    except Exception as e:
        logger = SafeLogger()
        logger.error(f"Erro inesperado em operação de arquivo: {e}")
        return None


def memory_usage_mb() -> float:
    """
    Retorna uso de memória atual em MB
    
    Returns:
        Uso de memória em MB ou -1 se psutil não disponível
    """
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return -1.0
    except Exception:
        return -1.0


def format_bytes(bytes_value: int) -> str:
    """
    Formata bytes em formato legível
    
    Args:
        bytes_value: Valor em bytes
        
    Returns:
        String formatada (ex: "1.5 MB")
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024.0
        unit_index += 1
    
    return f"{bytes_value:.1f} {units[unit_index]}"


def progress_bar(iterable, desc: str = "Processing", disable: bool = False):
    """
    Barra de progresso segura
    
    Args:
        iterable: Iterável para processar
        desc: Descrição da operação
        disable: Desabilitar barra de progresso
        
    Returns:
        Iterável com ou sem barra de progresso
    """
    if disable or not tqdm.available:
        return iterable
    
    try:
        return tqdm.module.tqdm(iterable, desc=desc)
    except Exception:
        return iterable


class PerformanceMonitor:
    """Monitor de performance simples"""
    
    def __init__(self):
        self.start_time = None
        self.checkpoints = {}
        self.logger = SafeLogger()
    
    def start(self):
        """Inicia monitoramento"""
        import time
        self.start_time = time.time()
        self.logger.info("Monitoramento de performance iniciado")
    
    def checkpoint(self, name: str):
        """Cria checkpoint de tempo"""
        if self.start_time is None:
            self.start()
        
        import time
        elapsed = time.time() - self.start_time
        self.checkpoints[name] = elapsed
        self.logger.debug(f"Checkpoint '{name}': {elapsed:.2f}s")
    
    def report(self) -> Dict[str, float]:
        """Retorna relatório de performance"""
        if not self.checkpoints:
            return {}
        
        total_time = max(self.checkpoints.values())
        memory_mb = memory_usage_mb()
        
        report = {
            'total_time_seconds': total_time,
            'memory_usage_mb': memory_mb,
            'checkpoints': self.checkpoints.copy()
        }
        
        self.logger.info(f"Performance: {total_time:.2f}s, Memória: {memory_mb:.1f}MB")
        return report


# Configuração inicial
setup_warnings()

# Logger global
logger = SafeLogger()

# Monitor de performance global
performance_monitor = PerformanceMonitor()


# Funções de conveniência para compatibilidade
def get_logger(name: str = None) -> SafeLogger:
    """Retorna logger seguro"""
    return SafeLogger(name or 'BW_AUTOMATE')


if __name__ == "__main__":
    # Teste das funcionalidades
    print("🔍 BW_AUTOMATE Utils - Teste de Dependências")
    print("=" * 50)
    
    # Verifica Python
    if validate_python_version():
        print("✅ Versão Python adequada")
    else:
        print("❌ Versão Python inadequada (requer 3.8+)")
    
    # Verifica dependências
    deps = safe_import_check()
    for name, available in deps.items():
        status = "✅" if available else "❌"
        print(f"{status} {name}")
    
    # Lista dependências faltando
    missing = get_missing_dependencies()
    if missing:
        print(f"\n📦 Para instalar faltando: pip install {' '.join(missing)}")
    else:
        print(f"\n🎉 Todas as dependências estão disponíveis!")
    
    # Teste de performance
    performance_monitor.start()
    performance_monitor.checkpoint("teste")
    print(f"\n📊 Performance: {performance_monitor.report()}")
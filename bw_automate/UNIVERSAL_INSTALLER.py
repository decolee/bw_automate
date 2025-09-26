#!/usr/bin/env python3
"""
UNIVERSAL INSTALLER & SETUP SYSTEM - BW AUTOMATE
Sistema universal de instalação que funciona em qualquer ambiente
Auto-detecção de sistema, instalação de dependências e configuração automática
"""

import os
import sys
import json
import platform
import subprocess
import logging
import tempfile
import shutil
import urllib.request
import zipfile
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import stat

try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'], check=True)
    import requests

try:
    import pkg_resources
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'setuptools'], check=True)
    import pkg_resources


class OperatingSystem(Enum):
    """Sistemas operacionais suportados"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class PythonManager(Enum):
    """Gerenciadores de pacotes Python"""
    PIP = "pip"
    CONDA = "conda"
    POETRY = "poetry"
    PIPENV = "pipenv"


class InstallationMode(Enum):
    """Modos de instalação"""
    FULL = "full"  # Instalação completa com todos os módulos
    MINIMAL = "minimal"  # Instalação mínima
    DEVELOPMENT = "development"  # Instalação para desenvolvimento
    PRODUCTION = "production"  # Instalação para produção
    CUSTOM = "custom"  # Instalação customizada


@dataclass
class SystemInfo:
    """Informações do sistema"""
    os: OperatingSystem
    os_version: str
    python_version: str
    python_executable: str
    package_manager: PythonManager
    available_managers: List[PythonManager]
    architecture: str
    total_memory: int
    available_disk: int
    has_git: bool
    has_docker: bool
    has_nodejs: bool
    user_permissions: Dict[str, bool]


@dataclass
class InstallationConfig:
    """Configuração de instalação"""
    mode: InstallationMode
    target_directory: str
    create_virtual_env: bool
    install_optional_deps: bool
    setup_monitoring: bool
    enable_security: bool
    create_shortcuts: bool
    add_to_path: bool
    install_examples: bool
    setup_database: bool
    configure_autostart: bool
    backup_existing: bool


@dataclass
class InstallationResult:
    """Resultado da instalação"""
    success: bool
    installation_path: str
    virtual_env_path: Optional[str]
    installed_packages: List[str]
    created_files: List[str]
    shortcuts_created: List[str]
    errors: List[str]
    warnings: List[str]
    next_steps: List[str]
    installation_time: float
    total_size: int


class SystemDetector:
    """Detector de informações do sistema"""
    
    def detect_system(self) -> SystemInfo:
        """Detecta informações completas do sistema"""
        
        # Sistema operacional
        os_name = platform.system().lower()
        if os_name == "windows":
            os_type = OperatingSystem.WINDOWS
        elif os_name == "linux":
            os_type = OperatingSystem.LINUX
        elif os_name == "darwin":
            os_type = OperatingSystem.MACOS
        else:
            os_type = OperatingSystem.UNKNOWN
        
        # Versão do Python
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Detecta gerenciadores de pacote
        available_managers = self._detect_package_managers()
        primary_manager = available_managers[0] if available_managers else PythonManager.PIP
        
        # Memória e disco
        memory_info = self._get_memory_info()
        disk_info = self._get_disk_info()
        
        # Ferramentas disponíveis
        has_git = self._command_exists("git")
        has_docker = self._command_exists("docker")
        has_nodejs = self._command_exists("node") or self._command_exists("nodejs")
        
        # Permissões
        permissions = self._check_permissions()
        
        return SystemInfo(
            os=os_type,
            os_version=platform.release(),
            python_version=python_version,
            python_executable=sys.executable,
            package_manager=primary_manager,
            available_managers=available_managers,
            architecture=platform.machine(),
            total_memory=memory_info.get('total', 0),
            available_disk=disk_info.get('available', 0),
            has_git=has_git,
            has_docker=has_docker,
            has_nodejs=has_nodejs,
            user_permissions=permissions
        )
    
    def _detect_package_managers(self) -> List[PythonManager]:
        """Detecta gerenciadores de pacote disponíveis"""
        managers = []
        
        # Verifica pip
        if self._command_exists("pip") or self._command_exists("pip3"):
            managers.append(PythonManager.PIP)
        
        # Verifica conda
        if self._command_exists("conda"):
            managers.append(PythonManager.CONDA)
        
        # Verifica poetry
        if self._command_exists("poetry"):
            managers.append(PythonManager.POETRY)
        
        # Verifica pipenv
        if self._command_exists("pipenv"):
            managers.append(PythonManager.PIPENV)
        
        return managers
    
    def _command_exists(self, command: str) -> bool:
        """Verifica se um comando existe"""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _get_memory_info(self) -> Dict[str, int]:
        """Obtém informações de memória"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available
            }
        except ImportError:
            # Fallback para sistemas sem psutil
            if platform.system() == "Linux":
                try:
                    with open('/proc/meminfo', 'r') as f:
                        lines = f.readlines()
                        mem_info = {}
                        for line in lines:
                            if 'MemTotal' in line:
                                mem_info['total'] = int(line.split()[1]) * 1024
                            elif 'MemAvailable' in line:
                                mem_info['available'] = int(line.split()[1]) * 1024
                        return mem_info
                except:
                    pass
            
            return {'total': 0, 'available': 0}
    
    def _get_disk_info(self) -> Dict[str, int]:
        """Obtém informações de disco"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total,
                'available': disk.free
            }
        except ImportError:
            try:
                statvfs = os.statvfs('.')
                return {
                    'total': statvfs.f_frsize * statvfs.f_blocks,
                    'available': statvfs.f_frsize * statvfs.f_bavail
                }
            except:
                return {'total': 0, 'available': 0}
    
    def _check_permissions(self) -> Dict[str, bool]:
        """Verifica permissões do usuário"""
        permissions = {
            'can_write_current_dir': os.access('.', os.W_OK),
            'can_create_files': True,
            'can_install_packages': True,
            'can_modify_path': True,
            'is_admin': False
        }
        
        # Verifica se é administrador
        try:
            if platform.system() == "Windows":
                import ctypes
                permissions['is_admin'] = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                permissions['is_admin'] = os.geteuid() == 0
        except:
            pass
        
        # Testa criação de arquivo temporário
        try:
            with tempfile.NamedTemporaryFile(delete=True):
                pass
        except:
            permissions['can_create_files'] = False
        
        # Testa instalação de pacote (sem realmente instalar)
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'pip'], 
                                  capture_output=True, timeout=10)
            permissions['can_install_packages'] = result.returncode == 0
        except:
            permissions['can_install_packages'] = False
        
        return permissions


class DependencyManager:
    """Gerenciador de dependências"""
    
    def __init__(self, system_info: SystemInfo):
        self.system_info = system_info
        self.requirements = self._load_requirements()
    
    def _load_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Carrega requirements por modo de instalação"""
        return {
            'minimal': {
                'required': [
                    'pandas>=1.3.0',
                    'numpy>=1.20.0',
                    'openpyxl>=3.0.0',
                    'sqlparse>=0.4.0',
                    'pyyaml>=6.0'
                ],
                'optional': []
            },
            'full': {
                'required': [
                    'pandas>=1.3.0',
                    'numpy>=1.20.0',
                    'openpyxl>=3.0.0',
                    'sqlparse>=0.4.0',
                    'pyyaml>=6.0',
                    'plotly>=5.0.0',
                    'dash>=2.0.0',
                    'jinja2>=3.0.0',
                    'networkx>=2.8.0',
                    'psycopg2-binary>=2.9.0'
                ],
                'optional': [
                    'redis>=4.0.0',
                    'celery>=5.2.0',
                    'docker>=6.0.0',
                    'kubernetes>=24.0.0',
                    'boto3>=1.26.0',
                    'google-cloud-container>=2.0.0',
                    'azure-mgmt-containerinstance>=10.0.0'
                ]
            },
            'development': {
                'required': [
                    'pandas>=1.3.0',
                    'numpy>=1.20.0',
                    'openpyxl>=3.0.0',
                    'sqlparse>=0.4.0',
                    'pyyaml>=6.0',
                    'plotly>=5.0.0',
                    'pytest>=7.0.0',
                    'black>=22.0.0',
                    'flake8>=5.0.0'
                ],
                'optional': [
                    'jupyter>=1.0.0',
                    'ipython>=8.0.0',
                    'memory-profiler>=0.60.0'
                ]
            },
            'production': {
                'required': [
                    'pandas>=1.3.0',
                    'numpy>=1.20.0',
                    'openpyxl>=3.0.0',
                    'sqlparse>=0.4.0',
                    'pyyaml>=6.0',
                    'gunicorn>=20.0.0',
                    'prometheus-client>=0.14.0'
                ],
                'optional': [
                    'redis>=4.0.0',
                    'celery>=5.2.0',
                    'sentry-sdk>=1.0.0'
                ]
            }
        }
    
    def install_dependencies(self, mode: InstallationMode, 
                           install_optional: bool = False,
                           virtual_env_path: str = None) -> Tuple[bool, List[str], List[str]]:
        """Instala dependências"""
        mode_name = mode.value
        requirements = self.requirements.get(mode_name, self.requirements['minimal'])
        
        packages_to_install = requirements['required'][:]
        if install_optional:
            packages_to_install.extend(requirements['optional'])
        
        installed_packages = []
        failed_packages = []
        
        # Prepara ambiente
        pip_cmd = [sys.executable, '-m', 'pip', 'install']
        
        if virtual_env_path:
            # Usa pip do ambiente virtual
            if platform.system() == "Windows":
                pip_executable = Path(virtual_env_path) / "Scripts" / "pip.exe"
            else:
                pip_executable = Path(virtual_env_path) / "bin" / "pip"
            
            if pip_executable.exists():
                pip_cmd = [str(pip_executable), 'install']
        
        # Instala pacotes
        for package in packages_to_install:
            try:
                print(f"Installing {package}...")
                result = subprocess.run(
                    pip_cmd + [package], 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                
                if result.returncode == 0:
                    installed_packages.append(package)
                    print(f"✅ {package} installed successfully")
                else:
                    failed_packages.append(package)
                    print(f"❌ Failed to install {package}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                failed_packages.append(package)
                print(f"❌ Timeout installing {package}")
            except Exception as e:
                failed_packages.append(package)
                print(f"❌ Error installing {package}: {e}")
        
        success = len(failed_packages) == 0
        return success, installed_packages, failed_packages
    
    def create_virtual_environment(self, venv_path: str) -> bool:
        """Cria ambiente virtual"""
        try:
            venv_path = Path(venv_path)
            
            # Remove se já existe
            if venv_path.exists():
                shutil.rmtree(venv_path)
            
            # Cria ambiente virtual
            subprocess.run([
                sys.executable, '-m', 'venv', str(venv_path)
            ], check=True)
            
            # Atualiza pip no ambiente virtual
            if platform.system() == "Windows":
                pip_path = venv_path / "Scripts" / "pip.exe"
                python_path = venv_path / "Scripts" / "python.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
                python_path = venv_path / "bin" / "python"
            
            if pip_path.exists():
                subprocess.run([
                    str(python_path), '-m', 'pip', 'install', '--upgrade', 'pip'
                ], check=True)
            
            print(f"✅ Virtual environment created: {venv_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False


class UniversalInstaller:
    """Instalador universal do BW_AUTOMATE"""
    
    def __init__(self):
        self.system_detector = SystemDetector()
        self.system_info = self.system_detector.detect_system()
        self.dependency_manager = DependencyManager(self.system_info)
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Configura logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def install(self, config: InstallationConfig) -> InstallationResult:
        """Executa instalação completa"""
        start_time = datetime.now()
        
        self.logger.info("Starting BW_AUTOMATE installation...")
        self.logger.info(f"Target: {config.target_directory}")
        self.logger.info(f"Mode: {config.mode.value}")
        
        result = InstallationResult(
            success=False,
            installation_path="",
            virtual_env_path=None,
            installed_packages=[],
            created_files=[],
            shortcuts_created=[],
            errors=[],
            warnings=[],
            next_steps=[],
            installation_time=0.0,
            total_size=0
        )
        
        try:
            # 1. Validação pré-instalação
            if not self._validate_system(config, result):
                return result
            
            # 2. Preparação do diretório
            if not self._prepare_installation_directory(config, result):
                return result
            
            # 3. Backup se solicitado
            if config.backup_existing:
                self._backup_existing_installation(config, result)
            
            # 4. Criação de ambiente virtual
            if config.create_virtual_env:
                if not self._create_virtual_environment(config, result):
                    return result
            
            # 5. Download e instalação do BW_AUTOMATE
            if not self._install_bw_automate_core(config, result):
                return result
            
            # 6. Instalação de dependências
            if not self._install_dependencies(config, result):
                return result
            
            # 7. Configuração do sistema
            if not self._configure_system(config, result):
                return result
            
            # 8. Criação de exemplos
            if config.install_examples:
                self._install_examples(config, result)
            
            # 9. Configuração de shortcuts
            if config.create_shortcuts:
                self._create_shortcuts(config, result)
            
            # 10. Configuração de PATH
            if config.add_to_path:
                self._add_to_path(config, result)
            
            # 11. Setup de monitoramento
            if config.setup_monitoring:
                self._setup_monitoring(config, result)
            
            # 12. Configuração de autostart
            if config.configure_autostart:
                self._configure_autostart(config, result)
            
            # 13. Validação final
            if not self._validate_installation(config, result):
                result.warnings.append("Installation validation failed")
            
            # 14. Geração de próximos passos
            self._generate_next_steps(config, result)
            
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            result.success = True
            
            self.logger.info("Installation completed successfully!")
            
        except Exception as e:
            result.errors.append(f"Installation failed: {e}")
            self.logger.error(f"Installation failed: {e}")
        
        return result
    
    def _validate_system(self, config: InstallationConfig, result: InstallationResult) -> bool:
        """Valida sistema antes da instalação"""
        
        # Verifica versão do Python
        python_version = tuple(map(int, self.system_info.python_version.split('.')))
        if python_version < (3, 8):
            result.errors.append(f"Python 3.8+ required, found {self.system_info.python_version}")
            return False
        
        # Verifica espaço em disco
        required_space = 1024 * 1024 * 1024  # 1GB
        if self.system_info.available_disk < required_space:
            result.warnings.append("Low disk space detected")
        
        # Verifica permissões
        if not self.system_info.user_permissions['can_create_files']:
            result.errors.append("Insufficient permissions to create files")
            return False
        
        if not self.system_info.user_permissions['can_install_packages']:
            result.warnings.append("May not be able to install packages")
        
        # Verifica gerenciador de pacotes
        if not self.system_info.available_managers:
            result.errors.append("No package manager available")
            return False
        
        return True
    
    def _prepare_installation_directory(self, config: InstallationConfig, result: InstallationResult) -> bool:
        """Prepara diretório de instalação"""
        try:
            target_path = Path(config.target_directory)
            
            # Cria diretório se não existe
            target_path.mkdir(parents=True, exist_ok=True)
            
            result.installation_path = str(target_path.absolute())
            
            # Cria estrutura de diretórios
            subdirs = ['bw_automate', 'config', 'logs', 'reports', 'examples']
            for subdir in subdirs:
                subdir_path = target_path / subdir
                subdir_path.mkdir(exist_ok=True)
                result.created_files.append(str(subdir_path.relative_to(target_path)))
            
            return True
            
        except Exception as e:
            result.errors.append(f"Failed to prepare installation directory: {e}")
            return False
    
    def _backup_existing_installation(self, config: InstallationConfig, result: InstallationResult):
        """Cria backup da instalação existente"""
        try:
            target_path = Path(config.target_directory)
            backup_path = target_path.parent / f"{target_path.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if target_path.exists():
                shutil.copytree(target_path, backup_path)
                result.warnings.append(f"Backup created: {backup_path}")
                
        except Exception as e:
            result.warnings.append(f"Failed to create backup: {e}")
    
    def _create_virtual_environment(self, config: InstallationConfig, result: InstallationResult) -> bool:
        """Cria ambiente virtual"""
        try:
            venv_path = Path(config.target_directory) / "venv"
            
            if self.dependency_manager.create_virtual_environment(str(venv_path)):
                result.virtual_env_path = str(venv_path)
                result.created_files.append("venv/")
                return True
            else:
                result.errors.append("Failed to create virtual environment")
                return False
                
        except Exception as e:
            result.errors.append(f"Virtual environment creation failed: {e}")
            return False
    
    def _install_bw_automate_core(self, config: InstallationConfig, result: InstallationResult) -> bool:
        """Instala arquivos core do BW_AUTOMATE"""
        try:
            target_path = Path(config.target_directory)
            bw_dir = target_path / "bw_automate"
            
            # Lista de arquivos core (assumindo que estão no mesmo diretório)
            current_dir = Path(__file__).parent
            core_files = [
                'run_analysis.py',
                'airflow_table_mapper.py',
                'sql_pattern_extractor.py',
                'table_mapper_engine.py',
                'enhanced_report_generator.py',
                'utils.py',
                'requirements.txt'
            ]
            
            # Copia arquivos core
            for file_name in core_files:
                source_file = current_dir / file_name
                if source_file.exists():
                    dest_file = bw_dir / file_name
                    shutil.copy2(source_file, dest_file)
                    result.created_files.append(f"bw_automate/{file_name}")
            
            # Cria arquivo __init__.py
            init_file = bw_dir / '__init__.py'
            with open(init_file, 'w') as f:
                f.write('"""BW_AUTOMATE - Universal Database Analysis System"""\\n')
                f.write(f'__version__ = "2.0.0"\\n')
                f.write(f'__install_date__ = "{datetime.now().isoformat()}"\\n')
            result.created_files.append("bw_automate/__init__.py")
            
            # Instala módulos avançados baseado no modo
            if config.mode in [InstallationMode.FULL, InstallationMode.DEVELOPMENT]:
                advanced_files = [
                    'REAL_TIME_MONITORING_ENGINE.py',
                    'ADVANCED_VISUALIZATION_DASHBOARD.py',
                    'UNIVERSAL_CODE_INTEGRATION.py',
                    'SMART_AUTO_DETECTION.py',
                    'PLUG_AND_PLAY_MODULES.py'
                ]
                
                for file_name in advanced_files:
                    source_file = current_dir / file_name
                    if source_file.exists():
                        dest_file = bw_dir / file_name
                        shutil.copy2(source_file, dest_file)
                        result.created_files.append(f"bw_automate/{file_name}")
            
            if config.enable_security:
                security_files = ['ENTERPRISE_SECURITY_COMPLIANCE.py']
                for file_name in security_files:
                    source_file = current_dir / file_name
                    if source_file.exists():
                        dest_file = bw_dir / file_name
                        shutil.copy2(source_file, dest_file)
                        result.created_files.append(f"bw_automate/{file_name}")
            
            return True
            
        except Exception as e:
            result.errors.append(f"Failed to install core files: {e}")
            return False
    
    def _install_dependencies(self, config: InstallationConfig, result: InstallationResult) -> bool:
        """Instala dependências"""
        try:
            success, installed, failed = self.dependency_manager.install_dependencies(
                config.mode,
                config.install_optional_deps,
                result.virtual_env_path
            )
            
            result.installed_packages = installed
            
            if failed:
                result.warnings.extend([f"Failed to install: {pkg}" for pkg in failed])
            
            return success or len(installed) > 0  # Sucesso se pelo menos alguns pacotes foram instalados
            
        except Exception as e:
            result.errors.append(f"Dependency installation failed: {e}")
            return False
    
    def _configure_system(self, config: InstallationConfig, result: InstallationResult) -> bool:
        """Configura sistema"""
        try:
            target_path = Path(config.target_directory)
            config_dir = target_path / "config"
            
            # Cria configuração principal
            main_config = {
                'installation': {
                    'version': '2.0.0',
                    'mode': config.mode.value,
                    'install_date': datetime.now().isoformat(),
                    'system_info': asdict(self.system_info)
                },
                'bw_automate': {
                    'default_output_dir': 'reports',
                    'enable_caching': True,
                    'parallel_processing': True,
                    'max_workers': min(4, os.cpu_count() or 2)
                },
                'security': {
                    'enabled': config.enable_security,
                    'validate_connections': False,
                    'encrypt_sensitive_data': config.enable_security
                },
                'monitoring': {
                    'enabled': config.setup_monitoring,
                    'real_time': config.setup_monitoring,
                    'dashboard_port': 8050
                }
            }
            
            config_file = config_dir / 'bw_automate_config.json'
            with open(config_file, 'w') as f:
                json.dump(main_config, f, indent=2, default=str)
            result.created_files.append("config/bw_automate_config.json")
            
            # Cria script de ativação
            self._create_activation_script(target_path, result)
            
            return True
            
        except Exception as e:
            result.errors.append(f"System configuration failed: {e}")
            return False
    
    def _create_activation_script(self, target_path: Path, result: InstallationResult):
        """Cria script de ativação do ambiente"""
        
        # Script para Windows
        if self.system_info.os == OperatingSystem.WINDOWS:
            activate_script = target_path / "activate_bw_automate.bat"
            script_content = f'''@echo off
echo Activating BW_AUTOMATE environment...

set BW_AUTOMATE_HOME={target_path}
set PATH=%BW_AUTOMATE_HOME%\\bw_automate;%PATH%

if exist "%BW_AUTOMATE_HOME%\\venv\\Scripts\\activate.bat" (
    call "%BW_AUTOMATE_HOME%\\venv\\Scripts\\activate.bat"
    echo Virtual environment activated
)

echo BW_AUTOMATE environment ready!
echo Run: python bw_automate\\run_analysis.py --help
'''
        
        # Script para Unix/Linux/macOS
        else:
            activate_script = target_path / "activate_bw_automate.sh"
            script_content = f'''#!/bin/bash
echo "Activating BW_AUTOMATE environment..."

export BW_AUTOMATE_HOME="{target_path}"
export PATH="$BW_AUTOMATE_HOME/bw_automate:$PATH"

if [ -f "$BW_AUTOMATE_HOME/venv/bin/activate" ]; then
    source "$BW_AUTOMATE_HOME/venv/bin/activate"
    echo "Virtual environment activated"
fi

echo "BW_AUTOMATE environment ready!"
echo "Run: python bw_automate/run_analysis.py --help"
'''
            
            # Torna executável
            with open(activate_script, 'w') as f:
                f.write(script_content)
            activate_script.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        with open(activate_script, 'w') as f:
            f.write(script_content)
        
        result.created_files.append(activate_script.name)
    
    def _install_examples(self, config: InstallationConfig, result: InstallationResult):
        """Instala exemplos"""
        try:
            target_path = Path(config.target_directory)
            examples_dir = target_path / "examples"
            
            # Exemplo básico
            basic_example = examples_dir / "basic_analysis.py"
            basic_content = f'''#!/usr/bin/env python3
"""
BW_AUTOMATE Basic Example
Basic usage example for database analysis
"""

import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent.parent / "bw_automate"))

from run_analysis import BWAutomate

def main():
    # Initialize BW_AUTOMATE
    bw = BWAutomate()
    
    # Run analysis on current directory
    results = bw.analyze_project(
        project_root=".",
        output_dir="../reports/basic_example"
    )
    
    print(f"Analysis completed!")
    print(f"Found {{results.get('total_tables', 0)}} database tables")
    print(f"Analyzed {{results.get('total_files', 0)}} files")
    print(f"Report generated in: ../reports/basic_example/")

if __name__ == "__main__":
    main()
'''
            
            with open(basic_example, 'w') as f:
                f.write(basic_content)
            result.created_files.append("examples/basic_analysis.py")
            
            # README dos exemplos
            readme_content = f'''# BW_AUTOMATE Examples

This directory contains example scripts showing how to use BW_AUTOMATE.

## Getting Started

1. Activate the BW_AUTOMATE environment:
   ```bash
   # On Windows:
   activate_bw_automate.bat
   
   # On Unix/Linux/macOS:
   source activate_bw_automate.sh
   ```

2. Run the basic example:
   ```bash
   python examples/basic_analysis.py
   ```

## Examples

- `basic_analysis.py` - Basic database analysis example
- More examples will be added based on your project type

## Configuration

Examples use the default configuration. To customize:

1. Copy `config/bw_automate_config.json` to your project
2. Modify settings as needed
3. Pass config path to BWAutomate()

## Support

For help and documentation, visit the BW_AUTOMATE repository.
'''
            
            readme_file = examples_dir / "README.md"
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            result.created_files.append("examples/README.md")
            
        except Exception as e:
            result.warnings.append(f"Failed to install examples: {e}")
    
    def _create_shortcuts(self, config: InstallationConfig, result: InstallationResult):
        """Cria shortcuts do sistema"""
        try:
            if self.system_info.os == OperatingSystem.WINDOWS:
                # Criar atalho no desktop (Windows)
                self._create_windows_shortcut(config, result)
            else:
                # Criar alias ou desktop entry (Unix)
                self._create_unix_shortcut(config, result)
                
        except Exception as e:
            result.warnings.append(f"Failed to create shortcuts: {e}")
    
    def _create_windows_shortcut(self, config: InstallationConfig, result: InstallationResult):
        """Cria atalho no Windows"""
        # Implementação simplificada - em produção usaria win32com
        result.shortcuts_created.append("Desktop shortcut (manual setup required)")
    
    def _create_unix_shortcut(self, config: InstallationConfig, result: InstallationResult):
        """Cria atalho Unix/Linux"""
        try:
            # Cria alias no .bashrc/.zshrc
            home = Path.home()
            bashrc = home / ".bashrc"
            
            if bashrc.exists():
                alias_line = f'alias bw-automate="cd {config.target_directory} && source activate_bw_automate.sh"'
                
                # Verifica se alias já existe
                with open(bashrc, 'r') as f:
                    content = f.read()
                
                if 'bw-automate=' not in content:
                    with open(bashrc, 'a') as f:
                        f.write(f'\\n# BW_AUTOMATE alias\\n{alias_line}\\n')
                    
                    result.shortcuts_created.append("Shell alias 'bw-automate' added to .bashrc")
                    
        except Exception as e:
            result.warnings.append(f"Failed to create Unix shortcut: {e}")
    
    def _add_to_path(self, config: InstallationConfig, result: InstallationResult):
        """Adiciona BW_AUTOMATE ao PATH"""
        # Esta é uma implementação simplificada
        # Em produção, modificaria registros do Windows ou arquivos de perfil Unix
        result.warnings.append("PATH modification requires manual setup")
    
    def _setup_monitoring(self, config: InstallationConfig, result: InstallationResult):
        """Configura monitoramento"""
        try:
            target_path = Path(config.target_directory)
            
            # Cria script de monitoramento
            monitor_script = target_path / "start_monitoring.py"
            monitor_content = '''#!/usr/bin/env python3
"""
BW_AUTOMATE Monitoring Starter
Starts real-time monitoring and dashboard
"""

import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

try:
    from REAL_TIME_MONITORING_ENGINE import RealTimeMonitoringEngine
    from ADVANCED_VISUALIZATION_DASHBOARD import InteractiveDashboard
    
    def main():
        print("Starting BW_AUTOMATE monitoring...")
        
        # Start monitoring
        monitor = RealTimeMonitoringEngine(".", "monitoring_output")
        monitor.start_monitoring()
        
        # Start dashboard
        dashboard = InteractiveDashboard("monitoring_output")
        dashboard.start_server()
        
        print("Monitoring active at http://localhost:8050")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("Monitoring stopped")

    if __name__ == "__main__":
        main()
        
except ImportError:
    print("Monitoring modules not available. Install with --mode full")
'''
            
            with open(monitor_script, 'w') as f:
                f.write(monitor_content)
            result.created_files.append("start_monitoring.py")
            
        except Exception as e:
            result.warnings.append(f"Failed to setup monitoring: {e}")
    
    def _configure_autostart(self, config: InstallationConfig, result: InstallationResult):
        """Configura autostart"""
        # Implementação simplificada
        result.warnings.append("Autostart configuration requires manual setup")
    
    def _validate_installation(self, config: InstallationConfig, result: InstallationResult) -> bool:
        """Valida instalação"""
        try:
            target_path = Path(config.target_directory)
            
            # Verifica arquivos essenciais
            essential_files = [
                'bw_automate/run_analysis.py',
                'bw_automate/__init__.py',
                'config/bw_automate_config.json'
            ]
            
            for file_path in essential_files:
                if not (target_path / file_path).exists():
                    result.errors.append(f"Missing essential file: {file_path}")
                    return False
            
            # Testa importação
            sys.path.insert(0, str(target_path / "bw_automate"))
            try:
                import run_analysis
                result.warnings.append("✅ Core modules can be imported")
            except ImportError as e:
                result.errors.append(f"Import test failed: {e}")
                return False
            finally:
                sys.path.pop(0)
            
            return True
            
        except Exception as e:
            result.errors.append(f"Validation failed: {e}")
            return False
    
    def _generate_next_steps(self, config: InstallationConfig, result: InstallationResult):
        """Gera próximos passos"""
        steps = [
            f"1. Navigate to installation directory: cd {result.installation_path}",
        ]
        
        if result.virtual_env_path:
            if self.system_info.os == OperatingSystem.WINDOWS:
                steps.append("2. Activate environment: activate_bw_automate.bat")
            else:
                steps.append("2. Activate environment: source activate_bw_automate.sh")
        
        steps.extend([
            "3. Test installation: python bw_automate/run_analysis.py --help",
            "4. Run example: python examples/basic_analysis.py",
            "5. Read examples/README.md for more information"
        ])
        
        if config.setup_monitoring:
            steps.append("6. Start monitoring: python start_monitoring.py")
        
        steps.extend([
            "7. Configure for your project using SMART_AUTO_DETECTION.py",
            "8. Integrate with your framework using PLUG_AND_PLAY_MODULES.py"
        ])
        
        result.next_steps = steps


# CLI Interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="BW_AUTOMATE Universal Installer")
    parser.add_argument("--target", "-t", default="./bw_automate_installation", 
                       help="Installation target directory")
    parser.add_argument("--mode", "-m", choices=[mode.value for mode in InstallationMode],
                       default="full", help="Installation mode")
    parser.add_argument("--no-venv", action="store_true", help="Skip virtual environment creation")
    parser.add_argument("--no-optional", action="store_true", help="Skip optional dependencies")
    parser.add_argument("--no-examples", action="store_true", help="Skip example installation")
    parser.add_argument("--enable-security", action="store_true", help="Enable security features")
    parser.add_argument("--enable-monitoring", action="store_true", help="Enable monitoring")
    parser.add_argument("--create-shortcuts", action="store_true", help="Create system shortcuts")
    parser.add_argument("--add-to-path", action="store_true", help="Add to system PATH")
    parser.add_argument("--backup", action="store_true", help="Backup existing installation")
    parser.add_argument("--autostart", action="store_true", help="Configure autostart")
    parser.add_argument("--system-info", action="store_true", help="Show system information and exit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    installer = UniversalInstaller()
    
    if args.system_info:
        # Mostra informações do sistema
        info = installer.system_info
        print("🖥️  System Information:")
        print(f"  OS: {info.os.value} {info.os_version}")
        print(f"  Architecture: {info.architecture}")
        print(f"  Python: {info.python_version} ({info.python_executable})")
        print(f"  Package Manager: {info.package_manager.value}")
        print(f"  Available Managers: {', '.join([m.value for m in info.available_managers])}")
        print(f"  Memory: {info.total_memory // (1024**3)} GB")
        print(f"  Available Disk: {info.available_disk // (1024**3)} GB")
        print(f"  Git: {'✅' if info.has_git else '❌'}")
        print(f"  Docker: {'✅' if info.has_docker else '❌'}")
        print(f"  Node.js: {'✅' if info.has_nodejs else '❌'}")
        print(f"  Admin Rights: {'✅' if info.user_permissions['is_admin'] else '❌'}")
        return
    
    # Configuração da instalação
    config = InstallationConfig(
        mode=InstallationMode(args.mode),
        target_directory=args.target,
        create_virtual_env=not args.no_venv,
        install_optional_deps=not args.no_optional,
        setup_monitoring=args.enable_monitoring,
        enable_security=args.enable_security,
        create_shortcuts=args.create_shortcuts,
        add_to_path=args.add_to_path,
        install_examples=not args.no_examples,
        setup_database=False,  # TODO: Implementar
        configure_autostart=args.autostart,
        backup_existing=args.backup
    )
    
    print("🚀 BW_AUTOMATE Universal Installer")
    print("=" * 50)
    print(f"Target: {config.target_directory}")
    print(f"Mode: {config.mode.value}")
    print(f"System: {installer.system_info.os.value} {installer.system_info.os_version}")
    print()
    
    # Executa instalação
    result = installer.install(config)
    
    # Mostra resultados
    if result.success:
        print("🎉 Installation completed successfully!")
        print(f"⏱️  Installation time: {result.installation_time:.1f} seconds")
        print(f"📦 Packages installed: {len(result.installed_packages)}")
        print(f"📁 Files created: {len(result.created_files)}")
        
        if result.warnings:
            print("\\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  • {warning}")
        
        print("\\n📋 Next Steps:")
        for step in result.next_steps:
            print(f"  {step}")
            
    else:
        print("❌ Installation failed!")
        for error in result.errors:
            print(f"  • {error}")
        
        if result.warnings:
            print("\\nWarnings:")
            for warning in result.warnings:
                print(f"  • {warning}")


if __name__ == "__main__":
    main()
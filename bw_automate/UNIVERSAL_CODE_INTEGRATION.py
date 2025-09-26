#!/usr/bin/env python3
"""
UNIVERSAL CODE INTEGRATION SYSTEM - BW AUTOMATE
Sistema universal para integração com qualquer codebase existente
Auto-detecção, configuração automática e plug-and-play
"""

import os
import sys
import json
import ast
import re
import subprocess
import importlib.util
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
import shutil
import tempfile
import zipfile
import tarfile

try:
    import yaml
except ImportError:
    print("Installing PyYAML...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyyaml'], check=True)
    import yaml

try:
    import git
except ImportError:
    print("Installing GitPython...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'gitpython'], check=True)
    import git

try:
    import toml
except ImportError:
    print("Installing TOML...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'toml'], check=True)
    import toml


class ProjectType(Enum):
    """Tipos de projeto detectados"""
    AIRFLOW = "airflow"
    DJANGO = "django"
    FLASK = "flask"
    FASTAPI = "fastapi"
    JUPYTER = "jupyter"
    STREAMLIT = "streamlit"
    GENERIC_PYTHON = "generic_python"
    JAVA_SPRING = "java_spring"
    NODEJS = "nodejs"
    REACT = "react"
    UNKNOWN = "unknown"


class DatabaseFramework(Enum):
    """Frameworks de banco detectados"""
    SQLALCHEMY = "sqlalchemy"
    DJANGO_ORM = "django_orm"
    PSYCOPG2 = "psycopg2"
    PYMONGO = "pymongo"
    MYSQL_CONNECTOR = "mysql_connector"
    PEEWEE = "peewee"
    TORTOISE = "tortoise"
    ASYNC_PG = "asyncpg"
    UNKNOWN = "unknown"


@dataclass
class ProjectMetadata:
    """Metadados do projeto detectado"""
    project_type: ProjectType
    root_path: str
    name: str
    version: str
    language: str
    frameworks: List[str]
    database_frameworks: List[DatabaseFramework]
    config_files: List[str]
    entry_points: List[str]
    dependencies: Dict[str, str]
    python_version: str
    structure: Dict[str, Any]


@dataclass
class IntegrationConfig:
    """Configuração de integração"""
    target_directory: str
    backup_enabled: bool = True
    auto_install_deps: bool = True
    create_examples: bool = True
    setup_monitoring: bool = True
    enable_security: bool = False
    deployment_ready: bool = False


class UniversalProjectDetector:
    """Detector universal de tipos de projeto"""
    
    def __init__(self):
        self.detection_patterns = {
            ProjectType.AIRFLOW: {
                'files': ['dags/', 'airflow.cfg', 'docker-compose.yml'],
                'imports': ['airflow', 'from airflow'],
                'dependencies': ['apache-airflow', 'airflow'],
                'indicators': ['DAG', 'BashOperator', 'PythonOperator']
            },
            ProjectType.DJANGO: {
                'files': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py'],
                'imports': ['django', 'from django'],
                'dependencies': ['Django', 'django'],
                'indicators': ['INSTALLED_APPS', 'urlpatterns']
            },
            ProjectType.FLASK: {
                'files': ['app.py', 'run.py', 'wsgi.py'],
                'imports': ['flask', 'from flask'],
                'dependencies': ['Flask', 'flask'],
                'indicators': ['@app.route', 'Flask(__name__)']
            },
            ProjectType.FASTAPI: {
                'files': ['main.py', 'app.py'],
                'imports': ['fastapi', 'from fastapi'],
                'dependencies': ['fastapi', 'uvicorn'],
                'indicators': ['@app.get', '@app.post', 'FastAPI()']
            },
            ProjectType.JUPYTER: {
                'files': ['*.ipynb', 'jupyter_notebook_config.py'],
                'imports': ['jupyter', 'IPython'],
                'dependencies': ['jupyter', 'notebook', 'jupyterlab'],
                'indicators': ['get_ipython()', 'display(']
            },
            ProjectType.STREAMLIT: {
                'files': ['streamlit_app.py', 'app.py'],
                'imports': ['streamlit', 'import streamlit'],
                'dependencies': ['streamlit'],
                'indicators': ['st.', 'streamlit.']
            },
            ProjectType.JAVA_SPRING: {
                'files': ['pom.xml', 'build.gradle', 'src/main/java'],
                'imports': ['org.springframework', 'import org.springframework'],
                'dependencies': ['spring-boot', 'spring-framework'],
                'indicators': ['@SpringBootApplication', '@RestController']
            },
            ProjectType.NODEJS: {
                'files': ['package.json', 'server.js', 'index.js'],
                'imports': ['require(', 'import '],
                'dependencies': ['express', 'node'],
                'indicators': ['npm', 'yarn', 'node_modules']
            }
        }
        
        self.database_patterns = {
            DatabaseFramework.SQLALCHEMY: {
                'imports': ['sqlalchemy', 'from sqlalchemy'],
                'dependencies': ['SQLAlchemy', 'sqlalchemy'],
                'indicators': ['create_engine', 'Session', 'Base.metadata']
            },
            DatabaseFramework.DJANGO_ORM: {
                'imports': ['django.db', 'from django.db'],
                'dependencies': ['Django'],
                'indicators': ['models.Model', 'objects.', 'ForeignKey']
            },
            DatabaseFramework.PSYCOPG2: {
                'imports': ['psycopg2', 'import psycopg2'],
                'dependencies': ['psycopg2', 'psycopg2-binary'],
                'indicators': ['psycopg2.connect', 'cursor.execute']
            },
            DatabaseFramework.PYMONGO: {
                'imports': ['pymongo', 'from pymongo'],
                'dependencies': ['pymongo'],
                'indicators': ['MongoClient', 'collection.find']
            }
        }
    
    def detect_project(self, project_path: str) -> ProjectMetadata:
        """Detecta tipo e características do projeto"""
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise ValueError(f"Project path {project_path} does not exist")
        
        # Coleta informações básicas
        basic_info = self._collect_basic_info(project_path)
        
        # Detecta tipo do projeto
        project_type = self._detect_project_type(project_path)
        
        # Detecta frameworks de banco
        db_frameworks = self._detect_database_frameworks(project_path)
        
        # Analisa estrutura
        structure = self._analyze_project_structure(project_path)
        
        # Detecta dependências
        dependencies = self._detect_dependencies(project_path)
        
        # Encontra pontos de entrada
        entry_points = self._find_entry_points(project_path, project_type)
        
        # Detecta arquivos de configuração
        config_files = self._find_config_files(project_path)
        
        metadata = ProjectMetadata(
            project_type=project_type,
            root_path=str(project_path.absolute()),
            name=basic_info.get('name', project_path.name),
            version=basic_info.get('version', '1.0.0'),
            language=basic_info.get('language', 'python'),
            frameworks=basic_info.get('frameworks', []),
            database_frameworks=db_frameworks,
            config_files=config_files,
            entry_points=entry_points,
            dependencies=dependencies,
            python_version=basic_info.get('python_version', '3.9'),
            structure=structure
        )
        
        return metadata
    
    def _collect_basic_info(self, project_path: Path) -> Dict[str, Any]:
        """Coleta informações básicas do projeto"""
        info = {
            'name': project_path.name,
            'version': '1.0.0',
            'language': 'python',
            'frameworks': [],
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}"
        }
        
        # Verifica package.json (Node.js)
        package_json = project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    info['name'] = data.get('name', info['name'])
                    info['version'] = data.get('version', info['version'])
                    info['language'] = 'javascript'
            except:
                pass
        
        # Verifica setup.py ou pyproject.toml
        setup_py = project_path / 'setup.py'
        pyproject_toml = project_path / 'pyproject.toml'
        
        if pyproject_toml.exists():
            try:
                with open(pyproject_toml, 'r') as f:
                    data = toml.load(f)
                    project_info = data.get('project', {})
                    info['name'] = project_info.get('name', info['name'])
                    info['version'] = project_info.get('version', info['version'])
            except:
                pass
        
        elif setup_py.exists():
            try:
                # Parse setup.py de forma segura
                with open(setup_py, 'r') as f:
                    content = f.read()
                    
                name_match = re.search(r'name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                if name_match:
                    info['name'] = name_match.group(1)
                    
                version_match = re.search(r'version\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                if version_match:
                    info['version'] = version_match.group(1)
            except:
                pass
        
        return info
    
    def _detect_project_type(self, project_path: Path) -> ProjectType:
        """Detecta tipo do projeto"""
        scores = {project_type: 0 for project_type in ProjectType}
        
        # Verifica arquivos
        for project_type, patterns in self.detection_patterns.items():
            for file_pattern in patterns.get('files', []):
                if '*' in file_pattern:
                    # Glob pattern
                    matches = list(project_path.rglob(file_pattern))
                    if matches:
                        scores[project_type] += 3
                else:
                    # Exact path
                    if (project_path / file_pattern).exists():
                        scores[project_type] += 3
        
        # Verifica imports e indicadores em arquivos Python
        for py_file in project_path.rglob('*.py'):
            try:
                if py_file.stat().st_size > 1024 * 1024:  # Skip files > 1MB
                    continue
                    
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for project_type, patterns in self.detection_patterns.items():
                    # Verifica imports
                    for import_pattern in patterns.get('imports', []):
                        if import_pattern in content:
                            scores[project_type] += 2
                    
                    # Verifica indicadores
                    for indicator in patterns.get('indicators', []):
                        if indicator in content:
                            scores[project_type] += 1
                            
            except Exception:
                continue
        
        # Verifica dependências
        dependencies = self._detect_dependencies(project_path)
        for project_type, patterns in self.detection_patterns.items():
            for dep in patterns.get('dependencies', []):
                if dep.lower() in [d.lower() for d in dependencies.keys()]:
                    scores[project_type] += 2
        
        # Retorna o tipo com maior score
        best_match = max(scores.items(), key=lambda x: x[1])
        return best_match[0] if best_match[1] > 0 else ProjectType.GENERIC_PYTHON
    
    def _detect_database_frameworks(self, project_path: Path) -> List[DatabaseFramework]:
        """Detecta frameworks de banco de dados"""
        detected = []
        scores = {fw: 0 for fw in DatabaseFramework}
        
        # Verifica arquivos Python
        for py_file in project_path.rglob('*.py'):
            try:
                if py_file.stat().st_size > 1024 * 1024:  # Skip files > 1MB
                    continue
                    
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for fw, patterns in self.database_patterns.items():
                    # Verifica imports
                    for import_pattern in patterns.get('imports', []):
                        if import_pattern in content:
                            scores[fw] += 2
                    
                    # Verifica indicadores
                    for indicator in patterns.get('indicators', []):
                        if indicator in content:
                            scores[fw] += 1
                            
            except Exception:
                continue
        
        # Verifica dependências
        dependencies = self._detect_dependencies(project_path)
        for fw, patterns in self.database_patterns.items():
            for dep in patterns.get('dependencies', []):
                if dep.lower() in [d.lower() for d in dependencies.keys()]:
                    scores[fw] += 2
        
        # Retorna frameworks com score > 0
        for fw, score in scores.items():
            if score > 0:
                detected.append(fw)
        
        return detected or [DatabaseFramework.UNKNOWN]
    
    def _analyze_project_structure(self, project_path: Path) -> Dict[str, Any]:
        """Analisa estrutura do projeto"""
        structure = {
            'total_files': 0,
            'python_files': 0,
            'config_files': 0,
            'test_files': 0,
            'directories': [],
            'main_modules': [],
            'has_tests': False,
            'has_docs': False,
            'has_docker': False,
            'has_ci': False
        }
        
        for item in project_path.rglob('*'):
            if item.is_file():
                structure['total_files'] += 1
                
                if item.suffix == '.py':
                    structure['python_files'] += 1
                    
                    # Verifica se é arquivo de teste
                    if 'test' in item.name.lower() or item.parent.name.lower() in ['tests', 'test']:
                        structure['test_files'] += 1
                
                # Verifica arquivos especiais
                name_lower = item.name.lower()
                if name_lower in ['dockerfile', 'docker-compose.yml']:
                    structure['has_docker'] = True
                elif name_lower in ['.github', '.gitlab-ci.yml', 'jenkinsfile']:
                    structure['has_ci'] = True
                elif name_lower in ['readme.md', 'docs']:
                    structure['has_docs'] = True
                elif item.suffix in ['.json', '.yml', '.yaml', '.toml', '.ini', '.cfg']:
                    structure['config_files'] += 1
            
            elif item.is_dir():
                dir_name = item.name.lower()
                structure['directories'].append(str(item.relative_to(project_path)))
                
                if dir_name in ['tests', 'test']:
                    structure['has_tests'] = True
                elif dir_name in ['docs', 'documentation']:
                    structure['has_docs'] = True
        
        return structure
    
    def _detect_dependencies(self, project_path: Path) -> Dict[str, str]:
        """Detecta dependências do projeto"""
        dependencies = {}
        
        # requirements.txt
        req_file = project_path / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '==' in line:
                                name, version = line.split('==', 1)
                                dependencies[name.strip()] = version.strip()
                            elif '>=' in line:
                                name = line.split('>=')[0].strip()
                                dependencies[name] = 'latest'
                            else:
                                dependencies[line] = 'latest'
            except:
                pass
        
        # package.json
        package_json = project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})
                    dependencies.update(deps)
                    dependencies.update(dev_deps)
            except:
                pass
        
        # pyproject.toml
        pyproject_toml = project_path / 'pyproject.toml'
        if pyproject_toml.exists():
            try:
                with open(pyproject_toml, 'r') as f:
                    data = toml.load(f)
                    deps = data.get('project', {}).get('dependencies', [])
                    for dep in deps:
                        if '>=' in dep:
                            name = dep.split('>=')[0].strip()
                            dependencies[name] = 'latest'
                        else:
                            dependencies[dep] = 'latest'
            except:
                pass
        
        return dependencies
    
    def _find_entry_points(self, project_path: Path, project_type: ProjectType) -> List[str]:
        """Encontra pontos de entrada do projeto"""
        entry_points = []
        
        common_entry_files = [
            'main.py', 'app.py', 'run.py', 'server.py', 'manage.py',
            'wsgi.py', 'asgi.py', 'index.py', '__main__.py'
        ]
        
        for file_name in common_entry_files:
            entry_file = project_path / file_name
            if entry_file.exists():
                entry_points.append(str(entry_file.relative_to(project_path)))
        
        # Específico por tipo de projeto
        if project_type == ProjectType.AIRFLOW:
            dags_dir = project_path / 'dags'
            if dags_dir.exists():
                for dag_file in dags_dir.rglob('*.py'):
                    entry_points.append(str(dag_file.relative_to(project_path)))
        
        elif project_type == ProjectType.JUPYTER:
            for notebook in project_path.rglob('*.ipynb'):
                entry_points.append(str(notebook.relative_to(project_path)))
        
        return entry_points
    
    def _find_config_files(self, project_path: Path) -> List[str]:
        """Encontra arquivos de configuração"""
        config_files = []
        
        config_patterns = [
            '*.json', '*.yml', '*.yaml', '*.toml', '*.ini', '*.cfg',
            '.env*', 'config.*', 'settings.*'
        ]
        
        for pattern in config_patterns:
            for config_file in project_path.rglob(pattern):
                if config_file.is_file():
                    config_files.append(str(config_file.relative_to(project_path)))
        
        return config_files


class UniversalIntegrator:
    """Integrador universal para qualquer projeto"""
    
    def __init__(self, bw_automate_path: str = None):
        self.bw_automate_path = Path(bw_automate_path or Path(__file__).parent)
        self.detector = UniversalProjectDetector()
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Configura logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def integrate_with_project(self, project_path: str, 
                             config: IntegrationConfig) -> Dict[str, Any]:
        """Integra BW_AUTOMATE com projeto existente"""
        project_path = Path(project_path)
        
        self.logger.info(f"Starting integration with project: {project_path}")
        
        # 1. Detecta projeto
        metadata = self.detector.detect_project(project_path)
        self.logger.info(f"Detected project type: {metadata.project_type.value}")
        
        # 2. Cria backup se solicitado
        if config.backup_enabled:
            backup_path = self._create_backup(project_path)
            self.logger.info(f"Backup created: {backup_path}")
        
        # 3. Gera configuração específica
        integration_config = self._generate_integration_config(metadata, config)
        
        # 4. Instala arquivos do BW_AUTOMATE
        installed_files = self._install_bw_automate_files(project_path, metadata, config)
        
        # 5. Gera código de integração
        integration_code = self._generate_integration_code(metadata, config)
        
        # 6. Instala dependências
        if config.auto_install_deps:
            self._install_dependencies(project_path, metadata)
        
        # 7. Cria exemplos
        if config.create_examples:
            examples = self._create_integration_examples(project_path, metadata)
        
        # 8. Configura monitoramento
        if config.setup_monitoring:
            monitoring_config = self._setup_monitoring(project_path, metadata)
        
        # 9. Gera documentação
        documentation = self._generate_integration_docs(project_path, metadata, config)
        
        result = {
            'success': True,
            'project_metadata': asdict(metadata),
            'integration_config': integration_config,
            'installed_files': installed_files,
            'integration_code': integration_code,
            'examples_created': examples if config.create_examples else [],
            'monitoring_setup': monitoring_config if config.setup_monitoring else {},
            'documentation': documentation,
            'backup_path': backup_path if config.backup_enabled else None,
            'next_steps': self._generate_next_steps(metadata, config)
        }
        
        self.logger.info("Integration completed successfully!")
        return result
    
    def _create_backup(self, project_path: Path) -> str:
        """Cria backup do projeto"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{project_path.name}_backup_{timestamp}.tar.gz"
        backup_path = project_path.parent / backup_name
        
        with tarfile.open(backup_path, 'w:gz') as tar:
            tar.add(project_path, arcname=project_path.name)
        
        return str(backup_path)
    
    def _generate_integration_config(self, metadata: ProjectMetadata, 
                                   config: IntegrationConfig) -> Dict[str, Any]:
        """Gera configuração específica para integração"""
        integration_config = {
            'bw_automate': {
                'version': '2.0.0',
                'integration_type': 'universal',
                'project_type': metadata.project_type.value,
                'database_frameworks': [fw.value for fw in metadata.database_frameworks],
                'auto_detection': True,
                'monitoring': config.setup_monitoring,
                'security': config.enable_security
            },
            'analysis': {
                'source_directories': self._get_source_directories(metadata),
                'file_patterns': self._get_file_patterns(metadata),
                'exclude_patterns': ['__pycache__', '*.pyc', '.git', 'node_modules'],
                'database_configs': self._detect_database_configs(metadata),
                'custom_patterns': self._generate_custom_patterns(metadata)
            },
            'output': {
                'reports_directory': 'bw_automate_reports',
                'formats': ['html', 'json', 'csv'],
                'include_visualizations': True,
                'real_time_monitoring': config.setup_monitoring
            },
            'integration': {
                'entry_points': metadata.entry_points,
                'config_files': metadata.config_files,
                'auto_run': False,
                'schedule': None
            }
        }
        
        return integration_config
    
    def _install_bw_automate_files(self, project_path: Path, metadata: ProjectMetadata, 
                                 config: IntegrationConfig) -> List[str]:
        """Instala arquivos do BW_AUTOMATE no projeto"""
        installed_files = []
        
        # Cria diretório BW_AUTOMATE
        bw_dir = project_path / 'bw_automate'
        bw_dir.mkdir(exist_ok=True)
        
        # Lista de arquivos essenciais para copiar
        essential_files = [
            'run_analysis.py',
            'airflow_table_mapper.py',
            'sql_pattern_extractor.py',
            'table_mapper_engine.py',
            'report_generator.py',
            'utils.py',
            'requirements.txt'
        ]
        
        # Copia arquivos essenciais
        for file_name in essential_files:
            source_file = self.bw_automate_path / file_name
            if source_file.exists():
                dest_file = bw_dir / file_name
                shutil.copy2(source_file, dest_file)
                installed_files.append(str(dest_file.relative_to(project_path)))
        
        # Copia módulos avançados se solicitados
        if config.setup_monitoring:
            advanced_files = [
                'REAL_TIME_MONITORING_ENGINE.py',
                'ADVANCED_VISUALIZATION_DASHBOARD.py'
            ]
            for file_name in advanced_files:
                source_file = self.bw_automate_path / file_name
                if source_file.exists():
                    dest_file = bw_dir / file_name
                    shutil.copy2(source_file, dest_file)
                    installed_files.append(str(dest_file.relative_to(project_path)))
        
        if config.enable_security:
            security_files = ['ENTERPRISE_SECURITY_COMPLIANCE.py']
            for file_name in security_files:
                source_file = self.bw_automate_path / file_name
                if source_file.exists():
                    dest_file = bw_dir / file_name
                    shutil.copy2(source_file, dest_file)
                    installed_files.append(str(dest_file.relative_to(project_path)))
        
        if config.deployment_ready:
            deployment_files = [
                'PRODUCTION_DEPLOYMENT_SYSTEM.py',
                'MULTI_DATABASE_LANGUAGE_SUPPORT.py'
            ]
            for file_name in deployment_files:
                source_file = self.bw_automate_path / file_name
                if source_file.exists():
                    dest_file = bw_dir / file_name
                    shutil.copy2(source_file, dest_file)
                    installed_files.append(str(dest_file.relative_to(project_path)))
        
        # Cria arquivo __init__.py
        init_file = bw_dir / '__init__.py'
        with open(init_file, 'w') as f:
            f.write('"""BW_AUTOMATE integration module"""')
        installed_files.append(str(init_file.relative_to(project_path)))
        
        return installed_files
    
    def _generate_integration_code(self, metadata: ProjectMetadata, 
                                 config: IntegrationConfig) -> Dict[str, str]:
        """Gera código específico de integração"""
        integration_code = {}
        
        # Código principal de integração
        main_integration = f'''#!/usr/bin/env python3
"""
BW_AUTOMATE Integration for {metadata.name}
Auto-generated integration code for {metadata.project_type.value} project
"""

import sys
import os
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

from bw_automate.run_analysis import BWAutomate
from bw_automate.utils import setup_logging

def run_bw_automate_analysis():
    """Run BW_AUTOMATE analysis on this project"""
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting BW_AUTOMATE analysis for {metadata.name}")
    
    # Initialize BW_AUTOMATE
    bw = BWAutomate()
    
    # Configure for this project
    config = {{
        "source_dirs": {self._get_source_directories(metadata)},
        "project_type": "{metadata.project_type.value}",
        "database_frameworks": {[fw.value for fw in metadata.database_frameworks]},
        "output_dir": "bw_automate_reports"
    }}
    
    # Run analysis
    try:
        results = bw.analyze_project(
            project_root=".",
            config=config
        )
        
        logger.info(f"Analysis completed successfully!")
        logger.info(f"Found {{results.get('total_tables', 0)}} database tables")
        logger.info(f"Analyzed {{results.get('total_files', 0)}} files")
        
        return results
        
    except Exception as e:
        logger.error(f"Analysis failed: {{e}}")
        raise

if __name__ == "__main__":
    run_bw_automate_analysis()
'''
        
        integration_code['bw_automate_integration.py'] = main_integration
        
        # Código específico por tipo de projeto
        if metadata.project_type == ProjectType.AIRFLOW:
            airflow_integration = self._generate_airflow_integration(metadata)
            integration_code['airflow_bw_integration.py'] = airflow_integration
        
        elif metadata.project_type == ProjectType.DJANGO:
            django_integration = self._generate_django_integration(metadata)
            integration_code['django_bw_integration.py'] = django_integration
        
        elif metadata.project_type == ProjectType.FLASK:
            flask_integration = self._generate_flask_integration(metadata)
            integration_code['flask_bw_integration.py'] = flask_integration
        
        # Script de configuração
        setup_script = f'''#!/usr/bin/env python3
"""
BW_AUTOMATE Setup Script for {metadata.name}
Configures and validates the integration
"""

import os
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    requirements_file = Path(__file__).parent / "bw_automate" / "requirements.txt"
    
    if requirements_file.exists():
        print("Installing BW_AUTOMATE dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("Dependencies installed successfully!")
    else:
        print("Requirements file not found")

def validate_integration():
    """Validate the integration"""
    print("Validating BW_AUTOMATE integration...")
    
    # Check if all required files exist
    bw_dir = Path(__file__).parent / "bw_automate"
    required_files = ["run_analysis.py", "airflow_table_mapper.py"]
    
    for file_name in required_files:
        file_path = bw_dir / file_name
        if not file_path.exists():
            print(f"❌ Missing required file: {{file_name}}")
            return False
        else:
            print(f"✅ Found: {{file_name}}")
    
    print("✅ Integration validation completed successfully!")
    return True

def main():
    print(f"Setting up BW_AUTOMATE for {metadata.name}")
    print(f"Project type: {metadata.project_type.value}")
    
    install_dependencies()
    
    if validate_integration():
        print("\\n🎉 BW_AUTOMATE integration setup completed!")
        print("\\nNext steps:")
        print("1. Run: python bw_automate_integration.py")
        print("2. Check reports in: bw_automate_reports/")
        print("3. See documentation in: bw_automate_docs.md")
    else:
        print("\\n❌ Integration setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
'''
        
        integration_code['setup_bw_automate.py'] = setup_script
        
        return integration_code
    
    def _generate_airflow_integration(self, metadata: ProjectMetadata) -> str:
        """Gera integração específica para Airflow"""
        return f'''#!/usr/bin/env python3
"""
BW_AUTOMATE Airflow-specific Integration
Specialized integration for Apache Airflow projects
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

# Airflow imports (if available)
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.bash import BashOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False

from bw_automate.run_analysis import BWAutomate

def run_bw_analysis(**context):
    """Function to run BW_AUTOMATE analysis as Airflow task"""
    
    bw = BWAutomate()
    
    # Configure for Airflow project
    config = {{
        "source_dirs": ["dags/", "plugins/", "include/"],
        "file_patterns": ["*.py"],
        "exclude_patterns": ["__pycache__", "*.pyc"],
        "airflow_specific": True,
        "detect_dag_dependencies": True
    }}
    
    results = bw.analyze_project(
        project_root="/opt/airflow",  # Default Airflow path
        config=config
    )
    
    # Store results in Airflow Variable or XCom
    if 'ti' in context:
        context['ti'].xcom_push(key='bw_analysis_results', value=results)
    
    return results

# Create Airflow DAG for BW_AUTOMATE
if AIRFLOW_AVAILABLE:
    default_args = {{
        'owner': 'bw_automate',
        'depends_on_past': False,
        'start_date': datetime(2024, 1, 1),
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }}
    
    dag = DAG(
        'bw_automate_analysis',
        default_args=default_args,
        description='BW_AUTOMATE database table analysis',
        schedule_interval=timedelta(days=1),  # Run daily
        catchup=False,
        tags=['bw_automate', 'analysis', 'database']
    )
    
    # Analysis task
    analysis_task = PythonOperator(
        task_id='run_bw_analysis',
        python_callable=run_bw_analysis,
        dag=dag,
    )
    
    # Generate report task
    report_task = BashOperator(
        task_id='generate_report',
        bash_command='cd /opt/airflow && python bw_automate/run_analysis.py --output-format html',
        dag=dag,
    )
    
    analysis_task >> report_task

# Standalone execution
if __name__ == "__main__":
    run_bw_analysis()
'''
    
    def _generate_django_integration(self, metadata: ProjectMetadata) -> str:
        """Gera integração específica para Django"""
        return f'''#!/usr/bin/env python3
"""
BW_AUTOMATE Django-specific Integration
Specialized integration for Django projects
"""

import os
import sys
import django
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{metadata.name}.settings')
try:
    django.setup()
    DJANGO_AVAILABLE = True
except:
    DJANGO_AVAILABLE = False

from bw_automate.run_analysis import BWAutomate

def analyze_django_models():
    """Analyze Django models and database usage"""
    
    if not DJANGO_AVAILABLE:
        print("Django not available, running generic analysis")
        return run_generic_analysis()
    
    from django.apps import apps
    from django.conf import settings
    
    bw = BWAutomate()
    
    # Get all Django apps
    installed_apps = [app.path for app in apps.get_app_configs()]
    
    config = {{
        "source_dirs": installed_apps + [".", "apps/"],
        "django_specific": True,
        "analyze_models": True,
        "analyze_migrations": True,
        "database_settings": dict(settings.DATABASES)
    }}
    
    results = bw.analyze_project(
        project_root=".",
        config=config
    )
    
    # Django-specific analysis
    if DJANGO_AVAILABLE:
        django_results = analyze_django_orm()
        results['django_analysis'] = django_results
    
    return results

def analyze_django_orm():
    """Analyze Django ORM usage"""
    from django.apps import apps
    
    models_info = []
    
    for model in apps.get_models():
        model_info = {{
            'app': model._meta.app_label,
            'model': model.__name__,
            'table': model._meta.db_table,
            'fields': [field.name for field in model._meta.fields],
            'relations': []
        }}
        
        # Analyze relationships
        for field in model._meta.fields:
            if hasattr(field, 'related_model') and field.related_model:
                model_info['relations'].append({{
                    'field': field.name,
                    'related_model': field.related_model.__name__,
                    'related_table': field.related_model._meta.db_table
                }})
        
        models_info.append(model_info)
    
    return {{
        'total_models': len(models_info),
        'models': models_info,
        'apps': list(set(model['app'] for model in models_info))
    }}

def run_generic_analysis():
    """Fallback generic analysis"""
    bw = BWAutomate()
    
    config = {{
        "source_dirs": [".", "apps/"],
        "file_patterns": ["*.py"],
        "exclude_patterns": ["migrations/", "__pycache__/"]
    }}
    
    return bw.analyze_project(project_root=".", config=config)

# Django management command integration
if DJANGO_AVAILABLE:
    from django.core.management.base import BaseCommand
    
    class Command(BaseCommand):
        help = 'Run BW_AUTOMATE analysis on Django project'
        
        def handle(self, *args, **options):
            self.stdout.write('Starting BW_AUTOMATE analysis...')
            
            results = analyze_django_models()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Analysis completed! Found {{results.get("total_tables", 0)}} tables'
                )
            )

if __name__ == "__main__":
    analyze_django_models()
'''
    
    def _generate_flask_integration(self, metadata: ProjectMetadata) -> str:
        """Gera integração específica para Flask"""
        return f'''#!/usr/bin/env python3
"""
BW_AUTOMATE Flask-specific Integration
Specialized integration for Flask projects
"""

import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

# Flask imports (if available)
try:
    from flask import Flask, jsonify, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from bw_automate.run_analysis import BWAutomate

def create_bw_analysis_blueprint():
    """Create Flask blueprint for BW_AUTOMATE"""
    
    if not FLASK_AVAILABLE:
        return None
    
    from flask import Blueprint
    
    bp = Blueprint('bw_automate', __name__, url_prefix='/bw-automate')
    
    @bp.route('/analyze')
    def analyze():
        """Run analysis and return JSON results"""
        try:
            bw = BWAutomate()
            
            config = {{
                "source_dirs": [".", "app/", "src/"],
                "flask_specific": True,
                "analyze_routes": True,
                "analyze_blueprints": True
            }}
            
            results = bw.analyze_project(project_root=".", config=config)
            return jsonify(results)
            
        except Exception as e:
            return jsonify({{"error": str(e)}}), 500
    
    @bp.route('/report')
    def report():
        """Generate HTML report"""
        try:
            bw = BWAutomate()
            results = bw.analyze_project(project_root=".")
            
            # Simple HTML template
            template = '''
            <html>
            <head><title>BW_AUTOMATE Report</title></head>
            <body>
                <h1>Database Analysis Report</h1>
                <h2>Summary</h2>
                <ul>
                    <li>Total Tables: {{{{ results.get('total_tables', 0) }}}}</li>
                    <li>Total Files: {{{{ results.get('total_files', 0) }}}}</li>
                    <li>Project Type: {{{{ results.get('project_type', 'Unknown') }}}}</li>
                </ul>
                <h2>Tables Found</h2>
                <ul>
                {% for table in results.get('tables', []) %}
                    <li>{{{{ table }}}}</li>
                {% endfor %}
                </ul>
            </body>
            </html>
            '''
            
            return render_template_string(template, results=results)
            
        except Exception as e:
            return f"Error generating report: {{e}}", 500
    
    return bp

def analyze_flask_app():
    """Analyze Flask application"""
    
    bw = BWAutomate()
    
    config = {{
        "source_dirs": [".", "app/", "src/"],
        "flask_specific": True,
        "file_patterns": ["*.py"],
        "exclude_patterns": ["__pycache__/", "venv/", "env/"]
    }}
    
    results = bw.analyze_project(project_root=".", config=config)
    
    # Flask-specific analysis
    if FLASK_AVAILABLE:
        flask_results = analyze_flask_routes()
        results['flask_analysis'] = flask_results
    
    return results

def analyze_flask_routes():
    """Analyze Flask routes and blueprints"""
    # This would analyze Flask route definitions and their database usage
    return {{
        'routes_analyzed': 0,
        'blueprints_found': 0,
        'database_operations': []
    }}

# Flask app integration
if FLASK_AVAILABLE:
    def integrate_with_flask_app(app):
        """Integrate BW_AUTOMATE with existing Flask app"""
        
        bp = create_bw_analysis_blueprint()
        if bp:
            app.register_blueprint(bp)
            
        @app.route('/bw-automate-status')
        def bw_status():
            return jsonify({{"status": "BW_AUTOMATE integrated", "version": "2.0.0"}})

if __name__ == "__main__":
    analyze_flask_app()
'''
    
    def _get_source_directories(self, metadata: ProjectMetadata) -> List[str]:
        """Determina diretórios de código fonte baseado no tipo de projeto"""
        if metadata.project_type == ProjectType.AIRFLOW:
            return ['dags/', 'plugins/', 'include/']
        elif metadata.project_type == ProjectType.DJANGO:
            return ['.', 'apps/', metadata.name + '/']
        elif metadata.project_type == ProjectType.FLASK:
            return ['.', 'app/', 'src/']
        elif metadata.project_type == ProjectType.JUPYTER:
            return ['.']
        else:
            return ['.', 'src/', 'app/']
    
    def _get_file_patterns(self, metadata: ProjectMetadata) -> List[str]:
        """Determina padrões de arquivo baseado no tipo de projeto"""
        patterns = ['*.py']
        
        if metadata.project_type == ProjectType.JUPYTER:
            patterns.append('*.ipynb')
        
        if metadata.project_type == ProjectType.JAVA_SPRING:
            patterns.extend(['*.java', '*.xml'])
        
        if metadata.project_type == ProjectType.NODEJS:
            patterns.extend(['*.js', '*.ts'])
        
        return patterns
    
    def _detect_database_configs(self, metadata: ProjectMetadata) -> Dict[str, Any]:
        """Detecta configurações de banco de dados"""
        configs = {}
        
        project_path = Path(metadata.root_path)
        
        # Procura por arquivos de configuração com credenciais de banco
        for config_file in metadata.config_files:
            config_path = project_path / config_file
            if config_path.exists() and config_path.suffix in ['.json', '.yml', '.yaml']:
                try:
                    if config_path.suffix == '.json':
                        with open(config_path, 'r') as f:
                            data = json.load(f)
                    else:
                        with open(config_path, 'r') as f:
                            data = yaml.safe_load(f)
                    
                    # Procura por chaves relacionadas a banco de dados
                    db_keys = ['database', 'db', 'databases', 'DATABASE_URL', 'SQLALCHEMY_DATABASE_URI']
                    for key in db_keys:
                        if key in str(data).lower():
                            configs[config_file] = {'type': 'config_file', 'contains_db_config': True}
                            break
                            
                except:
                    pass
        
        return configs
    
    def _generate_custom_patterns(self, metadata: ProjectMetadata) -> List[str]:
        """Gera padrões customizados baseado nos frameworks detectados"""
        patterns = []
        
        for fw in metadata.database_frameworks:
            if fw == DatabaseFramework.DJANGO_ORM:
                patterns.extend([
                    r'class\s+(\w+)\s*\(.*Model\)',
                    r'(\w+)\.objects\.',
                    r'Meta:\s*\n\s*db_table\s*=\s*[\'"](\w+)[\'"]'
                ])
            elif fw == DatabaseFramework.SQLALCHEMY:
                patterns.extend([
                    r'Table\s*\(\s*[\'"](\w+)[\'"]',
                    r'__tablename__\s*=\s*[\'"](\w+)[\'"]'
                ])
        
        return patterns
    
    def _install_dependencies(self, project_path: Path, metadata: ProjectMetadata):
        """Instala dependências necessárias"""
        requirements_file = project_path / 'bw_automate' / 'requirements.txt'
        
        if requirements_file.exists():
            self.logger.info("Installing BW_AUTOMATE dependencies...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ])
            self.logger.info("Dependencies installed successfully!")
    
    def _create_integration_examples(self, project_path: Path, 
                                   metadata: ProjectMetadata) -> List[str]:
        """Cria exemplos de integração"""
        examples = []
        
        examples_dir = project_path / 'bw_automate_examples'
        examples_dir.mkdir(exist_ok=True)
        
        # Exemplo básico
        basic_example = f'''#!/usr/bin/env python3
"""
Basic BW_AUTOMATE Example for {metadata.name}
Simple usage example showing how to run analysis
"""

import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent.parent / "bw_automate"))

from run_analysis import BWAutomate

def main():
    # Initialize BW_AUTOMATE
    bw = BWAutomate()
    
    # Run analysis
    results = bw.analyze_project(
        project_root="..",  # Parent directory (your project)
        output_dir="reports"
    )
    
    print(f"Analysis completed!")
    print(f"Found {{results.get('total_tables', 0)}} database tables")
    print(f"Analyzed {{results.get('total_files', 0)}} files")

if __name__ == "__main__":
    main()
'''
        
        basic_example_file = examples_dir / 'basic_analysis.py'
        with open(basic_example_file, 'w') as f:
            f.write(basic_example)
        examples.append(str(basic_example_file.relative_to(project_path)))
        
        # Exemplo avançado
        advanced_example = f'''#!/usr/bin/env python3
"""
Advanced BW_AUTOMATE Example for {metadata.name}
Advanced usage with custom configuration and monitoring
"""

import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent.parent / "bw_automate"))

from run_analysis import BWAutomate

def main():
    # Initialize with custom config
    bw = BWAutomate()
    
    # Advanced configuration
    config = {{
        "source_dirs": {self._get_source_directories(metadata)},
        "file_patterns": {self._get_file_patterns(metadata)},
        "exclude_patterns": ["__pycache__", "*.pyc", ".git"],
        "output_formats": ["html", "json", "csv"],
        "include_visualizations": True,
        "real_time_monitoring": True,
        "security_scan": True
    }}
    
    # Run comprehensive analysis
    results = bw.analyze_project(
        project_root="..",
        config=config,
        output_dir="comprehensive_reports"
    )
    
    # Print detailed results
    print("=== BW_AUTOMATE Comprehensive Analysis ===")
    print(f"Project: {metadata.name}")
    print(f"Type: {metadata.project_type.value}")
    print(f"Total Tables: {{results.get('total_tables', 0)}}")
    print(f"Total Files: {{results.get('total_files', 0)}}")
    
    if 'tables_by_type' in results:
        print("\\nTables by Database Type:")
        for db_type, tables in results['tables_by_type'].items():
            print(f"  {{db_type}}: {{len(tables)}} tables")
    
    if 'security_issues' in results:
        print(f"\\nSecurity Issues Found: {{len(results['security_issues'])}}")
    
    print("\\nReports generated in: comprehensive_reports/")

if __name__ == "__main__":
    main()
'''
        
        advanced_example_file = examples_dir / 'advanced_analysis.py'
        with open(advanced_example_file, 'w') as f:
            f.write(advanced_example)
        examples.append(str(advanced_example_file.relative_to(project_path)))
        
        return examples
    
    def _setup_monitoring(self, project_path: Path, metadata: ProjectMetadata) -> Dict[str, Any]:
        """Configura monitoramento em tempo real"""
        monitoring_config = {
            'enabled': True,
            'watch_directories': self._get_source_directories(metadata),
            'file_patterns': self._get_file_patterns(metadata),
            'auto_analysis': False,
            'notification_methods': ['log'],
            'dashboard_enabled': False
        }
        
        # Cria arquivo de configuração de monitoramento
        monitoring_config_file = project_path / 'bw_automate_monitoring.json'
        with open(monitoring_config_file, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        return monitoring_config
    
    def _generate_integration_docs(self, project_path: Path, metadata: ProjectMetadata, 
                                 config: IntegrationConfig) -> str:
        """Gera documentação de integração"""
        docs_content = f'''# BW_AUTOMATE Integration Documentation

## Project Information
- **Name**: {metadata.name}
- **Type**: {metadata.project_type.value}
- **Language**: {metadata.language}
- **Version**: {metadata.version}

## Detected Frameworks
- **Database Frameworks**: {', '.join([fw.value for fw in metadata.database_frameworks])}
- **Other Frameworks**: {', '.join(metadata.frameworks)}

## Integration Files
The following files have been added to your project:

### Core Files
- `bw_automate/` - Main BW_AUTOMATE module directory
- `bw_automate_integration.py` - Main integration script
- `setup_bw_automate.py` - Setup and validation script

### Examples
- `bw_automate_examples/basic_analysis.py` - Basic usage example
- `bw_automate_examples/advanced_analysis.py` - Advanced configuration example

## Quick Start

1. **Setup Dependencies**:
   ```bash
   python setup_bw_automate.py
   ```

2. **Run Basic Analysis**:
   ```bash
   python bw_automate_integration.py
   ```

3. **View Results**:
   ```bash
   # Reports will be generated in: bw_automate_reports/
   open bw_automate_reports/index.html
   ```

## Configuration

### Basic Configuration
Edit `bw_automate_integration.py` to customize:
- Source directories to analyze
- File patterns to include/exclude
- Output formats
- Database connection settings

### Advanced Configuration
For advanced features, modify the config dictionary:

```python
config = {{
    "source_dirs": {self._get_source_directories(metadata)},
    "file_patterns": {self._get_file_patterns(metadata)},
    "database_frameworks": {[fw.value for fw in metadata.database_frameworks]},
    "output_formats": ["html", "json", "csv"],
    "include_visualizations": True,
    "real_time_monitoring": {str(config.setup_monitoring).lower()},
    "security_enabled": {str(config.enable_security).lower()}
}}
```

## Project-Specific Integration

### {metadata.project_type.value.title()} Integration
'''

        if metadata.project_type == ProjectType.AIRFLOW:
            docs_content += '''
This is an Apache Airflow project. BW_AUTOMATE has been configured to:
- Analyze DAG files in the `dags/` directory
- Detect task dependencies and data flows
- Generate Airflow-specific reports
- Optionally create a monitoring DAG

**Usage in Airflow**:
```python
# Import in your DAGs
from bw_automate.airflow_bw_integration import run_bw_analysis

# Or run the dedicated analysis DAG
# DAG ID: bw_automate_analysis
```
'''
        
        elif metadata.project_type == ProjectType.DJANGO:
            docs_content += '''
This is a Django project. BW_AUTOMATE has been configured to:
- Analyze Django models and ORM usage
- Detect database relationships
- Analyze migration files
- Generate Django-specific reports

**Django Management Command**:
```bash
python manage.py bw_analyze
```
'''
        
        elif metadata.project_type == ProjectType.FLASK:
            docs_content += '''
This is a Flask project. BW_AUTOMATE has been configured to:
- Analyze Flask routes and blueprints
- Detect database operations in views
- Generate Flask-specific reports
- Optionally integrate web interface

**Flask Integration**:
```python
from bw_automate.flask_bw_integration import integrate_with_flask_app

# In your app factory
integrate_with_flask_app(app)

# Access via: /bw-automate/analyze
```
'''

        docs_content += f'''

## Output and Reports

BW_AUTOMATE generates several types of reports:

1. **HTML Report** - Interactive web-based report
2. **JSON Report** - Machine-readable data
3. **CSV Export** - Spreadsheet-compatible format
4. **Visualization Dashboard** - Charts and graphs

## Detected Configuration

Based on your project, BW_AUTOMATE detected:

- **Entry Points**: {', '.join(metadata.entry_points[:5])}
- **Config Files**: {', '.join(metadata.config_files[:5])}
- **Source Directories**: {', '.join(self._get_source_directories(metadata))}
- **Total Files**: {metadata.structure.get('total_files', 0)}
- **Python Files**: {metadata.structure.get('python_files', 0)}

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   python setup_bw_automate.py
   ```

2. **Permission Errors**: Ensure BW_AUTOMATE has read access to your source files

3. **No Tables Found**: Check that your database configuration is correct

4. **Performance Issues**: For large projects, consider excluding unnecessary directories

### Getting Help

- Check the troubleshooting guide: `bw_automate/TROUBLESHOOTING_GUIDE.md`
- View examples: `bw_automate_examples/`
- Enable debug mode in configuration

## Advanced Features

### Real-Time Monitoring
{f"✅ Enabled" if config.setup_monitoring else "❌ Disabled"}

### Security Scanning
{f"✅ Enabled" if config.enable_security else "❌ Disabled"}

### Production Deployment
{f"✅ Enabled" if config.deployment_ready else "❌ Disabled"}

## Next Steps

1. Run the analysis and review results
2. Customize configuration for your specific needs
3. Set up automated analysis (cron job, CI/CD)
4. Integrate with your monitoring systems
5. Share reports with your team

---

**BW_AUTOMATE v2.0.0** - Universal Database Analysis System
'''
        
        docs_file = project_path / 'bw_automate_docs.md'
        with open(docs_file, 'w') as f:
            f.write(docs_content)
        
        return str(docs_file.relative_to(project_path))
    
    def _generate_next_steps(self, metadata: ProjectMetadata, 
                           config: IntegrationConfig) -> List[str]:
        """Gera lista de próximos passos"""
        next_steps = [
            "1. Run setup script: `python setup_bw_automate.py`",
            "2. Execute analysis: `python bw_automate_integration.py`",
            "3. Review generated reports in `bw_automate_reports/`",
            "4. Read documentation: `bw_automate_docs.md`",
            "5. Try examples in `bw_automate_examples/`"
        ]
        
        if metadata.project_type == ProjectType.AIRFLOW:
            next_steps.append("6. Consider using the Airflow DAG for scheduled analysis")
        
        elif metadata.project_type == ProjectType.DJANGO:
            next_steps.append("6. Use Django management command: `python manage.py bw_analyze`")
        
        elif metadata.project_type == ProjectType.FLASK:
            next_steps.append("6. Access web interface at `/bw-automate/report`")
        
        if config.setup_monitoring:
            next_steps.append("7. Configure real-time monitoring settings")
        
        if config.enable_security:
            next_steps.append("8. Review security analysis results")
        
        next_steps.extend([
            "9. Customize configuration for your specific needs",
            "10. Set up automated analysis in CI/CD pipeline"
        ])
        
        return next_steps


# CLI Interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Universal BW_AUTOMATE Integration System")
    parser.add_argument("project_path", help="Path to project to integrate with")
    parser.add_argument("--target-dir", help="Target directory for BW_AUTOMATE files")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    parser.add_argument("--no-deps", action="store_true", help="Skip installing dependencies")
    parser.add_argument("--no-examples", action="store_true", help="Skip creating examples")
    parser.add_argument("--enable-monitoring", action="store_true", help="Enable real-time monitoring")
    parser.add_argument("--enable-security", action="store_true", help="Enable security features")
    parser.add_argument("--deployment-ready", action="store_true", help="Include deployment features")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    
    args = parser.parse_args()
    
    # Create integration config
    config = IntegrationConfig(
        target_directory=args.target_dir or args.project_path,
        backup_enabled=not args.no_backup,
        auto_install_deps=not args.no_deps,
        create_examples=not args.no_examples,
        setup_monitoring=args.enable_monitoring,
        enable_security=args.enable_security,
        deployment_ready=args.deployment_ready
    )
    
    # Initialize integrator
    integrator = UniversalIntegrator()
    
    if args.dry_run:
        # Dry run - just detect and show what would be done
        metadata = integrator.detector.detect_project(args.project_path)
        
        print(f"🔍 Project Detection Results:")
        print(f"  Name: {metadata.name}")
        print(f"  Type: {metadata.project_type.value}")
        print(f"  Language: {metadata.language}")
        print(f"  Database Frameworks: {', '.join([fw.value for fw in metadata.database_frameworks])}")
        print(f"  Total Files: {metadata.structure.get('total_files', 0)}")
        print(f"  Python Files: {metadata.structure.get('python_files', 0)}")
        print(f"  Entry Points: {', '.join(metadata.entry_points[:3])}")
        
        print(f"\\n📋 Integration Plan:")
        print(f"  Backup: {'Yes' if config.backup_enabled else 'No'}")
        print(f"  Install Dependencies: {'Yes' if config.auto_install_deps else 'No'}")
        print(f"  Create Examples: {'Yes' if config.create_examples else 'No'}")
        print(f"  Setup Monitoring: {'Yes' if config.setup_monitoring else 'No'}")
        print(f"  Enable Security: {'Yes' if config.enable_security else 'No'}")
        print(f"  Deployment Ready: {'Yes' if config.deployment_ready else 'No'}")
        
    else:
        # Actual integration
        try:
            result = integrator.integrate_with_project(args.project_path, config)
            
            if result['success']:
                print("🎉 BW_AUTOMATE integration completed successfully!")
                print(f"\\n📊 Integration Summary:")
                print(f"  Project: {result['project_metadata']['name']}")
                print(f"  Type: {result['project_metadata']['project_type']}")
                print(f"  Files Installed: {len(result['installed_files'])}")
                print(f"  Examples Created: {len(result['examples_created'])}")
                
                if result['backup_path']:
                    print(f"  Backup: {result['backup_path']}")
                
                print(f"\\n🚀 Next Steps:")
                for step in result['next_steps']:
                    print(f"  {step}")
                
            else:
                print("❌ Integration failed!")
                
        except Exception as e:
            print(f"❌ Integration error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
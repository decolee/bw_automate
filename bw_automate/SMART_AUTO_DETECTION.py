#!/usr/bin/env python3
"""
SMART AUTO-DETECTION & CONFIGURATION SYSTEM - BW AUTOMATE
Sistema inteligente de auto-detecção de configurações de banco de dados,
estruturas de projeto e geração automática de configurações otimizadas
"""

import os
import re
import ast
import json
import logging
import subprocess
import configparser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import sqlite3
import hashlib

try:
    import yaml
except ImportError:
    subprocess.run(['pip', 'install', 'pyyaml'], check=True)
    import yaml

try:
    import toml
except ImportError:
    subprocess.run(['pip', 'install', 'toml'], check=True)
    import toml

try:
    from dotenv import dotenv_values
except ImportError:
    subprocess.run(['pip', 'install', 'python-dotenv'], check=True)
    from dotenv import dotenv_values


@dataclass
class DatabaseConfig:
    """Configuração de banco de dados detectada"""
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str = None
    schema: str = None
    connection_string: str = None
    source_file: str = None
    confidence: float = 1.0
    ssl_mode: str = None
    additional_params: Dict[str, Any] = None


@dataclass
class ProjectStructure:
    """Estrutura do projeto detectada"""
    type: str
    framework: str
    language: str
    version: str
    main_directories: List[str]
    config_files: List[str]
    database_files: List[str]
    migration_files: List[str]
    model_files: List[str]
    entry_points: List[str]
    dependencies: Dict[str, str]
    patterns: Dict[str, List[str]]


@dataclass
class OptimizedConfig:
    """Configuração otimizada gerada"""
    analysis_config: Dict[str, Any]
    database_configs: List[DatabaseConfig]
    performance_settings: Dict[str, Any]
    monitoring_config: Dict[str, Any]
    security_settings: Dict[str, Any]
    output_settings: Dict[str, Any]
    recommendations: List[str]


class SmartDatabaseDetector:
    """Detector inteligente de configurações de banco de dados"""
    
    def __init__(self):
        self.db_patterns = {
            'postgresql': {
                'connection_strings': [
                    r'postgresql://(?:(\w+)(?::([^@]+))?@)?([^:/]+)(?::(\d+))?/(\w+)',
                    r'postgres://(?:(\w+)(?::([^@]+))?@)?([^:/]+)(?::(\d+))?/(\w+)',
                    r'psycopg2\.connect\s*\([^)]*host\s*=\s*[\'"]([^\'\"]+)[\'"]',
                ],
                'config_keys': [
                    'DATABASE_URL', 'POSTGRES_URL', 'POSTGRESQL_URL',
                    'DB_HOST', 'POSTGRES_HOST', 'DB_USER', 'POSTGRES_USER',
                    'DB_NAME', 'POSTGRES_DB', 'DB_PASSWORD', 'POSTGRES_PASSWORD'
                ],
                'imports': ['psycopg2', 'asyncpg', 'sqlalchemy'],
                'default_port': 5432
            },
            'mysql': {
                'connection_strings': [
                    r'mysql://(?:(\w+)(?::([^@]+))?@)?([^:/]+)(?::(\d+))?/(\w+)',
                    r'mysql\+pymysql://(?:(\w+)(?::([^@]+))?@)?([^:/]+)(?::(\d+))?/(\w+)',
                ],
                'config_keys': [
                    'MYSQL_URL', 'DB_HOST', 'MYSQL_HOST', 'DB_USER', 'MYSQL_USER',
                    'DB_NAME', 'MYSQL_DATABASE', 'DB_PASSWORD', 'MYSQL_PASSWORD'
                ],
                'imports': ['pymysql', 'mysql.connector', 'MySQLdb'],
                'default_port': 3306
            },
            'mongodb': {
                'connection_strings': [
                    r'mongodb://(?:(\w+)(?::([^@]+))?@)?([^:/]+)(?::(\d+))?/(\w+)',
                    r'mongodb\+srv://(?:(\w+)(?::([^@]+))?@)?([^:/]+)/(\w+)',
                ],
                'config_keys': [
                    'MONGODB_URL', 'MONGO_URL', 'MONGODB_URI', 'MONGO_URI',
                    'MONGO_HOST', 'MONGODB_HOST', 'MONGO_DB', 'MONGODB_DATABASE'
                ],
                'imports': ['pymongo', 'motor'],
                'default_port': 27017
            },
            'redis': {
                'connection_strings': [
                    r'redis://(?:(\w+)(?::([^@]+))?@)?([^:/]+)(?::(\d+))?/(\d+)',
                ],
                'config_keys': [
                    'REDIS_URL', 'CACHE_URL', 'REDIS_HOST', 'REDIS_PORT',
                    'REDIS_PASSWORD', 'REDIS_DB'
                ],
                'imports': ['redis', 'aioredis'],
                'default_port': 6379
            },
            'sqlite': {
                'connection_strings': [
                    r'sqlite:///([^?\s]+)',
                    r'sqlite://([^?\s]+)',
                ],
                'config_keys': [
                    'SQLITE_URL', 'DATABASE_FILE', 'DB_FILE', 'SQLITE_FILE'
                ],
                'imports': ['sqlite3'],
                'default_port': None
            }
        }
        
        self.framework_db_mappings = {
            'django': {
                'config_files': ['settings.py', 'settings/*.py'],
                'config_patterns': [
                    r"DATABASES\s*=\s*{[^}]*'ENGINE':\s*'[^']*\.(\w+)'",
                    r"'HOST':\s*'([^']*)'",
                    r"'PORT':\s*'([^']*)'",
                    r"'NAME':\s*'([^']*)'",
                    r"'USER':\s*'([^']*)'",
                    r"'PASSWORD':\s*'([^']*)'"
                ]
            },
            'flask': {
                'config_files': ['config.py', 'app.py', 'settings.py'],
                'config_patterns': [
                    r"SQLALCHEMY_DATABASE_URI\s*=\s*['\"]([^'\"]+)['\"]",
                    r"DATABASE_URL\s*=\s*['\"]([^'\"]+)['\"]"
                ]
            },
            'fastapi': {
                'config_files': ['main.py', 'config.py', 'settings.py'],
                'config_patterns': [
                    r"DATABASE_URL\s*=\s*['\"]([^'\"]+)['\"]",
                    r"SQLALCHEMY_DATABASE_URL\s*=\s*['\"]([^'\"]+)['\"]"
                ]
            },
            'airflow': {
                'config_files': ['airflow.cfg', 'airflow.conf'],
                'config_patterns': [
                    r"sql_alchemy_conn\s*=\s*([^\s]+)",
                    r"result_backend\s*=\s*([^\s]+)"
                ]
            }
        }
    
    def detect_databases(self, project_path: str) -> List[DatabaseConfig]:
        """Detecta todas as configurações de banco no projeto"""
        project_path = Path(project_path)
        detected_dbs = []
        
        # 1. Detecta via arquivos de configuração
        config_dbs = self._detect_from_config_files(project_path)
        detected_dbs.extend(config_dbs)
        
        # 2. Detecta via variáveis de ambiente
        env_dbs = self._detect_from_env_files(project_path)
        detected_dbs.extend(env_dbs)
        
        # 3. Detecta via código fonte
        code_dbs = self._detect_from_source_code(project_path)
        detected_dbs.extend(code_dbs)
        
        # 4. Detecta via arquivos Docker
        docker_dbs = self._detect_from_docker_files(project_path)
        detected_dbs.extend(docker_dbs)
        
        # 5. Remove duplicatas e valida
        unique_dbs = self._deduplicate_and_validate(detected_dbs)
        
        return unique_dbs
    
    def _detect_from_config_files(self, project_path: Path) -> List[DatabaseConfig]:
        """Detecta configurações em arquivos de configuração"""
        configs = []
        
        # Arquivos de configuração comuns
        config_files = [
            'config.json', 'config.yaml', 'config.yml', 'config.toml',
            'database.json', 'database.yaml', 'database.yml',
            'settings.json', 'settings.yaml', 'settings.yml',
            'app.json', 'app.yaml', 'app.yml'
        ]
        
        for config_file in config_files:
            file_path = project_path / config_file
            if file_path.exists():
                configs.extend(self._parse_config_file(file_path))
        
        # Busca recursiva por arquivos de configuração
        for config_file in project_path.rglob('*config*'):
            if config_file.is_file() and config_file.suffix in ['.json', '.yaml', '.yml', '.toml']:
                configs.extend(self._parse_config_file(config_file))
        
        return configs
    
    def _parse_config_file(self, file_path: Path) -> List[DatabaseConfig]:
        """Parse arquivo de configuração específico"""
        configs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.suffix == '.json':
                data = json.loads(content)
            elif file_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(content)
            elif file_path.suffix == '.toml':
                data = toml.loads(content)
            else:
                return configs
            
            # Extrai configurações de banco
            db_configs = self._extract_db_configs_from_dict(data, str(file_path))
            configs.extend(db_configs)
            
        except Exception as e:
            logging.warning(f"Failed to parse config file {file_path}: {e}")
        
        return configs
    
    def _extract_db_configs_from_dict(self, data: Dict[str, Any], source_file: str) -> List[DatabaseConfig]:
        """Extrai configurações de banco de um dicionário"""
        configs = []
        
        def search_dict(obj: Any, path: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Verifica se é uma URL de conexão
                    if isinstance(value, str) and self._is_connection_string(value):
                        db_config = self._parse_connection_string(value, source_file)
                        if db_config:
                            configs.append(db_config)
                    
                    # Verifica se é uma configuração de banco estruturada
                    elif isinstance(value, dict) and self._looks_like_db_config(value):
                        db_config = self._parse_structured_config(value, source_file)
                        if db_config:
                            configs.append(db_config)
                    
                    # Busca recursiva
                    elif isinstance(value, (dict, list)):
                        search_dict(value, current_path)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_dict(item, f"{path}[{i}]")
        
        search_dict(data)
        return configs
    
    def _detect_from_env_files(self, project_path: Path) -> List[DatabaseConfig]:
        """Detecta configurações em arquivos de ambiente"""
        configs = []
        
        env_files = [
            '.env', '.env.local', '.env.development', '.env.production',
            '.env.staging', '.env.test', 'environment.env'
        ]
        
        for env_file in env_files:
            file_path = project_path / env_file
            if file_path.exists():
                try:
                    env_vars = dotenv_values(file_path)
                    db_config = self._parse_env_vars(env_vars, str(file_path))
                    if db_config:
                        configs.extend(db_config)
                except Exception as e:
                    logging.warning(f"Failed to parse env file {file_path}: {e}")
        
        return configs
    
    def _parse_env_vars(self, env_vars: Dict[str, str], source_file: str) -> List[DatabaseConfig]:
        """Parse variáveis de ambiente para configurações de banco"""
        configs = []
        
        # Procura por URLs de conexão completas
        for key, value in env_vars.items():
            if value and self._is_connection_string(value):
                db_config = self._parse_connection_string(value, source_file)
                if db_config:
                    configs.append(db_config)
        
        # Procura por configurações estruturadas
        for db_type in self.db_patterns:
            config_keys = self.db_patterns[db_type]['config_keys']
            
            # Verifica se há chaves relacionadas a este tipo de banco
            relevant_vars = {k: v for k, v in env_vars.items() 
                           if any(key_pattern.lower() in k.lower() for key_pattern in config_keys)}
            
            if relevant_vars:
                db_config = self._build_config_from_env_vars(relevant_vars, db_type, source_file)
                if db_config:
                    configs.append(db_config)
        
        return configs
    
    def _detect_from_source_code(self, project_path: Path) -> List[DatabaseConfig]:
        """Detecta configurações no código fonte"""
        configs = []
        
        for py_file in project_path.rglob('*.py'):
            try:
                if py_file.stat().st_size > 1024 * 1024:  # Skip files > 1MB
                    continue
                
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Detecta strings de conexão no código
                file_configs = self._extract_connections_from_code(content, str(py_file))
                configs.extend(file_configs)
                
            except Exception as e:
                logging.debug(f"Failed to analyze {py_file}: {e}")
        
        return configs
    
    def _extract_connections_from_code(self, content: str, source_file: str) -> List[DatabaseConfig]:
        """Extrai configurações de conexão do código"""
        configs = []
        
        # Padrões para diferentes tipos de banco
        for db_type, patterns in self.db_patterns.items():
            for pattern in patterns['connection_strings']:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        db_config = self._create_config_from_match(match, db_type, source_file)
                        if db_config:
                            configs.append(db_config)
                    except Exception as e:
                        logging.debug(f"Failed to parse connection string: {e}")
        
        # Padrões específicos para frameworks
        framework_configs = self._detect_framework_specific_configs(content, source_file)
        configs.extend(framework_configs)
        
        return configs
    
    def _detect_from_docker_files(self, project_path: Path) -> List[DatabaseConfig]:
        """Detecta configurações em arquivos Docker"""
        configs = []
        
        docker_files = [
            'docker-compose.yml', 'docker-compose.yaml',
            'docker-compose.override.yml', 'docker-compose.dev.yml',
            'docker-compose.prod.yml', 'Dockerfile'
        ]
        
        for docker_file in docker_files:
            file_path = project_path / docker_file
            if file_path.exists():
                configs.extend(self._parse_docker_file(file_path))
        
        return configs
    
    def _parse_docker_file(self, file_path: Path) -> List[DatabaseConfig]:
        """Parse arquivo Docker para configurações de banco"""
        configs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'docker-compose' in file_path.name:
                # Parse docker-compose.yml
                data = yaml.safe_load(content)
                configs.extend(self._extract_docker_compose_dbs(data, str(file_path)))
            else:
                # Parse Dockerfile
                configs.extend(self._extract_dockerfile_dbs(content, str(file_path)))
                
        except Exception as e:
            logging.warning(f"Failed to parse Docker file {file_path}: {e}")
        
        return configs
    
    def _extract_docker_compose_dbs(self, data: Dict[str, Any], source_file: str) -> List[DatabaseConfig]:
        """Extrai configurações de banco do docker-compose"""
        configs = []
        
        services = data.get('services', {})
        
        for service_name, service_config in services.items():
            image = service_config.get('image', '')
            environment = service_config.get('environment', {})
            
            # Detecta serviços de banco pela imagem
            if any(db in image.lower() for db in ['postgres', 'mysql', 'mongo', 'redis']):
                db_config = self._create_docker_db_config(
                    service_name, image, environment, source_file
                )
                if db_config:
                    configs.append(db_config)
        
        return configs
    
    def _is_connection_string(self, value: str) -> bool:
        """Verifica se uma string é uma URL de conexão de banco"""
        db_schemes = ['postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'sqlite']
        return any(value.lower().startswith(f'{scheme}://') for scheme in db_schemes)
    
    def _parse_connection_string(self, connection_string: str, source_file: str) -> Optional[DatabaseConfig]:
        """Parse uma string de conexão"""
        try:
            parsed = urlparse(connection_string)
            
            db_type = parsed.scheme.lower()
            if db_type == 'postgres':
                db_type = 'postgresql'
            
            return DatabaseConfig(
                db_type=db_type,
                host=parsed.hostname or 'localhost',
                port=parsed.port or self.db_patterns.get(db_type, {}).get('default_port', 5432),
                database=parsed.path.lstrip('/') if parsed.path else '',
                username=parsed.username or '',
                password=parsed.password or '',
                connection_string=connection_string,
                source_file=source_file,
                confidence=0.9
            )
        except Exception as e:
            logging.debug(f"Failed to parse connection string {connection_string}: {e}")
            return None
    
    def _looks_like_db_config(self, config: Dict[str, Any]) -> bool:
        """Verifica se um dict parece uma configuração de banco"""
        db_indicators = ['host', 'port', 'database', 'user', 'username', 'password', 'engine', 'driver']
        return sum(1 for key in config.keys() if key.lower() in db_indicators) >= 2
    
    def _parse_structured_config(self, config: Dict[str, Any], source_file: str) -> Optional[DatabaseConfig]:
        """Parse configuração estruturada de banco"""
        try:
            # Mapeia chaves comuns
            key_mappings = {
                'host': ['host', 'hostname', 'server'],
                'port': ['port'],
                'database': ['database', 'db', 'name', 'db_name'],
                'username': ['user', 'username', 'login'],
                'password': ['password', 'passwd', 'pwd'],
                'db_type': ['engine', 'driver', 'dialect', 'type']
            }
            
            mapped_config = {}
            for target_key, possible_keys in key_mappings.items():
                for key in possible_keys:
                    if key in config:
                        mapped_config[target_key] = config[key]
                        break
            
            # Determina tipo do banco
            db_type = mapped_config.get('db_type', 'postgresql')
            if 'postgres' in db_type.lower():
                db_type = 'postgresql'
            elif 'mysql' in db_type.lower():
                db_type = 'mysql'
            elif 'mongo' in db_type.lower():
                db_type = 'mongodb'
            
            return DatabaseConfig(
                db_type=db_type,
                host=mapped_config.get('host', 'localhost'),
                port=int(mapped_config.get('port', 5432)),
                database=mapped_config.get('database', ''),
                username=mapped_config.get('username', ''),
                password=mapped_config.get('password', ''),
                source_file=source_file,
                confidence=0.8
            )
        except Exception as e:
            logging.debug(f"Failed to parse structured config: {e}")
            return None
    
    def _deduplicate_and_validate(self, configs: List[DatabaseConfig]) -> List[DatabaseConfig]:
        """Remove duplicatas e valida configurações"""
        unique_configs = []
        seen_configs = set()
        
        for config in configs:
            # Cria uma chave única baseada nas propriedades principais
            key = f"{config.db_type}://{config.host}:{config.port}/{config.database}"
            
            if key not in seen_configs:
                seen_configs.add(key)
                unique_configs.append(config)
            else:
                # Se já existe, mantém a com maior confiança
                for i, existing in enumerate(unique_configs):
                    existing_key = f"{existing.db_type}://{existing.host}:{existing.port}/{existing.database}"
                    if existing_key == key and config.confidence > existing.confidence:
                        unique_configs[i] = config
                        break
        
        return unique_configs


class SmartProjectAnalyzer:
    """Analisador inteligente de estrutura de projeto"""
    
    def __init__(self):
        self.framework_patterns = {
            'django': {
                'files': ['manage.py', 'settings.py', 'urls.py'],
                'imports': ['django', 'from django'],
                'indicators': ['INSTALLED_APPS', 'urlpatterns', 'Django'],
                'directories': ['apps/', 'templates/', 'static/']
            },
            'flask': {
                'files': ['app.py', 'run.py', 'wsgi.py'],
                'imports': ['flask', 'from flask'],
                'indicators': ['@app.route', 'Flask(__name__)'],
                'directories': ['templates/', 'static/']
            },
            'fastapi': {
                'files': ['main.py', 'app.py'],
                'imports': ['fastapi', 'from fastapi'],
                'indicators': ['@app.get', '@app.post', 'FastAPI()'],
                'directories': ['routers/', 'models/']
            },
            'airflow': {
                'files': ['airflow.cfg', 'dags/'],
                'imports': ['airflow', 'from airflow'],
                'indicators': ['DAG', 'BashOperator', 'PythonOperator'],
                'directories': ['dags/', 'plugins/', 'include/']
            },
            'jupyter': {
                'files': ['*.ipynb', 'jupyter_notebook_config.py'],
                'imports': ['jupyter', 'IPython'],
                'indicators': ['get_ipython()', 'display('],
                'directories': ['notebooks/']
            },
            'streamlit': {
                'files': ['streamlit_app.py', 'app.py'],
                'imports': ['streamlit', 'import streamlit'],
                'indicators': ['st.', 'streamlit.'],
                'directories': ['pages/', 'components/']
            }
        }
    
    def analyze_project_structure(self, project_path: str) -> ProjectStructure:
        """Analisa a estrutura completa do projeto"""
        project_path = Path(project_path)
        
        # Detecta framework e tipo
        framework_info = self._detect_framework(project_path)
        
        # Analisa estrutura de diretórios
        directory_structure = self._analyze_directories(project_path)
        
        # Detecta arquivos importantes
        important_files = self._find_important_files(project_path)
        
        # Analisa dependências
        dependencies = self._analyze_dependencies(project_path)
        
        # Detecta padrões específicos
        patterns = self._detect_patterns(project_path, framework_info['framework'])
        
        return ProjectStructure(
            type=framework_info['type'],
            framework=framework_info['framework'],
            language=framework_info['language'],
            version=framework_info['version'],
            main_directories=directory_structure['main_dirs'],
            config_files=important_files['config_files'],
            database_files=important_files['database_files'],
            migration_files=important_files['migration_files'],
            model_files=important_files['model_files'],
            entry_points=important_files['entry_points'],
            dependencies=dependencies,
            patterns=patterns
        )
    
    def _detect_framework(self, project_path: Path) -> Dict[str, str]:
        """Detecta framework e tipo do projeto"""
        scores = {framework: 0 for framework in self.framework_patterns}
        
        # Analisa arquivos
        for framework, patterns in self.framework_patterns.items():
            for file_pattern in patterns['files']:
                if '*' in file_pattern:
                    if list(project_path.rglob(file_pattern)):
                        scores[framework] += 3
                else:
                    if (project_path / file_pattern).exists():
                        scores[framework] += 3
        
        # Analisa código
        for py_file in project_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for framework, patterns in self.framework_patterns.items():
                    for import_pattern in patterns['imports']:
                        if import_pattern in content:
                            scores[framework] += 2
                    
                    for indicator in patterns['indicators']:
                        if indicator in content:
                            scores[framework] += 1
            except:
                continue
        
        # Determina framework principal
        best_framework = max(scores.items(), key=lambda x: x[1])
        
        return {
            'framework': best_framework[0] if best_framework[1] > 0 else 'generic',
            'type': 'web_application' if best_framework[0] in ['django', 'flask', 'fastapi'] else 'data_processing',
            'language': 'python',
            'version': '1.0.0'  # TODO: Detectar versão
        }
    
    def _analyze_directories(self, project_path: Path) -> Dict[str, List[str]]:
        """Analisa estrutura de diretórios"""
        main_dirs = []
        
        for item in project_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                main_dirs.append(item.name)
        
        return {'main_dirs': main_dirs}
    
    def _find_important_files(self, project_path: Path) -> Dict[str, List[str]]:
        """Encontra arquivos importantes por categoria"""
        config_extensions = ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']
        
        files = {
            'config_files': [],
            'database_files': [],
            'migration_files': [],
            'model_files': [],
            'entry_points': []
        }
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                name = file_path.name.lower()
                relative_path = str(file_path.relative_to(project_path))
                
                # Arquivos de configuração
                if file_path.suffix in config_extensions or 'config' in name or 'settings' in name:
                    files['config_files'].append(relative_path)
                
                # Arquivos de migration
                if 'migration' in str(file_path) or 'migrate' in name:
                    files['migration_files'].append(relative_path)
                
                # Arquivos de modelo
                if 'model' in name and file_path.suffix == '.py':
                    files['model_files'].append(relative_path)
                
                # Pontos de entrada
                if name in ['main.py', 'app.py', 'run.py', 'manage.py', 'server.py']:
                    files['entry_points'].append(relative_path)
        
        return files
    
    def _analyze_dependencies(self, project_path: Path) -> Dict[str, str]:
        """Analisa dependências do projeto"""
        dependencies = {}
        
        # requirements.txt
        req_file = project_path / 'requirements.txt'
        if req_file.exists():
            dependencies.update(self._parse_requirements_file(req_file))
        
        # pyproject.toml
        pyproject_file = project_path / 'pyproject.toml'
        if pyproject_file.exists():
            dependencies.update(self._parse_pyproject_toml(pyproject_file))
        
        # setup.py
        setup_file = project_path / 'setup.py'
        if setup_file.exists():
            dependencies.update(self._parse_setup_py(setup_file))
        
        return dependencies
    
    def _parse_requirements_file(self, file_path: Path) -> Dict[str, str]:
        """Parse requirements.txt"""
        deps = {}
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '==' in line:
                            name, version = line.split('==', 1)
                            deps[name.strip()] = version.strip()
                        else:
                            deps[line] = 'latest'
        except:
            pass
        return deps
    
    def _parse_pyproject_toml(self, file_path: Path) -> Dict[str, str]:
        """Parse pyproject.toml"""
        deps = {}
        try:
            with open(file_path, 'r') as f:
                data = toml.load(f)
                project_deps = data.get('project', {}).get('dependencies', [])
                for dep in project_deps:
                    if '>=' in dep:
                        name = dep.split('>=')[0].strip()
                        deps[name] = 'latest'
                    else:
                        deps[dep] = 'latest'
        except:
            pass
        return deps
    
    def _parse_setup_py(self, file_path: Path) -> Dict[str, str]:
        """Parse setup.py (simplified)"""
        # Implementação simplificada para detectar dependências básicas
        return {}
    
    def _detect_patterns(self, project_path: Path, framework: str) -> Dict[str, List[str]]:
        """Detecta padrões específicos do framework"""
        patterns = {
            'sql_patterns': [],
            'orm_patterns': [],
            'api_patterns': [],
            'custom_patterns': []
        }
        
        # Padrões específicos por framework
        if framework == 'django':
            patterns['orm_patterns'] = [
                r'class\s+(\w+)\s*\(.*Model\)',
                r'(\w+)\.objects\.',
                r'Meta:\s*\n\s*db_table\s*=\s*[\'"](\w+)[\'"]'
            ]
        elif framework == 'flask':
            patterns['sql_patterns'] = [
                r'db\.session\.',
                r'query\.',
                r'SELECT.*FROM\s+(\w+)'
            ]
        elif framework == 'airflow':
            patterns['custom_patterns'] = [
                r'BashOperator',
                r'PythonOperator',
                r'SqlOperator'
            ]
        
        return patterns


class SmartConfigGenerator:
    """Gerador inteligente de configurações otimizadas"""
    
    def __init__(self):
        self.db_detector = SmartDatabaseDetector()
        self.project_analyzer = SmartProjectAnalyzer()
    
    def generate_optimized_config(self, project_path: str) -> OptimizedConfig:
        """Gera configuração otimizada para o projeto"""
        project_path = Path(project_path)
        
        # Analisa projeto
        project_structure = self.project_analyzer.analyze_project_structure(project_path)
        
        # Detecta bancos de dados
        database_configs = self.db_detector.detect_databases(project_path)
        
        # Gera configurações otimizadas
        analysis_config = self._generate_analysis_config(project_structure, database_configs)
        performance_settings = self._generate_performance_settings(project_structure)
        monitoring_config = self._generate_monitoring_config(project_structure)
        security_settings = self._generate_security_settings(project_structure)
        output_settings = self._generate_output_settings(project_structure)
        recommendations = self._generate_recommendations(project_structure, database_configs)
        
        return OptimizedConfig(
            analysis_config=analysis_config,
            database_configs=database_configs,
            performance_settings=performance_settings,
            monitoring_config=monitoring_config,
            security_settings=security_settings,
            output_settings=output_settings,
            recommendations=recommendations
        )
    
    def _generate_analysis_config(self, structure: ProjectStructure, 
                                db_configs: List[DatabaseConfig]) -> Dict[str, Any]:
        """Gera configuração de análise"""
        config = {
            'project_type': structure.framework,
            'source_directories': structure.main_directories,
            'exclude_patterns': [
                '__pycache__/', '*.pyc', '.git/', 'node_modules/',
                'venv/', 'env/', '.env/', 'dist/', 'build/'
            ],
            'file_patterns': ['*.py'],
            'database_frameworks': self._detect_db_frameworks(structure),
            'custom_patterns': structure.patterns,
            'auto_detect_tables': True,
            'follow_imports': True,
            'analyze_migrations': len(structure.migration_files) > 0,
            'analyze_models': len(structure.model_files) > 0
        }
        
        # Configurações específicas por framework
        if structure.framework == 'django':
            config.update({
                'django_specific': True,
                'settings_module': self._find_django_settings(structure),
                'analyze_admin': True,
                'analyze_views': True
            })
        elif structure.framework == 'airflow':
            config.update({
                'airflow_specific': True,
                'dag_directories': ['dags/'],
                'analyze_operators': True,
                'analyze_connections': True
            })
        elif structure.framework in ['flask', 'fastapi']:
            config.update({
                'web_framework': structure.framework,
                'analyze_routes': True,
                'analyze_blueprints': True
            })
        
        return config
    
    def _generate_performance_settings(self, structure: ProjectStructure) -> Dict[str, Any]:
        """Gera configurações de performance"""
        # Ajusta configurações baseado no tamanho do projeto
        total_files = len(structure.config_files) + len(structure.model_files)
        
        if total_files > 1000:
            # Projeto grande
            return {
                'parallel_processing': True,
                'max_workers': 8,
                'batch_size': 100,
                'memory_limit_mb': 2048,
                'cache_enabled': True,
                'cache_ttl': 3600,
                'lazy_loading': True
            }
        elif total_files > 100:
            # Projeto médio
            return {
                'parallel_processing': True,
                'max_workers': 4,
                'batch_size': 50,
                'memory_limit_mb': 1024,
                'cache_enabled': True,
                'cache_ttl': 1800,
                'lazy_loading': False
            }
        else:
            # Projeto pequeno
            return {
                'parallel_processing': False,
                'max_workers': 2,
                'batch_size': 20,
                'memory_limit_mb': 512,
                'cache_enabled': False,
                'cache_ttl': 900,
                'lazy_loading': False
            }
    
    def _generate_monitoring_config(self, structure: ProjectStructure) -> Dict[str, Any]:
        """Gera configuração de monitoramento"""
        return {
            'enabled': True,
            'watch_directories': structure.main_directories[:5],  # Top 5 directories
            'file_patterns': ['*.py', '*.sql'],
            'auto_analysis': False,
            'notification_methods': ['log', 'file'],
            'metrics_collection': True,
            'dashboard_enabled': structure.framework in ['django', 'flask', 'fastapi'],
            'real_time_updates': True,
            'alert_thresholds': {
                'new_tables': 5,
                'modified_files': 10,
                'analysis_time': 300
            }
        }
    
    def _generate_security_settings(self, structure: ProjectStructure) -> Dict[str, Any]:
        """Gera configurações de segurança"""
        return {
            'enabled': True,
            'scan_for_credentials': True,
            'scan_for_sql_injection': True,
            'validate_connections': False,  # Don't validate by default for safety
            'encrypt_sensitive_data': True,
            'audit_logging': True,
            'access_control': structure.framework in ['django', 'flask', 'fastapi'],
            'security_headers': True,
            'vulnerability_scanning': True
        }
    
    def _generate_output_settings(self, structure: ProjectStructure) -> Dict[str, Any]:
        """Gera configurações de saída"""
        return {
            'formats': ['html', 'json'],
            'include_visualizations': True,
            'generate_summaries': True,
            'create_diagrams': True,
            'export_data': True,
            'output_directory': 'bw_automate_reports',
            'timestamp_reports': True,
            'compress_output': len(structure.main_directories) > 10,
            'detailed_logging': True
        }
    
    def _generate_recommendations(self, structure: ProjectStructure, 
                                db_configs: List[DatabaseConfig]) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        # Recomendações baseadas na estrutura
        if not structure.migration_files:
            recommendations.append("Consider implementing database migrations for better version control")
        
        if not structure.model_files:
            recommendations.append("Consider using ORM models for better database abstraction")
        
        # Recomendações baseadas nos bancos detectados
        if len(db_configs) == 0:
            recommendations.append("No database configurations detected. Check your configuration files.")
        elif len(db_configs) > 3:
            recommendations.append("Multiple database configurations detected. Consider database consolidation.")
        
        for db_config in db_configs:
            if db_config.password and db_config.password != '':
                recommendations.append(f"Database password found in {db_config.source_file}. Consider using environment variables.")
        
        # Recomendações baseadas no framework
        if structure.framework == 'django' and 'django.contrib.admin' not in str(structure.dependencies):
            recommendations.append("Consider enabling Django admin for better database management")
        
        if structure.framework == 'airflow' and not any('sensor' in d.lower() for d in structure.main_directories):
            recommendations.append("Consider implementing sensors for better data pipeline monitoring")
        
        # Recomendações de performance
        if len(structure.main_directories) > 20:
            recommendations.append("Large project detected. Enable parallel processing for better performance.")
        
        return recommendations
    
    def _detect_db_frameworks(self, structure: ProjectStructure) -> List[str]:
        """Detecta frameworks de banco baseado nas dependências"""
        frameworks = []
        
        deps_lower = {k.lower(): v for k, v in structure.dependencies.items()}
        
        if any('django' in dep for dep in deps_lower):
            frameworks.append('django_orm')
        if any('sqlalchemy' in dep for dep in deps_lower):
            frameworks.append('sqlalchemy')
        if any('psycopg2' in dep for dep in deps_lower):
            frameworks.append('psycopg2')
        if any('pymongo' in dep for dep in deps_lower):
            frameworks.append('pymongo')
        
        return frameworks or ['unknown']
    
    def _find_django_settings(self, structure: ProjectStructure) -> Optional[str]:
        """Encontra módulo de settings do Django"""
        for config_file in structure.config_files:
            if 'settings.py' in config_file:
                # Converte caminho do arquivo para módulo Python
                module_path = config_file.replace('/', '.').replace('.py', '')
                return module_path
        return None


# Interface principal
class SmartAutoDetectionSystem:
    """Sistema principal de auto-detecção inteligente"""
    
    def __init__(self):
        self.config_generator = SmartConfigGenerator()
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def auto_configure_project(self, project_path: str, 
                             output_path: str = None) -> Dict[str, Any]:
        """Configura automaticamente um projeto"""
        self.logger.info(f"Starting auto-configuration for project: {project_path}")
        
        try:
            # Gera configuração otimizada
            config = self.config_generator.generate_optimized_config(project_path)
            
            # Salva configuração
            output_path = output_path or str(Path(project_path) / 'bw_automate_config.json')
            self._save_config(config, output_path)
            
            # Gera scripts de integração
            scripts = self._generate_integration_scripts(project_path, config)
            
            result = {
                'success': True,
                'config_file': output_path,
                'optimized_config': asdict(config),
                'integration_scripts': scripts,
                'recommendations': config.recommendations,
                'detected_databases': len(config.database_configs),
                'project_type': config.analysis_config.get('project_type', 'unknown')
            }
            
            self.logger.info("Auto-configuration completed successfully!")
            return result
            
        except Exception as e:
            self.logger.error(f"Auto-configuration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommendations': ["Check project path and permissions"]
            }
    
    def _save_config(self, config: OptimizedConfig, output_path: str):
        """Salva configuração em arquivo"""
        config_dict = asdict(config)
        
        # Converte objetos não serializáveis
        config_dict['database_configs'] = [asdict(db) for db in config.database_configs]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def _generate_integration_scripts(self, project_path: str, 
                                    config: OptimizedConfig) -> Dict[str, str]:
        """Gera scripts de integração personalizados"""
        scripts = {}
        
        # Script principal
        main_script = f'''#!/usr/bin/env python3
"""
Auto-generated BW_AUTOMATE integration script
Generated on: {datetime.now().isoformat()}
Project type: {config.analysis_config.get('project_type', 'unknown')}
"""

import sys
from pathlib import Path

# Add BW_AUTOMATE to path
sys.path.insert(0, str(Path(__file__).parent / "bw_automate"))

from run_analysis import BWAutomate

def main():
    # Load auto-generated configuration
    bw = BWAutomate(config_path="bw_automate_config.json")
    
    # Run optimized analysis
    results = bw.analyze_project(
        project_root=".",
        output_dir="{config.output_settings['output_directory']}"
    )
    
    print(f"Analysis completed!")
    print(f"Found {{results.get('total_tables', 0)}} database tables")
    print(f"Analyzed {{results.get('total_files', 0)}} files")
    print(f"Generated reports in: {config.output_settings['output_directory']}/")

if __name__ == "__main__":
    main()
'''
        scripts['auto_run_analysis.py'] = main_script
        
        # Script de configuração
        config_script = f'''#!/usr/bin/env python3
"""
Auto-configuration validation and setup script
"""

import json
import os
from pathlib import Path

def validate_configuration():
    """Validate the auto-generated configuration"""
    config_file = "bw_automate_config.json"
    
    if not Path(config_file).exists():
        print(f"❌ Configuration file not found: {{config_file}}")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print("✅ Configuration file is valid")
        print(f"Project type: {{config['analysis_config']['project_type']}}")
        print(f"Databases detected: {{len(config['database_configs'])}}")
        print(f"Source directories: {{', '.join(config['analysis_config']['source_directories'])}}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {{e}}")
        return False

def setup_environment():
    """Setup the environment for BW_AUTOMATE"""
    # Create output directory
    output_dir = "{config.output_settings['output_directory']}"
    Path(output_dir).mkdir(exist_ok=True)
    print(f"✅ Output directory created: {{output_dir}}")
    
    # Check BW_AUTOMATE availability
    bw_dir = Path("bw_automate")
    if not bw_dir.exists():
        print("⚠ BW_AUTOMATE directory not found. Please ensure it's installed.")
        return False
    
    print("✅ BW_AUTOMATE directory found")
    return True

def main():
    print("🔧 BW_AUTOMATE Auto-Configuration Setup")
    print("=" * 40)
    
    if validate_configuration() and setup_environment():
        print("\\n🎉 Setup completed successfully!")
        print("\\nNext steps:")
        print("1. Run: python auto_run_analysis.py")
        print("2. Check results in: {config.output_settings['output_directory']}/")
    else:
        print("\\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
'''
        scripts['setup_auto_config.py'] = config_script
        
        return scripts


# CLI Interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Auto-Detection & Configuration System")
    parser.add_argument("project_path", help="Path to project to analyze and configure")
    parser.add_argument("--output", "-o", help="Output path for configuration file")
    parser.add_argument("--save-scripts", action="store_true", help="Save integration scripts")
    parser.add_argument("--detect-only", action="store_true", help="Only detect, don't generate config")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize system
    auto_detection = SmartAutoDetectionSystem()
    
    if args.detect_only:
        # Only detection mode
        detector = SmartDatabaseDetector()
        analyzer = SmartProjectAnalyzer()
        
        print("🔍 Detecting project structure...")
        structure = analyzer.analyze_project_structure(args.project_path)
        
        print("🔍 Detecting database configurations...")
        databases = detector.detect_databases(args.project_path)
        
        print(f"\\n📊 Detection Results:")
        print(f"  Project Type: {structure.framework}")
        print(f"  Language: {structure.language}")
        print(f"  Main Directories: {', '.join(structure.main_directories[:5])}")
        print(f"  Config Files: {len(structure.config_files)}")
        print(f"  Model Files: {len(structure.model_files)}")
        print(f"  Migration Files: {len(structure.migration_files)}")
        print(f"  Dependencies: {len(structure.dependencies)}")
        
        print(f"\\n🗄️ Database Configurations:")
        for i, db in enumerate(databases, 1):
            print(f"  {i}. {db.db_type}://{db.host}:{db.port}/{db.database}")
            print(f"     Source: {db.source_file}")
            print(f"     Confidence: {db.confidence:.1%}")
    
    else:
        # Full auto-configuration
        result = auto_detection.auto_configure_project(
            args.project_path, 
            args.output
        )
        
        if result['success']:
            print("🎉 Auto-configuration completed successfully!")
            print(f"\\n📊 Configuration Summary:")
            print(f"  Project Type: {result['project_type']}")
            print(f"  Databases Detected: {result['detected_databases']}")
            print(f"  Config File: {result['config_file']}")
            
            if result['recommendations']:
                print(f"\\n💡 Recommendations:")
                for rec in result['recommendations']:
                    print(f"  • {rec}")
            
            if args.save_scripts:
                # Save integration scripts
                project_path = Path(args.project_path)
                for script_name, script_content in result['integration_scripts'].items():
                    script_path = project_path / script_name
                    with open(script_path, 'w') as f:
                        f.write(script_content)
                    script_path.chmod(0o755)  # Make executable
                    print(f"  Script saved: {script_path}")
        
        else:
            print("❌ Auto-configuration failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
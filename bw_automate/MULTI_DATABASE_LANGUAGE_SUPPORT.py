#!/usr/bin/env python3
"""
MULTI-DATABASE & MULTI-LANGUAGE SUPPORT - BW AUTOMATE SYSTEM
Sistema universal de suporte para múltiplos bancos de dados e linguagens
Conectores especializados para PostgreSQL, MySQL, Oracle, SQL Server, MongoDB, Cassandra
Suporte para Python, Java, Scala, R, Go, Node.js, PHP, C#, C++
"""

import os
import re
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import subprocess
import tempfile

# Database connectors
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Installing psycopg2 for PostgreSQL...")
    os.system("pip install psycopg2-binary")
    import psycopg2
    import psycopg2.extras

try:
    import pymongo
except ImportError:
    print("Installing pymongo for MongoDB...")
    os.system("pip install pymongo")
    import pymongo

try:
    import mysql.connector
except ImportError:
    print("Installing mysql-connector for MySQL...")
    os.system("pip install mysql-connector-python")
    import mysql.connector

try:
    import cx_Oracle
except ImportError:
    print("Installing cx_Oracle for Oracle...")
    os.system("pip install cx_Oracle")
    try:
        import cx_Oracle
    except:
        print("⚠ Oracle client libraries not available, Oracle support disabled")
        cx_Oracle = None

try:
    import pyodbc
except ImportError:
    print("Installing pyodbc for SQL Server...")
    os.system("pip install pyodbc")
    try:
        import pyodbc
    except:
        print("⚠ ODBC drivers not available, SQL Server support limited")
        pyodbc = None

try:
    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider
except ImportError:
    print("Installing cassandra-driver for Cassandra...")
    os.system("pip install cassandra-driver")
    try:
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
    except:
        print("⚠ Cassandra driver not available")
        Cluster = None

try:
    import redis
except ImportError:
    print("Installing redis...")
    os.system("pip install redis")
    import redis


class DatabaseType(Enum):
    """Tipos de banco de dados suportados"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"
    CASSANDRA = "cassandra"
    REDIS = "redis"
    SQLITE = "sqlite"


class LanguageType(Enum):
    """Linguagens de programação suportadas"""
    PYTHON = "python"
    JAVA = "java"
    SCALA = "scala"
    R = "r"
    GO = "go"
    NODEJS = "nodejs"
    PHP = "php"
    CSHARP = "csharp"
    CPP = "cpp"
    RUBY = "ruby"
    KOTLIN = "kotlin"
    GROOVY = "groovy"


@dataclass
class DatabaseConnection:
    """Configuração de conexão com banco de dados"""
    db_type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str
    schema: Optional[str] = None
    ssl_mode: Optional[str] = None
    connection_params: Dict[str, Any] = None


@dataclass
class TableReference:
    """Referência de tabela encontrada no código"""
    table_name: str
    database_type: DatabaseType
    language: LanguageType
    file_path: str
    line_number: int
    context: str
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE, etc.
    confidence_score: float = 1.0
    schema_name: Optional[str] = None


@dataclass
class LanguagePattern:
    """Padrão de código para detecção de tabelas"""
    language: LanguageType
    patterns: List[str]
    db_patterns: Dict[DatabaseType, List[str]]
    file_extensions: List[str]
    import_patterns: List[str]


class DatabaseConnector(ABC):
    """Interface base para conectores de banco de dados"""
    
    @abstractmethod
    def connect(self, connection: DatabaseConnection) -> Any:
        """Conecta ao banco de dados"""
        pass
    
    @abstractmethod
    def get_tables(self, connection_obj: Any) -> List[str]:
        """Retorna lista de tabelas"""
        pass
    
    @abstractmethod
    def get_table_schema(self, connection_obj: Any, table_name: str, schema: str = None) -> Dict[str, Any]:
        """Retorna esquema da tabela"""
        pass
    
    @abstractmethod
    def validate_table_exists(self, connection_obj: Any, table_name: str, schema: str = None) -> bool:
        """Valida se tabela existe"""
        pass
    
    @abstractmethod
    def close(self, connection_obj: Any):
        """Fecha conexão"""
        pass


class PostgreSQLConnector(DatabaseConnector):
    """Conector para PostgreSQL"""
    
    def connect(self, connection: DatabaseConnection) -> psycopg2.extensions.connection:
        conn_params = {
            'host': connection.host,
            'port': connection.port,
            'database': connection.database,
            'user': connection.username,
            'password': connection.password
        }
        
        if connection.ssl_mode:
            conn_params['sslmode'] = connection.ssl_mode
        
        if connection.connection_params:
            conn_params.update(connection.connection_params)
        
        return psycopg2.connect(**conn_params)
    
    def get_tables(self, connection_obj: psycopg2.extensions.connection) -> List[str]:
        cursor = connection_obj.cursor()
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, connection_obj: psycopg2.extensions.connection, 
                        table_name: str, schema: str = None) -> Dict[str, Any]:
        cursor = connection_obj.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        schema_condition = f"AND table_schema = '{schema}'" if schema else "AND table_schema = 'public'"
        
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}' {schema_condition}
            ORDER BY ordinal_position
        """)
        
        columns = [dict(row) for row in cursor.fetchall()]
        
        return {
            'table_name': table_name,
            'schema': schema or 'public',
            'columns': columns
        }
    
    def validate_table_exists(self, connection_obj: psycopg2.extensions.connection, 
                             table_name: str, schema: str = None) -> bool:
        cursor = connection_obj.cursor()
        schema_condition = f"AND schemaname = '{schema}'" if schema else "AND schemaname = 'public'"
        
        cursor.execute(f"""
            SELECT 1 FROM pg_tables 
            WHERE tablename = '{table_name}' {schema_condition}
        """)
        
        return cursor.fetchone() is not None
    
    def close(self, connection_obj: psycopg2.extensions.connection):
        connection_obj.close()


class MySQLConnector(DatabaseConnector):
    """Conector para MySQL"""
    
    def connect(self, connection: DatabaseConnection) -> mysql.connector.MySQLConnection:
        conn_params = {
            'host': connection.host,
            'port': connection.port,
            'database': connection.database,
            'user': connection.username,
            'password': connection.password
        }
        
        if connection.connection_params:
            conn_params.update(connection.connection_params)
        
        return mysql.connector.connect(**conn_params)
    
    def get_tables(self, connection_obj: mysql.connector.MySQLConnection) -> List[str]:
        cursor = connection_obj.cursor()
        cursor.execute("SHOW TABLES")
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, connection_obj: mysql.connector.MySQLConnection, 
                        table_name: str, schema: str = None) -> Dict[str, Any]:
        cursor = connection_obj.cursor(dictionary=True)
        
        database = schema or connection_obj.database
        
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}' AND table_schema = '{database}'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        return {
            'table_name': table_name,
            'schema': database,
            'columns': columns
        }
    
    def validate_table_exists(self, connection_obj: mysql.connector.MySQLConnection, 
                             table_name: str, schema: str = None) -> bool:
        cursor = connection_obj.cursor()
        database = schema or connection_obj.database
        
        cursor.execute(f"""
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = '{table_name}' AND table_schema = '{database}'
        """)
        
        return cursor.fetchone() is not None
    
    def close(self, connection_obj: mysql.connector.MySQLConnection):
        connection_obj.close()


class MongoDBConnector(DatabaseConnector):
    """Conector para MongoDB"""
    
    def connect(self, connection: DatabaseConnection) -> pymongo.MongoClient:
        connection_string = f"mongodb://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
        
        if connection.connection_params:
            # Adiciona parâmetros extras à string de conexão
            params = "&".join([f"{k}={v}" for k, v in connection.connection_params.items()])
            connection_string += f"?{params}"
        
        client = pymongo.MongoClient(connection_string)
        return client
    
    def get_tables(self, connection_obj: pymongo.MongoClient) -> List[str]:
        # MongoDB usa collections ao invés de tables
        db = connection_obj[connection_obj.get_database().name]
        return db.list_collection_names()
    
    def get_table_schema(self, connection_obj: pymongo.MongoClient, 
                        table_name: str, schema: str = None) -> Dict[str, Any]:
        # MongoDB é schemaless, então inferimos schema a partir de documentos de exemplo
        db = connection_obj[connection_obj.get_database().name]
        collection = db[table_name]
        
        # Pega alguns documentos para inferir schema
        sample_docs = list(collection.find().limit(10))
        
        if not sample_docs:
            return {
                'collection_name': table_name,
                'fields': [],
                'sample_count': 0
            }
        
        # Infere campos a partir dos documentos
        all_fields = set()
        for doc in sample_docs:
            all_fields.update(doc.keys())
        
        field_types = {}
        for field in all_fields:
            # Determina tipo mais comum para cada campo
            types = []
            for doc in sample_docs:
                if field in doc:
                    types.append(type(doc[field]).__name__)
            
            field_types[field] = max(set(types), key=types.count) if types else 'unknown'
        
        return {
            'collection_name': table_name,
            'fields': [{'name': field, 'type': field_types[field]} for field in sorted(all_fields)],
            'sample_count': len(sample_docs)
        }
    
    def validate_table_exists(self, connection_obj: pymongo.MongoClient, 
                             table_name: str, schema: str = None) -> bool:
        db = connection_obj[connection_obj.get_database().name]
        return table_name in db.list_collection_names()
    
    def close(self, connection_obj: pymongo.MongoClient):
        connection_obj.close()


class LanguageAnalyzer(ABC):
    """Interface base para analisadores de linguagem"""
    
    @abstractmethod
    def analyze_file(self, file_path: str) -> List[TableReference]:
        """Analisa arquivo e retorna referências de tabelas"""
        pass
    
    @abstractmethod
    def get_patterns(self) -> LanguagePattern:
        """Retorna padrões de detecção para a linguagem"""
        pass


class PythonAnalyzer(LanguageAnalyzer):
    """Analisador para código Python"""
    
    def __init__(self):
        self.sql_patterns = [
            r'SELECT\s+.*?\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+SET',
            r'DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'CREATE\s+TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'DROP\s+TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        
        self.orm_patterns = {
            'django': [
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\(.*Model\)',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\.objects\.',
                r'Meta:\s*\n\s*db_table\s*=\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]'
            ],
            'sqlalchemy': [
                r'Table\s*\(\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]',
                r'__tablename__\s*=\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\.query\.',
                r'session\.query\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\)'
            ],
            'pandas': [
                r'read_sql.*?[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]',
                r'to_sql\s*\(\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]'
            ]
        }
    
    def analyze_file(self, file_path: str) -> List[TableReference]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            return []
        
        references = []
        lines = content.splitlines()
        
        # Detecta tipo de framework/biblioteca
        db_type = self._detect_database_type(content)
        
        # Analisa padrões SQL diretos
        for i, line in enumerate(lines, 1):
            for pattern in self.sql_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    operation = self._extract_operation_type(line)
                    references.append(TableReference(
                        table_name=match,
                        database_type=db_type,
                        language=LanguageType.PYTHON,
                        file_path=file_path,
                        line_number=i,
                        context=line.strip(),
                        operation_type=operation,
                        confidence_score=0.9
                    ))
        
        # Analisa padrões ORM
        for framework, patterns in self.orm_patterns.items():
            if framework.lower() in content.lower():
                for pattern in patterns:
                    for i, line in enumerate(lines, 1):
                        matches = re.findall(pattern, line, re.IGNORECASE)
                        for match in matches:
                            references.append(TableReference(
                                table_name=match,
                                database_type=db_type,
                                language=LanguageType.PYTHON,
                                file_path=file_path,
                                line_number=i,
                                context=line.strip(),
                                operation_type="ORM",
                                confidence_score=0.8
                            ))
        
        return references
    
    def _detect_database_type(self, content: str) -> DatabaseType:
        """Detecta tipo de banco baseado nos imports e conexões"""
        if 'psycopg2' in content or 'postgresql' in content.lower():
            return DatabaseType.POSTGRESQL
        elif 'mysql' in content.lower() or 'pymysql' in content:
            return DatabaseType.MYSQL
        elif 'pymongo' in content or 'mongodb' in content.lower():
            return DatabaseType.MONGODB
        elif 'cx_oracle' in content.lower() or 'oracle' in content.lower():
            return DatabaseType.ORACLE
        elif 'pyodbc' in content and 'sql server' in content.lower():
            return DatabaseType.SQLSERVER
        elif 'sqlite' in content.lower():
            return DatabaseType.SQLITE
        else:
            return DatabaseType.POSTGRESQL  # Default
    
    def _extract_operation_type(self, line: str) -> str:
        """Extrai tipo de operação SQL"""
        line_upper = line.upper()
        if 'SELECT' in line_upper:
            return 'SELECT'
        elif 'INSERT' in line_upper:
            return 'INSERT'
        elif 'UPDATE' in line_upper:
            return 'UPDATE'
        elif 'DELETE' in line_upper:
            return 'DELETE'
        elif 'CREATE' in line_upper:
            return 'CREATE'
        elif 'DROP' in line_upper:
            return 'DROP'
        else:
            return 'UNKNOWN'
    
    def get_patterns(self) -> LanguagePattern:
        return LanguagePattern(
            language=LanguageType.PYTHON,
            patterns=self.sql_patterns,
            db_patterns={
                DatabaseType.POSTGRESQL: self.orm_patterns['sqlalchemy'],
                DatabaseType.MYSQL: self.orm_patterns['sqlalchemy'],
                DatabaseType.MONGODB: ['db\\.([a-zA-Z_][a-zA-Z0-9_]*)\\.find']
            },
            file_extensions=['.py'],
            import_patterns=['import psycopg2', 'import pymongo', 'from sqlalchemy']
        )


class JavaAnalyzer(LanguageAnalyzer):
    """Analisador para código Java"""
    
    def __init__(self):
        self.sql_patterns = [
            r'SELECT\s+.*?\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+SET',
            r'DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        
        self.jpa_patterns = [
            r'@Table\s*\(\s*name\s*=\s*"([^"]+)"',
            r'@Entity.*?\npublic\s+class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+where',  # JPQL
            r'Query.*?createQuery\s*\(\s*".*?from\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        
        self.mybatis_patterns = [
            r'@Select\s*\(\s*".*?FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'@Insert\s*\(\s*".*?INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'@Update\s*\(\s*".*?UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'@Delete\s*\(\s*".*?FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
    
    def analyze_file(self, file_path: str) -> List[TableReference]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            return []
        
        references = []
        lines = content.splitlines()
        
        db_type = self._detect_database_type(content)
        
        # Analisa padrões SQL
        for i, line in enumerate(lines, 1):
            for pattern in self.sql_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    operation = self._extract_operation_type(line)
                    references.append(TableReference(
                        table_name=match,
                        database_type=db_type,
                        language=LanguageType.JAVA,
                        file_path=file_path,
                        line_number=i,
                        context=line.strip(),
                        operation_type=operation,
                        confidence_score=0.9
                    ))
        
        # Analisa padrões JPA
        for pattern in self.jpa_patterns:
            for i, line in enumerate(lines, 1):
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    references.append(TableReference(
                        table_name=match,
                        database_type=db_type,
                        language=LanguageType.JAVA,
                        file_path=file_path,
                        line_number=i,
                        context=line.strip(),
                        operation_type="JPA",
                        confidence_score=0.8
                    ))
        
        # Analisa padrões MyBatis
        for pattern in self.mybatis_patterns:
            for i, line in enumerate(lines, 1):
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    references.append(TableReference(
                        table_name=match,
                        database_type=db_type,
                        language=LanguageType.JAVA,
                        file_path=file_path,
                        line_number=i,
                        context=line.strip(),
                        operation_type="MyBatis",
                        confidence_score=0.8
                    ))
        
        return references
    
    def _detect_database_type(self, content: str) -> DatabaseType:
        if 'postgresql' in content.lower() or 'org.postgresql' in content:
            return DatabaseType.POSTGRESQL
        elif 'mysql' in content.lower() or 'com.mysql' in content:
            return DatabaseType.MYSQL
        elif 'oracle' in content.lower() or 'oracle.jdbc' in content:
            return DatabaseType.ORACLE
        elif 'sqlserver' in content.lower() or 'com.microsoft.sqlserver' in content:
            return DatabaseType.SQLSERVER
        else:
            return DatabaseType.POSTGRESQL  # Default
    
    def _extract_operation_type(self, line: str) -> str:
        line_upper = line.upper()
        if 'SELECT' in line_upper:
            return 'SELECT'
        elif 'INSERT' in line_upper:
            return 'INSERT'
        elif 'UPDATE' in line_upper:
            return 'UPDATE'
        elif 'DELETE' in line_upper:
            return 'DELETE'
        else:
            return 'UNKNOWN'
    
    def get_patterns(self) -> LanguagePattern:
        return LanguagePattern(
            language=LanguageType.JAVA,
            patterns=self.sql_patterns + self.jpa_patterns + self.mybatis_patterns,
            db_patterns={
                DatabaseType.POSTGRESQL: self.jpa_patterns,
                DatabaseType.MYSQL: self.jpa_patterns,
                DatabaseType.ORACLE: self.jpa_patterns
            },
            file_extensions=['.java'],
            import_patterns=['import javax.persistence', 'import org.springframework']
        )


class RAnalyzer(LanguageAnalyzer):
    """Analisador para código R"""
    
    def __init__(self):
        self.sql_patterns = [
            r'dbGetQuery\s*\([^,]+,\s*[\'"].*?FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'sqldf\s*\(\s*[\'"].*?FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'SELECT\s+.*?\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        
        self.dplyr_patterns = [
            r'tbl\s*\(\s*[^,]+,\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]',
            r'copy_to\s*\([^,]+,\s*[^,]+,\s*[\'"]([a-zA-Z_][a-zA-Z0-9_]*)[\'"]'
        ]
    
    def analyze_file(self, file_path: str) -> List[TableReference]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            return []
        
        references = []
        lines = content.splitlines()
        
        db_type = self._detect_database_type(content)
        
        # Analisa padrões SQL
        for i, line in enumerate(lines, 1):
            for pattern in self.sql_patterns + self.dplyr_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    operation = self._extract_operation_type(line)
                    references.append(TableReference(
                        table_name=match,
                        database_type=db_type,
                        language=LanguageType.R,
                        file_path=file_path,
                        line_number=i,
                        context=line.strip(),
                        operation_type=operation,
                        confidence_score=0.8
                    ))
        
        return references
    
    def _detect_database_type(self, content: str) -> DatabaseType:
        if 'RPostgreSQL' in content or 'postgresql' in content.lower():
            return DatabaseType.POSTGRESQL
        elif 'RMySQL' in content or 'mysql' in content.lower():
            return DatabaseType.MYSQL
        elif 'RODBC' in content:
            return DatabaseType.SQLSERVER
        else:
            return DatabaseType.POSTGRESQL  # Default
    
    def _extract_operation_type(self, line: str) -> str:
        if 'dbGetQuery' in line or 'sqldf' in line:
            return 'QUERY'
        elif 'copy_to' in line:
            return 'INSERT'
        else:
            return 'UNKNOWN'
    
    def get_patterns(self) -> LanguagePattern:
        return LanguagePattern(
            language=LanguageType.R,
            patterns=self.sql_patterns + self.dplyr_patterns,
            db_patterns={
                DatabaseType.POSTGRESQL: ['RPostgreSQL'],
                DatabaseType.MYSQL: ['RMySQL']
            },
            file_extensions=['.r', '.R'],
            import_patterns=['library(DBI)', 'library(dplyr)']
        )


class MultiLanguageDatabaseAnalyzer:
    """Analisador principal que suporta múltiplas linguagens e bancos"""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or "multi_db_config")
        self.config_dir.mkdir(exist_ok=True)
        
        # Inicializa analisadores de linguagem
        self.language_analyzers = {
            LanguageType.PYTHON: PythonAnalyzer(),
            LanguageType.JAVA: JavaAnalyzer(),
            LanguageType.R: RAnalyzer()
            # TODO: Adicionar outros analisadores
        }
        
        # Inicializa conectores de banco
        self.db_connectors = {
            DatabaseType.POSTGRESQL: PostgreSQLConnector(),
            DatabaseType.MYSQL: MySQLConnector(),
            DatabaseType.MONGODB: MongoDBConnector()
            # TODO: Adicionar outros conectores
        }
        
        # Cache de conexões ativas
        self.active_connections = {}
        
        # Configuração
        self.config = self._load_config()
        
        # Banco local para metadados
        self.metadata_db = self.config_dir / "metadata.db"
        self._init_metadata_db()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração"""
        config_file = self.config_dir / "config.json"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            default_config = {
                "supported_languages": [lang.value for lang in LanguageType],
                "supported_databases": [db.value for db in DatabaseType],
                "file_extensions": {
                    "python": [".py"],
                    "java": [".java"],
                    "scala": [".scala"],
                    "r": [".r", ".R"],
                    "go": [".go"],
                    "nodejs": [".js", ".ts"],
                    "php": [".php"],
                    "csharp": [".cs"],
                    "cpp": [".cpp", ".cc", ".cxx"]
                },
                "analysis_settings": {
                    "confidence_threshold": 0.7,
                    "max_file_size_mb": 10,
                    "parallel_processing": True
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    
    def _init_metadata_db(self):
        """Inicializa banco de metadados"""
        conn = sqlite3.connect(self.metadata_db)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS table_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                database_type TEXT NOT NULL,
                language TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                context TEXT,
                operation_type TEXT,
                confidence_score REAL,
                schema_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS database_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_name TEXT UNIQUE NOT NULL,
                db_type TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                database_name TEXT NOT NULL,
                username TEXT NOT NULL,
                encrypted_password TEXT NOT NULL,
                schema_name TEXT,
                ssl_mode TEXT,
                connection_params TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS validated_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                database_type TEXT NOT NULL,
                connection_name TEXT NOT NULL,
                schema_name TEXT,
                exists_in_db BOOLEAN NOT NULL,
                table_schema TEXT,
                validation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(table_name, database_type, connection_name, schema_name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_database_connection(self, connection_name: str, connection: DatabaseConnection) -> bool:
        """Adiciona configuração de conexão com banco"""
        try:
            # Testa conexão
            connector = self.db_connectors.get(connection.db_type)
            if not connector:
                raise ValueError(f"Database type {connection.db_type.value} not supported")
            
            conn_obj = connector.connect(connection)
            connector.close(conn_obj)
            
            # Salva configuração (senha criptografada)
            # TODO: Implementar criptografia de senha
            encrypted_password = connection.password  # Placeholder
            
            conn = sqlite3.connect(self.metadata_db)
            conn.execute('''
                INSERT OR REPLACE INTO database_connections 
                (connection_name, db_type, host, port, database_name, username, encrypted_password, 
                 schema_name, ssl_mode, connection_params)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                connection_name, connection.db_type.value, connection.host, connection.port,
                connection.database, connection.username, encrypted_password, connection.schema,
                connection.ssl_mode, json.dumps(connection.connection_params or {})
            ))
            conn.commit()
            conn.close()
            
            print(f"✅ Database connection '{connection_name}' added successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add connection '{connection_name}': {e}")
            return False
    
    def analyze_project(self, project_root: str, languages: List[LanguageType] = None) -> Dict[str, Any]:
        """Analisa projeto completo para múltiplas linguagens"""
        project_path = Path(project_root)
        
        if not project_path.exists():
            raise ValueError(f"Project path {project_root} does not exist")
        
        # Usa todas as linguagens suportadas se não especificado
        if languages is None:
            languages = list(self.language_analyzers.keys())
        
        results = {
            'project_root': str(project_path.absolute()),
            'analysis_timestamp': datetime.now().isoformat(),
            'languages_analyzed': [lang.value for lang in languages],
            'total_files_analyzed': 0,
            'total_references_found': 0,
            'by_language': {},
            'by_database': {},
            'unique_tables': set(),
            'files_with_references': []
        }
        
        # Analisa cada linguagem
        for language in languages:
            if language not in self.language_analyzers:
                print(f"⚠ Language {language.value} not supported, skipping...")
                continue
            
            analyzer = self.language_analyzers[language]
            file_extensions = self.config['file_extensions'].get(language.value, [])
            
            language_results = {
                'files_analyzed': 0,
                'references_found': 0,
                'table_references': []
            }
            
            # Busca arquivos da linguagem
            for ext in file_extensions:
                for file_path in project_path.rglob(f"*{ext}"):
                    try:
                        # Verifica tamanho do arquivo
                        if file_path.stat().st_size > self.config['analysis_settings']['max_file_size_mb'] * 1024 * 1024:
                            print(f"⚠ Skipping large file: {file_path}")
                            continue
                        
                        references = analyzer.analyze_file(str(file_path))
                        
                        if references:
                            language_results['table_references'].extend(references)
                            language_results['references_found'] += len(references)
                            results['files_with_references'].append(str(file_path))
                            
                            # Salva no banco de metadados
                            self._save_references_to_db(references)
                        
                        language_results['files_analyzed'] += 1
                        
                    except Exception as e:
                        logging.error(f"Error analyzing {file_path}: {e}")
            
            results['by_language'][language.value] = language_results
            results['total_files_analyzed'] += language_results['files_analyzed']
            results['total_references_found'] += language_results['references_found']
            
            # Coleta tabelas únicas
            for ref in language_results['table_references']:
                results['unique_tables'].add(ref.table_name)
        
        # Agrupa por tipo de banco
        for language_data in results['by_language'].values():
            for ref in language_data['table_references']:
                db_type = ref.database_type.value
                if db_type not in results['by_database']:
                    results['by_database'][db_type] = {
                        'tables': set(),
                        'reference_count': 0
                    }
                
                results['by_database'][db_type]['tables'].add(ref.table_name)
                results['by_database'][db_type]['reference_count'] += 1
        
        # Converte sets para listas para serialização JSON
        results['unique_tables'] = list(results['unique_tables'])
        for db_data in results['by_database'].values():
            db_data['tables'] = list(db_data['tables'])
        
        # Salva resultados
        self._save_analysis_results(results)
        
        print(f"✅ Analysis completed: {results['total_references_found']} references in {results['total_files_analyzed']} files")
        return results
    
    def _save_references_to_db(self, references: List[TableReference]):
        """Salva referências no banco de metadados"""
        conn = sqlite3.connect(self.metadata_db)
        
        for ref in references:
            conn.execute('''
                INSERT INTO table_references 
                (table_name, database_type, language, file_path, line_number, 
                 context, operation_type, confidence_score, schema_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ref.table_name, ref.database_type.value, ref.language.value,
                ref.file_path, ref.line_number, ref.context, ref.operation_type,
                ref.confidence_score, ref.schema_name
            ))
        
        conn.commit()
        conn.close()
    
    def _save_analysis_results(self, results: Dict[str, Any]):
        """Salva resultados da análise"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.config_dir / f"analysis_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    def validate_tables_with_database(self, connection_name: str) -> Dict[str, Any]:
        """Valida tabelas encontradas contra banco real"""
        # Carrega configuração de conexão
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.execute(
            'SELECT * FROM database_connections WHERE connection_name = ? AND is_active = 1',
            (connection_name,)
        )
        conn_config = cursor.fetchone()
        conn.close()
        
        if not conn_config:
            raise ValueError(f"Connection '{connection_name}' not found")
        
        # Cria objeto de conexão
        db_type = DatabaseType(conn_config[2])
        connection = DatabaseConnection(
            db_type=db_type,
            host=conn_config[3],
            port=conn_config[4],
            database=conn_config[5],
            username=conn_config[6],
            password=conn_config[7],  # TODO: Descriptografar
            schema=conn_config[8],
            ssl_mode=conn_config[9],
            connection_params=json.loads(conn_config[10])
        )
        
        # Conecta ao banco
        connector = self.db_connectors[db_type]
        conn_obj = connector.connect(connection)
        
        try:
            # Pega todas as tabelas do banco
            real_tables = set(connector.get_tables(conn_obj))
            
            # Pega tabelas encontradas na análise
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.execute(
                'SELECT DISTINCT table_name FROM table_references WHERE database_type = ?',
                (db_type.value,)
            )
            found_tables = set(row[0] for row in cursor.fetchall())
            conn.close()
            
            # Validação
            validated_tables = []
            missing_tables = []
            extra_tables = real_tables - found_tables
            
            for table_name in found_tables:
                exists = connector.validate_table_exists(conn_obj, table_name, connection.schema)
                
                validation_result = {
                    'table_name': table_name,
                    'exists_in_database': exists,
                    'schema': connection.schema
                }
                
                if exists:
                    # Pega schema da tabela
                    try:
                        schema_info = connector.get_table_schema(conn_obj, table_name, connection.schema)
                        validation_result['schema_info'] = schema_info
                    except Exception as e:
                        validation_result['schema_error'] = str(e)
                    
                    validated_tables.append(validation_result)
                else:
                    missing_tables.append(validation_result)
                
                # Salva no banco de metadados
                self._save_table_validation(connection_name, table_name, db_type, 
                                          connection.schema, exists, validation_result.get('schema_info'))
            
            results = {
                'connection_name': connection_name,
                'database_type': db_type.value,
                'validation_timestamp': datetime.now().isoformat(),
                'total_tables_in_db': len(real_tables),
                'total_tables_found_in_code': len(found_tables),
                'validated_tables': len(validated_tables),
                'missing_tables': len(missing_tables),
                'extra_tables_in_db': len(extra_tables),
                'validation_details': {
                    'validated': validated_tables,
                    'missing': missing_tables,
                    'extra_in_db': list(extra_tables)
                }
            }
            
            return results
            
        finally:
            connector.close(conn_obj)
    
    def _save_table_validation(self, connection_name: str, table_name: str, 
                              db_type: DatabaseType, schema: str, exists: bool, 
                              schema_info: Dict[str, Any] = None):
        """Salva resultado da validação"""
        conn = sqlite3.connect(self.metadata_db)
        conn.execute('''
            INSERT OR REPLACE INTO validated_tables 
            (table_name, database_type, connection_name, schema_name, exists_in_db, table_schema)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            table_name, db_type.value, connection_name, schema, exists,
            json.dumps(schema_info) if schema_info else None
        ))
        conn.commit()
        conn.close()
    
    def generate_cross_language_report(self, output_path: str) -> Dict[str, Any]:
        """Gera relatório consolidado multi-linguagem"""
        conn = sqlite3.connect(self.metadata_db)
        
        # Estatísticas gerais
        cursor = conn.execute('SELECT COUNT(*) FROM table_references')
        total_references = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT COUNT(DISTINCT table_name) FROM table_references')
        unique_tables = cursor.fetchone()[0]
        
        cursor = conn.execute('SELECT COUNT(DISTINCT file_path) FROM table_references')
        files_with_references = cursor.fetchone()[0]
        
        # Por linguagem
        cursor = conn.execute('''
            SELECT language, COUNT(*) as ref_count, COUNT(DISTINCT table_name) as unique_tables
            FROM table_references 
            GROUP BY language
        ''')
        by_language = [{'language': row[0], 'references': row[1], 'unique_tables': row[2]} 
                      for row in cursor.fetchall()]
        
        # Por tipo de banco
        cursor = conn.execute('''
            SELECT database_type, COUNT(*) as ref_count, COUNT(DISTINCT table_name) as unique_tables
            FROM table_references 
            GROUP BY database_type
        ''')
        by_database = [{'database_type': row[0], 'references': row[1], 'unique_tables': row[2]} 
                      for row in cursor.fetchall()]
        
        # Tabelas mais referenciadas
        cursor = conn.execute('''
            SELECT table_name, COUNT(*) as ref_count, 
                   GROUP_CONCAT(DISTINCT language) as languages,
                   GROUP_CONCAT(DISTINCT database_type) as databases
            FROM table_references 
            GROUP BY table_name 
            ORDER BY ref_count DESC 
            LIMIT 20
        ''')
        most_referenced = [{'table': row[0], 'references': row[1], 
                           'languages': row[2].split(','), 'databases': row[3].split(',')} 
                          for row in cursor.fetchall()]
        
        # Validações
        cursor = conn.execute('''
            SELECT connection_name, 
                   SUM(CASE WHEN exists_in_db = 1 THEN 1 ELSE 0 END) as valid_tables,
                   SUM(CASE WHEN exists_in_db = 0 THEN 1 ELSE 0 END) as invalid_tables
            FROM validated_tables 
            GROUP BY connection_name
        ''')
        validation_summary = [{'connection': row[0], 'valid': row[1], 'invalid': row[2]} 
                             for row in cursor.fetchall()]
        
        conn.close()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_references': total_references,
                'unique_tables': unique_tables,
                'files_with_references': files_with_references
            },
            'by_language': by_language,
            'by_database': by_database,
            'most_referenced_tables': most_referenced,
            'validation_summary': validation_summary
        }
        
        # Salva relatório
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Cross-language report generated: {output_path}")
        return report


# Exemplo de uso
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BW Automate Multi-Database & Multi-Language Support")
    parser.add_argument("--config-dir", "-c", default="multi_db_config", 
                       help="Configuration directory")
    parser.add_argument("--analyze", "-a", help="Analyze project directory")
    parser.add_argument("--languages", "-l", nargs="+", 
                       choices=[lang.value for lang in LanguageType],
                       help="Languages to analyze")
    parser.add_argument("--add-connection", help="Add database connection")
    parser.add_argument("--db-type", choices=[db.value for db in DatabaseType],
                       help="Database type")
    parser.add_argument("--host", help="Database host")
    parser.add_argument("--port", type=int, help="Database port")
    parser.add_argument("--database", help="Database name")
    parser.add_argument("--username", help="Database username")
    parser.add_argument("--password", help="Database password")
    parser.add_argument("--validate", help="Validate tables against database connection")
    parser.add_argument("--report", help="Generate cross-language report")
    
    args = parser.parse_args()
    
    # Cria analisador
    analyzer = MultiLanguageDatabaseAnalyzer(args.config_dir)
    
    if args.add_connection:
        if not all([args.db_type, args.host, args.port, args.database, args.username, args.password]):
            print("❌ All database connection parameters required")
            exit(1)
        
        connection = DatabaseConnection(
            db_type=DatabaseType(args.db_type),
            host=args.host,
            port=args.port,
            database=args.database,
            username=args.username,
            password=args.password
        )
        
        analyzer.add_database_connection(args.add_connection, connection)
    
    if args.analyze:
        languages = None
        if args.languages:
            languages = [LanguageType(lang) for lang in args.languages]
        
        results = analyzer.analyze_project(args.analyze, languages)
        print(f"\n📈 Analysis Results:")
        print(f"  Total files: {results['total_files_analyzed']}")
        print(f"  Total references: {results['total_references_found']}")
        print(f"  Unique tables: {len(results['unique_tables'])}")
        
        for lang, data in results['by_language'].items():
            print(f"  {lang.upper()}: {data['references_found']} references in {data['files_analyzed']} files")
    
    if args.validate:
        try:
            results = analyzer.validate_tables_with_database(args.validate)
            print(f"\n🔍 Validation Results for '{args.validate}':")
            print(f"  Tables in DB: {results['total_tables_in_db']}")
            print(f"  Tables found in code: {results['total_tables_found_in_code']}")
            print(f"  Validated: {results['validated_tables']}")
            print(f"  Missing: {results['missing_tables']}")
            print(f"  Extra in DB: {results['extra_tables_in_db']}")
        except Exception as e:
            print(f"❌ Validation failed: {e}")
    
    if args.report:
        report = analyzer.generate_cross_language_report(args.report)
        print(f"\n📊 Report Summary:")
        print(f"  Total references: {report['summary']['total_references']}")
        print(f"  Unique tables: {report['summary']['unique_tables']}")
        print(f"  Files with references: {report['summary']['files_with_references']}")
    
    print("✅ Multi-Database & Multi-Language system ready")
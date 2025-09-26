#!/usr/bin/env python3
"""
Enhanced SQL Analyzer v2.0
===========================

Analisador SQL aprimorado com capacidades avançadas de detecção e análise:
- Detecção de padrões SQL complexos
- Análise de performance e otimização
- Identificação de vulnerabilidades
- Extração de metadados avançados
- Suporte a SQL dinâmico e templates

Principais melhorias:
- Parser SQL mais robusto
- Detecção de anti-padrões
- Análise de linhagem de dados
- Métricas de qualidade de código SQL
- Sugestões de otimização

Autor: BW_AUTOMATE v2.0
Data: 2025-09-20
"""

import re
import ast
import logging
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class SQLStatement:
    """Representa um statement SQL analisado"""
    content: str
    file_path: str
    line_number: int
    statement_type: str  # SELECT, INSERT, UPDATE, DELETE, CREATE, etc.
    tables_referenced: List[str]
    columns_referenced: List[str]
    schemas_referenced: List[str]
    complexity_score: int
    performance_concerns: List[str]
    security_issues: List[str]
    optimization_suggestions: List[str]
    is_dynamic: bool = False
    template_variables: List[str] = None
    cte_count: int = 0
    join_count: int = 0
    subquery_count: int = 0
    function_calls: List[str] = None

@dataclass
class SQLAnalysisResult:
    """Resultado completo da análise SQL"""
    total_statements: int
    statements_by_type: Dict[str, int]
    complexity_distribution: Dict[str, int]
    performance_issues_count: int
    security_issues_count: int
    tables_usage_frequency: Dict[str, int]
    most_complex_queries: List[SQLStatement]
    optimization_opportunities: List[Dict[str, Any]]
    data_lineage: Dict[str, List[str]]
    quality_score: float

class EnhancedSQLAnalyzer:
    """
    Analisador SQL avançado com capacidades de detecção aprimoradas
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o analisador SQL
        
        Args:
            config: Configurações do analisador
        """
        self.config = config or {}
        self.setup_logging()
        
        # Padrões SQL aprimorados
        self.sql_patterns = {
            'select': [
                r'(?i)\bSELECT\b.*?\bFROM\b\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'(?i)\bWITH\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(',
                r'(?i)\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'(?i)\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'(?i)\bUNION\s+(?:ALL\s+)?SELECT\b',
            ],
            'insert': [
                r'(?i)\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'(?i)\bINSERT\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'update': [
                r'(?i)\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'delete': [
                r'(?i)\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'create': [
                r'(?i)\bCREATE\s+(?:TEMP\s+|TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'(?i)\bCREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'drop': [
                r'(?i)\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'(?i)\bDROP\s+VIEW\s+(?:IF\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'truncate': [
                r'(?i)\bTRUNCATE\s+(?:TABLE\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ]
        }
        
        # Padrões de vulnerabilidades SQL
        self.security_patterns = {
            'sql_injection': [
                r'(?i)["\'][^"\']*\+[^"\']*["\']',  # Concatenação de strings
                r'(?i)format\s*\([^)]*%[sd][^)]*\)',  # Format strings vulneráveis
                r'(?i)WHERE\s+[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*["\'][^"\']*\+',  # Concatenação em WHERE
            ],
            'unsafe_operations': [
                r'(?i)DELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_]*\s*(?:;|$)',  # DELETE sem WHERE
                r'(?i)UPDATE\s+[a-zA-Z_][a-zA-Z0-9_]*\s+SET\s+.*(?:;|$)(?!.*WHERE)',  # UPDATE sem WHERE
                r'(?i)TRUNCATE\s+TABLE',  # TRUNCATE operations
                r'(?i)DROP\s+(?:TABLE|DATABASE|SCHEMA)',  # DROP operations
            ],
            'performance_risks': [
                r'(?i)SELECT\s+\*\s+FROM',  # SELECT *
                r'(?i)WHERE\s+[a-zA-Z_][a-zA-Z0-9_]*\s+LIKE\s+["\']%',  # Leading wildcard LIKE
                r'(?i)ORDER\s+BY\s+[a-zA-Z_][a-zA-Z0-9_]*\s+(?:(?!LIMIT))',  # ORDER BY sem LIMIT
            ]
        }
        
        # Padrões de complexidade
        self.complexity_patterns = {
            'cte': r'(?i)\bWITH\b',
            'join': r'(?i)\b(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+|CROSS\s+)?JOIN\b',
            'subquery': r'(?i)SELECT\b(?=.*?\bFROM\b)',
            'window_function': r'(?i)\b(?:ROW_NUMBER|RANK|DENSE_RANK|LAG|LEAD|FIRST_VALUE|LAST_VALUE)\s*\(\s*\)\s+OVER\s*\(',
            'case_when': r'(?i)\bCASE\s+WHEN\b',
            'union': r'(?i)\bUNION\s+(?:ALL\s+)?',
            'aggregate': r'(?i)\b(?:COUNT|SUM|AVG|MIN|MAX|GROUP_CONCAT)\s*\(',
            'having': r'(?i)\bHAVING\b',
            'recursive': r'(?i)\bWITH\s+RECURSIVE\b',
        }
        
        # Funções SQL conhecidas
        self.sql_functions = {
            'string': ['CONCAT', 'SUBSTRING', 'REPLACE', 'UPPER', 'LOWER', 'TRIM', 'LENGTH'],
            'date': ['NOW', 'CURRENT_DATE', 'CURRENT_TIMESTAMP', 'DATE_ADD', 'DATE_SUB', 'EXTRACT'],
            'math': ['ABS', 'ROUND', 'CEIL', 'FLOOR', 'POWER', 'SQRT'],
            'aggregate': ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT'],
            'window': ['ROW_NUMBER', 'RANK', 'DENSE_RANK', 'LAG', 'LEAD', 'FIRST_VALUE', 'LAST_VALUE'],
            'conditional': ['CASE', 'COALESCE', 'NULLIF', 'ISNULL', 'IFNULL']
        }
        
    def setup_logging(self):
        """Configura logging"""
        self.logger = logging.getLogger('EnhancedSQLAnalyzer')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def analyze_file_content(self, content: str, file_path: str) -> List[SQLStatement]:
        """
        Analisa conteúdo de arquivo buscando SQL statements
        
        Args:
            content: Conteúdo do arquivo
            file_path: Caminho do arquivo
            
        Returns:
            Lista de SQLStatements encontrados
        """
        self.logger.info(f"Analisando SQL em: {file_path}")
        
        statements = []
        
        # 1. Extrai strings SQL diretas
        statements.extend(self._extract_direct_sql_strings(content, file_path))
        
        # 2. Extrai SQL de operações pandas
        statements.extend(self._extract_pandas_sql(content, file_path))
        
        # 3. Extrai SQL de f-strings e templates
        statements.extend(self._extract_dynamic_sql(content, file_path))
        
        # 4. Extrai SQL de comentários (se habilitado)
        if self.config.get('extract_from_comments', False):
            statements.extend(self._extract_sql_from_comments(content, file_path))
        
        # 5. Analisa cada statement encontrado
        analyzed_statements = []
        for stmt in statements:
            analyzed_stmt = self._analyze_sql_statement(stmt)
            analyzed_statements.append(analyzed_stmt)
        
        self.logger.info(f"Encontrados {len(analyzed_statements)} SQL statements em {file_path}")
        return analyzed_statements
    
    def _extract_direct_sql_strings(self, content: str, file_path: str) -> List[SQLStatement]:
        """Extrai strings SQL diretas"""
        statements = []
        
        # Padrões para strings SQL
        sql_string_patterns = [
            r'(?i)sql\s*=\s*["\'\`]([^"\'\`]+)["\'\`]',
            r'(?i)query\s*=\s*["\'\`]([^"\'\`]+)["\'\`]',
            r'(?i)["\'\`]([^"\'\`]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|TRUNCATE)[^"\'\`]*)["\'\`]',
        ]
        
        # Busca strings multilinhas
        multiline_patterns = [
            r'(?i)sql\s*=\s*["\'\`]{3}([^"\'`]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|TRUNCATE)[^"\'`]*)["\'\`]{3}',
            r'(?i)query\s*=\s*["\'\`]{3}([^"\'`]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|TRUNCATE)[^"\'`]*)["\'\`]{3}',
        ]
        
        for pattern in sql_string_patterns + multiline_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
            for match in matches:
                sql_content = match.group(1).strip()
                if self._is_valid_sql(sql_content):
                    line_number = content[:match.start()].count('\n') + 1
                    statements.append(SQLStatement(
                        content=sql_content,
                        file_path=file_path,
                        line_number=line_number,
                        statement_type='UNKNOWN',
                        tables_referenced=[],
                        columns_referenced=[],
                        schemas_referenced=[],
                        complexity_score=0,
                        performance_concerns=[],
                        security_issues=[],
                        optimization_suggestions=[],
                        function_calls=[]
                    ))
        
        return statements
    
    def _extract_pandas_sql(self, content: str, file_path: str) -> List[SQLStatement]:
        """Extrai SQL de operações pandas"""
        statements = []
        
        # Padrões para pandas
        pandas_patterns = [
            r'(?i)pd\.read_sql\s*\(\s*["\'\`]([^"\'\`]+)["\'\`]',
            r'(?i)pd\.read_sql_query\s*\(\s*["\'\`]([^"\'\`]+)["\'\`]',
            r'(?i)pd\.read_sql_table\s*\(\s*["\'\`]([^"\'\`]+)["\'\`]',
            r'(?i)\.to_sql\s*\(\s*["\'\`]([^"\'\`]+)["\'\`]',
        ]
        
        for pattern in pandas_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                sql_content = match.group(1).strip()
                if self._is_valid_sql(sql_content) or self._is_table_name(sql_content):
                    line_number = content[:match.start()].count('\n') + 1
                    statements.append(SQLStatement(
                        content=sql_content,
                        file_path=file_path,
                        line_number=line_number,
                        statement_type='PANDAS_SQL',
                        tables_referenced=[],
                        columns_referenced=[],
                        schemas_referenced=[],
                        complexity_score=0,
                        performance_concerns=[],
                        security_issues=[],
                        optimization_suggestions=[],
                        function_calls=[]
                    ))
        
        return statements
    
    def _extract_dynamic_sql(self, content: str, file_path: str) -> List[SQLStatement]:
        """Extrai SQL dinâmico (f-strings, format, etc.)"""
        statements = []
        
        # Padrões para SQL dinâmico
        dynamic_patterns = [
            r'(?i)f["\'\`]([^"\'\`]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)[^"\'\`]*)["\'\`]',
            r'(?i)["\'\`]([^"\'\`]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)[^"\'\`]*)["\'\`]\.format\s*\(',
            r'(?i)["\'\`]([^"\'\`]*\{[^}]*\}[^"\'\`]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)[^"\'\`]*)["\'\`]',
        ]
        
        for pattern in dynamic_patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                sql_content = match.group(1).strip()
                if self._contains_sql_keywords(sql_content):
                    line_number = content[:match.start()].count('\n') + 1
                    
                    # Extrai variáveis de template
                    template_vars = re.findall(r'\{([^}]+)\}', sql_content)
                    
                    statements.append(SQLStatement(
                        content=sql_content,
                        file_path=file_path,
                        line_number=line_number,
                        statement_type='DYNAMIC_SQL',
                        tables_referenced=[],
                        columns_referenced=[],
                        schemas_referenced=[],
                        complexity_score=0,
                        performance_concerns=[],
                        security_issues=[],
                        optimization_suggestions=[],
                        is_dynamic=True,
                        template_variables=template_vars,
                        function_calls=[]
                    ))
        
        return statements
    
    def _extract_sql_from_comments(self, content: str, file_path: str) -> List[SQLStatement]:
        """Extrai SQL de comentários (útil para documentação)"""
        statements = []
        
        # Busca SQL em comentários
        comment_patterns = [
            r'#\s*([^#\n]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)[^#\n]*)',
            r'"""\s*([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)[^"]*)\s*"""',
            r"'''\s*([^']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP)[^']*)\s*'''",
        ]
        
        for pattern in comment_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                sql_content = match.group(1).strip()
                if self._is_valid_sql(sql_content):
                    line_number = content[:match.start()].count('\n') + 1
                    statements.append(SQLStatement(
                        content=sql_content,
                        file_path=file_path,
                        line_number=line_number,
                        statement_type='COMMENT_SQL',
                        tables_referenced=[],
                        columns_referenced=[],
                        schemas_referenced=[],
                        complexity_score=0,
                        performance_concerns=[],
                        security_issues=[],
                        optimization_suggestions=[],
                        function_calls=[]
                    ))
        
        return statements
    
    def _analyze_sql_statement(self, stmt: SQLStatement) -> SQLStatement:
        """Analisa um SQL statement individualmente"""
        
        # 1. Determina tipo do statement
        stmt.statement_type = self._determine_statement_type(stmt.content)
        
        # 2. Extrai tabelas referenciadas
        stmt.tables_referenced = self._extract_referenced_tables(stmt.content)
        
        # 3. Extrai schemas
        stmt.schemas_referenced = self._extract_schemas(stmt.tables_referenced)
        
        # 4. Extrai colunas (básico)
        stmt.columns_referenced = self._extract_columns(stmt.content)
        
        # 5. Calcula score de complexidade
        stmt.complexity_score = self._calculate_complexity_score(stmt.content)
        
        # 6. Conta elementos complexos
        stmt.cte_count = len(re.findall(self.complexity_patterns['cte'], stmt.content, re.IGNORECASE))
        stmt.join_count = len(re.findall(self.complexity_patterns['join'], stmt.content, re.IGNORECASE))
        stmt.subquery_count = len(re.findall(self.complexity_patterns['subquery'], stmt.content, re.IGNORECASE)) - 1  # Remove o SELECT principal
        
        # 7. Identifica funções utilizadas
        stmt.function_calls = self._extract_function_calls(stmt.content)
        
        # 8. Detecta problemas de performance
        stmt.performance_concerns = self._detect_performance_issues(stmt.content)
        
        # 9. Detecta problemas de segurança
        stmt.security_issues = self._detect_security_issues(stmt.content)
        
        # 10. Gera sugestões de otimização
        stmt.optimization_suggestions = self._generate_optimization_suggestions(stmt)
        
        return stmt
    
    def _is_valid_sql(self, content: str) -> bool:
        """Verifica se o conteúdo parece ser SQL válido"""
        if not content or len(content.strip()) < 10:
            return False
        
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'TRUNCATE', 'ALTER']
        content_upper = content.upper()
        
        return any(keyword in content_upper for keyword in sql_keywords)
    
    def _is_table_name(self, content: str) -> bool:
        """Verifica se o conteúdo parece ser um nome de tabela"""
        if not content or len(content.strip()) < 2:
            return False
        
        # Nome de tabela básico: letras, números, underscore, ponto para schema
        return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?$', content.strip()) is not None
    
    def _contains_sql_keywords(self, content: str) -> bool:
        """Verifica se contém palavras-chave SQL"""
        sql_keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'UPDATE', 'SET', 'DELETE', 
                       'CREATE', 'TABLE', 'DROP', 'ALTER', 'JOIN', 'ON', 'GROUP BY', 'ORDER BY']
        content_upper = content.upper()
        
        return any(keyword in content_upper for keyword in sql_keywords)
    
    def _determine_statement_type(self, content: str) -> str:
        """Determina o tipo do SQL statement"""
        content_upper = content.upper().strip()
        
        if content_upper.startswith('SELECT') or content_upper.startswith('WITH'):
            return 'SELECT'
        elif content_upper.startswith('INSERT'):
            return 'INSERT'
        elif content_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif content_upper.startswith('DELETE'):
            return 'DELETE'
        elif content_upper.startswith('CREATE'):
            return 'CREATE'
        elif content_upper.startswith('DROP'):
            return 'DROP'
        elif content_upper.startswith('TRUNCATE'):
            return 'TRUNCATE'
        elif content_upper.startswith('ALTER'):
            return 'ALTER'
        else:
            return 'OTHER'
    
    def _extract_referenced_tables(self, content: str) -> List[str]:
        """Extrai tabelas referenciadas no SQL"""
        tables = set()
        
        for stmt_type, patterns in self.sql_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    if match and match.strip():
                        tables.add(match.strip())
        
        return list(tables)
    
    def _extract_schemas(self, tables: List[str]) -> List[str]:
        """Extrai schemas das tabelas referenciadas"""
        schemas = set()
        
        for table in tables:
            if '.' in table:
                schema = table.split('.')[0]
                schemas.add(schema)
        
        return list(schemas)
    
    def _extract_columns(self, content: str) -> List[str]:
        """Extrai colunas referenciadas (implementação básica)"""
        columns = set()
        
        # Busca padrões SELECT column1, column2
        select_patterns = [
            r'(?i)SELECT\s+((?:[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?,?\s*)+)\s+FROM',
            r'(?i)WHERE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'(?i)ORDER\s+BY\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            r'(?i)GROUP\s+BY\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
        ]
        
        for pattern in select_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if ',' in match:
                    cols = [col.strip() for col in match.split(',')]
                    columns.update(cols)
                else:
                    columns.add(match.strip())
        
        # Remove palavras-chave SQL e SELECT *
        sql_keywords = {'SELECT', 'FROM', 'WHERE', 'ORDER', 'GROUP', 'BY', '*', 'AS', 'AND', 'OR'}
        columns = {col for col in columns if col.upper() not in sql_keywords and col}
        
        return list(columns)
    
    def _calculate_complexity_score(self, content: str) -> int:
        """Calcula score de complexidade do SQL"""
        score = 0
        content_upper = content.upper()
        
        # Pontuação por padrão
        complexity_scores = {
            'cte': 5,  # CTEs
            'join': 3,  # Joins
            'subquery': 4,  # Subqueries
            'window_function': 6,  # Window functions
            'case_when': 2,  # Case statements
            'union': 3,  # Union operations
            'aggregate': 2,  # Aggregate functions
            'having': 2,  # Having clauses
            'recursive': 8,  # Recursive CTEs
        }
        
        for pattern_name, pattern in self.complexity_patterns.items():
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            score += matches * complexity_scores.get(pattern_name, 1)
        
        # Pontuação adicional por tamanho
        lines = content.count('\n') + 1
        if lines > 50:
            score += 5
        elif lines > 20:
            score += 3
        elif lines > 10:
            score += 1
        
        return score
    
    def _extract_function_calls(self, content: str) -> List[str]:
        """Extrai funções SQL utilizadas"""
        functions = set()
        
        for category, func_list in self.sql_functions.items():
            for func in func_list:
                pattern = rf'\b{func}\s*\('
                if re.search(pattern, content, re.IGNORECASE):
                    functions.add(func)
        
        return list(functions)
    
    def _detect_performance_issues(self, content: str) -> List[str]:
        """Detecta problemas de performance"""
        issues = []
        
        for issue_type, patterns in self.security_patterns.items():
            if issue_type == 'performance_risks':
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        if 'SELECT *' in pattern:
                            issues.append("SELECT * pode impactar performance - especifique colunas necessárias")
                        elif 'LIKE' in pattern:
                            issues.append("LIKE com wildcard inicial (%) pode ser lento - considere full-text search")
                        elif 'ORDER BY' in pattern:
                            issues.append("ORDER BY sem LIMIT pode consumir muita memória")
        
        # Verificações adicionais
        content_upper = content.upper()
        
        if 'ORDER BY' in content_upper and 'LIMIT' not in content_upper:
            issues.append("ORDER BY sem LIMIT pode ser ineficiente para grandes datasets")
        
        if content_upper.count('JOIN') > 5:
            issues.append("Muitos JOINs podem impactar performance - considere desnormalizar")
        
        if 'GROUP BY' in content_upper and 'HAVING' not in content_upper and 'WHERE' not in content_upper:
            issues.append("GROUP BY sem filtros pode processar muitos dados desnecessariamente")
        
        return issues
    
    def _detect_security_issues(self, content: str) -> List[str]:
        """Detecta problemas de segurança"""
        issues = []
        
        for issue_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    if issue_type == 'sql_injection':
                        issues.append("Possível vulnerabilidade de SQL injection - use parâmetros preparados")
                    elif issue_type == 'unsafe_operations':
                        if 'DELETE' in pattern:
                            issues.append("DELETE sem WHERE pode apagar todos os registros")
                        elif 'UPDATE' in pattern:
                            issues.append("UPDATE sem WHERE pode alterar todos os registros")
                        elif 'TRUNCATE' in pattern:
                            issues.append("TRUNCATE apaga todos os dados da tabela")
                        elif 'DROP' in pattern:
                            issues.append("DROP remove estruturas do banco - operação irreversível")
        
        return issues
    
    def _generate_optimization_suggestions(self, stmt: SQLStatement) -> List[str]:
        """Gera sugestões de otimização"""
        suggestions = []
        
        # Sugestões baseadas na complexidade
        if stmt.complexity_score > 20:
            suggestions.append("Query muito complexa - considere dividir em CTEs ou views")
        
        if stmt.join_count > 4:
            suggestions.append("Muitos JOINs - verifique se todos são necessários")
        
        if stmt.subquery_count > 3:
            suggestions.append("Muitas subqueries - considere usar JOINs ou CTEs")
        
        # Sugestões baseadas no tipo
        if stmt.statement_type == 'SELECT':
            if 'SELECT *' in stmt.content.upper():
                suggestions.append("Especifique apenas as colunas necessárias ao invés de SELECT *")
        
        # Sugestões baseadas em funções
        if 'COUNT' in stmt.function_calls and 'GROUP BY' not in stmt.content.upper():
            suggestions.append("COUNT sem GROUP BY pode ser otimizado com EXISTS")
        
        # Sugestões para queries dinâmicas
        if stmt.is_dynamic and stmt.template_variables:
            suggestions.append("Query dinâmica - valide parâmetros para prevenir SQL injection")
        
        return suggestions
    
    def generate_comprehensive_analysis(self, statements: List[SQLStatement]) -> SQLAnalysisResult:
        """Gera análise abrangente de todos os statements"""
        
        if not statements:
            return SQLAnalysisResult(
                total_statements=0,
                statements_by_type={},
                complexity_distribution={},
                performance_issues_count=0,
                security_issues_count=0,
                tables_usage_frequency={},
                most_complex_queries=[],
                optimization_opportunities=[],
                data_lineage={},
                quality_score=0.0
            )
        
        # Estatísticas por tipo
        statements_by_type = {}
        for stmt in statements:
            statements_by_type[stmt.statement_type] = statements_by_type.get(stmt.statement_type, 0) + 1
        
        # Distribuição de complexidade
        complexity_distribution = {
            'simples': len([s for s in statements if s.complexity_score <= 5]),
            'moderada': len([s for s in statements if 5 < s.complexity_score <= 15]),
            'alta': len([s for s in statements if 15 < s.complexity_score <= 30]),
            'muito_alta': len([s for s in statements if s.complexity_score > 30])
        }
        
        # Frequência de uso de tabelas
        tables_usage = {}
        for stmt in statements:
            for table in stmt.tables_referenced:
                tables_usage[table] = tables_usage.get(table, 0) + 1
        
        # Queries mais complexas
        most_complex = sorted(statements, key=lambda x: x.complexity_score, reverse=True)[:5]
        
        # Contagem de problemas
        performance_issues = sum(len(stmt.performance_concerns) for stmt in statements)
        security_issues = sum(len(stmt.security_issues) for stmt in statements)
        
        # Oportunidades de otimização
        optimization_opportunities = []
        for stmt in statements:
            if stmt.optimization_suggestions:
                optimization_opportunities.append({
                    'file': stmt.file_path,
                    'line': stmt.line_number,
                    'suggestions': stmt.optimization_suggestions,
                    'complexity': stmt.complexity_score
                })
        
        # Linhagem de dados (básica)
        data_lineage = self._build_basic_lineage(statements)
        
        # Score de qualidade
        quality_score = self._calculate_quality_score(statements)
        
        return SQLAnalysisResult(
            total_statements=len(statements),
            statements_by_type=statements_by_type,
            complexity_distribution=complexity_distribution,
            performance_issues_count=performance_issues,
            security_issues_count=security_issues,
            tables_usage_frequency=dict(sorted(tables_usage.items(), key=lambda x: x[1], reverse=True)),
            most_complex_queries=most_complex,
            optimization_opportunities=optimization_opportunities,
            data_lineage=data_lineage,
            quality_score=quality_score
        )
    
    def _build_basic_lineage(self, statements: List[SQLStatement]) -> Dict[str, List[str]]:
        """Constrói linhagem básica de dados"""
        lineage = {}
        
        for stmt in statements:
            if stmt.statement_type in ['INSERT', 'CREATE', 'UPDATE']:
                # Tabelas de destino
                target_tables = []
                if stmt.statement_type == 'INSERT':
                    target_tables = [t for t in stmt.tables_referenced if 'INSERT' in stmt.content.upper()]
                elif stmt.statement_type == 'CREATE':
                    target_tables = [t for t in stmt.tables_referenced if 'CREATE' in stmt.content.upper()]
                
                # Tabelas de origem (de SELECTs/JOINs)
                source_tables = [t for t in stmt.tables_referenced if t not in target_tables]
                
                for target in target_tables:
                    if target not in lineage:
                        lineage[target] = []
                    lineage[target].extend(source_tables)
        
        # Remove duplicatas
        for table in lineage:
            lineage[table] = list(set(lineage[table]))
        
        return lineage
    
    def _calculate_quality_score(self, statements: List[SQLStatement]) -> float:
        """Calcula score de qualidade do código SQL"""
        if not statements:
            return 0.0
        
        total_score = 0.0
        total_statements = len(statements)
        
        for stmt in statements:
            stmt_score = 100.0  # Começa com score perfeito
            
            # Penaliza por problemas de segurança
            stmt_score -= len(stmt.security_issues) * 15
            
            # Penaliza por problemas de performance
            stmt_score -= len(stmt.performance_concerns) * 5
            
            # Penaliza por complexidade excessiva
            if stmt.complexity_score > 30:
                stmt_score -= 20
            elif stmt.complexity_score > 15:
                stmt_score -= 10
            
            # Bonifica por uso de boas práticas
            if stmt.statement_type == 'SELECT' and 'SELECT *' not in stmt.content.upper():
                stmt_score += 5
            
            if stmt.cte_count > 0:  # Uso de CTEs é boa prática
                stmt_score += 3
            
            total_score += max(0, stmt_score)  # Não deixa score negativo
        
        return round(total_score / total_statements, 2)
    
    def export_analysis_report(self, analysis: SQLAnalysisResult, output_path: str) -> str:
        """Exporta relatório de análise para JSON"""
        
        # Converte dataclasses para dict
        report_data = {
            'analysis_metadata': {
                'timestamp': datetime.now().isoformat(),
                'analyzer_version': '2.0',
                'total_statements_analyzed': analysis.total_statements
            },
            'summary': {
                'statements_by_type': analysis.statements_by_type,
                'complexity_distribution': analysis.complexity_distribution,
                'quality_score': analysis.quality_score,
                'issues_summary': {
                    'performance_issues': analysis.performance_issues_count,
                    'security_issues': analysis.security_issues_count
                }
            },
            'detailed_analysis': {
                'tables_usage_frequency': analysis.tables_usage_frequency,
                'most_complex_queries': [asdict(stmt) for stmt in analysis.most_complex_queries],
                'optimization_opportunities': analysis.optimization_opportunities,
                'data_lineage': analysis.data_lineage
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Relatório de análise SQL exportado: {output_path}")
        return output_path
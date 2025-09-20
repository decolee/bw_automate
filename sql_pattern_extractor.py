#!/usr/bin/env python3
"""
SQL Pattern Extractor
====================

Módulo especializado para extração avançada de padrões SQL em códigos Python.
Suporte para SQL complexo, CTEs, subqueries e construções dinâmicas.

Autor: Assistant Claude
Data: 2025-09-20
"""

import re
import ast
import sqlparse
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SQLOperationType(Enum):
    """Tipos de operações SQL"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE_TABLE = "CREATE_TABLE"
    CREATE_TEMP_TABLE = "CREATE_TEMP_TABLE"
    DROP_TABLE = "DROP_TABLE"
    ALTER_TABLE = "ALTER_TABLE"
    TRUNCATE = "TRUNCATE"
    WITH_CTE = "WITH_CTE"
    MERGE = "MERGE"
    COPY = "COPY"


@dataclass
class SQLStatement:
    """Representa uma declaração SQL encontrada no código"""
    statement_type: SQLOperationType
    raw_sql: str
    tables_referenced: List[str]
    line_number: int
    is_dynamic: bool
    confidence: float
    context: str


class AdvancedSQLExtractor:
    """
    Extrator avançado de padrões SQL com suporte a construções complexas
    """
    
    def __init__(self):
        """Inicializa o extrator SQL"""
        # Padrões regex avançados para diferentes contextos
        self.sql_patterns = {
            # SQL em strings simples
            'simple_string': [
                r'["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE|WITH)[^"\']*)["\']',
                r'sql\s*=\s*["\']([^"\']+)["\']',
                r'query\s*=\s*["\']([^"\']+)["\']',
            ],
            
            # SQL em strings multi-linha
            'multiline_string': [
                r'["\'"]{3}([^"\']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE|WITH)[^"\']*)["\'"]{3}',
                r'sql\s*=\s*["\'"]{3}([^"\']+)["\'"]{3}',
            ],
            
            # SQL em f-strings
            'f_string': [
                r'f["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE|WITH)[^"\']*)["\']',
            ],
            
            # Pandas read_sql
            'pandas_read': [
                r'read_sql\s*\(\s*["\']([^"\']+)["\']',
                r'read_sql_query\s*\(\s*["\']([^"\']+)["\']',
                r'pd\.read_sql\s*\(\s*["\']([^"\']+)["\']',
            ],
            
            # Pandas to_sql
            'pandas_write': [
                r'\.to_sql\s*\(\s*["\']([^"\']+)["\']',
                r'to_sql\s*\(\s*["\']([^"\']+)["\']',
            ],
            
            # SQLAlchemy
            'sqlalchemy': [
                r'text\s*\(\s*["\']([^"\']+)["\']',
                r'execute\s*\(\s*["\']([^"\']+)["\']',
            ],
            
            # Airflow específico
            'airflow': [
                r'PostgresOperator\s*\([^)]*sql\s*=\s*["\']([^"\']+)["\']',
                r'sql\s*=\s*["\']([^"\']+)["\'].*PostgresOperator',
            ]
        }
        
        # Padrões para extração de nomes de tabelas
        self.table_patterns = {
            'from_clause': [
                r'(?i)FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'(?i)FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\s+(?:AS\s+)?[a-zA-Z_][a-zA-Z0-9_]*',
            ],
            'join_clause': [
                r'(?i)(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+|CROSS\s+)?JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'insert_into': [
                r'(?i)INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'update_table': [
                r'(?i)UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'delete_from': [
                r'(?i)DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'create_table': [
                r'(?i)CREATE\s+(?:TEMP\s+|TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'drop_table': [
                r'(?i)DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'alter_table': [
                r'(?i)ALTER\s+TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'truncate_table': [
                r'(?i)TRUNCATE\s+(?:TABLE\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
            ],
            'with_cte': [
                r'(?i)WITH\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+AS',
            ]
        }
        
        # Indicadores de SQL dinâmico
        self.dynamic_indicators = [
            r'\{[^}]*\}',  # {variable}
            r'%\([^)]*\)s',  # %(variable)s
            r'%s',  # %s
            r'\$\{[^}]*\}',  # ${variable}
            r'\.format\s*\(',  # .format()
            r'f["\']',  # f-string
        ]
    
    def extract_sql_statements(self, content: str, file_path: str) -> List[SQLStatement]:
        """
        Extrai todas as declarações SQL do conteúdo do arquivo
        
        Args:
            content: Conteúdo do arquivo
            file_path: Caminho do arquivo
            
        Returns:
            Lista de declarações SQL encontradas
        """
        statements = []
        lines = content.split('\n')
        
        # Processa linha por linha
        for line_num, line in enumerate(lines, 1):
            # Pula comentários
            if line.strip().startswith('#'):
                continue
            
            # Extrai SQL de diferentes contextos
            for pattern_type, patterns in self.sql_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        sql_text = match.group(1) if match.groups() else match.group(0)
                        
                        # Verifica se realmente é SQL
                        if self._is_valid_sql(sql_text):
                            statement = self._create_sql_statement(
                                sql_text, line_num, line.strip(), pattern_type
                            )
                            if statement:
                                statements.append(statement)
        
        # Processa strings multi-linha usando AST
        ast_statements = self._extract_multiline_sql_with_ast(content)
        statements.extend(ast_statements)
        
        return self._deduplicate_statements(statements)
    
    def _is_valid_sql(self, text: str) -> bool:
        """
        Verifica se o texto é uma declaração SQL válida
        
        Args:
            text: Texto a verificar
            
        Returns:
            True se é SQL válido
        """
        if len(text.strip()) < 10:
            return False
        
        # Palavras-chave SQL obrigatórias
        sql_keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 
            'ALTER', 'TRUNCATE', 'WITH', 'MERGE', 'COPY'
        ]
        
        text_upper = text.upper()
        return any(keyword in text_upper for keyword in sql_keywords)
    
    def _create_sql_statement(self, sql_text: str, line_num: int, context: str, pattern_type: str) -> Optional[SQLStatement]:
        """
        Cria um objeto SQLStatement a partir do texto SQL
        
        Args:
            sql_text: Texto SQL
            line_num: Número da linha
            context: Contexto da linha
            pattern_type: Tipo de padrão usado na extração
            
        Returns:
            SQLStatement se válido
        """
        try:
            # Determina o tipo da operação
            statement_type = self._determine_statement_type(sql_text)
            
            # Extrai tabelas referenciadas
            tables = self._extract_tables_from_sql(sql_text)
            
            # Verifica se é dinâmico
            is_dynamic = self._is_dynamic_sql(sql_text)
            
            # Calcula confiança baseada no contexto
            confidence = self._calculate_sql_confidence(sql_text, pattern_type)
            
            return SQLStatement(
                statement_type=statement_type,
                raw_sql=sql_text[:500],  # Limita tamanho
                tables_referenced=tables,
                line_number=line_num,
                is_dynamic=is_dynamic,
                confidence=confidence,
                context=context[:200]
            )
            
        except Exception:
            return None
    
    def _determine_statement_type(self, sql: str) -> SQLOperationType:
        """Determina o tipo de declaração SQL"""
        sql_upper = sql.upper().strip()
        
        if sql_upper.startswith('SELECT') or 'SELECT' in sql_upper[:20]:
            return SQLOperationType.SELECT
        elif sql_upper.startswith('INSERT'):
            return SQLOperationType.INSERT
        elif sql_upper.startswith('UPDATE'):
            return SQLOperationType.UPDATE
        elif sql_upper.startswith('DELETE'):
            return SQLOperationType.DELETE
        elif 'CREATE TEMP' in sql_upper or 'CREATE TEMPORARY' in sql_upper:
            return SQLOperationType.CREATE_TEMP_TABLE
        elif sql_upper.startswith('CREATE TABLE') or 'CREATE TABLE' in sql_upper[:30]:
            return SQLOperationType.CREATE_TABLE
        elif sql_upper.startswith('DROP TABLE') or 'DROP TABLE' in sql_upper[:20]:
            return SQLOperationType.DROP_TABLE
        elif sql_upper.startswith('ALTER TABLE') or 'ALTER TABLE' in sql_upper[:20]:
            return SQLOperationType.ALTER_TABLE
        elif sql_upper.startswith('TRUNCATE'):
            return SQLOperationType.TRUNCATE
        elif sql_upper.startswith('WITH'):
            return SQLOperationType.WITH_CTE
        elif sql_upper.startswith('MERGE'):
            return SQLOperationType.MERGE
        elif sql_upper.startswith('COPY'):
            return SQLOperationType.COPY
        else:
            return SQLOperationType.SELECT  # Default
    
    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """
        Extrai nomes de tabelas de uma declaração SQL
        
        Args:
            sql: Declaração SQL
            
        Returns:
            Lista de nomes de tabelas
        """
        tables = set()
        
        # Usa sqlparse para análise mais precisa quando possível
        try:
            parsed = sqlparse.parse(sql)
            for statement in parsed:
                tables.update(self._extract_tables_from_parsed_sql(statement))
        except:
            # Fallback para regex se sqlparse falhar
            pass
        
        # Usa padrões regex como backup/complemento
        for pattern_type, patterns in self.table_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, sql, re.IGNORECASE)
                for match in matches:
                    table_name = match.group(1).strip('"`\'')
                    if table_name and self._is_valid_table_name(table_name):
                        tables.add(table_name.lower())
        
        return list(tables)
    
    def _extract_tables_from_parsed_sql(self, statement) -> Set[str]:
        """
        Extrai tabelas usando sqlparse (análise sintática)
        
        Args:
            statement: Statement parseado pelo sqlparse
            
        Returns:
            Set de nomes de tabelas
        """
        tables = set()
        
        def extract_from_token(token):
            if token.ttype is sqlparse.tokens.Name:
                # Verifica se é um nome de tabela válido
                if self._is_valid_table_name(str(token)):
                    tables.add(str(token).lower())
            elif hasattr(token, 'tokens'):
                for subtoken in token.tokens:
                    extract_from_token(subtoken)
        
        for token in statement.tokens:
            extract_from_token(token)
        
        return tables
    
    def _is_valid_table_name(self, name: str) -> bool:
        """
        Verifica se é um nome de tabela válido
        
        Args:
            name: Nome a verificar
            
        Returns:
            True se é válido
        """
        if not name or len(name) < 2:
            return False
        
        # Remove schema se presente
        table_name = name.split('.')[-1]
        
        # Verifica se segue convenções de nomenclatura
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            return False
        
        # Exclui palavras-chave SQL comuns
        sql_keywords = {
            'select', 'from', 'where', 'and', 'or', 'not', 'in', 'on', 'as',
            'join', 'left', 'right', 'inner', 'outer', 'union', 'order', 'by',
            'group', 'having', 'limit', 'offset', 'case', 'when', 'then', 'else',
            'end', 'null', 'true', 'false', 'distinct', 'count', 'sum', 'avg',
            'max', 'min', 'exists', 'between', 'like', 'values'
        }
        
        return table_name.lower() not in sql_keywords
    
    def _is_dynamic_sql(self, sql: str) -> bool:
        """
        Verifica se o SQL contém elementos dinâmicos
        
        Args:
            sql: Declaração SQL
            
        Returns:
            True se é dinâmico
        """
        return any(re.search(pattern, sql) for pattern in self.dynamic_indicators)
    
    def _calculate_sql_confidence(self, sql: str, pattern_type: str) -> float:
        """
        Calcula confiança da extração SQL
        
        Args:
            sql: Declaração SQL
            pattern_type: Tipo de padrão usado
            
        Returns:
            Score de confiança (0-100)
        """
        confidence = 50.0  # Base
        
        # Ajusta baseado no tipo de padrão
        if pattern_type in ['simple_string', 'multiline_string']:
            confidence += 20
        elif pattern_type in ['pandas_read', 'pandas_write']:
            confidence += 30
        elif pattern_type == 'airflow':
            confidence += 25
        
        # Ajusta baseado na estrutura do SQL
        sql_upper = sql.upper()
        if 'FROM' in sql_upper and ('SELECT' in sql_upper or 'DELETE' in sql_upper):
            confidence += 15
        
        if 'WHERE' in sql_upper:
            confidence += 10
        
        # Penaliza se muito dinâmico
        if self._is_dynamic_sql(sql):
            confidence -= 15
        
        # Penaliza se muito curto
        if len(sql.strip()) < 20:
            confidence -= 20
        
        return max(0.0, min(100.0, confidence))
    
    def _extract_multiline_sql_with_ast(self, content: str) -> List[SQLStatement]:
        """
        Extrai SQL multi-linha usando análise AST
        
        Args:
            content: Conteúdo do arquivo
            
        Returns:
            Lista de statements SQL encontrados
        """
        statements = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Str):
                    # Python < 3.8
                    sql_candidate = node.s
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    # Python >= 3.8
                    sql_candidate = node.value
                else:
                    continue
                
                if self._is_valid_sql(sql_candidate):
                    statement = self._create_sql_statement(
                        sql_candidate, 
                        getattr(node, 'lineno', 0),
                        sql_candidate[:100],
                        'ast_extraction'
                    )
                    if statement:
                        statements.append(statement)
        
        except:
            # Se AST falhar, não é problema crítico
            pass
        
        return statements
    
    def _deduplicate_statements(self, statements: List[SQLStatement]) -> List[SQLStatement]:
        """
        Remove declarações SQL duplicadas
        
        Args:
            statements: Lista de statements
            
        Returns:
            Lista sem duplicatas
        """
        seen = set()
        unique_statements = []
        
        for stmt in statements:
            # Cria chave única baseada no SQL normalizado
            sql_normalized = re.sub(r'\s+', ' ', stmt.raw_sql.strip().upper())
            key = (sql_normalized, stmt.statement_type)
            
            if key not in seen:
                seen.add(key)
                unique_statements.append(stmt)
        
        return unique_statements
    
    def analyze_sql_complexity(self, statements: List[SQLStatement]) -> Dict[str, any]:
        """
        Analisa a complexidade das declarações SQL encontradas
        
        Args:
            statements: Lista de statements SQL
            
        Returns:
            Dicionário com métricas de complexidade
        """
        if not statements:
            return {}
        
        total_statements = len(statements)
        dynamic_count = sum(1 for s in statements if s.is_dynamic)
        
        # Conta tipos de operações
        operation_counts = {}
        for stmt in statements:
            op_type = stmt.statement_type.value
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        # Conta tabelas únicas
        all_tables = set()
        for stmt in statements:
            all_tables.update(stmt.tables_referenced)
        
        # Calcula confiança média
        avg_confidence = sum(s.confidence for s in statements) / total_statements
        
        return {
            'total_sql_statements': total_statements,
            'unique_tables_referenced': len(all_tables),
            'dynamic_statements': dynamic_count,
            'dynamic_percentage': (dynamic_count / total_statements) * 100,
            'operation_breakdown': operation_counts,
            'average_confidence': avg_confidence,
            'high_confidence_statements': sum(1 for s in statements if s.confidence > 80),
            'low_confidence_statements': sum(1 for s in statements if s.confidence < 50)
        }


# Exemplo de uso
if __name__ == "__main__":
    extractor = AdvancedSQLExtractor()
    
    # Exemplo de código para teste
    sample_code = '''
    import pandas as pd
    
    # Exemplo de SQL simples
    query = "SELECT * FROM usuarios WHERE ativo = true"
    
    # Exemplo de SQL multi-linha
    complex_query = """
        WITH vendas_recentes AS (
            SELECT cliente_id, SUM(valor) as total
            FROM vendas 
            WHERE data_venda >= '2024-01-01'
            GROUP BY cliente_id
        )
        SELECT c.nome, vr.total
        FROM clientes c
        JOIN vendas_recentes vr ON c.id = vr.cliente_id
        ORDER BY vr.total DESC
    """
    
    # Exemplo com pandas
    df = pd.read_sql("SELECT * FROM produtos WHERE categoria = 'eletrônicos'", conn)
    df.to_sql('produtos_eletronicos', conn, if_exists='replace')
    '''
    
    statements = extractor.extract_sql_statements(sample_code, "example.py")
    complexity = extractor.analyze_sql_complexity(statements)
    
    print(f"Statements encontrados: {len(statements)}")
    print(f"Complexidade: {complexity}")
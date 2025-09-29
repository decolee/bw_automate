#!/usr/bin/env python3
"""
Arquivo de teste para validação do mapeador PostgreSQL
Contém padrões diversos para teste de cobertura
"""

import pandas as pd
from sqlalchemy import create_engine
import psycopg2

# 1. SQL direto em strings
def query_users():
    sql = "SELECT * FROM usuarios WHERE ativo = true"
    return sql

# 2. ORM SQLAlchemy
class Usuario:
    __tablename__ = 'usuarios_orm'
    
    def save(self):
        engine = create_engine('postgresql://localhost/db')
        return engine.execute("INSERT INTO usuarios_orm VALUES (%s)", self.name)

# 3. Pandas SQL
def load_data():
    df = pd.read_sql("SELECT * FROM dados_pandas", con=connection)
    df.to_sql("dados_processados", con=connection, if_exists='replace')

# 4. F-strings dinâmicos
def dynamic_query(table_name):
    return f"SELECT count(*) FROM {table_name}_dinamica"

# 5. Operações complexas
def complex_operations():
    queries = [
        "CREATE TABLE vendas_temp AS SELECT * FROM vendas",
        "UPDATE estoque SET quantidade = quantidade - 1",
        "DELETE FROM logs WHERE data < '2024-01-01'",
        """
        WITH vendas_mensais AS (
            SELECT DATE_TRUNC('month', data) as mes, SUM(valor) as total
            FROM transacoes 
            GROUP BY mes
        )
        SELECT * FROM vendas_mensais
        """
    ]
    return queries

# 6. Padrões exóticos
quantum_tables = ["qubits_superposicao", "medidas_collapsed"]
blockchain_data = {"ethereum": "contratos_smart"}
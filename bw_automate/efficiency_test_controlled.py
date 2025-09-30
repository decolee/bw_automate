#!/usr/bin/env python3
"""
TESTE CONTROLADO DE EFICIÊNCIA - GROUND TRUTH
Dataset com tabelas conhecidas para medir precisão real
"""

# ========== TABELAS REAIS ESPERADAS (GROUND TRUTH) ==========
# Lista oficial de todas as tabelas que DEVEM ser detectadas neste arquivo
EXPECTED_TABLES = [
    # SQL direto
    "usuarios_sistema",
    "produtos_estoque",
    "pedidos_online",
    
    # ORM SQLAlchemy
    "categorias_produto",
    "enderecos_entrega",
    
    # Pandas
    "vendas_mensais",
    "relatorio_financeiro",
    
    # F-strings
    "logs_auditoria",
    
    # CTEs/Subqueries
    "metricas_performance",
    "dados_consolidados",
    
    # Operações CRUD
    "backup_dados",
    "temp_processamento",
    "historico_alteracoes",
    
    # Django ORM
    "auth_users",
    "django_sessions"
]

# ========== IMPLEMENTAÇÃO COM TABELAS REAIS ==========

import pandas as pd
import sqlalchemy as sa
from django.db import models

# 1. SQL DIRETO - DEVE DETECTAR 3 TABELAS
def consultas_basicas():
    sql1 = "SELECT * FROM usuarios_sistema WHERE ativo = true"
    sql2 = """
    INSERT INTO produtos_estoque (nome, quantidade, preco) 
    VALUES ('Produto A', 100, 29.90)
    """
    sql3 = "UPDATE pedidos_online SET status = 'enviado' WHERE id = 123"
    return [sql1, sql2, sql3]

# 2. ORM SQLALCHEMY - DEVE DETECTAR 2 TABELAS
class CategoriaProduto(sa.Table):
    __tablename__ = 'categorias_produto'
    id = sa.Column(sa.Integer, primary_key=True)
    nome = sa.Column(sa.String(100))

class EnderecoEntrega:
    __tablename__ = 'enderecos_entrega'
    
    def save_to_db(self):
        engine = sa.create_engine('postgresql://localhost/db')
        return engine.execute("INSERT INTO enderecos_entrega VALUES (%s)", self.data)

# 3. PANDAS SQL - DEVE DETECTAR 2 TABELAS
def processar_dados_pandas():
    # Leitura
    df_vendas = pd.read_sql("SELECT * FROM vendas_mensais", connection)
    
    # Escrita
    df_vendas.to_sql("relatorio_financeiro", con=connection, if_exists='replace')
    
    return df_vendas

# 4. F-STRINGS DINÂMICOS - DEVE DETECTAR 1 TABELA
def queries_dinamicas(data_inicio):
    tabela_logs = "logs_auditoria"
    query = f"SELECT * FROM {tabela_logs} WHERE data >= '{data_inicio}'"
    return query

# 5. CTEs E SUBQUERIES COMPLEXOS - DEVE DETECTAR 2 TABELAS
def relatorios_complexos():
    cte_query = """
    WITH metricas_performance AS (
        SELECT produto_id, AVG(tempo_resposta) as media_tempo
        FROM logs_sistema 
        GROUP BY produto_id
    )
    SELECT * FROM dados_consolidados d
    INNER JOIN metricas_performance m ON d.id = m.produto_id
    """
    return cte_query

# 6. OPERAÇÕES CRUD COMPLETAS - DEVE DETECTAR 3 TABELAS
def operacoes_manutencao():
    queries = [
        "CREATE TABLE backup_dados AS SELECT * FROM dados_principais",
        "INSERT INTO temp_processamento SELECT * FROM dados_raw WHERE status = 'new'",
        "UPDATE temp_processamento SET processado = true WHERE id > 0",
        "DELETE FROM historico_alteracoes WHERE data < '2024-01-01'",
        "DROP TABLE temp_old_data"
    ]
    return queries

# 7. DJANGO ORM - DEVE DETECTAR 2 TABELAS  
class User(models.Model):
    class Meta:
        db_table = 'auth_users'
    
    username = models.CharField(max_length=150)

class Session(models.Model):
    class Meta:
        db_table = 'django_sessions'
    
    session_key = models.CharField(max_length=40)

# ========== FALSOS NEGATIVOS INTENCIONAIS (NÃO DEVEM SER DETECTADOS) ==========
# Estas NÃO são tabelas reais, apenas palavras comuns
def palavras_comuns():
    # Palavras que PODEM ser confundidas com tabelas mas NÃO SÃO
    resultado = "success"
    dados = {"key": "value"}
    info = "informação importante"
    value = 123
    
    # Strings que PODEM parecer SQL mas NÃO SÃO
    mensagem = "FROM this point ON we will SELECT the best approach"
    texto = "CREATE a new UPDATE in the system"
    
    return resultado, dados, info, value, mensagem, texto

# ========== ANÁLISE DE EFICIÊNCIA ==========
if __name__ == "__main__":
    print("🎯 ARQUIVO DE TESTE CONTROLADO CRIADO")
    print(f"📊 Tabelas esperadas: {len(EXPECTED_TABLES)}")
    print("📋 Lista de tabelas que DEVEM ser detectadas:")
    for i, table in enumerate(EXPECTED_TABLES, 1):
        print(f"  {i:2d}. {table}")
    
    print("\n⚠️ IMPORTANTE: Este arquivo contém exatamente as tabelas listadas acima.")
    print("   Qualquer detecção adicional é um FALSO POSITIVO.")
    print("   Qualquer tabela não detectada é um FALSO NEGATIVO.")
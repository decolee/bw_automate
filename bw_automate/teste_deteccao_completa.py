#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO DE DETECÇÃO DE TABELAS POSTGRESQL
Testa TODOS os padrões possíveis de referência a tabelas
"""

# ===== 1. SQL DIRETO EM STRINGS =====
def sql_basico():
    query1 = "SELECT * FROM usuarios"
    query2 = "INSERT INTO produtos (nome, preco) VALUES ('teste', 100)"
    query3 = "UPDATE clientes SET ativo = true WHERE id = 1"
    query4 = "DELETE FROM pedidos WHERE status = 'cancelado'"
    query5 = "CREATE TABLE vendas (id SERIAL PRIMARY KEY)"
    query6 = "DROP TABLE temp_data"
    query7 = "TRUNCATE TABLE logs"
    query8 = "ALTER TABLE categorias ADD COLUMN descricao TEXT"

# ===== 2. SQL COM SCHEMAS =====
def sql_com_schema():
    query1 = "SELECT * FROM public.usuarios"
    query2 = "INSERT INTO warehouse.produtos VALUES (1, 'teste')"
    query3 = "UPDATE analytics.clientes SET status = 'ativo'"
    query4 = "DELETE FROM staging.temp_data"
    query5 = "CREATE TABLE reporting.vendas (id INT)"

# ===== 3. SQL EM F-STRINGS E FORMATAÇÃO =====
def sql_formatado():
    tabela = "usuarios"
    query1 = f"SELECT * FROM {tabela}"
    query2 = f"INSERT INTO produtos_{tabela} VALUES (1)"
    query3 = "SELECT * FROM {}".format("clientes")
    query4 = "INSERT INTO %s VALUES (1)" % "pedidos"

# ===== 4. SQL EM VARIÁVEIS E CONCATENAÇÃO =====
def sql_dinamico():
    base_table = "usuarios"
    schema = "public"
    
    # Concatenação simples
    query1 = "SELECT * FROM " + base_table
    query2 = "INSERT INTO " + schema + "." + base_table + " VALUES (1)"
    
    # Variáveis complexas
    table_name = f"{schema}.produtos"
    query3 = f"SELECT * FROM {table_name}"

# ===== 5. SQLALCHEMY MODELS =====
from sqlalchemy import Column, Integer, String, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))

class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True)

# SQLAlchemy Table direto
metadata = MetaData()
clientes_table = Table('clientes', metadata,
    Column('id', Integer, primary_key=True)
)

pedidos_table = Table(
    'pedidos', 
    metadata,
    Column('id', Integer)
)

# ===== 6. DJANGO MODELS =====
# (Simulando imports do Django)
class Model:
    pass

class CharField:
    def __init__(self, max_length=None):
        pass

class Usuario(Model):
    class Meta:
        db_table = 'usuarios_django'
    
    nome = CharField(max_length=100)

class Produto(Model):
    class Meta:
        db_table = 'produtos_django'

# ===== 7. DECORATORS E ANOTAÇÕES =====
def table(name):
    def decorator(cls):
        cls._table_name = name
        return cls
    return decorator

@table('usuarios_decorator')
class UsuarioDecorator:
    pass

@table('produtos_decorator')
class ProdutoDecorator:
    pass

# ===== 8. EXECUTE COM CURSOR =====
def database_operations():
    import psycopg2
    
    # Simulando operações com cursor
    cursor = None
    
    # Diferentes formas de execute
    cursor.execute("SELECT * FROM vendas")
    cursor.execute("INSERT INTO logs (mensagem) VALUES (%s)", ["teste"])
    cursor.execute("""
        SELECT v.id, v.total, c.nome 
        FROM vendas v 
        JOIN clientes c ON v.cliente_id = c.id
    """)
    
    # Execute com variáveis
    table_name = "relatorios"
    cursor.execute(f"SELECT * FROM {table_name}")

# ===== 9. PANDAS E BIBLIOTECAS DE DADOS =====
def pandas_operations():
    import pandas as pd
    
    # pd.read_sql
    df1 = pd.read_sql("SELECT * FROM vendas", conexao)
    df2 = pd.read_sql_table('usuarios', conexao)
    df3 = pd.read_sql_query("SELECT * FROM produtos", conexao)
    
    # to_sql
    df1.to_sql('vendas_backup', conexao)
    df2.to_sql(name='usuarios_temp', con=conexao)

# ===== 10. JOINS E QUERIES COMPLEXAS =====
def queries_complexas():
    query_join = """
        SELECT 
            u.nome,
            p.titulo,
            c.nome as categoria
        FROM usuarios u
        JOIN posts p ON u.id = p.usuario_id
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE u.ativo = true
    """
    
    query_subquery = """
        SELECT * FROM vendas v
        WHERE v.total > (
            SELECT AVG(total) FROM vendas_historico
        )
    """
    
    query_cte = """
        WITH vendas_mes AS (
            SELECT * FROM vendas WHERE EXTRACT(MONTH FROM data) = 3
        )
        SELECT * FROM vendas_mes vm
        JOIN produtos p ON vm.produto_id = p.id
    """

# ===== 11. NOMES DE TABELAS EM ARQUIVOS EXTERNOS =====
TABLE_MAPPING = {
    'users': 'usuarios_sistema',
    'products': 'produtos_catalogo',
    'orders': 'pedidos_ecommerce'
}

# Lista de tabelas
TABLES_LIST = [
    'auditoria',
    'configuracoes',
    'notificacoes',
    'backups'
]

# ===== 12. STORED PROCEDURES E FUNCTIONS =====
def stored_procedures():
    queries = [
        "CALL processar_vendas()",
        "SELECT * FROM obter_relatorio_vendas()",
        "EXECUTE criar_backup_tabela('usuarios')",
        "SELECT inserir_produto('Novo Produto', 99.99)"
    ]

# ===== 13. VIEWS E MATERIALIZED VIEWS =====
def views_operations():
    queries = [
        "CREATE VIEW vw_vendas_mes AS SELECT * FROM vendas",
        "DROP VIEW vw_produtos_ativos",
        "CREATE MATERIALIZED VIEW mv_relatorio AS SELECT * FROM dados_consolidados",
        "REFRESH MATERIALIZED VIEW mv_estatisticas"
    ]

# ===== 14. ÍNDICES E CONSTRAINTS =====
def indices_constraints():
    queries = [
        "CREATE INDEX idx_usuario_email ON usuarios(email)",
        "CREATE UNIQUE INDEX idx_produto_sku ON produtos(sku)",
        "ALTER TABLE pedidos ADD CONSTRAINT fk_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id)",
        "DROP INDEX idx_temp_data"
    ]

# ===== 15. TRIGGERS E EVENTOS =====
def triggers_eventos():
    queries = [
        "CREATE TRIGGER tr_audit_usuarios AFTER INSERT ON usuarios FOR EACH ROW EXECUTE FUNCTION audit_log()",
        "DROP TRIGGER tr_update_timestamp ON produtos",
        "CREATE OR REPLACE FUNCTION processar_pedido() RETURNS TRIGGER AS $$ BEGIN INSERT INTO auditoria VALUES (NEW.id); RETURN NEW; END; $$ LANGUAGE plpgsql"
    ]

# ===== 16. COPY E BULK OPERATIONS =====
def bulk_operations():
    queries = [
        "COPY usuarios FROM '/tmp/usuarios.csv' WITH CSV HEADER",
        "COPY produtos TO '/tmp/backup_produtos.csv' WITH CSV",
        "COPY (SELECT * FROM vendas WHERE data > '2023-01-01') TO '/tmp/vendas_2023.csv'"
    ]

if __name__ == "__main__":
    print("🧪 Arquivo de teste criado com TODOS os padrões possíveis de tabelas PostgreSQL")
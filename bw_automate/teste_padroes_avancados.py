#!/usr/bin/env python3
"""
🧪 TESTE DE PADRÕES AVANÇADOS DE DETECÇÃO
"""

# === TESTES DE PADRÕES AVANÇADOS ===

# 1. Nomes de tabelas em dicionários e listas
TABLES = {
    'master': 'usuarios_master',
    'backup': 'usuarios_backup'
}

table_list = ['vendas_2023', 'vendas_2024', 'vendas_temp']

# 2. Tabelas em loops dinâmicos  
for year in [2022, 2023, 2024]:
    table_name = f'vendas_{year}'
    query = f'SELECT * FROM {table_name}'

# 3. Tabelas em condicionais
if True:  # ambiente == 'prod'
    tabela_logs = 'logs_producao'
else:
    tabela_logs = 'logs_desenvolvimento'

# 4. Imports e configurações externas
# from config import DATABASE_TABLES
# main_table = DATABASE_TABLES['users']

# 5. Raw SQL em docstrings
def get_user_data():
    """
    Executa query: SELECT * FROM usuarios_analytics
    """
    pass

# 6. SQL em comentários
# Exemplo: INSERT INTO produtos_catalog VALUES (1, 'item')
# Query base: UPDATE clientes_crm SET status = 'ativo'

# 7. Context managers e with statements
class DatabaseContext:
    def table(self, name):
        return self
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

database = DatabaseContext()
with database.table('sessoes_usuario') as table:
    pass

# 8. Lambdas e compreensões
tables = [f'temp_{i}' for i in range(3)]
table_ops = lambda t: f'SELECT COUNT(*) FROM {t}'

# 9. Configuração via ENV
import os
TABLE_PREFIX = 'app_'
user_table = f'{TABLE_PREFIX}usuarios'

# 10. Template strings
query_template = 'SELECT * FROM $table_name'
final_query = query_template.replace('$table_name', 'produtos_especiais')

# 11. Nomes de tabelas em URLs/paths
api_endpoint = '/api/v1/table/usuarios_api/data'
file_path = '/data/exports/tabela_relatorios.csv'

# 12. SQL em diferentes formatos de string
sql_multiline = """
    SELECT u.id, u.nome,
           p.titulo
    FROM usuarios_blog u
    LEFT JOIN posts_blog p ON u.id = p.autor_id
"""

sql_raw = r'SELECT * FROM dados_raw WHERE path LIKE "%temp%"'

# 13. Exec e eval com SQL
sql_code = "SELECT * FROM tabela_dinamica"

# 14. Variáveis com nomes de tabela
MAIN_TABLE = "usuarios_principais"
BACKUP_TABLE = "usuarios_backup_2024"

# 15. SQL dentro de listas e tuplas
queries = [
    "SELECT * FROM vendas_janeiro",
    "SELECT * FROM vendas_fevereiro",
    "INSERT INTO auditoria_vendas VALUES (1)"
]

sql_tuple = (
    "UPDATE produtos_catalogo SET ativo = true",
    "DELETE FROM produtos_inativos"
)

# 16. SQL em dicionários
sql_operations = {
    'get_users': "SELECT * FROM usuarios_sistema",
    'get_products': "SELECT * FROM produtos_loja",
    'cleanup': "TRUNCATE TABLE cache_temporario"
}

# 17. Métodos que retornam SQL
def get_table_query(table_name):
    return f"SELECT * FROM {table_name}"

def build_insert_query():
    return "INSERT INTO logs_aplicacao (timestamp, message) VALUES (NOW(), 'test')"

# 18. Classes com SQL
class DatabaseManager:
    TABLE_NAME = "manager_config"
    
    def get_data(self):
        return "SELECT * FROM dados_manager"
    
    def insert_log(self):
        sql = "INSERT INTO logs_manager VALUES (1)"
        return sql

# 19. SQL com escape characters
escaped_sql = "SELECT * FROM \"table with spaces\" WHERE name = 'test'"
quoted_sql = 'SELECT * FROM `produtos_mysql` WHERE id = 1'

# 20. Arrays e sets com tabelas
table_array = ["tabela_a", "tabela_b", "tabela_c"]
table_set = {"set_tabela_1", "set_tabela_2"}

if __name__ == "__main__":
    print("🧪 Teste de padrões avançados criado")
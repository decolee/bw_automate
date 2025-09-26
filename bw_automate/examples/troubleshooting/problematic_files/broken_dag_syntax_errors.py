#!/usr/bin/env python3
"""
Arquivo problemático 1 - Erros de Sintaxe
==========================================

Este arquivo contém vários tipos de problemas que o BW_AUTOMATE deve detectar e reportar:
- Sintaxe SQL incorreta
- Strings não fechadas
- Variáveis indefinidas
- Tabelas com nomes inválidos

Este arquivo serve para testar a robustez do sistema de análise.
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

# DAG com problemas
dag = DAG(
    'dag_com_problemas',
    start_date=datetime(2025, 1, 1),
    catchup=False
)

def funcao_com_sql_quebrado():
    """
    Função com SQL mal formado
    """
    # SQL com sintaxe incorreta - SELECT sem FROM
    sql_quebrado = """
    SELECT 
        usuario_id,
        nome,
        email
    WHERE ativo = true;  -- Sem FROM!
    """
    
    # String SQL não fechada
    sql_nao_fechado = """
    SELECT * FROM usuarios
    WHERE data_criacao >= '2025-01-01
    # Aspas não fechadas!
    
    # Tabela com nome inválido (números no início)
    sql_nome_invalido = "SELECT * FROM 123_tabela_invalida"
    
    # SQL com caracteres especiais problemáticos
    sql_especiais = """
    SELECT * FROM "tabela com espaços" 
    WHERE campo = 'valor com ''' aspas problemáticas'
    """

def funcao_com_variaveis_indefinidas():
    """
    Função que usa variáveis não definidas
    """
    # Variável não definida
    sql = f"SELECT * FROM {tabela_nao_definida} WHERE id = {id_nao_existe}"
    
    # f-string com expressão complexa e perigosa
    tabela_dinamica = f"temp_{usuario}_{datetime.now().strftime('%Y%m%d')}"
    sql_dinamico = f"""
    CREATE TABLE {tabela_dinamica} AS 
    SELECT * FROM {outra_tabela_inexistente}
    """

def funcao_com_sql_complexo_quebrado():
    """
    SQL complexo com múltiplos problemas
    """
    # CTE mal formado
    sql_cte_quebrado = """
    WITH dados_usuario AS (
        SELECT 
            usuario_id,
            nome
        FROM usuarios  -- Vírgula faltando na próxima linha
        nome_completo VARCHAR(255)
    ),
    dados_pedidos AS  -- Faltou parênteses
        SELECT p.* 
        FROM pedidos p
        WHERE p.usuario_id = dados_usuario.usuario_id  -- Referência incorreta
    
    SELECT * FROM dados_usuario 
    INNER JOIN dados_pedidos ON 1=1;  -- Join sem critério adequado
    """
    
    # Subquery com problemas
    sql_subquery_problema = """
    SELECT 
        (SELECT COUNT(*) FROM pedidos WHERE usuario_id = u.id) as total_pedidos,
        (SELECT MAX(data) FROM pedidos WHERE usuario_id = u.id AND STATUS = 'concluido') as ultima_compra,
        -- Próxima linha tem problema: coluna não existe na subquery
        (SELECT produto_nome FROM pedidos WHERE usuario_id = u.id) as ultimo_produto
    FROM usuarios u
    WHERE EXISTS (
        SELECT 1 FROM pedidos 
        WHERE usuario_id = u.id 
        AND data >= CURRENT_DATE - INTERVAL  -- Faltou o valor do intervalo
    );
    """

def funcao_com_operacoes_pandas_problematicas():
    """
    Operações pandas com problemas
    """
    import pandas as pd
    
    # read_sql com problemas
    df = pd.read_sql("""
        SELECT * FROM tabela_que_nao_existe
        WHERE coluna_inexistente = 'valor'
    """, conexao_nao_definida)
    
    # to_sql com parâmetros incorretos
    df.to_sql(
        name="",  # Nome vazio
        con=engine_nao_existe,
        schema="schema.inexistente",  # Schema com ponto
        if_exists="create"  # Valor inválido
    )
    
    # Concatenação perigosa para SQL injection
    usuario_input = "'; DROP TABLE usuarios; --"
    sql_injection = f"SELECT * FROM logs WHERE usuario = '{usuario_input}'"

def funcao_com_encoding_problemas():
    """
    Problemas de encoding e caracteres especiais
    """
    # String com caracteres especiais problemáticos
    sql_encoding = """
    SELECT 
        usuário_id,  -- Caractere especial
        descrição,   -- Acentos
        endereço
    FROM usuários 
    WHERE situação = 'ação_pendente'
    """
    
    # Comentários com encoding problemático
    # Query para relatório de situação dos usuários
    # Última atualização: João da Silva - 20/09/2025
    sql_comentarios = "SELECT * FROM situacao_usuarios"

# Funções que simulam problemas de importação
try:
    from modulo_inexistente import funcao_nao_existe
    sql_com_import_quebrado = "SELECT * FROM tabela_modulo_quebrado"
except ImportError:
    # Tratamento inadequado
    pass

# Variáveis globais problemáticas
TABELA_GLOBAL = None  # Será usado em SQL
SCHEMA_INDEFINIDO = ""

def funcao_usando_globais_problematicas():
    """
    Usa variáveis globais que podem causar problemas
    """
    sql = f"SELECT * FROM {SCHEMA_INDEFINIDO}.{TABELA_GLOBAL}"
    
    # Lista de tabelas com problemas
    tabelas_com_problemas = [
        "tabela-com-hífen",  # Hífen no nome
        "123_inicia_com_numero",
        "tabela com espaços",
        "",  # Nome vazio
        None,  # Valor None
        "TABELA_MUITO_LONGA_QUE_EXCEDE_LIMITE_NORMAL_DE_CARACTERES_PARA_NOMES_DE_TABELAS_EM_POSTGRESQL"
    ]
    
    for tabela in tabelas_com_problemas:
        sql_loop = f"SELECT COUNT(*) FROM {tabela}"

# Tasks com problemas
task_problema_1 = PythonOperator(
    task_id='task_com_sql_quebrado',
    python_callable=funcao_com_sql_quebrado,
    dag=dag
)

# Task com callable que não existe
task_problema_2 = PythonOperator(
    task_id='task_com_funcao_inexistente', 
    python_callable=funcao_que_nao_existe,  # Função não definida
    dag=dag
)

# Dependência circular (se descomentado causaria erro)
# task_problema_1 >> task_problema_2
# task_problema_2 >> task_problema_1
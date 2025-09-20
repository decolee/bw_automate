#!/usr/bin/env python3
"""
DAG de Exemplo 1 - Operações Básicas
====================================

Este DAG demonstra operações básicas de leitura e escrita em tabelas PostgreSQL.
Inclui padrões comuns encontrados em DAGs do Airflow.

Tabelas envolvidas:
- Leitura: financeiro.transacoes, financeiro.clientes
- Escrita: analytics.vendas_diarias, staging.temp_import_clientes

Autor: BW_AUTOMATE Examples
Data: 2025-09-20
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.hooks.postgres_hook import PostgresHook
from datetime import datetime, timedelta
import pandas as pd
import logging

# Configurações do DAG
default_args = {
    'owner': 'time_dados',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'exemplo_basico_financeiro',
    default_args=default_args,
    description='DAG de exemplo com operações básicas PostgreSQL',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['exemplo', 'financeiro', 'basic']
)

def extrair_transacoes_do_dia():
    """
    Extrai transações do dia atual da tabela de transações
    """
    # Conexão com PostgreSQL
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # SQL para extrair transações (operação READ)
    sql_query = """
    SELECT 
        t.id,
        t.cliente_id,
        t.valor,
        t.data_transacao,
        c.nome as cliente_nome,
        c.categoria
    FROM financeiro.transacoes t
    INNER JOIN financeiro.clientes c ON t.cliente_id = c.id
    WHERE t.data_transacao = CURRENT_DATE
    ORDER BY t.data_transacao DESC;
    """
    
    # Executa query e retorna resultados
    df = pg_hook.get_pandas_df(sql_query)
    logging.info(f"Extraídas {len(df)} transações do dia")
    
    return df.to_json()

def processar_vendas_diarias(**context):
    """
    Processa vendas diárias e grava na tabela de analytics
    """
    # Recupera dados do task anterior
    ti = context['task_instance']
    transacoes_json = ti.xcom_pull(task_ids='extrair_transacoes')
    
    if not transacoes_json:
        logging.warning("Nenhuma transação encontrada")
        return
    
    # Converte de JSON para DataFrame
    df_transacoes = pd.read_json(transacoes_json)
    
    # Processa dados (agregação por categoria)
    vendas_por_categoria = df_transacoes.groupby('categoria').agg({
        'valor': ['sum', 'count', 'mean'],
        'cliente_id': 'nunique'
    }).round(2)
    
    # Prepara dados para inserção
    vendas_processadas = []
    for categoria in vendas_por_categoria.index:
        registro = {
            'categoria': categoria,
            'total_vendas': float(vendas_por_categoria.loc[categoria, ('valor', 'sum')]),
            'qtd_transacoes': int(vendas_por_categoria.loc[categoria, ('valor', 'count')]),
            'ticket_medio': float(vendas_por_categoria.loc[categoria, ('valor', 'mean')]),
            'clientes_unicos': int(vendas_por_categoria.loc[categoria, ('cliente_id', 'nunique')]),
            'data_processamento': datetime.now().date()
        }
        vendas_processadas.append(registro)
    
    # Grava na tabela de analytics (operação WRITE)
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Limpa dados do dia (se existirem)
    delete_sql = "DELETE FROM analytics.vendas_diarias WHERE data_processamento = CURRENT_DATE"
    pg_hook.run(delete_sql)
    
    # Insere novos dados
    for venda in vendas_processadas:
        insert_sql = """
        INSERT INTO analytics.vendas_diarias 
        (categoria, total_vendas, qtd_transacoes, ticket_medio, clientes_unicos, data_processamento)
        VALUES (%(categoria)s, %(total_vendas)s, %(qtd_transacoes)s, %(ticket_medio)s, %(clientes_unicos)s, %(data_processamento)s)
        """
        pg_hook.run(insert_sql, parameters=venda)
    
    logging.info(f"Processadas {len(vendas_processadas)} categorias de vendas")

def backup_clientes_staging():
    """
    Cria backup diário de clientes na área de staging
    """
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Cria tabela temporária (operação CREATE)
    create_temp_sql = """
    CREATE TEMP TABLE temp_backup_clientes AS
    SELECT 
        id,
        nome,
        email,
        categoria,
        data_cadastro,
        ativo,
        CURRENT_TIMESTAMP as data_backup
    FROM financeiro.clientes
    WHERE ativo = true;
    """
    
    pg_hook.run(create_temp_sql)
    
    # Limpa staging anterior
    truncate_sql = "TRUNCATE TABLE staging.temp_import_clientes"
    pg_hook.run(truncate_sql)
    
    # Copia dados para staging (operação INSERT)
    insert_staging_sql = """
    INSERT INTO staging.temp_import_clientes 
    SELECT * FROM temp_backup_clientes;
    """
    
    pg_hook.run(insert_staging_sql)
    
    # Verifica quantidade copiada
    count_sql = "SELECT COUNT(*) as total FROM staging.temp_import_clientes"
    result = pg_hook.get_first(count_sql)
    
    logging.info(f"Backup realizado: {result[0]} clientes copiados para staging")

def gerar_relatorio_diario():
    """
    Gera relatório consolidado do dia usando dados processados
    """
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Query complexa com múltiplas tabelas (múltiplas operações READ)
    relatorio_sql = """
    WITH vendas_hoje AS (
        SELECT 
            categoria,
            total_vendas,
            qtd_transacoes,
            ticket_medio
        FROM analytics.vendas_diarias 
        WHERE data_processamento = CURRENT_DATE
    ),
    clientes_ativos AS (
        SELECT 
            categoria,
            COUNT(*) as total_clientes
        FROM financeiro.clientes 
        WHERE ativo = true
        GROUP BY categoria
    )
    SELECT 
        v.categoria,
        v.total_vendas,
        v.qtd_transacoes,
        v.ticket_medio,
        c.total_clientes,
        ROUND(v.total_vendas / c.total_clientes, 2) as vendas_per_capita
    FROM vendas_hoje v
    LEFT JOIN clientes_ativos c ON v.categoria = c.categoria
    ORDER BY v.total_vendas DESC;
    """
    
    df_relatorio = pg_hook.get_pandas_df(relatorio_sql)
    
    # Salva relatório em arquivo (simulado)
    logging.info("Relatório diário gerado:")
    logging.info(f"\n{df_relatorio.to_string()}")
    
    return f"Relatório processado com {len(df_relatorio)} categorias"

# Definição das tasks
task_extrair = PythonOperator(
    task_id='extrair_transacoes',
    python_callable=extrair_transacoes_do_dia,
    dag=dag
)

task_processar = PythonOperator(
    task_id='processar_vendas',
    python_callable=processar_vendas_diarias,
    dag=dag
)

task_backup = PythonOperator(
    task_id='backup_clientes',
    python_callable=backup_clientes_staging,
    dag=dag
)

task_relatorio = PythonOperator(
    task_id='gerar_relatorio',
    python_callable=gerar_relatorio_diario,
    dag=dag
)

# Comando SQL direto via BashOperator (operação UPDATE)
task_update_stats = BashOperator(
    task_id='atualizar_estatisticas',
    bash_command="""
    psql $POSTGRES_CONN_STRING -c "
    UPDATE public.configurations 
    SET valor = CURRENT_TIMESTAMP::text 
    WHERE chave = 'ultima_execucao_vendas';
    "
    """,
    dag=dag
)

# Dependências entre tasks
task_extrair >> task_processar
task_processar >> [task_backup, task_relatorio]
[task_backup, task_relatorio] >> task_update_stats
#!/usr/bin/env python3
"""
DAG de Exemplo 3 - Operações Pandas
===================================

Este DAG demonstra uso intensivo de pandas com PostgreSQL:
- read_sql e to_sql
- Processamento de dados em DataFrames
- Operações ETL complexas
- Merge de múltiplas fontes

Tabelas envolvidas:
- Leitura: ecommerce.produtos, ecommerce.estoque, analytics.events, public.logs
- Escrita: analytics.metrics, staging.produtos_processados

Autor: BW_AUTOMATE Examples
Data: 2025-09-20
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from sqlalchemy import create_engine

default_args = {
    'owner': 'time_dados',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'etl_pandas_produtos',
    default_args=default_args,
    description='ETL completo usando pandas e PostgreSQL',
    schedule_interval='0 1 * * *',  # 1h da manhã
    catchup=False,
    tags=['etl', 'pandas', 'produtos', 'data-processing']
)

def extrair_dados_produtos(**context):
    """
    Extrai dados de produtos de múltiplas tabelas usando pandas
    """
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    engine = pg_hook.get_sqlalchemy_engine()
    
    # Extração 1: Dados básicos de produtos (operação READ)
    df_produtos = pd.read_sql("""
        SELECT 
            id as produto_id,
            nome,
            categoria,
            preco,
            descricao,
            ativo,
            data_criacao,
            data_atualizacao
        FROM ecommerce.produtos 
        WHERE ativo = true
    """, engine)
    
    logging.info(f"Extraídos {len(df_produtos)} produtos ativos")
    
    # Extração 2: Dados de estoque (operação READ)
    df_estoque = pd.read_sql("""
        SELECT 
            produto_id,
            quantidade_disponivel,
            quantidade_reservada,
            estoque_minimo,
            ultima_atualizacao_estoque,
            fornecedor_id
        FROM ecommerce.estoque
    """, engine)
    
    logging.info(f"Extraídos dados de estoque para {len(df_estoque)} produtos")
    
    # Extração 3: Eventos de produtos dos últimos 30 dias (operação READ)
    df_eventos = pd.read_sql("""
        SELECT 
            produto_id,
            evento_tipo,
            COUNT(*) as qtd_eventos,
            COUNT(DISTINCT usuario_id) as usuarios_unicos
        FROM analytics.events 
        WHERE timestamp_evento >= CURRENT_DATE - INTERVAL '30 days'
          AND produto_id IS NOT NULL
        GROUP BY produto_id, evento_tipo
    """, engine)
    
    logging.info(f"Extraídos eventos para {df_eventos['produto_id'].nunique()} produtos")
    
    # Salva dados em arquivos temporários para próxima task
    context['task_instance'].xcom_push(key='df_produtos', value=df_produtos.to_json())
    context['task_instance'].xcom_push(key='df_estoque', value=df_estoque.to_json())
    context['task_instance'].xcom_push(key='df_eventos', value=df_eventos.to_json())
    
    return {
        'produtos_extraidos': len(df_produtos),
        'registros_estoque': len(df_estoque),
        'eventos_produtos': len(df_eventos)
    }

def transformar_dados_produtos(**context):
    """
    Transforma e enriquece dados usando pandas
    """
    ti = context['task_instance']
    
    # Recupera dados da task anterior
    df_produtos = pd.read_json(ti.xcom_pull(key='df_produtos'))
    df_estoque = pd.read_json(ti.xcom_pull(key='df_estoque'))
    df_eventos = pd.read_json(ti.xcom_pull(key='df_eventos'))
    
    # Transformação 1: Pivot dos eventos por tipo
    df_eventos_pivot = df_eventos.pivot_table(
        index='produto_id',
        columns='evento_tipo',
        values=['qtd_eventos', 'usuarios_unicos'],
        aggfunc='sum',
        fill_value=0
    )
    
    # Achata as colunas multi-level
    df_eventos_pivot.columns = [f"{stat}_{evento}" for stat, evento in df_eventos_pivot.columns]
    df_eventos_pivot = df_eventos_pivot.reset_index()
    
    # Transformação 2: Merge dos DataFrames
    df_final = df_produtos.merge(df_estoque, on='produto_id', how='left')
    df_final = df_final.merge(df_eventos_pivot, on='produto_id', how='left')
    
    # Preenche valores NaN
    evento_cols = [col for col in df_final.columns if 'qtd_eventos_' in col or 'usuarios_unicos_' in col]
    df_final[evento_cols] = df_final[evento_cols].fillna(0)
    
    # Transformação 3: Cálculos e métricas derivadas
    df_final['estoque_total'] = df_final['quantidade_disponivel'] + df_final['quantidade_reservada']
    df_final['situacao_estoque'] = pd.cut(
        df_final['estoque_total'] / df_final['estoque_minimo'].replace(0, 1),
        bins=[0, 0.5, 1.0, 2.0, float('inf')],
        labels=['Crítico', 'Baixo', 'Normal', 'Alto']
    )
    
    # Calcula score de popularidade
    visualizacoes = df_final.get('qtd_eventos_visualizacao', pd.Series(0, index=df_final.index))
    compras = df_final.get('qtd_eventos_compra', pd.Series(0, index=df_final.index))
    
    df_final['score_popularidade'] = (
        visualizacoes * 0.1 + 
        compras * 1.0
    ).fillna(0)
    
    # Transformação 4: Categorização por performance
    df_final['faixa_preco'] = pd.cut(
        df_final['preco'],
        bins=[0, 50, 200, 500, float('inf')],
        labels=['Barato', 'Médio', 'Caro', 'Premium']
    )
    
    # Calcula percentis de popularidade por categoria
    df_final['percentil_popularidade'] = df_final.groupby('categoria')['score_popularidade'].rank(pct=True)
    
    df_final['classificacao_produto'] = pd.cut(
        df_final['percentil_popularidade'],
        bins=[0, 0.25, 0.50, 0.75, 1.0],
        labels=['D', 'C', 'B', 'A']
    )
    
    # Transformação 5: Análise temporal
    df_final['data_criacao'] = pd.to_datetime(df_final['data_criacao'])
    df_final['dias_desde_criacao'] = (datetime.now() - df_final['data_criacao']).dt.days
    
    df_final['fase_produto'] = pd.cut(
        df_final['dias_desde_criacao'],
        bins=[0, 30, 90, 365, float('inf')],
        labels=['Novo', 'Recente', 'Estabelecido', 'Maduro']
    )
    
    # Transformação 6: Limpeza e formatação final
    df_final['data_processamento'] = datetime.now()
    df_final = df_final.round(2)  # Arredonda valores numéricos
    
    # Remove produtos inativos ou com dados inconsistentes
    df_final = df_final[
        (df_final['ativo'] == True) & 
        (df_final['preco'] > 0) &
        (df_final['estoque_total'] >= 0)
    ].copy()
    
    logging.info(f"Dados transformados: {len(df_final)} produtos processados")
    
    # Salva resultado
    context['task_instance'].xcom_push(key='df_final', value=df_final.to_json())
    
    return {
        'produtos_processados': len(df_final),
        'categorias_unicas': df_final['categoria'].nunique(),
        'score_medio_popularidade': float(df_final['score_popularidade'].mean())
    }

def carregar_dados_processados(**context):
    """
    Carrega dados transformados de volta ao PostgreSQL
    """
    ti = context['task_instance']
    df_final = pd.read_json(ti.xcom_pull(key='df_final'))
    
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    engine = pg_hook.get_sqlalchemy_engine()
    
    # Carregamento 1: Tabela principal de produtos processados (operação WRITE)
    # Limpa dados anteriores
    pg_hook.run("TRUNCATE TABLE staging.produtos_processados")
    
    # Insere dados processados usando to_sql
    df_final.to_sql(
        'produtos_processados',
        engine,
        schema='staging',
        if_exists='append',
        index=False,
        method='multi',
        chunksize=1000
    )
    
    logging.info(f"Carregados {len(df_final)} produtos na tabela staging.produtos_processados")
    
    # Carregamento 2: Métricas resumidas (operação WRITE)
    metricas_por_categoria = df_final.groupby('categoria').agg({
        'produto_id': 'count',
        'preco': ['mean', 'median', 'min', 'max'],
        'score_popularidade': ['mean', 'sum'],
        'estoque_total': 'sum'
    }).round(2)
    
    # Achata as colunas
    metricas_por_categoria.columns = [f"{col[1]}_{col[0]}" if col[1] else col[0] for col in metricas_por_categoria.columns]
    metricas_por_categoria = metricas_por_categoria.reset_index()
    metricas_por_categoria['data_calculo'] = datetime.now().date()
    
    # Carrega métricas
    metricas_por_categoria.to_sql(
        'metricas_categoria_temp',
        engine,
        if_exists='replace',
        index=False
    )
    
    # Move dados para tabela final usando SQL
    pg_hook.run("""
        INSERT INTO analytics.metrics (metrica_nome, valor, descricao, data_calculo, metadata)
        SELECT 
            CONCAT('produtos_categoria_', categoria) as metrica_nome,
            count_produto_id as valor,
            CONCAT('Métricas da categoria ', categoria) as descricao,
            data_calculo,
            json_build_object(
                'categoria', categoria,
                'total_produtos', count_produto_id,
                'preco_medio', mean_preco,
                'preco_mediano', median_preco,
                'score_popularidade_total', sum_score_popularidade,
                'estoque_total', sum_estoque_total
            ) as metadata
        FROM metricas_categoria_temp
        ON CONFLICT (metrica_nome, data_calculo) 
        DO UPDATE SET 
            valor = EXCLUDED.valor,
            descricao = EXCLUDED.descricao,
            metadata = EXCLUDED.metadata;
    """)
    
    # Remove tabela temporária
    pg_hook.run("DROP TABLE IF EXISTS metricas_categoria_temp")
    
    return {
        'produtos_carregados': len(df_final),
        'categorias_processadas': len(metricas_por_categoria)
    }

def gerar_relatorio_qualidade(**context):
    """
    Gera relatório de qualidade dos dados usando pandas
    """
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    engine = pg_hook.get_sqlalchemy_engine()
    
    # Extrai dados para análise de qualidade (operação READ)
    df_qualidade = pd.read_sql("""
        SELECT 
            categoria,
            COUNT(*) as total_produtos,
            COUNT(CASE WHEN preco > 0 THEN 1 END) as produtos_com_preco,
            COUNT(CASE WHEN estoque_total > 0 THEN 1 END) as produtos_com_estoque,
            COUNT(CASE WHEN score_popularidade > 0 THEN 1 END) as produtos_com_atividade,
            AVG(CASE WHEN preco > 0 THEN preco END) as preco_medio,
            MIN(data_processamento) as primeira_atualizacao,
            MAX(data_processamento) as ultima_atualizacao
        FROM staging.produtos_processados
        GROUP BY categoria
    """, engine)
    
    # Calcula métricas de qualidade
    df_qualidade['percentual_com_preco'] = (df_qualidade['produtos_com_preco'] / df_qualidade['total_produtos'] * 100).round(2)
    df_qualidade['percentual_com_estoque'] = (df_qualidade['produtos_com_estoque'] / df_qualidade['total_produtos'] * 100).round(2)
    df_qualidade['percentual_com_atividade'] = (df_qualidade['produtos_com_atividade'] / df_qualidade['total_produtos'] * 100).round(2)
    
    # Classifica qualidade por categoria
    df_qualidade['score_qualidade'] = (
        df_qualidade['percentual_com_preco'] * 0.4 +
        df_qualidade['percentual_com_estoque'] * 0.3 +
        df_qualidade['percentual_com_atividade'] * 0.3
    ).round(2)
    
    df_qualidade['classificacao_qualidade'] = pd.cut(
        df_qualidade['score_qualidade'],
        bins=[0, 60, 75, 90, 100],
        labels=['Ruim', 'Regular', 'Boa', 'Excelente']
    )
    
    # Salva relatório de qualidade (operação WRITE)
    df_qualidade['data_relatorio'] = datetime.now().date()
    
    # Limpa relatórios antigos e insere novo
    pg_hook.run("DELETE FROM analytics.metrics WHERE metrica_nome = 'relatorio_qualidade_produtos'")
    
    relatorio_json = df_qualidade.to_json(orient='records')
    
    insert_relatorio_sql = """
        INSERT INTO analytics.metrics (metrica_nome, valor, descricao, data_calculo, metadata)
        VALUES (
            'relatorio_qualidade_produtos',
            %s,
            'Relatório de qualidade dos dados de produtos',
            %s,
            %s
        )
    """
    
    pg_hook.run(insert_relatorio_sql, parameters=[
        len(df_qualidade),
        datetime.now().date(),
        relatorio_json
    ])
    
    # Log do relatório
    logging.info("=== RELATÓRIO DE QUALIDADE DOS DADOS ===")
    logging.info(f"\n{df_qualidade[['categoria', 'total_produtos', 'score_qualidade', 'classificacao_qualidade']].to_string()}")
    
    # Identifica categorias com problemas
    categorias_problema = df_qualidade[df_qualidade['score_qualidade'] < 75]
    if not categorias_problema.empty:
        logging.warning(f"Categorias com problemas de qualidade: {list(categorias_problema['categoria'])}")
    
    return {
        'categorias_analisadas': len(df_qualidade),
        'score_qualidade_medio': float(df_qualidade['score_qualidade'].mean()),
        'categorias_problema': len(categorias_problema)
    }

def analise_logs_performance(**context):
    """
    Analisa logs de performance do sistema usando pandas
    """
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    engine = pg_hook.get_sqlalchemy_engine()
    
    # Extrai logs das últimas 24 horas (operação READ)
    df_logs = pd.read_sql("""
        SELECT 
            timestamp_log,
            nivel,
            mensagem,
            duracao_ms,
            usuario_id,
            operacao
        FROM public.logs 
        WHERE timestamp_log >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
          AND operacao IN ('consulta_produto', 'atualizacao_estoque', 'calculo_metricas')
        ORDER BY timestamp_log DESC
    """, engine)
    
    if df_logs.empty:
        logging.info("Nenhum log encontrado para análise")
        return {'logs_analisados': 0}
    
    # Análise de performance por operação
    df_performance = df_logs.groupby('operacao').agg({
        'duracao_ms': ['count', 'mean', 'median', 'min', 'max', 'std'],
        'usuario_id': 'nunique'
    }).round(2)
    
    df_performance.columns = [f"{col[1]}_{col[0]}" for col in df_performance.columns]
    df_performance = df_performance.reset_index()
    
    # Identifica operações lentas
    df_performance['classificacao_performance'] = pd.cut(
        df_performance['mean_duracao_ms'],
        bins=[0, 100, 500, 2000, float('inf')],
        labels=['Rápida', 'Normal', 'Lenta', 'Crítica']
    )
    
    # Análise temporal (por hora)
    df_logs['hora'] = pd.to_datetime(df_logs['timestamp_log']).dt.hour
    df_temporal = df_logs.groupby('hora')['duracao_ms'].agg(['count', 'mean']).round(2)
    
    # Salva análise de performance
    analise_json = {
        'performance_por_operacao': df_performance.to_dict('records'),
        'performance_temporal': df_temporal.to_dict(),
        'total_logs_analisados': len(df_logs),
        'periodo_analise': '24 horas'
    }
    
    # Insere na tabela de métricas (operação WRITE)
    insert_performance_sql = """
        INSERT INTO analytics.metrics (metrica_nome, valor, descricao, data_calculo, metadata)
        VALUES (
            'analise_performance_sistema',
            %s,
            'Análise de performance do sistema baseada em logs',
            %s,
            %s
        )
        ON CONFLICT (metrica_nome, data_calculo) 
        DO UPDATE SET 
            valor = EXCLUDED.valor,
            metadata = EXCLUDED.metadata
    """
    
    pg_hook.run(insert_performance_sql, parameters=[
        len(df_logs),
        datetime.now().date(),
        pd.io.json.dumps(analise_json)
    ])
    
    logging.info(f"Análise de performance concluída: {len(df_logs)} logs analisados")
    
    return {
        'logs_analisados': len(df_logs),
        'operacoes_analisadas': len(df_performance),
        'duracao_media_geral': float(df_logs['duracao_ms'].mean())
    }

# Definição das tasks
task_extrair = PythonOperator(
    task_id='extrair_dados_produtos',
    python_callable=extrair_dados_produtos,
    dag=dag
)

task_transformar = PythonOperator(
    task_id='transformar_dados',
    python_callable=transformar_dados_produtos,
    dag=dag
)

task_carregar = PythonOperator(
    task_id='carregar_dados_processados',
    python_callable=carregar_dados_processados,
    dag=dag
)

task_qualidade = PythonOperator(
    task_id='gerar_relatorio_qualidade',
    python_callable=gerar_relatorio_qualidade,
    dag=dag
)

task_performance = PythonOperator(
    task_id='analisar_performance',
    python_callable=analise_logs_performance,
    dag=dag
)

# Dependências do pipeline ETL
task_extrair >> task_transformar >> task_carregar
task_carregar >> [task_qualidade, task_performance]
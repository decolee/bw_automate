#!/usr/bin/env python3
"""
DAG de Exemplo 2 - SQL Complexo
===============================

Este DAG demonstra operações SQL complexas, incluindo:
- CTEs (Common Table Expressions)
- Subqueries aninhadas
- Window functions
- SQL dinâmico com F-strings
- Operações de múltiplas tabelas

Tabelas envolvidas:
- Leitura: ecommerce.pedidos, ecommerce.produtos, ecommerce.usuarios, analytics.events
- Escrita: analytics.user_segments, analytics.metrics

Autor: BW_AUTOMATE Examples
Data: 2025-09-20
"""

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.hooks.postgres_hook import PostgresHook
from datetime import datetime, timedelta
import pandas as pd
import logging

default_args = {
    'owner': 'time_analytics',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10)
}

dag = DAG(
    'analytics_complexo_ecommerce',
    default_args=default_args,
    description='Análise complexa de dados de e-commerce',
    schedule_interval='0 2 * * *',  # 2h da manhã todo dia
    catchup=False,
    tags=['analytics', 'ecommerce', 'complex', 'ml']
)

def calcular_rfm_avancado(**context):
    """
    Calcula RFM (Recency, Frequency, Monetary) com análise avançada
    Usa CTEs e window functions
    """
    execution_date = context['execution_date'].strftime('%Y-%m-%d')
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # SQL complexo com CTEs e window functions
    rfm_sql = f"""
    WITH base_pedidos AS (
        -- CTE 1: Dados base de pedidos com detalhes
        SELECT 
            p.usuario_id,
            p.data_pedido,
            p.valor_total,
            p.status,
            u.data_cadastro,
            u.categoria_cliente,
            DATE('{execution_date}') as data_analise,
            ROW_NUMBER() OVER (PARTITION BY p.usuario_id ORDER BY p.data_pedido DESC) as recencia_rank
        FROM ecommerce.pedidos p
        INNER JOIN ecommerce.usuarios u ON p.usuario_id = u.id
        WHERE p.data_pedido >= DATE('{execution_date}') - INTERVAL '365 days'
          AND p.status IN ('concluido', 'entregue')
    ),
    
    metricas_usuario AS (
        -- CTE 2: Cálculos de RFM por usuário
        SELECT 
            usuario_id,
            categoria_cliente,
            -- Recency: dias desde último pedido
            DATE('{execution_date}') - MAX(data_pedido) as dias_ultimo_pedido,
            
            -- Frequency: número de pedidos
            COUNT(*) as total_pedidos,
            
            -- Monetary: valor total gasto
            SUM(valor_total) as valor_total_gasto,
            AVG(valor_total) as ticket_medio,
            
            -- Métricas extras
            MAX(data_pedido) as data_ultimo_pedido,
            MIN(data_pedido) as data_primeiro_pedido,
            EXTRACT(DAYS FROM MAX(data_pedido) - MIN(data_pedido)) as dias_como_cliente
            
        FROM base_pedidos
        GROUP BY usuario_id, categoria_cliente
        HAVING COUNT(*) >= 1  -- Pelo menos 1 pedido
    ),
    
    quartis_rfm AS (
        -- CTE 3: Cálculo de quartis para segmentação
        SELECT 
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY dias_ultimo_pedido) as r_q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY dias_ultimo_pedido) as r_q2,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY dias_ultimo_pedido) as r_q3,
            
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_pedidos) as f_q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_pedidos) as f_q2,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_pedidos) as f_q3,
            
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_total_gasto) as m_q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY valor_total_gasto) as m_q2,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_total_gasto) as m_q3
        FROM metricas_usuario
    ),
    
    rfm_scores AS (
        -- CTE 4: Atribuição de scores RFM
        SELECT 
            m.*,
            -- Score Recency (invertido: menor dias = maior score)
            CASE 
                WHEN dias_ultimo_pedido <= q.r_q1 THEN 4
                WHEN dias_ultimo_pedido <= q.r_q2 THEN 3
                WHEN dias_ultimo_pedido <= q.r_q3 THEN 2
                ELSE 1
            END as r_score,
            
            -- Score Frequency
            CASE 
                WHEN total_pedidos >= q.f_q3 THEN 4
                WHEN total_pedidos >= q.f_q2 THEN 3
                WHEN total_pedidos >= q.f_q1 THEN 2
                ELSE 1
            END as f_score,
            
            -- Score Monetary
            CASE 
                WHEN valor_total_gasto >= q.m_q3 THEN 4
                WHEN valor_total_gasto >= q.m_q2 THEN 3
                WHEN valor_total_gasto >= q.m_q1 THEN 2
                ELSE 1
            END as m_score
            
        FROM metricas_usuario m
        CROSS JOIN quartis_rfm q
    )
    
    -- Query final com segmentação
    SELECT 
        usuario_id,
        categoria_cliente,
        dias_ultimo_pedido,
        total_pedidos,
        valor_total_gasto,
        ticket_medio,
        r_score,
        f_score,
        m_score,
        CONCAT(r_score, f_score, m_score) as rfm_segment,
        
        -- Classificação do segmento
        CASE 
            WHEN CONCAT(r_score, f_score, m_score) IN ('444', '443', '434', '344') THEN 'Champions'
            WHEN CONCAT(r_score, f_score, m_score) IN ('442', '441', '432', '431', '342', '341') THEN 'Loyal Customers'
            WHEN CONCAT(r_score, f_score, m_score) IN ('422', '421', '412', '411', '322', '321') THEN 'Potential Loyalists'
            WHEN CONCAT(r_score, f_score, m_score) IN ('433', '423', '413', '414', '424', '343', '333', '323') THEN 'New Customers'
            WHEN CONCAT(r_score, f_score, m_score) IN ('331', '312', '231', '212', '213', '232') THEN 'Promising'
            WHEN CONCAT(r_score, f_score, m_score) IN ('241', '142', '143', '242', '124', '132') THEN 'Need Attention'
            WHEN CONCAT(r_score, f_score, m_score) IN ('141', '131', '121', '113', '123', '114') THEN 'About to Sleep'
            WHEN CONCAT(r_score, f_score, m_score) IN ('222', '122', '221', '223', '133', '233') THEN 'At Risk'
            WHEN CONCAT(r_score, f_score, m_score) IN ('111', '112', '211', '311') THEN 'Lost'
            ELSE 'Others'
        END as segmento_final,
        
        DATE('{execution_date}') as data_analise,
        CURRENT_TIMESTAMP as data_processamento
        
    FROM rfm_scores
    ORDER BY r_score DESC, f_score DESC, m_score DESC;
    """
    
    # Executa análise RFM
    df_rfm = pg_hook.get_pandas_df(rfm_sql)
    logging.info(f"Análise RFM calculada para {len(df_rfm)} usuários")
    
    # Limpa dados anteriores e insere novos (operação DELETE + INSERT)
    delete_sql = f"DELETE FROM analytics.user_segments WHERE data_analise = '{execution_date}'"
    pg_hook.run(delete_sql)
    
    # Insere resultados na tabela de segmentos
    if not df_rfm.empty:
        # Usa pandas to_sql para insert bulk
        engine = pg_hook.get_sqlalchemy_engine()
        df_rfm.to_sql('user_segments', engine, schema='analytics', if_exists='append', index=False)
        
    logging.info(f"Segmentação RFM gravada: {len(df_rfm)} registros")
    
    return len(df_rfm)

def analise_comportamento_produtos(**context):
    """
    Análise complexa de comportamento de produtos
    SQL dinâmico baseado em parâmetros
    """
    execution_date = context['execution_date']
    dias_analise = context['dag_run'].conf.get('dias_analise', 30) if context['dag_run'].conf else 30
    
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # SQL dinâmico com f-strings
    data_inicio = (execution_date - timedelta(days=dias_analise)).strftime('%Y-%m-%d')
    data_fim = execution_date.strftime('%Y-%m-%d')
    
    analise_sql = f"""
    WITH eventos_produtos AS (
        -- Eventos relacionados a produtos
        SELECT 
            e.usuario_id,
            e.produto_id,
            e.evento_tipo,
            e.timestamp_evento,
            p.nome as produto_nome,
            p.categoria as produto_categoria,
            p.preco,
            LAG(e.timestamp_evento) OVER (
                PARTITION BY e.usuario_id, e.produto_id 
                ORDER BY e.timestamp_evento
            ) as evento_anterior
        FROM analytics.events e
        INNER JOIN ecommerce.produtos p ON e.produto_id = p.id
        WHERE e.timestamp_evento BETWEEN '{data_inicio}' AND '{data_fim}'
          AND e.evento_tipo IN ('visualizacao', 'adicionar_carrinho', 'compra', 'remover_carrinho')
    ),
    
    funil_conversao AS (
        -- Análise do funil de conversão por produto
        SELECT 
            produto_id,
            produto_nome,
            produto_categoria,
            preco,
            
            -- Métricas do funil
            COUNT(CASE WHEN evento_tipo = 'visualizacao' THEN 1 END) as visualizacoes,
            COUNT(CASE WHEN evento_tipo = 'adicionar_carrinho' THEN 1 END) as adicoes_carrinho,
            COUNT(CASE WHEN evento_tipo = 'compra' THEN 1 END) as compras,
            COUNT(CASE WHEN evento_tipo = 'remover_carrinho' THEN 1 END) as remocoes_carrinho,
            
            -- Usuários únicos por etapa
            COUNT(DISTINCT CASE WHEN evento_tipo = 'visualizacao' THEN usuario_id END) as usuarios_visualizaram,
            COUNT(DISTINCT CASE WHEN evento_tipo = 'adicionar_carrinho' THEN usuario_id END) as usuarios_adicionaram,
            COUNT(DISTINCT CASE WHEN evento_tipo = 'compra' THEN usuario_id END) as usuarios_compraram,
            
            -- Tempo médio entre eventos
            AVG(
                CASE WHEN evento_anterior IS NOT NULL 
                THEN EXTRACT(EPOCH FROM timestamp_evento - evento_anterior) / 60.0 
                END
            ) as tempo_medio_entre_eventos_min
            
        FROM eventos_produtos
        GROUP BY produto_id, produto_nome, produto_categoria, preco
        HAVING COUNT(CASE WHEN evento_tipo = 'visualizacao' THEN 1 END) >= 10  -- Mínimo de visualizações
    ),
    
    metricas_calculadas AS (
        -- Cálculo de métricas de performance
        SELECT 
            *,
            -- Taxa de conversão: carrinho -> compra
            CASE 
                WHEN usuarios_adicionaram > 0 
                THEN ROUND((usuarios_compraram::numeric / usuarios_adicionaram * 100), 2)
                ELSE 0 
            END as taxa_conversao_carrinho_compra,
            
            -- Taxa de conversão: visualização -> carrinho
            CASE 
                WHEN usuarios_visualizaram > 0 
                THEN ROUND((usuarios_adicionaram::numeric / usuarios_visualizaram * 100), 2)
                ELSE 0 
            END as taxa_conversao_view_carrinho,
            
            -- Taxa de conversão geral: visualização -> compra
            CASE 
                WHEN usuarios_visualizaram > 0 
                THEN ROUND((usuarios_compraram::numeric / usuarios_visualizaram * 100), 2)
                ELSE 0 
            END as taxa_conversao_geral,
            
            -- Taxa de abandono do carrinho
            CASE 
                WHEN adicoes_carrinho > 0 
                THEN ROUND((remocoes_carrinho::numeric / adicoes_carrinho * 100), 2)
                ELSE 0 
            END as taxa_abandono_carrinho,
            
            -- Receita estimada
            usuarios_compraram * preco as receita_estimada
            
        FROM funil_conversao
    )
    
    SELECT 
        produto_id,
        produto_nome,
        produto_categoria,
        preco,
        visualizacoes,
        adicoes_carrinho,
        compras,
        usuarios_visualizaram,
        usuarios_adicionaram,
        usuarios_compraram,
        taxa_conversao_geral,
        taxa_conversao_view_carrinho,
        taxa_conversao_carrinho_compra,
        taxa_abandono_carrinho,
        receita_estimada,
        tempo_medio_entre_eventos_min,
        
        -- Classificação do produto
        CASE 
            WHEN taxa_conversao_geral >= 10 AND receita_estimada >= 1000 THEN 'High Performer'
            WHEN taxa_conversao_geral >= 5 AND receita_estimada >= 500 THEN 'Good Performer'
            WHEN taxa_conversao_geral >= 2 AND receita_estimada >= 100 THEN 'Average Performer'
            WHEN taxa_conversao_geral >= 1 THEN 'Low Performer'
            ELSE 'Poor Performer'
        END as classificacao_performance,
        
        '{data_inicio}'::date as periodo_inicio,
        '{data_fim}'::date as periodo_fim,
        CURRENT_TIMESTAMP as data_processamento
        
    FROM metricas_calculadas
    ORDER BY receita_estimada DESC, taxa_conversao_geral DESC;
    """
    
    # Executa análise
    df_produtos = pg_hook.get_pandas_df(analise_sql)
    logging.info(f"Análise de produtos calculada: {len(df_produtos)} produtos analisados")
    
    # Salva métricas na tabela analytics.metrics
    if not df_produtos.empty:
        # Prepara dados para inserção
        metricas_resumo = {
            'metrica_nome': f'analise_produtos_{dias_analise}d',
            'valor': len(df_produtos),
            'descricao': f'Análise de comportamento de {len(df_produtos)} produtos em {dias_analise} dias',
            'data_calculo': execution_date.date(),
            'metadata': df_produtos.to_json()
        }
        
        # Insere na tabela de métricas (operação INSERT)
        insert_sql = """
        INSERT INTO analytics.metrics (metrica_nome, valor, descricao, data_calculo, metadata)
        VALUES (%(metrica_nome)s, %(valor)s, %(descricao)s, %(data_calculo)s, %(metadata)s)
        ON CONFLICT (metrica_nome, data_calculo) 
        DO UPDATE SET 
            valor = EXCLUDED.valor,
            descricao = EXCLUDED.descricao,
            metadata = EXCLUDED.metadata;
        """
        
        pg_hook.run(insert_sql, parameters=metricas_resumo)
    
    return f"Análise concluída: {len(df_produtos)} produtos"

# Task usando PostgresOperator com SQL complexo direto
task_limpar_dados_antigos = PostgresOperator(
    task_id='limpar_dados_antigos',
    postgres_conn_id='postgres_default',
    sql="""
    -- Limpa dados antigos das tabelas de analytics (operação DELETE)
    DELETE FROM analytics.user_segments 
    WHERE data_analise < CURRENT_DATE - INTERVAL '90 days';
    
    DELETE FROM analytics.metrics 
    WHERE data_calculo < CURRENT_DATE - INTERVAL '180 days'
      AND metrica_nome LIKE 'analise_produtos_%';
    
    -- Atualiza estatísticas das tabelas (operação ANALYZE)
    ANALYZE analytics.user_segments;
    ANALYZE analytics.metrics;
    """,
    dag=dag
)

task_rfm = PythonOperator(
    task_id='calcular_rfm_avancado',
    python_callable=calcular_rfm_avancado,
    dag=dag
)

task_produtos = PythonOperator(
    task_id='analisar_produtos',
    python_callable=analise_comportamento_produtos,
    dag=dag
)

# Task final com agregação complexa
task_resumo_final = PostgresOperator(
    task_id='gerar_resumo_final',
    postgres_conn_id='postgres_default',
    sql="""
    -- Gera resumo final combinando múltiplas análises (múltiplas operações READ)
    WITH resumo_segmentos AS (
        SELECT 
            segmento_final,
            COUNT(*) as qtd_usuarios,
            AVG(valor_total_gasto) as valor_medio_gasto,
            AVG(total_pedidos) as pedidos_medio
        FROM analytics.user_segments 
        WHERE data_analise = CURRENT_DATE
        GROUP BY segmento_final
    ),
    resumo_metricas AS (
        SELECT 
            COUNT(*) as total_metricas,
            AVG(valor) as valor_medio_metricas
        FROM analytics.metrics 
        WHERE data_calculo = CURRENT_DATE
    )
    
    -- Insere resumo consolidado (operação INSERT)
    INSERT INTO analytics.metrics (metrica_nome, valor, descricao, data_calculo, metadata)
    SELECT 
        'resumo_analytics_diario' as metrica_nome,
        s.qtd_usuarios as valor,
        'Resumo diário das análises de analytics' as descricao,
        CURRENT_DATE as data_calculo,
        json_build_object(
            'segmentos', json_agg(s.*),
            'metricas_processadas', m.total_metricas,
            'valor_medio_metricas', m.valor_medio_metricas
        ) as metadata
    FROM resumo_segmentos s
    CROSS JOIN resumo_metricas m
    GROUP BY m.total_metricas, m.valor_medio_metricas
    ON CONFLICT (metrica_nome, data_calculo) 
    DO UPDATE SET 
        valor = EXCLUDED.valor,
        descricao = EXCLUDED.descricao,
        metadata = EXCLUDED.metadata;
    """,
    dag=dag
)

# Dependências
task_limpar_dados_antigos >> [task_rfm, task_produtos]
[task_rfm, task_produtos] >> task_resumo_final
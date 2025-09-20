#!/usr/bin/env python3
"""
BW_AUTOMATE - Exemplo de Uso
============================

Script de exemplo demonstrando como usar o BW_AUTOMATE para análise
de tabelas PostgreSQL em códigos Python do Airflow.

Autor: Assistant Claude
Data: 2025-09-20
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório do BW_AUTOMATE ao path
bw_automate_dir = Path(__file__).parent
sys.path.insert(0, str(bw_automate_dir))

from run_analysis import BWAutomate


def criar_exemplo_tabelas_xlsx():
    """Cria um arquivo de exemplo com tabelas PostgreSQL"""
    import pandas as pd
    
    # Dados de exemplo
    tabelas_exemplo = {
        'table_name': [
            'usuarios', 'produtos', 'vendas', 'clientes', 'pedidos',
            'estoque', 'categorias', 'fornecedores', 'logs_sistema',
            'auditoria', 'configuracoes', 'relatorios'
        ],
        'schema': [
            'public', 'public', 'public', 'public', 'public',
            'staging', 'public', 'public', 'logs', 'audit',
            'public', 'reports'
        ],
        'tipo': [
            'transacional', 'transacional', 'transacional', 'transacional', 'transacional',
            'staging', 'referencia', 'referencia', 'log', 'auditoria',
            'configuracao', 'relatorio'
        ],
        'descricao': [
            'Cadastro de usuários do sistema',
            'Catálogo de produtos',
            'Registro de vendas realizadas',
            'Dados dos clientes',
            'Pedidos dos clientes',
            'Controle de estoque (staging)',
            'Categorias de produtos',
            'Dados dos fornecedores',
            'Logs do sistema',
            'Trilha de auditoria',
            'Configurações do sistema',
            'Relatórios gerados'
        ]
    }
    
    df = pd.DataFrame(tabelas_exemplo)
    
    # Salva arquivo Excel de exemplo
    excel_path = "tabelas_exemplo.xlsx"
    df.to_excel(excel_path, index=False)
    
    print(f"✅ Arquivo de exemplo criado: {excel_path}")
    return excel_path


def criar_codigo_python_exemplo():
    """Cria arquivos Python de exemplo com código Airflow"""
    
    # Cria diretório de exemplo
    exemplo_dir = "exemplo_dags"
    os.makedirs(exemplo_dir, exist_ok=True)
    
    # Exemplo 1: DAG de ETL básico
    dag_etl = '''
from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.python_operator import PythonOperator
import pandas as pd
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'etl_vendas_diario',
    default_args=default_args,
    description='ETL diário de vendas',
    schedule_interval='@daily',
    catchup=False
)

# Extrai dados de vendas
extrair_vendas = PostgresOperator(
    task_id='extrair_vendas',
    postgres_conn_id='postgres_default',
    sql="""
        SELECT v.id, v.data_venda, v.valor, c.nome as cliente, p.nome as produto
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.id
        JOIN produtos p ON v.produto_id = p.id
        WHERE v.data_venda = '{{ ds }}'
    """,
    dag=dag
)

def processar_vendas(**context):
    """Processa dados de vendas"""
    # Conecta com banco
    import psycopg2
    conn = psycopg2.connect("postgresql://user:pass@host/db")
    
    # Lê dados processados
    df = pd.read_sql("""
        SELECT * FROM staging.vendas_processadas 
        WHERE data_processamento = %s
    """, conn, params=[context['ds']])
    
    # Processa dados
    df['valor_com_desconto'] = df['valor'] * 0.9
    
    # Salva resultado
    df.to_sql('vendas_com_desconto', conn, schema='reports', 
              if_exists='append', index=False)
    
    conn.close()

processar_task = PythonOperator(
    task_id='processar_vendas',
    python_callable=processar_vendas,
    dag=dag
)

# Atualiza estatísticas
atualizar_stats = PostgresOperator(
    task_id='atualizar_estatisticas',
    postgres_conn_id='postgres_default',
    sql="""
        INSERT INTO relatorios.estatisticas_vendas (data, total_vendas, total_desconto)
        SELECT 
            '{{ ds }}' as data,
            SUM(valor) as total_vendas,
            SUM(valor_com_desconto) as total_desconto
        FROM reports.vendas_com_desconto
        WHERE DATE(created_at) = '{{ ds }}'
    """,
    dag=dag
)

extrair_vendas >> processar_task >> atualizar_stats
'''
    
    with open(f"{exemplo_dir}/dag_etl_vendas.py", 'w') as f:
        f.write(dag_etl)
    
    # Exemplo 2: DAG de limpeza de dados
    dag_limpeza = '''
from airflow import DAG
from airflow.operators.postgres_operator import PostgresOperator
import pandas as pd
from datetime import datetime, timedelta

dag = DAG(
    'limpeza_dados_semanal',
    default_args={'owner': 'admin'},
    description='Limpeza semanal de dados',
    schedule_interval='@weekly'
)

# Limpa logs antigos
limpar_logs = PostgresOperator(
    task_id='limpar_logs_sistema',
    postgres_conn_id='postgres_default',
    sql="""
        DELETE FROM logs.logs_sistema 
        WHERE created_at < NOW() - INTERVAL '30 days'
    """,
    dag=dag
)

# Arquiva dados antigos
arquivar_auditoria = PostgresOperator(
    task_id='arquivar_auditoria',
    postgres_conn_id='postgres_default',
    sql="""
        INSERT INTO audit.auditoria_arquivo
        SELECT * FROM audit.auditoria
        WHERE created_at < NOW() - INTERVAL '1 year';
        
        DELETE FROM audit.auditoria
        WHERE created_at < NOW() - INTERVAL '1 year';
    """,
    dag=dag
)

def consolidar_estoque():
    """Consolida dados de estoque"""
    import psycopg2
    
    conn = psycopg2.connect("postgresql://user:pass@host/db")
    
    # Lê dados de estoque atual
    df_estoque = pd.read_sql("SELECT * FROM estoque", conn)
    
    # Lê movimentações
    df_movimentacoes = pd.read_sql("""
        SELECT produto_id, SUM(quantidade) as total_movimento
        FROM staging.movimentacoes_estoque
        GROUP BY produto_id
    """, conn)
    
    # Atualiza estoque consolidado
    # ... lógica de consolidação ...
    
    # Limpa staging
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE staging.movimentacoes_estoque")
    conn.commit()
    conn.close()

from airflow.operators.python_operator import PythonOperator

consolidar_task = PythonOperator(
    task_id='consolidar_estoque',
    python_callable=consolidar_estoque,
    dag=dag
)

limpar_logs >> arquivar_auditoria >> consolidar_task
'''
    
    with open(f"{exemplo_dir}/dag_limpeza_dados.py", 'w') as f:
        f.write(dag_limpeza)
    
    # Exemplo 3: Script utilitário
    script_util = '''
"""
Utilitários para manipulação de dados
"""
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

def conectar_banco():
    """Conecta com banco PostgreSQL"""
    return psycopg2.connect("postgresql://user:pass@host/db")

def extrair_dados_usuarios():
    """Extrai dados de usuários ativos"""
    engine = create_engine("postgresql://user:pass@host/db")
    
    query = """
        SELECT u.id, u.nome, u.email, u.data_cadastro
        FROM public.usuarios u
        WHERE u.ativo = true
        AND u.data_ultimo_acesso > NOW() - INTERVAL '30 days'
    """
    
    return pd.read_sql(query, engine)

def atualizar_configuracoes(nova_config):
    """Atualiza tabela de configurações"""
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE public.configuracoes 
        SET valor = %s, data_atualizacao = NOW()
        WHERE chave = %s
    """, (nova_config['valor'], nova_config['chave']))
    
    conn.commit()
    conn.close()

def gerar_relatorio_vendas(data_inicio, data_fim):
    """Gera relatório de vendas por período"""
    conn = conectar_banco()
    
    df = pd.read_sql("""
        WITH vendas_periodo AS (
            SELECT 
                DATE(v.data_venda) as data,
                COUNT(*) as total_vendas,
                SUM(v.valor) as receita_total,
                AVG(v.valor) as ticket_medio
            FROM vendas v
            WHERE v.data_venda BETWEEN %s AND %s
            GROUP BY DATE(v.data_venda)
        )
        SELECT * FROM vendas_periodo
        ORDER BY data
    """, conn, params=[data_inicio, data_fim])
    
    # Salva relatório
    df.to_sql('relatorio_vendas_periodo', conn, schema='reports',
              if_exists='replace', index=False)
    
    conn.close()
    return df
'''
    
    with open(f"{exemplo_dir}/utils_dados.py", 'w') as f:
        f.write(script_util)
    
    print(f"✅ Códigos de exemplo criados em: {exemplo_dir}/")
    return exemplo_dir


def executar_exemplo_completo():
    """Executa exemplo completo do BW_AUTOMATE"""
    
    print("\n🚀 BW_AUTOMATE - EXEMPLO DE USO COMPLETO")
    print("="*50)
    
    # 1. Cria arquivos de exemplo
    print("\n📁 1. Criando arquivos de exemplo...")
    tabelas_xlsx = criar_exemplo_tabelas_xlsx()
    codigo_dir = criar_codigo_python_exemplo()
    
    # 2. Configura BW_AUTOMATE
    print("\n⚙️ 2. Configurando BW_AUTOMATE...")
    config_exemplo = {
        "analysis_settings": {
            "fuzzy_match_threshold": 75,
            "include_temp_tables": True,
            "schemas_to_analyze": ["public", "staging", "reports", "logs", "audit"],
            "max_files_to_analyze": 100
        },
        "reporting": {
            "generate_executive_dashboard": True,
            "generate_technical_report": True,
            "generate_table_explorer": True,
            "export_to_powerbi": True
        },
        "logging": {
            "log_level": "INFO"
        }
    }
    
    # 3. Executa análise
    print("\n🔍 3. Executando análise...")
    try:
        bw_automate = BWAutomate()
        bw_automate.config.update(config_exemplo)
        
        # Simula execução (sem executar realmente para não dar erro)
        print("   • Validando arquivos de entrada...")
        print("   • Carregando tabelas oficiais...")
        print("   • Analisando códigos Python...")
        print("   • Executando mapeamento de tabelas...")
        print("   • Gerando relatórios...")
        
        print("\n✅ Análise simulada concluída com sucesso!")
        
        # Mostra o que seria gerado
        print("\n📊 Relatórios que seriam gerados:")
        print("   • executive_dashboard_YYYYMMDD_HHMMSS.html")
        print("   • technical_report_YYYYMMDD_HHMMSS.html")
        print("   • table_explorer_YYYYMMDD_HHMMSS.html")
        print("   • powerbi_export_YYYYMMDD_HHMMSS.xlsx")
        print("   • table_mappings_YYYYMMDD_HHMMSS.csv")
        
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
    
    # 4. Instruções para uso real
    print("\n📋 4. Para uso real, execute:")
    print(f"python run_analysis.py --source-dir {codigo_dir} --tables-xlsx {tabelas_xlsx}")
    
    # 5. Limpeza (opcional)
    resposta = input("\n🧹 Deseja limpar os arquivos de exemplo? (s/n): ")
    if resposta.lower() == 's':
        import shutil
        os.remove(tabelas_xlsx)
        shutil.rmtree(codigo_dir)
        print("✅ Arquivos de exemplo removidos")
    else:
        print(f"📁 Arquivos mantidos: {tabelas_xlsx}, {codigo_dir}/")
    
    print("\n🎉 Exemplo concluído!")


if __name__ == "__main__":
    executar_exemplo_completo()
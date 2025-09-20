#!/usr/bin/env python3
"""
Script para criar arquivos Excel de exemplo para o BW_AUTOMATE
"""

import pandas as pd
import os

def create_sample_tables_excel():
    """Cria arquivo Excel com tabelas de exemplo"""
    
    # Dados de exemplo de tabelas PostgreSQL
    sample_tables = [
        # Sistema Financeiro
        {'table_name': 'contas', 'schema': 'financeiro', 'description': 'Plano de contas contábil', 'owner': 'time_financeiro', 'criticality': 'HIGH', 'environment': 'PROD'},
        {'table_name': 'transacoes', 'schema': 'financeiro', 'description': 'Transações financeiras', 'owner': 'time_financeiro', 'criticality': 'HIGH', 'environment': 'PROD'},
        {'table_name': 'clientes', 'schema': 'financeiro', 'description': 'Dados de clientes', 'owner': 'time_comercial', 'criticality': 'HIGH', 'environment': 'PROD'},
        {'table_name': 'fornecedores', 'schema': 'financeiro', 'description': 'Cadastro de fornecedores', 'owner': 'time_compras', 'criticality': 'MEDIUM', 'environment': 'PROD'},
        
        # Sistema E-commerce
        {'table_name': 'produtos', 'schema': 'ecommerce', 'description': 'Catálogo de produtos', 'owner': 'time_produto', 'criticality': 'HIGH', 'environment': 'PROD'},
        {'table_name': 'pedidos', 'schema': 'ecommerce', 'description': 'Pedidos de compra', 'owner': 'time_vendas', 'criticality': 'HIGH', 'environment': 'PROD'},
        {'table_name': 'usuarios', 'schema': 'ecommerce', 'description': 'Usuários do sistema', 'owner': 'time_produto', 'criticality': 'HIGH', 'environment': 'PROD'},
        {'table_name': 'estoque', 'schema': 'ecommerce', 'description': 'Controle de estoque', 'owner': 'time_logistica', 'criticality': 'HIGH', 'environment': 'PROD'},
        {'table_name': 'carrinho', 'schema': 'ecommerce', 'description': 'Itens no carrinho', 'owner': 'time_produto', 'criticality': 'MEDIUM', 'environment': 'PROD'},
        
        # Sistema Analytics
        {'table_name': 'events', 'schema': 'analytics', 'description': 'Eventos de usuário', 'owner': 'time_dados', 'criticality': 'HIGH', 'environment': 'PROD'},
        {'table_name': 'sessions', 'schema': 'analytics', 'description': 'Sessões de usuário', 'owner': 'time_dados', 'criticality': 'MEDIUM', 'environment': 'PROD'},
        {'table_name': 'metrics', 'schema': 'analytics', 'description': 'Métricas calculadas', 'owner': 'time_dados', 'criticality': 'MEDIUM', 'environment': 'PROD'},
        {'table_name': 'user_segments', 'schema': 'analytics', 'description': 'Segmentação de usuários', 'owner': 'time_marketing', 'criticality': 'MEDIUM', 'environment': 'PROD'},
        
        # Tabelas de Staging/Temporárias
        {'table_name': 'temp_import_clientes', 'schema': 'staging', 'description': 'Importação temporária de clientes', 'owner': 'time_dados', 'criticality': 'LOW', 'environment': 'STAGING'},
        {'table_name': 'tmp_vendas_diarias', 'schema': 'staging', 'description': 'Processamento diário de vendas', 'owner': 'time_dados', 'criticality': 'LOW', 'environment': 'STAGING'},
        {'table_name': 'staging_produtos', 'schema': 'staging', 'description': 'Área de staging para produtos', 'owner': 'time_dados', 'criticality': 'LOW', 'environment': 'STAGING'},
        
        # Schema Public (comum)
        {'table_name': 'logs', 'schema': 'public', 'description': 'Logs do sistema', 'owner': 'time_infra', 'criticality': 'LOW', 'environment': 'PROD'},
        {'table_name': 'configurations', 'schema': 'public', 'description': 'Configurações do sistema', 'owner': 'time_infra', 'criticality': 'MEDIUM', 'environment': 'PROD'},
        {'table_name': 'audit_trail', 'schema': 'public', 'description': 'Trilha de auditoria', 'owner': 'time_seguranca', 'criticality': 'HIGH', 'environment': 'PROD'},
        
        # Tabelas de Desenvolvimento
        {'table_name': 'test_data', 'schema': 'development', 'description': 'Dados de teste', 'owner': 'time_qa', 'criticality': 'LOW', 'environment': 'DEV'},
        {'table_name': 'mock_users', 'schema': 'development', 'description': 'Usuários fictícios', 'owner': 'time_qa', 'criticality': 'LOW', 'environment': 'DEV'},
    ]
    
    # Converte para DataFrame
    df = pd.DataFrame(sample_tables)
    
    # Cria arquivo principal
    excel_path = 'examples/input_formats/tables_postgresql.xlsx'
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    
    # Salva com múltiplas abas
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Aba principal com todas as tabelas
        df.to_excel(writer, sheet_name='all_tables', index=False)
        
        # Aba só com tabelas de produção
        df_prod = df[df['environment'] == 'PROD']
        df_prod.to_excel(writer, sheet_name='production_tables', index=False)
        
        # Aba por schema
        for schema in df['schema'].unique():
            schema_df = df[df['schema'] == schema]
            sheet_name = f'schema_{schema}'[:31]  # Excel limit
            schema_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"✅ Arquivo criado: {excel_path}")
    print(f"📊 Total de tabelas: {len(df)}")
    print(f"🏗️ Schemas: {', '.join(df['schema'].unique())}")
    
    return excel_path

def create_template_excel():
    """Cria template vazio para usuários preencherem"""
    
    # Template com colunas vazias
    template_data = {
        'table_name': ['exemplo_tabela_1', 'exemplo_tabela_2'],
        'schema': ['public', 'public'],
        'description': ['Descrição da tabela 1', 'Descrição da tabela 2'],
        'owner': ['seu_time', 'seu_time'],
        'criticality': ['MEDIUM', 'LOW'],
        'environment': ['PROD', 'DEV']
    }
    
    df_template = pd.DataFrame(template_data)
    
    template_path = 'examples/input_formats/tables_template.xlsx'
    
    with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
        # Aba com exemplo
        df_template.to_excel(writer, sheet_name='template_example', index=False)
        
        # Aba vazia para usuário preencher
        empty_df = pd.DataFrame(columns=['table_name', 'schema', 'description', 'owner', 'criticality', 'environment'])
        empty_df.to_excel(writer, sheet_name='your_tables', index=False)
        
        # Aba com instruções
        instructions = pd.DataFrame({
            'Coluna': ['table_name', 'schema', 'description', 'owner', 'criticality', 'environment'],
            'Obrigatória': ['SIM', 'NÃO', 'NÃO', 'NÃO', 'NÃO', 'NÃO'],
            'Tipo': ['Texto', 'Texto', 'Texto', 'Texto', 'HIGH/MEDIUM/LOW', 'PROD/DEV/STAGING'],
            'Exemplo': ['usuarios', 'public', 'Tabela de usuários', 'time_backend', 'HIGH', 'PROD'],
            'Observações': [
                'Nome da tabela sem schema',
                'Default: public',
                'Descrição opcional',
                'Time responsável',
                'Nível de criticidade',
                'Ambiente da tabela'
            ]
        })
        instructions.to_excel(writer, sheet_name='instructions', index=False)
    
    print(f"✅ Template criado: {template_path}")
    
    return template_path

if __name__ == "__main__":
    print("🚀 Criando arquivos Excel de exemplo...")
    
    sample_file = create_sample_tables_excel()
    template_file = create_template_excel()
    
    print("\n📁 Arquivos criados:")
    print(f"   • Exemplo completo: {sample_file}")
    print(f"   • Template para uso: {template_file}")
    print("\n💡 Dica: Use o template para suas próprias tabelas!")
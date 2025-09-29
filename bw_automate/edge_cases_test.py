#!/usr/bin/env python3
"""
EDGE CASES E PADRÕES COMPLEXOS
Testa limites e casos difíceis do sistema de detecção
"""

import pandas as pd
from sqlalchemy import create_engine, text
import json
import re

# TABELAS REAIS ESPERADAS (apenas 4)
EXPECTED_REAL_TABLES = ["complex_orders", "user_profiles", "system_logs", "data_warehouse"]

# ========== EDGE CASE 1: SQL COMPLEXO COM MÚLTIPLAS TABELAS ==========
def complex_sql_operations():
    # SQL com JOINs e subqueries - deve detectar apenas as tabelas PRINCIPAIS
    complex_query = """
    WITH order_stats AS (
        SELECT customer_id, COUNT(*) as order_count
        FROM complex_orders 
        WHERE created_at > '2024-01-01'
        GROUP BY customer_id
    )
    SELECT u.name, u.email, o.order_count, p.total_spent
    FROM user_profiles u
    INNER JOIN order_stats o ON u.id = o.customer_id
    LEFT JOIN customer_payments p ON u.id = p.customer_id
    WHERE o.order_count > 5
    """
    
    # Query de sistema (NÃO deve detectar)
    system_query = "SELECT COUNT(*) as table_count FROM information_schema.tables"
    
    return complex_query

# ========== EDGE CASE 2: STRINGS DINÂMICAS E F-STRINGS ==========
def dynamic_table_names():
    # F-strings com nomes de tabela - REAL
    table_name = "system_logs"
    query = f"SELECT * FROM {table_name} WHERE level = 'ERROR'"
    
    # Variáveis que NÃO são tabelas
    user_count = 1500
    error_threshold = 100
    log_retention_days = 30
    
    dynamic_sql = f"SELECT COUNT(*) as total_users FROM users WHERE created_at > NOW() - INTERVAL '{log_retention_days} days'"
    
    return query, dynamic_sql

# ========== EDGE CASE 3: MÚLTIPLAS TECNOLOGIAS MISTURADAS ==========
def mixed_technologies():
    # Pandas + SQLAlchemy - REAL
    engine = create_engine('postgresql://localhost/db')
    df = pd.read_sql("SELECT * FROM data_warehouse", engine)
    
    # API calls que NÃO são tabelas
    api_response = {
        "user_data": {"id": 123, "name": "John"},
        "order_history": [{"order_id": 1, "total": 100}],
        "metadata": {"total_records": 500}
    }
    
    # DataFrame operations que NÃO são tabelas
    df_grouped = df.groupby(['category', 'region']).sum()
    df_filtered = df[df['amount'] > 1000]
    
    return df, api_response

# ========== EDGE CASE 4: STRINGS COM PADRÕES ENGANOSOS ==========
def tricky_patterns():
    # Mensagens de erro que contêm nomes "parecidos" com tabelas
    error_messages = [
        "Connection to user_sessions failed",
        "Table 'temp_cache' was dropped",
        "Index on order_items created successfully",
        "Backup of customer_data completed"
    ]
    
    # Logs de aplicação
    log_entries = {
        "2024-01-01 10:00:00": "User admin accessed admin_panel",
        "2024-01-01 10:05:00": "Query on product_catalog took 2.5s",
        "2024-01-01 10:10:00": "Failed to insert into user_actions table"
    }
    
    # Configurações que NÃO são tabelas
    database_config = {
        "host": "localhost",
        "port": 5432,
        "database": "production_db",
        "pool_size": 20,
        "timeout": 30
    }
    
    return error_messages, log_entries

# ========== EDGE CASE 5: CÓDIGO COMENTADO E DOCUMENTAÇÃO ==========
def commented_code():
    """
    Esta função contém código comentado que pode confundir o detector.
    Histórico:
    - 2024-01-01: Criada tabela customer_archive
    - 2024-01-15: Removida tabela legacy_orders  
    - 2024-02-01: Migrada tabela user_settings para novo schema
    """
    
    # TODO: Implementar limpeza da tabela temp_data
    # FIXME: Bug na query da tabela order_summary
    
    # Este código está comentado e NÃO deve ser detectado:
    # old_query = "SELECT * FROM deprecated_table WHERE status = 'active'"
    # legacy_table = "old_user_data"
    
    active_query = "SELECT id, name FROM active_users WHERE last_login > NOW() - INTERVAL '7 days'"
    
    return active_query

# ========== EDGE CASE 6: CARACTERES ESPECIAIS E ENCODING ==========
def special_characters():
    # Nomes com caracteres especiais que NÃO devem ser detectados
    file_paths = [
        "/var/log/app.log",
        "./data/export_2024.csv", 
        "uploads/user_avatar_123.jpg",
        "templates/email_template.html"
    ]
    
    # URLs que NÃO são tabelas
    api_endpoints = [
        "https://api.example.com/users",
        "https://api.example.com/orders/123",
        "https://cdn.example.com/images/logo.png"
    ]
    
    # Regex patterns que NÃO são tabelas
    patterns = [
        r"user_\d+",
        r"order_[A-Z]{2}\d{4}",
        r"session_[a-f0-9]{32}"
    ]
    
    return file_paths, api_endpoints, patterns

# ========== EDGE CASE 7: CÓDIGO GERADO/AUTOMÁTICO ==========
def generated_code():
    # Código auto-gerado com nomes padronizados que NÃO devem ser detectados
    model_classes = [
        "UserModel", "OrderModel", "ProductModel", 
        "CategoryModel", "SessionModel"
    ]
    
    # Migrations auto-geradas
    migration_info = {
        "version": "20240101_120000",
        "description": "Create user_preferences table",
        "operations": ["CREATE TABLE", "ADD INDEX", "ADD CONSTRAINT"]
    }
    
    # Cache keys que NÃO são tabelas
    cache_keys = [
        "user_profile_123",
        "order_summary_456", 
        "product_details_789",
        "session_data_abc123"
    ]
    
    return model_classes, migration_info, cache_keys

if __name__ == "__main__":
    print("🧩 EDGE CASES E PADRÕES COMPLEXOS CRIADOS")
    print(f"📊 Tabelas reais esperadas: {len(EXPECTED_REAL_TABLES)}")
    print("📋 Lista de tabelas que DEVEM ser detectadas:")
    for i, table in enumerate(EXPECTED_REAL_TABLES, 1):
        print(f"  {i}. {table}")
    
    print("\n🎯 TESTE DE EDGE CASES:")
    print("  - SQL complexo com JOINs e CTEs")
    print("  - F-strings dinâmicos")
    print("  - Strings com padrões enganosos")
    print("  - Código comentado")
    print("  - Caracteres especiais")
    print("  - Código auto-gerado")
    print("\n⚠️ Qualquer detecção adicional é FALSO POSITIVO")
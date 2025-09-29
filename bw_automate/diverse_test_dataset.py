#!/usr/bin/env python3
"""
DATASET DIVERSIFICADO PARA TESTE DE VALIDAÇÃO
Mistura código real com potenciais falsos positivos
"""

import pandas as pd
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import requests
import json

# TABELAS REAIS ESPERADAS (6 tabelas apenas)
EXPECTED_REAL_TABLES = [
    "products", "customers", "orders", "inventory", "audit_logs", "user_sessions"
]

# ========== TABELAS REAIS (DEVEM SER DETECTADAS) ==========

# 1. SQLAlchemy Models - REAIS
class Product(sa.Table):
    __tablename__ = 'products'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255))

class Customer:
    __tablename__ = 'customers'
    
    def save(self):
        engine = sa.create_engine('postgresql://localhost/db')
        return engine.execute("INSERT INTO customers VALUES (%s)", self.data)

# 2. SQL Direto - REAIS
def business_queries():
    sql1 = "SELECT * FROM orders WHERE status = 'pending'"
    sql2 = "INSERT INTO inventory (product_id, quantity) VALUES (1, 100)"
    sql3 = "UPDATE audit_logs SET processed = true WHERE id > 0"
    return [sql1, sql2, sql3]

# 3. Pandas - REAL
def load_user_sessions():
    df = pd.read_sql("SELECT * FROM user_sessions", connection)
    return df

# ========== FALSOS POSITIVOS INTENCIONAIS (NÃO DEVEM SER DETECTADAS) ==========

# 4. Variáveis que parecem tabelas mas NÃO SÃO
def problematic_variables():
    user_id = 12345
    product_name = "Widget A"
    order_total = 199.99
    customer_email = "test@example.com"
    session_timeout = 3600
    last_login_date = "2024-01-01"
    
    # Headers HTTP
    headers = {
        "Content-Type": "application/json",
        "attachment": "filename=report.csv"
    }
    
    # Dados JSON com campos que parecem tabelas
    user_data = {
        "user_id": 123,
        "username": "admin",
        "is_active": True,
        "created_at": "2024-01-01",
        "permissions": ["read_users", "write_orders"]
    }
    
    return user_id, product_name, order_total

# 5. Lógica de contagem/agregação (NÃO são tabelas)
def calculate_metrics():
    total_products = 500
    active_customers = 1200
    pending_orders = 45
    monthly_revenue = 25000.00
    
    # Queries de sistema que NÃO são tabelas de usuário
    system_query = "SELECT name FROM sqlite_master WHERE type='table'"
    pg_query = "SELECT tablename FROM pg_tables WHERE schemaname='public'"
    
    return {
        'total_products': total_products,
        'active_customers': active_customers,
        'pending_orders': pending_orders
    }

# 6. Configurações e metadados (NÃO são tabelas)
def app_config():
    config = {
        "database_url": "postgresql://localhost:5432/mydb",
        "redis_host": "localhost",
        "log_level": "INFO",
        "session_duration": 3600,
        "backup_enabled": True
    }
    
    # Nomes de arquivo
    template_file = "template_orders.xlsx"
    logo_file = "company_logo.png"
    
    return config

# 7. Código de teste/mock (NÃO são tabelas reais)
def test_functions():
    # Dados de teste que NÃO devem ser considerados tabelas
    test_users = ["user1", "user2", "admin"]
    mock_orders = [{"id": 1, "total": 100}, {"id": 2, "total": 200}]
    sample_data = {"products": [1, 2, 3], "categories": ["A", "B"]}
    
    return test_users, mock_orders, sample_data

# 8. Mensagens e logs (NÃO são tabelas)
def logging_examples():
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Mensagens que contêm palavras como tabelas
    logger.info("Processing user_records table")
    logger.error("Failed to connect to product_database")
    logger.debug("Updating customer_profiles in memory")
    
    # Strings com SQL interno que NÃO são tabelas de usuário
    error_msg = "Table 'temp_data' doesn't exist"
    success_msg = "Created temporary table temp_processing"
    
    return logger

if __name__ == "__main__":
    print("🧪 DATASET DIVERSIFICADO CRIADO")
    print(f"📊 Tabelas reais esperadas: {len(EXPECTED_REAL_TABLES)}")
    print("📋 Lista de tabelas que DEVEM ser detectadas:")
    for i, table in enumerate(EXPECTED_REAL_TABLES, 1):
        print(f"  {i}. {table}")
    
    print("\n⚠️ IMPORTANTE:")
    print("  - Qualquer detecção adicional é um FALSO POSITIVO")
    print("  - Qualquer tabela não detectada é um FALSO NEGATIVO")
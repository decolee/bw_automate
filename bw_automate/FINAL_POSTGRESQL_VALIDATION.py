#!/usr/bin/env python3
"""
🏆 VALIDAÇÃO FINAL DO POSTGRESQL TABLE MAPPER
Testa o sistema completo em cenários de produção
"""

import os
import json
import shutil
from pathlib import Path
from POSTGRESQL_TABLE_MAPPER import PostgreSQLTableMapper
import time

def create_production_simulation():
    """Cria simulação de projeto de produção real"""
    
    test_dir = Path("production_simulation")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # 1. Sistema de E-commerce completo
    ecommerce_models = '''#!/usr/bin/env python3
"""
Modelos de E-commerce - Sistema Real
"""

from sqlalchemy import Column, Integer, String, DateTime, Decimal, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from django.db import models

Base = declarative_base()

# SQLAlchemy Models com esquemas específicos
class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'auth'}
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password_hash = Column(String(128))
    created_at = Column(DateTime)
    
class Customer(Base):
    __tablename__ = 'customers'
    __table_args__ = {'schema': 'crm'}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('auth.users.id'))
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone = Column(String(20))

class Product(Base):
    __tablename__ = 'products'
    __table_args__ = {'schema': 'inventory'}
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True)
    name = Column(String(200))
    description = Column(Text)
    price = Column(Decimal(10, 2))
    stock_quantity = Column(Integer)

class Order(Base):
    __tablename__ = 'orders'
    __table_args__ = {'schema': 'sales'}
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('crm.customers.id'))
    total_amount = Column(Decimal(10, 2))
    status = Column(String(20))
    created_at = Column(DateTime)

class OrderItem(Base):
    __tablename__ = 'order_items'
    __table_args__ = {'schema': 'sales'}
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('sales.orders.id'))
    product_id = Column(Integer, ForeignKey('inventory.products.id'))
    quantity = Column(Integer)
    unit_price = Column(Decimal(10, 2))

# Django Models para comparação
class Category(models.Model):
    class Meta:
        db_table = 'product_categories'
        
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)

class Review(models.Model):
    class Meta:
        db_table = 'product_reviews'
        
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
'''
    
    (test_dir / "ecommerce_models.py").write_text(ecommerce_models)
    
    # 2. Serviços com queries complexas
    ecommerce_services = '''#!/usr/bin/env python3
"""
Serviços de E-commerce com SQL complexo
"""

import psycopg2
from sqlalchemy import create_engine, text
from .ecommerce_models import User, Customer, Product, Order, OrderItem

class OrderService:
    def __init__(self, engine):
        self.engine = engine
    
    def get_customer_analytics(self, customer_id):
        """Analytics completo do cliente"""
        query = """
        SELECT 
            c.id,
            c.first_name,
            c.last_name,
            COUNT(DISTINCT o.id) as total_orders,
            SUM(o.total_amount) as lifetime_value,
            AVG(o.total_amount) as avg_order_value,
            COUNT(DISTINCT oi.product_id) as unique_products_bought,
            MAX(o.created_at) as last_order_date,
            AVG(pr.rating) as avg_product_rating
        FROM crm.customers c
        LEFT JOIN sales.orders o ON c.id = o.customer_id
        LEFT JOIN sales.order_items oi ON o.id = oi.order_id
        LEFT JOIN inventory.products p ON oi.product_id = p.id
        LEFT JOIN product_reviews pr ON p.id = pr.product_id AND c.id = pr.customer_id
        WHERE c.id = :customer_id
        GROUP BY c.id, c.first_name, c.last_name
        """
        
        with self.engine.connect() as conn:
            return conn.execute(text(query), customer_id=customer_id).fetchone()
    
    def update_inventory_after_order(self, order_id):
        """Atualiza estoque após pedido"""
        update_query = """
        UPDATE inventory.products 
        SET stock_quantity = stock_quantity - oi.quantity,
            last_updated = NOW()
        FROM sales.order_items oi
        WHERE products.id = oi.product_id 
          AND oi.order_id = :order_id
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(update_query), order_id=order_id)
    
    def generate_sales_report(self, start_date, end_date):
        """Relatório de vendas por período"""
        report_query = """
        INSERT INTO reporting.daily_sales_summary 
        (report_date, total_orders, total_revenue, avg_order_value, top_product_id)
        
        WITH daily_stats AS (
            SELECT 
                DATE(o.created_at) as order_date,
                COUNT(o.id) as order_count,
                SUM(o.total_amount) as revenue,
                AVG(o.total_amount) as avg_value
            FROM sales.orders o
            WHERE o.created_at BETWEEN :start_date AND :end_date
              AND o.status = 'completed'
            GROUP BY DATE(o.created_at)
        ),
        top_products AS (
            SELECT 
                DATE(o.created_at) as order_date,
                oi.product_id,
                SUM(oi.quantity) as total_sold,
                ROW_NUMBER() OVER (PARTITION BY DATE(o.created_at) ORDER BY SUM(oi.quantity) DESC) as rank
            FROM sales.orders o
            JOIN sales.order_items oi ON o.id = oi.order_id
            WHERE o.created_at BETWEEN :start_date AND :end_date
              AND o.status = 'completed'
            GROUP BY DATE(o.created_at), oi.product_id
        )
        SELECT 
            ds.order_date,
            ds.order_count,
            ds.revenue,
            ds.avg_value,
            tp.product_id
        FROM daily_stats ds
        LEFT JOIN top_products tp ON ds.order_date = tp.order_date AND tp.rank = 1
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(report_query), start_date=start_date, end_date=end_date)

class InventoryService:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
    
    def bulk_update_prices(self, category_id, percentage_increase):
        """Atualização em massa de preços"""
        cursor = self.conn.cursor()
        
        # Log da operação
        cursor.execute("""
            INSERT INTO audit.price_changes 
            (category_id, change_percentage, changed_by, change_date)
            VALUES (%s, %s, %s, NOW())
        """, (category_id, percentage_increase, 'system'))
        
        # Atualiza preços
        cursor.execute("""
            UPDATE inventory.products 
            SET price = price * (1 + %s / 100.0),
                last_price_update = NOW()
            WHERE id IN (
                SELECT p.id 
                FROM inventory.products p
                JOIN product_categories pc ON p.category_id = pc.id
                WHERE pc.id = %s OR pc.parent_id = %s
            )
        """, (percentage_increase, category_id, category_id))
        
        # Atualiza cache de preços
        cursor.execute("""
            DELETE FROM cache.product_pricing 
            WHERE product_id IN (
                SELECT p.id 
                FROM inventory.products p
                JOIN product_categories pc ON p.category_id = pc.id
                WHERE pc.id = %s OR pc.parent_id = %s
            )
        """, (category_id, category_id))
        
        self.conn.commit()
    
    def restock_notification(self, threshold=10):
        """Notificação de reposição de estoque"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO notifications.stock_alerts (product_id, current_stock, threshold, created_at)
            SELECT 
                p.id,
                p.stock_quantity,
                %s,
                NOW()
            FROM inventory.products p
            WHERE p.stock_quantity <= %s
              AND p.id NOT IN (
                  SELECT product_id 
                  FROM notifications.stock_alerts 
                  WHERE created_at > NOW() - INTERVAL '24 hours'
                    AND resolved = false
              )
        """, (threshold, threshold))
        
        self.conn.commit()

class ReportingService:
    def generate_comprehensive_analytics(self):
        """Analytics abrangente multi-esquema"""
        
        analytics_queries = [
            # Customer segmentation
            """
            CREATE OR REPLACE VIEW analytics.customer_segments AS
            SELECT 
                c.id,
                CASE 
                    WHEN total_spent > 5000 THEN 'VIP'
                    WHEN total_spent > 1000 THEN 'Premium'
                    WHEN total_spent > 100 THEN 'Regular'
                    ELSE 'New'
                END as segment,
                total_orders,
                total_spent,
                last_order_date
            FROM (
                SELECT 
                    c.id,
                    COUNT(o.id) as total_orders,
                    COALESCE(SUM(o.total_amount), 0) as total_spent,
                    MAX(o.created_at) as last_order_date
                FROM crm.customers c
                LEFT JOIN sales.orders o ON c.id = o.customer_id
                GROUP BY c.id
            ) c
            """,
            
            # Product performance
            """
            CREATE OR REPLACE VIEW analytics.product_performance AS
            SELECT 
                p.id,
                p.name,
                p.sku,
                COUNT(oi.id) as times_ordered,
                SUM(oi.quantity) as total_quantity_sold,
                SUM(oi.quantity * oi.unit_price) as total_revenue,
                AVG(pr.rating) as avg_rating,
                COUNT(pr.id) as review_count
            FROM inventory.products p
            LEFT JOIN sales.order_items oi ON p.id = oi.product_id
            LEFT JOIN product_reviews pr ON p.id = pr.product_id
            GROUP BY p.id, p.name, p.sku
            """,
            
            # Monthly trends
            """
            CREATE TABLE IF NOT EXISTS analytics.monthly_trends (
                month_year DATE PRIMARY KEY,
                total_orders INTEGER,
                total_revenue DECIMAL(15,2),
                new_customers INTEGER,
                avg_order_value DECIMAL(10,2),
                top_category_id INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        ]
        
        return analytics_queries
'''
    
    (test_dir / "ecommerce_services.py").write_text(ecommerce_services)
    
    # 3. Background jobs e scripts
    background_jobs = '''#!/usr/bin/env python3
"""
Jobs em background e scripts de manutenção
"""

import psycopg2
from datetime import datetime, timedelta

class DataMaintenanceJobs:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def daily_cleanup_job(self):
        """Job de limpeza diária"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Limpeza de dados antigos
        cleanup_operations = [
            # Remove sessões expiradas
            """
            DELETE FROM auth.user_sessions 
            WHERE expires_at < NOW() - INTERVAL '30 days'
            """,
            
            # Archive logs antigos
            """
            INSERT INTO archive.system_logs 
            SELECT * FROM logs.application_events 
            WHERE created_at < NOW() - INTERVAL '90 days'
            """,
            
            """
            DELETE FROM logs.application_events 
            WHERE created_at < NOW() - INTERVAL '90 days'
            """,
            
            # Limpa cache expirado
            """
            DELETE FROM cache.query_results 
            WHERE expires_at < NOW()
            """,
            
            # Remove tokens expirados
            """
            DELETE FROM auth.api_tokens 
            WHERE expires_at < NOW()
            """,
            
            # Atualiza estatísticas
            """
            VACUUM ANALYZE sales.orders
            """,
            
            """
            VACUUM ANALYZE inventory.products
            """,
            
            """
            REINDEX TABLE crm.customers
            """
        ]
        
        for operation in cleanup_operations:
            try:
                cursor.execute(operation)
                conn.commit()
            except Exception as e:
                print(f"Erro na operação: {operation[:50]}... - {e}")
                conn.rollback()
        
        cursor.close()
        conn.close()
    
    def weekly_analytics_job(self):
        """Job semanal de analytics"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Atualiza materalized views
        materialized_views = [
            "REFRESH MATERIALIZED VIEW analytics.customer_lifetime_value",
            "REFRESH MATERIALIZED VIEW analytics.product_popularity_trends",
            "REFRESH MATERIALIZED VIEW analytics.geographic_sales_distribution",
            "REFRESH MATERIALIZED VIEW analytics.seasonal_demand_patterns"
        ]
        
        for view_refresh in materialized_views:
            cursor.execute(view_refresh)
        
        # Gera relatórios semanais
        cursor.execute("""
            INSERT INTO reporting.weekly_summaries 
            (week_start, week_end, total_orders, total_revenue, new_customers, returning_customers)
            
            SELECT 
                DATE_TRUNC('week', NOW()) - INTERVAL '1 week' as week_start,
                DATE_TRUNC('week', NOW()) - INTERVAL '1 day' as week_end,
                COUNT(DISTINCT o.id) as total_orders,
                SUM(o.total_amount) as total_revenue,
                COUNT(DISTINCT CASE WHEN c.created_at >= DATE_TRUNC('week', NOW()) - INTERVAL '1 week' 
                                   THEN o.customer_id END) as new_customers,
                COUNT(DISTINCT CASE WHEN c.created_at < DATE_TRUNC('week', NOW()) - INTERVAL '1 week' 
                                   THEN o.customer_id END) as returning_customers
            FROM sales.orders o
            JOIN crm.customers c ON o.customer_id = c.id
            WHERE o.created_at >= DATE_TRUNC('week', NOW()) - INTERVAL '1 week'
              AND o.created_at < DATE_TRUNC('week', NOW())
              AND o.status = 'completed'
        """)
        
        conn.commit()
        cursor.close()
        conn.close()

class ETLJobs:
    """Extract, Transform, Load jobs"""
    
    def import_external_data(self):
        """Importa dados de sistemas externos"""
        
        import_queries = [
            # Importa dados de CRM externo
            """
            CREATE TABLE IF NOT EXISTS staging.external_customers (
                external_id VARCHAR(50),
                email VARCHAR(255),
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                company VARCHAR(100),
                import_date TIMESTAMP DEFAULT NOW()
            )
            """,
            
            """
            COPY staging.external_customers (external_id, email, first_name, last_name, company)
            FROM '/tmp/external_customers.csv'
            WITH CSV HEADER
            """,
            
            # Sincroniza com tabela principal
            """
            INSERT INTO crm.customers (user_id, first_name, last_name, external_reference)
            SELECT 
                u.id,
                ec.first_name,
                ec.last_name,
                ec.external_id
            FROM staging.external_customers ec
            JOIN auth.users u ON ec.email = u.email
            WHERE ec.external_id NOT IN (
                SELECT external_reference 
                FROM crm.customers 
                WHERE external_reference IS NOT NULL
            )
            """,
            
            # Importa dados de produtos
            """
            CREATE TABLE IF NOT EXISTS staging.product_updates (
                sku VARCHAR(50),
                new_price DECIMAL(10,2),
                new_stock INTEGER,
                supplier_id INTEGER,
                import_batch VARCHAR(50),
                import_date TIMESTAMP DEFAULT NOW()
            )
            """,
            
            """
            UPDATE inventory.products 
            SET 
                price = pu.new_price,
                stock_quantity = pu.new_stock,
                supplier_id = pu.supplier_id,
                last_updated = NOW()
            FROM staging.product_updates pu
            WHERE products.sku = pu.sku
              AND pu.import_batch = 'daily_sync_2024'
            """,
            
            # Limpeza de staging
            """
            TRUNCATE TABLE staging.external_customers
            """,
            
            """
            TRUNCATE TABLE staging.product_updates
            """
        ]
        
        return import_queries
    
    def export_for_analytics(self):
        """Exporta dados para ferramentas de analytics"""
        
        export_queries = [
            # Cria snapshot para analytics
            """
            CREATE TABLE IF NOT EXISTS analytics.daily_snapshot_orders AS
            SELECT 
                o.id,
                o.customer_id,
                o.total_amount,
                o.status,
                o.created_at,
                c.first_name,
                c.last_name,
                COUNT(oi.id) as item_count
            FROM sales.orders o
            JOIN crm.customers c ON o.customer_id = c.id
            LEFT JOIN sales.order_items oi ON o.id = oi.order_id
            WHERE DATE(o.created_at) = CURRENT_DATE - INTERVAL '1 day'
            GROUP BY o.id, o.customer_id, o.total_amount, o.status, o.created_at, c.first_name, c.last_name
            """,
            
            # Exporta para sistema de BI
            """
            COPY (
                SELECT 
                    p.sku,
                    p.name,
                    p.price,
                    p.stock_quantity,
                    pc.name as category_name,
                    SUM(oi.quantity) as units_sold_last_30_days
                FROM inventory.products p
                LEFT JOIN product_categories pc ON p.category_id = pc.id
                LEFT JOIN sales.order_items oi ON p.id = oi.product_id
                LEFT JOIN sales.orders o ON oi.order_id = o.id
                WHERE o.created_at >= NOW() - INTERVAL '30 days'
                  OR o.created_at IS NULL
                GROUP BY p.id, p.sku, p.name, p.price, p.stock_quantity, pc.name
            ) TO '/tmp/product_performance_export.csv' WITH CSV HEADER
            """
        ]
        
        return export_queries
'''
    
    (test_dir / "background_jobs.py").write_text(background_jobs)
    
    # 4. Arquivo de configuração e utils
    config_utils = '''#!/usr/bin/env python3
"""
Configurações e utilitários do sistema
"""

from .ecommerce_models import *
from .ecommerce_services import OrderService, InventoryService, ReportingService
from .background_jobs import DataMaintenanceJobs, ETLJobs

# Configurações de banco por ambiente
DATABASE_CONFIGS = {
    'production': {
        'auth': 'postgresql://user:pass@prod-auth-db:5432/auth_db',
        'crm': 'postgresql://user:pass@prod-crm-db:5432/crm_db', 
        'inventory': 'postgresql://user:pass@prod-inv-db:5432/inventory_db',
        'sales': 'postgresql://user:pass@prod-sales-db:5432/sales_db',
        'analytics': 'postgresql://user:pass@prod-analytics-db:5432/analytics_db',
        'reporting': 'postgresql://user:pass@prod-reporting-db:5432/reporting_db'
    },
    'staging': {
        'auth': 'postgresql://user:pass@staging-db:5432/staging_auth',
        'crm': 'postgresql://user:pass@staging-db:5432/staging_crm',
        'inventory': 'postgresql://user:pass@staging-db:5432/staging_inventory',
        'sales': 'postgresql://user:pass@staging-db:5432/staging_sales'
    }
}

# Mapeamento de tabelas por esquema
SCHEMA_TABLE_MAPPING = {
    'auth': ['users', 'user_sessions', 'api_tokens', 'password_resets'],
    'crm': ['customers', 'customer_addresses', 'customer_preferences'],
    'inventory': ['products', 'product_variants', 'suppliers', 'purchase_orders'],
    'sales': ['orders', 'order_items', 'discounts', 'promotions'],
    'analytics': ['customer_segments', 'product_performance', 'monthly_trends'],
    'reporting': ['daily_sales_summary', 'weekly_summaries', 'monthly_reports'],
    'cache': ['query_results', 'product_pricing', 'user_cart_cache'],
    'logs': ['application_events', 'error_logs', 'audit_trail'],
    'notifications': ['stock_alerts', 'price_alerts', 'system_notifications'],
    'staging': ['external_customers', 'product_updates', 'import_logs'],
    'archive': ['system_logs', 'old_orders', 'deleted_products']
}

class DatabaseRouter:
    """Router para múltiplos bancos de dados"""
    
    def get_connection(self, schema_name, environment='production'):
        """Retorna conexão baseada no esquema"""
        configs = DATABASE_CONFIGS.get(environment, {})
        return configs.get(schema_name)
    
    def execute_cross_schema_query(self, query, schemas_involved):
        """Executa query que envolve múltiplos esquemas"""
        # Implementação para queries cross-schema
        pass

def get_table_list_for_schema(schema_name):
    """Retorna lista de tabelas para um esquema"""
    return SCHEMA_TABLE_MAPPING.get(schema_name, [])

def validate_table_references():
    """Valida se todas as referências de tabelas estão corretas"""
    
    validation_queries = [
        # Verifica foreign keys
        """
        SELECT 
            tc.table_schema,
            tc.table_name,
            kcu.column_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema IN ('auth', 'crm', 'inventory', 'sales', 'analytics')
        """,
        
        # Verifica views que referenciam tabelas
        """
        SELECT 
            schemaname,
            viewname,
            definition
        FROM pg_views
        WHERE schemaname IN ('analytics', 'reporting')
        """,
        
        # Verifica índices
        """
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname IN ('auth', 'crm', 'inventory', 'sales')
        """
    ]
    
    return validation_queries
'''
    
    (test_dir / "config_utils.py").write_text(config_utils)
    
    return test_dir

def run_final_validation():
    """Executa validação final completa"""
    
    print("🏆 VALIDAÇÃO FINAL DO POSTGRESQL TABLE MAPPER")
    print("=" * 60)
    
    # Cria simulação de produção
    print("🏭 Criando simulação de projeto de produção...")
    prod_project = create_production_simulation()
    
    # Executa mapeador
    print("🔍 Executando análise de produção...")
    mapper = PostgreSQLTableMapper()
    
    start_time = time.time()
    results = mapper.analyze_project(str(prod_project))
    analysis_time = time.time() - start_time
    
    # Salva resultados
    output_file = "FINAL_PRODUCTION_VALIDATION.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Análise detalhada dos resultados
    print("\n📊 RESULTADOS DA VALIDAÇÃO FINAL:")
    print("=" * 50)
    
    summary = results['analysis_summary']
    tables = results['tables_discovered']
    stats = results['statistics']
    
    print(f"📁 Arquivos analisados: {summary['files_analyzed']}")
    print(f"🗃️ Tabelas únicas encontradas: {summary['unique_tables_found']}")
    print(f"📊 Total de referências: {summary['total_table_references']}")
    print(f"📂 Esquemas encontrados: {len(summary['schemas_found'])}")
    print(f"🔗 Mapeamentos cross-file: {summary['cross_file_mappings']}")
    print(f"⏱️ Tempo de análise: {analysis_time:.3f}s")
    print(f"🚀 Performance: {summary['files_analyzed'] / analysis_time:.1f} arquivos/segundo")
    
    # Validação de esquemas esperados
    expected_schemas = [
        'auth', 'crm', 'inventory', 'sales', 'analytics', 
        'reporting', 'cache', 'logs', 'notifications', 'staging', 'archive'
    ]
    found_schemas = set(summary['schemas_found'])
    
    print(f"\n📂 VALIDAÇÃO DE ESQUEMAS:")
    print(f"   Esperados: {len(expected_schemas)}")
    print(f"   Encontrados: {len(found_schemas)}")
    
    missing_schemas = set(expected_schemas) - found_schemas
    if missing_schemas:
        print(f"   ❌ Não encontrados: {', '.join(missing_schemas)}")
    else:
        print(f"   ✅ Todos os esquemas esperados foram encontrados!")
    
    extra_schemas = found_schemas - set(expected_schemas)
    if extra_schemas:
        print(f"   ➕ Extras: {', '.join(extra_schemas)}")
    
    # Validação de tabelas críticas
    critical_tables = [
        'users', 'customers', 'products', 'orders', 'order_items',
        'user_sessions', 'product_reviews', 'daily_sales_summary'
    ]
    
    found_table_names = {name.split('.')[-1] for name in tables.keys()}
    
    print(f"\n🗃️ VALIDAÇÃO DE TABELAS CRÍTICAS:")
    missing_critical = set(critical_tables) - found_table_names
    if missing_critical:
        print(f"   ❌ Tabelas críticas não encontradas: {', '.join(missing_critical)}")
    else:
        print(f"   ✅ Todas as tabelas críticas foram encontradas!")
    
    # Análise de contextos
    print(f"\n📈 DISTRIBUIÇÃO POR CONTEXTO:")
    for context, count in stats['context_breakdown'].items():
        percentage = (count / summary['total_table_references']) * 100
        print(f"   • {context}: {count} ({percentage:.1f}%)")
    
    # Análise de operações
    print(f"\n🔧 DISTRIBUIÇÃO POR OPERAÇÃO:")
    valid_operations = {k: v for k, v in stats['operation_breakdown'].items() 
                       if k and k != "UNKNOWN"}
    for operation, count in valid_operations.items():
        percentage = (count / summary['total_table_references']) * 100
        print(f"   • {operation}: {count} ({percentage:.1f}%)")
    
    # Top 10 tabelas mais referenciadas
    print(f"\n🏆 TOP 10 TABELAS MAIS REFERENCIADAS:")
    for i, item in enumerate(stats['most_referenced_tables'][:10], 1):
        print(f"   {i:2d}. {item['table']}: {item['references']} refs em {item['files']} arquivos")
    
    # Validação de confiança
    confidence_dist = stats['confidence_distribution']
    total_refs = sum(confidence_dist.values())
    high_confidence = confidence_dist.get('high (>= 0.9)', 0)
    high_confidence_pct = (high_confidence / total_refs) * 100 if total_refs > 0 else 0
    
    print(f"\n🎯 DISTRIBUIÇÃO DE CONFIANÇA:")
    for level, count in confidence_dist.items():
        percentage = (count / total_refs) * 100 if total_refs > 0 else 0
        print(f"   • {level}: {count} ({percentage:.1f}%)")
    
    print(f"\n✅ VALIDAÇÃO DE QUALIDADE:")
    if high_confidence_pct >= 70:
        print(f"   ✅ Alta confiança: {high_confidence_pct:.1f}% (Excelente!)")
    elif high_confidence_pct >= 50:
        print(f"   ⚠️  Alta confiança: {high_confidence_pct:.1f}% (Bom)")
    else:
        print(f"   ❌ Alta confiança: {high_confidence_pct:.1f}% (Precisa melhorar)")
    
    # Verifica se há tabela "if" (problema anterior)
    if 'if' in found_table_names:
        print(f"   ❌ PROBLEMA: Ainda detectando 'if' como tabela!")
    else:
        print(f"   ✅ Problema 'if' corrigido!")
    
    # Performance
    print(f"\n⚡ ANÁLISE DE PERFORMANCE:")
    refs_per_file = summary['total_table_references'] / summary['files_analyzed']
    tables_per_file = summary['unique_tables_found'] / summary['files_analyzed']
    
    print(f"   • Referências por arquivo: {refs_per_file:.1f}")
    print(f"   • Tabelas únicas por arquivo: {tables_per_file:.1f}")
    print(f"   • Tempo por arquivo: {(analysis_time / summary['files_analyzed']) * 1000:.1f}ms")
    
    # Score final
    score_components = {
        'schemas_found': min(100, (len(found_schemas) / len(expected_schemas)) * 100),
        'critical_tables': min(100, (len(found_table_names & set(critical_tables)) / len(critical_tables)) * 100),
        'high_confidence': high_confidence_pct,
        'no_false_positives': 100 if 'if' not in found_table_names else 0,
        'performance': min(100, (summary['files_analyzed'] / analysis_time) * 10)  # 10 arquivos/segundo = 100%
    }
    
    final_score = sum(score_components.values()) / len(score_components)
    
    print(f"\n🏆 SCORE FINAL: {final_score:.1f}/100")
    print(f"   • Esquemas: {score_components['schemas_found']:.1f}/100")
    print(f"   • Tabelas críticas: {score_components['critical_tables']:.1f}/100")
    print(f"   • Alta confiança: {score_components['high_confidence']:.1f}/100")
    print(f"   • Sem falsos positivos: {score_components['no_false_positives']:.1f}/100")
    print(f"   • Performance: {score_components['performance']:.1f}/100")
    
    if final_score >= 90:
        print(f"\n🎉 EXCELENTE! Sistema pronto para produção!")
    elif final_score >= 70:
        print(f"\n✅ BOM! Sistema funcional com melhorias possíveis")
    else:
        print(f"\n⚠️  PRECISA MELHORAR antes da produção")
    
    print(f"\n📄 Relatório completo salvo em: {output_file}")
    
    # Gera relatório de texto
    mapper.generate_table_map_report("FINAL_PRODUCTION_REPORT.json")
    
    # Limpeza
    shutil.rmtree(prod_project)
    print(f"🧹 Projeto de teste removido")
    
    return results, final_score

if __name__ == "__main__":
    results, score = run_final_validation()
    print(f"\n🎯 VALIDAÇÃO CONCLUÍDA - Score: {score:.1f}/100")
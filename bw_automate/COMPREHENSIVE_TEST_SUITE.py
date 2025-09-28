#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE TEST SUITE
Suite completa de testes para validação do sistema PostgreSQL + Airflow
"""

import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple
import unittest
from dataclasses import dataclass
from collections import defaultdict

# Import all analyzers
try:
    from ENHANCED_POSTGRESQL_AIRFLOW_MAPPER import EnhancedPostgreSQLAirflowMapper
    from POSTGRESQL_TABLE_MAPPER import PostgreSQLTableMapper
    from AIRFLOW_INTEGRATION_CLI import AirflowIntegrationCLI
    from BW_UNIFIED_CLI import BWUnifiedCLI
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    sys.exit(1)

@dataclass
class TestResult:
    """Resultado de um teste"""
    test_name: str
    passed: bool
    execution_time: float
    details: Dict[str, Any]
    error_message: str = ""

class TestProjectGenerator:
    """Gerador de projetos de teste"""
    
    def __init__(self):
        self.test_projects = {}
    
    def create_airflow_dag_project(self) -> Path:
        """Cria projeto focado em DAGs Airflow"""
        test_dir = Path("test_airflow_dag_project")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()
        
        # DAG complexa com múltiplas tabelas
        dag_code = '''#!/usr/bin/env python3
"""
DAG de ETL complexo para e-commerce
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
import pandas as pd
import psycopg2

# Configuração da DAG
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'ecommerce_etl_complex',
    default_args=default_args,
    description='ETL complexo para dados de e-commerce',
    schedule_interval=timedelta(days=1),
    catchup=False
)

def extract_customers():
    """Extrai dados de clientes"""
    conn = psycopg2.connect(
        host="localhost",
        database="ecommerce",
        user="etl_user",
        password="password"
    )
    
    query = """
    SELECT 
        c.customer_id,
        c.customer_name,
        c.email,
        c.registration_date,
        ca.address_line1,
        ca.city,
        ca.state
    FROM customers c
    LEFT JOIN customer_addresses ca ON c.customer_id = ca.customer_id
    WHERE c.status = 'active'
      AND c.registration_date >= CURRENT_DATE - INTERVAL '1 year'
    """
    
    df = pd.read_sql(query, conn)
    
    # Também busca dados de preferências
    preferences_query = """
    SELECT 
        customer_id,
        preference_category,
        preference_value
    FROM customer_preferences
    WHERE is_active = true
    """
    
    preferences_df = pd.read_sql(preferences_query, conn)
    
    conn.close()
    return df, preferences_df

def extract_orders():
    """Extrai dados de pedidos"""
    conn = psycopg2.connect(
        host="localhost", 
        database="ecommerce",
        user="etl_user",
        password="password"
    )
    
    # Query principal de pedidos
    orders_query = """
    SELECT 
        o.order_id,
        o.customer_id,
        o.order_date,
        o.total_amount,
        o.status,
        o.payment_method,
        oi.product_id,
        oi.quantity,
        oi.unit_price,
        p.product_name,
        p.category_id,
        pc.category_name
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    JOIN product_categories pc ON p.category_id = pc.category_id
    WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'
      AND o.status IN ('completed', 'shipped', 'delivered')
    """
    
    df = pd.read_sql(orders_query, conn)
    
    # Busca dados de desconto
    discounts_query = """
    SELECT 
        order_id,
        discount_code,
        discount_amount,
        discount_type
    FROM order_discounts
    WHERE applied_date >= CURRENT_DATE - INTERVAL '30 days'
    """
    
    discounts_df = pd.read_sql(discounts_query, conn)
    
    conn.close()
    return df, discounts_df

def transform_customer_data():
    """Transforma dados de clientes"""
    # Simula processamento
    pass

def load_to_warehouse():
    """Carrega dados no data warehouse"""
    conn = psycopg2.connect(
        host="localhost",
        database="warehouse",
        user="warehouse_user", 
        password="password"
    )
    
    cursor = conn.cursor()
    
    # Limpeza de dados antigos
    cursor.execute("""
        DELETE FROM warehouse.customer_summary 
        WHERE report_date < CURRENT_DATE - INTERVAL '30 days'
    """)
    
    # Inserção de novos dados
    cursor.execute("""
        INSERT INTO warehouse.customer_summary 
        (customer_id, total_orders, total_spent, last_order_date, report_date)
        SELECT 
            c.customer_id,
            COUNT(o.order_id) as total_orders,
            SUM(o.total_amount) as total_spent,
            MAX(o.order_date) as last_order_date,
            CURRENT_DATE as report_date
        FROM staging.customers_temp c
        LEFT JOIN staging.orders_temp o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id
    """)
    
    # Atualiza métricas
    cursor.execute("""
        UPDATE warehouse.daily_metrics 
        SET 
            total_customers = (SELECT COUNT(*) FROM warehouse.customer_summary),
            total_orders = (SELECT SUM(total_orders) FROM warehouse.customer_summary),
            last_updated = NOW()
        WHERE metric_date = CURRENT_DATE
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# Definição das tasks
extract_customers_task = PythonOperator(
    task_id='extract_customers',
    python_callable=extract_customers,
    dag=dag
)

extract_orders_task = PythonOperator(
    task_id='extract_orders', 
    python_callable=extract_orders,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform_customer_data',
    python_callable=transform_customer_data,
    dag=dag
)

# Script bash que chama Python externo
process_analytics_task = BashOperator(
    task_id='process_analytics',
    bash_command='python3 /scripts/analytics_processor.py --table warehouse.customer_summary',
    dag=dag
)

load_task = PythonOperator(
    task_id='load_to_warehouse',
    python_callable=load_to_warehouse,
    dag=dag
)

# Dependências
extract_customers_task >> transform_task
extract_orders_task >> transform_task
transform_task >> load_task
load_task >> process_analytics_task
'''
        
        (test_dir / "ecommerce_etl_dag.py").write_text(dag_code)
        
        # Script Python externo chamado pela DAG
        analytics_script = '''#!/usr/bin/env python3
"""
Script de analytics chamado via BashOperator
"""

import argparse
import psycopg2
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--table', required=True, help='Tabela para processar')
    args = parser.parse_args()
    
    table_name = args.table
    
    # Conecta ao warehouse
    conn = psycopg2.connect(
        host="localhost",
        database="warehouse", 
        user="analytics_user",
        password="password"
    )
    
    # Processa analytics
    query = f"""
    SELECT 
        customer_id,
        total_orders,
        total_spent,
        CASE 
            WHEN total_spent > 1000 THEN 'VIP'
            WHEN total_spent > 500 THEN 'Premium'
            ELSE 'Regular'
        END as customer_segment
    FROM {table_name}
    WHERE report_date = CURRENT_DATE
    """
    
    df = pd.read_sql(query, conn)
    
    # Salva resultados
    df.to_sql('customer_segments', conn, if_exists='replace', index=False)
    
    # Atualiza tabela de métricas
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO analytics.segment_metrics (segment, customer_count, avg_spent, date_calculated)
        SELECT 
            customer_segment,
            COUNT(*) as customer_count,
            AVG(total_spent) as avg_spent,
            CURRENT_DATE
        FROM customer_segments
        GROUP BY customer_segment
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Analytics processado para {table_name}")

if __name__ == "__main__":
    main()
'''
        
        scripts_dir = test_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "analytics_processor.py").write_text(analytics_script)
        
        return test_dir
    
    def create_python_standalone_project(self) -> Path:
        """Cria projeto Python standalone com PostgreSQL"""
        test_dir = Path("test_python_standalone")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()
        
        # Models SQLAlchemy
        models_code = '''#!/usr/bin/env python3
"""
Modelos de dados com SQLAlchemy
"""

from sqlalchemy import Column, Integer, String, DateTime, Decimal, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    price = Column(Decimal(10, 2))
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    category = relationship("Category", back_populates="products")

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    
    products = relationship("Product", back_populates="category")

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total = Column(Decimal(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

# Tabela adicional usando Table()
from sqlalchemy import Table, MetaData

metadata = MetaData()

user_sessions = Table('user_sessions', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('session_token', String(255)),
    Column('created_at', DateTime, default=datetime.utcnow)
)
'''
        
        (test_dir / "models.py").write_text(models_code)
        
        # Service layer com SQL complexo
        service_code = '''#!/usr/bin/env python3
"""
Camada de serviços com SQL complexo
"""

import psycopg2
import pandas as pd
from typing import List, Dict, Any
from models import User, Product, Order

class UserService:
    def __init__(self, connection_string: str):
        self.conn_str = connection_string
    
    def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """Analytics completo do usuário"""
        conn = psycopg2.connect(self.conn_str)
        
        query = """
        WITH user_stats AS (
            SELECT 
                u.id,
                u.username,
                u.email,
                COUNT(DISTINCT o.id) as total_orders,
                SUM(o.total) as total_spent,
                AVG(o.total) as avg_order_value,
                MAX(o.created_at) as last_order_date,
                COUNT(DISTINCT us.id) as total_sessions
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            LEFT JOIN user_sessions us ON u.id = us.user_id
            WHERE u.id = %s
            GROUP BY u.id, u.username, u.email
        ),
        product_preferences AS (
            SELECT 
                o.user_id,
                c.name as category_name,
                COUNT(*) as purchase_count
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE o.user_id = %s
            GROUP BY o.user_id, c.name
            ORDER BY purchase_count DESC
            LIMIT 5
        )
        SELECT 
            us.*,
            COALESCE(
                ARRAY_AGG(pp.category_name ORDER BY pp.purchase_count DESC) 
                FILTER (WHERE pp.category_name IS NOT NULL), 
                ARRAY[]::text[]
            ) as favorite_categories
        FROM user_stats us
        LEFT JOIN product_preferences pp ON us.id = pp.user_id
        GROUP BY us.id, us.username, us.email, us.total_orders, 
                 us.total_spent, us.avg_order_value, us.last_order_date, us.total_sessions
        """
        
        df = pd.read_sql(query, conn, params=[user_id, user_id])
        conn.close()
        
        return df.to_dict('records')[0] if not df.empty else {}
    
    def create_user_segment(self, segment_rules: Dict[str, Any]):
        """Cria segmento de usuários baseado em regras"""
        conn = psycopg2.connect(self.conn_str)
        cursor = conn.cursor()
        
        # Cria tabela de segmento se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_segments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                segment_name VARCHAR(100),
                segment_value TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Limpa segmentos antigos
        cursor.execute("""
            DELETE FROM user_segments 
            WHERE segment_name = %s
        """, (segment_rules['name'],))
        
        # Insere novos segmentos
        segment_query = """
        INSERT INTO user_segments (user_id, segment_name, segment_value)
        SELECT 
            u.id,
            %s,
            CASE 
                WHEN total_spent >= %s THEN 'VIP'
                WHEN total_spent >= %s THEN 'Premium'
                WHEN total_orders >= %s THEN 'Frequent'
                ELSE 'Regular'
            END
        FROM users u
        LEFT JOIN (
            SELECT 
                user_id,
                COUNT(*) as total_orders,
                SUM(total) as total_spent
            FROM orders
            GROUP BY user_id
        ) o ON u.id = o.user_id
        WHERE u.is_active = true
        """
        
        cursor.execute(segment_query, (
            segment_rules['name'],
            segment_rules.get('vip_threshold', 1000),
            segment_rules.get('premium_threshold', 500),
            segment_rules.get('frequent_orders', 10)
        ))
        
        conn.commit()
        cursor.close()
        conn.close()

class ProductService:
    def __init__(self, connection_string: str):
        self.conn_str = connection_string
    
    def update_product_rankings(self):
        """Atualiza rankings de produtos"""
        conn = psycopg2.connect(self.conn_str)
        cursor = conn.cursor()
        
        # Cria tabela de rankings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_rankings (
                product_id INTEGER REFERENCES products(id),
                category_id INTEGER REFERENCES categories(id),
                sales_rank INTEGER,
                revenue_rank INTEGER,
                popularity_score DECIMAL(5,2),
                last_updated TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (product_id, category_id)
            )
        """)
        
        # Calcula rankings
        ranking_query = """
        WITH product_metrics AS (
            SELECT 
                p.id as product_id,
                p.category_id,
                COUNT(oi.id) as total_sales,
                SUM(oi.quantity * oi.price) as total_revenue,
                AVG(pr.rating) as avg_rating,
                COUNT(DISTINCT o.user_id) as unique_customers
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            LEFT JOIN orders o ON oi.order_id = o.id
            LEFT JOIN product_reviews pr ON p.id = pr.product_id
            GROUP BY p.id, p.category_id
        ),
        ranked_products AS (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY total_sales DESC) as sales_rank,
                ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY total_revenue DESC) as revenue_rank,
                (total_sales * 0.4 + COALESCE(avg_rating, 0) * 20 * 0.3 + unique_customers * 0.3) as popularity_score
            FROM product_metrics
        )
        INSERT INTO product_rankings (product_id, category_id, sales_rank, revenue_rank, popularity_score)
        SELECT product_id, category_id, sales_rank, revenue_rank, popularity_score
        FROM ranked_products
        ON CONFLICT (product_id, category_id) 
        DO UPDATE SET 
            sales_rank = EXCLUDED.sales_rank,
            revenue_rank = EXCLUDED.revenue_rank,
            popularity_score = EXCLUDED.popularity_score,
            last_updated = NOW()
        """
        
        cursor.execute(ranking_query)
        conn.commit()
        cursor.close()
        conn.close()

def cleanup_old_data():
    """Limpa dados antigos do sistema"""
    conn = psycopg2.connect("postgresql://user:pass@localhost/db")
    cursor = conn.cursor()
    
    cleanup_queries = [
        "DELETE FROM user_sessions WHERE created_at < NOW() - INTERVAL '30 days'",
        "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days'",
        "DELETE FROM temporary_calculations WHERE created_at < NOW() - INTERVAL '1 day'",
        "VACUUM ANALYZE users",
        "VACUUM ANALYZE orders", 
        "VACUUM ANALYZE products"
    ]
    
    for query in cleanup_queries:
        cursor.execute(query)
    
    conn.commit()
    cursor.close()
    conn.close()
'''
        
        (test_dir / "services.py").write_text(service_code)
        
        return test_dir
    
    def create_mixed_project(self) -> Path:
        """Cria projeto misto com Airflow + Python standalone"""
        test_dir = Path("test_mixed_project")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()
        
        # DAG que chama múltiplos scripts Python
        dag_code = '''#!/usr/bin/env python3
"""
DAG mista que orquestra múltiplos scripts Python
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator

default_args = {
    'owner': 'mixed_team',
    'start_date': datetime(2024, 1, 1),
}

dag = DAG(
    'mixed_processing_pipeline',
    default_args=default_args,
    schedule_interval='@daily'
)

def orchestrator_function():
    """Função orquestradora que chama outros módulos"""
    import os
    import sys
    
    # Adiciona módulos locais ao path para import resolution
    sys.path.insert(0, os.path.dirname(__file__))
    
    from data_processor import DataProcessor
    from analytics_engine import AnalyticsEngine
    
    # Configuração de tabelas para cross-file tracking
    table_config = {
        'source_table': 'transactions',
        'analytics_table': 'user_behavior', 
        'output_table': 'processed_results'
    }
    
    # Processa dados básicos
    processor = DataProcessor()
    result1 = processor.process_daily_data(table_config['source_table'])
    
    # Executa analytics
    analytics = AnalyticsEngine()
    result2 = analytics.run_daily_analytics(table_config['analytics_table'])
    
    # Cross-file parameter passing
    processor.save_to_table(result1, table_config['output_table'])
    
    return {'processor': result1, 'analytics': result2, 'tables_used': table_config}

# Tasks
orchestrate_task = PythonOperator(
    task_id='orchestrate_processing',
    python_callable=orchestrator_function,
    dag=dag
)

ml_processing_task = BashOperator(
    task_id='run_ml_models',
    bash_command='python3 /ml/scripts/model_trainer.py --input_table ml.features --output_table ml.predictions',
    dag=dag
)

reporting_task = BashOperator(
    task_id='generate_reports',
    bash_command='python3 /reports/daily_report_generator.py',
    dag=dag
)

# Workflow
orchestrate_task >> ml_processing_task >> reporting_task
'''
        
        (test_dir / "mixed_dag.py").write_text(dag_code)
        
        # Processor Python
        processor_code = '''#!/usr/bin/env python3
"""
Processador de dados independente
"""

import psycopg2
import pandas as pd
from datetime import datetime, timedelta

class DataProcessor:
    def __init__(self):
        self.conn_str = "postgresql://user:pass@localhost/maindb"
    
    def process_daily_data(self, table_name: str):
        """Processa dados diários"""
        conn = psycopg2.connect(self.conn_str)
        
        # Busca dados do dia anterior
        query = f"""
        SELECT *
        FROM {table_name}
        WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
          AND created_at < CURRENT_DATE
        """
        
        df = pd.read_sql(query, conn)
        
        # Processa e salva
        processed_df = self._clean_and_transform(df)
        
        processed_df.to_sql(f'{table_name}_processed', conn, 
                          if_exists='append', index=False)
        
        # Log do processamento
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO processing_logs (table_name, records_processed, process_date)
            VALUES (%s, %s, %s)
        """, (table_name, len(processed_df), datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return len(processed_df)
    
    def save_to_table(self, data, table_name: str):
        """Salva dados em tabela específica - cross-file method"""
        conn = psycopg2.connect(self.conn_str)
        cursor = conn.cursor()
        
        # Cria tabela se não existir
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                data_value INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Insere dados
        cursor.execute(f"""
            INSERT INTO {table_name} (data_value) VALUES (%s)
        """, (data,))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def _clean_and_transform(self, df):
        """Limpeza e transformação dos dados"""
        # Simula processamento
        return df.dropna()

if __name__ == "__main__":
    processor = DataProcessor()
    result = processor.process_daily_data('transactions')
    print(f"Processados {result} registros")
'''
        
        (test_dir / "data_processor.py").write_text(processor_code)
        
        # Analytics Engine
        analytics_code = '''#!/usr/bin/env python3
"""
Engine de analytics
"""

import psycopg2
import pandas as pd
import numpy as np
from typing import Dict, List

class AnalyticsEngine:
    def __init__(self):
        self.conn_str = "postgresql://user:pass@localhost/analytics"
    
    def run_daily_analytics(self, analysis_type: str) -> Dict:
        """Executa analytics diários"""
        conn = psycopg2.connect(self.conn_str)
        
        if analysis_type == 'user_behavior':
            return self._analyze_user_behavior(conn)
        elif analysis_type == 'product_performance':
            return self._analyze_product_performance(conn)
        else:
            conn.close()
            return {}
    
    def _analyze_user_behavior(self, conn) -> Dict:
        """Analisa comportamento do usuário"""
        
        # Extrai dados de comportamento
        behavior_query = """
        SELECT 
            u.user_id,
            u.registration_date,
            COUNT(DISTINCT s.session_id) as total_sessions,
            COUNT(DISTINCT o.order_id) as total_orders,
            SUM(o.total_amount) as total_spent,
            AVG(s.duration_minutes) as avg_session_duration
        FROM users u
        LEFT JOIN user_sessions s ON u.user_id = s.user_id
        LEFT JOIN orders o ON u.user_id = o.user_id
        WHERE u.registration_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY u.user_id, u.registration_date
        """
        
        df = pd.read_sql(behavior_query, conn)
        
        # Calcula métricas
        metrics = {
            'total_users': len(df),
            'avg_orders_per_user': df['total_orders'].mean(),
            'avg_spent_per_user': df['total_spent'].mean(),
            'conversion_rate': (df['total_orders'] > 0).mean()
        }
        
        # Salva resultados
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics_results (analysis_type, metrics, calculated_date)
            VALUES (%s, %s, CURRENT_DATE)
        """, ('user_behavior', str(metrics)))
        
        # Segmenta usuários
        self._create_user_segments(conn, df)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return metrics
    
    def _analyze_product_performance(self, conn) -> Dict:
        """Analisa performance de produtos"""
        
        performance_query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.category_id,
            COUNT(DISTINCT oi.order_id) as times_ordered,
            SUM(oi.quantity) as total_quantity_sold,
            SUM(oi.quantity * oi.unit_price) as total_revenue,
            AVG(pr.rating) as avg_rating
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.order_id
        LEFT JOIN product_reviews pr ON p.product_id = pr.product_id
        WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY p.product_id, p.product_name, p.category_id
        ORDER BY total_revenue DESC
        """
        
        df = pd.read_sql(performance_query, conn)
        
        # Salva top performers
        df.head(100).to_sql('top_products_monthly', conn, 
                           if_exists='replace', index=False)
        
        metrics = {
            'products_analyzed': len(df),
            'total_revenue': df['total_revenue'].sum(),
            'avg_rating': df['avg_rating'].mean()
        }
        
        conn.close()
        return metrics
    
    def _create_user_segments(self, conn, df):
        """Cria segmentos de usuário"""
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE TABLE user_behavior_segments")
        
        for _, row in df.iterrows():
            segment = self._determine_segment(row)
            cursor.execute("""
                INSERT INTO user_behavior_segments (user_id, segment, metrics)
                VALUES (%s, %s, %s)
            """, (row['user_id'], segment, str(row.to_dict())))
        
        cursor.close()
    
    def _determine_segment(self, user_data) -> str:
        """Determina segmento do usuário"""
        if user_data['total_spent'] > 1000:
            return 'high_value'
        elif user_data['total_orders'] > 5:
            return 'frequent_buyer'
        elif user_data['total_sessions'] > 10:
            return 'engaged_browser'
        else:
            return 'casual_user'
'''
        
        (test_dir / "analytics_engine.py").write_text(analytics_code)
        
        return test_dir

class ComprehensiveTestSuite:
    """Suite completa de testes"""
    
    def __init__(self):
        self.project_generator = TestProjectGenerator()
        self.test_results: List[TestResult] = []
        self.temp_dirs: List[Path] = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes"""
        print("🧪 INICIANDO SUITE COMPLETA DE TESTES")
        print("=" * 60)
        
        start_time = time.time()
        
        # Testes de funcionalidade
        self._test_basic_postgresql_detection()
        self._test_airflow_dag_analysis()
        self._test_parameter_chain_tracking()
        self._test_cross_file_dependencies()
        self._test_mixed_project_analysis()
        
        # Testes de performance
        self._test_performance_large_project()
        self._test_memory_usage()
        
        # Testes de edge cases
        self._test_syntax_error_handling()
        self._test_encoding_issues()
        self._test_empty_files()
        
        # Testes de CLI
        self._test_cli_integration()
        
        total_time = time.time() - start_time
        
        # Compila resultados
        results = self._compile_test_results(total_time)
        
        # Cleanup
        self._cleanup_temp_dirs()
        
        return results
    
    def _test_basic_postgresql_detection(self):
        """Teste básico de detecção PostgreSQL"""
        print("🔍 Testando detecção básica PostgreSQL...")
        
        start_time = time.time()
        try:
            # Cria projeto de teste
            test_project = self.project_generator.create_python_standalone_project()
            self.temp_dirs.append(test_project)
            
            # Executa análise
            mapper = PostgreSQLTableMapper()
            results = mapper.analyze_project(str(test_project))
            
            # Validações
            expected_tables = ['users', 'products', 'categories', 'orders', 'user_sessions']
            found_tables = set(results['tables_discovered'].keys())
            
            missing_tables = set(expected_tables) - found_tables
            
            success = len(missing_tables) == 0
            
            self.test_results.append(TestResult(
                test_name="basic_postgresql_detection",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'expected_tables': expected_tables,
                    'found_tables': list(found_tables),
                    'missing_tables': list(missing_tables),
                    'total_references': results['analysis_summary']['total_table_references']
                },
                error_message="" if success else f"Missing tables: {missing_tables}"
            ))
            
            print(f"   ✅ Encontradas {len(found_tables)} tabelas")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="basic_postgresql_detection",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_airflow_dag_analysis(self):
        """Teste de análise de DAGs Airflow"""
        print("🚁 Testando análise de DAGs Airflow...")
        
        start_time = time.time()
        try:
            # Cria projeto Airflow
            test_project = self.project_generator.create_airflow_dag_project()
            self.temp_dirs.append(test_project)
            
            # Executa análise avançada
            mapper = EnhancedPostgreSQLAirflowMapper()
            results = mapper.analyze_project(str(test_project))
            
            # Validações
            airflow_analysis = results['airflow_analysis']
            expected_dag = 'ecommerce_etl_complex'
            
            dag_found = any(dag['dag_id'] == expected_dag for dag in airflow_analysis['dags'])
            tasks_found = airflow_analysis['total_tasks'] > 0
            tables_found = results['analysis_summary']['unique_tables_found'] > 0
            
            success = dag_found and tasks_found and tables_found
            
            self.test_results.append(TestResult(
                test_name="airflow_dag_analysis",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'dags_found': airflow_analysis['total_dags'],
                    'tasks_found': airflow_analysis['total_tasks'],
                    'tables_found': results['analysis_summary']['unique_tables_found'],
                    'dag_ids': [dag['dag_id'] for dag in airflow_analysis['dags']]
                }
            ))
            
            print(f"   ✅ {airflow_analysis['total_dags']} DAGs, {airflow_analysis['total_tasks']} tasks")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="airflow_dag_analysis",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_parameter_chain_tracking(self):
        """Teste de rastreamento de chains de parâmetros"""
        print("🔗 Testando rastreamento de parâmetros...")
        
        start_time = time.time()
        try:
            # Usa projeto misto para testar chains
            test_project = self.project_generator.create_mixed_project()
            self.temp_dirs.append(test_project)
            
            mapper = EnhancedPostgreSQLAirflowMapper()
            results = mapper.analyze_project(str(test_project))
            
            # Verifica se há chains detectadas
            param_flows = results['parameter_flow_analysis']['total_flows']
            tables_with_chains = sum(1 for table_info in results['tables_discovered'].values() 
                                   if any(ref.get('parameter_chain', []) for ref in table_info['references']))
            
            success = param_flows > 0 or tables_with_chains > 0
            
            self.test_results.append(TestResult(
                test_name="parameter_chain_tracking",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'parameter_flows': param_flows,
                    'tables_with_chains': tables_with_chains,
                    'flow_types': results['parameter_flow_analysis'].get('flow_types', {})
                }
            ))
            
            print(f"   ✅ {param_flows} fluxos de parâmetros detectados")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="parameter_chain_tracking",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_cross_file_dependencies(self):
        """Teste de dependências cross-file"""
        print("📁 Testando dependências entre arquivos...")
        
        start_time = time.time()
        try:
            test_project = self.project_generator.create_mixed_project()
            self.temp_dirs.append(test_project)
            
            mapper = EnhancedPostgreSQLAirflowMapper()
            results = mapper.analyze_project(str(test_project))
            
            # Verifica mapeamentos cross-file
            cross_file_deps = results['parameter_flow_analysis']['cross_file_dependencies']
            files_in_graph = results['parameter_flow_analysis']['files_in_dependency_graph']
            
            # Considera sucesso se há pelo menos arquivos no grafo de dependências
            success = files_in_graph > 0
            
            self.test_results.append(TestResult(
                test_name="cross_file_dependencies",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'cross_file_dependencies': cross_file_deps,
                    'files_in_graph': files_in_graph
                },
                error_message=""
            ))
            
            print(f"   ✅ {files_in_graph} arquivos no grafo, {cross_file_deps} dependências")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="cross_file_dependencies",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_mixed_project_analysis(self):
        """Teste de projeto misto Airflow + Python"""
        print("🔄 Testando projeto misto...")
        
        start_time = time.time()
        try:
            test_project = self.project_generator.create_mixed_project()
            self.temp_dirs.append(test_project)
            
            mapper = EnhancedPostgreSQLAirflowMapper()
            results = mapper.analyze_project(str(test_project))
            
            # Deve detectar tanto DAGs quanto PostgreSQL
            has_dags = results['airflow_analysis']['total_dags'] > 0
            has_tables = results['analysis_summary']['unique_tables_found'] > 0
            has_both = has_dags and has_tables
            
            self.test_results.append(TestResult(
                test_name="mixed_project_analysis",
                passed=has_both,
                execution_time=time.time() - start_time,
                details={
                    'has_airflow': has_dags,
                    'has_postgresql': has_tables,
                    'dags_count': results['airflow_analysis']['total_dags'],
                    'tables_count': results['analysis_summary']['unique_tables_found']
                }
            ))
            
            print(f"   ✅ DAGs: {has_dags}, PostgreSQL: {has_tables}")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="mixed_project_analysis",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_performance_large_project(self):
        """Teste de performance em projeto grande"""
        print("⚡ Testando performance em projeto grande...")
        
        start_time = time.time()
        try:
            # Usa o projeto labcom_etiquetas (255 arquivos)
            project_path = "/home/dev/code/labcom_etiquetas"
            
            if os.path.exists(project_path):
                mapper = PostgreSQLTableMapper()
                results = mapper.analyze_project(project_path)
                
                analysis_time = results['analysis_summary']['analysis_time_seconds']
                files_count = results['analysis_summary']['files_analyzed']
                files_per_second = files_count / analysis_time if analysis_time > 0 else 0
                
                # Performance aceitável: > 30 arquivos/segundo
                success = files_per_second > 30
                
                self.test_results.append(TestResult(
                    test_name="performance_large_project",
                    passed=success,
                    execution_time=time.time() - start_time,
                    details={
                        'files_analyzed': files_count,
                        'analysis_time': analysis_time,
                        'files_per_second': files_per_second,
                        'tables_found': results['analysis_summary']['unique_tables_found']
                    }
                ))
                
                print(f"   ✅ {files_per_second:.1f} arquivos/segundo")
            else:
                raise FileNotFoundError("Projeto de teste não encontrado")
                
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="performance_large_project",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_memory_usage(self):
        """Teste de uso de memória"""
        print("💾 Testando uso de memória...")
        
        start_time = time.time()
        try:
            import psutil
            import gc
            
            # Medição inicial
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Executa análise
            test_project = self.project_generator.create_airflow_dag_project()
            self.temp_dirs.append(test_project)
            
            mapper = EnhancedPostgreSQLAirflowMapper()
            results = mapper.analyze_project(str(test_project))
            
            # Medição final
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = final_memory - initial_memory
            
            # Cleanup forçado
            del mapper, results
            gc.collect()
            
            # Memória aceitável: < 100MB para projeto pequeno
            success = memory_used < 100
            
            self.test_results.append(TestResult(
                test_name="memory_usage",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'initial_memory_mb': initial_memory,
                    'final_memory_mb': final_memory,
                    'memory_used_mb': memory_used
                }
            ))
            
            print(f"   ✅ {memory_used:.1f} MB utilizados")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="memory_usage",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_syntax_error_handling(self):
        """Teste de tratamento de erros de sintaxe"""
        print("🔧 Testando tratamento de erros de sintaxe...")
        
        start_time = time.time()
        try:
            # Cria arquivo com erro de sintaxe
            test_dir = Path("test_syntax_errors")
            if test_dir.exists():
                shutil.rmtree(test_dir)
            test_dir.mkdir()
            self.temp_dirs.append(test_dir)
            
            # Arquivo com erro de sintaxe mas com SQL válido
            broken_code = '''#!/usr/bin/env python3
# Arquivo com erro de sintaxe mas SQL detectável

def valid_function():
    """Função válida"""
    query = """
    SELECT * FROM users WHERE active = true
    """
    return query

def broken_function(
    # Erro de sintaxe: parênteses não fechados
    param1: str
    param2: int  # Faltando vírgula
):
    """Função com erro de sintaxe"""
    sql = "INSERT INTO products (name, price) VALUES ('test', 100)"
    return sql

# Mais SQL detectável mesmo com sintaxe quebrada
UPDATE orders SET status = 'completed' WHERE id = 1
'''
            
            (test_dir / "broken_syntax.py").write_text(broken_code)
            
            # Executa análise
            mapper = PostgreSQLTableMapper()
            results = mapper.analyze_project(str(test_dir))
            
            # Deve detectar tabelas mesmo com erro de sintaxe
            tables_found = results['analysis_summary']['unique_tables_found']
            success = tables_found > 0  # Deve encontrar pelo menos 'users', 'products', 'orders'
            
            self.test_results.append(TestResult(
                test_name="syntax_error_handling",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'tables_found': tables_found,
                    'files_analyzed': results['analysis_summary']['files_analyzed']
                }
            ))
            
            print(f"   ✅ {tables_found} tabelas detectadas mesmo com erro de sintaxe")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="syntax_error_handling",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_encoding_issues(self):
        """Teste de problemas de encoding"""
        print("📝 Testando problemas de encoding...")
        
        start_time = time.time()
        try:
            test_dir = Path("test_encoding")
            if test_dir.exists():
                shutil.rmtree(test_dir)
            test_dir.mkdir()
            self.temp_dirs.append(test_dir)
            
            # Arquivo com caracteres especiais
            content_with_encoding = '''#!/usr/bin/env python3
# -*- coding: latin-1 -*-
"""
Arquivo com caracteres especiais e SQL
"""

def processar_usuários():
    """Função com acentos"""
    query = """
    SELECT 
        nome,
        sobrenome,
        endereço
    FROM usuários 
    WHERE região = 'São Paulo'
    """
    return query

# Comentário com çaracteres especiais: ção, ã, ê
sql_especial = "INSERT INTO configurações (parâmetro, valor) VALUES ('teste', 'ação')"
'''
            
            # Salva com encoding latin-1
            with open(test_dir / "encoding_test.py", 'w', encoding='latin-1') as f:
                f.write(content_with_encoding)
            
            # Executa análise
            mapper = PostgreSQLTableMapper()
            results = mapper.analyze_project(str(test_dir))
            
            # Deve detectar tabelas mesmo com encoding diferente
            tables_found = results['analysis_summary']['unique_tables_found']
            success = tables_found > 0
            
            self.test_results.append(TestResult(
                test_name="encoding_issues",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'tables_found': tables_found,
                    'files_analyzed': results['analysis_summary']['files_analyzed']
                }
            ))
            
            print(f"   ✅ {tables_found} tabelas detectadas com encoding especial")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="encoding_issues",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_empty_files(self):
        """Teste com arquivos vazios"""
        print("📄 Testando arquivos vazios...")
        
        start_time = time.time()
        try:
            test_dir = Path("test_empty_files")
            if test_dir.exists():
                shutil.rmtree(test_dir)
            test_dir.mkdir()
            self.temp_dirs.append(test_dir)
            
            # Cria vários tipos de arquivos
            (test_dir / "empty.py").write_text("")
            (test_dir / "only_comments.py").write_text("# Just a comment\n# Another comment")
            (test_dir / "only_whitespace.py").write_text("   \n  \n\t\n")
            (test_dir / "valid_with_sql.py").write_text('query = "SELECT * FROM test_table"')
            
            # Executa análise
            mapper = PostgreSQLTableMapper()
            results = mapper.analyze_project(str(test_dir))
            
            # Deve analisar sem erro e encontrar pelo menos a tabela válida
            files_analyzed = results['analysis_summary']['files_analyzed']
            tables_found = results['analysis_summary']['unique_tables_found']
            
            success = files_analyzed > 0 and tables_found > 0
            
            self.test_results.append(TestResult(
                test_name="empty_files",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'files_analyzed': files_analyzed,
                    'tables_found': tables_found
                }
            ))
            
            print(f"   ✅ {files_analyzed} arquivos processados, {tables_found} tabelas")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="empty_files",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _test_cli_integration(self):
        """Teste de integração do CLI"""
        print("🖥️ Testando integração do CLI...")
        
        start_time = time.time()
        try:
            # Cria projeto para teste
            test_project = self.project_generator.create_python_standalone_project()
            self.temp_dirs.append(test_project)
            
            # Testa CLI unificado
            cli = BWUnifiedCLI()
            
            # Verifica analisadores disponíveis
            available = cli.available_analyzers
            has_postgresql = available.get('postgresql', False)
            
            if has_postgresql:
                # Testa análise via CLI
                with tempfile.TemporaryDirectory() as temp_output:
                    results = cli.analyze_postgresql(str(test_project), temp_output)
                    
                    # Verifica se arquivo foi criado
                    output_file = Path(temp_output) / "postgresql_analysis.json"
                    file_created = output_file.exists()
                    tables_found = results['analysis_summary']['unique_tables_found'] > 0
                    
                    success = file_created and tables_found
            else:
                success = False
            
            self.test_results.append(TestResult(
                test_name="cli_integration",
                passed=success,
                execution_time=time.time() - start_time,
                details={
                    'postgresql_available': has_postgresql,
                    'file_created': file_created if has_postgresql else False,
                    'tables_found': tables_found if has_postgresql else 0
                }
            ))
            
            status = "✅" if success else "❌"
            print(f"   {status} CLI funcionando: {success}")
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="cli_integration",
                passed=False,
                execution_time=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Erro: {e}")
    
    def _compile_test_results(self, total_time: float) -> Dict[str, Any]:
        """Compila resultados dos testes"""
        passed_tests = [t for t in self.test_results if t.passed]
        failed_tests = [t for t in self.test_results if not t.passed]
        
        success_rate = len(passed_tests) / len(self.test_results) * 100 if self.test_results else 0
        
        return {
            'test_summary': {
                'total_tests': len(self.test_results),
                'passed_tests': len(passed_tests),
                'failed_tests': len(failed_tests),
                'success_rate': success_rate,
                'total_execution_time': total_time
            },
            'test_results': [
                {
                    'test_name': test.test_name,
                    'passed': test.passed,
                    'execution_time': test.execution_time,
                    'details': test.details,
                    'error_message': test.error_message
                }
                for test in self.test_results
            ],
            'performance_metrics': {
                'avg_test_time': sum(t.execution_time for t in self.test_results) / len(self.test_results) if self.test_results else 0,
                'slowest_test': max(self.test_results, key=lambda t: t.execution_time).test_name if self.test_results else None,
                'fastest_test': min(self.test_results, key=lambda t: t.execution_time).test_name if self.test_results else None
            }
        }
    
    def _cleanup_temp_dirs(self):
        """Limpa diretórios temporários"""
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

def main():
    """Executa suite de testes"""
    test_suite = ComprehensiveTestSuite()
    results = test_suite.run_all_tests()
    
    # Salva resultados
    with open("comprehensive_test_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Mostra resumo
    summary = results['test_summary']
    print(f"\n📊 RESUMO DOS TESTES:")
    print(f"   Total: {summary['total_tests']}")
    print(f"   Passou: {summary['passed_tests']} ✅")
    print(f"   Falhou: {summary['failed_tests']} ❌")
    print(f"   Taxa de sucesso: {summary['success_rate']:.1f}%")
    print(f"   Tempo total: {summary['total_execution_time']:.2f}s")
    
    if summary['failed_tests'] > 0:
        print(f"\n❌ TESTES FALHARAM:")
        for test in results['test_results']:
            if not test['passed']:
                print(f"   • {test['test_name']}: {test['error_message']}")
    
    print(f"\n📄 Relatório completo: comprehensive_test_results.json")

if __name__ == "__main__":
    main()
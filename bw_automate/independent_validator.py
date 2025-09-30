#!/usr/bin/env python3
"""
VALIDADOR INDEPENDENTE - Verificação Real Life
Valida se o PostgreSQL Table Mapper detectou REALMENTE todas as tabelas
SEM aceitar resultados chumbados ou mockados
"""

import json
import re

def extract_real_tables_manual():
    """Extração MANUAL das tabelas reais do arquivo real_world_validation.py"""
    
    # TABELAS REAIS que DEVEM ser detectadas (análise manual do código)
    expected_tables = {
        # Django Models REAIS
        'auth_users': {
            'source': 'Django Meta db_table',
            'line_approx': 14,
            'context': 'class User(AbstractUser) -> Meta.db_table'
        },
        'customers_data': {
            'source': 'Django Meta db_table', 
            'line_approx': 22,
            'context': 'class Customer(models.Model) -> Meta.db_table'
        },
        
        # SQLAlchemy REAIS
        'products_catalog': {
            'source': 'SQLAlchemy __tablename__',
            'line_approx': 32,
            'context': 'class Product(Base) -> __tablename__'
        },
        'orders_history': {
            'source': 'SQLAlchemy __tablename__',
            'line_approx': 39,
            'context': 'class Order(Base) -> __tablename__'
        },
        
        # SQL Queries REAIS
        'order_items': {
            'source': 'SQL JOIN real',
            'line_approx': 49,
            'context': 'JOIN order_items oi ON...'
        },
        'sales_transactions': {
            'source': 'SQL query analytics',
            'line_approx': 65,
            'context': 'FROM sales_transactions WHERE...'
        },
        
        # Airflow REAL
        'staging_raw_data': {
            'source': 'Airflow PostgresOperator',
            'line_approx': 95,
            'context': 'INSERT INTO staging_raw_data SELECT...'
        },
        'source_transactions': {
            'source': 'Airflow PostgresOperator',
            'line_approx': 95,
            'context': 'SELECT * FROM source_transactions...'
        },
        'processed_analytics': {
            'source': 'Airflow PostgresOperator',
            'line_approx': 107,
            'context': 'INSERT INTO processed_analytics SELECT...'
        },
        
        # F-strings dinâmicos REAIS
        'monthly_reports_': {  # Nome dinâmico com prefixo
            'source': 'F-string dinâmico real',
            'line_approx': 130,
            'context': 'f"monthly_reports_{current_month}"',
            'dynamic': True
        },
        
        # Loop REAL com múltiplas tabelas
        'users_profile': {
            'source': 'Loop backup real',
            'line_approx': 142,
            'context': 'for table in tables_to_backup'
        },
        'audit_logs': {
            'source': 'Loop backup real', 
            'line_approx': 147,
            'context': 'for table in tables_to_backup'
        },
        
        # Configuração REAL
        'user_accounts': {
            'source': 'Configuração dicionário',
            'line_approx': 166,
            'context': "DATABASE_CONFIG['production']['tables']['users']"
        },
        'order_records': {
            'source': 'Configuração dicionário',
            'line_approx': 167,
            'context': "DATABASE_CONFIG['production']['tables']['orders']"
        },
        'product_inventory': {
            'source': 'Configuração dicionário',
            'line_approx': 168,
            'context': "DATABASE_CONFIG['production']['tables']['products']"
        },
        'application_logs': {
            'source': 'Configuração dicionário',
            'line_approx': 169,
            'context': "DATABASE_CONFIG['production']['tables']['logs']"
        },
        'staging_users': {
            'source': 'Configuração staging',
            'line_approx': 176,
            'context': "DATABASE_CONFIG['staging']['tables']['users']"
        },
        'staging_orders': {
            'source': 'Configuração staging',
            'line_approx': 177,
            'context': "DATABASE_CONFIG['staging']['tables']['orders']"
        },
        'staging_products': {
            'source': 'Configuração staging',
            'line_approx': 178,
            'context': "DATABASE_CONFIG['staging']['tables']['products']"
        },
        
        # CTEs e queries complexas REAIS
        'customer_profiles': {
            'source': 'CTE complexo real',
            'line_approx': 195,
            'context': 'WITH customer_metrics AS (SELECT ... FROM customer_profiles'
        },
        'order_transactions': {
            'source': 'CTE e múltiplas referências',
            'line_approx': 196,
            'context': 'Múltiplas referências em CTEs'
        },
        'purchase_patterns': {
            'source': 'CTE aninhado',
            'line_approx': 204,
            'context': 'purchase_patterns AS (SELECT...'
        },
        
        # Migrations REAIS
        'user_notifications': {
            'source': 'CREATE TABLE real',
            'line_approx': 224,
            'context': 'CREATE TABLE IF NOT EXISTS user_notifications'
        },
        'user_preferences': {
            'source': 'CREATE TABLE real',
            'line_approx': 236,
            'context': 'CREATE TABLE IF NOT EXISTS user_preferences'
        },
        
        # Auditoria REAL
        'audit_trail': {
            'source': 'INSERT auditoria real',
            'line_approx': 264,
            'context': 'INSERT INTO audit_trail (...) VALUES'
        }
    }
    
    return expected_tables

def load_mapper_results():
    """Carrega os resultados do mapeador"""
    try:
        with open('/home/dev/code/bw_automate/postgresql_ultimate_map.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Arquivo de resultados não encontrado!")
        return None

def validate_detection_accuracy():
    """Validação RIGOROSA da detecção sem aceitar chumbados"""
    
    print("🔍 VALIDADOR INDEPENDENTE - VERIFICAÇÃO REAL LIFE")
    print("=" * 60)
    
    # Carrega tabelas esperadas (análise manual)
    expected_tables = extract_real_tables_manual()
    print(f"📋 Tabelas REAIS esperadas: {len(expected_tables)}")
    
    # Carrega resultados do mapeador
    mapper_results = load_mapper_results()
    if not mapper_results:
        return False
    
    detected_tables = mapper_results.get('tables_discovered', {})
    print(f"🔍 Tabelas detectadas pelo mapeador: {len(detected_tables)}")
    
    # VALIDAÇÃO RIGOROSA
    true_positives = 0
    false_negatives = []
    false_positives = []
    
    print("\n🎯 ANÁLISE DETALHADA:")
    print("-" * 40)
    
    # Verifica cada tabela esperada
    for expected_table, details in expected_tables.items():
        found = False
        
        # Busca exata
        if expected_table in detected_tables:
            found = True
            true_positives += 1
            print(f"✅ {expected_table} - DETECTADO CORRETAMENTE")
            print(f"    Fonte: {details['source']}")
            
        # Busca por padrão (para tabelas dinâmicas)
        elif details.get('dynamic', False):
            for detected_name in detected_tables.keys():
                if expected_table.rstrip('_') in detected_name:
                    found = True
                    true_positives += 1
                    print(f"✅ {expected_table} -> {detected_name} - DETECTADO (dinâmico)")
                    print(f"    Fonte: {details['source']}")
                    break
        
        if not found:
            false_negatives.append(expected_table)
            print(f"❌ {expected_table} - NÃO DETECTADO")
            print(f"    Fonte: {details['source']}")
            print(f"    Linha: ~{details['line_approx']}")
    
    # Verifica falsos positivos (tabelas detectadas que não existem)
    print(f"\n🔍 VERIFICAÇÃO DE FALSOS POSITIVOS:")
    print("-" * 40)
    
    suspicious_detections = []
    for detected_table in detected_tables.keys():
        is_valid = False
        
        # Verifica se é uma tabela esperada
        if detected_table in expected_tables:
            is_valid = True
        
        # Verifica se é variação dinâmica válida
        for expected_table in expected_tables.keys():
            if expected_table.rstrip('_') in detected_table:
                is_valid = True
                break
        
        # Casos especiais válidos
        valid_special_cases = [
            'daily_transactions',  # Usado em query analytics
            'backup_',  # Padrão de backup (dinâmico)
            'monthly_reports_',  # F-string dinâmico
        ]
        
        for special_case in valid_special_cases:
            if special_case in detected_table:
                is_valid = True
                break
        
        if not is_valid:
            suspicious_detections.append(detected_table)
            print(f"⚠️ {detected_table} - POSSÍVEL FALSO POSITIVO")
            
            # Mostra contexto da detecção
            table_data = detected_tables[detected_table]
            for ref in table_data.get('references', []):
                print(f"    Linha {ref.get('line', '?')}: {ref.get('raw_content', 'N/A')[:100]}...")
    
    # CÁLCULO DE MÉTRICAS REAIS
    print(f"\n📊 MÉTRICAS REAIS (SEM CHUMBADAS):")
    print("=" * 40)
    
    total_expected = len(expected_tables)
    total_detected = len(detected_tables)
    
    # Precision = True Positives / (True Positives + False Positives)
    precision = true_positives / total_detected if total_detected > 0 else 0
    
    # Recall = True Positives / (True Positives + False Negatives)  
    recall = true_positives / total_expected if total_expected > 0 else 0
    
    # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"📈 True Positives: {true_positives}")
    print(f"📉 False Negatives: {len(false_negatives)}")
    print(f"⚠️ Suspeitos (Falsos Positivos): {len(suspicious_detections)}")
    print(f"")
    print(f"🎯 PRECISION: {precision:.1%} ({true_positives}/{total_detected})")
    print(f"🎯 RECALL: {recall:.1%} ({true_positives}/{total_expected})")
    print(f"🎯 F1-SCORE: {f1_score:.1%}")
    
    # VEREDICTO FINAL
    print(f"\n🏆 VEREDICTO FINAL:")
    print("=" * 30)
    
    if f1_score >= 0.95:
        print("✅ SISTEMA EXCELENTE - 95%+ de eficiência real")
    elif f1_score >= 0.85:
        print("✅ SISTEMA BOM - 85%+ de eficiência real")
    elif f1_score >= 0.70:
        print("⚠️ SISTEMA ACEITÁVEL - 70%+ de eficiência real")
    else:
        print("❌ SISTEMA PROBLEMÁTICO - <70% de eficiência real")
    
    # Detalhes dos problemas
    if false_negatives:
        print(f"\n❌ TABELAS NÃO DETECTADAS ({len(false_negatives)}):")
        for table in false_negatives:
            details = expected_tables[table]
            print(f"   • {table} - {details['source']}")
    
    if suspicious_detections:
        print(f"\n⚠️ DETECÇÕES SUSPEITAS ({len(suspicious_detections)}):")
        for table in suspicious_detections:
            print(f"   • {table}")
    
    return {
        'precision': precision,
        'recall': recall, 
        'f1_score': f1_score,
        'true_positives': true_positives,
        'false_negatives': false_negatives,
        'suspicious_detections': suspicious_detections,
        'is_100_percent_claim_valid': f1_score >= 0.99
    }

if __name__ == "__main__":
    result = validate_detection_accuracy()
    
    print(f"\n🎯 CONCLUSÃO: A afirmação de '100% eficiência' é {'' if result['is_100_percent_claim_valid'] else 'NÃO '}VÁLIDA")
    print(f"📊 Eficiência REAL medida: {result['f1_score']:.1%}")
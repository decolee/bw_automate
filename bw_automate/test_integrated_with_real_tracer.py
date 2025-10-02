#!/usr/bin/env python3
"""
Teste da integração completa com Real Call Chain Tracer
"""

from integrated_analyzer import IntegratedAnalyzer
import pandas as pd
import os

# Cria tabelas oficiais de exemplo
os.makedirs("test_output", exist_ok=True)

# Cria Excel com tabelas oficiais
tables_data = {
    'table_name': [
        'fx_symbol_master',
        'equity_master',
        'real_orders_table',
        'symbols',
        'historical_prices'
    ],
    'schema': [
        'staging',
        'public',
        'public',
        'crypto',
        'analytics'
    ]
}

df = pd.DataFrame(tables_data)
df.to_excel('test_output/official_tables.xlsx', index=False)

print("📊 Tabelas oficiais criadas")
print(df)
print()

# Executa análise integrada
print("="*80)
print("🚀 INICIANDO ANÁLISE INTEGRADA COM REAL TRACER")
print("="*80)

analyzer = IntegratedAnalyzer()
results = analyzer.analyze_repository(
    source_dir='test_real_scenario',
    tables_xlsx='test_output/official_tables.xlsx',
    output_dir='test_output'
)

print("\n" + "="*80)
print("📊 RESUMO DOS RESULTADOS")
print("="*80)
print(f"Total de arquivos: {results['summary']['total_files']}")
print(f"Total de tabelas encontradas: {results['summary']['total_tables_found']}")
print(f"Tabelas matched: {results['summary']['matched_tables']}")
print(f"Match rate: {results['summary']['match_rate']:.1f}%")
print(f"Confiança média: {results['summary']['avg_confidence']:.1f}%")
print(f"Call chains (deep): {results['summary']['deep_call_chains']}")
print(f"Descobertas (real tracer): {results['summary']['real_tracer_discoveries']}")

print("\n✅ Teste concluído!")

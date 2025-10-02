"""
Getters - Aqui é onde FINALMENTE chegamos nas tabelas reais!
"""

import pandas as pd

def get_table_data(table_name):
    """
    Aqui está a tabela REAL no SQL!
    """
    query = f"""
    SELECT * FROM public.real_orders_table
    WHERE status = 'active'
    """
    return pd.read_sql(query, connection)


def fetch_symbol_data(symbol_key):
    """
    Outra função que tem a tabela REAL
    """
    # Mapeamento de chaves para tabelas reais
    table_mapping = {
        "fx_symbols": "staging.fx_symbol_master",
        "equity_symbols": "public.equity_master",
        "crypto": "crypto.symbols"
    }

    real_table = table_mapping.get(symbol_key, "public.default_symbols")

    query = f"""
    SELECT symbol_id, symbol_name, market
    FROM {real_table}
    WHERE active = true
    """

    return pd.read_sql(query, connection)


def get_historical_data(table_key):
    """Mais uma função com SQL direto"""
    sql = """
    SELECT h.date, h.price, s.symbol_name
    FROM analytics.historical_prices h
    JOIN staging.fx_symbol_master s ON h.symbol_id = s.id
    WHERE h.date >= CURRENT_DATE - INTERVAL '30 days'
    """
    return pd.read_sql(sql, conn)

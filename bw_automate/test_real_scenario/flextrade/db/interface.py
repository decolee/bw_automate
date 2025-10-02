"""
DBInterface - Interface intermediária que chama getters
"""

from flextrade.db.utils.getters import get_table_data, fetch_symbol_data

class DBInterface:
    def __init__(self):
        self.connection = None

    def get(self, table_key):
        """
        Método get que recebe uma chave e chama funções específicas
        """
        if table_key == "fx_symbols":
            # Aqui chama outra função importada
            return get_symbol_data(table_key)
        elif table_key == "orders_table":
            return get_table_data(table_key)
        else:
            return fetch_symbol_data(table_key)

def get_symbol_data(key):
    """Wrapper que chama fetch"""
    from flextrade.db.utils.getters import fetch_symbol_data
    return fetch_symbol_data(key)

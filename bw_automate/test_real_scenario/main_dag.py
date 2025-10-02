"""
Exemplo REAL - Arquivo principal que usa DBInterface
"""

from flextrade.db import DBInterface

class DataProcessor:
    def __init__(self):
        self._db_interface = DBInterface()

    def get_fx_data(self):
        # Aqui só vemos o método get() com string "fx_symbols"
        # Precisamos rastrear até a tabela real!
        result = self._db_interface.get("fx_symbols")
        return result

    def process_orders(self):
        # Outro exemplo
        orders = self._db_interface.get("orders_table")
        return orders

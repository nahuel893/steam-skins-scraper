from src.data import DataInventory
"""
    TO-DO:
        * Agregar historial de precios en el tablero
        * Agregar funcionalidad para obtener el inventario de N usuarios
        * Separar desgaste de los nombres
        * Quitar columnas innecesarias
        * 
"""

steamid = "76561198102151621"

data_inventory = DataInventory(steamid)
data_inventory.transform_data()

data_inventory.show_data()
data_inventory.to_excel()
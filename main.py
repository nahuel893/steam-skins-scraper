
from src.datasources import SkinspockAPI

"""
    TO-DO:
        * Inicializar el proyecto en git y subirlo a github
        * Crear un README.md
        * Agregar historial de precios en el tablero 
        * Agregar funcionalidad para obtener el inventario de N usuarios
        * Separar desgaste de los nombres
        * Quitar columnas innecesarias
        * 
"""

steamid = "76561197961106934"

skinspock = SkinspockAPI(steamid)
skinspock.get_inventory(excel=True)
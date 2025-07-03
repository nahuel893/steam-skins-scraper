import pandas as pd
import os
import json
from typing import Any
from src.datasources import SkinspockAPI

class DataInventory:
    """
    Clase para transformar datos y exportarlos a diferentes formatos (por ejemplo, Excel).
    """
    def __init__(self, steamid) -> None:
        self.steamid = steamid
        self.skinspock = SkinspockAPI(steamid)
        self.data = self.skinspock.get_inventory()
        self.bloat_columns = self.skinspock.get_bloat_columns()

        # Convert list to string and then to JSON, then to DataFrame
        self.data = json.dumps(self.data)
        self.data = json.loads(self.data)
        self.df = pd.DataFrame(self.data)

        self.price_date_name = "priceupdatedat"

    def export_to_excel(self, filepath: str = "data.xlsx") -> None:
        """
        Exporta los datos a un archivo Excel en la ruta especificada.
        """
        self.df.to_excel(filepath, index=False)


    def delete_bloat_columns(self) -> None:
        """
        Elimina columnas innecesarias del DataFrame.
        """
        self.df.drop(columns=self.bloat_columns, inplace=True, errors='ignore')

    def transform_data(self) -> None:
        """
        Realiza transformaciones adicionales en los datos.
        """
        self.delete_bloat_columns()
        print(self.df[self.price_date_name])  # type: ignore

    def show_data(self) -> None:
        """
        Muestra los datos en la consola.
        """
        print(self.df.head())
        print(self.df.columns)

    def to_excel(self) -> None:
        """
        Exporta los datos a un archivo Excel.
        """
        self.df.to_excel(r"../data/skinspock.xlsx", index=False)  
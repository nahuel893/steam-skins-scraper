"""
Module for managing and transforming data from the various Steam skin APIs...
"""

import pandas as pd
import os
import json
from typing import Any
from scrapers.skinspock import SkinspockAPI
from scrapers.steam import SteamAPIMarket

class DataInventory:
    """
    Clase dedicada a la limpieza y transformacion de los datos obtenidos de las API de Skinspock.
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
        """
        self.df.to_excel(r"../data/skinspock.xlsx", index=False)



class DataPriceHistory:

    def __init__(self, appid: int=730) -> None:
        self.appid = appid
        self.steam = SteamAPIMarket(appid)
        
    def get_price_history(self) -> Any:
        pass

    def transform_steam(self) -> Any:
        """
        Transforma el historial de precios obtenido de la API de Steam.
        """
        self.steam.get_price_history(self.appid)



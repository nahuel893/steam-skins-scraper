import requests
import os

import pandas as pd
import json


class SkinspockAPI:
    """
    A class to interact with the Skinpock API for retrieving user inventory data.
    This class provides methods to fetch the inventory of a specified Steam user.
    """

    def __init__(self, steamid: str):	
        """
        Initializes the data source for interacting with the Skinpock API.
        Args:
            steamid (str): The Steam ID of the user whose inventory will be accessed.
        Attributes:
            steamid (str): The Steam ID of the user.
            __base_url (str): The base URL for the Skinpock API.
            __session (requests.Session): A session object for making HTTP requests.
            params (dict): Parameters for the API request, including Steam ID, sorting options, game, and language.
            headers (dict): Headers for the API request, including Accept, User-Agent, Referer, Accept-Language, and API keys.
        """
        
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")
        self.SRC_DIR = os.path.join(self.BASE_DIR, "src")

        # Load API key from a file
        apikey_path = os.path.join(self.DATA_DIR, "apikey.txt")
        with open(apikey_path, "r") as file:
            self.apikey = file.read().strip()

        self.steamid = steamid
        self.__base_url_inventory = "https://www.skinpock.com/api/inventory"
        self.__session = requests.Session()
        self.data = None

        self.bloat_columns = [
            "markethashname",
            "inspectlink",
            # "pricelatestsell24h",
            # "pricelatestsell7d",
            # "pricelatestsell30d",
            # "pricelatestsell90d",
            # "pricereal",
            # "pricereal24h",
            # "pricereal7d",
            # "pricereal30d",
            # "pricereal90d"
        ]

        self.params = {
            "steam_id": self.steamid,
            "sort":      "price_max",
            "game":      "cs2",
            "language":  "english"
        }
        self.headers = {# type: ignore
            "Accept":          "application/json, text/plain, */*",
            "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                            "AppleWebKit/537.36 (KHTML, like Gecko) " \
                            "Chrome/135.0.0.0 Safari/537.36",
            "Referer":         f"https://www.skinpock.com/es/inventory/{self.steamid}",
            "Accept-Language": "es-ES,es;q=0.9",
            "Apikeys":  self.apikey
        } 

    def get_inventory(self, steamid: str = "") -> list[str]:
        """
        Returns a DataFrame containing the inventory of the specified Steam user.
        Args:
            steamid (str): The Steam ID of the user whose inventory will be accessed.
        Attributes:
        """
        if steamid != "":
            self.steamid = steamid
            self.params["steam_id"] = steamid

        try:
            response = self.__session.get(self.__base_url_inventory, params=self.params, headers=self.headers)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()
            return data
        
        except requests.exceptions.RequestException as e:
            print("Error:", e)
            return None
        

    def get_bloat_columns(self) -> list[str]:
        return self.bloat_columns


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


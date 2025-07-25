import requests
import os
from dotenv import load_dotenv  # type: ignore
import json

import re
from urllib.parse import quote
load_dotenv()

# Define paths for the project
"""
    TO-DO:
        * Quitar doble creacion de variables BASE_DIR, DATA_DIR y SRC_DIR
        * Quitar exportacion a excel, mover a otra clase
"""

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


class SkinSniperAPI:
    """
    A class to interact with the SkinSniper API for retrieving skin pricing data.
    This class provides methods to fetch pricing data for all CS2 skins.
    """

    def __init__(self):
        """
        Initializes the data source for interacting with the SkinSniper API.
        Attributes:
            __base_url (str): The base URL for the SkinSniper API.
            __session (requests.Session): A session object for making HTTP requests.
            headers (dict): Headers for the API request, including Accept, User-Agent, and API keys.
        """
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")
        self.SRC_DIR = os.path.join(self.BASE_DIR, "src")

        self.__base_url = "https://skins-backend.skinsniper.com/api/v1/item/skin"
        self.__session = requests.Session()
        
        self.params = {
            "itemName": "M4A1-S",
            "page": 1,
            "limit": 9999,
            "orderBy": "rarity,DESC",
            "type": "skin",
            "availability": "",
            "primaryColor": ""
        }
        
        self.headers = {

        }

    def get_skin_prices(self, excel:bool=False):
        """
        Fetches pricing data for all CS2 skins.
        Args:
            excel (bool): If True, saves the data to an Excel file.
        Returns:
            pd.DataFrame: A DataFrame containing the pricing data for all CS2 skins.
        """
        try:
            response = self.__session.get(self.__base_url, headers=self.headers)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()
            data = data.to_string()

            return data.__str__()
        except requests.exceptions.RequestException as e:
            print("Error:", e)
            return None


class SteamAPIMarket:
    """
    Class for collecting CS2 skin price data using the public (unofficial) Steam Market API.
    This class interacts with the same endpoints used by the Steam Market web interface,
    not an official or documented Steam API.
    """

    def __init__(self, appid: int = 730, currency: int = 1, user_agent: str = None):
        """
        Initializes the client with appid (default 730 for CS:GO/CS2) and currency (1=USD).
        You can specify a custom User-Agent.
        """
        self.appid = appid
        self.currency = currency
        self.base_price_url = "https://steamcommunity.com/market/priceoverview/"
        self.base_history_url = "https://steamcommunity.com/market/pricehistory/"
        self.base_history_url_alt = "https://steamcommunity.com/market/listings/"
        self.session = requests.Session()
        ua = user_agent or 'Mozilla/5.0 (compatible; DataSteamMarket/1.0)'
        self.session.headers.update({'User-Agent': ua})

    def get_price_overview(self, market_hash_name: str) -> dict:
        """
        Gets the current price and volume for an item.

        :param market_hash_name: Encoded item name, e.g. "AK-47 | Redline (Field-Tested)"
        :return: Dictionary with keys: success, lowest_price, median_price, volume
        """
        params = {
            'appid': self.appid,
            'currency': self.currency,
            'market_hash_name': market_hash_name
        }

        resp = self.session.get(self.base_price_url, params=params)
        
        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise ValueError(f"Error al decodificar JSON para '{market_hash_name}': {resp.text}")
        except ValueError:
            raise ValueError(f"Respuesta inesperada al obtener precio overview para '{market_hash_name}': {resp.text}")
        
        if not data.get('success', False):
            raise ValueError(f"Error al obtener precio overview para '{market_hash_name}'")
        return data

    def get_price_history(self, market_hash_name: str):
        """
        Gets the price history for an item.

        :param market_hash_name: Encoded item name
        :return: Json (timestamp_ms, price_str)

        Test URL:
        https://steamcommunity.com/market/pricehistory/?appid=730&market_hash_name=AK-47%20|%20Redline%20(Field-Tested)
        gpt: https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Redline%20%28Field-Tested%29
        steam: https://steamcommunity.com/market/listings/730/AK-47+%7C+Redline+%28Field-Tested%29
        """
        params = {
            'appid': self.appid,
            'market_hash_name': market_hash_name
        }
        print(params)
        print("quote:" + f"{quote(params['market_hash_name'])}")
        url = f"{self.base_history_url_alt}{self.appid}/{quote(params['market_hash_name'])}"
        print("url: " + url)
        # Generamos la request a la URL de historial de precios
        resp = requests.get(url)

        if resp.status_code == 200:
            # DEBUG: Save HTML for inspection
            # output_path = os.path.join("/run/media/nahuel/SSD WD GREEN/Proyectos/steam-skin-scraper/data/", f"{market_hash_name}_price_history.html")
            # with open(output_path, "w", encoding="utf-8") as f:
            #     f.write(resp.text)

            # Find the JSON array in the HTML response
            match = re.search(r'var line1=(\[.*?\]);', resp.text, re.S)
            print(f"match: {match}")

            # Convert matched JSON string to Python object
            if match:

                raw_json = match.group(1)  # Contenido del array
                price_history = json.loads(raw_json)
                print(f"Se encontraron {len(price_history)} puntos de historial")
                print(price_history[:5])  # Muestra los primeros 5

            else:
                print("No se encontró el historial en el HTML")
            return price_history
        
        else:
            print(f"Error al obtener historial de precios para '{market_hash_name}': {resp.status_code}")          
            return None
    

if __name__ == '__main__':
    # Usage of SkinspockAPI to get inventory data
    # steamid = "76561198102151621"
    # api = SkinspockAPI(steamid)
    # inventory_data = api.get_inventory()

    # Usage of Steam Market API to get price overview and history
    client = SteamAPIMarket(currency=1)
    item = "AK-47 | Redline (Field-Tested)"

    overview = client.get_price_overview(item)
    print(f"Overview for {item}:")
    print(f"Median price: {overview['median_price']}, Volume: {overview['volume']}")
    if 'lowest_price' in overview:
        print(f"Lowest price: {overview['lowest_price']}")

    history = client.get_price_history(item)
    print(history)

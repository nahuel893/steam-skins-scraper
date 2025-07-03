import requests
import os
from dotenv import load_dotenv  # type: ignore


load_dotenv()

# Define paths for the project
"""
    TO-DO:
        * Quitar doble creacion de variables BASE_DIR, DATA_DIR y SRC_DIR\
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
        with open(r"./data/apikey.txt", "r") as file:
            self.apikey = file.read().strip()

        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")
        self.SRC_DIR = os.path.join(self.BASE_DIR, "src")
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


if __name__ == "__main__":
    #Example usage
    steamid = "76561198102151621"
    api = SkinspockAPI(steamid)
    inventory_data = api.get_inventory()
    #print(inventory_data)

    # sniper_api = SkinSniperAPI()
    # sniper_data = sniper_api.get_skin_prices(excel=True)
    # print(sniper_data)
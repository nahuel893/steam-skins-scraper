import requests
import os

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



import requests
from dotenv import load_dotenv  # type: ignore
import json
import re
from urllib.parse import quote
load_dotenv()


class SteamAPIMarket:
    """
    Class for collecting CS2 skin price data using the public (unofficial) Steam Market API.
    This class interacts with the same endpoints used by the Steam Market web interface,
    not an official or documented Steam API.
    """

    def __init__(self, appid: int = 730, currency: int = 1, user_agent: str = ""):
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
                return price_history
            else:
                print("No se encontró el historial en el HTML")
                return None
        else:
            print(f"Error al obtener historial de precios para '{market_hash_name}': {resp.status_code}")          
            return None

    def get_max_items(self) -> int:  
        url = "https://steamcommunity.com/market/search/render/"    
        params = {
            "appid": 730,
            "count": 1,   # máximo por request
            "start": 0,
            "norender": 1
        }
        m = None
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
        
            m = data.get("total_count",  0)
            print(f"Total items to fetch: {m}")
        
        return m

    def get_list_items(self, start: int = 0) -> list:
        url = "https://steamcommunity.com/market/search/render/"
        start = start
        count = 100 # max per request 
        all_items = []
        m = self.get_max_items()

        while True:
            params = {
                "appid": 730,
                "count": count,   # máximo por request
                "start": start,
                "norender": 1
            }

            resp = requests.get(url, params=params)
            data = resp.json()

            if data:
                # Obtenemos el array de json que contiene los items (de 100 en 100)
                results = data.get("results", [])

                if results == None or results == []:
                    # Agregar log para revisar ultima salida
                    break

                # Agregamos los 100 itemos a nuestra lista
                all_items += results

            if start >= m:
                break

            start += count

        return all_items
        
if __name__ == '__main__':
    # Usage of Steam Market API to get price overview and history
    client = SteamAPIMarket(currency=1)
    x = client.get_max_items()

    # item = "AK-47 | Redline (Field-Tested)"
    # overview = client.get_price_overview(item)
    # print(f"Overview for {item}:")
    # print(f"Median price: {overview['median_price']}, Volume: {overview['volume']}")
    # if 'lowest_price' in overview:
    #     print(f"Lowest price: {overview['lowest_price']}")
    # history = client.get_price_history(item)
    # print(history)

    items = client.get_list_items()
    
    print(f"Total items found: {len(items)}")
    print("Primeros 1000 items", items[:1000])

    with open("steam_market_items.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print("Solved in steam_market_items.json")
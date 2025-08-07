import requests
import json
import re
import time
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from core.loggin_config import logger
from core.config import config
from core.rate_limiter import RateLimiter


class SteamAPIMarket:
    """
    Class for collecting CS2 skin price data using the public (unofficial) Steam Market API.
    This class interacts with the same endpoints used by the Steam Market web interface,
    not an official or documented Steam API.
    """

    def __init__(self, appid: int = None, currency: int = None, user_agent: str = ""):
        """
        Initializes the client with configuration from centralized config.
        """
        steam_config = config.steam_config
        self.appid = appid or steam_config["app_id"]
        self.currency = currency or steam_config["currency"]
        self.base_price_url = f"{steam_config['base_url']}/market/priceoverview/"
        self.base_history_url = f"{steam_config['base_url']}/market/pricehistory/"
        self.base_history_url_alt = f"{steam_config['base_url']}/market/listings/"
        
        # Setup session with retry strategy
        self.session = self._create_session(user_agent or steam_config["user_agent"])
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter()
        
    def _create_session(self, user_agent: str) -> requests.Session:
        """
        Crea una sesión con retry strategy y timeouts configurados.
        
        Fundamento Teórico:
        - Retry Strategy: Reintenta automáticamente en fallos temporales
        - Circuit Breaker: Evita requests a servicios que fallan consistentemente
        - Connection Pooling: Reutiliza conexiones TCP para mejor rendimiento
        """
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Timeout por defecto
        session.timeout = config.steam_config["timeout"]
        
        return session

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
            "count": 1,
            "start": 0,
            "norender": 1,
            "query": "USP-S |"
        }
        m = None
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
        
            m = data.get("total_count",  0)
            print(f"Total items to fetch: {m}")
        else:
            logger.error(f"Error al obtener el número máximo de items: {resp.status_code}")
            logger.error(f"Response: {resp.text}")
            m = 0
        return m
    
    def _make_request_with_rate_limit(self, url: str, params: dict = None) -> Optional[requests.Response]:
        """
        Hace un request respetando rate limits y manejando errores robustamente.
        
        Fundamento Teórico:
        - Rate Limiting: Previene ser bloqueado por APIs
        - Exponential Backoff: Reduce carga en servicios bajo estrés  
        - Circuit Breaker: Evita requests a servicios caídos
        """
        attempt = 0
        while attempt <= self.rate_limiter.max_retries:
            try:
                # Verificar rate limit antes del request
                self.rate_limiter.wait_if_needed()
                
                logger.debug(f"Request attempt {attempt + 1} to {url}")
                response = self.session.get(url, params=params)
                
                # Verificar status code
                if response.status_code == 200:
                    self.rate_limiter.record_request(success=True)
                    return response
                elif response.status_code == 429:  # Rate limited
                    logger.warning(f"Rate limited by Steam (429). Attempt {attempt + 1}")
                    self.rate_limiter.record_request(success=False)
                elif response.status_code in [500, 502, 503, 504]:  # Server errors
                    logger.warning(f"Server error {response.status_code}. Attempt {attempt + 1}")
                    self.rate_limiter.record_request(success=False)
                else:
                    logger.error(f"Unexpected status code {response.status_code}: {response.text}")
                    self.rate_limiter.record_request(success=False)
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception on attempt {attempt + 1}: {e}")
                self.rate_limiter.record_request(success=False)
            
            attempt += 1
            if attempt <= self.rate_limiter.max_retries:
                backoff_time = self.rate_limiter._calculate_backoff(attempt)
                logger.info(f"Retrying in {backoff_time:.1f}s...")
                time.sleep(backoff_time)
        
        logger.error(f"Failed to get response after {self.rate_limiter.max_retries} attempts")
        return None

    def get_list_items(self, start: int = 0, query: str = "USP-S |") -> List[Dict[str, Any]]:
        """
        Gets a list of items from the Steam Market API with robust error handling.
        
        Fundamento Teórico:
        - Paginación: Obtiene datos en chunks manejables
        - Rate Limiting: Respeta límites de API para evitar bloqueos
        - Resilencia: Maneja fallos temporales y recupera automáticamente
        """
        url = f"{config.steam_config['base_url']}/market/search/render/"
        count = config.rate_limit_config.get("batch_size", 10)
        all_items = []
        
        # Obtener total de items disponibles
        total_items = self.get_max_items()
        if total_items == 0:
            logger.error("No se pudo obtener el total de items disponibles")
            return []
            
        logger.info(f"Iniciando scraping. Total items disponibles: {total_items}")
        current_start = start

        while current_start < total_items:
            logger.info(f"Obteniendo items {current_start}-{current_start + count} de {total_items}")
            
            params = {
                "appid": self.appid,
                "count": count,
                "start": current_start,
                "norender": 1,
                "query": query
            }
            
            # Usar nuestro método con rate limiting
            response = self._make_request_with_rate_limit(url, params)
            
            if not response:
                logger.error(f"No se pudo obtener respuesta para start={current_start}")
                break
                
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Error decodificando JSON: {e}")
                break
                
            results = data.get("results", [])
            if not results:
                logger.warning(f"No hay más resultados disponibles en start={current_start}")
                break
                
            # Log de progreso
            for item in results:
                logger.debug(f"Item obtenido: {item.get('hash_name', 'N/A')}")
                
            all_items.extend(results)
            current_start += count
            
            # Status del rate limiter
            status = self.rate_limiter.get_status()
            logger.debug(f"Rate limiter status: {status}")

        logger.info(f"Scraping completado. Items obtenidos: {len(all_items)}")
        return all_items
        
if __name__ == '__main__':
    # Usage of Steam Market API to get price overview and history
    client = SteamAPIMarket(currency=1)

    import pandas as pd
    df = pd.DataFrame(client.get_list_items())
    df.to_csv("steam_market_items.csv", index=False)
    # item = "AK-47 | Redline (Field-Tested)"
    # overview = client.get_price_overview(item)
    # print(f"Overview for {item}:")
    # print(f"Median price: {overview['median_price']}, Volume: {overview['volume']}")
    # if 'lowest_price' in overview:
    #     print(f"Lowest price: {overview['lowest_price']}")
    # history = client.get_price_history(item)
    # print(history)



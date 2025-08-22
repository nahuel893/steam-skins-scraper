import requests
import json
import re
import time
import sys
import os
import random
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.loggin_config import logger
from core.config import config
from core.rate_limiter import RateLimiter


class SteamAPIMarket:
    """
    Class for collecting CS2 skin price data using the public (unofficial) Steam Market API.
    This class interacts with the same endpoints used by the Steam Market web interface,
    not an official or documented Steam API.
    """

    def __init__(self, appid: int = 730, currency: int = 0, user_agent: str = ""):
        """
        Initializes the client with configuration from centralized config.
        """
        steam_config = config.steam_config
        self.appid = appid or steam_config["app_id"]
        self.currency = currency or steam_config["currency"]
        self.base_price_url = f"{steam_config['base_url']}/market/priceoverview/"
        self.base_history_url = f"{steam_config['base_url']}/market/pricehistory/"
        self.base_history_url_alt = f"{steam_config['base_url']}/market/listings/"
        
        # Setup session requests with retry strategy
        self.session = self._create_session(user_agent or steam_config["user_agent"])
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter()
        
    def _create_session(self, user_agent: str) -> requests.Session:
        """
        Crea una sesión con retry strategy, timeouts y cookies realistas.
        
        Fundamento Teórico:
        - Retry Strategy: Reintenta automáticamente en fallos temporales
        - Circuit Breaker: Evita requests a servicios que fallan consistentemente
        - Connection Pooling: Reutiliza conexiones TCP para mejor rendimiento
        - Session Persistence: Mantiene estado como navegador real
        """
        session = requests.Session()
        
        # Configurar retry strategy más conservadora
        retry_strategy = Retry(
            total=2,  # Menos reintentos automáticos, manejamos manualmente
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504],  # Excluimos 429 para manejo manual
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers iniciales básicos (se actualizarán dinámicamente)
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Simular cookies de sesión realistas
        session.cookies.update({
            'browserid': f"{random.randint(1000000000000000000, 9999999999999999999)}",
            'sessionid': f"steam_session_{random.randint(100000, 999999)}",
            'steamMachineAuth': f"auth_{random.randint(1000000, 9999999)}",
            'Steam_Language': 'english',
            'timezoneOffset': '0,0'
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
        url = f"{self.base_history_url_alt}{self.appid}/{quote(params['market_hash_name'])}"
        # Generamos la request a la URL de historial de precios
        resp = requests.get(url)

        if resp.status_code == 200:
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
        """
        Obtiene el número total de items disponibles usando el rate limiter mejorado.
        """
        url = "https://steamcommunity.com/market/search/render/"    
        params = {
            "appid": 730,
            "count": 1,
            "start": 0,
            "norender": 1,
            "query": ""
        }
        
        # Usar el método con rate limiting
        response = self._make_request_with_rate_limit(url, params)
        
        if not response:
            logger.error("No se pudo obtener el total de items disponibles")
            return 0
            
        try:
            data = response.json()
            total_count = data.get("total_count", 0)
            logger.info(f"Total items disponibles en Steam Market: {total_count}")
            return total_count
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
            return 0
    
    def _make_request_with_rate_limit(self, url: str, params: dict = {}) -> Optional[requests.Response]:
        """
        Hace un request respetando rate limits con headers realistas y manejo avanzado.
        
        Fundamento Teórico:
        - Rate Limiting: Previene ser bloqueado por APIs
        - Exponential Backoff: Reduce carga en servicios bajo estrés  
        - Circuit Breaker: Evita requests a servicios caídos
        - Header Rotation: Simula comportamiento humano variable
        """
        
        attempt = 0
        while attempt <= self.rate_limiter.max_retries:
            try:
                # Verificar rate limit antes del request
                self.rate_limiter.wait_if_needed()
                
                # Actualizar headers realistas para cada request
                realistic_headers = self.rate_limiter.get_realistic_headers()
                self.session.headers.update(realistic_headers)
                
                logger.debug(f"Request attempt {attempt + 1} to {url}")
                logger.debug(f"Using User-Agent: {realistic_headers.get('User-Agent', 'N/A')[:50]}...")
                
                # Medir tiempo de respuesta
                start_time = time.time()
                response = self.session.get(url, params=params)
                response_time = time.time() - start_time
                
                # Verificar status code y registrar con metadata completa
                if response.status_code == 200:
                    self.rate_limiter.record_request(
                        success=True, 
                        response_time=response_time, 
                        status_code=200
                    )
                    logger.debug(f"Request exitoso en {response_time:.2f}s")
                    return response
                elif response.status_code == 429:  # Rate limited
                    logger.warning(f"Rate limited by Steam (429). Attempt {attempt + 1}")
                    self.rate_limiter.record_request(
                        success=False, 
                        response_time=response_time, 
                        status_code=429
                    )
                elif response.status_code in [500, 502, 503, 504]:  # Server errors
                    logger.warning(f"Server error {response.status_code}. Attempt {attempt + 1}")
                    self.rate_limiter.record_request(
                        success=False, 
                        response_time=response_time, 
                        status_code=response.status_code
                    )
                else:
                    logger.error(f"Unexpected status code {response.status_code}: {response.text[:200]}")
                    self.rate_limiter.record_request(
                        success=False, 
                        response_time=response_time, 
                        status_code=response.status_code
                    )
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception on attempt {attempt + 1}: {e}")
                self.rate_limiter.record_request(success=False, status_code=None)
            
            attempt += 1
            if attempt <= self.rate_limiter.max_retries:
                backoff_time = self.rate_limiter._calculate_backoff(attempt)
                logger.info(f"Retrying in {backoff_time:.1f}s...")
                time.sleep(backoff_time)
        
        logger.error(f"Failed to get response after {self.rate_limiter.max_retries} attempts")
        return None

    def get_list_items(self, start: int = 0, query: str = "") -> List[Dict[str, Any]]:
        """
        Gets a list of items from the Steam Market API with robust error handling.
        
        Fundamento Teórico:
        - Paginación: Obtiene datos en chunks manejables
        - Rate Limiting: Respeta límites de API para evitar bloqueos
        - Resilencia: Maneja fallos temporales y recupera automáticamente
        """
        url = f"{config.steam_config['list_url']}"
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
            
            # Status detallado del rate limiter cada ciertos requests
            if current_start % (count * 5) == 0:  # Cada 5 batches
                status = self.rate_limiter.get_status()
                logger.info(f"Rate limiter status - Success rate: {status['recent_success_rate']:.1f}%, "
                          f"Avg response time: {status['avg_response_time']:.2f}s, "
                          f"Degraded: {status['degraded_service']}")
                
                if status['performance_degraded']:
                    logger.warning("Performance degradada detectada. Considerando pausas más largas.")

        logger.info(f"Scraping completado. Items obtenidos: {len(all_items)}")
        
        # Status final
        final_status = self.rate_limiter.get_status()
        logger.info(f"Estadísticas finales - Duración sesión: {final_status['session_duration']:.0f}s, "
                   f"Success rate: {final_status['recent_success_rate']:.1f}%")
        
        return all_items
        
if __name__ == '__main__':
    # Usage of Steam Market API to get price overview and history
    client = SteamAPIMarket(currency=1)

    import pandas as pd
    df = pd.DataFrame(client.get_list_items())
    df.to_csv("steam_market_items.csv", index=False)



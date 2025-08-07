"""
Sistema de Rate Limiting robusto para controlar requests a APIs externas.
Implementa el patrón Token Bucket con backoff exponencial.
"""
import time
import random
from typing import List
from dataclasses import dataclass
from core.loggin_config import logger
from core.config import config

@dataclass
class RequestRecord:
    """Registro de un request con timestamp."""
    timestamp: float

class RateLimiter:
    """
    Rate Limiter que implementa Sliding Window con backoff exponencial.
    
    Fundamento Teórico:
    - Sliding Window: Mantiene ventana deslizante de requests recientes
    - Backoff Exponencial: Aumenta tiempo de espera progresivamente
    - Jitter: Añade aleatoriedad para evitar thundering herd
    """
    
    def __init__(
        self, 
        max_requests: int = None,
        window_seconds: int = None,
        max_retries: int = None
    ):
        self.max_requests = max_requests or config.rate_limit_config["max_requests"]
        self.window_seconds = window_seconds or config.rate_limit_config["wait_seconds"]
        self.max_retries = max_retries or config.rate_limit_config["max_retries"]
        self.requests: List[RequestRecord] = []
        self.consecutive_failures = 0
        
    def _clean_old_requests(self) -> None:
        """Elimina requests fuera de la ventana deslizante."""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        self.requests = [req for req in self.requests if req.timestamp > cutoff_time]
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calcula tiempo de backoff exponencial con jitter.
        Formula: base_delay * (2^attempt) + jitter
        """
        base_delay = 1  # segundo base
        exponential_delay = base_delay * (2 ** attempt)
        jitter = random.uniform(0, 0.1 * exponential_delay)  # 10% jitter
        return min(exponential_delay + jitter, 300)  # Max 5 minutos
    
    def can_make_request(self) -> bool:
        """Verifica si se puede hacer un request sin violar límites."""
        self._clean_old_requests()
        return len(self.requests) < self.max_requests
    
    def wait_if_needed(self) -> None:
        """
        Espera el tiempo necesario si se alcanzó el límite de requests.
        Implementa backoff exponencial en caso de fallos consecutivos.
        """
        self._clean_old_requests()
        
        if len(self.requests) >= self.max_requests:
            # Calcular tiempo hasta que el request más antiguo expire
            oldest_request = min(self.requests, key=lambda x: x.timestamp)
            wait_time = (oldest_request.timestamp + self.window_seconds) - time.time()
            
            # Aplicar backoff si hay fallos consecutivos
            if self.consecutive_failures > 0:
                backoff_time = self._calculate_backoff(self.consecutive_failures)
                wait_time = max(wait_time, backoff_time)
                logger.warning(
                    f"Rate limit + backoff: esperando {wait_time:.1f}s "
                    f"(fallos consecutivos: {self.consecutive_failures})"
                )
            else:
                logger.info(f"Rate limit: esperando {wait_time:.1f}s")
            
            if wait_time > 0:
                time.sleep(wait_time)
                self._clean_old_requests()  # Limpiar después de esperar
    
    def record_request(self, success: bool = True) -> None:
        """
        Registra un request realizado y actualiza contadores de fallos.
        """
        self.requests.append(RequestRecord(timestamp=time.time()))
        
        if success:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            logger.warning(f"Request fallido. Fallos consecutivos: {self.consecutive_failures}")
    
    def should_retry(self, attempt: int) -> bool:
        """Determina si se debe reintentar un request fallido."""
        return attempt < self.max_retries
    
    def get_status(self) -> dict:
        """Retorna información del estado actual del rate limiter."""
        self._clean_old_requests()
        return {
            "requests_in_window": len(self.requests),
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "consecutive_failures": self.consecutive_failures,
            "can_make_request": self.can_make_request()
        }
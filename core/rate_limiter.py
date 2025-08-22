"""
Sistema de Rate Limiting robusto para controlar requests a APIs externas.
Implementa el patrón Token Bucket con backoff exponencial, rotación de User-Agents,
headers realistas y detección inteligente de rate limits.
"""
import time
import random
from typing import List, Optional
from dataclasses import dataclass
from core.loggin_config import logger
from core.config import config

@dataclass
class RequestRecord:
    """Registro de un request con timestamp y metadata de performance."""
    timestamp: float
    success: bool = True
    response_time: Optional[float] = None
    status_code: Optional[int] = None

class RateLimiter:
    """
    Rate Limiter avanzado que implementa Sliding Window con backoff exponencial,
    rotación de User-Agents, headers realistas y detección inteligente de rate limits.
    
    Fundamento Teórico:
    - Sliding Window: Mantiene ventana deslizante de requests recientes
    - Backoff Exponencial: Aumenta tiempo de espera progresivamente
    - Jitter: Añade aleatoriedad para evitar thundering herd
    - Circuit Breaker: Detección automática de degradación del servicio
    - Header Rotation: Simula comportamiento humano real
    """
    
    def __init__(
        self, 
        max_requests: int = None,
        window_seconds: int = None,
        max_retries: int = None 
    ):
        rate_config = config.rate_limit_config
        self.max_requests = max_requests or rate_config["max_requests"]
        self.window_seconds = window_seconds or rate_config["wait_seconds"]
        self.max_retries = max_retries or rate_config["max_retries"]
        self.backoff_base = rate_config["backoff_base"]
        self.jitter_percentage = rate_config["jitter_percentage"]
        
        self.requests: List[RequestRecord] = []
        self.consecutive_failures = 0
        self.current_user_agent_index = 0
        self.session_start_time = time.time()
        self.degraded_service = False
        self.last_429_time = None
        
    def _clean_old_requests(self) -> None:
        """Elimina requests fuera de la ventana deslizante."""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        self.requests = [req for req in self.requests if req.timestamp > cutoff_time]
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calcula tiempo de backoff exponencial con jitter más agresivo.
        Formula: backoff_base * (2^attempt) + jitter
        """
        exponential_delay = self.backoff_base * (2 ** (attempt - 1))
        jitter = random.uniform(0, self.jitter_percentage * exponential_delay)
        backoff_time = exponential_delay + jitter
        
        # Si hemos recibido 429 recientemente, ser más conservador
        if self.last_429_time and (time.time() - self.last_429_time) < 300:  # 5 minutos
            backoff_time *= 2
            logger.warning(f"429 reciente detectado, duplicando backoff a {backoff_time:.1f}s")
        
        return min(backoff_time, 900)  # Max 15 minutos
        
    def _add_jitter_to_wait(self, base_wait: float) -> float:
        """Añade jitter aleatorio al tiempo de espera base."""
        jitter = random.uniform(-self.jitter_percentage, self.jitter_percentage) * base_wait
        return max(base_wait + jitter, 1.0)  # Mínimo 1 segundo
    
    def can_make_request(self) -> bool:
        """Verifica si se puede hacer un request sin violar límites."""
        self._clean_old_requests()
        return len(self.requests) < self.max_requests
    
    def wait_if_needed(self) -> None:
        """
        Espera el tiempo necesario si se alcanzó el límite de requests.
        Implementa backoff exponencial, jitter y detección de degradación del servicio.
        """
        self._clean_old_requests()
        
        if len(self.requests) >= self.max_requests:
            # Calcular tiempo hasta que el request más antiguo expire
            oldest_request = min(self.requests, key=lambda x: x.timestamp)
            wait_time = (oldest_request.timestamp + self.window_seconds) - time.time()
            
            # Añadir jitter al tiempo base
            wait_time = self._add_jitter_to_wait(wait_time)
            
            # Aplicar backoff si hay fallos consecutivos
            if self.consecutive_failures > 0:
                backoff_time = self._calculate_backoff(self.consecutive_failures)
                wait_time = max(wait_time, backoff_time)
                logger.warning(
                    f"Rate limit + backoff: esperando {wait_time:.1f}s "
                    f"(fallos consecutivos: {self.consecutive_failures})"
                )
            else:
                logger.info(f"Rate limit: esperando {wait_time:.1f}s (con jitter)")
            
            # Detectar si el servicio está degradado
            if self.consecutive_failures >= 3:
                self.degraded_service = True
                logger.error(f"Servicio Steam posiblemente degradado. Aumentando precauciones.")
            
            if wait_time > 0:
                time.sleep(wait_time)
                self._clean_old_requests()  # Limpiar después de esperar
    
    def record_request(self, success: bool = True, response_time: Optional[float] = None, status_code: Optional[int] = None) -> None:
        """
        Registra un request realizado con metadata completa y actualiza contadores.
        """
        record = RequestRecord(
            timestamp=time.time(),
            success=success,
            response_time=response_time,
            status_code=status_code
        )
        self.requests.append(record)
        
        if success:
            self.consecutive_failures = 0
            if self.degraded_service:
                logger.info("Servicio Steam se ha recuperado")
                self.degraded_service = False
        else:
            self.consecutive_failures += 1
            if status_code == 429:
                self.last_429_time = time.time()
                logger.error(f"Rate limited (429). Fallos consecutivos: {self.consecutive_failures}")
            else:
                logger.warning(f"Request fallido (status: {status_code}). Fallos consecutivos: {self.consecutive_failures}")
    
    def should_retry(self, attempt: int) -> bool:
        """Determina si se debe reintentar un request fallido."""
        return attempt < self.max_retries
    
    def get_next_user_agent(self) -> str:
        """Obtiene el siguiente User-Agent en rotación."""
        user_agents = config.user_agents
        self.current_user_agent_index = (self.current_user_agent_index + 1) % len(user_agents)
        return user_agents[self.current_user_agent_index]
    
    def get_realistic_headers(self) -> dict:
        """
        Genera headers realistas que simulan navegación humana.
        """
        headers = {
            'User-Agent': self.get_next_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice(['en-US,en;q=0.9', 'en-US,en;q=0.8,es;q=0.7', 'en-GB,en;q=0.9']),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # Ocasionalmente añadir referer de Steam
        if random.random() < 0.3:  # 30% del tiempo
            headers['Referer'] = 'https://steamcommunity.com/market/'
        
        return headers
    
    def _detect_performance_degradation(self) -> bool:
        """
        Detecta si el rendimiento del servicio se está degradando.
        """
        if len(self.requests) < 3:
            return False
        
        recent_requests = [r for r in self.requests if r.response_time is not None][-5:]
        if len(recent_requests) < 3:
            return False
        
        avg_response_time = sum(r.response_time for r in recent_requests) / len(recent_requests)
        slow_requests = sum(1 for r in recent_requests if r.response_time > 5.0)
        
        # Si más del 60% de requests recientes son lentos (>5s), considerar degradado
        return slow_requests / len(recent_requests) > 0.6 or avg_response_time > 8.0
    
    def get_status(self) -> dict:
        """Retorna información completa del estado actual del rate limiter."""
        self._clean_old_requests()
        
        # Calcular estadísticas de performance
        recent_success_rate = 0
        avg_response_time = 0
        if self.requests:
            recent_requests = self.requests[-10:]  # Últimos 10 requests
            successful = sum(1 for r in recent_requests if r.success)
            recent_success_rate = successful / len(recent_requests) * 100
            
            response_times = [r.response_time for r in recent_requests if r.response_time is not None]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "requests_in_window": len(self.requests),
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "consecutive_failures": self.consecutive_failures,
            "can_make_request": self.can_make_request(),
            "degraded_service": self.degraded_service,
            "last_429_time": self.last_429_time,
            "session_duration": time.time() - self.session_start_time,
            "recent_success_rate": recent_success_rate,
            "avg_response_time": avg_response_time,
            "performance_degraded": self._detect_performance_degradation()
        }

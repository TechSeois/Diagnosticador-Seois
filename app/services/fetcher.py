"""
Cliente HTTP asíncrono con httpx para descarga de páginas web.
Incluye retries, manejo de robots.txt y rate limiting.
"""
import asyncio
import httpx
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HTTPFetcher:
    """Cliente HTTP asíncrono con funcionalidades avanzadas."""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.last_request_time: Dict[str, float] = {}
        
    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def start(self):
        """Inicializa el cliente HTTP."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.default_timeout),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
    
    async def close(self):
        """Cierra el cliente HTTP."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def fetch_url(self, url: str, retries: int = 3) -> Optional[httpx.Response]:
        """
        Descarga una URL con retries exponenciales.
        
        Args:
            url: URL a descargar
            retries: Número de reintentos
            
        Returns:
            Response de httpx o None si falla
        """
        if not self.client:
            await self.start()
        
        for attempt in range(retries + 1):
            try:
                # Rate limiting simple
                await self._rate_limit(url)
                
                logger.info(f"Descargando URL: {url} (intento {attempt + 1})")
                response = await self.client.get(url)
                response.raise_for_status()
                
                logger.info(f"URL descargada exitosamente: {url} ({len(response.content)} bytes)")
                return response
                
            except httpx.HTTPStatusError as e:
                logger.warning(f"Error HTTP {e.response.status_code} para {url}: {e}")
                if e.response.status_code in [404, 403, 401]:
                    # No reintentar para estos códigos
                    break
                    
            except httpx.RequestError as e:
                logger.warning(f"Error de request para {url}: {e}")
                
            except Exception as e:
                logger.error(f"Error inesperado descargando {url}: {e}")
            
            if attempt < retries:
                # Backoff exponencial
                wait_time = 2 ** attempt
                logger.info(f"Esperando {wait_time}s antes del siguiente intento...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"Falló descargar URL después de {retries + 1} intentos: {url}")
        return None
    
    async def _rate_limit(self, url: str):
        """Implementa rate limiting simple."""
        domain = urlparse(url).netloc
        current_time = time.time()
        
        if domain in self.last_request_time:
            time_since_last = current_time - self.last_request_time[domain]
            min_delay = 1.0  # 1 segundo mínimo entre requests al mismo dominio
            
            if time_since_last < min_delay:
                sleep_time = min_delay - time_since_last
                await asyncio.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    async def check_robots_txt(self, base_url: str) -> Optional[RobotFileParser]:
        """
        Descarga y parsea robots.txt para un dominio.
        
        Args:
            base_url: URL base del dominio
            
        Returns:
            RobotFileParser o None si no se puede obtener
        """
        domain = urlparse(base_url).netloc
        
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        robots_url = urljoin(base_url, '/robots.txt')
        
        try:
            response = await self.fetch_url(robots_url)
            if response and response.status_code == 200:
                robots = RobotFileParser()
                robots.set_url(robots_url)
                robots.read()
                
                self.robots_cache[domain] = robots
                logger.info(f"Robots.txt cargado para {domain}")
                return robots
                
        except Exception as e:
            logger.warning(f"Error cargando robots.txt para {domain}: {e}")
        
        return None
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """
        Verifica si se puede hacer fetch de una URL según robots.txt.
        
        Args:
            url: URL a verificar
            user_agent: User agent a usar
            
        Returns:
            True si se puede hacer fetch, False en caso contrario
        """
        domain = urlparse(url).netloc
        
        if domain in self.robots_cache:
            robots = self.robots_cache[domain]
            return robots.can_fetch(user_agent, url)
        
        # Si no hay robots.txt, permitir por defecto
        return True
    
    async def fetch_multiple_urls(self, urls: List[str], max_concurrent: Optional[int] = None) -> Dict[str, Optional[httpx.Response]]:
        """
        Descarga múltiples URLs en paralelo con límite de concurrencia.
        
        Args:
            urls: Lista de URLs a descargar
            max_concurrent: Máximo número de requests concurrentes
            
        Returns:
            Diccionario con URL como clave y Response como valor
        """
        if max_concurrent is None:
            max_concurrent = settings.max_concurrent_requests
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url: str) -> tuple[str, Optional[httpx.Response]]:
            async with semaphore:
                response = await self.fetch_url(url)
                return url, response
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados y manejar excepciones
        url_responses = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error en fetch múltiple: {result}")
                continue
            
            url, response = result
            url_responses[url] = response
        
        return url_responses
    
    def get_content_type(self, response: httpx.Response) -> str:
        """Extrae content-type de una response."""
        return response.headers.get('content-type', '').split(';')[0].lower()
    
    def is_html_content(self, response: httpx.Response) -> bool:
        """Verifica si el contenido es HTML."""
        content_type = self.get_content_type(response)
        return 'text/html' in content_type or 'application/xhtml' in content_type
    
    def get_encoding(self, response: httpx.Response) -> str:
        """Detecta la codificación del contenido."""
        # Intentar obtener de headers
        content_type = response.headers.get('content-type', '')
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[1].split(';')[0].strip()
            return charset
        
        # Detectar automáticamente
        try:
            return response.encoding or 'utf-8'
        except:
            return 'utf-8'


# Función de conveniencia para uso simple
async def fetch_url_simple(url: str) -> Optional[str]:
    """
    Función simple para descargar una URL y obtener su contenido HTML.
    
    Args:
        url: URL a descargar
        
    Returns:
        Contenido HTML como string o None si falla
    """
    async with HTTPFetcher() as fetcher:
        response = await fetcher.fetch_url(url)
        if response and fetcher.is_html_content(response):
            return response.text
    return None


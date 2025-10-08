"""
Descubrimiento y parseo de sitemaps XML.
Implementa descubrimiento automático, parseo recursivo y filtrado de URLs.
"""
import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime, timedelta
from collections import defaultdict

from app.services.fetcher import HTTPFetcher
from app.services.utils import URLUtils

logger = logging.getLogger(__name__)


class SitemapService:
    """Servicio para descubrimiento y parseo de sitemaps."""
    
    def __init__(self):
        self.url_utils = URLUtils()
        self.processed_sitemaps: Set[str] = set()
    
    async def discover_sitemap(self, base_url: str, fetcher: HTTPFetcher) -> Optional[str]:
        """
        Descubre la URL del sitemap para un dominio.
        
        Args:
            base_url: URL base del dominio
            fetcher: Instancia de HTTPFetcher
            
        Returns:
            URL del sitemap encontrado o None
        """
        try:
            # Intentar ubicaciones comunes de sitemap
            sitemap_candidates = [
                urljoin(base_url, '/sitemap.xml'),
                urljoin(base_url, '/sitemap_index.xml'),
                urljoin(base_url, '/wp-sitemap.xml'),
                urljoin(base_url, '/sitemap.xml.gz'),
                urljoin(base_url, '/sitemap_index.xml.gz')
            ]
            
            for sitemap_url in sitemap_candidates:
                try:
                    response = await fetcher.fetch_url(sitemap_url)
                    if response and response.status_code == 200:
                        logger.info(f"Sitemap encontrado: {sitemap_url}")
                        return sitemap_url
                except Exception as e:
                    logger.debug(f"No se pudo acceder a {sitemap_url}: {e}")
                    continue
            
            # Buscar en robots.txt
            robots_sitemap = await self._find_sitemap_in_robots(base_url, fetcher)
            if robots_sitemap:
                return robots_sitemap
            
            logger.warning(f"No se encontró sitemap para {base_url}")
            return None
            
        except Exception as e:
            logger.error(f"Error descubriendo sitemap para {base_url}: {e}")
            return None
    
    async def _find_sitemap_in_robots(self, base_url: str, fetcher: HTTPFetcher) -> Optional[str]:
        """Busca sitemap en robots.txt."""
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            response = await fetcher.fetch_url(robots_url)
            
            if response and response.status_code == 200:
                robots_content = response.text
                
                # Buscar líneas Sitemap:
                for line in robots_content.split('\n'):
                    line = line.strip()
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        if sitemap_url:
                            logger.info(f"Sitemap encontrado en robots.txt: {sitemap_url}")
                            return sitemap_url
            
            return None
            
        except Exception as e:
            logger.debug(f"Error buscando sitemap en robots.txt: {e}")
            return None
    
    async def parse_sitemap(self, sitemap_url: str, fetcher: HTTPFetcher, 
                          max_urls: int = 1000) -> List[Dict[str, Any]]:
        """
        Parsea un sitemap y extrae URLs con metadatos.
        
        Args:
            sitemap_url: URL del sitemap
            fetcher: Instancia de HTTPFetcher
            max_urls: Máximo número de URLs a procesar
            
        Returns:
            Lista de URLs con metadatos
        """
        try:
            response = await fetcher.fetch_url(sitemap_url)
            if not response or response.status_code != 200:
                logger.error(f"No se pudo descargar sitemap: {sitemap_url}")
                return []
            
            # Parsear XML
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                logger.error(f"Error parseando XML del sitemap: {e}")
                return []
            
            # Determinar tipo de sitemap
            if root.tag.endswith('sitemapindex'):
                return await self._parse_sitemap_index(root, fetcher, max_urls)
            elif root.tag.endswith('urlset'):
                return self._parse_urlset(root, max_urls)
            else:
                logger.warning(f"Tipo de sitemap desconocido: {root.tag}")
                return []
                
        except Exception as e:
            logger.error(f"Error parseando sitemap {sitemap_url}: {e}")
            return []
    
    async def _parse_sitemap_index(self, root: ET.Element, fetcher: HTTPFetcher, 
                                 max_urls: int) -> List[Dict[str, Any]]:
        """Parsea un sitemap index (sitemap de sitemaps)."""
        urls = []
        
        try:
            # Encontrar todos los sitemaps
            sitemap_elements = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap')
            
            for sitemap_elem in sitemap_elements:
                if len(urls) >= max_urls:
                    break
                
                loc_elem = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc_elem is not None:
                    sitemap_url = loc_elem.text.strip()
                    
                    # Evitar procesar el mismo sitemap múltiples veces
                    if sitemap_url in self.processed_sitemaps:
                        continue
                    
                    self.processed_sitemaps.add(sitemap_url)
                    
                    # Parsear sitemap individual
                    logger.info(f"Procesando sitemap individual: {sitemap_url}")
                    individual_urls = await self.parse_sitemap(sitemap_url, fetcher, max_urls - len(urls))
                    urls.extend(individual_urls)
            
            logger.info(f"Sitemap index procesado: {len(urls)} URLs encontradas")
            return urls
            
        except Exception as e:
            logger.error(f"Error parseando sitemap index: {e}")
            return []
    
    def _parse_urlset(self, root: ET.Element, max_urls: int) -> List[Dict[str, Any]]:
        """Parsea un urlset (sitemap de URLs)."""
        urls = []
        
        try:
            # Encontrar todas las URLs
            url_elements = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
            
            for url_elem in url_elements:
                if len(urls) >= max_urls:
                    break
                
                url_data = self._extract_url_data(url_elem)
                if url_data:
                    urls.append(url_data)
            
            logger.info(f"URLset procesado: {len(urls)} URLs encontradas")
            return urls
            
        except Exception as e:
            logger.error(f"Error parseando urlset: {e}")
            return []
    
    def _extract_url_data(self, url_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Extrae datos de un elemento URL del sitemap."""
        try:
            url_data = {
                'url': None,
                'lastmod': None,
                'changefreq': None,
                'priority': None
            }
            
            # URL
            loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_elem is not None:
                url_data['url'] = loc_elem.text.strip()
            else:
                return None  # URL es obligatoria
            
            # Última modificación
            lastmod_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            if lastmod_elem is not None:
                url_data['lastmod'] = lastmod_elem.text.strip()
            
            # Frecuencia de cambio
            changefreq_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq')
            if changefreq_elem is not None:
                url_data['changefreq'] = changefreq_elem.text.strip()
            
            # Prioridad
            priority_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}priority')
            if priority_elem is not None:
                try:
                    url_data['priority'] = float(priority_elem.text.strip())
                except ValueError:
                    url_data['priority'] = 0.5  # Valor por defecto
            
            return url_data
            
        except Exception as e:
            logger.warning(f"Error extrayendo datos de URL: {e}")
            return None
    
    def filter_urls(self, urls: List[Dict[str, Any]], base_domain: str, 
                   language: str = 'es') -> List[Dict[str, Any]]:
        """
        Filtra URLs según criterios de relevancia.
        
        Args:
            urls: Lista de URLs con metadatos
            base_domain: Dominio base para filtrar
            language: Idioma preferido
            
        Returns:
            Lista de URLs filtradas
        """
        filtered_urls = []
        
        try:
            for url_data in urls:
                url = url_data.get('url', '')
                
                # Verificar que la URL es válida
                if not self.url_utils.is_valid_url(url):
                    continue
                
                # Verificar que pertenece al dominio base
                if not self.url_utils.is_internal_link(url, base_domain):
                    continue
                
                # Filtrar por tipo de contenido
                if self._is_irrelevant_content(url):
                    continue
                
                # Filtrar por idioma (heurística simple)
                if not self._is_preferred_language(url, language):
                    continue
                
                # Añadir score de relevancia
                url_data['relevance_score'] = self._calculate_relevance_score(url_data)
                
                filtered_urls.append(url_data)
            
            # Ordenar por relevancia y prioridad
            filtered_urls.sort(key=lambda x: (
                x.get('relevance_score', 0),
                x.get('priority', 0.5)
            ), reverse=True)
            
            logger.info(f"URLs filtradas: {len(urls)} -> {len(filtered_urls)}")
            return filtered_urls
            
        except Exception as e:
            logger.error(f"Error filtrando URLs: {e}")
            return urls  # Retornar originales en caso de error
    
    def _is_irrelevant_content(self, url: str) -> bool:
        """Determina si una URL contiene contenido irrelevante."""
        # Patrones de URLs irrelevantes
        irrelevant_patterns = [
            r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|jpg|jpeg|png|gif|svg|css|js|xml)$',
            r'/(admin|login|logout|register|signup|signin)/',
            r'/(api|ajax|json|rss|feed)/',
            r'/(search|filter|sort)/',
            r'/(print|pdf|download)/',
            r'/(cart|checkout|payment|billing)/',
            r'/(user|profile|account|dashboard)/',
            r'/(404|error|not-found)/',
            r'/(test|debug|dev|staging)/'
        ]
        
        url_lower = url.lower()
        for pattern in irrelevant_patterns:
            if re.search(pattern, url_lower):
                return True
        
        return False
    
    def _is_preferred_language(self, url: str, language: str) -> bool:
        """Determina si una URL está en el idioma preferido."""
        if language == 'es':
            # Priorizar URLs en español
            spanish_patterns = [
                r'/es/',
                r'\.es/',
                r'/[a-z]+-es/',
                r'/[a-z]+_es/'
            ]
            
            # Penalizar URLs en otros idiomas
            other_language_patterns = [
                r'/en/',
                r'/fr/',
                r'/de/',
                r'/it/',
                r'/pt/',
                r'\.com/en/',
                r'\.com/fr/',
                r'\.com/de/'
            ]
            
            url_lower = url.lower()
            
            # Si tiene patrón de otro idioma, rechazar
            for pattern in other_language_patterns:
                if re.search(pattern, url_lower):
                    return False
            
            # Si tiene patrón español o no tiene patrón de idioma, aceptar
            for pattern in spanish_patterns:
                if re.search(pattern, url_lower):
                    return True
            
            # Por defecto aceptar si no hay indicadores de idioma
            return True
        
        return True  # Para otros idiomas, aceptar por defecto
    
    def _calculate_relevance_score(self, url_data: Dict[str, Any]) -> float:
        """Calcula score de relevancia para una URL."""
        score = 0.5  # Score base
        
        url = url_data.get('url', '').lower()
        
        # Bonus por prioridad del sitemap
        priority = url_data.get('priority', 0.5)
        score += priority * 0.3
        
        # Bonus por contenido relevante
        relevant_patterns = [
            r'/(producto|product|item)/',
            r'/(articulo|article|post|blog)/',
            r'/(categoria|category)/',
            r'/(servicio|service)/',
            r'/(nosotros|about|sobre)/',
            r'/(contacto|contact)/'
        ]
        
        for pattern in relevant_patterns:
            if re.search(pattern, url):
                score += 0.1
        
        # Penalizar URLs muy profundas
        depth = url.count('/') - 2  # Restar protocolo y dominio
        if depth > 4:
            score -= 0.1 * (depth - 4)
        
        # Bonus por URLs con palabras clave
        keyword_patterns = [
            r'/(guia|guide|tutorial)/',
            r'/(mejor|best|top)/',
            r'/(precio|price|cost)/',
            r'/(oferta|offer|deal)/'
        ]
        
        for pattern in keyword_patterns:
            if re.search(pattern, url):
                score += 0.05
        
        return max(0.0, min(1.0, score))  # Normalizar entre 0 y 1
    
    async def crawl_fallback(self, base_url: str, fetcher: HTTPFetcher, 
                           max_urls: int = 100) -> List[Dict[str, Any]]:
        """
        Crawl superficial como fallback cuando no hay sitemap.
        
        Args:
            base_url: URL base del dominio
            fetcher: Instancia de HTTPFetcher
            max_urls: Máximo número de URLs a descubrir
            
        Returns:
            Lista de URLs descubiertas
        """
        urls = []
        
        try:
            logger.info(f"Iniciando crawl de fallback para {base_url}")
            
            # Descargar página principal
            response = await fetcher.fetch_url(base_url)
            if not response:
                return urls
            
            # Parsear HTML para extraer enlaces
            from app.services.parser import HTMLParserService
            parser = HTMLParserService()
            parsed_data = parser.parse_html(response.text, base_url)
            
            # Obtener enlaces internos
            internal_links = parsed_data.get('links', {}).get('internal', [])
            
            # Filtrar y limitar enlaces
            for link in internal_links[:max_urls]:
                if len(urls) >= max_urls:
                    break
                
                url_data = {
                    'url': link,
                    'lastmod': None,
                    'changefreq': None,
                    'priority': 0.5,
                    'relevance_score': 0.5
                }
                
                urls.append(url_data)
            
            logger.info(f"Crawl de fallback completado: {len(urls)} URLs descubiertas")
            return urls
            
        except Exception as e:
            logger.error(f"Error en crawl de fallback: {e}")
            return urls

    async def parse_sitemap_with_dates(self, sitemap_url: str, fetcher: HTTPFetcher) -> List[Dict[str, Any]]:
        """
        Parsea sitemap extrayendo URLs con fechas de modificación.
        
        Args:
            sitemap_url: URL del sitemap
            fetcher: Instancia de HTTPFetcher
            
        Returns:
            Lista de diccionarios con URL, fecha y metadatos
        """
        try:
            response = await fetcher.fetch_url(sitemap_url)
            if not response or response.status_code != 200:
                logger.warning(f"No se pudo descargar sitemap: {sitemap_url}")
                return []
            
            root = ET.fromstring(response.text)
            
            # Verificar si es sitemap index
            if root.tag.endswith('sitemapindex'):
                return await self._parse_sitemap_index_with_dates(root, fetcher)
            else:
                return self._parse_urlset_with_dates(root)
                
        except Exception as e:
            logger.error(f"Error parseando sitemap con fechas: {e}")
            return []

    async def _parse_sitemap_index_with_dates(self, root: ET.Element, fetcher: HTTPFetcher) -> List[Dict[str, Any]]:
        """Parsea sitemap index extrayendo fechas."""
        urls_with_dates = []
        
        for sitemap_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
            loc_elem = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            lastmod_elem = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            
            if loc_elem is not None:
                sitemap_url = loc_elem.text
                lastmod = lastmod_elem.text if lastmod_elem is not None else None
                
                # Parsear URLs del sitemap individual
                individual_urls = await self.parse_sitemap_with_dates(sitemap_url, fetcher)
                urls_with_dates.extend(individual_urls)
        
        return urls_with_dates

    def _parse_urlset_with_dates(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Parsea urlset extrayendo fechas."""
        urls_with_dates = []
        
        for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            url_data = self._extract_url_data_with_dates(url_elem)
            if url_data:
                urls_with_dates.append(url_data)
        
        return urls_with_dates

    def _extract_url_data_with_dates(self, url_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Extrae datos de URL incluyendo fecha de modificación."""
        try:
            loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc_elem is None:
                return None
            
            url = loc_elem.text.strip()
            
            # Extraer fecha de modificación
            lastmod_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            lastmod = None
            if lastmod_elem is not None:
                try:
                    lastmod = datetime.fromisoformat(lastmod_elem.text.replace('Z', '+00:00'))
                except ValueError:
                    # Intentar otros formatos de fecha
                    try:
                        lastmod = datetime.strptime(lastmod_elem.text, '%Y-%m-%d')
                    except ValueError:
                        pass
            
            # Extraer prioridad
            priority_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}priority')
            priority = 0.5
            if priority_elem is not None:
                try:
                    priority = float(priority_elem.text)
                except ValueError:
                    priority = 0.5
            
            # Extraer frecuencia de cambio
            changefreq_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq')
            changefreq = 'monthly'
            if changefreq_elem is not None:
                changefreq = changefreq_elem.text
            
            return {
                'url': url,
                'lastmod': lastmod,
                'priority': priority,
                'changefreq': changefreq,
                'relevance_score': self._calculate_relevance_score({
                    'url': url,
                    'priority': priority,
                    'changefreq': changefreq
                })
            }
            
        except Exception as e:
            logger.warning(f"Error extrayendo datos de URL: {e}")
            return None

    def _select_intelligent_urls(self, urls_with_dates: List[Dict[str, Any]], domain: str, max_urls: int = 15) -> List[str]:
        """
        Selecciona URLs inteligentemente por categorías y fecha.
        
        Args:
            urls_with_dates: Lista de URLs con fechas y metadatos
            domain: Dominio base
            max_urls: Número máximo de URLs a seleccionar
            
        Returns:
            Lista de URLs seleccionadas
        """
        try:
            # Filtrar URLs de los últimos 5 días
            five_days_ago = datetime.now() - timedelta(days=5)
            recent_urls = [url for url in urls_with_dates 
                          if url['lastmod'] and url['lastmod'] >= five_days_ago]
            
            logger.info(f"URLs de últimos 5 días: {len(recent_urls)}")
            
            # Si no hay suficientes URLs recientes, usar todas
            if len(recent_urls) < max_urls:
                logger.info("Usando todas las URLs disponibles")
                urls_to_categorize = urls_with_dates
            else:
                urls_to_categorize = recent_urls
            
            # Categorizar URLs
            categories = self._categorize_urls(urls_to_categorize, domain)
            
            # Seleccionar URLs por categoría
            selected_urls = self._select_by_categories(categories, max_urls)
            
            logger.info(f"URLs seleccionadas por categorías: {len(selected_urls)}")
            return selected_urls
            
        except Exception as e:
            logger.error(f"Error seleccionando URLs inteligentemente: {e}")
            # Fallback: seleccionar por relevancia
            return self._select_by_relevance(urls_with_dates, max_urls)

    def _categorize_urls(self, urls: List[Dict[str, Any]], domain: str) -> Dict[str, List[Dict[str, Any]]]:
        """Categoriza URLs por tipo de contenido."""
        categories = defaultdict(list)
        
        for url_data in urls:
            url = url_data['url']
            
            # Categorizar por patrones de URL
            if self._is_product_url(url):
                categories['products'].append(url_data)
            elif self._is_blog_url(url):
                categories['blog'].append(url_data)
            elif self._is_category_url(url):
                categories['categories'].append(url_data)
            elif self._is_landing_page(url):
                categories['landing'].append(url_data)
            else:
                categories['other'].append(url_data)
        
        # Ordenar cada categoría por relevancia y fecha
        for category in categories:
            categories[category].sort(key=lambda x: (
                x['relevance_score'], 
                x['lastmod'] or datetime.min
            ), reverse=True)
        
        logger.info(f"Categorías encontradas: {dict(categories)}")
        return dict(categories)

    def _is_product_url(self, url: str) -> bool:
        """Detecta si es URL de producto."""
        product_patterns = [
            r'/product/', r'/products/', r'/item/', r'/items/',
            r'/shop/', r'/tienda/', r'/comprar/', r'/buy/',
            r'/\d+$',  # URLs que terminan en números (IDs)
            r'/[a-z0-9-]+-\d+$'  # URLs con formato producto-123
        ]
        return any(re.search(pattern, url.lower()) for pattern in product_patterns)

    def _is_blog_url(self, url: str) -> bool:
        """Detecta si es URL de blog."""
        blog_patterns = [
            r'/blog/', r'/news/', r'/noticias/', r'/articulos/',
            r'/post/', r'/posts/', r'/article/', r'/articles/',
            r'/tutorial/', r'/guia/', r'/guide/'
        ]
        return any(re.search(pattern, url.lower()) for pattern in blog_patterns)

    def _is_category_url(self, url: str) -> bool:
        """Detecta si es URL de categoría."""
        category_patterns = [
            r'/category/', r'/categoria/', r'/categorias/',
            r'/section/', r'/seccion/', r'/departamento/',
            r'/department/', r'/rubro/'
        ]
        return any(re.search(pattern, url.lower()) for pattern in category_patterns)

    def _is_landing_page(self, url: str) -> bool:
        """Detecta si es página de aterrizaje."""
        landing_patterns = [
            r'/$',  # Página principal
            r'/home/', r'/inicio/', r'/principal/',
            r'/about/', r'/acerca/', r'/nosotros/',
            r'/contact/', r'/contacto/', r'/contactanos/'
        ]
        return any(re.search(pattern, url.lower()) for pattern in landing_patterns)

    def _select_by_categories(self, categories: Dict[str, List[Dict[str, Any]]], max_urls: int) -> List[str]:
        """Selecciona URLs balanceando categorías."""
        selected_urls = []
        
        # Priorizar categorías importantes
        priority_categories = ['products', 'blog', 'categories', 'landing', 'other']
        
        # Distribución aproximada
        category_limits = {
            'products': max(1, max_urls // 3),
            'blog': max(1, max_urls // 4),
            'categories': max(1, max_urls // 6),
            'landing': max(1, max_urls // 8),
            'other': max(1, max_urls // 8)
        }
        
        for category in priority_categories:
            if category in categories and len(selected_urls) < max_urls:
                category_urls = categories[category][:category_limits[category]]
                for url_data in category_urls:
                    if len(selected_urls) < max_urls:
                        selected_urls.append(url_data['url'])
        
        # Si no se alcanzó el límite, llenar con las más relevantes
        if len(selected_urls) < max_urls:
            all_urls = []
            for category_urls in categories.values():
                all_urls.extend(category_urls)
            
            all_urls.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            for url_data in all_urls:
                if url_data['url'] not in selected_urls and len(selected_urls) < max_urls:
                    selected_urls.append(url_data['url'])
        
        return selected_urls[:max_urls]

    def _select_by_relevance(self, urls: List[Dict[str, Any]], max_urls: int) -> List[str]:
        """Selecciona URLs por relevancia como fallback."""
        urls.sort(key=lambda x: x['relevance_score'], reverse=True)
        return [url_data['url'] for url_data in urls[:max_urls]]

    async def get_intelligent_urls(self, domain: str, max_urls: int = 15) -> List[str]:
        """
        Obtiene URLs de forma inteligente usando sitemap con filtrado por categorías y fecha.
        
        Args:
            domain: Dominio a analizar
            max_urls: Número máximo de URLs a retornar
            
        Returns:
            Lista de URLs seleccionadas inteligentemente
        """
        try:
            async with HTTPFetcher() as fetcher:
                # Descubrir sitemap
                sitemap_url = await self.discover_sitemap(domain, fetcher)
                
                if not sitemap_url:
                    logger.warning(f"No se encontró sitemap para {domain}, usando crawl de fallback")
                    fallback_urls = await self.crawl_fallback(domain, fetcher, max_urls)
                    return [url_data['url'] for url_data in fallback_urls[:max_urls]]
                
                # Parsear sitemap con fechas
                urls_with_dates = await self.parse_sitemap_with_dates(sitemap_url, fetcher)
                
                if not urls_with_dates:
                    logger.warning(f"No se obtuvieron URLs del sitemap, usando crawl de fallback")
                    fallback_urls = await self.crawl_fallback(domain, fetcher, max_urls)
                    return [url_data['url'] for url_data in fallback_urls[:max_urls]]
                
                # Seleccionar URLs inteligentemente
                selected_urls = self._select_intelligent_urls(urls_with_dates, domain, max_urls)
                
                logger.info(f"URLs inteligentes seleccionadas para {domain}: {len(selected_urls)}")
                return selected_urls
                
        except Exception as e:
            logger.error(f"Error obteniendo URLs inteligentes para {domain}: {e}")
            return []


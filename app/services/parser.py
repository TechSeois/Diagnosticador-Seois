"""
Parser HTML completo para extracción de metas, headings, texto limpio y schema.org.
Usa selectolax para parsing rápido y eficiente.
"""
import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
from selectolax.parser import HTMLParser

from app.services.utils import TextUtils, URLUtils, get_reading_time_minutes

logger = logging.getLogger(__name__)


class HTMLParserService:
    """Servicio principal para parsing de HTML."""
    
    def __init__(self):
        self.text_utils = TextUtils()
        self.url_utils = URLUtils()
    
    def parse_html(self, html_content: str, base_url: str) -> Dict[str, Any]:
        """
        Parsea HTML completo y extrae toda la información estructurada.
        
        Args:
            html_content: Contenido HTML como string
            base_url: URL base para resolver enlaces relativos
            
        Returns:
            Diccionario con toda la información extraída
        """
        try:
            tree = HTMLParser(html_content)
            
            result = {
                'meta': self._extract_meta_data(tree),
                'headings': self._extract_headings(tree),
                'main_content': self._extract_main_content(tree),
                'schema_data': self._extract_schema_data(tree),
                'links': self._extract_links(tree, base_url),
                'stats': self._calculate_stats(tree)
            }
            
            logger.info(f"HTML parseado exitosamente para {base_url}")
            return result
            
        except Exception as e:
            logger.error(f"Error parseando HTML para {base_url}: {e}")
            return self._get_empty_result()
    
    def _extract_meta_data(self, tree: HTMLParser) -> Dict[str, Optional[str]]:
        """Extrae metadatos de la página."""
        meta = {
            'title': None,
            'description': None,
            'og_title': None,
            'og_description': None,
            'canonical': None,
            'lang': 'es'
        }
        
        # Título
        title_tag = tree.css_first('title')
        if title_tag:
            meta['title'] = self.text_utils.clean_html_text(title_tag.text())
        
        # Meta description
        desc_tag = tree.css_first('meta[name="description"]')
        if desc_tag:
            meta['description'] = desc_tag.attributes.get('content', '').strip()
        
        # Open Graph
        og_title = tree.css_first('meta[property="og:title"]')
        if og_title:
            meta['og_title'] = og_title.attributes.get('content', '').strip()
        
        og_desc = tree.css_first('meta[property="og:description"]')
        if og_desc:
            meta['og_description'] = og_desc.attributes.get('content', '').strip()
        
        # Canonical
        canonical = tree.css_first('link[rel="canonical"]')
        if canonical:
            meta['canonical'] = canonical.attributes.get('href', '').strip()
        
        # Idioma
        html_tag = tree.css_first('html')
        if html_tag:
            lang = html_tag.attributes.get('lang', 'es')
            meta['lang'] = lang.split('-')[0]  # Solo el código principal
        
        return meta
    
    def _extract_headings(self, tree: HTMLParser) -> Dict[str, List[str]]:
        """Extrae headings H1-H3."""
        headings = {'h1': [], 'h2': [], 'h3': []}
        
        for level in ['h1', 'h2', 'h3']:
            heading_tags = tree.css(f'{level}')
            for tag in heading_tags:
                text = self.text_utils.clean_html_text(tag.text())
                if text and len(text.strip()) > 0:
                    headings[level].append(text.strip())
        
        return headings
    
    def _extract_main_content(self, tree: HTMLParser) -> str:
        """
        Extrae contenido principal usando heurística tipo Readability.
        Prioriza <main>, <article>, y bloques con alta densidad de texto.
        """
        # Selectores prioritarios para contenido principal
        priority_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.main-content',
            '.content',
            '.post-content',
            '.entry-content'
        ]
        
        main_content = ""
        
        # Buscar en selectores prioritarios
        for selector in priority_selectors:
            elements = tree.css(selector)
            if elements:
                for element in elements:
                    content = self._extract_text_from_element(element)
                    if len(content) > len(main_content):
                        main_content = content
        
        # Si no se encontró contenido principal, usar heurística
        if not main_content or len(main_content) < 100:
            main_content = self._extract_content_heuristic(tree)
        
        return main_content
    
    def _extract_text_from_element(self, element) -> str:
        """Extrae texto limpio de un elemento HTML."""
        # Eliminar elementos no deseados
        for unwanted in element.css('script, style, svg, noscript, nav, footer, aside'):
            unwanted.decompose()
        
        # Extraer texto
        text = element.text()
        return self.text_utils.clean_html_text(text)
    
    def _extract_content_heuristic(self, tree: HTMLParser) -> str:
        """
        Heurística para encontrar contenido principal basada en densidad de texto.
        """
        # Elementos candidatos (excluyendo los ya procesados)
        candidates = []
        
        # Buscar divs y sections con contenido sustancial
        for tag in tree.css('div, section, p'):
            if self._is_content_candidate(tag):
                text = self._extract_text_from_element(tag)
                if len(text) > 50:  # Mínimo de contenido
                    candidates.append((tag, text, len(text)))
        
        # Ordenar por longitud de texto
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        # Tomar los mejores candidatos
        main_content_parts = []
        for _, text, _ in candidates[:5]:  # Top 5 candidatos
            main_content_parts.append(text)
        
        return ' '.join(main_content_parts)
    
    def _is_content_candidate(self, element) -> bool:
        """Determina si un elemento es candidato para contenido principal."""
        # Excluir elementos de navegación y estructura
        excluded_classes = [
            'nav', 'navigation', 'menu', 'sidebar', 'footer', 'header',
            'breadcrumb', 'pagination', 'social', 'share', 'comments',
            'advertisement', 'ad', 'banner', 'widget'
        ]
        
        # Verificar clases CSS
        class_attr = element.attributes.get('class', '').lower()
        for excluded in excluded_classes:
            if excluded in class_attr:
                return False
        
        # Verificar ID
        id_attr = element.attributes.get('id', '').lower()
        for excluded in excluded_classes:
            if excluded in id_attr:
                return False
        
        # Verificar densidad de enlaces (penalizar elementos con muchos enlaces)
        links = element.css('a')
        text_length = len(element.text() or '')
        
        if text_length > 0 and len(links) / text_length > 0.1:  # Más del 10% enlaces
            return False
        
        return True
    
    def _extract_schema_data(self, tree: HTMLParser) -> Dict[str, Any]:
        """Extrae datos de schema.org (JSON-LD y microdata)."""
        schema_data = {
            'json_ld': [],
            'microdata': [],
            'types': set()
        }
        
        # JSON-LD
        json_ld_scripts = tree.css('script[type="application/ld+json"]')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.text())
                schema_data['json_ld'].append(data)
                
                # Extraer tipos
                if isinstance(data, dict):
                    schema_type = data.get('@type', '')
                    if schema_type:
                        schema_data['types'].add(schema_type)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_type = item.get('@type', '')
                            if schema_type:
                                schema_data['types'].add(schema_type)
                                
            except json.JSONDecodeError:
                logger.warning("Error parseando JSON-LD")
        
        # Microdata
        microdata_elements = tree.css('[itemtype]')
        for element in microdata_elements:
            itemtype = element.attributes.get('itemtype', '')
            if itemtype:
                schema_data['types'].add(itemtype.split('/')[-1])  # Solo el nombre del tipo
                
                # Extraer propiedades
                properties = {}
                for prop_element in element.css('[itemprop]'):
                    prop_name = prop_element.attributes.get('itemprop', '')
                    prop_value = prop_element.text() or prop_element.attributes.get('content', '')
                    if prop_name and prop_value:
                        properties[prop_name] = prop_value.strip()
                
                if properties:
                    schema_data['microdata'].append({
                        'type': itemtype,
                        'properties': properties
                    })
        
        # Convertir set a list para serialización
        schema_data['types'] = list(schema_data['types'])
        
        return schema_data
    
    def _extract_links(self, tree: HTMLParser, base_url: str) -> Dict[str, List[str]]:
        """Extrae enlaces internos y externos."""
        links = {'internal': [], 'external': []}
        
        link_elements = tree.css('a[href]')
        base_domain = self.url_utils.get_domain(base_url)
        
        for link in link_elements:
            href = link.attributes.get('href', '')
            if not href:
                continue
            
            # Resolver URL relativa
            full_url = urljoin(base_url, href)
            
            # Verificar si es válida
            if not self.url_utils.is_valid_url(full_url):
                continue
            
            # Clasificar como interno o externo
            if self.url_utils.is_internal_link(full_url, base_domain):
                links['internal'].append(full_url)
            else:
                links['external'].append(full_url)
        
        # Eliminar duplicados
        links['internal'] = list(set(links['internal']))
        links['external'] = list(set(links['external']))
        
        return links
    
    def _calculate_stats(self, tree: HTMLParser) -> Dict[str, int]:
        """Calcula estadísticas de la página."""
        # Contar palabras en contenido principal
        main_content = self._extract_main_content(tree)
        word_count = len(self.text_utils.tokenize_text(main_content))
        
        # Contar enlaces
        internal_links = len(tree.css('a[href]'))
        external_links = 0  # Se calculará en _extract_links
        
        # Tiempo de lectura estimado
        reading_time = get_reading_time_minutes(word_count)
        
        return {
            'words': word_count,
            'reading_time_min': reading_time,
            'internal_links': internal_links,
            'external_links': external_links  # Se actualizará después
        }
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Retorna resultado vacío en caso de error."""
        return {
            'meta': {
                'title': None, 'description': None, 'og_title': None,
                'og_description': None, 'canonical': None, 'lang': 'es'
            },
            'headings': {'h1': [], 'h2': [], 'h3': []},
            'main_content': '',
            'schema_data': {'json_ld': [], 'microdata': [], 'types': []},
            'links': {'internal': [], 'external': []},
            'stats': {'words': 0, 'reading_time_min': 0, 'internal_links': 0, 'external_links': 0}
        }
    
    def extract_products_from_schema(self, schema_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae productos específicamente de datos de schema.org."""
        products = []
        
        # Buscar en JSON-LD
        for data in schema_data.get('json_ld', []):
            if isinstance(data, dict) and data.get('@type') == 'Product':
                product = self._parse_product_schema(data)
                if product:
                    products.append(product)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        product = self._parse_product_schema(item)
                        if product:
                            products.append(product)
        
        # Buscar en microdata
        for item in schema_data.get('microdata', []):
            if 'Product' in item.get('type', ''):
                product = self._parse_product_microdata(item)
                if product:
                    products.append(product)
        
        return products
    
    def _parse_product_schema(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parsea un producto de schema.org JSON-LD."""
        try:
            product = {
                'nombre': data.get('name', ''),
                'categoria': None,
                'marca': None,
                'precio': None,
                'moneda': None
            }
            
            # Categoría
            if 'category' in data:
                category = data['category']
                if isinstance(category, str):
                    product['categoria'] = category
                elif isinstance(category, dict):
                    product['categoria'] = category.get('name', '')
            
            # Marca
            if 'brand' in data:
                brand = data['brand']
                if isinstance(brand, str):
                    product['marca'] = brand
                elif isinstance(brand, dict):
                    product['marca'] = brand.get('name', '')
            
            # Precio
            if 'offers' in data:
                offers = data['offers']
                if isinstance(offers, dict):
                    price_info = self._extract_price_from_offer(offers)
                    if price_info:
                        product['precio'] = price_info['price']
                        product['moneda'] = price_info['currency']
                elif isinstance(offers, list) and offers:
                    price_info = self._extract_price_from_offer(offers[0])
                    if price_info:
                        product['precio'] = price_info['price']
                        product['moneda'] = price_info['currency']
            
            return product if product['nombre'] else None
            
        except Exception as e:
            logger.warning(f"Error parseando producto schema: {e}")
            return None
    
    def _parse_product_microdata(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parsea un producto de microdata."""
        try:
            properties = item.get('properties', {})
            
            product = {
                'nombre': properties.get('name', ''),
                'categoria': properties.get('category', None),
                'marca': properties.get('brand', None),
                'precio': None,
                'moneda': None
            }
            
            # Buscar precio en propiedades
            price_text = properties.get('price', '')
            if price_text:
                price_info = self.text_utils.extract_price(price_text)
                if price_info:
                    product['precio'] = price_info['price']
                    product['moneda'] = price_info['currency']
            
            return product if product['nombre'] else None
            
        except Exception as e:
            logger.warning(f"Error parseando producto microdata: {e}")
            return None
    
    def _extract_price_from_offer(self, offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrae precio de una oferta de schema.org."""
        try:
            price = offer.get('price', '')
            currency = offer.get('priceCurrency', 'EUR')
            
            if price:
                if isinstance(price, (int, float)):
                    return {'price': float(price), 'currency': currency}
                elif isinstance(price, str):
                    price_info = self.text_utils.extract_price(price)
                    if price_info:
                        return {'price': price_info['price'], 'currency': currency}
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extrayendo precio de oferta: {e}")
            return None


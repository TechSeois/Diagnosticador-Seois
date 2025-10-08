"""
Clasificador para determinar tipo de página (blog/e-commerce), audiencia e intención.
Implementa heurísticas basadas en contenido, schema.org y patrones de texto.
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

from app.config import get_settings
from app.services.utils import RegexPatterns

logger = logging.getLogger(__name__)
settings = get_settings()


class PageClassifier:
    """Clasificador principal para páginas web."""
    
    def __init__(self):
        self.patterns = RegexPatterns()
    
    def classify_page_type(self, parsed_data: Dict[str, Any], url: str) -> str:
        """
        Clasifica el tipo de página: ecommerce, blog, o mixto.
        
        Args:
            parsed_data: Datos parseados del HTML
            url: URL de la página
            
        Returns:
            Tipo de página: 'ecommerce', 'blog', o 'mixto'
        """
        try:
            # Calcular scores para cada tipo
            ecommerce_score = self._calculate_ecommerce_score(parsed_data, url)
            blog_score = self._calculate_blog_score(parsed_data, url)
            
            logger.debug(f"Scores - E-commerce: {ecommerce_score:.2f}, Blog: {blog_score:.2f}")
            
            # Determinar tipo basado en scores y umbrales
            score_diff = abs(ecommerce_score - blog_score)
            
            if score_diff < settings.mixed_threshold:
                return 'mixto'
            elif ecommerce_score > blog_score and ecommerce_score > settings.ecommerce_threshold:
                return 'ecommerce'
            elif blog_score > ecommerce_score:
                return 'blog'
            else:
                return 'mixto'
                
        except Exception as e:
            logger.error(f"Error clasificando tipo de página: {e}")
            return 'mixto'
    
    def _calculate_ecommerce_score(self, parsed_data: Dict[str, Any], url: str) -> float:
        """Calcula score para clasificación e-commerce."""
        score = 0.0
        
        # Schema.org Product/Offer
        schema_types = parsed_data.get('schema_data', {}).get('types', [])
        if 'Product' in schema_types:
            score += 0.4
        if 'Offer' in schema_types:
            score += 0.3
        
        # Contenido de texto
        main_content = parsed_data.get('main_content', '')
        meta_data = parsed_data.get('meta', {})
        
        # Combinar texto para análisis
        text_to_analyze = f"{main_content} {meta_data.get('title', '')} {meta_data.get('description', '')}"
        
        # Patrones de e-commerce en texto
        if self.patterns.ECOMMERCE_PATTERNS['price_keywords'].search(text_to_analyze):
            score += 0.2
        if self.patterns.ECOMMERCE_PATTERNS['cart_keywords'].search(text_to_analyze):
            score += 0.2
        if self.patterns.ECOMMERCE_PATTERNS['product_keywords'].search(text_to_analyze):
            score += 0.15
        
        # Patrones en URL
        if self.patterns.ECOMMERCE_PATTERNS['ecommerce_paths'].search(url):
            score += 0.25
        
        # Open Graph type
        og_type = meta_data.get('og_type', '')
        if 'product' in og_type.lower():
            score += 0.2
        
        # Headings con contenido comercial
        headings = parsed_data.get('headings', {})
        for heading_list in headings.values():
            for heading in heading_list:
                if self.patterns.ECOMMERCE_PATTERNS['price_keywords'].search(heading):
                    score += 0.1
                if self.patterns.ECOMMERCE_PATTERNS['product_keywords'].search(heading):
                    score += 0.1
        
        return min(score, 1.0)  # Normalizar a máximo 1.0
    
    def _calculate_blog_score(self, parsed_data: Dict[str, Any], url: str) -> float:
        """Calcula score para clasificación blog."""
        score = 0.0
        
        # Schema.org Article/BlogPosting
        schema_types = parsed_data.get('schema_data', {}).get('types', [])
        if 'Article' in schema_types:
            score += 0.3
        if 'BlogPosting' in schema_types:
            score += 0.4
        
        # Contenido de texto
        main_content = parsed_data.get('main_content', '')
        meta_data = parsed_data.get('meta', {})
        
        # Combinar texto para análisis
        text_to_analyze = f"{main_content} {meta_data.get('title', '')} {meta_data.get('description', '')}"
        
        # Patrones de blog en texto
        if self.patterns.BLOG_PATTERNS['article_keywords'].search(text_to_analyze):
            score += 0.2
        if self.patterns.BLOG_PATTERNS['author_keywords'].search(text_to_analyze):
            score += 0.15
        if self.patterns.BLOG_PATTERNS['date_keywords'].search(text_to_analyze):
            score += 0.15
        
        # Patrones en URL
        if self.patterns.BLOG_PATTERNS['blog_paths'].search(url):
            score += 0.3
        
        # Open Graph type
        og_type = meta_data.get('og_type', '')
        if 'article' in og_type.lower():
            score += 0.2
        
        # Detectar fecha de publicación en contenido
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD/MM/YYYY o DD-MM-YYYY
            r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text_to_analyze, re.IGNORECASE):
                score += 0.1
                break
        
        # Detectar autor en contenido
        author_patterns = [
            r'\b(por|escrito por|autor|author)\s+[A-Za-z\s]+',
            r'\b(publicado por|published by)\s+[A-Za-z\s]+'
        ]
        
        for pattern in author_patterns:
            if re.search(pattern, text_to_analyze, re.IGNORECASE):
                score += 0.1
                break
        
        return min(score, 1.0)  # Normalizar a máximo 1.0
    
    def detect_audience(self, parsed_data: Dict[str, Any]) -> List[str]:
        """
        Detecta la audiencia objetivo de la página.
        
        Args:
            parsed_data: Datos parseados del HTML
            
        Returns:
            Lista de audiencias detectadas
        """
        audiences = []
        
        try:
            # Combinar todo el texto para análisis
            main_content = parsed_data.get('main_content', '')
            meta_data = parsed_data.get('meta', {})
            headings = parsed_data.get('headings', {})
            
            text_to_analyze = f"{main_content} {meta_data.get('title', '')} {meta_data.get('description', '')}"
            
            # Añadir headings
            for heading_list in headings.values():
                text_to_analyze += " " + " ".join(heading_list)
            
            # Detectar cada tipo de audiencia
            for audience_type, pattern in self.patterns.AUDIENCE_PATTERNS.items():
                if pattern.search(text_to_analyze):
                    audiences.append(audience_type)
            
            # Detectar audiencia B2B/B2C basada en contenido
            b2b_keywords = ['empresa', 'empresas', 'corporativo', 'corporación', 'B2B', 'negocio', 'negocios']
            b2c_keywords = ['consumidor', 'consumidores', 'cliente', 'clientes', 'particular', 'particulares', 'B2C']
            
            text_lower = text_to_analyze.lower()
            b2b_count = sum(text_lower.count(keyword) for keyword in b2b_keywords)
            b2c_count = sum(text_lower.count(keyword) for keyword in b2c_keywords)
            
            if b2b_count > b2c_count and b2b_count > 2:
                audiences.append('B2B')
            elif b2c_count > b2b_count and b2c_count > 2:
                audiences.append('B2C')
            
            # Eliminar duplicados y ordenar
            audiences = list(set(audiences))
            
            logger.debug(f"Audiencias detectadas: {audiences}")
            return audiences
            
        except Exception as e:
            logger.error(f"Error detectando audiencia: {e}")
            return []
    
    def detect_intent(self, parsed_data: Dict[str, Any], url: str) -> str:
        """
        Detecta la intención principal de la página.
        
        Args:
            parsed_data: Datos parseados del HTML
            url: URL de la página
            
        Returns:
            Intención: 'comercial', 'consideracion', o 'informacional'
        """
        try:
            # Combinar texto para análisis
            main_content = parsed_data.get('main_content', '')
            meta_data = parsed_data.get('meta', {})
            headings = parsed_data.get('headings', {})
            
            text_to_analyze = f"{main_content} {meta_data.get('title', '')} {meta_data.get('description', '')}"
            
            # Añadir headings
            for heading_list in headings.values():
                text_to_analyze += " " + " ".join(heading_list)
            
            # Calcular scores para cada intención
            commercial_score = self._calculate_commercial_score(text_to_analyze, url)
            consideration_score = self._calculate_consideration_score(text_to_analyze, url)
            informational_score = self._calculate_informational_score(text_to_analyze, url)
            
            logger.debug(f"Scores intención - Comercial: {commercial_score:.2f}, "
                        f"Consideración: {consideration_score:.2f}, "
                        f"Informacional: {informational_score:.2f}")
            
            # Determinar intención con mayor score
            scores = {
                'comercial': commercial_score,
                'consideracion': consideration_score,
                'informacional': informational_score
            }
            
            intent = max(scores, key=scores.get)
            
            # Si el score es muy bajo, usar informacional por defecto
            if scores[intent] < 0.1:
                intent = 'informacional'
            
            return intent
            
        except Exception as e:
            logger.error(f"Error detectando intención: {e}")
            return 'informacional'
    
    def _calculate_commercial_score(self, text: str, url: str) -> float:
        """Calcula score para intención comercial."""
        score = 0.0
        
        # Patrones comerciales en texto
        if self.patterns.INTENT_PATTERNS['commercial'].search(text):
            score += 0.4
        
        # Patrones en URL
        commercial_url_patterns = [
            r'/(comprar|buy|purchase|carrito|cart|checkout|pagar|payment)/',
            r'/(oferta|offer|descuento|discount|promocion|promotion)/',
            r'/(tienda|shop|store|venta|sale)/'
        ]
        
        for pattern in commercial_url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                score += 0.3
        
        # Detectar CTAs comerciales
        cta_patterns = [
            r'\b(comprar ahora|buy now|añadir al carrito|add to cart)\b',
            r'\b(solicitar presupuesto|request quote|contactar|contact)\b',
            r'\b(reservar|book|reserve|inscribirse|sign up)\b'
        ]
        
        for pattern in cta_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_consideration_score(self, text: str, url: str) -> float:
        """Calcula score para intención de consideración."""
        score = 0.0
        
        # Patrones de consideración en texto
        if self.patterns.INTENT_PATTERNS['consideration'].search(text):
            score += 0.4
        
        # Patrones en URL
        consideration_url_patterns = [
            r'/(comparar|compare|comparativa|comparison)/',
            r'/(mejor|best|top|ranking|rankings)/',
            r'/(opiniones|reviews|reseñas|test|tests)/',
            r'/(vs|versus|comparacion|comparison)/'
        ]
        
        for pattern in consideration_url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                score += 0.3
        
        # Detectar contenido comparativo
        comparison_patterns = [
            r'\b(mejor|best|top|ranking)\s+\w+',
            r'\b(comparar|compare|comparativa)\s+\w+',
            r'\b(vs|versus|frente a)\b',
            r'\b(pros y contras|pros and cons)\b'
        ]
        
        for pattern in comparison_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_informational_score(self, text: str, url: str) -> float:
        """Calcula score para intención informacional."""
        score = 0.0
        
        # Patrones informacionales en texto
        if self.patterns.INTENT_PATTERNS['informational'].search(text):
            score += 0.4
        
        # Patrones en URL
        informational_url_patterns = [
            r'/(guia|guide|tutorial|tutoriales|como|cómo|how)/',
            r'/(que es|qué es|what is|definicion|definition)/',
            r'/(aprender|learn|conocimiento|knowledge)/',
            r'/(blog|articulo|article|noticia|news)/'
        ]
        
        for pattern in informational_url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                score += 0.3
        
        # Detectar contenido educativo
        educational_patterns = [
            r'\b(guía|guide|tutorial|tutoriales)\s+\w+',
            r'\b(cómo|how to|como hacer|how to do)\b',
            r'\b(qué es|what is|definición|definition)\b',
            r'\b(aprender|learn|conocer|know)\b',
            r'\b(paso a paso|step by step)\b'
        ]
        
        for pattern in educational_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.2
        
        # Bonus por contenido largo (típico de contenido informacional)
        word_count = len(text.split())
        if word_count > 500:
            score += 0.1
        if word_count > 1000:
            score += 0.1
        
        return min(score, 1.0)
    
    def extract_brand_info(self, parsed_data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """
        Extrae información de marca del contenido.
        
        Args:
            parsed_data: Datos parseados del HTML
            url: URL de la página
            
        Returns:
            Diccionario con información de marca
        """
        brand_info = {
            'name': None,
            'domain': None,
            'confidence': 0.0
        }
        
        try:
            # Extraer dominio como marca base
            domain = urlparse(url).netloc.replace('www.', '')
            brand_info['domain'] = domain
            
            # Buscar en schema.org
            schema_data = parsed_data.get('schema_data', {})
            for json_ld in schema_data.get('json_ld', []):
                if isinstance(json_ld, dict):
                    # Buscar Organization o Brand
                    if json_ld.get('@type') in ['Organization', 'Brand', 'Corporation']:
                        brand_name = json_ld.get('name', '')
                        if brand_name:
                            brand_info['name'] = brand_name
                            brand_info['confidence'] = 0.8
                            break
            
            # Buscar en microdata
            if not brand_info['name']:
                for microdata in schema_data.get('microdata', []):
                    if microdata.get('type') and 'Organization' in microdata.get('type', ''):
                        brand_name = microdata.get('properties', {}).get('name', '')
                        if brand_name:
                            brand_info['name'] = brand_name
                            brand_info['confidence'] = 0.7
                            break
            
            # Fallback: usar título de la página
            if not brand_info['name']:
                title = parsed_data.get('meta', {}).get('title', '')
                if title:
                    # Extraer primera parte del título como posible marca
                    brand_name = title.split(' - ')[0].split(' | ')[0].strip()
                    if len(brand_name) > 2 and len(brand_name) < 50:
                        brand_info['name'] = brand_name
                        brand_info['confidence'] = 0.3
            
            logger.debug(f"Información de marca extraída: {brand_info}")
            return brand_info
            
        except Exception as e:
            logger.error(f"Error extrayendo información de marca: {e}")
            return brand_info


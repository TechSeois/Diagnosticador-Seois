"""
Utilidades comunes: stopwords, helpers, regex patterns.
"""
import re
import string
from typing import List, Set, Dict, Any
import nltk
from nltk.corpus import stopwords


# Descargar stopwords de NLTK si no están disponibles
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('stopwords', quiet=True)
    except Exception as e:
        # En entornos con permisos restringidos (Docker, Cloud Run)
        # los datos ya deberían estar descargados en build time
        print(f"Warning: Could not download NLTK stopwords: {e}")
        print("Assuming stopwords are already available in the system.")


class TextUtils:
    """Utilidades para procesamiento de texto."""
    
    # Stopwords combinadas ES/EN
    STOPWORDS_ES = set(stopwords.words('spanish'))
    STOPWORDS_EN = set(stopwords.words('english'))
    STOPWORDS_COMBINED = STOPWORDS_ES.union(STOPWORDS_EN)
    
    # Stopwords adicionales específicas del dominio
    ADDITIONAL_STOPWORDS = {
        'página', 'página', 'sitio', 'web', 'website', 'www', 'http', 'https',
        'com', 'es', 'org', 'net', 'click', 'aquí', 'aquí', 'más', 'ver',
        'leer', 'continuar', 'siguiente', 'anterior', 'inicio', 'home',
        'contacto', 'sobre', 'nosotros', 'servicios', 'productos', 'tienda',
        'carrito', 'comprar', 'añadir', 'agregar', 'buscar', 'buscar',
        'menú', 'navegación', 'footer', 'header', 'sidebar', 'lateral'
    }
    
    ALL_STOPWORDS = STOPWORDS_COMBINED.union(ADDITIONAL_STOPWORDS)
    
    # Patrones regex comunes
    PATTERNS = {
        'price': re.compile(r'[\d.,]+\s*(€|EUR|USD|\$|pesos?|euros?)', re.IGNORECASE),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'(\+?34|0034)?[6-9]\d{8}'),
        'url': re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
        'clean_text': re.compile(r'[^\w\s]', re.UNICODE),
        'multiple_spaces': re.compile(r'\s+'),
        'html_tags': re.compile(r'<[^>]+>'),
        'whitespace': re.compile(r'\s+')
    }
    
    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normaliza texto: lowercase, quita puntuación, espacios múltiples."""
        if not text:
            return ""
        
        # Convertir a lowercase
        text = text.lower()
        
        # Quitar HTML tags si los hay
        text = cls.PATTERNS['html_tags'].sub(' ', text)
        
        # Quitar puntuación pero mantener espacios
        text = cls.PATTERNS['clean_text'].sub(' ', text)
        
        # Normalizar espacios múltiples
        text = cls.PATTERNS['multiple_spaces'].sub(' ', text)
        
        return text.strip()
    
    @classmethod
    def tokenize_text(cls, text: str) -> List[str]:
        """Tokeniza texto normalizado."""
        normalized = cls.normalize_text(text)
        return [token for token in normalized.split() if token and len(token) > 1]
    
    @classmethod
    def remove_stopwords(cls, tokens: List[str]) -> List[str]:
        """Elimina stopwords de una lista de tokens."""
        return [token for token in tokens if token not in cls.ALL_STOPWORDS]
    
    @classmethod
    def extract_price(cls, text: str) -> Dict[str, Any]:
        """Extrae precio y moneda de texto."""
        match = cls.PATTERNS['price'].search(text)
        if match:
            price_text = match.group(0)
            # Extraer número
            price_num = re.search(r'[\d.,]+', price_text)
            if price_num:
                try:
                    price = float(price_num.group(0).replace(',', '.'))
                    # Detectar moneda
                    currency = 'EUR'
                    if '$' in price_text or 'USD' in price_text:
                        currency = 'USD'
                    elif 'pesos' in price_text.lower():
                        currency = 'MXN'
                    
                    return {'price': price, 'currency': currency, 'text': price_text}
                except ValueError:
                    pass
        return None
    
    @classmethod
    def clean_html_text(cls, html_text: str) -> str:
        """Limpia texto HTML manteniendo solo contenido textual."""
        if not html_text:
            return ""
        
        # Quitar scripts, styles, etc.
        text = re.sub(r'<(script|style|svg|noscript)[^>]*>.*?</\1>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Quitar todos los tags HTML
        text = cls.PATTERNS['html_tags'].sub(' ', text)
        
        # Decodificar entidades HTML básicas
        html_entities = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'",
            '&nbsp;': ' ', '&copy;': '©', '&reg;': '®', '&trade;': '™'
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        # Normalizar espacios
        text = cls.PATTERNS['whitespace'].sub(' ', text)
        
        return text.strip()


class URLUtils:
    """Utilidades para manejo de URLs."""
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normaliza URL añadiendo protocolo si falta."""
        if not url.startswith(('http://', 'https://')):
            return f"https://{url}"
        return url
    
    @staticmethod
    def get_domain(url: str) -> str:
        """Extrae dominio de una URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    @staticmethod
    def is_internal_link(url: str, base_domain: str) -> bool:
        """Verifica si un enlace es interno al dominio base."""
        from urllib.parse import urlparse
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_domain)
            return parsed_url.netloc == parsed_base.netloc
        except:
            return False
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Verifica si una URL es válida."""
        from urllib.parse import urlparse
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False


class RegexPatterns:
    """Patrones regex para detección de contenido específico."""
    
    # Patrones para clasificación de páginas
    ECOMMERCE_PATTERNS = {
        'price_keywords': re.compile(r'\b(precio|price|cost|coste|costo|€|\$|eur|usd)\b', re.IGNORECASE),
        'cart_keywords': re.compile(r'\b(añadir|agregar|add|carrito|cart|comprar|buy|comprar)\b', re.IGNORECASE),
        'product_keywords': re.compile(r'\b(producto|product|item|artículo|sku|código)\b', re.IGNORECASE),
        'ecommerce_paths': re.compile(r'/(producto|product|tienda|shop|cart|carrito|checkout)/', re.IGNORECASE)
    }
    
    BLOG_PATTERNS = {
        'article_keywords': re.compile(r'\b(artículo|article|post|entrada|blog|noticia|news)\b', re.IGNORECASE),
        'author_keywords': re.compile(r'\b(autor|author|escrito|por|by)\b', re.IGNORECASE),
        'date_keywords': re.compile(r'\b(fecha|date|publicado|published|ago|hace)\b', re.IGNORECASE),
        'blog_paths': re.compile(r'/(blog|articulo|article|post|noticia|news)/', re.IGNORECASE)
    }
    
    # Patrones para detección de audiencia
    AUDIENCE_PATTERNS = {
        'beginners': re.compile(r'\b(principiantes|para empezar|básico|básica|iniciación|inicio)\b', re.IGNORECASE),
        'professionals': re.compile(r'\b(profesionales|empresas|B2B|corporativo|corporación|empresarial)\b', re.IGNORECASE),
        'children': re.compile(r'\b(niños|niñas|infantil|familia|familiar|padres|madres)\b', re.IGNORECASE),
        'women': re.compile(r'\b(mujer|mujeres|ella|femenino|femenina|chica|chicas)\b', re.IGNORECASE),
        'men': re.compile(r'\b(hombre|hombres|él|masculino|masculina|chico|chicos)\b', re.IGNORECASE),
        'gaming': re.compile(r'\b(gaming|juegos|videojuegos|gamer|gamers|playstation|xbox|nintendo)\b', re.IGNORECASE)
    }
    
    # Patrones para detección de intención
    INTENT_PATTERNS = {
        'commercial': re.compile(r'\b(comprar|precio|oferta|descuento|carrito|checkout|pagar)\b', re.IGNORECASE),
        'consideration': re.compile(r'\b(comparar|mejor|vs|versus|opiniones|review|reseña|comparativa)\b', re.IGNORECASE),
        'informational': re.compile(r'\b(guía|tutorial|cómo|qué es|qué son|definición|explicación|aprender)\b', re.IGNORECASE)
    }


def get_reading_time_minutes(word_count: int, words_per_minute: int = 200) -> int:
    """Calcula tiempo de lectura estimado en minutos."""
    return max(1, round(word_count / words_per_minute))


def extract_domain_name(url: str) -> str:
    """Extrae nombre del dominio sin protocolo."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc.replace('www.', '')


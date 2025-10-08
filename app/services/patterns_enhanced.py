"""
Patrones mejorados para clasificación de páginas web con soporte específico para diferentes sectores.
Incluye patrones para sector legal, médico, tecnológico, etc.
"""
import re
from typing import Dict, Pattern

class EnhancedPatterns:
    """Patrones mejorados para clasificación de páginas web."""
    
    def __init__(self):
        # Patrones de e-commerce mejorados
        self.ECOMMERCE_PATTERNS = {
            'price_keywords': re.compile(
                r'\b(precio|price|coste|costo|cost|€|EUR|USD|\$|pesos?|euros?|descuento|discount|oferta|offer|rebaja|sale)\b',
                re.IGNORECASE
            ),
            'cart_keywords': re.compile(
                r'\b(carrito|cart|comprar|buy|purchase|añadir|add|agregar|checkout|pagar|payment|pedido|order)\b',
                re.IGNORECASE
            ),
            'product_keywords': re.compile(
                r'\b(producto|product|artículo|item|modelo|model|marca|brand|stock|disponible|available)\b',
                re.IGNORECASE
            ),
            'ecommerce_paths': re.compile(
                r'/(tienda|shop|store|productos|products|comprar|buy|carrito|cart|checkout|pagar|payment)/',
                re.IGNORECASE
            )
        }
        
        # Patrones de blog mejorados
        self.BLOG_PATTERNS = {
            'article_keywords': re.compile(
                r'\b(artículo|article|post|entrada|entry|blog|noticia|news|tutorial|guía|guide)\b',
                re.IGNORECASE
            ),
            'author_keywords': re.compile(
                r'\b(autor|author|escrito por|written by|publicado por|published by|por|by)\b',
                re.IGNORECASE
            ),
            'date_keywords': re.compile(
                r'\b(fecha|date|publicado|published|creado|created|actualizado|updated)\b',
                re.IGNORECASE
            ),
            'blog_paths': re.compile(
                r'/(blog|articulos|articles|posts|noticias|news|tutoriales|tutorials|guias|guides)/',
                re.IGNORECASE
            )
        }
        
        # Patrones de audiencia mejorados
        self.AUDIENCE_PATTERNS = {
            'empresas': re.compile(
                r'\b(empresa|empresas|corporación|corporation|corporativo|corporate|negocio|negocios|business|B2B)\b',
                re.IGNORECASE
            ),
            'particulares': re.compile(
                r'\b(particular|particulares|consumidor|consumidores|cliente|clientes|usuario|usuarios|B2C)\b',
                re.IGNORECASE
            ),
            'profesionales': re.compile(
                r'\b(profesional|profesionales|experto|expertos|especialista|especialistas|técnico|técnicos)\b',
                re.IGNORECASE
            ),
            'estudiantes': re.compile(
                r'\b(estudiante|estudiantes|alumno|alumnos|aprendiz|aprendices|educación|education)\b',
                re.IGNORECASE
            )
        }
        
        # Patrones de intención mejorados
        self.INTENT_PATTERNS = {
            'commercial': re.compile(
                r'\b(comprar|buy|purchase|contratar|hire|solicitar|request|contactar|contact|reservar|book)\b',
                re.IGNORECASE
            ),
            'consideration': re.compile(
                r'\b(comparar|compare|mejor|best|top|ranking|opiniones|reviews|reseñas|test|tests|vs|versus)\b',
                re.IGNORECASE
            ),
            'informational': re.compile(
                r'\b(qué es|what is|definición|definition|cómo|how|guía|guide|tutorial|aprender|learn|información|information)\b',
                re.IGNORECASE
            )
        }
        
        # Patrones específicos por sector
        self.SECTOR_PATTERNS = {
            'legal': re.compile(
                r'\b(abogado|abogados|abogacía|lawyer|attorney|legal|ley|law|jurídico|juridico|derecho|rights|justicia|justice|tribunal|court|juez|judge|proceso|process|demanda|lawsuit|contrato|contract|asesoría|legal advice)\b',
                re.IGNORECASE
            ),
            'medical': re.compile(
                r'\b(médico|medico|doctor|doctores|salud|health|hospital|clínica|clinica|enfermedad|disease|tratamiento|treatment|medicina|medicine|paciente|patient|consulta|consultation)\b',
                re.IGNORECASE
            ),
            'technology': re.compile(
                r'\b(tecnología|technology|software|hardware|programación|programming|desarrollo|development|aplicación|application|app|sistema|system|digital|informática|informatics)\b',
                re.IGNORECASE
            ),
            'education': re.compile(
                r'\b(educación|education|enseñanza|teaching|aprendizaje|learning|curso|courses|formación|training|estudio|study|academia|academy|universidad|university|colegio|school)\b',
                re.IGNORECASE
            ),
            'finance': re.compile(
                r'\b(financiero|financial|banco|bank|crédito|credit|préstamo|loan|inversión|investment|ahorro|savings|seguro|insurance|contabilidad|accounting)\b',
                re.IGNORECASE
            ),
            'real_estate': re.compile(
                r'\b(inmobiliario|real estate|vivienda|housing|casa|house|apartamento|apartment|alquiler|rent|venta|sale|propiedad|property|inmueble|real estate)\b',
                re.IGNORECASE
            ),
            'sports': re.compile(
                r'\b(deporte|sports|fútbol|football|baloncesto|basketball|tenis|tennis|natación|swimming|gimnasio|gym|fitness|ejercicio|exercise|competencia|competition)\b',
                re.IGNORECASE
            ),
            'food': re.compile(
                r'\b(comida|food|restaurante|restaurant|cocina|kitchen|receta|recipe|ingrediente|ingredient|chef|cocinero|cook|gastronomía|gastronomy)\b',
                re.IGNORECASE
            ),
            'travel': re.compile(
                r'\b(viaje|travel|turismo|tourism|hotel|vuelo|flight|vacaciones|vacation|destino|destination|reserva|booking|alojamiento|accommodation)\b',
                re.IGNORECASE
            ),
            'automotive': re.compile(
                r'\b(automóvil|automobile|coche|car|vehículo|vehicle|moto|motorcycle|concesionario|dealership|taller|garage|repuesto|spare part)\b',
                re.IGNORECASE
            )
        }
        
        # Patrones de contenido específico
        self.CONTENT_PATTERNS = {
            'services': re.compile(
                r'\b(servicio|servicios|service|services|asesoría|consulting|consultoría|consulting|soporte|support|mantenimiento|maintenance)\b',
                re.IGNORECASE
            ),
            'products': re.compile(
                r'\b(producto|productos|product|products|artículo|artículos|item|items|mercancía|merchandise)\b',
                re.IGNORECASE
            ),
            'information': re.compile(
                r'\b(información|information|contenido|content|artículo|article|noticia|news|blog|guía|guide)\b',
                re.IGNORECASE
            ),
            'contact': re.compile(
                r'\b(contacto|contact|teléfono|phone|email|correo|mail|dirección|address|ubicación|location)\b',
                re.IGNORECASE
            )
        }
        
        # Patrones de calidad de contenido
        self.QUALITY_PATTERNS = {
            'professional': re.compile(
                r'\b(profesional|professional|experto|expert|especialista|specialist|certificado|certified|acreditado|accredited)\b',
                re.IGNORECASE
            ),
            'authority': re.compile(
                r'\b(autoridad|authority|líder|leader|referencia|reference|reconocido|recognized|prestigioso|prestigious)\b',
                re.IGNORECASE
            ),
            'trust': re.compile(
                r'\b(confianza|trust|seguro|secure|garantía|guarantee|certificado|certified|verificado|verified)\b',
                re.IGNORECASE
            )
        }
    
    def detect_sector(self, text: str) -> str:
        """
        Detecta el sector principal del contenido.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Sector detectado o 'general' si no se detecta ninguno específico
        """
        sector_scores = {}
        
        for sector, pattern in self.SECTOR_PATTERNS.items():
            matches = pattern.findall(text)
            sector_scores[sector] = len(matches)
        
        if sector_scores:
            max_sector = max(sector_scores, key=sector_scores.get)
            if sector_scores[max_sector] > 0:
                return max_sector
        
        return 'general'
    
    def detect_content_type(self, text: str) -> str:
        """
        Detecta el tipo de contenido principal.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Tipo de contenido detectado
        """
        content_scores = {}
        
        for content_type, pattern in self.CONTENT_PATTERNS.items():
            matches = pattern.findall(text)
            content_scores[content_type] = len(matches)
        
        if content_scores:
            max_content = max(content_scores, key=content_scores.get)
            if content_scores[max_content] > 0:
                return max_content
        
        return 'information'
    
    def calculate_quality_score(self, text: str) -> float:
        """
        Calcula un score de calidad del contenido.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Score de calidad entre 0 y 1
        """
        quality_score = 0.0
        
        for quality_type, pattern in self.QUALITY_PATTERNS.items():
            matches = pattern.findall(text)
            quality_score += len(matches) * 0.1
        
        # Normalizar por longitud del texto
        word_count = len(text.split())
        if word_count > 0:
            quality_score = min(quality_score / (word_count / 100), 1.0)
        
        return quality_score


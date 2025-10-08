"""
Scorer para cálculo de scores de keywords y bucketización.
Implementa ranking y clasificación en buckets según especificación.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.config import get_settings
from app.services.utils import TextUtils
from app.services.nlp import NLPService

logger = logging.getLogger(__name__)
settings = get_settings()


class KeywordScorer:
    """Servicio para scoring y bucketización de keywords."""
    
    def __init__(self):
        self.text_utils = TextUtils()
        self.nlp_service = NLPService()
    
    def calculate_keyword_score(self, keyword: str, text_data: Dict[str, Any], 
                               brand_info: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calcula score completo para una keyword usando la fórmula especificada.
        
        Args:
            keyword: Keyword a evaluar
            text_data: Datos de texto (contenido, metas, headings)
            brand_info: Información de marca
            weights: Pesos personalizados (opcional)
            
        Returns:
            Score normalizado entre 0 y 1
        """
        try:
            if weights is None:
                weights = settings.scoring_weights
            
            # Extraer componentes del score
            freq_score = self._calculate_frequency_score(keyword, text_data)
            tfidf_score = self._calculate_tfidf_score(keyword, text_data)
            cooccurrence_score = self._calculate_cooccurrence_score(keyword, text_data)
            position_score = self._calculate_position_score(keyword, text_data)
            similarity_score = self._calculate_similarity_score(keyword, brand_info)
            
            # Aplicar fórmula ponderada
            final_score = (
                weights.w1_frequency * freq_score +
                weights.w2_tfidf * tfidf_score +
                weights.w3_cooccurrence * cooccurrence_score +
                weights.w4_position_title * position_score +
                weights.w5_similarity_brand * similarity_score
            )
            
            # Normalizar a rango [0, 1]
            final_score = max(0.0, min(1.0, final_score))
            
            logger.debug(f"Score para '{keyword}': {final_score:.3f} "
                        f"(freq:{freq_score:.2f}, tfidf:{tfidf_score:.2f}, "
                        f"cooc:{cooccurrence_score:.2f}, pos:{position_score:.2f}, "
                        f"sim:{similarity_score:.2f})")
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculando score para keyword '{keyword}': {e}")
            return 0.0
    
    def _calculate_frequency_score(self, keyword: str, text_data: Dict[str, Any]) -> float:
        """Calcula score basado en frecuencia de la keyword."""
        try:
            # Combinar todo el texto
            main_content = text_data.get('main_content', '')
            meta_data = text_data.get('meta', {})
            headings = text_data.get('headings', {})
            
            all_text = f"{main_content} {meta_data.get('title', '')} {meta_data.get('description', '')}"
            
            # Añadir headings
            for heading_list in headings.values():
                all_text += " " + " ".join(heading_list)
            
            # Normalizar texto
            normalized_text = self.text_utils.normalize_text(all_text)
            tokens = self.text_utils.tokenize_text(normalized_text)
            
            if not tokens:
                return 0.0
            
            # Contar frecuencia
            keyword_lower = keyword.lower()
            keyword_tokens = keyword_lower.split()
            
            if len(keyword_tokens) == 1:
                # Keyword de una palabra
                count = tokens.count(keyword_lower)
            else:
                # Keyword de múltiples palabras
                count = 0
                for i in range(len(tokens) - len(keyword_tokens) + 1):
                    if tokens[i:i+len(keyword_tokens)] == keyword_tokens:
                        count += 1
            
            # Normalizar por longitud del texto
            total_words = len(tokens)
            frequency = count / total_words if total_words > 0 else 0
            
            # Aplicar transformación logarítmica para suavizar
            if frequency > 0:
                freq_score = min(1.0, np.log(1 + frequency * 100))
            else:
                freq_score = 0.0
            
            return freq_score
            
        except Exception as e:
            logger.error(f"Error calculando frecuencia para '{keyword}': {e}")
            return 0.0
    
    def _calculate_tfidf_score(self, keyword: str, text_data: Dict[str, Any]) -> float:
        """Calcula score TF-IDF para la keyword."""
        try:
            # Crear corpus mínimo con el documento actual
            main_content = text_data.get('main_content', '')
            meta_data = text_data.get('meta', {})
            
            document = f"{main_content} {meta_data.get('title', '')} {meta_data.get('description', '')}"
            
            # Usar el servicio NLP para calcular TF-IDF
            tfidf_scores = self.nlp_service.calculate_tfidf_scores([keyword], [document])
            
            return tfidf_scores.get(keyword, 0.0)
            
        except Exception as e:
            logger.error(f"Error calculando TF-IDF para '{keyword}': {e}")
            return 0.0
    
    def _calculate_cooccurrence_score(self, keyword: str, text_data: Dict[str, Any]) -> float:
        """Calcula score basado en co-ocurrencias en headings importantes."""
        try:
            headings = text_data.get('headings', {})
            meta_data = text_data.get('meta', {})
            
            # Texto de headings importantes
            important_text = []
            
            # Título (máxima importancia)
            title = meta_data.get('title', '')
            if title:
                important_text.append(title)
            
            # H1 (alta importancia)
            h1_list = headings.get('h1', [])
            important_text.extend(h1_list)
            
            # H2 (importancia media)
            h2_list = headings.get('h2', [])
            important_text.extend(h2_list[:3])  # Solo los primeros 3 H2
            
            # Buscar co-ocurrencias
            keyword_lower = keyword.lower()
            cooccurrence_count = 0
            total_important_text = 0
            
            for text in important_text:
                if text:
                    text_lower = text.lower()
                    total_important_text += len(text_lower.split())
                    
                    # Buscar keyword en el texto
                    if keyword_lower in text_lower:
                        cooccurrence_count += 1
            
            if total_important_text == 0:
                return 0.0
            
            # Score basado en presencia en elementos importantes
            cooccurrence_score = cooccurrence_count / len(important_text) if important_text else 0
            
            return min(1.0, cooccurrence_score)
            
        except Exception as e:
            logger.error(f"Error calculando co-ocurrencias para '{keyword}': {e}")
            return 0.0
    
    def _calculate_position_score(self, keyword: str, text_data: Dict[str, Any]) -> float:
        """Calcula score basado en posición en el título."""
        try:
            meta_data = text_data.get('meta', {})
            title = meta_data.get('title', '')
            
            if not title:
                return 0.0
            
            title_lower = title.lower()
            keyword_lower = keyword.lower()
            
            # Buscar keyword en el título
            if keyword_lower not in title_lower:
                return 0.0
            
            # Calcular posición relativa
            keyword_pos = title_lower.find(keyword_lower)
            title_length = len(title_lower)
            
            if title_length == 0:
                return 0.0
            
            # Score más alto para keywords al inicio del título
            position_ratio = keyword_pos / title_length
            position_score = max(0.0, 1.0 - position_ratio)
            
            return position_score
            
        except Exception as e:
            logger.error(f"Error calculando posición para '{keyword}': {e}")
            return 0.0
    
    def _calculate_similarity_score(self, keyword: str, brand_info: Dict[str, Any]) -> float:
        """Calcula score basado en similitud con la marca."""
        try:
            brand_name = brand_info.get('name', '')
            brand_domain = brand_info.get('domain', '')
            
            if not brand_name and not brand_domain:
                return 0.0
            
            keyword_lower = keyword.lower()
            
            # Similitud con nombre de marca
            brand_similarity = 0.0
            if brand_name:
                brand_lower = brand_name.lower()
                
                # Coincidencia exacta
                if keyword_lower == brand_lower:
                    brand_similarity = 1.0
                # Contención
                elif keyword_lower in brand_lower or brand_lower in keyword_lower:
                    brand_similarity = 0.7
                # Palabras comunes
                elif any(word in keyword_lower for word in brand_lower.split()):
                    brand_similarity = 0.5
            
            # Similitud con dominio
            domain_similarity = 0.0
            if brand_domain:
                domain_name = brand_domain.replace('www.', '').split('.')[0]
                domain_lower = domain_name.lower()
                
                if keyword_lower == domain_lower:
                    domain_similarity = 0.8
                elif keyword_lower in domain_lower or domain_lower in keyword_lower:
                    domain_similarity = 0.6
            
            # Usar el máximo de ambas similitudes
            similarity_score = max(brand_similarity, domain_similarity)
            
            return similarity_score
            
        except Exception as e:
            logger.error(f"Error calculando similitud para '{keyword}': {e}")
            return 0.0
    
    def bucketize_keywords(self, keywords: List[Dict[str, Any]], page_type: str, 
                         brand_info: Dict[str, Any], domain_keywords: Optional[Dict[str, float]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Clasifica keywords en buckets según el tipo de página y contexto.
        
        Args:
            keywords: Lista de keywords con scores
            page_type: Tipo de página (ecommerce, blog, mixto)
            brand_info: Información de marca
            domain_keywords: Keywords globales del dominio (opcional)
            
        Returns:
            Diccionario con keywords clasificadas en buckets
        """
        try:
            buckets = {
                'cliente': [],
                'producto_o_post': [],
                'generales_seo': []
            }
            
            for keyword_data in keywords:
                keyword = keyword_data['term']
                score = keyword_data['score']
                
                # Clasificar en bucket apropiado
                bucket = self._classify_keyword_bucket(keyword, score, page_type, brand_info, domain_keywords)
                
                if bucket in buckets:
                    buckets[bucket].append({
                        'term': keyword,
                        'score': score
                    })
            
            # Ordenar cada bucket por score descendente
            for bucket_name in buckets:
                buckets[bucket_name].sort(key=lambda x: x['score'], reverse=True)
                # Limitar a top 30 por bucket
                buckets[bucket_name] = buckets[bucket_name][:30]
            
            logger.info(f"Keywords bucketizadas: {len(keywords)} -> "
                       f"Cliente: {len(buckets['cliente'])}, "
                       f"Producto/Post: {len(buckets['producto_o_post'])}, "
                       f"Generales: {len(buckets['generales_seo'])}")
            
            return buckets
            
        except Exception as e:
            logger.error(f"Error bucketizando keywords: {e}")
            return {
                'cliente': [],
                'producto_o_post': [],
                'generales_seo': []
            }
    
    def _classify_keyword_bucket(self, keyword: str, score: float, page_type: str, 
                               brand_info: Dict[str, Any], domain_keywords: Optional[Dict[str, float]] = None) -> str:
        """Clasifica una keyword en el bucket apropiado."""
        try:
            keyword_lower = keyword.lower()
            brand_name = brand_info.get('name', '').lower()
            brand_domain = brand_info.get('domain', '').lower()
            
            # Bucket CLIENTE: marca, términos del dominio, alta frecuencia global
            if (brand_name and (keyword_lower == brand_name or keyword_lower in brand_name or brand_name in keyword_lower)):
                return 'cliente'
            
            if (brand_domain and keyword_lower in brand_domain):
                return 'cliente'
            
            # Si hay keywords globales del dominio, verificar frecuencia
            if domain_keywords and keyword in domain_keywords:
                domain_freq = domain_keywords[keyword]
                if domain_freq > 0.1:  # Alta frecuencia en el dominio
                    return 'cliente'
            
            # Bucket PRODUCTO/POST: específicos de la página actual
            if page_type == 'ecommerce':
                # Para e-commerce, keywords específicas de productos
                product_keywords = [
                    'precio', 'comprar', 'oferta', 'descuento', 'envío', 'entrega',
                    'talla', 'color', 'marca', 'modelo', 'especificaciones'
                ]
                
                if any(pk in keyword_lower for pk in product_keywords):
                    return 'producto_o_post'
                
                # Keywords que aparecen en múltiples páginas del dominio (no específicas)
                if domain_keywords and keyword in domain_keywords:
                    return 'generales_seo'
                
                return 'producto_o_post'
            
            elif page_type == 'blog':
                # Para blog, keywords específicas del post
                blog_keywords = [
                    'tutorial', 'guía', 'cómo', 'paso', 'método', 'técnica',
                    'ejemplo', 'caso', 'experiencia', 'opinión', 'review'
                ]
                
                if any(bk in keyword_lower for bk in blog_keywords):
                    return 'producto_o_post'
                
                # Keywords que aparecen en múltiples posts (no específicas)
                if domain_keywords and keyword in domain_keywords:
                    return 'generales_seo'
                
                return 'producto_o_post'
            
            else:  # mixto
                # Para páginas mixtas, usar heurística general
                if domain_keywords and keyword in domain_keywords:
                    return 'generales_seo'
                else:
                    return 'producto_o_post'
            
        except Exception as e:
            logger.error(f"Error clasificando keyword '{keyword}': {e}")
            return 'generales_seo'
    
    def aggregate_domain_keywords(self, all_url_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Agrega keywords de todas las URLs del dominio para análisis global.
        
        Args:
            all_url_results: Lista de resultados de análisis por URL
            
        Returns:
            Diccionario con keywords globales y sus frecuencias
        """
        try:
            keyword_counts = Counter()
            total_urls = len(all_url_results)
            
            for url_result in all_url_results:
                keywords_buckets = url_result.get('keywords', {})
                
                # Contar todas las keywords de todos los buckets
                for bucket_name, keywords in keywords_buckets.items():
                    for keyword_data in keywords:
                        keyword = keyword_data['term']
                        keyword_counts[keyword] += 1
            
            # Convertir a frecuencias normalizadas
            domain_keywords = {}
            for keyword, count in keyword_counts.items():
                frequency = count / total_urls if total_urls > 0 else 0
                domain_keywords[keyword] = frequency
            
            logger.info(f"Keywords del dominio agregadas: {len(domain_keywords)} términos únicos")
            return domain_keywords
            
        except Exception as e:
            logger.error(f"Error agregando keywords del dominio: {e}")
            return {}
    
    def get_top_keywords_by_bucket(self, all_url_results: List[Dict[str, Any]], 
                                 bucket_name: str, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene las top keywords de un bucket específico de todas las URLs.
        
        Args:
            all_url_results: Lista de resultados de análisis por URL
            bucket_name: Nombre del bucket
            top_n: Número de keywords a retornar
            
        Returns:
            Lista de top keywords con scores agregados
        """
        try:
            keyword_scores = {}
            
            for url_result in all_url_results:
                keywords_buckets = url_result.get('keywords', {})
                bucket_keywords = keywords_buckets.get(bucket_name, [])
                
                for keyword_data in bucket_keywords:
                    keyword = keyword_data['term']
                    score = keyword_data['score']
                    
                    if keyword in keyword_scores:
                        # Promediar scores si aparece en múltiples URLs
                        keyword_scores[keyword].append(score)
                    else:
                        keyword_scores[keyword] = [score]
            
            # Calcular scores promedio y ordenar
            top_keywords = []
            for keyword, scores in keyword_scores.items():
                avg_score = sum(scores) / len(scores)
                top_keywords.append({
                    'term': keyword,
                    'score': avg_score
                })
            
            # Ordenar por score descendente
            top_keywords.sort(key=lambda x: x['score'], reverse=True)
            
            return top_keywords[:top_n]
            
        except Exception as e:
            logger.error(f"Error obteniendo top keywords del bucket '{bucket_name}': {e}")
            return []


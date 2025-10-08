"""
Servicio de scoring mejorado con algoritmos más sofisticados y soporte para diferentes sectores.
Incluye scoring contextual, temporal y de relevancia.
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import math

from app.config import get_settings
from app.services.patterns_enhanced import EnhancedPatterns

logger = logging.getLogger(__name__)
settings = get_settings()

class EnhancedKeywordScorer:
    """Servicio de scoring mejorado para keywords."""
    
    def __init__(self):
        self.patterns = EnhancedPatterns()
        self.sector_weights = {
            'legal': {'cliente': 0.4, 'producto': 0.3, 'generales': 0.3},
            'medical': {'cliente': 0.3, 'producto': 0.4, 'generales': 0.3},
            'technology': {'cliente': 0.2, 'producto': 0.5, 'generales': 0.3},
            'education': {'cliente': 0.3, 'producto': 0.2, 'generales': 0.5},
            'finance': {'cliente': 0.4, 'producto': 0.3, 'generales': 0.3},
            'general': {'cliente': 0.3, 'producto': 0.3, 'generales': 0.4}
        }
    
    def score_keywords(self, keywords: List[Dict[str, Any]], 
                      parsed_data: Dict[str, Any], 
                      url: str,
                      sector: str = 'general') -> List[Dict[str, Any]]:
        """
        Score keywords con algoritmos mejorados.
        
        Args:
            keywords: Lista de keywords a scorear
            parsed_data: Datos parseados del HTML
            url: URL de la página
            sector: Sector detectado del contenido
            
        Returns:
            Lista de keywords con scores mejorados
        """
        try:
            if not keywords:
                return []
            
            # Detectar sector si no se proporciona
            if sector == 'general':
                sector = self._detect_sector_from_content(parsed_data, url)
            
            # Calcular scores contextuales
            contextual_scores = self._calculate_contextual_scores(keywords, parsed_data, url)
            
            # Calcular scores de relevancia
            relevance_scores = self._calculate_relevance_scores(keywords, parsed_data, sector)
            
            # Calcular scores de posición
            position_scores = self._calculate_position_scores(keywords, parsed_data)
            
            # Calcular scores de frecuencia
            frequency_scores = self._calculate_frequency_scores(keywords, parsed_data)
            
            # Combinar scores
            scored_keywords = []
            for i, keyword in enumerate(keywords):
                term = keyword.get('term', '')
                
                # Scores base
                base_score = keyword.get('score', 0.0)
                contextual_score = contextual_scores.get(term, 0.0)
                relevance_score = relevance_scores.get(term, 0.0)
                position_score = position_scores.get(term, 0.0)
                frequency_score = frequency_scores.get(term, 0.0)
                
                # Peso por sector
                sector_weights = self.sector_weights.get(sector, self.sector_weights['general'])
                
                # Calcular score final ponderado
                final_score = (
                    base_score * 0.3 +
                    contextual_score * 0.25 +
                    relevance_score * 0.25 +
                    position_score * 0.1 +
                    frequency_score * 0.1
                )
                
                # Aplicar boost por sector
                sector_boost = self._calculate_sector_boost(term, sector)
                final_score *= (1 + sector_boost)
                
                # Normalizar score
                final_score = min(final_score, 1.0)
                
                scored_keywords.append({
                    'term': term,
                    'score': final_score,
                    'source': keyword.get('source', 'unknown'),
                    'contextual_score': contextual_score,
                    'relevance_score': relevance_score,
                    'position_score': position_score,
                    'frequency_score': frequency_score,
                    'sector': sector,
                    'sector_boost': sector_boost
                })
            
            # Ordenar por score final
            scored_keywords.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Scored {len(scored_keywords)} keywords for sector '{sector}'")
            return scored_keywords
            
        except Exception as e:
            logger.error(f"Error scoring keywords: {e}")
            return keywords
    
    def _detect_sector_from_content(self, parsed_data: Dict[str, Any], url: str) -> str:
        """Detecta el sector del contenido."""
        try:
            # Combinar texto para análisis
            main_content = parsed_data.get('main_content', '')
            meta_data = parsed_data.get('meta', {})
            headings = parsed_data.get('headings', {})
            
            text_to_analyze = f"{main_content} {meta_data.get('title', '')} {meta_data.get('description', '')}"
            
            # Añadir headings
            for heading_list in headings.values():
                text_to_analyze += " " + " ".join(heading_list)
            
            return self.patterns.detect_sector(text_to_analyze)
            
        except Exception as e:
            logger.error(f"Error detecting sector: {e}")
            return 'general'
    
    def _calculate_contextual_scores(self, keywords: List[Dict[str, Any]], 
                                   parsed_data: Dict[str, Any], 
                                   url: str) -> Dict[str, float]:
        """Calcula scores contextuales basados en la posición y contexto."""
        contextual_scores = {}
        
        try:
            # Extraer diferentes tipos de contenido
            title = parsed_data.get('meta', {}).get('title', '')
            description = parsed_data.get('meta', {}).get('description', '')
            headings = parsed_data.get('headings', {})
            main_content = parsed_data.get('main_content', '')
            
            # Pesos por posición
            position_weights = {
                'title': 1.0,
                'description': 0.8,
                'h1': 0.9,
                'h2': 0.7,
                'h3': 0.5,
                'main_content': 0.3
            }
            
            # Analizar cada keyword
            for keyword in keywords:
                term = keyword.get('term', '').lower()
                score = 0.0
                
                # Score por título
                if term in title.lower():
                    score += position_weights['title']
                
                # Score por descripción
                if term in description.lower():
                    score += position_weights['description']
                
                # Score por headings
                for level, heading_list in headings.items():
                    for heading in heading_list:
                        if term in heading.lower():
                            weight_key = f'h{level}' if level in [1, 2, 3] else 'h3'
                            score += position_weights.get(weight_key, 0.3)
                
                # Score por contenido principal
                if term in main_content.lower():
                    score += position_weights['main_content']
                
                contextual_scores[term] = min(score, 1.0)
            
            return contextual_scores
            
        except Exception as e:
            logger.error(f"Error calculating contextual scores: {e}")
            return {}
    
    def _calculate_relevance_scores(self, keywords: List[Dict[str, Any]], 
                                  parsed_data: Dict[str, Any], 
                                  sector: str) -> Dict[str, float]:
        """Calcula scores de relevancia basados en el sector y contenido."""
        relevance_scores = {}
        
        try:
            # Patrones de relevancia por sector
            sector_patterns = {
                'legal': [
                    r'\b(abogado|abogados|legal|ley|derecho|jurídico|tribunal|juez|proceso|demanda|contrato|asesoría)\b',
                    r'\b(justicia|justice|lawyer|attorney|court|judge|lawsuit|contract|legal advice)\b'
                ],
                'medical': [
                    r'\b(médico|medico|doctor|salud|health|hospital|clínica|enfermedad|tratamiento|medicina|paciente)\b',
                    r'\b(doctor|health|hospital|clinic|disease|treatment|medicine|patient|consultation)\b'
                ],
                'technology': [
                    r'\b(tecnología|technology|software|hardware|programación|desarrollo|aplicación|sistema|digital)\b',
                    r'\b(technology|software|hardware|programming|development|application|system|digital)\b'
                ],
                'education': [
                    r'\b(educación|education|enseñanza|aprendizaje|curso|formación|estudio|academia|universidad)\b',
                    r'\b(education|teaching|learning|courses|training|study|academy|university|school)\b'
                ]
            }
            
            # Combinar texto para análisis
            main_content = parsed_data.get('main_content', '')
            meta_data = parsed_data.get('meta', {})
            headings = parsed_data.get('headings', {})
            
            text_to_analyze = f"{main_content} {meta_data.get('title', '')} {meta_data.get('description', '')}"
            
            # Añadir headings
            for heading_list in headings.values():
                text_to_analyze += " " + " ".join(heading_list)
            
            # Analizar cada keyword
            for keyword in keywords:
                term = keyword.get('term', '').lower()
                score = 0.0
                
                # Score por patrones del sector
                if sector in sector_patterns:
                    for pattern in sector_patterns[sector]:
                        if re.search(pattern, term, re.IGNORECASE):
                            score += 0.5
                        if re.search(pattern, text_to_analyze, re.IGNORECASE):
                            score += 0.3
                
                # Score por co-ocurrencia con términos del sector
                sector_terms = self._get_sector_terms(sector)
                for sector_term in sector_terms:
                    if sector_term in text_to_analyze.lower() and term in text_to_analyze.lower():
                        # Calcular distancia entre términos
                        distance = self._calculate_term_distance(term, sector_term, text_to_analyze)
                        if distance < 50:  # Términos cercanos
                            score += 0.2
                
                relevance_scores[term] = min(score, 1.0)
            
            return relevance_scores
            
        except Exception as e:
            logger.error(f"Error calculating relevance scores: {e}")
            return {}
    
    def _calculate_position_scores(self, keywords: List[Dict[str, Any]], 
                                 parsed_data: Dict[str, Any]) -> Dict[str, float]:
        """Calcula scores basados en la posición del término en el documento."""
        position_scores = {}
        
        try:
            main_content = parsed_data.get('main_content', '')
            content_length = len(main_content)
            
            for keyword in keywords:
                term = keyword.get('term', '').lower()
                score = 0.0
                
                # Buscar todas las ocurrencias del término
                positions = []
                start = 0
                while True:
                    pos = main_content.lower().find(term, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                
                if positions:
                    # Score basado en posición relativa (términos al inicio tienen mayor score)
                    for pos in positions:
                        relative_position = 1 - (pos / content_length)
                        score += relative_position * 0.1
                    
                    # Normalizar por número de ocurrencias
                    score = min(score, 1.0)
                
                position_scores[term] = score
            
            return position_scores
            
        except Exception as e:
            logger.error(f"Error calculating position scores: {e}")
            return {}
    
    def _calculate_frequency_scores(self, keywords: List[Dict[str, Any]], 
                                  parsed_data: Dict[str, Any]) -> Dict[str, float]:
        """Calcula scores basados en la frecuencia del término."""
        frequency_scores = {}
        
        try:
            main_content = parsed_data.get('main_content', '').lower()
            total_words = len(main_content.split())
            
            for keyword in keywords:
                term = keyword.get('term', '').lower()
                
                # Contar ocurrencias
                occurrences = main_content.count(term)
                
                # Calcular frecuencia relativa
                if total_words > 0:
                    frequency = occurrences / total_words
                    # Normalizar frecuencia (log scale para evitar dominancia de términos muy frecuentes)
                    score = min(math.log(1 + frequency * 1000) / 10, 1.0)
                else:
                    score = 0.0
                
                frequency_scores[term] = score
            
            return frequency_scores
            
        except Exception as e:
            logger.error(f"Error calculating frequency scores: {e}")
            return {}
    
    def _calculate_sector_boost(self, term: str, sector: str) -> float:
        """Calcula boost adicional basado en el sector."""
        boost = 0.0
        
        # Términos específicos por sector
        sector_terms = {
            'legal': ['abogado', 'legal', 'ley', 'derecho', 'jurídico', 'tribunal', 'juez', 'proceso', 'demanda', 'contrato'],
            'medical': ['médico', 'doctor', 'salud', 'health', 'hospital', 'clínica', 'enfermedad', 'tratamiento', 'medicina'],
            'technology': ['tecnología', 'software', 'hardware', 'programación', 'desarrollo', 'aplicación', 'sistema', 'digital'],
            'education': ['educación', 'enseñanza', 'aprendizaje', 'curso', 'formación', 'estudio', 'academia', 'universidad']
        }
        
        if sector in sector_terms:
            term_lower = term.lower()
            for sector_term in sector_terms[sector]:
                if sector_term in term_lower or term_lower in sector_term:
                    boost += 0.2
        
        return min(boost, 0.5)  # Máximo boost del 50%
    
    def _get_sector_terms(self, sector: str) -> List[str]:
        """Obtiene términos clave para un sector específico."""
        sector_terms = {
            'legal': ['abogado', 'legal', 'ley', 'derecho', 'jurídico', 'tribunal', 'juez', 'proceso', 'demanda', 'contrato'],
            'medical': ['médico', 'doctor', 'salud', 'health', 'hospital', 'clínica', 'enfermedad', 'tratamiento', 'medicina'],
            'technology': ['tecnología', 'software', 'hardware', 'programación', 'desarrollo', 'aplicación', 'sistema', 'digital'],
            'education': ['educación', 'enseñanza', 'aprendizaje', 'curso', 'formación', 'estudio', 'academia', 'universidad']
        }
        
        return sector_terms.get(sector, [])
    
    def _calculate_term_distance(self, term1: str, term2: str, text: str) -> int:
        """Calcula la distancia mínima entre dos términos en el texto."""
        try:
            text_lower = text.lower()
            term1_positions = []
            term2_positions = []
            
            # Encontrar posiciones de ambos términos
            start = 0
            while True:
                pos = text_lower.find(term1, start)
                if pos == -1:
                    break
                term1_positions.append(pos)
                start = pos + 1
            
            start = 0
            while True:
                pos = text_lower.find(term2, start)
                if pos == -1:
                    break
                term2_positions.append(pos)
                start = pos + 1
            
            # Calcular distancia mínima
            min_distance = float('inf')
            for pos1 in term1_positions:
                for pos2 in term2_positions:
                    distance = abs(pos1 - pos2)
                    min_distance = min(min_distance, distance)
            
            return min_distance if min_distance != float('inf') else 1000
            
        except Exception as e:
            logger.error(f"Error calculating term distance: {e}")
            return 1000


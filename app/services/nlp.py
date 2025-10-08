"""
Módulo NLP principal con YAKE, KeyBERT+MiniLM, normalización y fusión de keywords.
Implementa extracción de keywords usando múltiples algoritmos y fusión inteligente.
"""
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import yake
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.services.utils import TextUtils

logger = logging.getLogger(__name__)
settings = get_settings()


class NLPService:
    """Servicio principal para procesamiento de lenguaje natural."""
    
    def __init__(self):
        self.text_utils = TextUtils()
        self.keybert_model = None
        self.sentence_transformer = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Inicializa los modelos de NLP."""
        try:
            # Inicializar KeyBERT con MiniLM
            logger.info("Inicializando KeyBERT con modelo MiniLM...")
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            self.keybert_model = KeyBERT(model=self.sentence_transformer)
            
            logger.info("Modelos NLP inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando modelos NLP: {e}")
            raise
    
    async def extract_keywords(self, text: str, max_keywords: int = 50) -> List[Dict[str, Any]]:
        """
        Extrae keywords usando YAKE y KeyBERT en paralelo, luego fusiona los resultados.
        
        Args:
            text: Texto a procesar
            max_keywords: Máximo número de keywords a retornar
            
        Returns:
            Lista de keywords con scores normalizados
        """
        if not text or len(text.strip()) < 50:
            logger.warning("Texto muy corto para extracción de keywords")
            return []
        
        try:
            # Normalizar texto
            normalized_text = self.text_utils.normalize_text(text)
            
            # Ejecutar extracciones en paralelo
            import asyncio
            yake_task = asyncio.create_task(self._extract_with_yake_async(normalized_text))
            keybert_task = asyncio.create_task(self._extract_with_keybert_async(normalized_text))
            
            # Esperar ambos resultados
            yake_keywords, keybert_keywords = await asyncio.gather(
                yake_task, 
                keybert_task,
                return_exceptions=True
            )
            
            # Manejar excepciones
            if isinstance(yake_keywords, Exception):
                logger.error(f"Error en YAKE: {yake_keywords}")
                yake_keywords = []
            if isinstance(keybert_keywords, Exception):
                logger.error(f"Error en KeyBERT: {keybert_keywords}")
                keybert_keywords = []
            
            # Fusionar resultados
            merged_keywords = self._merge_keyword_results(yake_keywords, keybert_keywords)
            
            # Limitar resultados
            final_keywords = merged_keywords[:max_keywords]
            
            logger.info(f"Extraídas {len(final_keywords)} keywords de {len(text)} caracteres")
            return final_keywords
            
        except Exception as e:
            logger.error(f"Error extrayendo keywords: {e}")
            return []
    
    async def _extract_with_yake_async(self, text: str) -> List[Dict[str, Any]]:
        """Extrae keywords usando YAKE de forma asíncrona."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_with_yake, text)
    
    async def _extract_with_keybert_async(self, text: str) -> List[Dict[str, Any]]:
        """Extrae keywords usando KeyBERT de forma asíncrona."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_with_keybert, text)
    
    def _extract_with_yake(self, text: str) -> List[Dict[str, Any]]:
        """Extrae keywords usando YAKE."""
        try:
            # Configurar YAKE
            kw_extractor = yake.KeywordExtractor(
                lan="es",  # Español
                n=settings.yake_max_ngram_size,  # n-gramas máximos
                dedupLim=settings.yake_deduplication_threshold,  # Umbral deduplicación
                top=30,  # Top keywords
                features=None  # Usar todas las características
            )
            
            # Extraer keywords
            keywords = kw_extractor.extract_keywords(text)
            
            # Convertir a formato estándar
            yake_results = []
            for item in keywords:
                try:
                    # YAKE puede devolver (score, keyword) o (keyword, score)
                    # Verificar el tipo del primer elemento
                    if isinstance(item[0], (int, float)):
                        score, keyword = item
                    else:
                        keyword, score = item
                    
                    # Asegurar que score sea numérico
                    if isinstance(score, str):
                        score = float(score)
                    normalized_score = max(0, 1 - score)
                    
                    yake_results.append({
                        'term': keyword.strip(),
                        'score': normalized_score,
                        'source': 'yake'
                    })
                except (ValueError, TypeError, IndexError) as e:
                    logger.warning(f"Error procesando keyword YAKE: {item}, error: {e}")
                    continue
            
            logger.debug(f"YAKE extrajo {len(yake_results)} keywords")
            return yake_results
            
        except Exception as e:
            logger.warning(f"Error en extracción YAKE: {e}")
            return []
    
    def _extract_with_keybert(self, text: str) -> List[Dict[str, Any]]:
        """Extrae keywords usando KeyBERT."""
        try:
            if not self.keybert_model:
                logger.warning("KeyBERT no inicializado")
                return []
            
            # Extraer keywords con KeyBERT
            keywords = self.keybert_model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, settings.keybert_max_ngram_size),
                stop_words=list(self.text_utils.ALL_STOPWORDS),
                use_maxsum=True,
                nr_candidates=50,
                diversity=settings.keybert_diversity
            )
            
            # Convertir a formato estándar
            keybert_results = []
            for keyword, score in keywords:
                keybert_results.append({
                    'term': keyword.strip(),
                    'score': float(score),
                    'source': 'keybert'
                })
            
            logger.debug(f"KeyBERT extrajo {len(keybert_results)} keywords")
            return keybert_results
            
        except Exception as e:
            logger.warning(f"Error en extracción KeyBERT: {e}")
            return []
    
    def _merge_keyword_results(self, yake_results: List[Dict[str, Any]], 
                              keybert_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fusiona resultados de YAKE y KeyBERT eliminando duplicados por similitud.
        """
        all_keywords = yake_results + keybert_results
        
        if not all_keywords:
            return []
        
        # Agrupar por término exacto primero
        exact_groups = {}
        for kw in all_keywords:
            term = kw['term'].lower().strip()
            if term not in exact_groups:
                exact_groups[term] = []
            exact_groups[term].append(kw)
        
        # Procesar grupos exactos
        merged_keywords = []
        for term, group in exact_groups.items():
            if len(group) == 1:
                # Solo una ocurrencia, usar directamente
                merged_keywords.append(group[0])
            else:
                # Múltiples ocurrencias, promediar scores
                avg_score = np.mean([kw['score'] for kw in group])
                sources = list(set([kw['source'] for kw in group]))
                
                merged_keywords.append({
                    'term': group[0]['term'],
                    'score': avg_score,
                    'source': '+'.join(sources)
                })
        
        # Eliminar duplicados por similitud semántica
        final_keywords = self._deduplicate_by_similarity(merged_keywords)
        
        # Ordenar por score descendente
        final_keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return final_keywords
    
    def _deduplicate_by_similarity(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Elimina keywords similares usando similitud coseno de embeddings.
        """
        if len(keywords) <= 1:
            return keywords
        
        try:
            if not self.sentence_transformer:
                logger.warning("SentenceTransformer no disponible para deduplicación")
                return keywords
            
            # Crear embeddings para todos los términos
            terms = [kw['term'] for kw in keywords]
            embeddings = self.sentence_transformer.encode(terms)
            
            # Calcular matriz de similitud
            similarity_matrix = cosine_similarity(embeddings)
            
            # Encontrar términos similares
            to_remove = set()
            for i in range(len(keywords)):
                if i in to_remove:
                    continue
                
                for j in range(i + 1, len(keywords)):
                    if j in to_remove:
                        continue
                    
                    similarity = similarity_matrix[i][j]
                    if similarity > settings.similarity_threshold:
                        # Mantener el término con mayor score
                        if keywords[i]['score'] >= keywords[j]['score']:
                            to_remove.add(j)
                        else:
                            to_remove.add(i)
                            break
            
            # Filtrar términos a eliminar
            final_keywords = [kw for i, kw in enumerate(keywords) if i not in to_remove]
            
            logger.debug(f"Deduplicación: {len(keywords)} -> {len(final_keywords)} keywords")
            return final_keywords
            
        except Exception as e:
            logger.warning(f"Error en deduplicación por similitud: {e}")
            return keywords
    
    def calculate_tfidf_scores(self, keywords: List[str], corpus: List[str]) -> Dict[str, float]:
        """
        Calcula scores TF-IDF para keywords en un corpus.
        
        Args:
            keywords: Lista de keywords
            corpus: Lista de documentos del corpus
            
        Returns:
            Diccionario con keyword -> score TF-IDF
        """
        try:
            if not corpus or not keywords:
                return {}
            
            # Crear vectorizador TF-IDF
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words=list(self.text_utils.ALL_STOPWORDS),
                max_features=10000,
                lowercase=True
            )
            
            # Ajustar vectorizador al corpus
            tfidf_matrix = vectorizer.fit_transform(corpus)
            feature_names = vectorizer.get_feature_names_out()
            
            # Crear diccionario de scores
            tfidf_scores = {}
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Buscar coincidencias exactas o parciales
                matches = [i for i, name in enumerate(feature_names) 
                          if keyword_lower in name or name in keyword_lower]
                
                if matches:
                    # Usar el score máximo de las coincidencias
                    max_score = max(tfidf_matrix[:, match].max() for match in matches)
                    tfidf_scores[keyword] = float(max_score)
                else:
                    tfidf_scores[keyword] = 0.0
            
            return tfidf_scores
            
        except Exception as e:
            logger.warning(f"Error calculando TF-IDF: {e}")
            return {}
    
    def detect_language(self, text: str) -> str:
        """
        Detecta el idioma del texto usando heurísticas simples.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Código de idioma ('es', 'en', etc.)
        """
        if not text:
            return 'es'
        
        # Patrones para detectar idiomas
        spanish_patterns = [
            r'\b(es|está|están|tiene|tienen|para|con|por|del|de la|en el|en la)\b',
            r'\b(que|qué|como|cómo|donde|dónde|cuando|cuándo)\b',
            r'\b(muy|más|menos|todo|todos|toda|todas)\b'
        ]
        
        english_patterns = [
            r'\b(is|are|has|have|for|with|by|the|in the|on the)\b',
            r'\b(what|how|where|when|why|which)\b',
            r'\b(very|more|less|all|every|some)\b'
        ]
        
        text_lower = text.lower()
        
        spanish_score = sum(len(re.findall(pattern, text_lower)) for pattern in spanish_patterns)
        english_score = sum(len(re.findall(pattern, text_lower)) for pattern in english_patterns)
        
        if spanish_score > english_score:
            return 'es'
        elif english_score > spanish_score:
            return 'en'
        else:
            return 'es'  # Por defecto español
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrae entidades básicas del texto usando regex patterns.
        
        Args:
            text: Texto a procesar
            
        Returns:
            Lista de entidades encontradas
        """
        entities = []
        
        # Patrones para diferentes tipos de entidades
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?34|0034)?[6-9]\d{8}',
            'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
            'price': r'[\d.,]+\s*(€|EUR|USD|\$|pesos?|euros?)',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'percentage': r'\d+(?:\.\d+)?%'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'type': entity_type,
                    'value': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    async def process_multiple_texts(self, texts: List[str], max_keywords: int = 50) -> List[List[Dict[str, Any]]]:
        """
        Procesa múltiples textos en paralelo para mejor rendimiento.
        
        Args:
            texts: Lista de textos a procesar
            max_keywords: Máximo número de keywords por texto
            
        Returns:
            Lista de listas de keywords para cada texto
        """
        try:
            import asyncio
            
            # Crear tareas para cada texto
            tasks = [
                asyncio.create_task(self.extract_keywords(text, max_keywords))
                for text in texts
            ]
            
            # Esperar todos los resultados
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Manejar excepciones
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error procesando texto {i}: {result}")
                    processed_results.append([])
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error en procesamiento múltiple: {e}")
            return [[] for _ in texts]
    
    def get_text_summary(self, text: str, max_sentences: int = 3) -> str:
        """
        Genera un resumen básico del texto extrayendo las primeras oraciones más importantes.
        
        Args:
            text: Texto a resumir
            max_sentences: Máximo número de oraciones en el resumen
            
        Returns:
            Resumen del texto
        """
        if not text:
            return ""
        
        # Dividir en oraciones
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return text
        
        # Seleccionar las primeras oraciones más largas (heurística simple)
        sentence_lengths = [(i, len(sentence)) for i, sentence in enumerate(sentences)]
        sentence_lengths.sort(key=lambda x: x[1], reverse=True)
        
        # Tomar las mejores oraciones manteniendo el orden original
        selected_indices = sorted([i for i, _ in sentence_lengths[:max_sentences]])
        summary_sentences = [sentences[i] for i in selected_indices]
        
        return '. '.join(summary_sentences) + '.'


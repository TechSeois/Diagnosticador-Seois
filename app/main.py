"""
Aplicación FastAPI principal con todos los endpoints, middleware y orquestación.
Implementa análisis de URLs individuales y dominios completos con procesamiento asíncrono.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import get_settings
from app.schemas import (
    DomainAnalysisRequest, URLAnalysisRequest, DomainAnalysisResponse,
    URLAnalysisResponse, UpdateScoringWeightsRequest, ScoringWeightsResponse,
    HealthResponse, ErrorResponse, MetaData, Headings, Stats, Product,
    KeywordsBuckets, DomainSummary, KeywordScore
)
from app.services.fetcher import HTTPFetcher
from app.services.sitemap import SitemapService
from app.services.parser import HTMLParserService
from app.services.classifier import PageClassifier
from app.services.nlp import NLPService
from app.services.ecom import EcommerceExtractor
from app.services.scorer import KeywordScorer
from app.services.utils import URLUtils

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar configuración
settings = get_settings()

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Análisis SEO de Dominios",
    description="API para análisis completo de dominios web con extracción de keywords y clasificación",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Servicios globales
nlp_service = NLPService()
classifier = PageClassifier()
parser_service = HTMLParserService()
ecom_extractor = EcommerceExtractor()
scorer = KeywordScorer()
sitemap_service = SitemapService()
url_utils = URLUtils()


# Dependencias
async def verify_api_key(x_api_key: str = Header(None)):
    """Verifica la clave API."""
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="API key inválida o faltante"
        )
    return x_api_key


# Middleware de logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests."""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


# Endpoints
@app.post("/analyze-url", response_model=URLAnalysisResponse)
async def analyze_url(
    request: URLAnalysisRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Analiza una URL individual y extrae keywords clasificadas.
    """
    try:
        logger.info(f"Iniciando análisis de URL: {request.url}")
        
        async with HTTPFetcher() as fetcher:
            # Descargar HTML
            response = await fetcher.fetch_url(request.url)
            if not response:
                raise HTTPException(
                    status_code=400,
                    detail=f"No se pudo descargar la URL: {request.url}"
                )
            
            # Parsear HTML
            parsed_data = parser_service.parse_html(response.text, request.url)
            
            # Clasificar página
            page_type = classifier.classify_page_type(parsed_data, request.url)
            audiencia = classifier.detect_audience(parsed_data)
            intencion = classifier.detect_intent(parsed_data, request.url)
            brand_info = classifier.extract_brand_info(parsed_data, request.url)
            
            # Extraer productos si es e-commerce
            productos = []
            if page_type == 'ecommerce':
                productos = ecom_extractor.extract_products(parsed_data, request.url)
            
            # Extraer keywords
            main_content = parsed_data.get('main_content', '')
            keywords_raw = await nlp_service.extract_keywords(main_content)
            
            # Calcular scores y bucketizar
            text_data = {
                'main_content': main_content,
                'meta': parsed_data.get('meta', {}),
                'headings': parsed_data.get('headings', {})
            }
            
            # Recalcular scores con fórmula completa
            keywords_with_scores = []
            for kw_data in keywords_raw:
                keyword = kw_data['term']
                score = scorer.calculate_keyword_score(keyword, text_data, brand_info)
                keywords_with_scores.append({
                    'term': keyword,
                    'score': score
                })
            
            # Bucketizar keywords
            keywords_buckets = scorer.bucketize_keywords(
                keywords_with_scores, page_type, brand_info
            )
            
            # Construir respuesta
            result = URLAnalysisResponse(
                url=request.url,
                tipo=page_type,
                meta=MetaData(**parsed_data.get('meta', {})),
                headings=Headings(**parsed_data.get('headings', {})),
                stats=Stats(**parsed_data.get('stats', {})),
                audiencia=audiencia,
                intencion=intencion,
                productos=[Product(**p) for p in productos],
                keywords=KeywordsBuckets(**keywords_buckets)
            )
            
            logger.info(f"Análisis de URL completado: {request.url}")
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analizando URL {request.url}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno analizando URL: {str(e)}"
        )


@app.post("/analyze-domain", response_model=DomainAnalysisResponse)
async def analyze_domain(
    request: DomainAnalysisRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Analiza un dominio completo descubriendo sitemap y procesando múltiples URLs.
    """
    try:
        logger.info(f"Iniciando análisis de dominio: {request.domain}")
        
        # Normalizar dominio
        domain = url_utils.normalize_url(request.domain)
        base_domain = url_utils.get_domain(domain)
        
        async with HTTPFetcher() as fetcher:
            # Descubrir URLs inteligentemente por categorías y fecha
            urls_to_process = await sitemap_service.get_intelligent_urls(base_domain, request.max_urls)
            
            if not urls_to_process:
                logger.warning(f"No se encontraron URLs para {request.domain}")
                return DomainAnalysisResponse(
                    domain=request.domain,
                    summary=DomainSummary(total_urls=0),
                    urls=[]
                )
            
            logger.info(f"URLs seleccionadas inteligentemente para {request.domain}: {len(urls_to_process)}")
            
            if not urls_to_process:
                raise HTTPException(
                    status_code=400,
                    detail="No se encontraron URLs para procesar"
                )
            
            # Procesar URLs en paralelo
            semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
            
            async def process_url(url: str) -> Optional[URLAnalysisResponse]:
                async with semaphore:
                    try:
                        # Descargar HTML
                        response = await fetcher.fetch_url(url)
                        if not response:
                            return None
                        
                        # Parsear HTML
                        parsed_data = parser_service.parse_html(response.text, url)
                        
                        # Clasificar página
                        page_type = classifier.classify_page_type(parsed_data, url)
                        audiencia = classifier.detect_audience(parsed_data)
                        intencion = classifier.detect_intent(parsed_data, url)
                        brand_info = classifier.extract_brand_info(parsed_data, url)
                        
                        # Extraer productos si es e-commerce
                        productos = []
                        if page_type == 'ecommerce':
                            productos = ecom_extractor.extract_products(parsed_data, url)
                        
                        # Extraer keywords
                        main_content = parsed_data.get('main_content', '')
                        keywords_raw = await nlp_service.extract_keywords(main_content)
                        
                        # Calcular scores y bucketizar
                        text_data = {
                            'main_content': main_content,
                            'meta': parsed_data.get('meta', {}),
                            'headings': parsed_data.get('headings', {})
                        }
                        
                        # Recalcular scores con fórmula completa
                        keywords_with_scores = []
                        for kw_data in keywords_raw:
                            keyword = kw_data['term']
                            score = scorer.calculate_keyword_score(keyword, text_data, brand_info)
                            keywords_with_scores.append({
                                'term': keyword,
                                'score': score
                            })
                        
                        # Bucketizar keywords
                        keywords_buckets = scorer.bucketize_keywords(
                            keywords_with_scores, page_type, brand_info
                        )
                        
                        return URLAnalysisResponse(
                            url=url,
                            tipo=page_type,
                            meta=MetaData(**parsed_data.get('meta', {})),
                            headings=Headings(**parsed_data.get('headings', {})),
                            stats=Stats(**parsed_data.get('stats', {})),
                            audiencia=audiencia,
                            intencion=intencion,
                            productos=[Product(**p) for p in productos],
                            keywords=KeywordsBuckets(**keywords_buckets)
                        )
                        
                    except Exception as e:
                        logger.warning(f"Error procesando URL {url}: {e}")
                        return None
            
            # Ejecutar procesamiento en paralelo
            tasks = [process_url(url) for url in urls_to_process]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filtrar resultados válidos
            valid_results = []
            for result in results:
                if isinstance(result, URLAnalysisResponse):
                    valid_results.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Error en procesamiento: {result}")
            
            if not valid_results:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudieron procesar URLs válidas"
                )
            
            # Agregar resultados del dominio
            domain_summary = _create_domain_summary(valid_results)
            
            # Construir respuesta
            response = DomainAnalysisResponse(
                domain=request.domain,
                resumen=domain_summary,
                urls=valid_results
            )
            
            logger.info(f"Análisis de dominio completado: {request.domain} - {len(valid_results)} URLs procesadas")
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analizando dominio {request.domain}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno analizando dominio: {str(e)}"
        )


@app.get("/scoring-weights", response_model=ScoringWeightsResponse)
async def get_scoring_weights(api_key: str = Depends(verify_api_key)):
    """Obtiene los pesos actuales de scoring."""
    weights = settings.scoring_weights
    return ScoringWeightsResponse(
        weights={
            'w1_frequency': weights.w1_frequency,
            'w2_tfidf': weights.w2_tfidf,
            'w3_cooccurrence': weights.w3_cooccurrence,
            'w4_position_title': weights.w4_position_title,
            'w5_similarity_brand': weights.w5_similarity_brand
        },
        normalized=True
    )


@app.put("/scoring-weights", response_model=ScoringWeightsResponse)
async def update_scoring_weights(
    request: UpdateScoringWeightsRequest,
    api_key: str = Depends(verify_api_key)
):
    """Actualiza los pesos de scoring dinámicamente."""
    try:
        # Crear diccionario con solo los valores proporcionados
        weights_dict = {}
        if request.w1_frequency is not None:
            weights_dict['w1_frequency'] = request.w1_frequency
        if request.w2_tfidf is not None:
            weights_dict['w2_tfidf'] = request.w2_tfidf
        if request.w3_cooccurrence is not None:
            weights_dict['w3_cooccurrence'] = request.w3_cooccurrence
        if request.w4_position_title is not None:
            weights_dict['w4_position_title'] = request.w4_position_title
        if request.w5_similarity_brand is not None:
            weights_dict['w5_similarity_brand'] = request.w5_similarity_brand
        
        # Actualizar pesos
        settings.update_scoring_weights(weights_dict)
        
        # Retornar pesos actualizados
        weights = settings.scoring_weights
        return ScoringWeightsResponse(
            weights={
                'w1_frequency': weights.w1_frequency,
                'w2_tfidf': weights.w2_tfidf,
                'w3_cooccurrence': weights.w3_cooccurrence,
                'w4_position_title': weights.w4_position_title,
                'w5_similarity_brand': weights.w5_similarity_brand
            },
            normalized=True
        )
        
    except Exception as e:
        logger.error(f"Error actualizando pesos de scoring: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando pesos: {str(e)}"
        )


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


# Funciones auxiliares
def _create_domain_summary(url_results: List[URLAnalysisResponse]) -> DomainSummary:
    """Crea resumen agregado del análisis de dominio."""
    try:
        total_urls = len(url_results)
        
        # Contar por tipo
        por_tipo = {'ecommerce': 0, 'blog': 0, 'mixto': 0}
        for result in url_results:
            tipo = result.tipo
            if tipo in por_tipo:
                por_tipo[tipo] += 1
        
        # Agregar keywords globales
        all_keywords_data = []
        for result in url_results:
            all_keywords_data.append({
                'keywords': result.keywords.dict(),
                'tipo': result.tipo
            })
        
        # Obtener top keywords por bucket
        top_keywords_cliente = scorer.get_top_keywords_by_bucket(
            all_keywords_data, 'cliente', 20
        )
        top_keywords_producto = scorer.get_top_keywords_by_bucket(
            all_keywords_data, 'producto_o_post', 20
        )
        top_keywords_generales = scorer.get_top_keywords_by_bucket(
            all_keywords_data, 'generales_seo', 20
        )
        
        return DomainSummary(
            total_urls=total_urls,
            por_tipo=por_tipo,
            top_keywords_cliente=[KeywordScore(**kw) for kw in top_keywords_cliente],
            top_keywords_producto=[KeywordScore(**kw) for kw in top_keywords_producto],
            top_keywords_generales=[KeywordScore(**kw) for kw in top_keywords_generales]
        )
        
    except Exception as e:
        logger.error(f"Error creando resumen de dominio: {e}")
        return DomainSummary(
            total_urls=len(url_results),
            por_tipo={'ecommerce': 0, 'blog': 0, 'mixto': 0},
            top_keywords_cliente=[],
            top_keywords_producto=[],
            top_keywords_generales=[]
        )


# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones."""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Error interno del servidor",
            detail=str(exc),
            timestamp=datetime.utcnow()
        ).dict()
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )


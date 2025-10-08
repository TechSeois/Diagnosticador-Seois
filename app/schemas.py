"""
Modelos Pydantic para requests y responses de la API.
Define la estructura completa de datos según especificación.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime


# ===== REQUEST MODELS =====

class DomainAnalysisRequest(BaseModel):
    """Request para análisis completo de dominio."""
    domain: str = Field(..., description="Dominio a analizar (ej: https://ejemplo.com)")
    max_urls: int = Field(default=100, ge=1, le=1000, description="Máximo número de URLs a procesar")
    timeout: int = Field(default=15, ge=5, le=60, description="Timeout por request en segundos")
    
    @validator('domain')
    def validate_domain(cls, v):
        if not v.startswith(('http://', 'https://')):
            v = f"https://{v}"
        return v


class URLAnalysisRequest(BaseModel):
    """Request para análisis de URL individual."""
    url: str = Field(..., description="URL a analizar")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            v = f"https://{v}"
        return v


class UpdateScoringWeightsRequest(BaseModel):
    """Request para actualizar pesos de scoring dinámicamente."""
    w1_frequency: Optional[float] = Field(None, ge=0, le=1, description="Peso frecuencia")
    w2_tfidf: Optional[float] = Field(None, ge=0, le=1, description="Peso TF-IDF")
    w3_cooccurrence: Optional[float] = Field(None, ge=0, le=1, description="Peso co-ocurrencias")
    w4_position_title: Optional[float] = Field(None, ge=0, le=1, description="Peso posición título")
    w5_similarity_brand: Optional[float] = Field(None, ge=0, le=1, description="Peso similitud marca")


# ===== RESPONSE MODELS =====

class KeywordScore(BaseModel):
    """Modelo para keyword con score."""
    term: str = Field(..., description="Término/keyword")
    score: float = Field(..., ge=0, le=1, description="Score normalizado 0-1")


class MetaData(BaseModel):
    """Metadatos extraídos de la página."""
    title: Optional[str] = Field(None, description="Título de la página")
    description: Optional[str] = Field(None, description="Meta description")
    og_title: Optional[str] = Field(None, description="Open Graph title")
    og_description: Optional[str] = Field(None, description="Open Graph description")
    canonical: Optional[str] = Field(None, description="URL canónica")
    lang: Optional[str] = Field(default="es", description="Idioma detectado")


class Headings(BaseModel):
    """Estructura de headings extraídos."""
    h1: List[str] = Field(default_factory=list, description="Lista de H1")
    h2: List[str] = Field(default_factory=list, description="Lista de H2")
    h3: List[str] = Field(default_factory=list, description="Lista de H3")


class Stats(BaseModel):
    """Estadísticas de la página."""
    words: int = Field(default=0, description="Número de palabras")
    reading_time_min: int = Field(default=0, description="Tiempo lectura estimado en minutos")
    internal_links: int = Field(default=0, description="Enlaces internos")
    external_links: int = Field(default=0, description="Enlaces externos")


class Product(BaseModel):
    """Modelo para producto extraído."""
    nombre: str = Field(..., description="Nombre del producto")
    categoria: Optional[str] = Field(None, description="Categoría del producto")
    marca: Optional[str] = Field(None, description="Marca del producto")
    precio: Optional[float] = Field(None, description="Precio del producto")
    moneda: Optional[str] = Field(None, description="Moneda del precio")


class KeywordsBuckets(BaseModel):
    """Buckets de keywords clasificadas."""
    cliente: List[KeywordScore] = Field(default_factory=list, description="Keywords de cliente/marca")
    producto_o_post: List[KeywordScore] = Field(default_factory=list, description="Keywords específicas producto/post")
    generales_seo: List[KeywordScore] = Field(default_factory=list, description="Keywords generales SEO")


class URLAnalysisResponse(BaseModel):
    """Response completo para análisis de URL individual."""
    url: str = Field(..., description="URL analizada")
    tipo: str = Field(..., description="Tipo de página: ecommerce|blog|mixto")
    meta: MetaData = Field(..., description="Metadatos extraídos")
    headings: Headings = Field(..., description="Headings extraídos")
    stats: Stats = Field(..., description="Estadísticas de la página")
    audiencia: List[str] = Field(default_factory=list, description="Audiencia detectada")
    intencion: str = Field(..., description="Intención: informacional|consideracion|comercial")
    productos: List[Product] = Field(default_factory=list, description="Productos extraídos (si aplica)")
    keywords: KeywordsBuckets = Field(..., description="Keywords clasificadas en buckets")


class DomainSummary(BaseModel):
    """Resumen agregado del análisis de dominio."""
    total_urls: int = Field(..., description="Total URLs procesadas")
    por_tipo: Dict[str, int] = Field(..., description="Conteo por tipo de página")
    top_keywords_cliente: List[KeywordScore] = Field(default_factory=list, description="Top keywords cliente")
    top_keywords_producto: List[KeywordScore] = Field(default_factory=list, description="Top keywords producto")
    top_keywords_generales: List[KeywordScore] = Field(default_factory=list, description="Top keywords generales")


class DomainAnalysisResponse(BaseModel):
    """Response completo para análisis de dominio."""
    domain: str = Field(..., description="Dominio analizado")
    resumen: DomainSummary = Field(..., description="Resumen agregado")
    urls: List[URLAnalysisResponse] = Field(..., description="Lista de análisis por URL")


class ScoringWeightsResponse(BaseModel):
    """Response con pesos actuales de scoring."""
    weights: Dict[str, float] = Field(..., description="Pesos actuales")
    normalized: bool = Field(default=True, description="Si los pesos están normalizados")


class HealthResponse(BaseModel):
    """Response para health check."""
    status: str = Field(default="healthy", description="Estado del servicio")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del check")
    version: str = Field(default="1.0.0", description="Versión de la API")


# ===== ERROR MODELS =====

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error."""
    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del error")


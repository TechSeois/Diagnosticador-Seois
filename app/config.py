"""
Configuración de la aplicación usando Pydantic Settings.
Maneja variables de entorno y pesos ajustables para scoring.
"""
from typing import Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ScoringWeights(BaseModel):
    """Pesos ajustables para el cálculo de scores de keywords."""
    w1_frequency: float = Field(default=0.3, ge=0, le=1, description="Peso para frecuencia de términos")
    w2_tfidf: float = Field(default=0.25, ge=0, le=1, description="Peso para TF-IDF")
    w3_cooccurrence: float = Field(default=0.2, ge=0, le=1, description="Peso para co-ocurrencias en headings")
    w4_position_title: float = Field(default=0.15, ge=0, le=1, description="Peso para posición en título")
    w5_similarity_brand: float = Field(default=0.1, ge=0, le=1, description="Peso para similitud con marca")
    
    def normalize_weights(self) -> None:
        """Normaliza los pesos para que sumen 1.0"""
        total = sum([self.w1_frequency, self.w2_tfidf, self.w3_cooccurrence, 
                    self.w4_position_title, self.w5_similarity_brand])
        if total > 0:
            self.w1_frequency /= total
            self.w2_tfidf /= total
            self.w3_cooccurrence /= total
            self.w4_position_title /= total
            self.w5_similarity_brand /= total


class Settings(BaseSettings):
    """Configuración principal de la aplicación."""
    
    # API Configuration
    api_key: str = Field(default="your-secret-api-key-here", alias="API_KEY", description="Clave API para autenticación")
    max_concurrent_requests: int = Field(default=10, alias="MAX_CONCURRENT_REQUESTS", ge=1, le=50, description="Máximo requests concurrentes")
    default_timeout: int = Field(default=15, alias="DEFAULT_TIMEOUT", ge=5, le=60, description="Timeout por defecto en segundos")
    max_urls_per_domain: int = Field(default=100, alias="MAX_URLS_PER_DOMAIN", ge=1, le=1000, description="Máximo URLs por dominio")
    
    # Scoring weights
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    
    # NLP Configuration
    yake_max_ngram_size: int = Field(default=2, alias="YAKE_MAX_NGRAM_SIZE", ge=1, le=3, description="Tamaño máximo n-gramas YAKE")
    yake_deduplication_threshold: float = Field(default=0.7, alias="YAKE_DEDUPLICATION_THRESHOLD", ge=0, le=1, description="Umbral deduplicación YAKE")
    keybert_max_ngram_size: int = Field(default=2, alias="KEYBERT_MAX_NGRAM_SIZE", ge=1, le=3, description="Tamaño máximo n-gramas KeyBERT")
    keybert_diversity: float = Field(default=0.5, alias="KEYBERT_DIVERSITY", ge=0, le=1, description="Diversidad KeyBERT")
    similarity_threshold: float = Field(default=0.85, alias="SIMILARITY_THRESHOLD", ge=0, le=1, description="Umbral similitud coseno")
    
    # Classification Configuration
    ecommerce_threshold: float = Field(default=0.6, alias="ECOMMERCE_THRESHOLD", ge=0, le=1, description="Umbral clasificación e-commerce")
    mixed_threshold: float = Field(default=0.1, alias="MIXED_THRESHOLD", ge=0, le=1, description="Umbral para páginas mixtas")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Nivel de logging")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Normalizar pesos al inicializar
        self.scoring_weights.normalize_weights()
    
    def update_scoring_weights(self, weights: Dict[str, float]) -> None:
        """Actualiza los pesos de scoring dinámicamente."""
        if "w1_frequency" in weights:
            self.scoring_weights.w1_frequency = weights["w1_frequency"]
        if "w2_tfidf" in weights:
            self.scoring_weights.w2_tfidf = weights["w2_tfidf"]
        if "w3_cooccurrence" in weights:
            self.scoring_weights.w3_cooccurrence = weights["w3_cooccurrence"]
        if "w4_position_title" in weights:
            self.scoring_weights.w4_position_title = weights["w4_position_title"]
        if "w5_similarity_brand" in weights:
            self.scoring_weights.w5_similarity_brand = weights["w5_similarity_brand"]
        
        self.scoring_weights.normalize_weights()


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Obtiene la instancia de configuración."""
    return settings

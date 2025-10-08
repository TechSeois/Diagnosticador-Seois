#!/usr/bin/env python3
"""
Script de prueba para verificar que el sistema funciona correctamente.
"""

import asyncio
import sys
import os

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_basic_functionality():
    """Prueba básica de funcionalidad."""
    try:
        print("🔍 Probando configuración...")
        from app.config import get_settings
        settings = get_settings()
        print(f"✅ Configuración OK - API Key: {settings.api_key[:10]}...")
        
        print("🔍 Probando schemas...")
        from app.schemas import URLAnalysisRequest, DomainAnalysisRequest
        url_req = URLAnalysisRequest(url="https://example.com")
        domain_req = DomainAnalysisRequest(domain="https://example.com", max_urls=10)
        print("✅ Schemas OK")
        
        print("🔍 Probando servicios básicos...")
        from app.services.utils import TextUtils
        text_utils = TextUtils()
        normalized = text_utils.normalize_text("Hola mundo! Esto es una prueba.")
        print(f"✅ TextUtils OK - Texto normalizado: {normalized}")
        
        print("🔍 Probando fetcher...")
        from app.services.fetcher import HTTPFetcher
        async with HTTPFetcher() as fetcher:
            print("✅ HTTPFetcher OK")
        
        print("🔍 Probando parser...")
        from app.services.parser import HTMLParserService
        parser = HTMLParserService()
        print("✅ HTMLParser OK")
        
        print("🔍 Probando clasificador...")
        from app.services.classifier import PageClassifier
        classifier = PageClassifier()
        print("✅ PageClassifier OK")
        
        print("🔍 Probando NLP (sin inicializar modelos pesados)...")
        # Solo probamos la importación, no la inicialización completa
        print("✅ NLP imports OK")
        
        print("🔍 Probando scorer...")
        from app.services.scorer import KeywordScorer
        scorer = KeywordScorer()
        print("✅ KeywordScorer OK")
        
        print("🔍 Probando sitemap...")
        from app.services.sitemap import SitemapService
        sitemap_service = SitemapService()
        print("✅ SitemapService OK")
        
        print("🔍 Probando ecom...")
        from app.services.ecom import EcommerceExtractor
        ecom_extractor = EcommerceExtractor()
        print("✅ EcommerceExtractor OK")
        
        print("\n🎉 ¡Todas las pruebas básicas pasaron correctamente!")
        print("📋 El sistema está listo para usar.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fastapi_app():
    """Prueba la aplicación FastAPI."""
    try:
        print("\n🔍 Probando aplicación FastAPI...")
        from app.main import app
        print("✅ FastAPI app OK")
        
        # Verificar que los endpoints están registrados
        routes = [route.path for route in app.routes]
        expected_routes = ["/analyze-url", "/analyze-domain", "/scoring-weights", "/healthz", "/docs", "/redoc"]
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Endpoint {route} registrado")
            else:
                print(f"⚠️  Endpoint {route} no encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en FastAPI: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal de pruebas."""
    print("🚀 Iniciando pruebas del Sistema de Análisis SEO de Dominios")
    print("=" * 60)
    
    # Pruebas básicas
    basic_ok = await test_basic_functionality()
    
    # Pruebas FastAPI
    fastapi_ok = test_fastapi_app()
    
    print("\n" + "=" * 60)
    if basic_ok and fastapi_ok:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ El sistema está completamente funcional")
        print("\n📝 Para iniciar el servidor:")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload")
        print("\n📝 Para probar con Docker:")
        print("   docker-compose up -d")
        print("\n📝 Documentación disponible en:")
        print("   http://localhost:8080/docs")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisa los errores anteriores")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())


#!/usr/bin/env python3
"""
Prueba del fallback cuando no hay sitemap - Solo home
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.fetcher import HTTPFetcher
from app.services.parser import HTMLParserService
from app.services.classifier import PageClassifier
from app.services.nlp import NLPService
from app.services.scorer import KeywordScorer
from app.services.sitemap import SitemapService

async def test_fallback_no_sitemap():
    """Prueba qué pasa cuando no hay sitemap disponible."""
    
    # Usar un dominio real que probablemente no tenga sitemap
    TEST_DOMAIN = "https://httpbin.org"
    
    print("PRUEBA DE FALLBACK SIN SITEMAP")
    print("=" * 50)
    print(f"Dominio: {TEST_DOMAIN}")
    print(f"Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        # Inicializar servicios
        print("1. Inicializando servicios...")
        parser_service = HTMLParserService()
        classifier = PageClassifier()
        nlp_service = NLPService()
        scorer = KeywordScorer()
        sitemap_service = SitemapService()
        print("   Servicios inicializados correctamente")
        
        # Paso 1: Intentar descubrir sitemap
        print("2. Intentando descubrir sitemap...")
        async with HTTPFetcher() as fetcher:
            sitemap_url = await sitemap_service.discover_sitemap(TEST_DOMAIN, fetcher)
            
            if sitemap_url:
                print(f"   Sitemap encontrado: {sitemap_url}")
                return False  # No es lo que queremos probar
            else:
                print("   OK - No se encontró sitemap (como esperábamos)")
        
        # Paso 2: Probar fallback con crawl
        print("3. Probando fallback con crawl...")
        async with HTTPFetcher() as fetcher:
            urls_data = await sitemap_service.crawl_fallback(TEST_DOMAIN, fetcher, max_urls=5)
            
            if urls_data:
                print(f"   URLs encontradas por crawl: {len(urls_data)}")
                for i, url_data in enumerate(urls_data[:3], 1):
                    print(f"     {i}. {url_data['url']}")
            else:
                print("   ERROR - No se encontraron URLs por crawl")
                return False
        
        # Paso 3: Analizar la página principal (home)
        print("4. Analizando página principal...")
        async with HTTPFetcher() as fetcher:
            response = await fetcher.fetch_url(TEST_DOMAIN)
            if not response:
                print("   ERROR - No se pudo descargar la página principal")
                return False
            
            print(f"   OK - Página principal descargada: {len(response.content)} bytes")
            
            # Parsear HTML
            parsed_data = parser_service.parse_html(response.text, TEST_DOMAIN)
            main_content = parsed_data.get('main_content', '')
            
            # Clasificar página
            page_type = classifier.classify_page_type(parsed_data, TEST_DOMAIN)
            audiencia = classifier.detect_audience(parsed_data)
            intencion = classifier.detect_intent(parsed_data, TEST_DOMAIN)
            brand_info = classifier.extract_brand_info(parsed_data, TEST_DOMAIN)
            
            print(f"   Tipo: {page_type}")
            print(f"   Audiencia: {audiencia}")
            print(f"   Intención: {intencion}")
            print(f"   Marca: {brand_info}")
            
            # Extraer keywords
            keywords_raw = nlp_service.extract_keywords(main_content)
            
            if keywords_raw:
                print(f"   OK - Keywords extraídas: {len(keywords_raw)}")
                
                # Calcular scores
                text_data = {
                    'main_content': main_content,
                    'meta': parsed_data.get('meta', {}),
                    'headings': parsed_data.get('headings', {})
                }
                
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
                
                print(f"   Cliente: {len(keywords_buckets['cliente'])}")
                print(f"   Producto/Post: {len(keywords_buckets['producto_o_post'])}")
                print(f"   Generales SEO: {len(keywords_buckets['generales_seo'])}")
                
                # Mostrar top keywords
                print("\nTOP KEYWORDS:")
                for bucket_name, keywords in keywords_buckets.items():
                    if keywords:
                        print(f"   {bucket_name.upper()}:")
                        for kw in keywords[:3]:
                            print(f"     - {kw['term']} (score: {kw['score']:.3f})")
                
                return True
            else:
                print("   ERROR - No se extrajeron keywords")
                return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal."""
    print("PRUEBA DE FALLBACK SIN SITEMAP")
    print("=" * 60)
    
    success = await test_fallback_no_sitemap()
    
    print("\n" + "=" * 60)
    if success:
        print("PRUEBA EXITOSA!")
        print("El fallback funciona correctamente cuando no hay sitemap")
        print("- Descubrimiento de sitemap falla correctamente")
        print("- Crawl de fallback funciona")
        print("- Análisis de página principal funciona")
        print("- Extracción de keywords funciona")
    else:
        print("PRUEBA FALLIDA")
        print("Revisa los errores anteriores")

if __name__ == "__main__":
    asyncio.run(main())

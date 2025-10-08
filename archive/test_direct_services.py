#!/usr/bin/env python3
"""
Prueba directa de los servicios sin pasar por la API
"""

import asyncio
import json
from app.services.fetcher import HTTPFetcher
from app.services.parser import HTMLParserService
from app.services.classifier import PageClassifier
from app.services.nlp import NLPService
from app.services.scorer import KeywordScorer

async def test_direct_services():
    """Prueba los servicios directamente."""
    
    TEST_URL = "https://speedlogic.com.co/"
    
    print("PRUEBA DIRECTA DE SERVICIOS")
    print("=" * 40)
    
    # Paso 1: Descargar
    print("1. Descargando HTML...")
    async with HTTPFetcher() as fetcher:
        response = await fetcher.fetch_url(TEST_URL)
        if not response:
            print("ERROR: No se pudo descargar")
            return
        print(f"   OK - {len(response.content)} bytes")
    
    # Paso 2: Parsear
    print("2. Parseando HTML...")
    parser = HTMLParserService()
    parsed_data = parser.parse_html(response.text, TEST_URL)
    main_content = parsed_data.get('main_content', '')
    print(f"   OK - {len(main_content)} caracteres")
    
    # Paso 3: Clasificar
    print("3. Clasificando...")
    classifier = PageClassifier()
    page_type = classifier.classify_page_type(parsed_data, TEST_URL)
    audiencia = classifier.detect_audience(parsed_data)
    intencion = classifier.detect_intent(parsed_data, TEST_URL)
    brand_info = classifier.extract_brand_info(parsed_data, TEST_URL)
    
    print(f"   Tipo: {page_type}")
    print(f"   Audiencia: {audiencia}")
    print(f"   Intencion: {intencion}")
    print(f"   Marca: {brand_info}")
    
    # Paso 4: NLP
    print("4. Extrayendo keywords...")
    nlp_service = NLPService()
    keywords_raw = nlp_service.extract_keywords(main_content)
    print(f"   Keywords extraidas: {len(keywords_raw)}")
    
    if len(keywords_raw) > 0:
        print("   Top 5 keywords:")
        for i, kw in enumerate(keywords_raw[:5], 1):
            print(f"     {i}. {kw['term']} (score: {kw['score']:.3f}, source: {kw['source']})")
    else:
        print("   PROBLEMA: No se extrajeron keywords")
        return
    
    # Paso 5: Scoring
    print("5. Calculando scores...")
    scorer = KeywordScorer()
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
    
    print(f"   Scores calculados: {len(keywords_with_scores)}")
    
    # Paso 6: Bucketización
    print("6. Bucketizando...")
    keywords_buckets = scorer.bucketize_keywords(
        keywords_with_scores, page_type, brand_info
    )
    
    print(f"   Cliente: {len(keywords_buckets['cliente'])}")
    print(f"   Producto/Post: {len(keywords_buckets['producto_o_post'])}")
    print(f"   Generales SEO: {len(keywords_buckets['generales_seo'])}")
    
    # Mostrar resultados
    print("\nRESULTADOS FINALES:")
    for bucket_name, keywords in keywords_buckets.items():
        if keywords:
            print(f"\n{bucket_name.upper()}:")
            for kw in keywords[:5]:
                print(f"  - {kw['term']} (score: {kw['score']:.3f})")
    
    # Guardar resultado
    result = {
        'url': TEST_URL,
        'page_type': page_type,
        'audiencia': audiencia,
        'intencion': intencion,
        'brand_info': brand_info,
        'keywords_raw': keywords_raw,
        'keywords_buckets': keywords_buckets
    }
    
    with open('direct_services_test.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultado guardado en: direct_services_test.json")
    print("¡PRUEBA DIRECTA EXITOSA!")

async def main():
    await test_direct_services()

if __name__ == "__main__":
    asyncio.run(main())


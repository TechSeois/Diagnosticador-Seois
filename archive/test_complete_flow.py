#!/usr/bin/env python3
"""
Prueba detallada del flujo completo de análisis
"""

import asyncio
import httpx
import json
from app.services.fetcher import HTTPFetcher
from app.services.parser import HTMLParserService
from app.services.classifier import PageClassifier
from app.services.nlp import NLPService
from app.services.scorer import KeywordScorer

async def test_complete_flow():
    """Prueba el flujo completo paso a paso."""
    
    TEST_URL = "https://speedlogic.com.co/"
    
    print("PRUEBA COMPLETA DEL FLUJO DE ANALISIS")
    print("=" * 50)
    
    # Paso 1: Descargar HTML
    print("1. Descargando HTML...")
    async with HTTPFetcher() as fetcher:
        response = await fetcher.fetch_url(TEST_URL)
        if not response:
            print("ERROR: No se pudo descargar")
            return
        print(f"   OK - {len(response.content)} bytes")
    
    # Paso 2: Parsear HTML
    print("2. Parseando HTML...")
    parser = HTMLParserService()
    parsed_data = parser.parse_html(response.text, TEST_URL)
    main_content = parsed_data.get('main_content', '')
    print(f"   OK - {len(main_content)} caracteres de contenido")
    
    # Paso 3: Clasificar
    print("3. Clasificando pagina...")
    classifier = PageClassifier()
    page_type = classifier.classify_page_type(parsed_data, TEST_URL)
    audiencia = classifier.detect_audience(parsed_data)
    intencion = classifier.detect_intent(parsed_data, TEST_URL)
    brand_info = classifier.extract_brand_info(parsed_data, TEST_URL)
    
    print(f"   Tipo: {page_type}")
    print(f"   Audiencia: {audiencia}")
    print(f"   Intencion: {intencion}")
    print(f"   Marca: {brand_info}")
    
    # Paso 4: Extraer keywords
    print("4. Extrayendo keywords...")
    nlp_service = NLPService()
    keywords_raw = nlp_service.extract_keywords(main_content)
    print(f"   Keywords extraidas: {len(keywords_raw)}")
    
    for i, kw in enumerate(keywords_raw[:5], 1):
        print(f"   {i}. {kw['term']} (score: {kw['score']:.3f}, source: {kw['source']})")
    
    if len(keywords_raw) == 0:
        print("   PROBLEMA: No se extrajeron keywords")
        return
    
    # Paso 5: Calcular scores
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
        print(f"   {keyword}: {score:.3f}")
    
    # Paso 6: Bucketizar
    print("6. Bucketizando keywords...")
    keywords_buckets = scorer.bucketize_keywords(
        keywords_with_scores, page_type, brand_info
    )
    
    print(f"   Cliente: {len(keywords_buckets['cliente'])}")
    print(f"   Producto/Post: {len(keywords_buckets['producto_o_post'])}")
    print(f"   Generales SEO: {len(keywords_buckets['generales_seo'])}")
    
    # Mostrar keywords por bucket
    for bucket_name, keywords in keywords_buckets.items():
        if keywords:
            print(f"   {bucket_name}:")
            for kw in keywords[:3]:
                print(f"     - {kw['term']} (score: {kw['score']:.3f})")
    
    print()
    print("RESUMEN FINAL:")
    print(f"- Keywords extraidas: {len(keywords_raw)}")
    print(f"- Keywords con scores: {len(keywords_with_scores)}")
    print(f"- Total en buckets: {sum(len(bucket) for bucket in keywords_buckets.values())}")
    
    # Guardar resultado
    result = {
        'url': TEST_URL,
        'keywords_raw': keywords_raw,
        'keywords_with_scores': keywords_with_scores,
        'keywords_buckets': keywords_buckets,
        'page_type': page_type,
        'brand_info': brand_info
    }
    
    with open('speedlogic_complete_flow.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("Resultado guardado en: speedlogic_complete_flow.json")

async def main():
    await test_complete_flow()

if __name__ == "__main__":
    asyncio.run(main())


#!/usr/bin/env python3
"""
Prueba directa de los servicios sin servidor HTTP
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

async def test_speedlogic_direct():
    """Prueba directa del análisis de SpeedLogic sin servidor."""
    
    TEST_URL = "https://speedlogic.com.co/"
    
    print("PRUEBA DIRECTA - SPEEDLOGIC")
    print("=" * 50)
    print(f"URL: {TEST_URL}")
    print(f"Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    try:
        # Inicializar servicios
        print("1. Inicializando servicios...")
        parser_service = HTMLParserService()
        classifier = PageClassifier()
        nlp_service = NLPService()
        scorer = KeywordScorer()
        print("   Servicios inicializados correctamente")
        
        # Paso 1: Descargar HTML
        print("2. Descargando HTML...")
        async with HTTPFetcher() as fetcher:
            response = await fetcher.fetch_url(TEST_URL)
            if not response:
                print("ERROR: No se pudo descargar la URL")
                return False
            print(f"   OK - {len(response.content)} bytes descargados")
        
        # Paso 2: Parsear HTML
        print("3. Parseando HTML...")
        parsed_data = parser_service.parse_html(response.text, TEST_URL)
        main_content = parsed_data.get('main_content', '')
        print(f"   OK - {len(main_content)} caracteres de contenido principal")
        
        # Paso 3: Clasificar página
        print("4. Clasificando página...")
        page_type = classifier.classify_page_type(parsed_data, TEST_URL)
        audiencia = classifier.detect_audience(parsed_data)
        intencion = classifier.detect_intent(parsed_data, TEST_URL)
        brand_info = classifier.extract_brand_info(parsed_data, TEST_URL)
        
        print(f"   Tipo: {page_type}")
        print(f"   Audiencia: {audiencia}")
        print(f"   Intención: {intencion}")
        print(f"   Marca: {brand_info}")
        
        # Paso 4: Extraer keywords
        print("5. Extrayendo keywords...")
        keywords_raw = nlp_service.extract_keywords(main_content)
        print(f"   Keywords extraídas: {len(keywords_raw)}")
        
        if len(keywords_raw) == 0:
            print("   PROBLEMA: No se extrajeron keywords")
            return False
        
        # Paso 5: Calcular scores
        print("6. Calculando scores...")
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
        
        # Paso 6: Bucketizar keywords
        print("7. Bucketizando keywords...")
        keywords_buckets = scorer.bucketize_keywords(
            keywords_with_scores, page_type, brand_info
        )
        
        print(f"   Cliente: {len(keywords_buckets['cliente'])}")
        print(f"   Producto/Post: {len(keywords_buckets['producto_o_post'])}")
        print(f"   Generales SEO: {len(keywords_buckets['generales_seo'])}")
        
        # Mostrar resultados
        print("\nRESULTADOS FINALES:")
        print("=" * 50)
        
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
            'keywords_buckets': keywords_buckets,
            'meta': parsed_data.get('meta', {}),
            'headings': parsed_data.get('headings', {}),
            'stats': {
                'words': len(main_content.split()),
                'reading_time_min': len(main_content.split()) // 200
            }
        }
        
        with open('results/speedlogic_direct_test.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResultado guardado en: results/speedlogic_direct_test.json")
        print("PRUEBA DIRECTA EXITOSA!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal."""
    print("PRUEBA DIRECTA DE SERVICIOS - SPEEDLOGIC")
    print("=" * 60)
    
    success = await test_speedlogic_direct()
    
    print("\n" + "=" * 60)
    if success:
        print("PRUEBA EXITOSA!")
        print("Los servicios funcionan correctamente sin servidor HTTP")
    else:
        print("PRUEBA FALLIDA")
        print("Revisa los errores anteriores")

if __name__ == "__main__":
    asyncio.run(main())

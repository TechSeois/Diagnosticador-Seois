#!/usr/bin/env python3
"""
Diagnóstico del análisis de SpeedLogic
"""

import asyncio
import httpx
import json
from app.services.fetcher import HTTPFetcher
from app.services.parser import HTMLParserService

async def diagnose_speedlogic():
    """Diagnostica el análisis de SpeedLogic paso a paso."""
    
    TEST_URL = "https://speedlogic.com.co/"
    
    print("DIAGNOSTICO DEL ANALISIS DE SPEEDLOGIC")
    print("=" * 50)
    
    async with HTTPFetcher() as fetcher:
        print("1. Descargando HTML...")
        response = await fetcher.fetch_url(TEST_URL)
        
        if not response:
            print("ERROR: No se pudo descargar la URL")
            return
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Tamaño: {len(response.content)} bytes")
        print()
        
        print("2. Parseando HTML...")
        parser = HTMLParserService()
        parsed_data = parser.parse_html(response.text, TEST_URL)
        
        print("   Metadatos extraidos:")
        meta = parsed_data.get('meta', {})
        print(f"   - Titulo: {meta.get('title', 'N/A')[:50]}...")
        print(f"   - Descripcion: {meta.get('description', 'N/A')[:50]}...")
        print()
        
        print("   Headings extraidos:")
        headings = parsed_data.get('headings', {})
        print(f"   - H1: {len(headings.get('h1', []))}")
        print(f"   - H2: {len(headings.get('h2', []))}")
        print(f"   - H3: {len(headings.get('h3', []))}")
        print()
        
        print("   Contenido principal:")
        main_content = parsed_data.get('main_content', '')
        print(f"   - Longitud: {len(main_content)} caracteres")
        print(f"   - Palabras: {len(main_content.split())}")
        print(f"   - Primeros 200 caracteres: {main_content[:200]}...")
        print()
        
        print("   Estadisticas:")
        stats = parsed_data.get('stats', {})
        print(f"   - Palabras: {stats.get('words', 0)}")
        print(f"   - Enlaces internos: {stats.get('internal_links', 0)}")
        print(f"   - Enlaces externos: {stats.get('external_links', 0)}")
        print()
        
        print("3. Probando extraccion de keywords...")
        from app.services.nlp import NLPService
        
        try:
            nlp_service = NLPService()
            keywords = nlp_service.extract_keywords(main_content, max_keywords=10)
            
            print(f"   Keywords extraidas: {len(keywords)}")
            for i, kw in enumerate(keywords[:5], 1):
                print(f"   {i}. {kw['term']} (score: {kw['score']:.3f}, source: {kw['source']})")
            
            if len(keywords) == 0:
                print("   PROBLEMA: No se extrajeron keywords")
                print("   Posibles causas:")
                print("   - Contenido muy corto")
                print("   - Problema con modelos NLP")
                print("   - Texto no contiene palabras significativas")
            
        except Exception as e:
            print(f"   ERROR en extraccion de keywords: {e}")
        
        print()
        print("4. Probando clasificacion...")
        from app.services.classifier import PageClassifier
        
        try:
            classifier = PageClassifier()
            page_type = classifier.classify_page_type(parsed_data, TEST_URL)
            audiencia = classifier.detect_audience(parsed_data)
            intencion = classifier.detect_intent(parsed_data, TEST_URL)
            
            print(f"   Tipo de pagina: {page_type}")
            print(f"   Audiencia: {audiencia}")
            print(f"   Intencion: {intencion}")
            
        except Exception as e:
            print(f"   ERROR en clasificacion: {e}")
        
        print()
        print("5. Guardando datos completos...")
        with open('speedlogic_diagnostic.json', 'w', encoding='utf-8') as f:
            json.dump({
                'url': TEST_URL,
                'parsed_data': parsed_data,
                'keywords': keywords if 'keywords' in locals() else []
            }, f, indent=2, ensure_ascii=False)
        
        print("   Datos guardados en: speedlogic_diagnostic.json")

async def main():
    await diagnose_speedlogic()

if __name__ == "__main__":
    asyncio.run(main())


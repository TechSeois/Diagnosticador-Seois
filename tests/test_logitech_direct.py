#!/usr/bin/env python3
"""
Prueba directa del análisis de dominio con Logitech sin servidor HTTP
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

async def test_logitech_domain_direct():
    """Prueba directa del análisis de dominio de Logitech."""
    
    TEST_DOMAIN = "https://www.logitech.com"
    MAX_URLS = 5  # Reducido para prueba rápida
    
    print("PRUEBA DIRECTA DE DOMINIO - LOGITECH")
    print("=" * 60)
    print(f"Dominio: {TEST_DOMAIN}")
    print(f"Max URLs: {MAX_URLS}")
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
        
        # Paso 1: Descubrir URLs del sitemap
        print("2. Descubriendo URLs del sitemap...")
        async with HTTPFetcher() as fetcher:
            # Primero descubrir el sitemap
            sitemap_url = await sitemap_service.discover_sitemap(TEST_DOMAIN, fetcher)
            if not sitemap_url:
                print("   ERROR: No se encontró sitemap")
                return False
            
            print(f"   Sitemap encontrado: {sitemap_url}")
            
            # Parsear el sitemap
            urls_data = await sitemap_service.parse_sitemap(sitemap_url, fetcher, max_urls=MAX_URLS)
            urls = [url_data['url'] for url_data in urls_data]
            
            print(f"   URLs encontradas: {len(urls)}")
            
            if not urls:
                print("   ERROR: No se encontraron URLs")
                return False
            
            # Mostrar algunas URLs encontradas
            print("   Primeras URLs encontradas:")
            for i, url in enumerate(urls[:3], 1):
                print(f"     {i}. {url}")
        
        # Paso 2: Analizar cada URL
        print(f"\n3. Analizando {len(urls)} URLs...")
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"   Analizando URL {i}/{len(urls)}: {url}")
            
            try:
                # Descargar HTML
                response = await fetcher.fetch_url(url)
                if not response:
                    print(f"     ERROR: No se pudo descargar")
                    continue
                
                # Parsear HTML
                parsed_data = parser_service.parse_html(response.text, url)
                main_content = parsed_data.get('main_content', '')
                
                # Clasificar página
                page_type = classifier.classify_page_type(parsed_data, url)
                audiencia = classifier.detect_audience(parsed_data)
                intencion = classifier.detect_intent(parsed_data, url)
                brand_info = classifier.extract_brand_info(parsed_data, url)
                
                # Extraer keywords
                keywords_raw = nlp_service.extract_keywords(main_content)
                
                if keywords_raw:
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
                    
                    result = {
                        'url': url,
                        'tipo': page_type,
                        'audiencia': audiencia,
                        'intencion': intencion,
                        'brand_info': brand_info,
                        'keywords': keywords_buckets,
                        'meta': parsed_data.get('meta', {}),
                        'stats': {
                            'words': len(main_content.split()),
                            'reading_time_min': len(main_content.split()) // 200
                        }
                    }
                    
                    results.append(result)
                    print(f"     OK - {len(keywords_with_scores)} keywords extraídas")
                else:
                    print(f"     WARNING: No se extrajeron keywords")
                    
            except Exception as e:
                print(f"     ERROR: {e}")
                continue
        
        if not results:
            print("ERROR: No se pudo analizar ninguna URL")
            return False
        
        # Paso 3: Generar resumen
        print(f"\n4. Generando resumen de {len(results)} URLs analizadas...")
        
        # Contar por tipo
        tipos = {}
        for result in results:
            tipo = result['tipo']
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        # Agregar keywords por bucket
        all_keywords = {'cliente': [], 'producto_o_post': [], 'generales_seo': []}
        
        for result in results:
            for bucket_name, keywords in result['keywords'].items():
                all_keywords[bucket_name].extend(keywords)
        
        # Ordenar y tomar top keywords por bucket
        top_keywords = {}
        for bucket_name, keywords in all_keywords.items():
            keywords_sorted = sorted(keywords, key=lambda x: x['score'], reverse=True)
            # Eliminar duplicados por término
            seen = set()
            unique_keywords = []
            for kw in keywords_sorted:
                if kw['term'] not in seen:
                    unique_keywords.append(kw)
                    seen.add(kw['term'])
            top_keywords[bucket_name] = unique_keywords[:10]
        
        resumen = {
            'total_urls': len(results),
            'por_tipo': tipos,
            'top_keywords_cliente': top_keywords['cliente'],
            'top_keywords_producto': top_keywords['producto_o_post'],
            'top_keywords_generales': top_keywords['generales_seo']
        }
        
        # Mostrar resultados
        print("\nRESUMEN DEL ANÁLISIS:")
        print("=" * 50)
        print(f"Total URLs procesadas: {resumen['total_urls']}")
        print(f"Por tipo: {resumen['por_tipo']}")
        print()
        
        # Top keywords por bucket
        print("TOP KEYWORDS DEL DOMINIO:")
        if resumen['top_keywords_cliente']:
            print(f"   Cliente ({len(resumen['top_keywords_cliente'])}):")
            for kw in resumen['top_keywords_cliente'][:5]:
                print(f"     - {kw['term']} (score: {kw['score']:.3f})")
        
        if resumen['top_keywords_producto']:
            print(f"   Producto ({len(resumen['top_keywords_producto'])}):")
            for kw in resumen['top_keywords_producto'][:5]:
                print(f"     - {kw['term']} (score: {kw['score']:.3f})")
        
        if resumen['top_keywords_generales']:
            print(f"   Generales ({len(resumen['top_keywords_generales'])}):")
            for kw in resumen['top_keywords_generales'][:5]:
                print(f"     - {kw['term']} (score: {kw['score']:.3f})")
        
        # Guardar resultado completo
        final_result = {
            'domain': TEST_DOMAIN,
            'resumen': resumen,
            'urls': results
        }
        
        with open('results/logitech_direct_test.json', 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResultado completo guardado en: results/logitech_direct_test.json")
        print("PRUEBA DIRECTA DE DOMINIO EXITOSA!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal."""
    print("PRUEBA DIRECTA DE ANÁLISIS DE DOMINIO - LOGITECH")
    print("=" * 70)
    
    success = await test_logitech_domain_direct()
    
    print("\n" + "=" * 70)
    if success:
        print("PRUEBA EXITOSA!")
        print("El análisis de dominio de Logitech funcionó correctamente")
        print("- Descubrimiento de sitemap funcionando")
        print("- Análisis de múltiples URLs funcionando")
        print("- Clasificación por tipo funcionando")
        print("- Extracción de keywords funcionando")
    else:
        print("PRUEBA FALLIDA")
        print("Revisa los errores anteriores")

if __name__ == "__main__":
    asyncio.run(main())

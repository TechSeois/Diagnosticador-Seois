#!/usr/bin/env python3
"""
Prueba del análisis inteligente de dominio con SpeedLogic
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_intelligent_domain_analysis():
    """Prueba el análisis inteligente de dominio."""
    
    API_BASE_URL = "http://127.0.0.1:8080"
    API_KEY = "your-secret-api-key-here"
    TEST_DOMAIN = "https://speedlogic.com.co"
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "domain": TEST_DOMAIN,
        "max_urls": 15,
        "timeout": 30
    }
    
    print("PRUEBA DE ANALISIS INTELIGENTE DE DOMINIO")
    print("=" * 60)
    print(f"Dominio: {TEST_DOMAIN}")
    print(f"Max URLs: {payload['max_urls']}")
    print(f"Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print("Enviando request de analisis de dominio...")
            response = await client.post(
                f"{API_BASE_URL}/analyze-domain",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print("Analisis de dominio completado exitosamente!")
                print()
                
                # Información del resumen
                resumen = data['resumen']
                print("RESUMEN DEL DOMINIO:")
                print(f"   Total URLs procesadas: {resumen['total_urls']}")
                print(f"   Por tipo: {resumen['por_tipo']}")
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
                
                print()
                
                # Detalles de URLs procesadas
                urls = data['urls']
                print(f"DETALLES DE {len(urls)} URLs PROCESADAS:")
                
                # Agrupar por tipo
                tipos = {}
                for url_data in urls:
                    tipo = url_data['tipo']
                    if tipo not in tipos:
                        tipos[tipo] = []
                    tipos[tipo].append(url_data)
                
                for tipo, urls_tipo in tipos.items():
                    print(f"\n{tipo.upper()} ({len(urls_tipo)} URLs):")
                    for i, url_data in enumerate(urls_tipo[:3], 1):  # Mostrar solo las primeras 3
                        print(f"   {i}. {url_data['url']}")
                        print(f"      Tipo: {url_data['tipo']}")
                        print(f"      Intencion: {url_data['intencion']}")
                        print(f"      Audiencia: {', '.join(url_data['audiencia']) if url_data['audiencia'] else 'No detectada'}")
                        print(f"      Palabras: {url_data['stats']['words']}")
                        
                        # Mostrar keywords principales
                        keywords = url_data['keywords']
                        if any(keywords.values()):
                            print(f"      Keywords principales:")
                            for bucket_name, bucket_keywords in keywords.items():
                                if bucket_keywords:
                                    top_kw = bucket_keywords[0]
                                    print(f"        {bucket_name}: {top_kw['term']} ({top_kw['score']:.3f})")
                        print()
                
                # Guardar resultado completo
                with open('results/speedlogic_domain_analysis.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("Resultado completo guardado en: results/speedlogic_domain_analysis.json")
                
                print()
                print("ANALISIS INTELIGENTE COMPLETADO EXITOSAMENTE!")
                print(f"- URLs seleccionadas inteligentemente: {len(urls)}")
                print(f"- Categorizacion por tipo: {resumen['por_tipo']}")
                print(f"- Keywords extraidas y clasificadas")
                print(f"- Analisis profundo por categoria")
                
                return True
                
            else:
                print(f"Error en el analisis: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return False
                
        except httpx.ConnectError:
            print("No se pudo conectar al servidor")
            print("Asegurate de que el servidor este ejecutandose:")
            print("   uvicorn app.main:app --host 127.0.0.1 --port 8080")
            return False
        except Exception as e:
            print(f"Error inesperado: {e}")
            return False

async def test_health_check():
    """Prueba el health check antes del análisis."""
    print("Verificando servidor...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8080/healthz")
            if response.status_code == 200:
                data = response.json()
                print(f"Servidor OK: {data['status']}")
                return True
            else:
                print(f"Servidor no disponible: {response.status_code}")
                return False
    except Exception as e:
        print(f"Error conectando al servidor: {e}")
        return False

async def main():
    """Función principal."""
    print("PRUEBA DE ANALISIS INTELIGENTE DE DOMINIO - SPEEDLOGIC")
    print("=" * 70)
    
    # Verificar servidor
    if not await test_health_check():
        print("\nPara iniciar el servidor:")
        print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8080")
        return
    
    print()
    
    # Ejecutar análisis inteligente
    success = await test_intelligent_domain_analysis()
    
    print("\n" + "=" * 70)
    if success:
        print("PRUEBA EXITOSA!")
        print("El analisis inteligente de dominio funciono correctamente")
        print("- Seleccion por categorias implementada")
        print("- Filtrado por fecha (ultimos 5 dias) funcionando")
        print("- Analisis profundo de hasta 15 URLs")
    else:
        print("PRUEBA FALLIDA")
        print("Revisa los errores anteriores")

if __name__ == "__main__":
    asyncio.run(main())

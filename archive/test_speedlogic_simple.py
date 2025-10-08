#!/usr/bin/env python3
"""
Prueba específica con la URL de SpeedLogic
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_speedlogic_url():
    """Prueba el análisis de la URL de SpeedLogic."""
    
    API_BASE_URL = "http://127.0.0.1:8080"
    API_KEY = "your-secret-api-key-here"
    TEST_URL = "https://speedlogic.com.co/"
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": TEST_URL
    }
    
    print("Probando analisis de SpeedLogic")
    print("=" * 50)
    print(f"URL: {TEST_URL}")
    print(f"Iniciado: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print("Enviando request de analisis...")
            response = await client.post(
                f"{API_BASE_URL}/analyze-url",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print("Analisis completado exitosamente!")
                print()
                
                # Información básica
                print("INFORMACION BASICA:")
                print(f"   URL: {data['url']}")
                print(f"   Tipo: {data['tipo']}")
                print(f"   Intencion: {data['intencion']}")
                print(f"   Audiencia: {', '.join(data['audiencia']) if data['audiencia'] else 'No detectada'}")
                print()
                
                # Metadatos
                meta = data['meta']
                print("METADATOS:")
                print(f"   Titulo: {meta['title'][:80]}..." if meta['title'] else "   Titulo: No encontrado")
                print(f"   Descripcion: {meta['description'][:100]}..." if meta['description'] else "   Descripcion: No encontrada")
                print(f"   Idioma: {meta['lang']}")
                print()
                
                # Headings
                headings = data['headings']
                print("HEADINGS:")
                if headings['h1']:
                    print(f"   H1: {headings['h1'][0]}")
                if headings['h2']:
                    print(f"   H2: {', '.join(headings['h2'][:3])}")
                if headings['h3']:
                    print(f"   H3: {', '.join(headings['h3'][:3])}")
                print()
                
                # Estadísticas
                stats = data['stats']
                print("ESTADISTICAS:")
                print(f"   Palabras: {stats['words']}")
                print(f"   Tiempo lectura: {stats['reading_time_min']} min")
                print(f"   Enlaces internos: {stats['internal_links']}")
                print(f"   Enlaces externos: {stats['external_links']}")
                print()
                
                # Productos (si es e-commerce)
                if data['productos']:
                    print("PRODUCTOS DETECTADOS:")
                    for i, producto in enumerate(data['productos'][:3], 1):
                        print(f"   {i}. {producto['nombre']}")
                        if producto['precio']:
                            print(f"      Precio: {producto['precio']} {producto['moneda']}")
                        if producto['categoria']:
                            print(f"      Categoria: {producto['categoria']}")
                    print()
                
                # Keywords por bucket
                keywords = data['keywords']
                print("KEYWORDS EXTRAIDAS:")
                
                if keywords['cliente']:
                    print(f"   Cliente ({len(keywords['cliente'])}):")
                    for kw in keywords['cliente'][:5]:
                        print(f"      - {kw['term']} (score: {kw['score']:.3f})")
                
                if keywords['producto_o_post']:
                    print(f"   Producto/Post ({len(keywords['producto_o_post'])}):")
                    for kw in keywords['producto_o_post'][:5]:
                        print(f"      - {kw['term']} (score: {kw['score']:.3f})")
                
                if keywords['generales_seo']:
                    print(f"   Generales SEO ({len(keywords['generales_seo'])}):")
                    for kw in keywords['generales_seo'][:5]:
                        print(f"      - {kw['term']} (score: {kw['score']:.3f})")
                
                print()
                print("Analisis completado exitosamente!")
                
                # Guardar resultado completo
                with open('speedlogic_analysis.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("Resultado guardado en: speedlogic_analysis.json")
                
                return True
                
            else:
                print(f"Error en el analisis: {response.status_code}")
                print(f"   Respuesta: {response.text}")
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
    print("PRUEBA ESPECIFICA - SPEEDLOGIC")
    print("=" * 60)
    
    # Verificar servidor
    if not await test_health_check():
        print("\nPara iniciar el servidor:")
        print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8080")
        return
    
    print()
    
    # Ejecutar análisis
    success = await test_speedlogic_url()
    
    print("\n" + "=" * 60)
    if success:
        print("PRUEBA EXITOSA!")
        print("El sistema analizo correctamente la URL de SpeedLogic")
    else:
        print("PRUEBA FALLIDA")
        print("Revisa los errores anteriores")

if __name__ == "__main__":
    asyncio.run(main())


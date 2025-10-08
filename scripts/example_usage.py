#!/usr/bin/env python3
"""
Ejemplo de uso del Sistema de Análisis SEO de Dominios.
Demuestra cómo usar la API para analizar URLs y dominios.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuración
API_BASE_URL = "http://localhost:8080"
API_KEY = "your-secret-api-key-here"  # Cambiar por tu API key

async def test_health_check():
    """Prueba el endpoint de health check."""
    print("🔍 Probando health check...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/healthz")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check OK: {data['status']}")
                return True
            else:
                print(f"❌ Health check falló: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error en health check: {e}")
            return False

async def test_scoring_weights():
    """Prueba el endpoint de pesos de scoring."""
    print("\n🔍 Probando scoring weights...")
    
    headers = {"X-API-Key": API_KEY}
    
    async with httpx.AsyncClient() as client:
        try:
            # Obtener pesos actuales
            response = await client.get(f"{API_BASE_URL}/scoring-weights", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print("✅ Pesos actuales:")
                for key, value in data['weights'].items():
                    print(f"   {key}: {value}")
                
                # Actualizar pesos
                new_weights = {
                    "w1_frequency": 0.4,
                    "w2_tfidf": 0.3,
                    "w3_cooccurrence": 0.2,
                    "w4_position_title": 0.05,
                    "w5_similarity_brand": 0.05
                }
                
                response = await client.put(
                    f"{API_BASE_URL}/scoring-weights",
                    headers=headers,
                    json=new_weights
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Pesos actualizados:")
                    for key, value in data['weights'].items():
                        print(f"   {key}: {value}")
                    return True
                else:
                    print(f"❌ Error actualizando pesos: {response.status_code}")
                    return False
            else:
                print(f"❌ Error obteniendo pesos: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error en scoring weights: {e}")
            return False

async def test_url_analysis():
    """Prueba el análisis de una URL individual."""
    print("\n🔍 Probando análisis de URL...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # URL de ejemplo (usar una URL real para pruebas)
    test_url = "https://example.com"
    
    payload = {
        "url": test_url
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/analyze-url",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Análisis de URL completado:")
                print(f"   URL: {data['url']}")
                print(f"   Tipo: {data['tipo']}")
                print(f"   Intención: {data['intencion']}")
                print(f"   Audiencia: {', '.join(data['audiencia'])}")
                print(f"   Palabras: {data['stats']['words']}")
                print(f"   Tiempo lectura: {data['stats']['reading_time_min']} min")
                
                # Mostrar keywords por bucket
                keywords = data['keywords']
                print(f"\n📊 Keywords extraídas:")
                print(f"   Cliente ({len(keywords['cliente'])}): {[kw['term'] for kw in keywords['cliente'][:3]]}")
                print(f"   Producto/Post ({len(keywords['producto_o_post'])}): {[kw['term'] for kw in keywords['producto_o_post'][:3]]}")
                print(f"   Generales SEO ({len(keywords['generales_seo'])}): {[kw['term'] for kw in keywords['generales_seo'][:3]]}")
                
                return True
            else:
                print(f"❌ Error en análisis de URL: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error en análisis de URL: {e}")
            return False

async def test_domain_analysis():
    """Prueba el análisis completo de un dominio."""
    print("\n🔍 Probando análisis de dominio...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Dominio de ejemplo (usar un dominio real para pruebas)
    test_domain = "https://example.com"
    
    payload = {
        "domain": test_domain,
        "max_urls": 5,  # Limitar para pruebas rápidas
        "timeout": 15
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/analyze-domain",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                resumen = data['resumen']
                
                print(f"✅ Análisis de dominio completado:")
                print(f"   Dominio: {data['domain']}")
                print(f"   URLs procesadas: {resumen['total_urls']}")
                print(f"   Por tipo: {resumen['por_tipo']}")
                
                # Mostrar top keywords globales
                print(f"\n📊 Top keywords del dominio:")
                print(f"   Cliente: {[kw['term'] for kw in resumen['top_keywords_cliente'][:3]]}")
                print(f"   Producto: {[kw['term'] for kw in resumen['top_keywords_producto'][:3]]}")
                print(f"   Generales: {[kw['term'] for kw in resumen['top_keywords_generales'][:3]]}")
                
                return True
            else:
                print(f"❌ Error en análisis de dominio: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error en análisis de dominio: {e}")
            return False

async def main():
    """Función principal de demostración."""
    print("🚀 Demostración del Sistema de Análisis SEO de Dominios")
    print("=" * 60)
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"🔑 API Key: {API_KEY[:10]}...")
    print()
    
    # Ejecutar pruebas
    tests = [
        ("Health Check", test_health_check),
        ("Scoring Weights", test_scoring_weights),
        ("URL Analysis", test_url_analysis),
        ("Domain Analysis", test_domain_analysis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎉 ¡Todas las pruebas pasaron! El sistema está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores anteriores.")
    
    print("\n📝 Para más información:")
    print(f"   📖 Documentación: {API_BASE_URL}/docs")
    print(f"   🔧 ReDoc: {API_BASE_URL}/redoc")

if __name__ == "__main__":
    print("⚠️  NOTA: Asegúrate de que el servidor esté ejecutándose:")
    print("   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload")
    print()
    
    asyncio.run(main())


#!/usr/bin/env python3
"""
Debug específico del endpoint de la API
"""

import asyncio
import httpx
import json

async def debug_api_endpoint():
    """Debug del endpoint de la API."""
    
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
    
    print("DEBUG DEL ENDPOINT DE LA API")
    print("=" * 40)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print("Enviando request...")
            response = await client.post(
                f"{API_BASE_URL}/analyze-url",
                headers=headers,
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                
                print("\nRESPUESTA COMPLETA:")
                try:
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except UnicodeEncodeError:
                    print("Respuesta contiene caracteres especiales, guardando en archivo...")
                    with open('api_response_debug.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print("Respuesta guardada en: api_response_debug.json")
                
                # Verificar específicamente las keywords
                keywords = data.get('keywords', {})
                print(f"\nKEYWORDS DEBUG:")
                print(f"  Tipo: {type(keywords)}")
                print(f"  Claves: {list(keywords.keys()) if isinstance(keywords, dict) else 'No es dict'}")
                
                for bucket_name, bucket_keywords in keywords.items():
                    print(f"  {bucket_name}: {len(bucket_keywords)} keywords")
                    if bucket_keywords:
                        print(f"    Ejemplo: {bucket_keywords[0]}")
                
            else:
                print(f"Error: {response.status_code}")
                print(f"Respuesta: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

async def main():
    await debug_api_endpoint()

if __name__ == "__main__":
    asyncio.run(main())

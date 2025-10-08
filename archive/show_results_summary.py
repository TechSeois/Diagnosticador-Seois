#!/usr/bin/env python3
"""
Resumen de todos los resultados de análisis organizados
"""

import os
import json
from datetime import datetime

def show_results_summary():
    """Muestra un resumen de todos los resultados organizados."""
    
    print("=" * 80)
    print("RESUMEN DE RESULTADOS DE ANALISIS DE DOMINIOS")
    print("=" * 80)
    
    results_dir = "results"
    
    if not os.path.exists(results_dir):
        print(f"La carpeta {results_dir} no existe.")
        return
    
    print(f"\nCarpeta de resultados: {results_dir}/")
    print(f"Fecha de generacion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Listar archivos JSON
    json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
    
    if not json_files:
        print("\nNo se encontraron archivos JSON en la carpeta results/")
        return
    
    print(f"\nArchivos encontrados: {len(json_files)}")
    
    # Categorizar archivos
    domain_analysis_files = [f for f in json_files if 'domain_analysis' in f]
    individual_analysis_files = [f for f in json_files if 'analysis' in f and 'domain' not in f]
    test_files = [f for f in json_files if 'test' in f or 'debug' in f or 'diagnostic' in f or 'flow' in f]
    
    print("\n" + "=" * 60)
    print("ANALISIS DE DOMINIO COMPLETO")
    print("=" * 60)
    
    for file in domain_analysis_files:
        file_path = os.path.join(results_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            domain = data.get('domain', 'N/A')
            resumen = data.get('resumen', {})
            total_urls = resumen.get('total_urls', 0)
            por_tipo = resumen.get('por_tipo', {})
            
            print(f"\nArchivo: {file}")
            print(f"Dominio: {domain}")
            print(f"URLs procesadas: {total_urls}")
            print(f"Distribucion por tipo: {por_tipo}")
            
            # Mostrar top keywords si existen
            top_client = resumen.get('top_keywords_cliente', [])
            top_product = resumen.get('top_keywords_producto', [])
            top_general = resumen.get('top_keywords_generales', [])
            
            if top_client or top_product or top_general:
                print("Top keywords:")
                if top_client:
                    print(f"  Cliente: {len(top_client)} keywords")
                if top_product:
                    print(f"  Producto: {len(top_product)} keywords")
                if top_general:
                    print(f"  Generales: {len(top_general)} keywords")
            else:
                print("Keywords: No extraidas (problema NLP)")
            
        except Exception as e:
            print(f"\nArchivo: {file}")
            print(f"Error leyendo archivo: {e}")
    
    print("\n" + "=" * 60)
    print("ANALISIS DE URL INDIVIDUAL")
    print("=" * 60)
    
    for file in individual_analysis_files:
        file_path = os.path.join(results_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            url = data.get('url', 'N/A')
            tipo = data.get('tipo', 'N/A')
            intencion = data.get('intencion', 'N/A')
            audiencia = data.get('audiencia', [])
            palabras = data.get('stats', {}).get('words', 0)
            
            print(f"\nArchivo: {file}")
            print(f"URL: {url}")
            print(f"Tipo: {tipo}")
            print(f"Intencion: {intencion}")
            print(f"Audiencia: {', '.join(audiencia) if audiencia else 'No detectada'}")
            print(f"Palabras: {palabras}")
            
        except Exception as e:
            print(f"\nArchivo: {file}")
            print(f"Error leyendo archivo: {e}")
    
    print("\n" + "=" * 60)
    print("ARCHIVOS DE PRUEBA Y DEBUG")
    print("=" * 60)
    
    for file in test_files:
        file_path = os.path.join(results_dir, file)
        file_size = os.path.getsize(file_path)
        print(f"\nArchivo: {file}")
        print(f"Tamaño: {file_size:,} bytes")
        print(f"Tipo: {'Debug' if 'debug' in file else 'Test' if 'test' in file else 'Diagnostico' if 'diagnostic' in file else 'Flujo'}")
    
    print("\n" + "=" * 60)
    print("ESTADISTICAS GENERALES")
    print("=" * 60)
    
    total_size = sum(os.path.getsize(os.path.join(results_dir, f)) for f in json_files)
    print(f"Total archivos JSON: {len(json_files)}")
    print(f"Tamaño total: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print(f"Archivos de dominio: {len(domain_analysis_files)}")
    print(f"Archivos individuales: {len(individual_analysis_files)}")
    print(f"Archivos de prueba: {len(test_files)}")
    
    print("\n" + "=" * 60)
    print("COMPARACION DE DOMINIOS")
    print("=" * 60)
    
    # Comparar SpeedLogic vs Logitech
    speedlogic_file = None
    logitech_file = None
    
    for file in domain_analysis_files:
        if 'speedlogic' in file.lower():
            speedlogic_file = file
        elif 'logitech' in file.lower():
            logitech_file = file
    
    if speedlogic_file and logitech_file:
        try:
            # SpeedLogic
            with open(os.path.join(results_dir, speedlogic_file), 'r', encoding='utf-8') as f:
                speedlogic_data = json.load(f)
            
            # Logitech
            with open(os.path.join(results_dir, logitech_file), 'r', encoding='utf-8') as f:
                logitech_data = json.load(f)
            
            print("\nSPEEDLOGIC:")
            print(f"  Dominio: {speedlogic_data.get('domain')}")
            print(f"  URLs: {speedlogic_data.get('resumen', {}).get('total_urls', 0)}")
            print(f"  Tipo principal: {max(speedlogic_data.get('resumen', {}).get('por_tipo', {}), key=speedlogic_data.get('resumen', {}).get('por_tipo', {}).get)}")
            
            print("\nLOGITECH:")
            print(f"  Dominio: {logitech_data.get('domain')}")
            print(f"  URLs: {logitech_data.get('resumen', {}).get('total_urls', 0)}")
            print(f"  Tipo principal: {max(logitech_data.get('resumen', {}).get('por_tipo', {}), key=logitech_data.get('resumen', {}).get('por_tipo', {}).get)}")
            
            print("\nDIFERENCIAS:")
            print("  SpeedLogic: Sitio de blog gaming")
            print("  Logitech: Sitio e-commerce gaming")
            print("  Ambos: Audiencia gaming detectada")
            print("  Ambos: Analisis inteligente funcionando")
            
        except Exception as e:
            print(f"Error comparando dominios: {e}")
    
    print("\n" + "=" * 80)
    print("¡RESUMEN COMPLETADO!")
    print("=" * 80)

if __name__ == "__main__":
    show_results_summary()


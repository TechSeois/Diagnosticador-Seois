#!/usr/bin/env python3
"""
Script de inicio rápido para el Sistema de Análisis SEO de Dominios.
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Verifica que las dependencias estén instaladas."""
    print("🔍 Verificando dependencias...")
    
    try:
        import fastapi
        import uvicorn
        import httpx
        import pydantic
        import selectolax
        import yake
        import keybert
        import sentence_transformers
        import sklearn
        import nltk
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("💡 Ejecuta: pip install -r requirements.txt")
        return False

def setup_environment():
    """Configura el entorno de desarrollo."""
    print("🔧 Configurando entorno...")
    
    # Crear archivo .env si no existe
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path("env.example")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            print("✅ Archivo .env creado desde env.example")
        else:
            print("⚠️  Archivo env.example no encontrado")
    
    # Descargar datos de NLTK
    try:
        import nltk
        nltk.download('stopwords', quiet=True)
        print("✅ Datos de NLTK descargados")
    except Exception as e:
        print(f"⚠️  Error descargando datos NLTK: {e}")

def start_server():
    """Inicia el servidor de desarrollo."""
    print("🚀 Iniciando servidor de desarrollo...")
    print("📝 El servidor estará disponible en: http://localhost:8080")
    print("📖 Documentación: http://localhost:8080/docs")
    print("🔧 ReDoc: http://localhost:8080/redoc")
    print("\n⏹️  Presiona Ctrl+C para detener el servidor")
    print("-" * 60)
    
    try:
        # Ejecutar uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8080", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")

def run_tests():
    """Ejecuta las pruebas del sistema."""
    print("🧪 Ejecutando pruebas del sistema...")
    
    try:
        result = subprocess.run([sys.executable, "test_system.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Pruebas completadas exitosamente")
            print(result.stdout)
        else:
            print("❌ Algunas pruebas fallaron")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")

def run_example():
    """Ejecuta el ejemplo de uso."""
    print("📚 Ejecutando ejemplo de uso...")
    
    try:
        subprocess.run([sys.executable, "example_usage.py"])
    except Exception as e:
        print(f"❌ Error ejecutando ejemplo: {e}")

def show_menu():
    """Muestra el menú principal."""
    while True:
        print("\n" + "=" * 60)
        print("🎯 SISTEMA DE ANÁLISIS SEO DE DOMINIOS")
        print("=" * 60)
        print("1. 🚀 Iniciar servidor de desarrollo")
        print("2. 🧪 Ejecutar pruebas del sistema")
        print("3. 📚 Ejecutar ejemplo de uso")
        print("4. 🔧 Configurar entorno")
        print("5. 📖 Abrir documentación (requiere servidor)")
        print("6. 🐳 Iniciar con Docker")
        print("7. ❌ Salir")
        print("-" * 60)
        
        choice = input("Selecciona una opción (1-7): ").strip()
        
        if choice == "1":
            start_server()
        elif choice == "2":
            run_tests()
        elif choice == "3":
            run_example()
        elif choice == "4":
            setup_environment()
        elif choice == "5":
            try:
                webbrowser.open("http://localhost:8080/docs")
                print("🌐 Abriendo documentación en el navegador...")
            except Exception as e:
                print(f"❌ Error abriendo navegador: {e}")
        elif choice == "6":
            print("🐳 Iniciando con Docker...")
            try:
                subprocess.run(["docker-compose", "up", "-d"])
                print("✅ Servidor iniciado con Docker")
                print("📝 Disponible en: http://localhost:8080")
            except Exception as e:
                print(f"❌ Error con Docker: {e}")
        elif choice == "7":
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

def main():
    """Función principal."""
    print("🎉 ¡Bienvenido al Sistema de Análisis SEO de Dominios!")
    print("📋 Este script te ayudará a configurar y ejecutar el sistema")
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n💡 Para instalar dependencias:")
        print("   pip install -r requirements.txt")
        return
    
    # Configurar entorno
    setup_environment()
    
    # Mostrar menú
    show_menu()

if __name__ == "__main__":
    main()


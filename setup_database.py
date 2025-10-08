"""
Script de instalación y configuración para la base de datos N8NMC
Instala dependencias y configura la conexión a Supabase
"""
import subprocess
import sys
import os

def install_dependencies():
    """Instala las dependencias necesarias"""
    print("Instalando dependencias...")
    
    dependencies = [
        "psycopg2-binary",
        "python-dotenv"
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"OK {dep} instalado")
        except subprocess.CalledProcessError:
            print(f"Error instalando {dep}")
            return False
    
    return True

def create_env_file():
    """Crea archivo .env con configuración de ejemplo"""
    env_content = """# Configuración de Base de Datos Supabase
# Reemplaza 'tu_password_aqui' con tu contraseña real de Supabase

SUPABASE_HOST=db.umqgbhmhweqqmatrgpqr.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=tu_password_aqui

# Configuración de la aplicación
RESULTS_DIR=results
SCHEMA_FILE=database_schema.sql

# Configuración de logging
LOG_LEVEL=INFO
LOG_FILE=database_load.log
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("OK Archivo .env creado")
        print("IMPORTANTE: Edita .env y agrega tu contraseña de Supabase")
    else:
        print("Archivo .env ya existe")

def test_connection():
    """Prueba la conexión a la base de datos"""
    print("\nProbando conexión a Supabase...")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        conn_params = {
            'host': os.getenv('SUPABASE_HOST'),
            'port': os.getenv('SUPABASE_PORT'),
            'database': os.getenv('SUPABASE_DATABASE'),
            'user': os.getenv('SUPABASE_USER'),
            'password': os.getenv('SUPABASE_PASSWORD')
        }
        
        if conn_params['password'] == 'tu_password_aqui':
            print("Configura tu contraseña en el archivo .env antes de probar la conexión")
            return False
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"OK Conexión exitosa a PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False

def main():
    """Función principal de instalación"""
    print("INSTALACIÓN DE BASE DE DATOS N8NMC")
    print("=" * 50)
    
    # Instalar dependencias
    if not install_dependencies():
        print("Error instalando dependencias")
        return
    
    # Crear archivo de configuración
    create_env_file()
    
    # Probar conexión
    if test_connection():
        print("\nInstalación completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. Configura tu contraseña en el archivo .env")
        print("2. Ejecuta: python load_data_to_db.py")
        print("3. Ejecuta: python database_queries.py")
    else:
        print("\nInstalación completada, pero configura la conexión")
        print("1. Edita el archivo .env con tu contraseña de Supabase")
        print("2. Ejecuta: python load_data_to_db.py")

if __name__ == "__main__":
    main()

"""
Script simple para configurar y crear tablas en Supabase
"""
import psycopg2
import os

def get_password():
    """Solicita la contraseña de Supabase al usuario"""
    print("CONFIGURACION DE SUPABASE")
    print("=" * 40)
    print("Necesitas tu contraseña de Supabase para crear las tablas.")
    print("Puedes encontrarla en:")
    print("1. Ve a tu proyecto en Supabase")
    print("2. Settings > Database")
    print("3. Connection string o Database password")
    print()
    
    password = input("Ingresa tu contraseña de Supabase: ").strip()
    
    if not password:
        print("Error: Debes ingresar una contraseña")
        return None
    
    # Guardar en archivo .env
    env_content = f"""# Configuración de Base de Datos Supabase
SUPABASE_HOST=db.umqgbhmhweqqmatrgpqr.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD={password}

# Configuración de la aplicación
RESULTS_DIR=results
SCHEMA_FILE=database_schema.sql
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("OK Contraseña guardada en archivo .env")
    return password

def test_connection(password):
    """Prueba la conexión con la contraseña proporcionada"""
    try:
        conn = psycopg2.connect(
            host='db.umqgbhmhweqqmatrgpqr.supabase.co',
            port=5432,
            database='postgres',
            user='postgres',
            password=password
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"OK Conexion exitosa: {version[0][:50]}...")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error de conexion: {e}")
        return False

def create_tables(password):
    """Crea las tablas en Supabase"""
    try:
        conn = psycopg2.connect(
            host='db.umqgbhmhweqqmatrgpqr.supabase.co',
            port=5432,
            database='postgres',
            user='postgres',
            password=password
        )
        cursor = conn.cursor()
        
        print("Creando tablas...")
        
        # Leer esquema SQL
        with open('database_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Ejecutar esquema
        cursor.execute(schema_sql)
        conn.commit()
        
        print("OK Esquema ejecutado exitosamente")
        
        # Verificar tablas creadas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print("\nTablas creadas:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\nBase de datos lista para usar!")
        return True
        
    except Exception as e:
        print(f"Error creando tablas: {e}")
        return False

def main():
    """Función principal"""
    print("CREACION DE TABLAS EN SUPABASE")
    print("=" * 50)
    
    # Obtener contraseña
    password = get_password()
    if not password:
        return
    
    # Probar conexión
    print("\nProbando conexion...")
    if not test_connection(password):
        print("No se pudo conectar. Verifica tu contraseña.")
        return
    
    # Crear tablas
    print("\nCreando tablas...")
    if create_tables(password):
        print("\nProceso completado exitosamente!")
        print("\nAhora puedes:")
        print("1. Ejecutar: python load_data_to_db.py")
        print("2. Ejecutar: python database_queries.py")
    else:
        print("\nError creando las tablas")

if __name__ == "__main__":
    main()


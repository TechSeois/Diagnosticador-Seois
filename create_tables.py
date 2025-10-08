"""
Script para crear las tablas en Supabase PostgreSQL
Ejecuta el esquema de base de datos directamente
"""
import psycopg2
import os
from dotenv import load_dotenv

def create_tables_in_supabase():
    """Crea las tablas en Supabase ejecutando el esquema SQL"""
    
    # Cargar configuración desde .env
    load_dotenv()
    
    # Configuración de conexión
    conn_params = {
        'host': os.getenv('SUPABASE_HOST', 'db.umqgbhmhweqqmatrgpqr.supabase.co'),
        'port': os.getenv('SUPABASE_PORT', 5432),
        'database': os.getenv('SUPABASE_DATABASE', 'postgres'),
        'user': os.getenv('SUPABASE_USER', 'postgres'),
        'password': os.getenv('SUPABASE_PASSWORD')
    }
    
    if not conn_params['password'] or conn_params['password'] == 'tu_password_aqui':
        print("Error: Configura tu contraseña de Supabase en el archivo .env")
        print("Edita el archivo .env y reemplaza 'tu_password_aqui' con tu contraseña real")
        return False
    
    try:
        print("Conectando a Supabase...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        print("Conexion establecida exitosamente")
        
        # Leer el esquema SQL
        print("Leyendo esquema de base de datos...")
        with open('database_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        print("Creando tablas y esquema...")
        
        # Dividir el SQL en statements individuales
        statements = schema_sql.split(';')
        
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    print(f"   Ejecutando statement {i+1}/{len(statements)}...")
                    cursor.execute(statement)
                    print(f"   OK Statement {i+1} ejecutado")
                except psycopg2.Error as e:
                    if "already exists" in str(e).lower():
                        print(f"   Statement {i+1} ya existe (saltando)")
                    else:
                        print(f"   Error en statement {i+1}: {e}")
                        print(f"   SQL: {statement[:100]}...")
        
        # Confirmar cambios
        conn.commit()
        print("Esquema creado exitosamente")
        
        # Verificar que las tablas se crearon
        print("\nVerificando tablas creadas...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print("Tablas creadas:")
        for table in tables:
            print(f"   OK {table[0]}")
        
        # Verificar vistas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        views = cursor.fetchall()
        if views:
            print("\nVistas creadas:")
            for view in views:
                print(f"   OK {view[0]}")
        
        cursor.close()
        conn.close()
        
        print("\nBase de datos creada exitosamente en Supabase!")
        print("\nProximos pasos:")
        print("1. Ejecuta: python load_data_to_db.py")
        print("2. Ejecuta: python database_queries.py")
        
        return True
        
    except psycopg2.Error as e:
        print(f"Error de base de datos: {e}")
        return False
    except FileNotFoundError:
        print("Error: No se encontro el archivo database_schema.sql")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def test_connection():
    """Prueba la conexión a Supabase"""
    load_dotenv()
    
    conn_params = {
        'host': os.getenv('SUPABASE_HOST', 'db.umqgbhmhweqqmatrgpqr.supabase.co'),
        'port': os.getenv('SUPABASE_PORT', 5432),
        'database': os.getenv('SUPABASE_DATABASE', 'postgres'),
        'user': os.getenv('SUPABASE_USER', 'postgres'),
        'password': os.getenv('SUPABASE_PASSWORD')
    }
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Conexion exitosa: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error de conexion: {e}")
        return False

def main():
    """Función principal"""
    print("CREANDO TABLAS EN SUPABASE")
    print("=" * 50)
    
    # Probar conexión primero
    print("Probando conexion...")
    if not test_connection():
        print("\nNo se pudo conectar a Supabase")
        print("Verifica tu contraseña en el archivo .env")
        return
    
    # Crear tablas
    if create_tables_in_supabase():
        print("\nProceso completado exitosamente!")
    else:
        print("\nError creando las tablas")

if __name__ == "__main__":
    main()

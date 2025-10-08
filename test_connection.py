"""
Script simple para probar la conexión a Supabase
"""
import psycopg2
import os

def test_supabase_connection():
    """Prueba la conexión básica a Supabase"""
    
    # Configuración
    host = 'db.umqgbhmhweqqmatrgpqr.supabase.co'
    port = 5432
    database = 'postgres'
    user = 'postgres'
    
    # Obtener contraseña de variable de entorno
    password = os.getenv('SUPABASE_PASSWORD')
    
    if not password:
        print("ERROR: No se encontro SUPABASE_PASSWORD")
        print("Configura la variable de entorno:")
        print("set SUPABASE_PASSWORD=tu_password_aqui")
        return False
    
    try:
        print("Probando conexion a Supabase...")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"Database: {database}")
        print(f"User: {user}")
        print(f"Password: {'*' * len(password)}")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"OK Conexion exitosa!")
        print(f"PostgreSQL: {version[0][:50]}...")
        
        # Probar una consulta simple
        cursor.execute("SELECT current_database(), current_user;")
        db_info = cursor.fetchone()
        print(f"Database actual: {db_info[0]}")
        print(f"Usuario actual: {db_info[1]}")
        
        cursor.close()
        conn.close()
        
        print("Conexion funcionando correctamente!")
        return True
        
    except psycopg2.Error as e:
        print(f"Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def main():
    print("PRUEBA DE CONEXION A SUPABASE")
    print("=" * 40)
    
    if test_supabase_connection():
        print("\nLa conexion funciona! Ahora puedes:")
        print("1. Ejecutar: python create_tables_env.py")
        print("2. Ejecutar: python load_data_to_db.py")
    else:
        print("\nError en la conexion. Verifica:")
        print("1. Tu contraseña de Supabase")
        print("2. Tu conexion a internet")
        print("3. Que el proyecto de Supabase este activo")

if __name__ == "__main__":
    main()


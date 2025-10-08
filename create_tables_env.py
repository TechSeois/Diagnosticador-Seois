"""
Script para crear tablas en Supabase usando variables de entorno
"""
import psycopg2
import os

def create_tables_with_env():
    """Crea las tablas usando variables de entorno"""
    
    # Configuración desde variables de entorno
    host = os.getenv('SUPABASE_HOST', 'db.umqgbhmhweqqmatrgpqr.supabase.co')
    port = int(os.getenv('SUPABASE_PORT', 5432))
    database = os.getenv('SUPABASE_DATABASE', 'postgres')
    user = os.getenv('SUPABASE_USER', 'postgres')
    password = os.getenv('SUPABASE_PASSWORD')
    
    if not password:
        print("ERROR: No se encontro SUPABASE_PASSWORD en variables de entorno")
        print("Configura la variable de entorno:")
        print("set SUPABASE_PASSWORD=tu_password_aqui")
        return False
    
    try:
        print("Conectando a Supabase...")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"Database: {database}")
        print(f"User: {user}")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        
        print("OK Conexion establecida")
        
        # Probar conexión
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL version: {version[0][:50]}...")
        
        # Leer esquema SQL
        print("Leyendo esquema de base de datos...")
        with open('database_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        print("Ejecutando esquema SQL...")
        
        # Dividir en statements y ejecutar uno por uno
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement and not statement.startswith('--'):
                try:
                    print(f"Ejecutando statement {i+1}/{len(statements)}...")
                    cursor.execute(statement)
                    print(f"OK Statement {i+1} ejecutado")
                except psycopg2.Error as e:
                    if "already exists" in str(e).lower():
                        print(f"Statement {i+1} ya existe (saltando)")
                    else:
                        print(f"Error en statement {i+1}: {e}")
                        print(f"SQL: {statement[:100]}...")
        
        # Confirmar cambios
        conn.commit()
        print("OK Esquema ejecutado exitosamente")
        
        # Verificar tablas creadas
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
            print(f"  - {table[0]}")
        
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
                print(f"  - {view[0]}")
        
        cursor.close()
        conn.close()
        
        print("\nBase de datos creada exitosamente!")
        return True
        
    except psycopg2.Error as e:
        print(f"Error de PostgreSQL: {e}")
        return False
    except FileNotFoundError:
        print("Error: No se encontro database_schema.sql")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def main():
    """Función principal"""
    print("CREACION DE TABLAS EN SUPABASE")
    print("=" * 50)
    
    if create_tables_with_env():
        print("\nProceso completado exitosamente!")
        print("\nAhora puedes:")
        print("1. Ejecutar: python load_data_to_db.py")
        print("2. Ejecutar: python database_queries.py")
    else:
        print("\nError en el proceso")
        print("\nPara configurar la contraseña:")
        print("set SUPABASE_PASSWORD=tu_password_de_supabase")

if __name__ == "__main__":
    main()


"""
Script de consultas útiles para la base de datos N8NMC
Incluye queries para análisis, reportes y estadísticas
"""
import psycopg2
import json
from typing import List, Dict, Any
import os

class DatabaseQueries:
    """Clase para ejecutar consultas útiles en la base de datos"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str = None):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password or os.getenv('SUPABASE_PASSWORD')
        }
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establece conexión con la base de datos"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor()
            print("✅ Conexión establecida")
        except Exception as e:
            print(f"❌ Error conectando: {e}")
            raise
    
    def disconnect(self):
        """Cierra la conexión"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def get_domains_summary(self) -> List[Dict]:
        """Obtiene resumen de todos los dominios"""
        query = """
        SELECT 
            d.domain_name,
            d.sector,
            COUNT(da.id) as total_analyses,
            MAX(da.analysis_date) as last_analysis,
            SUM(da.total_urls) as total_urls,
            SUM(da.urls_processed) as urls_processed,
            AVG(da.processing_time_seconds) as avg_processing_time
        FROM domains d
        LEFT JOIN domain_analyses da ON d.id = da.domain_id
        GROUP BY d.id, d.domain_name, d.sector
        ORDER BY d.domain_name
        """
        
        self.cursor.execute(query)
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_top_keywords_by_domain(self, domain_name: str = None, limit: int = 20) -> List[Dict]:
        """Obtiene top keywords por dominio"""
        if domain_name:
            query = """
            SELECT 
                d.domain_name,
                d.sector,
                k.keyword,
                k.bucket,
                AVG(k.score) as avg_score,
                COUNT(k.id) as frequency,
                COUNT(DISTINCT au.id) as url_count
            FROM domains d
            JOIN domain_analyses da ON d.id = da.domain_id
            JOIN analyzed_urls au ON da.id = au.domain_analysis_id
            JOIN keywords k ON au.id = k.url_id
            WHERE d.domain_name = %s
            GROUP BY d.domain_name, d.sector, k.keyword, k.bucket
            ORDER BY avg_score DESC
            LIMIT %s
            """
            self.cursor.execute(query, (domain_name, limit))
        else:
            query = """
            SELECT 
                d.domain_name,
                d.sector,
                k.keyword,
                k.bucket,
                AVG(k.score) as avg_score,
                COUNT(k.id) as frequency,
                COUNT(DISTINCT au.id) as url_count
            FROM domains d
            JOIN domain_analyses da ON d.id = da.domain_id
            JOIN analyzed_urls au ON da.id = au.domain_analysis_id
            JOIN keywords k ON au.id = k.url_id
            GROUP BY d.domain_name, d.sector, k.keyword, k.bucket
            ORDER BY avg_score DESC
            LIMIT %s
            """
            self.cursor.execute(query, (limit,))
        
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_sector_analysis(self) -> List[Dict]:
        """Análisis por sector"""
        query = """
        SELECT 
            d.sector,
            COUNT(DISTINCT d.id) as total_domains,
            COUNT(DISTINCT da.id) as total_analyses,
            SUM(da.total_urls) as total_urls,
            SUM(da.urls_processed) as urls_processed,
            AVG(da.processing_time_seconds) as avg_processing_time,
            COUNT(DISTINCT au.id) as unique_urls,
            COUNT(k.id) as total_keywords,
            AVG(k.score) as avg_keyword_score
        FROM domains d
        LEFT JOIN domain_analyses da ON d.id = da.domain_id
        LEFT JOIN analyzed_urls au ON da.id = au.domain_analysis_id
        LEFT JOIN keywords k ON au.id = k.url_id
        GROUP BY d.sector
        ORDER BY total_domains DESC
        """
        
        self.cursor.execute(query)
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_bucket_distribution(self, domain_name: str = None) -> List[Dict]:
        """Distribución de keywords por bucket"""
        if domain_name:
            query = """
            SELECT 
                d.domain_name,
                k.bucket,
                COUNT(k.id) as keyword_count,
                AVG(k.score) as avg_score,
                MAX(k.score) as max_score,
                MIN(k.score) as min_score
            FROM domains d
            JOIN domain_analyses da ON d.id = da.domain_id
            JOIN analyzed_urls au ON da.id = au.domain_analysis_id
            JOIN keywords k ON au.id = k.url_id
            WHERE d.domain_name = %s
            GROUP BY d.domain_name, k.bucket
            ORDER BY keyword_count DESC
            """
            self.cursor.execute(query, (domain_name,))
        else:
            query = """
            SELECT 
                k.bucket,
                COUNT(k.id) as keyword_count,
                AVG(k.score) as avg_score,
                MAX(k.score) as max_score,
                MIN(k.score) as min_score,
                COUNT(DISTINCT d.domain_name) as domains_count
            FROM domains d
            JOIN domain_analyses da ON d.id = da.domain_id
            JOIN analyzed_urls au ON da.id = au.domain_analysis_id
            JOIN keywords k ON au.id = k.url_id
            GROUP BY k.bucket
            ORDER BY keyword_count DESC
            """
            self.cursor.execute(query)
        
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_audience_analysis(self) -> List[Dict]:
        """Análisis de audiencias"""
        query = """
        SELECT 
            d.domain_name,
            d.sector,
            au.audiences,
            COUNT(au.id) as url_count,
            AVG(au.word_count) as avg_word_count,
            AVG(au.processing_time_seconds) as avg_processing_time
        FROM domains d
        JOIN domain_analyses da ON d.id = da.domain_id
        JOIN analyzed_urls au ON da.id = au.domain_analysis_id
        GROUP BY d.domain_name, d.sector, au.audiences
        ORDER BY url_count DESC
        """
        
        self.cursor.execute(query)
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_intent_analysis(self) -> List[Dict]:
        """Análisis de intenciones"""
        query = """
        SELECT 
            d.domain_name,
            d.sector,
            au.intent,
            COUNT(au.id) as url_count,
            AVG(au.word_count) as avg_word_count,
            AVG(au.processing_time_seconds) as avg_processing_time
        FROM domains d
        JOIN domain_analyses da ON d.id = da.domain_id
        JOIN analyzed_urls au ON da.id = au.domain_analysis_id
        GROUP BY d.domain_name, d.sector, au.intent
        ORDER BY url_count DESC
        """
        
        self.cursor.execute(query)
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
    
    def get_performance_metrics(self) -> List[Dict]:
        """Métricas de rendimiento"""
        query = """
        SELECT 
            d.domain_name,
            d.sector,
            COUNT(da.id) as total_analyses,
            AVG(da.processing_time_seconds) as avg_processing_time,
            AVG(da.urls_processed::float / da.total_urls * 100) as success_rate,
            AVG(au.word_count) as avg_word_count,
            AVG(au.processing_time_seconds) as avg_url_processing_time,
            COUNT(k.id) as total_keywords,
            AVG(k.score) as avg_keyword_score
        FROM domains d
        JOIN domain_analyses da ON d.id = da.domain_id
        JOIN analyzed_urls au ON da.id = au.domain_analysis_id
        JOIN keywords k ON au.id = k.url_id
        GROUP BY d.domain_name, d.sector
        ORDER BY avg_processing_time DESC
        """
        
        self.cursor.execute(query)
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
    
    def search_keywords(self, keyword_pattern: str, limit: int = 50) -> List[Dict]:
        """Busca keywords por patrón"""
        query = """
        SELECT 
            d.domain_name,
            d.sector,
            k.keyword,
            k.bucket,
            k.score,
            au.url,
            au.page_type,
            au.intent
        FROM domains d
        JOIN domain_analyses da ON d.id = da.domain_id
        JOIN analyzed_urls au ON da.id = au.domain_analysis_id
        JOIN keywords k ON au.id = k.url_id
        WHERE k.keyword ILIKE %s
        ORDER BY k.score DESC
        LIMIT %s
        """
        
        self.cursor.execute(query, (f'%{keyword_pattern}%', limit))
        columns = [desc[0] for desc in self.cursor.description]
        results = self.cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in results]
    
    def export_domain_data(self, domain_name: str) -> Dict:
        """Exporta todos los datos de un dominio"""
        # Obtener datos del dominio
        domain_query = """
        SELECT * FROM domains WHERE domain_name = %s
        """
        self.cursor.execute(domain_query, (domain_name,))
        domain_data = self.cursor.fetchone()
        
        if not domain_data:
            return None
        
        # Obtener análisis del dominio
        analysis_query = """
        SELECT * FROM domain_analyses WHERE domain_id = %s
        """
        self.cursor.execute(analysis_query, (domain_data[0],))
        analyses = self.cursor.fetchall()
        
        # Obtener URLs
        urls_query = """
        SELECT * FROM analyzed_urls WHERE domain_analysis_id = %s
        """
        urls_data = []
        for analysis in analyses:
            self.cursor.execute(urls_query, (analysis[0],))
            urls = self.cursor.fetchall()
            urls_data.extend(urls)
        
        # Obtener keywords
        keywords_query = """
        SELECT * FROM keywords WHERE url_id = %s
        """
        keywords_data = []
        for url in urls_data:
            self.cursor.execute(keywords_query, (url[0],))
            keywords = self.cursor.fetchall()
            keywords_data.extend(keywords)
        
        return {
            'domain': domain_data,
            'analyses': analyses,
            'urls': urls_data,
            'keywords': keywords_data
        }


def print_formatted_results(results: List[Dict], title: str):
    """Imprime resultados formateados"""
    print(f"\n📊 {title}")
    print("=" * 80)
    
    if not results:
        print("No hay datos disponibles")
        return
    
    # Obtener columnas
    columns = list(results[0].keys())
    
    # Imprimir encabezados
    header = " | ".join([col[:15].ljust(15) for col in columns])
    print(header)
    print("-" * len(header))
    
    # Imprimir datos
    for row in results:
        data_row = " | ".join([str(row[col])[:15].ljust(15) for col in columns])
        print(data_row)


def main():
    """Función principal para ejecutar consultas"""
    
    # Configuración de Supabase
    HOST = "db.umqgbhmhweqqmatrgpqr.supabase.co"
    PORT = 5432
    DATABASE = "postgres"
    USER = "postgres"
    
    queries = DatabaseQueries(HOST, PORT, DATABASE, USER)
    
    try:
        queries.connect()
        
        print("🔍 EJECUTANDO CONSULTAS DE ANÁLISIS")
        print("=" * 60)
        
        # Resumen de dominios
        domains = queries.get_domains_summary()
        print_formatted_results(domains, "RESUMEN DE DOMINIOS")
        
        # Análisis por sector
        sectors = queries.get_sector_analysis()
        print_formatted_results(sectors, "ANÁLISIS POR SECTOR")
        
        # Distribución por buckets
        buckets = queries.get_bucket_distribution()
        print_formatted_results(buckets, "DISTRIBUCIÓN POR BUCKETS")
        
        # Top keywords globales
        top_keywords = queries.get_top_keywords_by_domain(limit=20)
        print_formatted_results(top_keywords, "TOP KEYWORDS GLOBALES")
        
        # Métricas de rendimiento
        performance = queries.get_performance_metrics()
        print_formatted_results(performance, "MÉTRICAS DE RENDIMIENTO")
        
        # Análisis de audiencias
        audiences = queries.get_audience_analysis()
        print_formatted_results(audiences, "ANÁLISIS DE AUDIENCIAS")
        
        # Análisis de intenciones
        intents = queries.get_intent_analysis()
        print_formatted_results(intents, "ANÁLISIS DE INTENCIONES")
        
    except Exception as e:
        print(f"❌ Error ejecutando consultas: {e}")
    finally:
        queries.disconnect()


if __name__ == "__main__":
    main()


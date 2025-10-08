"""
Script para cargar datos de análisis JSON a PostgreSQL
Conecta con Supabase y carga los datos de manera estructurada
"""
import json
import psycopg2
import hashlib
from datetime import datetime
from typing import Dict, List, Any
import os

class DatabaseLoader:
    """Clase para cargar datos de análisis a PostgreSQL"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str = None):
        """
        Inicializa la conexión a la base de datos
        
        Args:
            host: Host de Supabase
            port: Puerto (5432)
            database: Nombre de la base de datos
            user: Usuario
            password: Contraseña (se puede pasar como variable de entorno)
        """
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
            print("✅ Conexión a la base de datos establecida")
        except Exception as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            raise
    
    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("🔌 Conexión cerrada")
    
    def create_schema(self, schema_file: str = "database_schema.sql"):
        """Crea el esquema de la base de datos"""
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            self.cursor.execute(schema_sql)
            self.conn.commit()
            print("✅ Esquema de base de datos creado exitosamente")
        except Exception as e:
            print(f"❌ Error creando esquema: {e}")
            self.conn.rollback()
            raise
    
    def load_domain_analysis(self, json_file: str):
        """
        Carga un análisis completo de dominio desde un archivo JSON
        
        Args:
            json_file: Ruta al archivo JSON con el análisis
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            domain_name = data['domain']
            analysis_data = data['resumen']
            urls_data = data['urls']
            
            print(f"\n📊 Cargando análisis de {domain_name}...")
            
            # 1. Insertar o obtener dominio
            domain_id = self._upsert_domain(domain_name, analysis_data)
            
            # 2. Insertar análisis del dominio
            analysis_id = self._insert_domain_analysis(domain_id, analysis_data, data)
            
            # 3. Insertar URLs analizadas
            url_ids = self._insert_analyzed_urls(analysis_id, urls_data)
            
            # 4. Insertar keywords
            self._insert_keywords(url_ids, urls_data)
            
            # 5. Insertar estadísticas del dominio
            self._insert_domain_stats(domain_id, analysis_data, urls_data)
            
            self.conn.commit()
            print(f"✅ Análisis de {domain_name} cargado exitosamente")
            
        except Exception as e:
            print(f"❌ Error cargando análisis: {e}")
            self.conn.rollback()
            raise
    
    def _upsert_domain(self, domain_name: str, analysis_data: Dict) -> int:
        """Inserta o actualiza un dominio y retorna su ID"""
        # Detectar sector basado en el análisis
        sector = self._detect_sector_from_analysis(analysis_data)
        
        # Intentar insertar
        try:
            self.cursor.execute("""
                INSERT INTO domains (domain_name, sector) 
                VALUES (%s, %s) 
                RETURNING id
            """, (domain_name, sector))
            domain_id = self.cursor.fetchone()[0]
            print(f"   📝 Dominio {domain_name} insertado (ID: {domain_id})")
        except psycopg2.IntegrityError:
            # Si ya existe, obtener el ID
            self.cursor.execute("""
                SELECT id FROM domains WHERE domain_name = %s
            """, (domain_name,))
            domain_id = self.cursor.fetchone()[0]
            print(f"   🔄 Dominio {domain_name} ya existe (ID: {domain_id})")
        
        return domain_id
    
    def _detect_sector_from_analysis(self, analysis_data: Dict) -> str:
        """Detecta el sector basado en el análisis"""
        # Analizar keywords para detectar sector
        keywords_client = analysis_data.get('top_keywords_cliente', [])
        keywords_text = ' '.join([kw['keyword'] for kw in keywords_client[:5]])
        
        # Patrones de detección de sector
        if any(word in keywords_text.lower() for word in ['abogado', 'legal', 'ley', 'derecho', 'jurídico', 'tribunal']):
            return 'legal'
        elif any(word in keywords_text.lower() for word in ['padel', 'court', 'club', 'deporte', 'sport']):
            return 'sports'
        elif any(word in keywords_text.lower() for word in ['case', 'setup', 'ensamble', 'modding', 'corsair', 'intel', 'nvidia']):
            return 'technology'
        else:
            return 'general'
    
    def _insert_domain_analysis(self, domain_id: int, analysis_data: Dict, full_data: Dict) -> int:
        """Inserta el análisis del dominio y retorna el ID"""
        self.cursor.execute("""
            INSERT INTO domain_analyses (
                domain_id, total_urls, urls_processed, processing_time_seconds,
                page_types, audiences, intents, top_keywords_client,
                top_keywords_product, top_keywords_general, summary_stats, raw_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            domain_id,
            analysis_data.get('total_urls', 0),
            analysis_data.get('urls_procesadas', 0),
            analysis_data.get('tiempo_total', 0),
            json.dumps(analysis_data.get('por_tipo', {})),
            json.dumps(analysis_data.get('por_audiencia', {})),
            json.dumps(analysis_data.get('por_intencion', {})),
            json.dumps(analysis_data.get('top_keywords_cliente', [])),
            json.dumps(analysis_data.get('top_keywords_producto_o_post', [])),
            json.dumps(analysis_data.get('top_keywords_generales_seo', [])),
            json.dumps(analysis_data.get('estadisticas', {})),
            json.dumps(full_data)
        ))
        
        analysis_id = self.cursor.fetchone()[0]
        print(f"   📊 Análisis insertado (ID: {analysis_id})")
        return analysis_id
    
    def _insert_analyzed_urls(self, analysis_id: int, urls_data: List[Dict]) -> Dict[str, int]:
        """Inserta las URLs analizadas y retorna mapeo URL -> ID"""
        url_ids = {}
        
        for url_data in urls_data:
            url = url_data['url']
            url_hash = hashlib.md5(url.encode()).hexdigest()
            
            self.cursor.execute("""
                INSERT INTO analyzed_urls (
                    domain_analysis_id, url, url_hash, page_type, audiences,
                    intent, word_count, heading_count, processing_time_seconds,
                    title, description, main_content
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (domain_analysis_id, url_hash) DO UPDATE SET
                    page_type = EXCLUDED.page_type,
                    audiences = EXCLUDED.audiences,
                    intent = EXCLUDED.intent,
                    word_count = EXCLUDED.word_count,
                    heading_count = EXCLUDED.heading_count,
                    processing_time_seconds = EXCLUDED.processing_time_seconds,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    main_content = EXCLUDED.main_content
                RETURNING id
            """, (
                analysis_id,
                url,
                url_hash,
                url_data.get('tipo'),
                url_data.get('audiencia', []),
                url_data.get('intencion'),
                url_data.get('palabras', 0),
                url_data.get('heading_count', 0),
                url_data.get('tiempo_procesamiento', 0),
                url_data.get('titulo', ''),
                url_data.get('descripcion', ''),
                url_data.get('contenido_principal', '')
            ))
            
            url_id = self.cursor.fetchone()[0]
            url_ids[url] = url_id
        
        print(f"   🔗 {len(url_ids)} URLs insertadas")
        return url_ids
    
    def _insert_keywords(self, url_ids: Dict[str, int], urls_data: List[Dict]):
        """Inserta las keywords extraídas"""
        total_keywords = 0
        
        for url_data in urls_data:
            url = url_data['url']
            url_id = url_ids[url]
            
            # Insertar keywords por bucket
            for bucket_name, keywords in url_data.get('keywords', {}).items():
                for i, kw_data in enumerate(keywords):
                    self.cursor.execute("""
                        INSERT INTO keywords (
                            url_id, keyword, score, bucket, source, position,
                            contextual_score, relevance_score, position_score,
                            frequency_score, sector_boost
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url_id, keyword, bucket) DO UPDATE SET
                            score = EXCLUDED.score,
                            position = EXCLUDED.position,
                            contextual_score = EXCLUDED.contextual_score,
                            relevance_score = EXCLUDED.relevance_score,
                            position_score = EXCLUDED.position_score,
                            frequency_score = EXCLUDED.frequency_score,
                            sector_boost = EXCLUDED.sector_boost
                    """, (
                        url_id,
                        kw_data['keyword'],
                        kw_data['score'],
                        bucket_name,
                        kw_data.get('source', 'unknown'),
                        i + 1,
                        kw_data.get('contextual_score', 0),
                        kw_data.get('relevance_score', 0),
                        kw_data.get('position_score', 0),
                        kw_data.get('frequency_score', 0),
                        kw_data.get('sector_boost', 0)
                    ))
                    total_keywords += 1
        
        print(f"   🔑 {total_keywords} keywords insertadas")
    
    def _insert_domain_stats(self, domain_id: int, analysis_data: Dict, urls_data: List[Dict]):
        """Inserta estadísticas agregadas del dominio"""
        # Calcular estadísticas
        total_keywords = sum(len(url.get('keywords', {}).get('cliente', [])) + 
                           len(url.get('keywords', {}).get('producto_o_post', [])) + 
                           len(url.get('keywords', {}).get('generales_seo', [])) 
                           for url in urls_data)
        
        avg_keywords_per_url = total_keywords / len(urls_data) if urls_data else 0
        
        # Distribución por buckets
        bucket_distribution = {
            'cliente': sum(len(url.get('keywords', {}).get('cliente', [])) for url in urls_data),
            'producto_o_post': sum(len(url.get('keywords', {}).get('producto_o_post', [])) for url in urls_data),
            'generales_seo': sum(len(url.get('keywords', {}).get('generales_seo', [])) for url in urls_data)
        }
        
        # Keywords específicas del sector
        sector_keywords = {}
        for bucket_name, keywords in analysis_data.get('top_keywords_cliente', {}).items():
            sector_keywords[bucket_name] = keywords[:10]  # Top 10
        
        # Métricas de rendimiento
        performance_metrics = {
            'avg_processing_time': analysis_data.get('tiempo_total', 0) / len(urls_data) if urls_data else 0,
            'success_rate': 100.0,  # Asumiendo que todas las URLs se procesaron
            'avg_word_count': sum(url.get('palabras', 0) for url in urls_data) / len(urls_data) if urls_data else 0
        }
        
        self.cursor.execute("""
            INSERT INTO domain_stats (
                domain_id, total_keywords, avg_keywords_per_url,
                bucket_distribution, sector_keywords, performance_metrics
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (domain_id, stat_date) DO UPDATE SET
                total_keywords = EXCLUDED.total_keywords,
                avg_keywords_per_url = EXCLUDED.avg_keywords_per_url,
                bucket_distribution = EXCLUDED.bucket_distribution,
                sector_keywords = EXCLUDED.sector_keywords,
                performance_metrics = EXCLUDED.performance_metrics
        """, (
            domain_id,
            total_keywords,
            avg_keywords_per_url,
            json.dumps(bucket_distribution),
            json.dumps(sector_keywords),
            json.dumps(performance_metrics)
        ))
        
        print(f"   📈 Estadísticas del dominio insertadas")
    
    def load_all_json_files(self, results_dir: str = "results"):
        """Carga todos los archivos JSON de la carpeta results"""
        import glob
        
        json_files = glob.glob(f"{results_dir}/*_domain_complete_test.json")
        
        if not json_files:
            print(f"❌ No se encontraron archivos JSON en {results_dir}")
            return
        
        print(f"📁 Encontrados {len(json_files)} archivos JSON:")
        for file in json_files:
            print(f"   - {file}")
        
        for json_file in json_files:
            try:
                self.load_domain_analysis(json_file)
            except Exception as e:
                print(f"❌ Error cargando {json_file}: {e}")
                continue
        
        print(f"\n🎉 Carga completa finalizada!")
    
    def get_analysis_summary(self):
        """Obtiene un resumen de todos los análisis cargados"""
        try:
            self.cursor.execute("""
                SELECT 
                    d.domain_name,
                    d.sector,
                    COUNT(da.id) as total_analyses,
                    SUM(da.total_urls) as total_urls,
                    SUM(da.urls_processed) as urls_processed,
                    AVG(da.processing_time_seconds) as avg_processing_time,
                    COUNT(DISTINCT au.id) as unique_urls,
                    COUNT(k.id) as total_keywords
                FROM domains d
                LEFT JOIN domain_analyses da ON d.id = da.domain_id
                LEFT JOIN analyzed_urls au ON da.id = au.domain_analysis_id
                LEFT JOIN keywords k ON au.id = k.url_id
                GROUP BY d.id, d.domain_name, d.sector
                ORDER BY d.domain_name
            """)
            
            results = self.cursor.fetchall()
            
            print("\n📊 RESUMEN DE ANÁLISIS EN BASE DE DATOS:")
            print("=" * 80)
            
            for row in results:
                domain_name, sector, analyses, urls, processed, avg_time, unique_urls, keywords = row
                print(f"🌐 {domain_name}")
                print(f"   Sector: {sector}")
                print(f"   Análisis: {analyses}")
                print(f"   URLs totales: {urls}")
                print(f"   URLs procesadas: {processed}")
                print(f"   URLs únicas: {unique_urls}")
                print(f"   Keywords: {keywords}")
                print(f"   Tiempo promedio: {avg_time:.2f}s")
                print()
                
        except Exception as e:
            print(f"❌ Error obteniendo resumen: {e}")


def main():
    """Función principal para cargar datos"""
    
    # Configuración de Supabase
    HOST = "db.umqgbhmhweqqmatrgpqr.supabase.co"
    PORT = 5432
    DATABASE = "postgres"
    USER = "postgres"
    
    # La contraseña se puede pasar como variable de entorno
    # export SUPABASE_PASSWORD="tu_password_aqui"
    
    print("🚀 Iniciando carga de datos a Supabase PostgreSQL")
    print("=" * 60)
    
    loader = DatabaseLoader(HOST, PORT, DATABASE, USER)
    
    try:
        # Conectar a la base de datos
        loader.connect()
        
        # Crear esquema si no existe
        print("\n📋 Creando esquema de base de datos...")
        loader.create_schema()
        
        # Cargar todos los archivos JSON
        print("\n📁 Cargando archivos JSON...")
        loader.load_all_json_files()
        
        # Mostrar resumen
        loader.get_analysis_summary()
        
    except Exception as e:
        print(f"❌ Error en la carga: {e}")
    finally:
        loader.disconnect()


if __name__ == "__main__":
    main()


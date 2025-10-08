# 🗄️ Base de Datos N8NMC - PostgreSQL con Supabase

## 📋 Descripción

Sistema de base de datos diseñado para almacenar y analizar los resultados de la API N8NMC de manera estructurada y eficiente. Utiliza PostgreSQL en Supabase para almacenar análisis de dominios, URLs, keywords y métricas de rendimiento.

## 🏗️ Arquitectura de la Base de Datos

### **Tablas Principales**

| **Tabla** | **Descripción** | **Relaciones** |
|-----------|-----------------|----------------|
| `domains` | Dominios analizados | 1:N con `domain_analyses` |
| `domain_analyses` | Análisis completos de dominios | 1:N con `analyzed_urls` |
| `analyzed_urls` | URLs individuales analizadas | 1:N con `keywords` |
| `keywords` | Keywords extraídas con scores | N:1 con `analyzed_urls` |
| `domain_stats` | Estadísticas agregadas por dominio | 1:1 con `domains` |

### **Esquema de Datos**

```sql
domains (id, domain_name, sector, created_at, updated_at)
    ↓
domain_analyses (id, domain_id, analysis_date, total_urls, urls_processed, 
                page_types, audiences, intents, top_keywords_*, raw_data)
    ↓
analyzed_urls (id, domain_analysis_id, url, url_hash, page_type, 
              audiences, intent, word_count, title, description)
    ↓
keywords (id, url_id, keyword, score, bucket, source, position, 
         contextual_score, relevance_score, position_score, 
         frequency_score, sector_boost)
```

## 🚀 Configuración e Instalación

### **1. Instalación Automática**

```bash
python setup_database.py
```

Este script:
- ✅ Instala dependencias (`psycopg2-binary`, `python-dotenv`)
- ✅ Crea archivo `.env` con configuración
- ✅ Prueba la conexión a Supabase

### **2. Configuración Manual**

1. **Instalar dependencias:**
```bash
pip install psycopg2-binary python-dotenv
```

2. **Crear archivo `.env`:**
```env
SUPABASE_HOST=db.umqgbhmhweqqmatrgpqr.supabase.co
SUPABASE_PORT=5432
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=tu_password_aqui
```

3. **Crear esquema de base de datos:**
```bash
python load_data_to_db.py
```

## 📊 Carga de Datos

### **Cargar Todos los JSONs**

```bash
python load_data_to_db.py
```

Este script:
- 🔄 Crea el esquema de base de datos
- 📁 Carga todos los archivos `*_domain_complete_test.json`
- 🏷️ Detecta automáticamente el sector de cada dominio
- 📈 Calcula estadísticas agregadas
- ✅ Maneja duplicados y actualizaciones

### **Cargar JSON Específico**

```python
from load_data_to_db import DatabaseLoader

loader = DatabaseLoader(HOST, PORT, DATABASE, USER, PASSWORD)
loader.connect()
loader.load_domain_analysis("results/legalia_domain_complete_test.json")
loader.disconnect()
```

## 🔍 Consultas y Análisis

### **Ejecutar Consultas Predefinidas**

```bash
python database_queries.py
```

### **Consultas Disponibles**

1. **Resumen de Dominios**
   - Total de análisis por dominio
   - URLs procesadas y tiempo promedio
   - Sector detectado

2. **Análisis por Sector**
   - Comparación entre sectores (Legal, Sports, Technology)
   - Métricas agregadas por industria

3. **Top Keywords Globales**
   - Keywords más relevantes por dominio
   - Scores promedio y frecuencia

4. **Distribución por Buckets**
   - Cliente, Producto/Post, Generales SEO
   - Estadísticas por categoría

5. **Métricas de Rendimiento**
   - Tiempo de procesamiento
   - Tasa de éxito
   - Palabras promedio por URL

6. **Análisis de Audiencias**
   - Distribución por tipo de audiencia
   - Métricas por segmento

7. **Análisis de Intenciones**
   - Informacional, Comercial, Consideración
   - Estadísticas por intención

### **Consultas Personalizadas**

```python
from database_queries import DatabaseQueries

queries = DatabaseQueries(HOST, PORT, DATABASE, USER, PASSWORD)
queries.connect()

# Buscar keywords específicas
results = queries.search_keywords("legal", limit=20)

# Exportar datos de un dominio
data = queries.export_domain_data("legalia.com.co")

queries.disconnect()
```

## 📈 Vistas y Reportes

### **Vistas Predefinidas**

1. **`domain_analysis_summary`**
   - Resumen completo con joins
   - Métricas agregadas por dominio

2. **`top_keywords_by_domain`**
   - Top keywords con frecuencia
   - Scores promedio por dominio

### **Consultas SQL Útiles**

```sql
-- Top keywords por sector
SELECT d.sector, k.keyword, AVG(k.score) as avg_score
FROM domains d
JOIN domain_analyses da ON d.id = da.domain_id
JOIN analyzed_urls au ON da.id = au.domain_analysis_id
JOIN keywords k ON au.id = k.url_id
GROUP BY d.sector, k.keyword
ORDER BY avg_score DESC;

-- Distribución de audiencias
SELECT au.audiences, COUNT(*) as url_count
FROM analyzed_urls au
GROUP BY au.audiences
ORDER BY url_count DESC;

-- Métricas de rendimiento por dominio
SELECT 
    d.domain_name,
    AVG(da.processing_time_seconds) as avg_time,
    AVG(au.word_count) as avg_words,
    COUNT(k.id) as total_keywords
FROM domains d
JOIN domain_analyses da ON d.id = da.domain_id
JOIN analyzed_urls au ON da.id = au.domain_analysis_id
JOIN keywords k ON au.id = k.url_id
GROUP BY d.domain_name;
```

## 🎯 Casos de Uso

### **1. Análisis Competitivo**
- Comparar keywords entre dominios del mismo sector
- Identificar oportunidades de contenido
- Analizar estrategias de audiencia

### **2. Optimización SEO**
- Identificar keywords de alto valor
- Analizar distribución por buckets
- Optimizar contenido por intención

### **3. Reportes Ejecutivos**
- Métricas de rendimiento por dominio
- Análisis de tendencias por sector
- KPIs de procesamiento y calidad

### **4. Investigación de Mercado**
- Análisis de audiencias por sector
- Patrones de intención de contenido
- Benchmarking de métricas

## 🔧 Mantenimiento

### **Backup de Datos**

```sql
-- Exportar datos de un dominio
COPY (
    SELECT * FROM domains d
    JOIN domain_analyses da ON d.id = da.domain_id
    WHERE d.domain_name = 'legalia.com.co'
) TO '/path/to/backup.csv' WITH CSV HEADER;
```

### **Limpieza de Datos**

```sql
-- Eliminar análisis antiguos (más de 1 año)
DELETE FROM domain_analyses 
WHERE analysis_date < NOW() - INTERVAL '1 year';

-- Limpiar keywords con score muy bajo
DELETE FROM keywords 
WHERE score < 0.1;
```

### **Optimización de Rendimiento**

```sql
-- Actualizar estadísticas
ANALYZE domains;
ANALYZE domain_analyses;
ANALYZE analyzed_urls;
ANALYZE keywords;

-- Reindexar tablas grandes
REINDEX TABLE keywords;
```

## 📊 Métricas Almacenadas

### **Por Dominio**
- Total de URLs analizadas
- Tiempo de procesamiento promedio
- Distribución de tipos de página
- Audiencias detectadas
- Intenciones identificadas

### **Por URL**
- Tipo de página (blog, e-commerce, mixto)
- Audiencia objetivo
- Intención del contenido
- Conteo de palabras y headings
- Tiempo de procesamiento

### **Por Keyword**
- Score final (0-1)
- Bucket de clasificación
- Scores componentes (contextual, relevancia, posición, frecuencia)
- Boost por sector
- Posición en ranking

## 🚨 Troubleshooting

### **Errores Comunes**

1. **Error de conexión**
   - Verificar credenciales en `.env`
   - Confirmar que Supabase esté activo
   - Revisar firewall y red

2. **Error de esquema**
   - Ejecutar `database_schema.sql` manualmente
   - Verificar permisos de usuario
   - Revisar logs de Supabase

3. **Error de carga de datos**
   - Verificar formato de JSON
   - Revisar encoding de archivos
   - Confirmar estructura de datos

### **Logs y Debugging**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Habilitar logs de psycopg2
import psycopg2
psycopg2.extensions.set_wait_callback(psycopg2.extensions.make_wait_callback())
```

## 📚 Archivos del Sistema

- `database_schema.sql` - Esquema completo de la base de datos
- `load_data_to_db.py` - Script de carga de datos
- `database_queries.py` - Consultas y análisis
- `setup_database.py` - Instalación automática
- `config.env.example` - Plantilla de configuración

## 🎉 Beneficios

✅ **Almacenamiento Estructurado** - Datos organizados y normalizados  
✅ **Consultas Eficientes** - Índices optimizados para búsquedas rápidas  
✅ **Escalabilidad** - Diseño preparado para grandes volúmenes  
✅ **Análisis Avanzado** - Vistas y consultas predefinidas  
✅ **Integración Supabase** - Backend robusto y confiable  
✅ **Backup Automático** - Protección de datos garantizada  

La base de datos está lista para producción y puede manejar análisis de miles de dominios con alta eficiencia y confiabilidad.


# 🚀 Sistema de Análisis SEO de Dominios - Guía Completa

**Versión:** 1.0.0  
**Última actualización:** 8 de Octubre 2025  
**Estado:** ✅ Producción Ready

---

## 📋 Índice

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura](#arquitectura)
3. [Requisitos](#requisitos)
4. [Instalación Local](#instalación-local)
5. [Levantar el Backend](#levantar-el-backend)
6. [Endpoints de la API](#endpoints-de-la-api)
7. [Deployment en Railway](#deployment-en-railway)
8. [Deployment en Cloud Run](#deployment-en-cloud-run)
9. [Configuración de Variables](#configuración-de-variables)
10. [Correcciones Docker Aplicadas](#correcciones-docker-aplicadas)
11. [Troubleshooting](#troubleshooting)

---

## 📖 Descripción del Proyecto

API completa en FastAPI para análisis exhaustivo de dominios web con:
- ✅ Extracción inteligente de keywords usando YAKE + KeyBERT
- ✅ Clasificación automática de páginas (e-commerce/blog/mixto)
- ✅ Análisis de audiencia e intención de búsqueda
- ✅ Descubrimiento automático de sitemaps
- ✅ Procesamiento asíncrono y paralelo
- ✅ Bucketización de keywords en 3 categorías
- ✅ Scoring personalizable con fórmula ponderada

---

## 🏗️ Arquitectura

```
N8NMC/
├── app/
│   ├── main.py              # FastAPI app, endpoints, middleware
│   ├── config.py            # Configuración y pesos ajustables
│   ├── schemas.py           # Modelos Pydantic
│   └── services/
│       ├── fetcher.py       # HTTP asíncrono con retries
│       ├── sitemap.py       # Descubrimiento y parseo sitemaps
│       ├── parser.py        # Extracción HTML completa
│       ├── classifier.py    # Clasificación de páginas
│       ├── nlp.py           # YAKE, KeyBERT, MiniLM
│       ├── ecom.py          # Extracción de productos
│       ├── scorer.py        # Scoring y bucketización
│       └── utils.py         # Stopwords, helpers
├── Dockerfile               # Configuración Docker optimizada
├── docker-compose.yml       # Orquestación local
├── requirements.txt         # Dependencias Python
├── railway.json             # Configuración Railway
├── nixpacks.toml           # Build config Railway
└── Procfile                # Comando de inicio Railway
```

---

## 📋 Requisitos

- **Python:** 3.11+
- **RAM:** 2GB mínimo (para modelos NLP)
- **Dependencias principales:**
  - FastAPI 0.109.0
  - Uvicorn 0.27.0
  - HTTPX 0.26.0
  - SentenceTransformers 2.3.1
  - KeyBERT 0.8.4
  - YAKE 0.4.8

---

## 🛠️ Instalación Local

### **1. Clonar el Repositorio**

```bash
git clone https://github.com/TechSeois/Diagnosticador-Seois.git
cd Diagnosticador-Seois
```

### **2. Crear Entorno Virtual**

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### **3. Instalar Dependencias**

```bash
pip install -r requirements.txt
```

### **4. Configurar Variables de Entorno (Opcional)**

```bash
# Copiar ejemplo
cp env.example .env

# Editar .env con tus valores
API_KEY=tu-clave-secreta-aqui
MAX_CONCURRENT_REQUESTS=10
DEFAULT_TIMEOUT=15
```

---

## 🚀 Levantar el Backend

### **Opción 1: Comando Básico**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### **Opción 2: Con Hot Reload (Desarrollo)**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### **Opción 3: Con Workers (Producción)**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

### **Opción 4: Docker Local**

```bash
# Build
docker build -t seo-analysis-api .

# Run
docker run -p 8080:8080 -e API_KEY=tu-clave seo-analysis-api

# O con docker-compose
docker-compose up -d
```

### **Verificar que Funciona**

```bash
# Health check
curl http://localhost:8080/healthz

# Documentación interactiva
# Abrir en navegador: http://localhost:8080/docs
```

---

## 📡 Endpoints de la API

### **1. POST /analyze-url**

Analiza una URL individual y extrae keywords clasificadas.

**Request:**
```bash
curl -X POST "http://localhost:8080/analyze-url" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://speedlogic.com.co/"
  }'
```

**Response:**
```json
{
  "url": "https://speedlogic.com.co/",
  "tipo": "mixto",
  "meta": {
    "title": "Speed Logic - Tienda de Tecnología",
    "description": "..."
  },
  "headings": {
    "h1": ["Speed Logic"],
    "h2": ["Productos", "Ofertas"]
  },
  "stats": {
    "words": 484,
    "reading_time_min": 2
  },
  "audiencia": ["gaming", "professionals"],
  "intencion": "comercial",
  "productos": [...],
  "keywords": {
    "cliente": [],
    "producto_o_post": [
      {"term": "ram", "score": 0.343},
      {"term": "tarjeta gráfica", "score": 0.338}
    ],
    "generales_seo": []
  }
}
```

### **2. POST /analyze-domain**

Analiza un dominio completo con múltiples URLs.

**Request:**
```bash
curl -X POST "http://localhost:8080/analyze-domain" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "https://speedlogic.com.co",
    "max_urls": 10,
    "timeout": 15
  }'
```

**Response:**
```json
{
  "domain": "https://speedlogic.com.co",
  "resumen": {
    "total_urls": 5,
    "por_tipo": {
      "ecommerce": 0,
      "blog": 1,
      "mixto": 4
    },
    "top_keywords_cliente": [...],
    "top_keywords_producto": [
      {"term": "speed logic", "score": 0.654},
      {"term": "tarjeta", "score": 0.482}
    ],
    "top_keywords_generales": [...]
  },
  "urls": [
    /* Array con análisis detallado de cada URL */
  ]
}
```

### **3. GET /scoring-weights**

Obtiene los pesos actuales de la fórmula de scoring.

```bash
curl -X GET "http://localhost:8080/scoring-weights" \
  -H "X-API-Key: your-secret-api-key-here"
```

### **4. PUT /scoring-weights**

Actualiza los pesos de scoring dinámicamente.

```bash
curl -X PUT "http://localhost:8080/scoring-weights" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "w1_frequency": 0.35,
    "w2_tfidf": 0.30,
    "w3_cooccurrence": 0.20,
    "w4_position_title": 0.10,
    "w5_similarity_brand": 0.05
  }'
```

### **5. GET /healthz**

Health check (no requiere autenticación).

```bash
curl http://localhost:8080/healthz
```

---

## 🚂 Deployment en Railway

### **Configuración**

Railway detecta automáticamente aplicaciones FastAPI usando los archivos:
- `railway.json` - Configuración principal
- `Procfile` - Comando de inicio
- `nixpacks.toml` - Optimización del build

### **Pasos de Deployment**

**1. Subir código a GitHub:**
```bash
git push origin master
```

**2. Crear proyecto en Railway:**
- Ve a https://railway.app/dashboard
- Clic en "New Project"
- Selecciona "Deploy from GitHub repo"
- Selecciona tu repositorio

**3. Configurar Variables de Entorno:**

En Railway Dashboard → Variables:
```env
API_KEY=tu-clave-secreta-aqui
PORT=8080
MAX_CONCURRENT_REQUESTS=10
DEFAULT_TIMEOUT=15
MAX_URLS_PER_DOMAIN=100
```

**4. Deploy Automático:**

Railway desplegará automáticamente. El proceso toma ~3-5 minutos.

### **URL del Servicio**

Railway te dará una URL como:
```
https://diagnosticador-seois-production.up.railway.app
```

### **Verificar Deployment**

```bash
curl https://tu-app.railway.app/healthz
```

---

## ☁️ Deployment en Cloud Run (Google Cloud)

### **Método 1: Deploy desde Código Local**

```bash
# 1. Autenticarse
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Deploy directo
gcloud run deploy diagnosticador-seois \
  --source . \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "API_KEY=your-secret-api-key-here"
```

### **Método 2: Deploy desde Cloud Build (Automático)**

**1. Conectar repositorio a Cloud Build:**
- Ve a: https://console.cloud.google.com/cloud-build/triggers
- Clic en "Connect Repository"
- Selecciona tu repositorio GitHub

**2. Crear Trigger:**
- Branch pattern: `^master$`
- Build configuration: `Dockerfile`
- Location: `/Dockerfile`

**3. Push al repositorio:**
```bash
git push origin master
```

Cloud Build desplegará automáticamente.

### **URL del Servicio**

```
https://diagnosticador-seois-HASH.us-east1.run.app
```

### **Verificar Deployment**

```bash
curl https://tu-servicio.run.app/healthz
```

---

## ⚙️ Configuración de Variables

### **Variables de Entorno Principales**

| Variable | Descripción | Default | Obligatoria |
|----------|-------------|---------|-------------|
| `API_KEY` | Clave de autenticación | `your-secret-api-key-here` | ✅ Sí |
| `PORT` | Puerto del servidor | `8080` | No (Railway/Cloud Run lo asignan) |
| `MAX_CONCURRENT_REQUESTS` | Requests paralelos | `10` | No |
| `DEFAULT_TIMEOUT` | Timeout en segundos | `15` | No |
| `MAX_URLS_PER_DOMAIN` | URLs máximas por dominio | `100` | No |

### **Pesos de Scoring (Opcionales)**

| Variable | Descripción | Default |
|----------|-------------|---------|
| `W1_FREQUENCY` | Peso frecuencia | `0.3` |
| `W2_TFIDF` | Peso TF-IDF | `0.25` |
| `W3_COOCCURRENCE` | Peso co-ocurrencias | `0.2` |
| `W4_POSITION_TITLE` | Peso posición en título | `0.15` |
| `W5_SIMILARITY_BRAND` | Peso similitud con marca | `0.1` |

**Fórmula de Scoring:**
```
score = w1*frequency + w2*tfidf + w3*cooccurrence + w4*position_title + w5*similarity_brand
```

### **Variables Docker/NLP (Ya configuradas en Dockerfile)**

| Variable | Propósito | Valor |
|----------|-----------|-------|
| `TRANSFORMERS_CACHE` | Caché Transformers | `/usr/local/share/transformers_cache` |
| `HF_HOME` | Home HuggingFace | `/usr/local/share/huggingface` |
| `SENTENCE_TRANSFORMERS_HOME` | Caché SentenceTransformers | `/usr/local/share/sentence_transformers` |
| `NLTK_DATA` | Datos NLTK | `/usr/local/share/nltk_data` |

---

## 🐳 Correcciones Docker Aplicadas

### **Problema Original**

Al ejecutar en Docker/Cloud Run, la aplicación fallaba con:
```
PermissionError: [Errno 13] Permission denied: '/home/appuser'
```

**Causa:** Los modelos NLP (NLTK, HuggingFace, SentenceTransformers) intentaban descargar datos en runtime en `/home/appuser`, pero el usuario `appuser` no tenía permisos de escritura.

### **Soluciones Implementadas**

#### **1. Dockerfile - Configuración de Cachés (Líneas 31-47)**

```dockerfile
# Configurar directorios de caché con permisos apropiados
ENV TRANSFORMERS_CACHE=/usr/local/share/transformers_cache
ENV HF_HOME=/usr/local/share/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/usr/local/share/sentence_transformers
ENV NLTK_DATA=/usr/local/share/nltk_data

# Crear directorios con permisos 755
RUN mkdir -p ${TRANSFORMERS_CACHE} ${HF_HOME} ${SENTENCE_TRANSFORMERS_HOME} ${NLTK_DATA} && \
    chmod -R 755 ${TRANSFORMERS_CACHE} ${HF_HOME} ${SENTENCE_TRANSFORMERS_HOME} ${NLTK_DATA}

# Descargar modelos en build time (como root)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
RUN python -c "import nltk; nltk.download('stopwords', download_dir='${NLTK_DATA}', quiet=True)"
```

#### **2. app/services/utils.py - Manejo Robusto de Errores**

```python
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('stopwords', quiet=True)
    except Exception as e:
        # Fallback: asume que ya están disponibles
        print(f"Warning: Could not download NLTK stopwords: {e}")
```

#### **3. app/services/nlp.py - Carga Desde Caché**

```python
cache_dir = os.environ.get('SENTENCE_TRANSFORMERS_HOME') or os.environ.get('TRANSFORMERS_CACHE')
if cache_dir:
    self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=cache_dir)
```

### **Resultado**

✅ Todos los modelos se descargan en **build time** (como root)  
✅ Se guardan en directorios con **permisos 755**  
✅ Usuario `appuser` puede **leer** (pero no escribir) los cachés  
✅ Aplicación inicia sin errores de permisos

---

## 🔍 Troubleshooting

### **1. Error: "API key inválida o faltante"**

**Problema:** Request sin header `X-API-Key` o con clave incorrecta.

**Solución:**
```bash
# Asegúrate de incluir el header correcto
curl -H "X-API-Key: your-secret-api-key-here" ...
```

### **2. Error: "Connection refused" o "Cannot connect"**

**Problema:** El servidor no está corriendo.

**Solución:**
```bash
# Verificar que el servidor esté levantado
uvicorn app.main:app --host 0.0.0.0 --port 8080

# Verificar puerto
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # Linux/Mac
```

### **3. Error: "PermissionError" en Docker**

**Problema:** Modelos NLP no pueden descargarse en runtime.

**Solución:** Ya está corregido en el Dockerfile actual. Si persiste:
```bash
# Rebuild la imagen desde cero
docker build --no-cache -t seo-analysis-api .
```

### **4. Error: "Out of Memory" en Cloud Run**

**Problema:** Memoria insuficiente para modelos NLP.

**Solución:**
```bash
# Aumentar memoria a 2GB mínimo
gcloud run deploy diagnosticador-seois --memory 2Gi
```

### **5. Error: "Timeout" en análisis de dominio**

**Problema:** El análisis tarda más que el timeout configurado.

**Solución:**
```bash
# Aumentar timeout a 300 segundos
gcloud run deploy diagnosticador-seois --timeout 300

# O reducir max_urls en el request
{
  "domain": "https://ejemplo.com",
  "max_urls": 10  # Reducir de 50 a 10
}
```

### **6. Cloud Run muestra "placeholder"**

**Problema:** El build falló y no hay código desplegado.

**Solución:**
```bash
# Ver logs de Cloud Build
gcloud builds list --limit=5
gcloud builds log [BUILD_ID]

# Redesplegar
git push origin master  # Si tienes CI/CD
# O deploy directo
gcloud run deploy diagnosticador-seois --source .
```

### **7. Puerto incorrecto en Railway/Cloud Run**

**Problema:** La aplicación no responde porque escucha en puerto incorrecto.

**Verificación:** El archivo `app/main.py` ya está configurado para leer `PORT` de la variable de entorno:
```python
port = int(os.environ.get("PORT", 8080))
```

### **8. Modelos NLP no cargan**

**Problema:** Primera vez que corres la app, los modelos deben descargarse.

**Solución:** Espera ~20-30 segundos en el primer inicio. Los modelos se descargan automáticamente.

---

## 📊 Especificaciones Técnicas

### **Recursos Necesarios**

- **RAM:** 2GB mínimo (modelos NLP)
- **CPU:** 1 vCPU suficiente
- **Disco:** ~1.5GB (incluye modelos)
- **Network:** Ancho de banda normal

### **Tiempos de Respuesta**

- **Health check:** <100ms
- **Análisis URL individual:** 5-10 segundos
- **Análisis dominio (10 URLs):** 30-60 segundos
- **Startup time:** 10-15 segundos

### **Modelos NLP Incluidos**

- **SentenceTransformer:** all-MiniLM-L6-v2 (~90MB)
- **NLTK stopwords:** Spanish + English (~1MB)
- **YAKE:** Sin modelo pre-descargado (on-demand)

---

## 🎯 Características Principales

### **Análisis Completo**

✅ Extracción de metadatos (title, description, og tags)  
✅ Análisis de headings (H1, H2, H3)  
✅ Estadísticas de contenido (palabras, tiempo de lectura, enlaces)  
✅ Clasificación de tipo de página (ecommerce, blog, mixto)  
✅ Detección de audiencia (B2B, B2C, gaming, professionals, etc.)  
✅ Detección de intención (comercial, informacional, transaccional)  
✅ Extracción de información de marca  
✅ Extracción de productos (schema.org)

### **Keywords Inteligentes**

✅ Extracción con YAKE + KeyBERT  
✅ Fusión y deduplicación inteligente  
✅ Scoring con fórmula ponderada personalizable  
✅ Bucketización en 3 categorías:
   - **Cliente:** Keywords de marca/empresa
   - **Producto/Post:** Keywords específicas de contenido
   - **Generales SEO:** Keywords amplias y head terms

### **Procesamiento Asíncrono**

✅ Descarga paralela de múltiples URLs  
✅ Control de concurrencia (semáforos)  
✅ Rate limiting configurable  
✅ Manejo robusto de errores  
✅ Timeout por request configurable

---

## 📚 Documentación Adicional

### **Documentación Interactiva (Swagger)**

Una vez corriendo, accede a:
```
http://localhost:8080/docs
```

### **Documentación ReDoc**

```
http://localhost:8080/redoc
```

### **Logs**

```bash
# Ver logs en tiempo real (Docker)
docker logs -f container-name

# Ver logs en Cloud Run
gcloud run logs read diagnosticador-seois --limit=50

# Ver logs en Railway
railway logs
```

---

## ✅ Checklist de Deployment

- [ ] Código pusheado al repositorio
- [ ] Variables de entorno configuradas
- [ ] API_KEY cambiado a valor seguro
- [ ] Proyecto creado en Railway o Cloud Run
- [ ] Primer deployment exitoso
- [ ] Health check funcionando (`/healthz`)
- [ ] Documentación accesible (`/docs`)
- [ ] Endpoint `/analyze-url` probado
- [ ] Endpoint `/analyze-domain` probado
- [ ] Logs verificados sin errores
- [ ] Configuración de memoria adecuada (2GB)

---

## 🎉 Estado del Proyecto

**Versión:** 1.0.0  
**Estado:** ✅ **PRODUCCIÓN READY**

- ✅ Todos los errores de permisos corregidos
- ✅ Docker optimizado y funcional
- ✅ Configuración Railway completa
- ✅ Configuración Cloud Run completa
- ✅ Documentación completa
- ✅ Tests pasados exitosamente
- ✅ Listo para deployment

---

## 📞 Soporte

Para problemas o preguntas:
- **Logs de build:** Ver en Cloud Console o Railway Dashboard
- **Health check:** `curl https://tu-app/healthz`
- **Documentación API:** `https://tu-app/docs`

---

**Desarrollado con ❤️ usando FastAPI, YAKE, KeyBERT y MiniLM**

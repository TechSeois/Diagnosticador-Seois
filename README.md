# Sistema de Análisis SEO de Dominios

Una API completa desarrollada en FastAPI para análisis exhaustivo de dominios web, extracción de keywords inteligente y clasificación de contenido. El sistema descubre automáticamente sitemaps, analiza páginas individuales y genera keywords clasificadas en buckets específicos usando algoritmos avanzados de NLP.

## 🚀 Características Principales

- **Descubrimiento Automático de Sitemaps**: Detecta y parsea sitemaps XML, incluyendo sitemap indexes
- **Análisis Completo de Páginas**: Extrae metadatos, headings, contenido principal y datos de schema.org
- **Clasificación Inteligente**: Determina tipo de página (e-commerce/blog/mixto), audiencia e intención
- **Extracción de Keywords Avanzada**: Combina YAKE y KeyBERT con MiniLM para máxima precisión
- **Bucketización Inteligente**: Clasifica keywords en buckets específicos (cliente/producto/generales)
- **Scoring Personalizable**: Fórmula ponderada ajustable dinámicamente
- **Procesamiento Asíncrono**: Análisis paralelo de múltiples URLs con rate limiting
- **Extracción de Productos**: Detecta productos automáticamente desde schema.org
- **API REST Completa**: Endpoints documentados con OpenAPI/Swagger

## 🏗️ Arquitectura

```
N8NMC/
├── app/                 # Aplicación principal FastAPI
│   ├── main.py         # FastAPI app, endpoints, middleware
│   ├── config.py       # Configuración y pesos ajustables
│   ├── schemas.py      # Modelos Pydantic request/response
│   └── services/       # Servicios del sistema
│       ├── fetcher.py  # HTTP asíncrono con retries
│       ├── sitemap.py  # Descubrimiento y parseo sitemaps
│       ├── parser.py   # Extracción HTML completa
│       ├── classifier.py # Clasificación blog/ecom/audiencia
│       ├── nlp.py      # YAKE, KeyBERT, normalización
│       ├── ecom.py     # Extracción productos
│       ├── scorer.py   # Scoring y bucketización
│       └── utils.py    # Stopwords, helpers, regex
├── tests/              # Pruebas principales del sistema
│   ├── test_logitech_domain.py  # Prueba análisis de dominio
│   └── test_speedlogic.py       # Prueba análisis de URL
├── scripts/            # Scripts de utilidad y desarrollo
│   ├── start.py        # Script de inicio
│   ├── example_usage.py # Ejemplos de uso
│   └── debug_api.py    # Herramientas de debugging
├── docs/               # Documentación del proyecto
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── cloud-run-deploy.md
├── results/            # Resultados de análisis guardados
├── archive/            # Archivos antiguos y pruebas obsoletas
├── docker-compose.yml  # Configuración Docker
├── Dockerfile         # Imagen Docker
├── requirements.txt   # Dependencias Python
└── README.md          # Este archivo
```

## 📋 Requisitos

- Python 3.11+
- Docker (opcional)
- Google Cloud SDK (para deploy)

## 🛠️ Instalación

### Desarrollo Local

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd N8NMC
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate    # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp env.example .env
# Editar .env con tus configuraciones
```

5. **Inicio rápido (recomendado)**
```bash
python start.py
```

6. **O ejecutar manualmente**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Verificación del Sistema

Ejecuta las pruebas principales para verificar que todo funciona:
```bash
# Prueba de análisis de dominio (Logitech)
python tests/test_logitech_domain.py

# Prueba de análisis de URL individual (SpeedLogic)
python tests/test_speedlogic.py
```

Ejecuta el ejemplo de uso:
```bash
python scripts/example_usage.py
```

### Docker

1. **Construir imagen**
```bash
docker build -t seo-analysis-api .
```

2. **Ejecutar con Docker Compose**
```bash
docker-compose up -d
```

3. **Verificar funcionamiento**
```bash
curl http://localhost:8080/healthz
```

## 📚 Uso de la API

### Autenticación

Todas las requests requieren header de autenticación:
```bash
curl -H "X-API-Key: your-secret-api-key-here" ...
```

### Endpoints Principales

#### 1. Análisis de URL Individual

```bash
curl -X POST "http://localhost:8080/analyze-url" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://ejemplo.com/producto-zapatillas"
  }'
```

**Response:**
```json
{
  "url": "https://ejemplo.com/producto-zapatillas",
  "tipo": "ecommerce",
  "meta": {
    "title": "Zapatillas Running XYZ - Mejor Precio",
    "description": "Zapatillas de running profesionales...",
    "og_title": "Zapatillas Running XYZ",
    "og_description": "Descubre las mejores zapatillas...",
    "canonical": "https://ejemplo.com/producto-zapatillas",
    "lang": "es"
  },
  "headings": {
    "h1": ["Zapatillas Running XYZ"],
    "h2": ["Características", "Especificaciones", "Opiniones"],
    "h3": ["Material", "Suela", "Tallas disponibles"]
  },
  "stats": {
    "words": 1234,
    "reading_time_min": 6,
    "internal_links": 24,
    "external_links": 3
  },
  "audiencia": ["principiantes", "B2C"],
  "intencion": "comercial",
  "productos": [
    {
      "nombre": "Zapatillas Running XYZ",
      "categoria": "Calzado Deportivo",
      "marca": "MarcaA",
      "precio": 89.99,
      "moneda": "EUR"
    }
  ],
  "keywords": {
    "cliente": [
      {"term": "marcaA", "score": 0.83},
      {"term": "tienda online", "score": 0.61}
    ],
    "producto_o_post": [
      {"term": "zapatillas running", "score": 0.78},
      {"term": "calzado deportivo", "score": 0.72}
    ],
    "generales_seo": [
      {"term": "deportes", "score": 0.65},
      {"term": "ejercicio", "score": 0.58}
    ]
  }
}
```

#### 2. Análisis Completo de Dominio

```bash
curl -X POST "http://localhost:8080/analyze-domain" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "https://ejemplo.com",
    "max_urls": 50,
    "timeout": 15
  }'
```

**Response:**
```json
{
  "domain": "https://ejemplo.com",
  "resumen": {
    "total_urls": 45,
    "por_tipo": {
      "ecommerce": 28,
      "blog": 15,
      "mixto": 2
    },
    "top_keywords_cliente": [
      {"term": "marcaA", "score": 0.89},
      {"term": "tienda online", "score": 0.76}
    ],
    "top_keywords_producto": [
      {"term": "zapatillas", "score": 0.82},
      {"term": "ropa deportiva", "score": 0.71}
    ],
    "top_keywords_generales": [
      {"term": "deportes", "score": 0.68},
      {"term": "salud", "score": 0.62}
    ]
  },
  "urls": [
    // Array de análisis individuales por URL
  ]
}
```

#### 3. Gestión de Pesos de Scoring

**Obtener pesos actuales:**
```bash
curl -X GET "http://localhost:8080/scoring-weights" \
  -H "X-API-Key: your-api-key"
```

**Actualizar pesos:**
```bash
curl -X PUT "http://localhost:8080/scoring-weights" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "w1_frequency": 0.4,
    "w2_tfidf": 0.3,
    "w3_cooccurrence": 0.2,
    "w4_position_title": 0.05,
    "w5_similarity_brand": 0.05
  }'
```

#### 4. Health Check

```bash
curl -X GET "http://localhost:8080/healthz"
```

## ⚙️ Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `API_KEY` | Clave API para autenticación | `your-secret-api-key-here` |
| `MAX_CONCURRENT_REQUESTS` | Requests concurrentes máximos | `10` |
| `DEFAULT_TIMEOUT` | Timeout por request (segundos) | `15` |
| `MAX_URLS_PER_DOMAIN` | URLs máximas por dominio | `100` |
| `W1_FREQUENCY` | Peso frecuencia en scoring | `0.3` |
| `W2_TFIDF` | Peso TF-IDF en scoring | `0.25` |
| `W3_COOCCURRENCE` | Peso co-ocurrencias | `0.2` |
| `W4_POSITION_TITLE` | Peso posición en título | `0.15` |
| `W5_SIMILARITY_BRAND` | Peso similitud con marca | `0.1` |

### Fórmula de Scoring

El score final de cada keyword se calcula usando la fórmula:

```
score = w1*freq + w2*tfidf + w3*cooccur + w4*pos_title + w5*sim_brand
```

Donde:
- **freq**: Frecuencia normalizada del término
- **tfidf**: Score TF-IDF del término
- **cooccur**: Co-ocurrencias en headings importantes
- **pos_title**: Posición en el título (más alto al inicio)
- **sim_brand**: Similitud con la marca detectada

## 🚀 Deploy en Google Cloud Run

### 1. Configuración Inicial

```bash
# Autenticarse en Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region europe-west1
```

### 2. Build y Deploy

```bash
# Construir imagen
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/seo-analysis-api

# Deploy a Cloud Run
gcloud run deploy seo-analysis-api \
  --image gcr.io/YOUR_PROJECT_ID/seo-analysis-api \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 10 \
  --max-instances 10 \
  --port 8080 \
  --set-env-vars "API_KEY=your-production-api-key"
```

### 3. Configuración Recomendada para Producción

- **Memory**: 2GB (necesario para modelos NLP)
- **CPU**: 1 vCPU
- **Timeout**: 300s (análisis de dominio puede ser largo)
- **Concurrency**: 10-20 requests simultáneos
- **Max instances**: 10-50 dependiendo del tráfico
- **Min instances**: 0 para ahorrar costos

## 📊 Buckets de Keywords

El sistema clasifica automáticamente las keywords en tres buckets:

### 1. **Cliente** (`keywords_cliente`)
- Marca y términos del dominio
- Keywords con alta frecuencia global
- Términos que aparecen en múltiples páginas

### 2. **Producto/Post** (`producto_o_post`)
- Keywords específicas de la página actual
- Términos relacionados con productos (e-commerce)
- Contenido específico del post (blog)

### 3. **Generales SEO** (`generales_seo`)
- Términos amplios y head terms
- Keywords de intención informacional
- Entidades genéricas del dominio

## 🔍 Algoritmos de NLP

### YAKE (Yet Another Keyword Extractor)
- Extracción rápida sin embeddings
- Optimizado para español
- N-gramas 1-2 configurable

### KeyBERT + MiniLM
- Modelo `all-MiniLM-L6-v2`
- Extracción semántica avanzada
- Deduplicación por similitud coseno

### Fusión Inteligente
- Combina resultados de ambos algoritmos
- Elimina duplicados por similitud > 0.85
- Normaliza scores finales

## 🛡️ Seguridad

- **Autenticación**: Header `X-API-Key` requerido
- **Rate Limiting**: Delay configurable entre requests
- **Robots.txt**: Respeta restricciones automáticamente
- **User-Agent**: Headers realistas para evitar bloqueos
- **Timeouts**: Límites configurables por request

## 📈 Monitoreo y Logging

- **Logs estructurados**: Formato JSON con timestamps
- **Health checks**: Endpoint `/healthz` para monitoreo
- **Métricas**: Tiempo de procesamiento y estadísticas
- **Error handling**: Manejo robusto de excepciones

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de memoria**: Aumentar memoria a 2GB mínimo
2. **Timeout en análisis de dominio**: Aumentar `DEFAULT_TIMEOUT`
3. **Rate limiting**: Ajustar `MAX_CONCURRENT_REQUESTS`
4. **Modelos no cargan**: Verificar conexión a internet para descarga inicial

### Logs Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f api

# Ver logs específicos
grep "ERROR" logs/app.log
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear issue en GitHub
- Email: soporte@ejemplo.com
- Documentación: `/docs` (Swagger UI)

---

**Versión**: 1.0.0  
**Última actualización**: Enero 2025

# Cloud Run deployment configuration
# Este archivo contiene comandos y configuraciones para deploy en Google Cloud Run

# 1. Configuración inicial de Google Cloud
# gcloud auth login
# gcloud config set project YOUR_PROJECT_ID
# gcloud config set run/region europe-west1

# 2. Build y push de la imagen Docker
# gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/seo-analysis-api

# 3. Deploy a Cloud Run
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
  --min-instances 0 \
  --port 8080 \
  --set-env-vars "API_KEY=your-production-api-key" \
  --set-env-vars "MAX_CONCURRENT_REQUESTS=10" \
  --set-env-vars "DEFAULT_TIMEOUT=15" \
  --set-env-vars "MAX_URLS_PER_DOMAIN=100" \
  --set-env-vars "LOG_LEVEL=INFO"

# 4. Configuración de dominio personalizado (opcional)
# gcloud run domain-mappings create \
#   --service seo-analysis-api \
#   --domain api.yourdomain.com \
#   --region europe-west1

# 5. Configuración de autenticación (opcional)
# gcloud run services add-iam-policy-binding seo-analysis-api \
#   --member="user:your-email@domain.com" \
#   --role="roles/run.invoker" \
#   --region europe-west1

# Variables de entorno recomendadas para producción:
# API_KEY: Clave API segura para autenticación
# MAX_CONCURRENT_REQUESTS: 10-20 dependiendo del tráfico
# DEFAULT_TIMEOUT: 15-30 segundos
# MAX_URLS_PER_DOMAIN: 100-500 dependiendo del uso
# LOG_LEVEL: INFO o WARNING para producción

# Configuración de recursos recomendada:
# Memory: 2GB (necesario para modelos NLP)
# CPU: 1 vCPU
# Timeout: 300s (análisis de dominio puede ser largo)
# Concurrency: 10-20 requests simultáneos
# Max instances: 10-50 dependiendo del tráfico
# Min instances: 0 para ahorrar costos

# Monitoreo y logging:
# Los logs se envían automáticamente a Google Cloud Logging
# Métricas disponibles en Google Cloud Monitoring
# Health check endpoint: /healthz


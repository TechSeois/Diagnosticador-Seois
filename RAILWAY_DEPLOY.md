# 🚂 Despliegue en Railway

Guía completa para desplegar el Sistema de Análisis SEO de Dominios en Railway.

## 📋 Requisitos Previos

- Cuenta en [Railway](https://railway.app)
- Código en un repositorio Git (GitHub, GitLab, Bitbucket)
- Railway CLI (opcional)

## 🚀 Método 1: Despliegue desde GitHub (Recomendado)

### Paso 1: Preparar el Repositorio

```bash
# Asegúrate de que los cambios estén commiteados
git add railway.json Procfile nixpacks.toml RAILWAY_DEPLOY.md
git commit -m "Add Railway configuration files"
git push origin master
```

### Paso 2: Crear Proyecto en Railway

1. Ve a https://railway.app/dashboard
2. Clic en "New Project"
3. Selecciona "Deploy from GitHub repo"
4. Autoriza Railway a acceder a tu GitHub
5. Selecciona el repositorio `Diagnosticador-Seois`
6. Railway detectará automáticamente que es una aplicación Python/FastAPI

### Paso 3: Configurar Variables de Entorno

En el dashboard de Railway, ve a tu proyecto → Variables:

```env
# Obligatorias
API_KEY=tu-clave-secreta-aqui-cambiar
PORT=8080

# Configuración de la aplicación
MAX_CONCURRENT_REQUESTS=10
DEFAULT_TIMEOUT=15
MAX_URLS_PER_DOMAIN=100

# Pesos de scoring
W1_FREQUENCY=0.3
W2_TFIDF=0.25
W3_COOCCURRENCE=0.2
W4_POSITION_TITLE=0.15
W5_SIMILARITY_BRAND=0.1

# Configuración NLP
YAKE_MAX_NGRAM_SIZE=2
YAKE_DEDUPLICATION_THRESHOLD=0.7
KEYBERT_MAX_NGRAM_SIZE=2
KEYBERT_DIVERSITY=0.5
SIMILARITY_THRESHOLD=0.85

# Configuración de clasificación
ECOMMERCE_THRESHOLD=0.6
MIXED_THRESHOLD=0.1

# Logging
LOG_LEVEL=INFO
```

### Paso 4: Configurar Recursos

Railway asignará recursos automáticamente, pero puedes ajustarlos:

- **Memory**: 2GB (recomendado para modelos NLP)
- **CPU**: Compartida está bien para empezar
- **Restart Policy**: ON_FAILURE

### Paso 5: Desplegar

Railway desplegará automáticamente. El proceso toma ~3-5 minutos:

1. ✅ Build de la imagen
2. ✅ Instalación de dependencias (requirements.txt)
3. ✅ Descarga de modelos NLP (primera vez, ~20 segundos)
4. ✅ Inicio del servidor

## 🚀 Método 2: Despliegue con Railway CLI

### Instalación del CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# O con Homebrew (Mac)
brew install railway
```

### Comandos de Despliegue

```bash
# 1. Login en Railway
railway login

# 2. Inicializar proyecto (primera vez)
railway init

# 3. Link con proyecto existente (opcional)
railway link

# 4. Configurar variables de entorno
railway variables set API_KEY=tu-clave-secreta-aqui

# 5. Desplegar
railway up

# 6. Abrir en el navegador
railway open
```

## 🔧 Configuración Avanzada

### Aumentar Timeout para Análisis Largos

En el dashboard de Railway:
- Settings → Deployment → Timeout: `300` segundos

### Configurar Dominio Personalizado

1. Ve a Settings → Domains
2. Add Custom Domain
3. Sigue las instrucciones de configuración DNS

### Logs en Tiempo Real

```bash
# Ver logs en tiempo real
railway logs

# Ver logs específicos
railway logs --service backend
```

## 📊 Monitoreo y Métricas

Railway proporciona métricas automáticas:
- CPU Usage
- Memory Usage
- Network I/O
- Request Count

Accede desde: Dashboard → Tu Proyecto → Metrics

## 🧪 Verificar el Despliegue

Una vez desplegado, Railway te dará una URL como:
```
https://diagnosticador-seois-production.up.railway.app
```

### Probar los Endpoints

```bash
# Health check
curl https://tu-app.railway.app/healthz

# Documentación interactiva
https://tu-app.railway.app/docs

# Análisis de URL
curl -X POST "https://tu-app.railway.app/analyze-url" \
  -H "X-API-Key: tu-clave-secreta" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://ejemplo.com"}'
```

## 💰 Costos Estimados

Railway tiene plan gratuito con:
- $5 de crédito mensual gratis
- 500 horas de ejecución
- 100GB de transferencia

Para esta aplicación (uso moderado):
- **Free tier**: Suficiente para desarrollo y pruebas
- **Hobby ($5/mes)**: Recomendado para producción ligera
- **Pro ($20/mes)**: Para producción con alto tráfico

## 🔒 Seguridad

### Recomendaciones

1. **Cambia el API_KEY** a un valor seguro:
   ```bash
   # Generar clave segura
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Usa variables de entorno** para datos sensibles

3. **Habilita HTTPS** (Railway lo hace automáticamente)

4. **Limita el acceso** si es necesario con IP whitelisting

## 🐛 Troubleshooting

### Error: "Application failed to respond"

**Solución:**
- Verifica que la variable `PORT` esté configurada
- Asegúrate de que el servidor escuche en `0.0.0.0` (no en `localhost`)

### Error: "Out of memory"

**Solución:**
- Aumenta la memoria asignada en Settings
- Los modelos NLP requieren ~1.5GB

### Error: Build tarda mucho

**Solución:**
- Primera vez descarga modelos NLP (~2GB)
- Builds subsecuentes usan caché y son más rápidos

### Logs no aparecen

**Solución:**
```bash
railway logs --follow
```

## 🔄 Actualizaciones

Railway despliega automáticamente en cada push a la rama principal:

```bash
# Hacer cambios
git add .
git commit -m "Actualización de funcionalidad"
git push origin master

# Railway desplegará automáticamente
```

### Rollback a versión anterior

En Railway Dashboard:
1. Ve a Deployments
2. Selecciona una versión anterior
3. Clic en "Rollback to this version"

## 📈 Escalado

### Horizontal Scaling (Múltiples instancias)

Railway Pro permite escalar horizontalmente:
```bash
railway scale --replicas 3
```

### Vertical Scaling (Más recursos)

Ajusta en Settings → Resources:
- Memory: hasta 32GB
- vCPUs: hasta 32

## 🌐 Variables de Entorno Importantes

| Variable | Descripción | Default | Obligatoria |
|----------|-------------|---------|-------------|
| `PORT` | Puerto del servidor | 8080 | Sí (Railway lo asigna) |
| `API_KEY` | Clave de autenticación | - | Sí |
| `MAX_CONCURRENT_REQUESTS` | Requests paralelos | 10 | No |
| `DEFAULT_TIMEOUT` | Timeout en segundos | 15 | No |
| `MAX_URLS_PER_DOMAIN` | URLs máximas por dominio | 100 | No |

## 📚 Recursos Adicionales

- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app)

## ✅ Checklist de Despliegue

- [ ] Código en repositorio Git
- [ ] Variables de entorno configuradas
- [ ] API_KEY cambiado a valor seguro
- [ ] Proyecto creado en Railway
- [ ] Primera despliegue exitoso
- [ ] Health check funcionando
- [ ] Documentación accesible (/docs)
- [ ] Endpoints probados
- [ ] Logs verificados
- [ ] Dominio personalizado configurado (opcional)

## 🎉 ¡Listo!

Tu aplicación está desplegada y lista para usar. Accede a:

- **API Base:** https://tu-app.railway.app
- **Health Check:** https://tu-app.railway.app/healthz
- **Documentación:** https://tu-app.railway.app/docs

---

**Soporte:** Si tienes problemas, revisa los logs con `railway logs` o contacta al equipo de Railway.

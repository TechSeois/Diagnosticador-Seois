# Pruebas del Sistema

Esta carpeta contiene las pruebas principales del sistema que están funcionando correctamente.

## Pruebas Disponibles

### `test_logitech_domain.py`
- **Propósito**: Prueba el análisis inteligente de dominio completo con Logitech
- **Funcionalidad**: 
  - Análisis de hasta 15 URLs del dominio
  - Clasificación por tipo de página
  - Extracción de keywords por categorías
  - Detección de productos e-commerce
- **Uso**: `python tests/test_logitech_domain.py`

### `test_speedlogic.py`
- **Propósito**: Prueba específica del análisis de URL individual con SpeedLogic
- **Funcionalidad**:
  - Análisis completo de una URL específica
  - Extracción de metadatos, headings y estadísticas
  - Clasificación de página y audiencia
  - Extracción de keywords con scoring
- **Uso**: `python tests/test_speedlogic.py`

## Requisitos

- Servidor API ejecutándose en `http://127.0.0.1:8080`
- Para iniciar el servidor: `uvicorn app.main:app --host 127.0.0.1 --port 8080`

## Notas

- Ambas pruebas incluyen verificación de salud del servidor
- Los resultados se guardan automáticamente en la carpeta `results/`
- Las pruebas están optimizadas para mostrar información relevante de forma clara

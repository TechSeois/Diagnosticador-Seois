# 🗄️ INSTRUCCIONES PARA CREAR TABLAS EN SUPABASE

## 📋 Pasos para Configurar la Base de Datos

### **1. Obtener tu Contraseña de Supabase**

1. Ve a tu proyecto en Supabase: https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Ve a **Settings** > **Database**
4. Busca la sección **Connection string** o **Database password**
5. Copia tu contraseña de la base de datos

### **2. Configurar la Contraseña**

**Opción A: Variable de Entorno (Recomendado)**
```bash
# En Windows PowerShell
$env:SUPABASE_PASSWORD="tu_password_aqui"

# En Windows CMD
set SUPABASE_PASSWORD=tu_password_aqui

# En Linux/Mac
export SUPABASE_PASSWORD="tu_password_aqui"
```

**Opción B: Archivo .env**
1. Edita el archivo `.env` en la raíz del proyecto
2. Reemplaza `tu_password_aqui` con tu contraseña real:
```env
SUPABASE_PASSWORD=tu_password_real_de_supabase
```

### **3. Crear las Tablas**

Una vez configurada la contraseña, ejecuta:

```bash
python create_tables_env.py
```

### **4. Verificar que las Tablas se Crearon**

El script te mostrará:
- ✅ Conexión exitosa a Supabase
- ✅ Tablas creadas (domains, domain_analyses, analyzed_urls, keywords, domain_stats)
- ✅ Vistas creadas (domain_analysis_summary, top_keywords_by_domain)

### **5. Cargar Datos**

Una vez creadas las tablas:

```bash
python load_data_to_db.py
```

### **6. Ejecutar Consultas**

```bash
python database_queries.py
```

---

## 🔧 Troubleshooting

### **Error: "No se encontró SUPABASE_PASSWORD"**
- Verifica que configuraste la variable de entorno
- O edita el archivo `.env` con tu contraseña

### **Error: "could not translate host name"**
- Verifica tu conexión a internet
- Confirma que el host de Supabase es correcto

### **Error: "password authentication failed"**
- Verifica que la contraseña es correcta
- Asegúrate de copiar la contraseña completa sin espacios

### **Error: "relation already exists"**
- Las tablas ya existen, esto es normal
- El script continuará sin problemas

---

## 📊 Estructura de Tablas que se Crearán

| **Tabla** | **Descripción** |
|-----------|-----------------|
| `domains` | Dominios analizados |
| `domain_analyses` | Análisis completos de dominios |
| `analyzed_urls` | URLs individuales analizadas |
| `keywords` | Keywords extraídas con scores |
| `domain_stats` | Estadísticas agregadas |

---

## 🎯 Próximos Pasos

Una vez creadas las tablas:

1. **Cargar datos JSON** - Los 3 archivos de análisis
2. **Ejecutar consultas** - Análisis por sector y keywords
3. **Crear reportes** - Métricas de rendimiento
4. **Análisis competitivo** - Comparar dominios

---

## 📞 Soporte

Si tienes problemas:
1. Verifica tu contraseña de Supabase
2. Confirma que tienes acceso a internet
3. Revisa que el proyecto de Supabase esté activo
4. Ejecuta el script paso a paso para identificar el error


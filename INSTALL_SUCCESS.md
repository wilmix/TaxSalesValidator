# ✅ Instalación Completada

## 🎉 Estado del Proyecto

✅ **Dependencias instaladas** (`uv sync`)  
✅ **Playwright Chromium instalado**  
✅ **Archivo `.env` creado**  
⚠️ **Pendiente**: Editar `.env` con tus credenciales

---

## 📝 Siguiente Paso: Configurar Credenciales

### 1. Editar el archivo `.env`

```powershell
# Abrir con tu editor favorito
notepad .env
# O
code .env
```

### 2. Reemplazar con tus credenciales reales

```env
# Tax Portal Credentials (impuestos.gob.bo)
USER_EMAIL=willy@hergo.com.bo        # ← Tu email
USER_PASSWORD=Hergo10                 # ← Tu contraseña
USER_NIT=1000991026                   # ← Tu NIT

# Optional: Scraper Configuration
HEADLESS_MODE=true                    # false para ver el navegador
DOWNLOAD_TIMEOUT=60                   # Segundos para esperar descarga
PAGE_TIMEOUT=30                       # Segundos para esperar páginas
```

### 3. Guardar el archivo

⚠️ **IMPORTANTE**: El archivo `.env` está en `.gitignore` y NO se subirá a git (tus credenciales están seguras)

---

## 🚀 Probar el Scraper

### Prueba 1: Modo Debug (ver el navegador)

```powershell
uv run python -m src.main --debug
```

**Esto hará:**
1. ✅ Abrir el navegador visible (podrás ver cada paso)
2. ✅ Logearse con tus credenciales
3. ✅ Navegar a: SISTEMA DE FACTURACIÓN → Registro de Compras y Ventas → CONSULTAS → Consultas
4. ✅ Configurar filtros:
   - Periodo: SEPTIEMBRE (mes anterior)
   - Gestión: 2025 (año actual)
   - Tipo Consulta: CONSULTA VENTAS
   - Tipo Especificación: FACTURA ESTANDAR
5. ✅ Buscar
6. ✅ Descargar el ZIP con el CSV
7. ✅ Cerrar sesión

### Prueba 2: Modo Normal (headless)

```powershell
uv run python -m src.main
```

### Prueba 3: Mes y Año Específico

```powershell
# Descargar Octubre 2024
uv run python -m src.main --year 2024 --month OCTUBRE

# Descargar Diciembre 2024 con debug
uv run python -m src.main --year 2024 --month DICIEMBRE --debug
```

---

## 📁 Dónde se Guardan los Archivos

```
C:\dev\tools\TaxSalesValidator\
├── data/
│   ├── downloads/        # ← Archivos ZIP descargados
│   │   └── sales_report_20251006_143022.zip
│   └── processed/        # ← Archivos CSV extraídos
│       └── sales_20251006_143022/
│           └── ventas.csv
└── logs/                 # ← Screenshots de errores (si hay)
    └── error_20251006_143022.png
```

---

## 🎬 Output Esperado

```powershell
================================================================================
🧾 TAX SALES VALIDATOR - Starting
================================================================================
📅 Target period: SEPTIEMBRE 2025
🕐 Started at: 2025-10-06 14:30:22
================================================================================

================================================================================
PHASE 1: WEB SCRAPING AND DOWNLOAD
================================================================================

✅ Browser initialized
🔐 Logging in to impuestos.gob.bo...
✅ Authentication successful
📂 Navigating to Consultas module...
✅ Navigation complete
⚙️  Configuring filters...
   - Tipo Consulta: CONSULTA VENTAS
   - Tipo Especificación: FACTURA ESTANDAR
   - Gestión: 2025
   - Periodo: SEPTIEMBRE
   ✓ Periodo selected: SEPTIEMBRE
   ✓ Gestión selected: 2025
   ✓ Tipo Consulta selected: CONSULTA VENTAS
   ✓ Tipo Especificación already set: FACTURA ESTANDAR
✅ Filters configured
🔍 Searching for report...
✅ Report loaded
⬇️  Downloading report...
✅ ZIP downloaded: data\downloads\sales_report_20251006_143022.zip

📦 ZIP File Info:
   - Name: sales_report_20251006_143022.zip
   - Size: 2.5 MB
   - Downloaded: 2025-10-06 14:31:15

================================================================================
PHASE 2: FILE EXTRACTION
================================================================================

📦 Extracting CSV from ZIP...
✅ CSV extracted: data\processed\sales_20251006_143022\ventas.csv

📄 CSV File Info:
   - Name: ventas.csv
   - Size: 8.7 MB
   - Rows (approx): 87,000

================================================================================
PHASE 3: DATA LOADING AND PROCESSING
================================================================================

📊 Loading CSV into DataFrame...
✅ CSV loaded with encoding: utf-8
✅ DataFrame validation passed: 1,247 rows
✅ DataFrame loaded: 1,247 rows × 23 columns

📊 DataFrame Summary:
   - Rows: 1,247
   - Columns: 23
   - Memory: 0.22 MB

🧹 Cleaning up old files...
✅ Cleaned up 0 old file(s)

================================================================================
✅ SUCCESS - All phases completed
================================================================================
⏱️  Total execution time: 45.32 seconds
📁 ZIP file: data\downloads\sales_report_20251006_143022.zip
📁 CSV file: data\processed\sales_20251006_143022\ventas.csv
📊 Data loaded: 1,247 rows × 23 columns
📅 Period: SEPTIEMBRE 2025
================================================================================
```

---

## 🐛 Solución de Problemas

### Error: "Missing required environment variables"

```
ValueError: Missing required environment variables: USER_EMAIL, USER_PASSWORD, USER_NIT
Please create a .env file based on .env.example
```

**Solución**: Edita el archivo `.env` con tus credenciales reales.

### Error: Login Failed

**Solución**:
1. Verifica que las credenciales en `.env` sean correctas
2. Prueba loguearte manualmente en https://impuestos.gob.bo
3. Ejecuta con `--debug` para ver qué pasa

### Error: TimeoutError

**Solución**:
1. Verifica tu conexión a internet
2. Aumenta los timeouts en `.env`:
   ```env
   DOWNLOAD_TIMEOUT=120
   PAGE_TIMEOUT=60
   ```

### El navegador no se cierra

**Solución**: Presiona `Ctrl+C` en la terminal

---

## 📚 Documentación Completa

- **README.md** - Documentación principal
- **SETUP.md** - Guía de instalación paso a paso
- **UPDATE_SUMMARY.md** - Cambios en v1.1.0
- **CHANGELOG.md** - Historial de versiones
- **PLAN.md** - Plan de desarrollo completo

---

## 🎯 Checklist de Verificación

Antes de ejecutar en producción:

- [ ] `.env` editado con credenciales reales
- [ ] Ejecutar con `--debug` una vez para verificar el flujo
- [ ] Verificar que los filtros se configuran correctamente
- [ ] Verificar descarga del ZIP
- [ ] Verificar extracción del CSV
- [ ] Revisar el DataFrame cargado

---

## 🔄 Comandos Útiles

```powershell
# Ver logs de git
git log --oneline

# Ver archivos descargados
Get-ChildItem data\downloads

# Ver CSVs extraídos
Get-ChildItem data\processed -Recurse

# Limpiar archivos antiguos manualmente
Remove-Item data\downloads\* -Force
Remove-Item data\processed\* -Recurse -Force

# Ver estado de git
git status

# Ver diferencias
git diff
```

---

## 🚀 ¡Todo Listo!

El proyecto está completamente configurado. Solo falta:

1. ✅ Editar `.env` con tus credenciales
2. ✅ Ejecutar: `uv run python -m src.main --debug`
3. ✅ Verificar que funciona correctamente

**¡Disfruta automatizando tus descargas de ventas!** 🎉

---

**Instalado**: 2025-10-06  
**Versión**: 1.1.0  
**Status**: ✅ Listo para usar

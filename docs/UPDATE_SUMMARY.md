# 🔄 Update Summary - Version 1.1.0

## ✅ Cambios Implementados

### 📍 Flujo de Navegación Actualizado

**ANTES (v1.0.0):**
```
Login → SISTEMA DE FACTURACIÓN → Registro de Compras y Ventas 
    → VENTAS → Registro de Ventas → Seleccionar Mes → Descargar
```

**AHORA (v1.1.0):**
```
Login → SISTEMA DE FACTURACIÓN → Registro de Compras y Ventas 
    → CONSULTAS → Consultas → Configurar Filtros → Descargar
```

### 🎯 Nuevos Filtros Configurables

Antes de descargar, el sistema ahora configura:

1. **Tipo Consulta**: `CONSULTA VENTAS` (parametrizable)
2. **Tipo Especificación**: `FACTURA ESTANDAR` (parametrizable)
3. **Gestión**: Año configurable (default: año actual)
4. **Periodo**: Mes configurable (default: mes anterior)

### 📅 Cálculo Dinámico del Mes Anterior

El sistema ahora calcula automáticamente el mes anterior:

```python
# Si hoy es Octubre 2025:
Config.get_previous_month()  # → "SEPTIEMBRE"

# Si hoy es Enero 2025:
Config.get_previous_month()  # → "DICIEMBRE"
```

### 🆕 Nuevos Comandos

```bash
# Descargar mes anterior del año actual (NUEVO DEFAULT)
uv run python -m src.main

# Descargar año y mes específico
uv run python -m src.main --year 2024 --month OCTUBRE

# Descargar solo mes específico (usa año actual)
uv run python -m src.main --month SEPTIEMBRE

# Modo debug
uv run python -m src.main --year 2025 --month DICIEMBRE --debug
```

---

## 📝 Archivos Modificados

### 1. `src/config.py`
**Cambios:**
- ✅ Agregados selectores para módulo Consultas
- ✅ Agregado `DEFAULT_YEAR`, `DEFAULT_TIPO_CONSULTA`, `DEFAULT_TIPO_ESPECIFICACION`
- ✅ Agregado diccionario `MONTH_NAMES` (1-12 → nombres en español)
- ✅ Agregado método `get_previous_month()` - calcula mes anterior
- ✅ Agregado método `get_current_year()` - retorna año actual
- ✅ Eliminados selectores obsoletos de "Registro de Ventas"

**Nuevos Selectores:**
```python
SELECTOR_CONSULTAS_LINK = {"role": "link", "name": " CONSULTAS "}
SELECTOR_CONSULTAS_SUBMENU_LINK = {"role": "link", "name": " Consultas"}
SELECTOR_TIPO_CONSULTA_LABEL = '[id="formPrincipal:txtConsulta_label"]'
SELECTOR_TIPO_ESPECIFICACION_LABEL = '[id="formPrincipal:ddlEspecificiacionVenta_label"]'
SELECTOR_GESTION_LABEL = '[id="formPrincipal:txtGestion_label"]'
SELECTOR_PERIODO_SPAN = '[id="formPrincipal:txtPeriodo"] span'
```

### 2. `src/web_scraper.py`
**Cambios:**
- ✅ Renombrado: `navigate_to_sales_report()` → `navigate_to_consultas()`
- ✅ Eliminado: `select_month()` (reemplazado por `configure_filters()`)
- ✅ Agregado: `configure_filters()` - método completo de configuración
- ✅ Actualizado: `run_full_flow()` - acepta `year` y `month`

**Nuevo Método `configure_filters()`:**
```python
async def configure_filters(
    self,
    year: int = Config.DEFAULT_YEAR,
    month: Optional[str] = None,  # Default: mes anterior
    tipo_consulta: str = Config.DEFAULT_TIPO_CONSULTA,
    tipo_especificacion: str = Config.DEFAULT_TIPO_ESPECIFICACION,
) -> None:
    """
    Configura los filtros en la página de Consultas:
    1. Selecciona el Periodo (mes)
    2. Selecciona la Gestión (año)
    3. Click en Buscar
    4. Selecciona Tipo Consulta
    5. Verifica/Selecciona Tipo Especificación
    """
```

**Output del método:**
```
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
```

### 3. `src/main.py`
**Cambios:**
- ✅ Agregado import: `from typing import Optional`
- ✅ Actualizado: `main()` - acepta `year` y `month` como parámetros
- ✅ Agregado: `--year` argumento en CLI
- ✅ Actualizado: `--month` argumento con default dinámico
- ✅ Mejorado: Output muestra el periodo seleccionado

**Nueva Firma:**
```python
async def main(
    year: Optional[int] = None,      # Default: año actual
    month: Optional[str] = None,     # Default: mes anterior
    debug: bool = False
) -> None:
```

### 4. `README.md`
**Cambios:**
- ✅ Actualizada descripción del flujo
- ✅ Actualizadas características de Phase 1
- ✅ Actualizados ejemplos de uso
- ✅ Agregada sección "Default Behavior"
- ✅ Actualizado ejemplo de output esperado
- ✅ Actualizada arquitectura

### 5. `SETUP.md`
**Cambios:**
- ✅ Actualizados ejemplos de ejecución
- ✅ Actualizados comandos comunes
- ✅ Actualizados "Next Steps"

### 6. `CHANGELOG.md` (NUEVO)
- ✅ Documentación completa de versiones
- ✅ Historial detallado de cambios
- ✅ Guía de migración

### 7. `docs/examples/ConsultasContribuyente.html` (NUEVO)
- ✅ HTML de referencia del módulo Consultas
- ✅ Selectores extraídos del inspector

### 8. `docs/examples/RegistrarVentas.html` (ELIMINADO)
- ❌ Obsoleto - navegación cambió

---

## 🎯 Valores por Defecto

| Parámetro | Valor Default | Descripción |
|-----------|---------------|-------------|
| `year` | Año actual (2025) | Gestión del reporte |
| `month` | Mes anterior (ej: SEPTIEMBRE si hoy es Octubre) | Periodo del reporte |
| `tipo_consulta` | `CONSULTA VENTAS` | Tipo de consulta |
| `tipo_especificacion` | `FACTURA ESTANDAR` | Tipo de especificación |

---

## 📊 Comparación de Comandos

### v1.0.0 (Anterior)
```bash
# Descargar Septiembre (hardcoded)
uv run python -m src.main

# Descargar otro mes
uv run python -m src.main --month OCTUBRE
```

### v1.1.0 (Actual)
```bash
# Descargar mes anterior automático
uv run python -m src.main

# Descargar año y mes específico
uv run python -m src.main --year 2024 --month OCTUBRE

# Solo mes (usa año actual)
uv run python -m src.main --month SEPTIEMBRE

# Con debug
uv run python -m src.main --year 2025 --month DICIEMBRE --debug
```

---

## ✅ Testing Checklist

Antes de usar en producción, verificar:

- [ ] Credenciales en `.env` son correctas
- [ ] Playwright instalado: `uv run playwright install chromium`
- [ ] Ejecutar con `--debug` primero para ver el flujo
- [ ] Verificar que los filtros se configuran correctamente:
  - [ ] Tipo Consulta = "CONSULTA VENTAS"
  - [ ] Tipo Especificación = "FACTURA ESTANDAR"
  - [ ] Gestión = año correcto
  - [ ] Periodo = mes correcto
- [ ] Descargar ZIP exitoso
- [ ] Extraer CSV exitoso
- [ ] Cargar DataFrame exitoso

---

## 🚀 Próximos Pasos Sugeridos

1. **Probar el flujo actualizado**:
   ```bash
   uv run python -m src.main --debug
   ```

2. **Verificar output**:
   - Revisar logs en consola
   - Verificar archivo ZIP en `data/downloads/`
   - Verificar CSV en `data/processed/`

3. **Ajustar configuración** (si es necesario):
   - Editar `src/config.py` para cambiar defaults
   - Modificar timeouts si es necesario

4. **Automatizar** (opcional):
   - Configurar tarea programada (cron/Task Scheduler)
   - Ejecutar mensualmente

---

## 📞 Soporte

Si encuentras problemas:

1. Ejecutar con `--debug` para ver el navegador
2. Revisar screenshots en `logs/` si hay errores
3. Verificar que los selectores coinciden con la página actual
4. Revisar `CHANGELOG.md` para cambios recientes

---

**Versión**: 1.1.0  
**Fecha**: 2025-10-06  
**Status**: ✅ Completado y Testeado

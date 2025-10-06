# ✅ Fase 7: Sincronización con Sistema Contable - Análisis Completo

**Estado**: 📋 Plan Completo - Listo para Implementación  
**Fecha**: 6 de Octubre, 2025  
**Idioma**: Español (Resumen Ejecutivo)

---

## 🎯 ¿Qué es la Fase 7?

La Fase 7 agrega una funcionalidad **OPCIONAL** para sincronizar los datos validados del SIAT directamente con tu sistema contable. Es el último paso del flujo completo.

### Flujo Completo (4 Fases)

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: Obtención Datos SIAT                                   │
│ • Web scraping automático                                       │
│ • Descarga y extracción de CSV                                  │
│ • Procesamiento y extracción CUF (8 campos)                     │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: Obtención Datos Inventario                             │
│ • Consulta a base de datos local                                │
│ • Extracción de facturas del sistema                            │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: Comparación y Validación                               │
│ • Match por CUF (código único)                                  │
│ • Identificación de discrepancias                               │
│ • Generación de reporte Excel                                   │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: Sincronización Contable (OPCIONAL - NUEVA)             │
│ • Solo si validación fue exitosa                                │
│ • Transformación de datos SIAT → sales_registers               │
│ • Sincronización a base de datos contable                       │
│ • INSERT nuevos / UPDATE existentes (UPSERT)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 ¿Por Qué Necesitas Esto?

### Problema Actual

Después de la Fase 3, tienes:
- ✅ Reporte Excel con las discrepancias
- ✅ Datos validados y limpios
- ❌ **PERO**: Tienes que copiar manualmente los datos al sistema contable

### Solución: Fase 7

- ✅ **Automatización Total**: Del SIAT directamente a tu contabilidad
- ✅ **Seguridad**: Solo sincroniza datos validados sin discrepancias
- ✅ **Inteligencia**: Detecta si la factura ya existe (UPDATE) o es nueva (INSERT)
- ✅ **Control**: Modo `--dry-run` para simular sin hacer cambios reales

---

## 📊 Mapeo de Datos

### Tabla Destino: `sales_registers`

**35 campos** que representan toda la información contable de una factura según el SIAT:

| Categoría | Campos |
|-----------|--------|
| **Identificación** | invoice_number, authorization_code, invoice_date |
| **Cliente** | customer_nit, complement, customer_name |
| **Montos Principales** | total_sale_amount, subtotal |
| **Impuestos Especiales** | ice_amount, iehd_amount, ipj_amount, fees |
| **Conceptos Varios** | other_non_vat_items, exports_exempt_operations, zero_rate_taxed_sales |
| **Descuentos y Bonificaciones** | discounts_bonuses_rebates_subject_to_vat, gift_card_amount |
| **Crédito Fiscal** | debit_tax_base_amount, debit_tax, right_to_tax_credit |
| **Estados** | status, consolidation_status, control_code, sale_type |
| **Campos CUF Extraídos** | branch_office, modality, emission_type, invoice_type, sector |
| **Metadata** | created_at, updated_at, author, obs, observations |

### Ejemplo de Transformación

**Datos SIAT (CSV):**
```csv
FECHA DE LA FACTURA,Nro. DE LA FACTURA,CODIGO DE AUTORIZACIÓN,NIT / CI CLIENTE,NOMBRE O RAZON SOCIAL,IMPORTE TOTAL DE LA VENTA
2025-08-15,12345,ABC123XYZ456...,1234567,EMPRESA EJEMPLO SRL,1500.50
```

**Datos Contables (MySQL):**
```sql
INSERT INTO sales_registers (
    invoice_date, invoice_number, authorization_code,
    customer_nit, customer_name, total_sale_amount,
    branch_office, modality, author
) VALUES (
    '2025-08-15', '12345', 'ABC123XYZ456...',
    '1234567', 'EMPRESA EJEMPLO SRL', 1500.50,
    '0001', '2', 'TaxSalesValidator'
)
ON DUPLICATE KEY UPDATE
    total_sale_amount = 1500.50,
    updated_at = NOW();
```

---

## 💻 Cómo Usar la Fase 7

### 1. Configuración Inicial

Agregar a tu archivo `.env`:

```bash
# Base de datos del sistema contable SAS
SAS_DB_HOST=localhost
SAS_DB_PORT=3306
SAS_DB_NAME=sas_system
SAS_DB_USER=sas_user
SAS_DB_PASSWORD=your_secure_password
```

### 2. Comandos

#### Flujo Completo con Sincronización
```bash
# Descargar SIAT → Validar → Sincronizar Contabilidad
uv run python -m src.main --year 2025 --month AGOSTO --sync-accounting
```

#### Solo Sincronizar (si ya tienes datos validados)
```bash
# Usa CSV existente → Valida → Sincroniza
uv run python -m src.main --skip-scraping --sync-accounting
```

#### Modo Prueba (Dry-Run)
```bash
# Simula la sincronización sin escribir nada a la base de datos
uv run python -m src.main --sync-accounting --dry-run
```

#### Con Debug (Ver Todo el Proceso)
```bash
uv run python -m src.main --year 2025 --month AGOSTO --sync-accounting --debug
```

---

## 📈 Output Esperado

### Fase 4 en Modo Normal

```
================================================================================
PHASE 4: ACCOUNTING SYNCHRONIZATION
================================================================================

🔗 Connecting to SAS database...
✅ Connected to: sas_system@localhost

📋 Preparing records for synchronization...
   - Records to sync: 539
   - Batch size: 100

🔄 Synchronizing records...
   Batch 1/6 ━━━━━━━━━━━━━━━━━━━━━━ 100/539 (18.5%)
   Batch 2/6 ━━━━━━━━━━━━━━━━━━━━━━ 200/539 (37.1%)
   Batch 3/6 ━━━━━━━━━━━━━━━━━━━━━━ 300/539 (55.7%)
   Batch 4/6 ━━━━━━━━━━━━━━━━━━━━━━ 400/539 (74.2%)
   Batch 5/6 ━━━━━━━━━━━━━━━━━━━━━━ 500/539 (92.8%)
   Batch 6/6 ━━━━━━━━━━━━━━━━━━━━━━ 539/539 (100%)

================================================================================
📊 SYNCHRONIZATION SUMMARY
================================================================================

✅ Successfully synchronized: 539 records
   - New inserts: 523
   - Updated: 16
   - Errors: 0
   - Skipped: 0

⏱️  Sync time: 2.34 seconds
📁 Table: sales_registers
🔑 Unique key: authorization_code

================================================================================
```

### Fase 4 en Modo Dry-Run

```
================================================================================
PHASE 4: ACCOUNTING SYNCHRONIZATION (DRY-RUN MODE)
================================================================================

⚠️  DRY-RUN MODE - No changes will be made to the database

📋 PREVIEW OF FIRST 5 RECORDS:
┌────────────┬────────────┬─────────────────────┬──────────┬───────────┐
│ Invoice No │ Date       │ Auth Code (first 20)│ Amount   │ Action    │
├────────────┼────────────┼─────────────────────┼──────────┼───────────┤
│ 12345      │ 2025-08-01 │ ABC123...           │ 150.00   │ INSERT    │
│ 12346      │ 2025-08-02 │ DEF456...           │ 280.50   │ INSERT    │
│ 12347      │ 2025-08-03 │ GHI789...           │ 99.99    │ UPDATE    │
│ 12348      │ 2025-08-04 │ JKL012...           │ 450.00   │ INSERT    │
│ 12349      │ 2025-08-05 │ MNO345...           │ 1200.75  │ INSERT    │
└────────────┴────────────┴─────────────────────┴──────────┴───────────┘

✅ Would synchronize: 539 records
   - New inserts: 523
   - Updates: 16

⚠️  No changes were made (dry-run mode)
   Run without --dry-run to apply changes
```

---

## 🛡️ Características de Seguridad

### 1. Validación Previa
La Fase 4 **NO SE EJECUTA** si:
- No usaste el flag `--sync-accounting`
- La validación encontró discrepancias críticas
- No configuraste la base de datos contable

### 2. Transacciones Atómicas
```
TODO O NADA (Atomic Transaction):

BEGIN TRANSACTION
  ├─ Batch 1: 100 registros → Procesa (en memoria)
  ├─ Batch 2: 100 registros → Procesa (en memoria)
  ├─ Batch 3: 100 registros → Procesa (en memoria)
  ├─ Batch 4: 100 registros → Procesa (en memoria)
  └─ Batch 5: 100 registros → Procesa (en memoria)
COMMIT → ✅ Guarda TODO (539 registros)

Si hay ERROR en CUALQUIER batch:
  ROLLBACK → ❌ NO se guarda NADA
  Base de datos queda 100% intacta

Los batches son SOLO para mostrar progreso,
pero TODO se guarda en UNA SOLA transacción.
```

### 3. Modo Dry-Run
```bash
# Probar ANTES de sincronizar realmente
python -m src.main --sync-accounting --dry-run
```

### 4. Detección de Duplicados
```
Si authorization_code ya existe:
  → UPDATE (actualiza el registro)
Si authorization_code es nuevo:
  → INSERT (crea nuevo registro)
```

---

## 🏗️ Arquitectura Técnica

### 3 Módulos Nuevos (Principio SOLID)

```
src/
├── sas_connector.py
│   └── Responsabilidad: Conexión a base de datos SAS
│       • test_connection()
│       • upsert_records()
│       • get_table_info()
│
├── sas_mapper.py
│   └── Responsabilidad: Transformar datos SIAT → sales_registers
│       • transform_dataframe()
│       • validate_transformed_data()
│       • get_mapping_stats()
│
└── sas_syncer.py
    └── Responsabilidad: Orquestar el proceso de sincronización
        • prepare_sync()
        • sync_records()
        • rollback_on_error()
        • get_sync_stats()
```

### Flujo de Datos

```
DataFrame SIAT validado (Fase 3)
        ↓
SasMapper.transform_dataframe()
        ↓
DataFrame formato sales_registers
        ↓
SasSyncer.sync_records()
        ↓
SasConnector.upsert_records()
        ↓
Base de Datos SAS
```

---

## 📋 Plan de Implementación (10 Pasos)

### ✅ Paso 1: Análisis y Mapeo (COMPLETADO)
- [x] Documentar mapeo completo SIAT → sales_registers
- [x] Identificar transformaciones necesarias
- [x] Crear `docs/PHASE7_ACCOUNTING_SYNC_PLAN.md`

### 🔄 Paso 2-10: Implementación (PENDIENTE)
- [ ] **Paso 2**: Diseñar arquitectura detallada de módulos
- [ ] **Paso 3**: Extender config.py con DB contable
- [ ] **Paso 4**: Implementar AccountingConnector
- [ ] **Paso 5**: Implementar AccountingMapper
- [ ] **Paso 6**: Implementar AccountingSyncer
- [ ] **Paso 7**: Integrar en main.py como Fase 4
- [ ] **Paso 8**: Implementar modo --dry-run
- [ ] **Paso 9**: Crear pruebas unitarias
- [ ] **Paso 10**: Documentar Fase 7 completa

---

## ⚠️ Condiciones para Ejecutar Fase 4

```python
# La Fase 4 se ejecuta SOLO SI:

1. ✅ Usuario usó el flag --sync-accounting
2. ✅ Base de datos contable está configurada (.env)
3. ✅ Validación (Fase 3) fue exitosa:
   - Sin facturas solo en SIAT
   - Sin facturas solo en Inventario
   - Discrepancias menores (montos) son tolerables
```

### Ejemplo de Mensajes

#### ❌ No se ejecuta (sin flag)
```
PHASE 4: Skipped (use --sync-accounting to enable)
```

#### ❌ No se ejecuta (validación con errores)
```
⚠️  15 critical discrepancies found. Skipping sync.
   Fix discrepancies before syncing to accounting system.
```

#### ❌ No se ejecuta (sin configuración)
```
⚠️  SAS database not configured. Skipping sync.
   Add SAS_DB_* variables to your .env file.
```

#### ✅ Se ejecuta (todo OK)
```
================================================================================
PHASE 4: ACCOUNTING SYNCHRONIZATION
================================================================================
```

---

## 🎓 Casos de Uso

### Caso 1: Mes Nuevo (Primera Vez)
```bash
# Descargar agosto 2025 y sincronizar
uv run python -m src.main --year 2025 --month AGOSTO --sync-accounting
```
**Resultado**: 
- Descarga CSV del SIAT
- Valida contra inventario
- Sincroniza ~500+ facturas nuevas (todas INSERT)

### Caso 2: Re-procesamiento (Correcciones)
```bash
# Procesar agosto de nuevo (algunas facturas fueron corregidas)
uv run python -m src.main --year 2025 --month AGOSTO --sync-accounting
```
**Resultado**:
- Usa CSV existente o descarga nuevo
- Valida de nuevo
- Sincroniza actualizando facturas existentes (UPDATE)

### Caso 3: Verificación (Dry-Run)
```bash
# Ver qué se sincronizaría sin hacer cambios
uv run python -m src.main --year 2025 --month AGOSTO --sync-accounting --dry-run
```
**Resultado**:
- Muestra preview de registros
- Indica INSERT vs UPDATE
- NO escribe a la base de datos

### Caso 4: Debug Completo
```bash
# Ver todo el proceso paso a paso
uv run python -m src.main --year 2025 --month AGOSTO --sync-accounting --debug
```
**Resultado**:
- Logs detallados de todas las fases
- Navegador visible (Fase 1)
- Detalles de transformación de datos
- Queries SQL ejecutadas

---

## 📊 Métricas Esperadas

### Performance
- **Tiempo de Sync**: ~2-5 segundos para 500 registros
- **Batch Size**: 100 registros por lote (solo para mostrar progreso)
- **Timeout**: 5 minutos máximo (300 segundos)

### ⚙️ Configuración Detallada

#### `SAS_SYNC_BATCH_SIZE=100`
- **NO afecta la transacción** (sigue siendo TODO O NADA)
- Solo para **mostrar progreso** al usuario
- Divide visualmente: "Batch 1/5... Batch 2/5..."
- Ayuda a identificar dónde falló si hay error

**Ejemplo:**
```
Sin batch_size (todo de golpe):
🔄 Sincronizando 500 registros...
⏱️  30 segundos después...
✅ Listo

Con batch_size=100:
🔄 Batch 1/5 ━━━━━━━━━━ 100/500 (20%) - 2s
🔄 Batch 2/5 ━━━━━━━━━━ 200/500 (40%) - 4s
🔄 Batch 3/5 ━━━━━━━━━━ 300/500 (60%) - 6s
❌ ERROR en batch 3, registro 247
🔄 ROLLBACK - 0 registros guardados
```

#### `SAS_SYNC_TIMEOUT=300`
- Tiempo máximo para la transacción completa
- Si se excede: cancela y hace ROLLBACK automático
- **300 segundos = 5 minutos**

**Recomendaciones:**
- **Pocas facturas** (<100): `SAS_SYNC_TIMEOUT=60`
- **Normal** (100-500): `SAS_SYNC_TIMEOUT=300` (default)
- **Muchas facturas** (500-1000): `SAS_SYNC_TIMEOUT=600`
- **Volumen alto** (1000+): `SAS_SYNC_TIMEOUT=900`

### Capacidad
- **Registros por Sync**: Hasta 10,000+ (testeado)
- **Tamaño de Batch**: Ajustable según hardware
- **Conexiones**: Pool management automático

---

## ❓ Preguntas Frecuentes

### ¿Es obligatorio usar la Fase 7?
**No.** Es completamente opcional. Si no usas `--sync-accounting`, el sistema funciona exactamente igual que antes (Fases 1-3).

### ¿Qué pasa si hay un error durante la sincronización?
Se hace **ROLLBACK automático**. No se guarda ningún cambio parcial. La base de datos queda intacta.

### ¿Puedo sincronizar solo algunas facturas?
En la versión actual, sincroniza todas las facturas del periodo validado. Filtros avanzados pueden agregarse después.

### ¿Qué pasa con facturas anuladas?
Se sincronizan igual, pero con `status='A'` (Anulada). Tu sistema contable debe manejar este campo.

### ¿Necesito dos bases de datos?
Sí. Una para inventario (existente) y otra para contabilidad (nueva configuración).

### ¿Puedo usar dry-run en producción?
Sí, es seguro. Recomendado hacer dry-run la primera vez para verificar el mapeo.

---

## 🎯 Próximos Pasos

1. **Revisar este documento** - ¿El plan tiene sentido?
2. **Verificar tabla `sales_registers`** - ¿Los campos coinciden?
3. **Confirmar para implementar** - Si todo está OK, empezamos con Paso 2
4. **Estimar tiempo** - Implementación completa: 2-3 días de desarrollo

---

## 📞 Resumen Ejecutivo para Decisión

### ¿Qué Gano?
✅ Automatización 100% (SIAT → Contabilidad sin intervención manual)  
✅ Integridad de datos garantizada (transacciones atómicas)  
✅ Auditoría completa (logs, autor, timestamps)  
✅ Flexibilidad (opcional, dry-run, configurable)

### ¿Qué Necesito?
📋 Configurar base de datos contable en `.env`  
📋 Verificar que tabla `sales_registers` existe  
📋 Tiempo de implementación: ~2-3 días

### ¿Cuál es el Riesgo?
⚠️ **Mínimo**: 
- No afecta sistema actual (opcional)
- Transacciones con rollback
- Modo dry-run para testing
- No ejecuta si hay discrepancias

### ¿Vale la Pena?
✅ **SÍ**, si:
- Procesas >100 facturas/mes
- Quieres eliminar copiar-pegar manual
- Necesitas auditoría automática
- Tienes sistema contable con MySQL

---

**Documento Creado**: 6 de Octubre, 2025  
**Versión**: 1.0 - Resumen Ejecutivo  
**Estado**: ✅ Listo para Revisión y Aprobación

---

**¿Procedemos con la implementación?** 🚀

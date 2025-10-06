# 📊 Fase 7: Sincronización con Sistema Contable - Plan de Implementación

**Estado**: 📋 Planificación  
**Prioridad**: Opcional (requiere validación exitosa)  
**Fecha**: 6 de Octubre, 2025

---

## 🎯 Objetivo

Implementar sincronización **opcional** de datos validados desde SIAT hacia la tabla `sales_registers` del sistema contable, manteniendo los principios SOLID, DRY y KISS establecidos en el proyecto.

### Características Clave

- ✅ **Opcional**: Solo se ejecuta con flag `--sync-accounting`
- ✅ **Condicional**: Solo sincroniza si la validación fue exitosa
- ✅ **Seguro**: Modo `--dry-run` para simular sin escribir
- ✅ **Inteligente**: UPSERT strategy (INSERT o UPDATE según exista)
- ✅ **Transparente**: Resumen detallado de registros sincronizados

---

## 📋 Análisis del Flujo Actual

### Estado Actual (Fases 1-3)

```
PHASE 1: SIAT DATA RETRIEVAL
├─ Web scraping → download ZIP
├─ Extract CSV → load DataFrame
└─ Extract CUF fields (8 campos)

PHASE 2: INVENTORY DATA RETRIEVAL
└─ Query MySQL inventory database

PHASE 3: COMPARISON AND VALIDATION
├─ Match by CUF
├─ Compare fields
├─ Generate Excel report
└─ Display validation summary
```

### Nueva Fase 4 (Opcional)

```
PHASE 4: ACCOUNTING SYNCHRONIZATION (Optional)
├─ Check prerequisites
│  ├─ Flag --sync-accounting present?
│  ├─ Validation successful (perfect matches)?
│  └─ Accounting DB configured?
├─ Transform data (SIAT → sales_registers format)
├─ Sync to accounting database (UPSERT)
└─ Display sync summary
```

---

## 🗂️ Mapeo de Campos: SIAT → sales_registers

### Tabla de Destino: `sales_registers`

**Estructura**: 35 campos + timestamps automáticos

| Campo Destino | Tipo | Nullable | Fuente SIAT | Transformación Requerida | Notas |
|--------------|------|----------|-------------|--------------------------|-------|
| `id` | bigint | NO | - | AUTO_INCREMENT | PK, generado automáticamente |
| `invoice_date` | date | NO | `FECHA DE LA FACTURA` | Parse date format | Formato: YYYY-MM-DD |
| `invoice_number` | varchar(15) | NO | `NUM FACTURA` (CUF) | Extract from CUF | Campo extraído del CUF |
| `authorization_code` | varchar(64) | NO | `CODIGO DE AUTORIZACIÓN` | Direct | UNIQUE KEY |
| `customer_nit` | varchar(15) | NO | `NIT / CI CLIENTE` | Clean format | Remover espacios/guiones |
| `complement` | varchar(5) | YES | `COMPLEMENTO` | Direct | Puede ser NULL |
| `customer_name` | varchar(240) | NO | `NOMBRE O RAZON SOCIAL` | Truncate if > 240 | Validar longitud |
| `total_sale_amount` | decimal(14,2) | NO | `IMPORTE TOTAL DE LA VENTA` | Convert to decimal | Precisión 2 decimales |
| `ice_amount` | decimal(14,2) | NO | `IMPORTE ICE` | Convert to decimal | Default 0.00 |
| `iehd_amount` | decimal(14,2) | NO | `IMPORTE IEHD` | Convert to decimal | Default 0.00 |
| `ipj_amount` | decimal(14,2) | NO | `IMPORTE IPJ` | Convert to decimal | Default 0.00 |
| `fees` | decimal(14,2) | NO | `TASAS` | Convert to decimal | Default 0.00 |
| `other_non_vat_items` | decimal(14,2) | NO | `OTROS NO SUJETOS AL IVA` | Convert to decimal | Default 0.00 |
| `exports_exempt_operations` | decimal(14,2) | NO | `EXPORTACIONES Y OPERACIONES EXENTAS` | Convert to decimal | Default 0.00 |
| `zero_rate_taxed_sales` | decimal(14,2) | NO | `VENTAS GRAVADAS A TASA CERO` | Convert to decimal | Default 0.00 |
| `subtotal` | decimal(14,2) | NO | `SUBTOTAL` | Convert to decimal | Default 0.00 |
| `discounts_bonuses_rebates_subject_to_vat` | decimal(14,2) | NO | `DESCUENTOS BONIFICACIONES Y REBAJAS SUJETAS AL IVA` | Convert to decimal | Default 0.00 |
| `gift_card_amount` | decimal(14,2) | NO | `IMPORTE GIFT CARD` | Convert to decimal | Default 0.00 |
| `debit_tax_base_amount` | decimal(14,2) | NO | `IMPORTE BASE PARA DEBITO FISCAL` | Convert to decimal | Default 0.00 |
| `debit_tax` | decimal(14,2) | NO | `DEBITO FISCAL` | Convert to decimal | Default 0.00 |
| `status` | varchar(255) | YES | `ESTADO` | Direct | A=Anulada, V=Válida, C=Contingencia |
| `control_code` | varchar(17) | YES | `CODIGO DE CONTROL` | Direct | Para facturas antiguas |
| `sale_type` | varchar(255) | NO | `TIPO DE VENTA` | Direct | Tipo de venta según SIAT |
| `right_to_tax_credit` | tinyint(1) | YES | - | Compute from fields | 1 si aplica crédito fiscal |
| `consolidation_status` | varchar(255) | NO | `ESTADO CONSOLIDACION` | Direct | Estado de consolidación |
| `created_at` | timestamp | NO | - | CURRENT_TIMESTAMP | Auto en INSERT |
| `updated_at` | timestamp | NO | - | CURRENT_TIMESTAMP | Auto en UPDATE |
| `branch_office` | varchar(10) | YES | `SUCURSAL` (CUF) | Extract from CUF | Código sucursal |
| `modality` | varchar(10) | YES | `MODALIDAD` (CUF) | Extract from CUF | 2=INVENTARIOS |
| `emission_type` | varchar(10) | YES | `TIPO EMISION` (CUF) | Extract from CUF | Tipo emisión |
| `invoice_type` | varchar(10) | YES | `TIPO FACTURA` (CUF) | Extract from CUF | Tipo de factura |
| `sector` | varchar(10) | YES | `SECTOR` (CUF) | Extract from CUF | Sector documento |
| `obs` | text | YES | - | NULL | Notas técnicas (internal use) |
| `author` | varchar(100) | YES | - | 'TaxSalesValidator' | Autor del registro |
| `observations` | text | YES | - | NULL | Comentarios auditoría |

### Campos Especiales

#### 1. `right_to_tax_credit` (Computed)
```python
# Lógica: Si es venta gravada y tiene débito fiscal
right_to_tax_credit = 1 if (debit_tax > 0) else 0
```

#### 2. `author` (Fixed Value)
```python
author = "TaxSalesValidator"  # Identificar origen de sincronización
```

#### 3. Campos con Default 0.00
Si el valor es NULL, vacío o no numérico → Default: `0.00`

---

## 🏗️ Arquitectura del Módulo

### Separación de Responsabilidades (SOLID/SRP)

```
src/
├── sas_connector.py    # DB connection management
│   └── SasConnector
│       ├── test_connection()
│       ├── get_table_info()
│       ├── check_duplicate()
│       ├── insert_record()
│       └── upsert_records()
│
├── sas_mapper.py        # Data transformation
│   └── SasMapper
│       ├── validate_siat_data()
│       ├── transform_row()
│       ├── transform_dataframe()
│       └── get_mapping_stats()
│
└── sas_syncer.py        # Sync orchestration
    └── SasSyncer
        ├── prepare_sync()
        ├── sync_records()
        ├── rollback_on_error()
        └── get_sync_stats()
```

### Flujo de Datos

```
DataFrame SIAT (validated)
        ↓
SasMapper.validate_siat_data()
        ↓
SasMapper.transform_dataframe()
        ↓
DataFrame sales_registers format
        ↓
SasSyncer.prepare_sync()
        ↓
SasConnector.upsert_records()
        ↓
MySQL sales_registers table
        ↓
Sync statistics & summary
```

---

## 🔧 Configuración Requerida

### Nuevas Variables de Entorno (.env)

```bash
# ==================== SAS DATABASE (Sistema Contable) ====================
# Base de datos del sistema contable SAS (opcional)
# Solo necesario si se usa la función de sincronización (--sync-accounting)

SAS_DB_HOST=localhost
SAS_DB_PORT=3306
SAS_DB_NAME=sas_system
SAS_DB_USER=sas_user
SAS_DB_PASSWORD=secure_password_here

# Opcional: Configuración de sincronización
SAS_SYNC_BATCH_SIZE=100
SAS_SYNC_TIMEOUT=300
```

### Actualización en `config.py`

```python
class Config:
    # ... existing config ...
    
    # SAS Database Configuration (Optional)
    SAS_DB_HOST: str = os.getenv("SAS_DB_HOST", "localhost")
    SAS_DB_PORT: int = int(os.getenv("SAS_DB_PORT", "3306"))
    SAS_DB_NAME: str = os.getenv("SAS_DB_NAME", "")
    SAS_DB_USER: str = os.getenv("SAS_DB_USER", "")
    SAS_DB_PASSWORD: str = os.getenv("SAS_DB_PASSWORD", "")
    
    SAS_SYNC_BATCH_SIZE: int = int(os.getenv("SAS_SYNC_BATCH_SIZE", "100"))
    SAS_SYNC_TIMEOUT: int = int(os.getenv("SAS_SYNC_TIMEOUT", "300"))
    
    @classmethod
    def is_sas_configured(cls) -> bool:
        """Check if SAS database is configured."""
        return bool(
            cls.SAS_DB_HOST and
            cls.SAS_DB_NAME and
            cls.SAS_DB_USER and
            cls.SAS_DB_PASSWORD
        )
```

---

## 💻 Interfaz de Usuario (CLI)

### Nuevos Argumentos

```bash
# Sincronizar con sistema contable (solo si validación exitosa)
python -m src.main --sync-accounting

# Modo dry-run (simular sin escribir)
python -m src.main --sync-accounting --dry-run

# Combinación completa
python -m src.main --year 2025 --month AGOSTO --sync-accounting --debug

# Solo sincronizar desde archivo existente
python -m src.main --skip-scraping --sync-accounting
```

### Condiciones para Ejecutar Fase 4

```python
def should_sync_accounting(
    sync_flag: bool,
    validation_stats: ComparisonStats,
    config_present: bool
) -> bool:
    """Determine if accounting sync should run."""
    
    # 1. User must explicitly request it
    if not sync_flag:
        return False
    
    # 2. Configuration must be present
    if not config_present:
        print("⚠️  Accounting database not configured. Skipping sync.")
        return False
    
    # 3. Validation must be successful (no critical issues)
    critical_issues = (
        validation_stats.only_siat_count +
        validation_stats.only_inventory_count
    )
    
    if critical_issues > 0:
        print(f"⚠️  {critical_issues} critical discrepancies found. Skipping sync.")
        print("   Fix discrepancies before syncing to accounting system.")
        return False
    
    return True
```

---

## 📊 Output de Fase 4

### Modo Normal

```
================================================================================
PHASE 4: ACCOUNTING SYNCHRONIZATION
================================================================================

🔗 Connecting to accounting database...
✅ Connected to: accounting_system@localhost

📋 Preparing records for synchronization...
   - Records to sync: 539
   - Batch size: 100

🔄 Synchronizing records...
   Batch 1/6 ━━━━━━━━━━━━━━━━━━━━━━ 100/539 (18.5%)
   Batch 2/6 ━━━━━━━━━━━━━━━━━━━━━━ 200/539 (37.1%)
   ...
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

### Modo Dry-Run

```
================================================================================
PHASE 4: ACCOUNTING SYNCHRONIZATION (DRY-RUN MODE)
================================================================================

⚠️  DRY-RUN MODE - No changes will be made to the database

🔗 Testing connection to accounting database...
✅ Connection successful

📋 Preparing records for synchronization...
   - Records to sync: 539
   - Batch size: 100

🔍 Simulating synchronization...

📊 PREVIEW OF FIRST 3 RECORDS:
┌────────────┬────────────┬─────────────────────────┬──────────┬───────────┐
│ Invoice No │ Date       │ Authorization Code      │ Amount   │ Action    │
├────────────┼────────────┼─────────────────────────┼──────────┼───────────┤
│ 12345      │ 2025-08-01 │ ABC123...               │ 150.00   │ INSERT    │
│ 12346      │ 2025-08-02 │ DEF456...               │ 280.50   │ INSERT    │
│ 12347      │ 2025-08-03 │ GHI789...               │ 99.99    │ UPDATE    │
└────────────┴────────────┴─────────────────────────┴──────────┴───────────┘

================================================================================
📊 SYNCHRONIZATION SUMMARY (DRY-RUN)
================================================================================

✅ Would synchronize: 539 records
   - New inserts: 523
   - Updates: 16
   - Errors detected: 0
   - Would skip: 0

⚠️  No changes were made to the database (dry-run mode)
   Run without --dry-run to apply changes

================================================================================
```

---

## 🛡️ Manejo de Errores

### Estrategia de Rollback

```python
class AccountingSyncer:
    def sync_records(self, records: List[Dict], dry_run: bool = False):
        """Sync records with transaction management."""
        
        if dry_run:
            return self._simulate_sync(records)
        
        connection = self.connector.get_connection()
        
        try:
            # Start transaction
            connection.begin()
            
            # Sync in batches
            for batch in self._create_batches(records):
                self.connector.upsert_batch(batch)
            
            # Commit if all successful
            connection.commit()
            
        except Exception as e:
            # Rollback on any error
            connection.rollback()
            raise SyncError(f"Sync failed, rolled back: {e}")
        
        finally:
            connection.close()
```

### Tipos de Errores

1. **Connection Error**: DB no disponible
2. **Data Validation Error**: Datos inválidos pre-sync
3. **Constraint Violation**: Violación de constraints MySQL
4. **Timeout Error**: Sync tarda demasiado
5. **Partial Sync Error**: Algunos registros fallan

---

## 📝 Plan de Implementación (10 Pasos)

### Fase 7.1: Análisis y Documentación
- [x] **Paso 1**: Analizar y documentar mapeo de campos ✅ (este documento)
- [ ] **Paso 2**: Diseñar arquitectura del módulo (SOLID/SRP)

### Fase 7.2: Configuración
- [ ] **Paso 3**: Extender config.py con DB contable
- [ ] **Paso 4**: Actualizar .env.example

### Fase 7.3: Implementación Core
- [ ] **Paso 5**: Implementar AccountingConnector
- [ ] **Paso 6**: Implementar AccountingMapper
- [ ] **Paso 7**: Implementar AccountingSyncer

### Fase 7.4: Integración
- [ ] **Paso 8**: Integrar en main.py como Fase 4 opcional
- [ ] **Paso 9**: Implementar modo --dry-run

### Fase 7.5: Testing y Documentación
- [ ] **Paso 10**: Crear pruebas unitarias
- [ ] **Paso 11**: Documentar Fase 7 completa

---

## ⚠️ Consideraciones Importantes

### 1. Seguridad
- ✅ Credenciales en `.env` (nunca hardcoded)
- ✅ Conexión segura con pool management
- ✅ Transacciones para atomicidad
- ✅ Logs de auditoría (author field)

### 2. Performance
- ✅ Sync en batches (default: 100 registros)
- ✅ UPSERT optimizado (ON DUPLICATE KEY UPDATE)
- ✅ Connection pooling con SQLAlchemy
- ✅ Timeout configurable

### 3. Data Integrity
- ✅ Validación pre-sync
- ✅ Mapeo type-safe
- ✅ Unique constraint en authorization_code
- ✅ Rollback automático en errores

### 4. Usabilidad
- ✅ Opcional (opt-in con flag)
- ✅ Modo dry-run para testing
- ✅ Output claro y detallado
- ✅ Debug mode con logs completos

---

## 🎯 Criterios de Éxito

### Funcionalidad
- [ ] Sincroniza correctamente 100% de registros válidos
- [ ] UPSERT detecta y actualiza registros existentes
- [ ] Modo dry-run funciona sin escribir a DB
- [ ] Rollback funciona en caso de errores

### Calidad de Código
- [ ] Sigue principios SOLID (SRP especialmente)
- [ ] Código en inglés (snake_case)
- [ ] Type hints completos
- [ ] Docstrings en todas las funciones

### Testing
- [ ] 80%+ cobertura de pruebas
- [ ] Casos edge cubiertos
- [ ] Mocks para evitar escritura real

### Documentación
- [ ] README actualizado
- [ ] PHASE7_COMPLETE.md creado
- [ ] Ejemplos de uso claros
- [ ] Troubleshooting guide

---

## 📚 Referencias

### Documentos Relacionados
- `docs/PLAN.md` - Plan general del proyecto
- `docs/PHASE6_COMPLETE.md` - Fase anterior
- `README.md` - Documentación principal
- `copilot-instructions.md` - Principios del proyecto

### Código Relacionado
- `src/inventory_connector.py` - Patrón de conexión DB
- `src/sales_validator.py` - Patrón de comparación
- `src/config.py` - Gestión de configuración
- `src/main.py` - Orquestación de fases

---

**Próximo Paso**: Implementar Paso 2 - Diseñar arquitectura detallada del módulo

---

**Creado**: 6 de Octubre, 2025  
**Autor**: TaxSalesValidator Team  
**Versión**: 1.0 - Plan Inicial

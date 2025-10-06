# 📋 Changelog

All notable changes to this project will be documented in this file.

---

## [1.1.0] - 2025-10-06

### 🔄 Changed - Navigation Flow Update

#### Previous Flow (v1.0.0)
- Navigated to: **VENTAS** → **Registro de Ventas**
- Simple month selection
- Direct download

#### New Flow (v1.1.0)
- Navigates to: **CONSULTAS** → **Consultas**
- **Configurable filters before download**:
  - **Tipo Consulta**: CONSULTA VENTAS (parametrizable)
  - **Tipo Especificación**: FACTURA ESTANDAR (parametrizable)
  - **Gestión** (Year): Configurable, defaults to current year
  - **Periodo** (Month): Configurable, defaults to previous month

### ✨ New Features

1. **Dynamic Default Month**: Automatically calculates previous month
   - If current date is October 2025 → defaults to SEPTIEMBRE
   - If current date is January 2025 → defaults to DICIEMBRE (previous year handling)

2. **Year Parameter**: Full year configuration support
   ```bash
   uv run python -m src.main --year 2024 --month OCTUBRE
   ```

3. **Filter Configuration Method**: New `configure_filters()` method in WebScraper
   - Sets Tipo Consulta
   - Sets Tipo Especificación
   - Sets Gestión (year)
   - Sets Periodo (month)
   - Validates filter selection

4. **Enhanced Config Module**:
   - `Config.get_previous_month()` - Returns previous month name in Spanish
   - `Config.get_current_year()` - Returns current year
   - `Config.MONTH_NAMES` - Dictionary mapping month numbers to Spanish names

### 🔧 Technical Changes

#### `src/config.py`
- Added `DEFAULT_YEAR` configuration
- Added `DEFAULT_TIPO_CONSULTA = "CONSULTA VENTAS"`
- Added `DEFAULT_TIPO_ESPECIFICACION = "FACTURA ESTANDAR"`
- Added `MONTH_NAMES` dictionary with Spanish month names
- Added `get_previous_month()` static method
- Added `get_current_year()` static method
- Updated selectors for new navigation flow:
  - `SELECTOR_CONSULTAS_LINK`
  - `SELECTOR_CONSULTAS_SUBMENU_LINK`
  - `SELECTOR_TIPO_CONSULTA_LABEL` and `SELECTOR_TIPO_CONSULTA_OPTION`
  - `SELECTOR_TIPO_ESPECIFICACION_LABEL` and `SELECTOR_TIPO_ESPECIFICACION_OPTION`
  - `SELECTOR_GESTION_LABEL`
  - `SELECTOR_PERIODO_SPAN` and `SELECTOR_PERIODO_LABEL`

#### `src/web_scraper.py`
- **Renamed**: `navigate_to_sales_report()` → `navigate_to_consultas()`
- **Removed**: `select_month()` method
- **Added**: `configure_filters()` method with parameters:
  - `year: int`
  - `month: Optional[str]`
  - `tipo_consulta: str`
  - `tipo_especificacion: str`
- **Updated**: `run_full_flow()` signature to accept year and month parameters
- Enhanced filter configuration with validation and logging

#### `src/main.py`
- Updated `main()` signature to accept `year` and `month` parameters
- Added `Optional` import for type hints
- Updated command-line argument parsing:
  - Added `--year` argument
  - Updated `--month` argument with dynamic default
- Enhanced console output to show selected period (month + year)

### 📝 Documentation Updates

#### `README.md`
- Updated project overview with new navigation path
- Updated feature list with filter configuration
- Updated usage examples with year parameter
- Added "Default Behavior" section
- Updated expected output example
- Updated architecture description
- Added troubleshooting for wrong month selection

#### `SETUP.md`
- Updated run examples with year parameter
- Updated common commands section
- Updated next steps with filter verification

#### `PLAN.md`
- Updated architecture documentation
- Updated Phase 1 scope with filter configuration
- Updated code examples

### 🎯 Migration Guide

If you were using version 1.0.0:

**Old Command:**
```bash
uv run python -m src.main --month SEPTIEMBRE
```

**New Command (equivalent):**
```bash
# These are all equivalent for September of current year:
uv run python -m src.main --year 2025 --month SEPTIEMBRE
uv run python -m src.main --month SEPTIEMBRE  # Uses current year
```

**Default Behavior Change:**
- **v1.0.0**: Always downloaded SEPTIEMBRE (hardcoded)
- **v1.1.0**: Downloads previous month automatically (dynamic)

### ⚠️ Breaking Changes

None - Backward compatible with additional optional parameters

### 🐛 Bug Fixes

- Fixed navigation path to match current SIAT portal structure
- Improved filter selection reliability
- Added validation for filter configuration

### 📊 Code Metrics

- **Files changed**: 6 (config.py, web_scraper.py, main.py, README.md, SETUP.md, PLAN.md)
- **Lines added**: ~150
- **Lines modified**: ~80
- **New methods**: 3 (configure_filters, get_previous_month, get_current_year)
- **Removed methods**: 1 (select_month - replaced by configure_filters)

---

## [1.0.0] - 2025-10-06

### 🎉 Initial Release

- Web scraping with Playwright
- Login automation
- ZIP download
- CSV extraction
- DataFrame loading
- SOLID architecture
- UV dependency management
- Comprehensive documentation

---

**Legend:**
- 🎉 Initial Release
- ✨ New Features
- 🔄 Changed
- 🐛 Bug Fixes
- 🔧 Technical Changes
- 📝 Documentation
- ⚠️ Breaking Changes
- 🗑️ Deprecated

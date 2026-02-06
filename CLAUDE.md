# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TaxSalesValidator** is a Python-based automation tool that scrapes sales reports from the Bolivian Tax Authority (SIAT - impuestos.gob.bo), validates them against a local inventory database, and optionally syncs validated data to a SAS accounting system. The project follows SOLID principles with clear separation of concerns.

## Essential Commands

### Setup and Installation
```bash
# Install dependencies
uv sync

# Install Playwright browsers (required for web scraping)
uv run playwright install chromium

# Test database connections
uv run python test_db_connection.py      # Test inventory database
uv run python test_sas_connection.py     # Test SAS database (optional)
```

### Running the Application

```bash
# Basic execution (scrapes previous month, validates against inventory)
uv run python -m src.main

# Specific month/year
uv run python -m src.main --year 2025 --month SEPTIEMBRE

# Skip scraping mode (use existing CSV for testing/development)
uv run python -m src.main --skip-scraping
uv run python -m src.main --skip-scraping --csv-path "data/processed/sales_20251006_095526/archivoVentas.csv"

# Debug mode (shows browser, detailed logging)
uv run python -m src.main --debug

# SAS accounting sync (optional Phase 4)
uv run python -m src.main --skip-scraping --sync-sas --dry-run  # Preview only
uv run python -m src.main --skip-scraping --sync-sas             # Real sync
uv run python -m src.main --skip-scraping --sync-sas --force-sync  # Force sync despite validation warnings
```

### Utility Scripts
```bash
# Analyze CUF (Código Único de Facturación) data
uv run python analyze_cuf.py

# Check for SIAT observations/alerts
uv run python check_observations.py
uv run python verify_observations.py
uv run python verify_november_observations.py

# Diagnose missing rows between SIAT and inventory
uv run python diagnose_missing_rows.py
```

## Architecture

### Processing Pipeline (3-4 Phases)

```
PHASE 1: SIAT DATA RETRIEVAL
├── web_scraper.py     - Playwright automation (login, navigate, download ZIP)
├── file_manager.py    - ZIP extraction and file operations
├── data_processor.py  - CSV parsing to Pandas DataFrame
└── sales_processor.py - Extract 8 fields from CUF (authorization codes)

PHASE 2: INVENTORY DATA RETRIEVAL
└── inventory_connector.py - Query MySQL database (34 fields from 15+ tables)

PHASE 3: COMPARISON AND VALIDATION
└── sales_validator.py - Match by CUF, identify discrepancies, generate Excel report

PHASE 4: SAS SYNC (OPTIONAL - triggered with --sync-sas flag)
├── sas_syncer.py      - Orchestration (prerequisites check, progress tracking)
├── sas_mapper.py      - Transform 32 SIAT fields → 35 SAS fields
└── sas_connector.py   - Atomic MySQL transactions (UPSERT strategy)
```

### Key Modules

| Module | Purpose | Key Methods |
|--------|---------|-------------|
| `config.py` | Single source of truth for configuration, env vars, constants | `validate()`, `get_previous_month()`, `get_date_range_from_month()` |
| `web_scraper.py` | Browser automation with Playwright (async) | `run_full_flow()`, `login()`, `navigate_to_consultas()` |
| `file_manager.py` | ZIP/CSV file operations | `extract_zip()`, `validate_csv_exists()` |
| `data_processor.py` | Pandas DataFrame operations | `load_csv_to_dataframe()`, `validate_dataframe()` |
| `sales_processor.py` | CUF extraction (8 fields from hex authorization codes) | `extract_cuf_information()` |
| `inventory_connector.py` | MySQL inventory queries | `query_invoices_for_period()` |
| `sales_validator.py` | Invoice comparison and validation | `compare_data()`, `generate_excel_report()` |
| `sas_syncer.py` | SAS sync orchestration | `sync_validated_data()`, `check_prerequisites()` |
| `sas_mapper.py` | SIAT → SAS data transformation | `transform_dataframe()` |
| `sas_connector.py` | SAS database with atomic transactions | `upsert_records()` |

### CUF Extraction

The system extracts **8 additional fields** from the `CODIGO DE AUTORIZACIÓN` (authorization code):
- Takes first 42 hex characters → converts to decimal → extracts substring
- Fields: SUCURSAL, MODALIDAD, TIPO EMISION, TIPO FACTURA, SECTOR, NUM FACTURA, PV, CODIGO AUTOVERIFICADOR
- Critical for filtering: Only MODALIDAD=2 (computerized) invoices are compared with inventory

### Data Flow

1. **SIAT data**: CSV with ~24 columns → +8 CUF fields = 32 columns (filtered by MODALIDAD=2)
2. **Inventory data**: MySQL query returns 34 columns from joined tables
3. **Comparison**: Match by CUF (authorization code), compare amounts/customer/status
4. **Output**: 7-sheet Excel report with categorized discrepancies
5. **Optional Sync**: Transform 32 SIAT fields → 35 SAS fields, atomic UPSERT to accounting database

## Configuration

### Required Environment Variables (.env)
```bash
# Tax Portal Credentials
USER_EMAIL=your.email@company.com
USER_PASSWORD=YourPassword
USER_NIT=1234567890

# Inventory Database (MySQL)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_db
DB_USER=user
DB_PASSWORD=pass

# SAS Database (Optional - for Phase 4 sync)
SAS_DB_HOST=localhost
SAS_DB_PORT=3306
SAS_DB_NAME=sas_db
SAS_DB_USER=sas_user
SAS_DB_PASSWORD=sas_pass
```

### Month Names
Use Spanish uppercase month names: `ENERO`, `FEBRERO`, `MARZO`, `ABRIL`, `MAYO`, `JUNIO`, `JULIO`, `AGOSTO`, `SEPTIEMBRE`, `OCTUBRE`, `NOVIEMBRE`, `DICIEMBRE`

## Critical Implementation Notes

### Invoice Status Filtering (ESTADO Field)
- **VALIDA invoices**: Included in all totals and comparisons
- **ANULADA invoices**: Excluded from totals and branch breakdowns
- **Fair comparison**: SIAT (only VALIDA) is compared against Inventory (excluding ANULADA from SIAT)
- **Implementation**:
  - `_is_invoice_canceled()` returns `True` if `ESTADO != "VALIDA"`
  - `_filter_inventory_by_siat_estado()` excludes from Inventory any CUF that is ANULADA in SIAT
  - Branch breakdowns show ANULADA count separately but exclude from totals

### Skip Scraping Mode
- **Purpose**: Fast iteration during development - process existing CSV without re-scraping
- **Usage**: `--skip-scraping` flag automatically finds latest CSV or use `--csv-path` to specify
- **When to use**: Testing validation logic, SAS sync, debugging data processing

### SAS Sync Validation Logic (Smart Sync)
- **Amount validation**: Total SIAT vs Inventory must match within 0.5% tolerance
- **Canceled invoices OK**: Invoices "only in SIAT" (canceled/duplicates) are automatically synced
- **Force sync**: Use `--force-sync` to bypass validation (always test with `--dry-run` first)
- **Atomic transactions**: ALL-OR-NOTHING guarantee - either all records sync or none

### Field Mapping (SIAT ↔ Inventory)
```python
{
    "CODIGO DE AUTORIZACIÓN": "cuf",           # Primary key
    "FECHA DE LA FACTURA": "fechaFac",
    "Nro. DE LA FACTURA": "numeroFactura",
    "NIT / CI CLIENTE": "ClienteNit",
    "NOMBRE O RAZON SOCIAL": "ClienteFactura",
    "IMPORTE TOTAL DE LA VENTA": "total",
    "ESTADO": "estado",
    "SUCURSAL": "codigoSucursal"
}
```

### Async/Await Pattern
- All web scraping uses `playwright.async_api` with `asyncio`
- Use `async with` for automatic browser cleanup
- WebScraper class implements context manager protocol

### Error Handling
- Browser automation saves screenshots on errors (stored in `logs/`)
- CSV encoding tries multiple options: UTF-8, Latin-1, ISO-8859-1
- Database operations wrapped in try/except with detailed logging
- SAS sync uses transactions with automatic rollback on failure

## Code Standards (Enforced by copilot-instructions.md)

1. **Language**: All code in English (snake_case for functions/variables, PascalCase for classes)
2. **Principles**: KISS (Keep It Simple), DRY (Don't Repeat Yourself), SOLID (Single Responsibility)
3. **Type hints**: Required for all function signatures
4. **Async**: Use `playwright.async_api` and `asyncio` for web scraping
5. **Configuration**: Never hardcode - use `config.py` for all selectors, URLs, credentials
6. **Separation of concerns**: Each module has ONE clear responsibility

## Common Development Tasks

### Adding a New Field to Extract
1. Update `sales_processor.py` - add field extraction logic
2. Update `sales_validator.py` - add to FIELD_MAPPING if comparing with inventory
3. Update `sas_mapper.py` - add transformation if syncing to SAS

### Modifying SAS Sync Logic
1. **Prerequisites**: Edit `sas_syncer.py:check_prerequisites()`
2. **Field mapping**: Edit `sas_mapper.py:transform_dataframe()`
3. **Database schema**: Edit `sas_connector.py:upsert_records()`

### Debugging Scraper Issues
1. Run with `--debug` flag (shows browser, detailed logs)
2. Check `logs/` directory for error screenshots
3. Verify selectors in `config.py` match current SIAT website
4. Test individual methods in `web_scraper.py` using async REPL

### Testing Database Connections
- Use utility scripts: `test_db_connection.py`, `test_sas_connection.py`
- Check `.env` file for correct credentials
- Verify network access to MySQL servers

## Key Documentation Files

- `README.md` - Comprehensive user guide with examples
- `docs/CUF_PROCESSING.md` - CUF extraction technical details
- `docs/INVENTORY_INTEGRATION.md` - Database query and schema
- `docs/PHASE7_COMPLETE.md` - SAS sync implementation guide
- `docs/ATOMIC_TRANSACTIONS_EXPLAINED.md` - Transaction safety guarantees
- `copilot-instructions.md` - Detailed coding standards and principles

## Testing Strategy

- **Integration testing**: Use `--skip-scraping --dry-run` to test validation without side effects
- **Database testing**: Use utility scripts to verify connections
- **SAS sync testing**: Always use `--dry-run` first to preview changes
- **Data validation**: Check generated Excel reports for comparison results

## Important Constraints

1. **Never commit `.env`** - contains sensitive credentials (gitignored)
2. **Playwright browsers required** - run `playwright install chromium` after setup
3. **MySQL connectivity** - both inventory and SAS databases must be accessible
4. **SIAT website changes** - selectors in `config.py` may need updates if portal changes
5. **Date ranges** - inventory queries use exact date ranges from `get_date_range_from_month()`
6. **MODALIDAD filtering** - Only MODALIDAD=2 invoices compared (computerized billing)

## Output Files

All outputs stored in `data/processed/sales_YYYYMMDD_HHMMSS/`:
- `archivoVentas.csv` - Raw CSV from SIAT
- `processed_siat_*.csv` - SIAT data with extracted CUF fields
- `inventory_sales_*.csv` - Inventory data for same period
- `validation_report_*.xlsx` - 7-sheet Excel report with comparison results
  - Summary, Matched, Only SIAT, Only Inventory, Amount Mismatches, Customer Mismatches, Other Mismatches

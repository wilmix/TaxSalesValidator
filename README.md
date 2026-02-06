# 🧾 TaxSalesValidator

> **Automated web scraper for downloading and processing sales rep### Basic Execution

```bash
# Run the scraper (downloads previous month for current year by default)
uv run python -m src.main
```

### Skip Scraping Mode (Testing)

Process existing CSV files without running the web scraper - perfect for testing data processing logic:

```bash
# Process the most recent CSV automatically
uv run python -m src.main --skip-scraping

# Process a specific CSV file
uv run python -m src.main --skip-scraping --csv-path "data/processed/sales_20251006_095526/archivoVentas.csv"

# With debug mode for detailed logging
uv run python -m src.main --skip-scraping --debug
```

### Advanced Options

```bash
# Download a specific year and month
uv run python -m src.main --year 2024 --month OCTUBRE

# Download December 2024
uv run python -m src.main --year 2024 --month DICIEMBRE

# Use default (previous month, current year)
uv run python -m src.main

# Enable verbose logging
uv run python -m src.main --debug

# Specific period with debug mode
uv run python -m src.main --year 2025 --month SEPTIEMBRE --debug
```

### Available Months

```
ENERO, FEBRERO, MARZO, ABRIL, MAYO, JUNIO,
JULIO, AGOSTO, SEPTIEMBRE, OCTUBRE, NOVIEMBRE, DICIEMBRE
```ian Tax Authority (impuestos.gob.bo)**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-async-green.svg)](https://playwright.dev/python/)
[![UV](https://img.shields.io/badge/package%20manager-uv-orange.svg)](https://github.com/astral-sh/uv)

---

## 📖 Overview

TaxSalesValidator is a Python-based automation tool that:
1. **Authenticates** to the Bolivian Tax Authority portal (SIAT)
2. **Navigates** to the Consultas module ("Consultas de Compras y Ventas")
3. **Configures filters**: Tipo Consulta (CONSULTA VENTAS), Tipo Especificación (FACTURA ESTANDAR), Year, and Month
4. **Downloads** monthly sales reports in CSV format (packaged in ZIP)
5. **Processes** the data using Pandas for validation and analysis
6. **Validates** sales records against local inventory systems (future feature)

### Why This Project?

- **Eliminate Manual Work**: No more repetitive login → navigate → download cycles
- **Data Accuracy**: Automated extraction reduces human error
- **Audit Trail**: Timestamped downloads and processing logs
- **Extensible**: Built with SOLID principles for easy feature additions

---

## ✨ Features

### Phase 1 (Current - MVP)
- ✅ Async web scraping with Playwright
- ✅ Secure credential management via `.env`
- ✅ Navigate to Consultas module
- ✅ Configurable filters (Year, Month, Query Type, Specification Type)
- ✅ Automatic previous month calculation (default)
- ✅ Robust ZIP download and extraction
- ✅ CSV to Pandas DataFrame conversion
- ✅ **CUF (Código Único de Facturación) extraction** - Extract 8 additional fields from authorization codes
- ✅ **MySQL inventory integration** - Connect to local inventory database
- ✅ **Dual data loading** - Load both SIAT and inventory data for comparison
- ✅ **Skip scraping mode** - Process existing CSV files for testing
- ✅ Automatic browser cleanup and error handling

### Phase 2 (Completed)
- ✅ **CUF field extraction** (SUCURSAL, MODALIDAD, TIPO EMISION, etc.) ✅ COMPLETED
- ✅ **Inventory database connection** ✅ COMPLETED
- ✅ **Invoice comparison logic** - Match SIAT vs Inventory by CUF ✅ COMPLETED
- ✅ **Discrepancy identification and reporting** ✅ COMPLETED
- ✅ **Excel report generation** ✅ COMPLETED
- ✅ **Simplified output** (3 phases instead of 6) ✅ COMPLETED

### Phase 3 (Completed)
- ✅ Advanced analytics dashboard
- ✅ Historical data comparison
- ✅ Export to multiple formats (Excel, JSON, SQL)

### Phase 4 (Optional) - SAS Accounting System Integration
- ✅ **Atomic transaction sync** - ALL-OR-NOTHING guarantee (no partial data) ✅ COMPLETED
- ✅ **Data transformation** - 35-field mapping from SIAT to sales_registers ✅ COMPLETED
- ✅ **Dry run mode** - Test sync without database changes ✅ COMPLETED
- ✅ **Prerequisites validation** - Check config and validation success ✅ COMPLETED
- ✅ **UPSERT strategy** - Insert new records, update existing ✅ COMPLETED
- ✅ **Optional Phase 4** - Triggered with --sync-sas flag ✅ COMPLETED

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** installed
- **UV package manager** ([install guide](https://github.com/astral-sh/uv#installation))
- Valid credentials for impuestos.gob.bo (SIAT)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/TaxSalesValidator.git
cd TaxSalesValidator

# 2. Install dependencies with UV
uv sync

# 3. Install Playwright browsers
uv run playwright install chromium

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your actual credentials
```

### Configuration

Edit the `.env` file with your tax portal credentials and database connection:

```env
# .env
# Tax Portal Credentials
USER_EMAIL=your.email@company.com
USER_PASSWORD=YourSecurePassword
USER_NIT=1234567890

# MySQL Database Credentials (Inventory System)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
DB_USER=your_db_username
DB_PASSWORD=your_db_password
```

⚠️ **IMPORTANT**: Never commit the `.env` file to version control!

---

## 💻 Usage

### Basic Execution

```bash
# Run the scraper (downloads previous month for current year by default)
uv run python -m src.main

# Alternative: Use the installed script (after uv sync)
uv run tax-scraper
```

### Advanced Options

```bash
# Download a specific month
uv run python -m src.main --month OCTUBRE

# Download a specific year and month
uv run python -m src.main --year 2024 --month OCTUBRE

# Enable verbose logging
uv run python -m src.main --debug

# Specify custom download directory
uv run python -m src.main --output-dir ./custom_data
```

### SAS Accounting System Integration (Phase 4)

**Sync validated SIAT data to SAS accounting database:**

```bash
# Dry run - preview what would be synced (no database changes)
uv run python -m src.main --skip-scraping --sync-sas --dry-run

# Real sync - actually write to SAS database (atomic transaction)
uv run python -m src.main --skip-scraping --sync-sas

# Force sync despite minor discrepancies (e.g., canceled/duplicate invoices)
# Use this when you've verified discrepancies are acceptable
uv run python -m src.main --skip-scraping --sync-sas --force-sync --dry-run
uv run python -m src.main --skip-scraping --sync-sas --force-sync

# Full workflow: scrape + validate + sync
uv run python -m src.main --month SEPTIEMBRE --sync-sas
```

**Requirements for --sync-sas:**
- SAS_DB_* variables configured in `.env`
- **Amount validation passed** (total amounts match within 0.5% tolerance)
- **No individual amount mismatches** between matched invoices
- Network access to SAS MySQL database

**Validation Logic (Smart Sync):**
- ✅ **Canceled/duplicate invoices in SIAT are OK** - They will be included in sync
- ✅ **Critical check: Total amounts** must match within 0.5% (SIAT vs Inventory)
- ✅ **No amount mismatches** in individual matched invoices
- ℹ️ Invoices "only in SIAT" (e.g., canceled/duplicates) are automatically synced to SAS

**--force-sync Flag:**
- Use when amount validation fails but you've verified discrepancies are acceptable
- ⚠️ **Always use with --dry-run first** to verify what would be synced
- Bypasses the 0.5% amount tolerance check
- Recommended workflow:
  1. `--force-sync --dry-run` (review what would sync)
  2. Verify amount discrepancies are acceptable
  3. `--force-sync` (real sync)

**See detailed documentation**: [docs/PHASE7_COMPLETE.md](docs/PHASE7_COMPLETE.md)

### Expected Output

```
================================================================================
🧾 TAX SALES VALIDATOR
================================================================================
📅 Period: SEPTIEMBRE 2025
🕐 Started: 2025-10-06 13:03:40
================================================================================

================================================================================
PHASE 1: SIAT DATA RETRIEVAL
================================================================================

🌐 Downloading SIAT report...
✅ Download complete
📊 Processing SIAT data...
✅ SIAT data retrieved: 675 invoices

================================================================================
PHASE 2: INVENTORY DATA RETRIEVAL
================================================================================

�️  Querying inventory database...
✅ Inventory data retrieved: 662 invoices

================================================================================
PHASE 3: COMPARISON AND VALIDATION
================================================================================

� Comparing SIAT vs Inventory data...

================================================================================
📋 VALIDATION SUMMARY
================================================================================

📊 Dataset Sizes:
   - SIAT (MODALIDAD=2): 662 invoices
   - Inventory: 662 invoices

✅ Matches:
   - Perfect matches: 662 (100.00%)

⚠️  Discrepancies:
   - Only in SIAT: 0
   - Only in Inventory: 0
   - Amount mismatches: 0
   - Customer mismatches: 0
   - Other field mismatches: 0

🎯 Overall Status:
   ✅ PERFECT - No discrepancies found!
================================================================================

� Report generated: validation_report_20251006_130351.xlsx

================================================================================
✅ SUCCESS
================================================================================
⏱️  Execution time: 11.54 seconds
� Period: SEPTIEMBRE 2025 (2025-09-01 to 2025-09-30)
📊 SIAT: 675 invoices
📊 Inventory: 662 invoices
� Report: validation_report_20251006_130351.xlsx
================================================================================
```

**Note**:
- Use `--debug` flag to see detailed step-by-step output with browser automation details, CUF extraction validation, and full file paths
- ANULADA (canceled) invoices are automatically excluded from amount totals and comparisons for accurate reconciliation

### Invoice Status Handling

The system automatically filters invoices based on their status in SIAT:

```
ESTADO Field Values:
├── VALIDA   → Included in totals and comparisons ✅
└── ANULADA  → Excluded from totals and branch breakdowns
                (but counted separately for transparency)
```

**Fair Comparison Logic:**
- **SIAT Total Amount** = VALIDA invoices only
- **Inventory Total Amount** = Only invoices that are VALIDA in SIAT (ANULADA excluded from both sides)
- **Branch Breakdown**: Shows VALIDA count + separate ANULADA count, but amounts exclude ANULADA

**Example:**
```
SANTA CRUZ (Sucursal 5):
- SIAT:       173 VALID invoices | Bs. 473,896.15
              6 ANULADAS (excluded from totals)
- Inventory:  173 invoices | Bs. 473,896.15
- Difference: 0 invoices | Bs. 0.00 (accurate comparison)
```

---

## � CUF Extraction

The system automatically extracts **8 additional fields** from the authorization code (`CODIGO DE AUTORIZACIÓN`):

### Extracted Fields

| Field | Description | Example |
|-------|-------------|---------|
| `SUCURSAL` | Branch office code | `0`, `5`, `6` |
| `MODALIDAD` | Billing modality | `2` (Computerized), `3` (Electronic) |
| `TIPO EMISION` | Emission type | `1` (Online) |
| `TIPO FACTURA` | Invoice type | `1` (Standard) |
| `SECTOR` | Business sector | `1`, `2`, `35` |
| `NUM FACTURA` | Invoice number | `9587`, `6923` |
| `PV` | Point of sale | `0` |
| `CODIGO AUTOVERIFICADOR` | Verification digit | `1`, `8`, `7` |

### How It Works

```python
# Example authorization code (CUF)
codigo = "447D97004336A8D7C85C2495A6D872EA2398A919E1187C56A11D12F74"

# Extraction process:
# 1. Take first 42 hex chars → Convert to decimal
# 2. Convert decimal to string
# 3. Extract from position 27 onwards
# 4. Parse fixed positions for each field
```

### Real Data Insights

From 670 invoices (September 2025):
- **3 branch offices**: Branch 0 (47%), Branch 5 (29%), Branch 6 (24%)
- **98% computerized**, 2% electronic billing
- **100% online emission**, all standard invoices
- **670 unique invoice numbers** (perfect tracking)

### Usage

```bash
# CUF extraction happens automatically in Phase 4
uv run python -m src.main --skip-scraping

# Output includes validation:
# 📋 CUF Extraction Validation:
#    - SUCURSAL: 670/670 (100.00%)
#    - MODALIDAD: 670/670 (100.00%)
#    - NUM FACTURA: 670/670 (100.00%)
#    ...
```

📚 **Detailed documentation**: See [`docs/CUF_PROCESSING.md`](docs/CUF_PROCESSING.md)

---

## 🗄️ Inventory Integration

The system automatically connects to your local MySQL inventory database to retrieve sales data for the same period as the SIAT report.

### Features

- ✅ **Automatic synchronization**: Uses same year/month as SIAT scraping
- ✅ **Dual DataFrame loading**: Both SIAT and inventory data loaded simultaneously
- ✅ **Comprehensive query**: 34 fields from 15+ joined tables
- ✅ **Ready for comparison**: Data prepared for Phase 6 validation

### Configuration

Add your MySQL credentials to `.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
DB_USER=your_db_username
DB_PASSWORD=your_db_password
```

### Test Connection

```bash
# Test database connectivity
uv run python test_db_connection.py
```

### Retrieved Data (34 columns)

The inventory query retrieves comprehensive sales information:

| Category | Fields |
|----------|--------|
| **Identification** | codigoSucursal, codigoPuntoVenta, numeroFactura, idFactura |
| **Customer** | ClienteNit, ClienteFactura, emailCliente |
| **Amounts** | total, moneda, tipoPago, metodoPago |
| **SIAT** | cuf, codigoRecepcion, fechaEmisionSiat, leyenda |
| **Status** | estado, pagada, anulada, pagadaF |
| **Personnel** | vendedor, emisor |
| **Dates** | fechaFac, fecha, fechaEmisionSiat |
| **Other** | lote, almacen, pedido, glosa, cafc |

### Output Example

```
================================================================================
PHASE 5: INVENTORY DATA RETRIEVAL
================================================================================

📅 Querying inventory for period:
   - Year: 2025
   - Month: SEPTIEMBRE
   - Date Range: 2025-09-01 to 2025-09-30

✅ Query executed successfully
   - Records retrieved: 662

📊 Inventory Data Summary:
   - Total rows: 662
   - Total columns: 34
   - Total sales amount: Bs. 3,707,096.74
   - Unique invoices: 662
   - Invoices with CUF: 662
   - Date range: 2025-09-01 to 2025-09-30

💾 Inventory data saved: data/processed/inventory_sales_20251006_104637.csv

🎯 Ready for Phase 6: Invoice Comparison and Validation
   Both datasets loaded and ready for comparison:
   - df_siat: SIAT tax report data (670 rows)
   - df_inventory: Inventory system data (662 rows)
```

### Generated Files

After Phase 5, you'll have:

1. **`processed_siat_YYYYMMDD_HHMMSS.csv`** - SIAT tax report with CUF fields (32 columns)
2. **`inventory_sales_YYYYMMDD_HHMMSS.csv`** - Inventory sales data (34 columns)

Both files ready for comparison in Phase 6.

📚 **Detailed documentation**: See [`docs/INVENTORY_INTEGRATION.md`](docs/INVENTORY_INTEGRATION.md)

---

## �📁 Project Structure

```
TaxSalesValidator/
├── .env                      # Your credentials (DO NOT COMMIT)
├── .env.example              # Template for setup
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── PLAN.md                   # Detailed development plan
├── SETUP.md                  # Setup instructions
├── CHANGELOG.md              # Version history
├── pyproject.toml            # UV dependencies
├── uv.lock                   # Dependency lock file
├── analyze_cuf.py            # Quick CUF analysis script
├── check_observations.py     # Observation checking utility
├── diagnose_missing_rows.py  # Diagnostic script for missing rows
├── test_db_connection.py     # Database connection test script
├── test_sas_connection.py    # SAS database connection test
├── test_sas_mapper.py        # SAS mapper test script
├── verify_november_observations.py # November observations verification
├── verify_observations.py    # General observations verification
│
├── src/
│   ├── __init__.py
│   ├── config.py             # Configuration loader & dynamic defaults
│   ├── web_scraper.py        # Playwright automation
│   ├── file_manager.py       # ZIP/CSV file handling
│   ├── data_processor.py     # Pandas data processing
│   ├── sales_processor.py    # CUF extraction
│   ├── inventory_connector.py # MySQL database connector
│   ├── sales_validator.py    # Invoice comparison and validation
│   ├── sas_connector.py      # SAS database connector
│   ├── sas_mapper.py         # SAS data transformation
│   ├── sas_syncer.py         # SAS sync orchestration
│   ├── main.py               # Application entry point
│   └── main_backup.py        # Backup of main.py
│
├── data/
│   ├── downloads/            # Downloaded ZIP files
│   └── processed/            # Extracted CSV files & processed data
│
├── docs/                     # Documentation
│   ├── ATOMIC_TRANSACTIONS_EXPLAINED.md
│   ├── COMMIT_SUMMARY.md
│   ├── CUF_IMPLEMENTATION_SUMMARY.md
│   ├── CUF_PROCESSING.md     # CUF extraction guide
│   ├── DELIVERY.md
│   ├── INVENTORY_INTEGRATION.md  # Database integration guide
│   ├── INVENTORY_SETUP_COMPLETE.md  # Setup summary
│   ├── INSTALL_SUCCESS.md
│   ├── OUTPUT_SIMPLIFICATION.md
│   ├── PHASE5_COMPLETE.md
│   ├── PHASE5_RESUMEN_ESPAÑOL.md
│   ├── PHASE6_COMPLETE.md
│   ├── PHASE7_ACCOUNTING_SYNC_PLAN.md
│   ├── PHASE7_COMPLETE.md
│   ├── PHASE7_IMPLEMENTATION_SUMMARY.md
│   ├── PHASE7_RESUMEN_ESPANOL.md
│   ├── PLAN.md
│   ├── QUICKSTART_CUF.md
│   ├── RESUMEN_CAMBIOS_ES.md
│   └── SETUP.md
│
├── logs/                     # Execution logs & error screenshots
│
├── tests/                    # Unit and integration tests
│   └── __init__.py
│
├── build/                    # PyInstaller build output
├── context/                  # Codegen context files
└── dist/                     # Distribution files
```

---

## 🏗️ Architecture

This project follows **SOLID principles** with clear separation of concerns:

| Module | Responsibility |
|--------|---------------|
| `config.py` | Load environment variables, store constants, calculate dynamic defaults |
| `web_scraper.py` | Browser automation (login, navigation, filter configuration, download) |
| `file_manager.py` | File operations (ZIP extraction, cleanup) |
| `data_processor.py` | CSV parsing and DataFrame operations |
| `sales_processor.py` | CUF extraction - Parse authorization codes into 8 structured fields |
| `inventory_connector.py` | MySQL database connection and inventory queries |
| `sales_validator.py` | Invoice comparison, discrepancy detection, Excel report generation |
| `main.py` | Orchestrate the entire 3-phase workflow |

### Processing Pipeline

```
PHASE 1: SIAT DATA RETRIEVAL
   1. Web Scraping       → web_scraper.py
   2. File Extraction    → file_manager.py
   3. CSV Loading        → data_processor.py
   4. CUF Extraction     → sales_processor.py

PHASE 2: INVENTORY DATA RETRIEVAL
   5. Database Query     → inventory_connector.py

PHASE 3: COMPARISON AND VALIDATION
   6. Invoice Matching   → sales_validator.py
   7. Report Generation  → sales_validator.py (Excel output)
```

### Design Principles

- **KISS**: Simple, readable async/await flow
- **DRY**: Single source of truth for configuration
- **SRP**: Each class has ONE clear responsibility
- **Type Safety**: Full type hints for better IDE support
- **Error Handling**: Graceful failures with detailed logging

---

## 🔧 Development

### Setup Development Environment

```bash
# Install dev dependencies
uv add --dev pytest pytest-asyncio black ruff

# Format code
uv run black src/

# Lint code
uv run ruff check src/
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src tests/
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add: brief description of changes"

# Push and create PR
git push origin feature/your-feature-name
```

---

## 🔒 Security

### Credential Management

- **Local Development**: Use `.env` file (gitignored)
- **Production**: Use environment variables or secret management services
- **Never** hardcode credentials in source code
- **Rotate** passwords regularly

### Data Privacy

- CSV files contain sensitive tax information
- Store downloaded files securely
- Implement automatic cleanup of old files
- Consider encrypting stored data

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Login Fails
```
Error: Login failed - invalid credentials
```
**Solution**: Verify your `.env` credentials are correct

#### 2. Download Timeout
```
Error: TimeoutError waiting for download
```
**Solution**: Check internet connection or increase timeout in `config.py`

#### 3. Wrong Month Downloaded
```
Error: Expected OCTUBRE but got SEPTIEMBRE
```
**Solution**: Verify month name spelling (must be in Spanish UPPERCASE)

#### 4. Playwright Browser Not Found
```
Error: Executable doesn't exist at /path/to/chromium
```
**Solution**: Run `uv run playwright install chromium`

#### 4. CSV Encoding Issues
```
Error: UnicodeDecodeError
```
**Solution**: The script automatically tries UTF-8 and Latin-1 encodings

### Debug Mode

Enable detailed logging to diagnose issues:

```bash
uv run python src/main.py --debug
```

This will:
- Show browser window (non-headless)
- Log all HTTP requests
- Save screenshots on errors
- Print detailed stack traces

---

## 📊 Dependencies

### Core Libraries

- **playwright** (1.40+): Browser automation
- **pandas** (2.1+): Data manipulation
- **python-dotenv** (1.0+): Environment variable management
- **pymysql** (1.1+): MySQL database driver (NEW)
- **sqlalchemy** (2.0+): SQL toolkit and ORM (NEW)

### Development Tools

- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking (optional)

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Follow** the coding standards (see `PLAN.md`)
4. **Write** tests for new features
5. **Commit** with clear messages (`git commit -m 'Add: amazing feature'`)
6. **Push** to the branch (`git push origin feature/AmazingFeature`)
7. **Open** a Pull Request

### Code Standards

- All code in **English**
- Use **type hints**
- Follow **PEP 8** style guide
- Write **docstrings** for public methods
- Keep functions **under 50 lines**

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- [Playwright Python](https://playwright.dev/python/) for excellent browser automation
- [UV](https://github.com/astral-sh/uv) for fast Python package management
- [Pandas](https://pandas.pydata.org/) for powerful data processing
- Bolivian Tax Authority (SIN) for providing the SIAT portal

---

## 📅 Roadmap

### Version 1.0 (Current - Production Ready)
- [x] Basic web scraping functionality
- [x] ZIP download and extraction
- [x] CSV to DataFrame conversion
- [x] CUF field extraction (8 additional fields)
- [x] MySQL inventory integration
- [x] Dual data loading (SIAT + Inventory)
- [x] Invoice comparison logic (match by CUF)
- [x] Discrepancy identification and categorization
- [x] Excel report generation (7-sheet workbook)
- [x] Simplified 3-phase output
- [x] Debug mode for detailed logging

### Version 1.1 (Next)
- [ ] Scheduled monthly execution (cron jobs)
- [ ] Email notifications for discrepancies
- [ ] Unit test coverage (>80%)
- [ ] Historical data comparison

### Version 2.0 (Future)
- [ ] Scheduled execution (cron jobs)
- [ ] Email notifications
- [ ] Web dashboard for monitoring
- [ ] Multi-month batch downloads
- [ ] Historical data comparison

---

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [PLAN.md](PLAN.md) for architecture details
3. Open an [issue](https://github.com/yourusername/TaxSalesValidator/issues) on GitHub
4. Contact the maintainer via email

---

**Made with ❤️ and Python** | **Automation for Tax Compliance**

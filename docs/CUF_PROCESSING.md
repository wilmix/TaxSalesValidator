# CUF Processing Documentation

## Overview

The **CUF (Código Único de Facturación)** processing module extracts detailed invoice information from the authorization code field (`CODIGO DE AUTORIZACIÓN`) in the tax sales reports.

## What is CUF?

The CUF is a unique alphanumeric code that contains encoded information about each invoice, including:
- Branch office (Sucursal)
- Billing modality
- Emission type
- Invoice type
- Business sector
- Invoice number
- Point of sale
- Auto-verification code

## Extraction Process

### Technical Flow

The `SalesProcessor` class implements a sophisticated extraction algorithm:

1. **Validation**: Verifies the authorization code is at least 42 characters long
2. **Hex to Decimal**: Converts the first 42 hexadecimal characters to a decimal integer
3. **String Conversion**: Transforms the decimal integer to a string
4. **Substring Extraction**: Extracts from position 27 onwards (minimum 24 characters required)
5. **Field Parsing**: Extracts fixed-position substrings for each field

### Extracted Fields

| Field | Position | Length | Description |
|-------|----------|--------|-------------|
| SUCURSAL | 0-4 | 4 chars | Branch office code |
| MODALIDAD | 4-5 | 1 char | Billing modality (2=Computerized, 3=Electronic) |
| TIPO EMISION | 5-6 | 1 char | Emission type (1=Online) |
| TIPO FACTURA | 6-7 | 1 char | Invoice type (1=Standard) |
| SECTOR | 7-9 | 2 chars | Business sector code |
| NUM FACTURA | 9-19 | 10 chars | Sequential invoice number |
| PV | 19-23 | 4 chars | Point of sale code |
| CODIGO AUTOVERIFICADOR | 23-24 | 1 char | Auto-verification digit |

## Usage

### Testing Without Scraping

To process an existing CSV file without running the web scraper:

```bash
# Process the most recent CSV automatically
uv run python -m src.main --skip-scraping

# Process a specific CSV file
uv run python -m src.main --skip-scraping --csv-path "data/processed/sales_20251006_095526/archivoVentas.csv"

# With debug mode for detailed logging
uv run python -m src.main --skip-scraping --debug
```

### Full Workflow (with Scraping)

```bash
# Download and process September 2025 data
uv run python -m src.main --year 2025 --month SEPTIEMBRE

# The CUF extraction happens automatically in Phase 4
```

## Output

### Processed File

The processor saves an enriched CSV file with 8 additional columns:
- Original columns: 24
- CUF extracted columns: 8
- **Total: 32 columns**

File location: `data/processed/processed_sales_YYYYMMDD_HHMMSS.csv`

### Validation Report

After processing, you'll see validation statistics:

```
📋 CUF Extraction Validation:
   - SUCURSAL: 670/670 (100.00%)
   - MODALIDAD: 670/670 (100.00%)
   - TIPO EMISION: 670/670 (100.00%)
   - TIPO FACTURA: 670/670 (100.00%)
   - SECTOR: 670/670 (100.00%)
   - NUM FACTURA: 670/670 (100.00%)
   - PV: 670/670 (100.00%)
   - CODIGO AUTOVERIFICADOR: 670/670 (100.00%)
```

## Real Data Analysis

Based on 670 real invoices from September 2025:

### Branch Distribution
- **Branch 0**: 314 invoices (46.9%) - Main office
- **Branch 5**: 193 invoices (28.8%)
- **Branch 6**: 163 invoices (24.3%)

### Modality Distribution
- **Computerized (2)**: 657 invoices (98.1%)
- **Electronic (3)**: 13 invoices (1.9%)

### Sector Distribution
- **Sector 1**: 649 invoices (96.9%) - Standard commerce
- **Sector 2**: 13 invoices (1.9%) - Special sector
- **Sector 35**: 8 invoices (1.2%) - Specific industry

### Key Insights
- **100% online emission** (TIPO EMISION = 1)
- **100% standard invoices** (TIPO FACTURA = 1)
- **All from point of sale 0** (PV = 0)
- **670 unique invoice numbers** - perfect 1:1 mapping

## Code Example

### Using the SalesProcessor

```python
from pathlib import Path
import pandas as pd
from src.sales_processor import SalesProcessor

# Load your CSV
df = pd.read_csv("data/processed/sales_20251006_095526/archivoVentas.csv")

# Create processor
processor = SalesProcessor(debug=True)

# Extract CUF information
df = processor.extract_cuf_information(df)

# Validate extraction
validation = processor.validate_extracted_data(df)
print(validation)

# Save processed data
output_path = Path("data/processed/my_processed_sales.csv")
processor.save_processed_data(df, output_path)

# Get statistics
stats = processor.get_processing_stats()
print(f"Success rate: {stats['success_rate']:.2%}")
```

### Analyzing CUF Fields

```python
import pandas as pd

df = pd.read_csv("data/processed/processed_sales_20251006_102333.csv")

# Analyze branch distribution
print(df['SUCURSAL'].value_counts())

# Filter by modality
electronic_invoices = df[df['MODALIDAD'] == '3']
print(f"Electronic invoices: {len(electronic_invoices)}")

# Group by sector
sector_totals = df.groupby('SECTOR')['IMPORTE TOTAL DE LA VENTA'].sum()
print(sector_totals)

# Find invoices from specific branch
branch_5 = df[df['SUCURSAL'] == '5']
print(f"Branch 5 total sales: {branch_5['IMPORTE TOTAL DE LA VENTA'].sum():.2f}")
```

## Performance

- **Processing speed**: ~1,630 rows/second
- **Success rate**: 100% on real data (670/670 invoices)
- **Memory efficient**: Processes in-place with minimal overhead
- **Total execution time**: ~0.41 seconds for 670 rows

## Error Handling

The processor gracefully handles:
- Invalid authorization codes (too short)
- Malformed hexadecimal strings
- Missing or null values
- Corrupted data

Errors are logged but don't stop processing. Failed rows show empty strings for CUF fields.

## Architecture (SOLID Principles)

### Single Responsibility Principle
- `SalesProcessor`: Only handles CUF extraction logic
- Separate from web scraping, file management, and data loading

### Separation of Concerns
```
src/
├── web_scraper.py      # Web automation
├── file_manager.py     # File I/O operations
├── data_processor.py   # CSV to DataFrame
└── sales_processor.py  # CUF extraction (NEW)
```

## Next Steps

Now that CUF fields are extracted, you can:

1. **Compare with inventory**: Match `NUM FACTURA` with your local system
2. **Validate branch codes**: Ensure `SUCURSAL` matches expected offices
3. **Analyze by sector**: Group financial metrics by `SECTOR`
4. **Detect anomalies**: Find unusual patterns in modality or emission type

## Troubleshooting

### No CSV found
```bash
Error: No CSV file found. Please run without --skip-scraping first
```
**Solution**: Run the full scraper at least once to download data

### Invalid authorization code
If you see warnings about invalid codes:
- Check the source data quality
- Enable debug mode: `--debug`
- Inspect specific rows in the CSV

### Low fill rate
If validation shows < 100% fill rate:
- Review error messages in debug mode
- Check for data corruption in source CSV
- Verify CUF field positions haven't changed

## References

- [Tax Authority Portal](https://impuestos.gob.bo)
- [CUF Specification](https://impuestos.gob.bo/documentacion)
- Project README: `README.md`
- Main code: `src/sales_processor.py`

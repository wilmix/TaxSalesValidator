# Quick Start Guide - CUF Processing

## 🚀 For Testing Data Processing (No Scraping)

Perfect for developing validation logic without hitting the tax portal repeatedly:

```bash
# Process the most recent CSV file
uv run python -m src.main --skip-scraping
```

**What this does:**
1. ✅ Finds the most recent CSV in `data/processed/`
2. ✅ Loads it into a Pandas DataFrame
3. ✅ Extracts 8 CUF fields from authorization codes
4. ✅ Validates extraction (shows 100% success rate)
5. ✅ Saves processed file with all 32 columns
6. ⚡ Total time: ~0.41 seconds (for 670 rows)

**Output:**
```
⚡ SKIP SCRAPING MODE - Using existing CSV
📊 Data loaded: 670 rows × 24 columns
📊 EXTRACTING CUF INFORMATION
✅ Successfully processed: 670 rows
📋 CUF Extraction Validation: All fields 100%
💾 Processed data saved: processed_sales_20251006_102333.csv
✅ SUCCESS - Total time: 0.41 seconds
```

---

## 📊 Analyzing Extracted Data

### Quick Analysis
```bash
# Run the analysis helper script
uv run python analyze_cuf.py
```

Shows:
- Distribution of each CUF field
- Top values and percentages
- Sample records with all fields

### Custom Analysis with Python

```python
import pandas as pd

# Load processed data
df = pd.read_csv("data/processed/processed_sales_20251006_102333.csv")

# 1. Sales by branch
branch_sales = df.groupby('SUCURSAL')['IMPORTE TOTAL DE LA VENTA'].sum()
print("Sales by branch:")
print(branch_sales)

# 2. Count by modality
print("\nInvoices by modality:")
print(df['MODALIDAD'].value_counts())

# 3. Top 10 invoices
top10 = df.nlargest(10, 'IMPORTE TOTAL DE LA VENTA')
print("\nTop 10 invoices:")
print(top10[['NUM FACTURA', 'NOMBRE O RAZON SOCIAL', 'IMPORTE TOTAL DE LA VENTA']])

# 4. Electronic vs Computerized
electronic = df[df['MODALIDAD'] == '3']
computerized = df[df['MODALIDAD'] == '2']
print(f"\nElectronic: {len(electronic)} ({len(electronic)/len(df)*100:.1f}%)")
print(f"Computerized: {len(computerized)} ({len(computerized)/len(df)*100:.1f}%)")

# 5. Unique invoice numbers (should equal total rows)
print(f"\nUnique invoices: {df['NUM FACTURA'].nunique()} / {len(df)}")
```

---

## 🔄 Full Workflow (With Scraping)

When you're ready to download fresh data:

```bash
# Download and process September 2025
uv run python -m src.main --year 2025 --month SEPTIEMBRE
```

**Phases:**
1. ⬇️ Web scraping and download (~20 seconds)
2. 📦 File extraction (~1 second)
3. 📊 Data loading (~2 seconds)
4. 🔍 **CUF extraction (~0.4 seconds)** ← New!
5. 💾 Save processed file

---

## 📁 File Locations

### Input (Original CSV)
```
data/processed/sales_20251006_095526/archivoVentas.csv
- 670 rows × 24 columns
- 142 KB
```

### Output (Processed CSV)
```
data/processed/processed_sales_20251006_102333.csv
- 670 rows × 32 columns (24 original + 8 CUF)
- 151 KB
```

### Available CUF Fields
- `SUCURSAL` (Branch: 0, 5, 6)
- `MODALIDAD` (2=Computerized, 3=Electronic)
- `TIPO EMISION` (1=Online)
- `TIPO FACTURA` (1=Standard)
- `SECTOR` (1, 2, 35)
- `NUM FACTURA` (Unique invoice number)
- `PV` (Point of sale: 0)
- `CODIGO AUTOVERIFICADOR` (0-9)

---

## 🎯 Common Use Cases

### 1. Validate Invoice Numbers
```python
# Check if all invoice numbers are unique
df = pd.read_csv("data/processed/processed_sales_*.csv")
duplicates = df[df.duplicated(subset=['NUM FACTURA'], keep=False)]
if len(duplicates) > 0:
    print(f"⚠️ Found {len(duplicates)} duplicate invoices!")
else:
    print("✅ All invoice numbers are unique")
```

### 2. Branch Performance Report
```python
# Sales summary by branch
summary = df.groupby('SUCURSAL').agg({
    'IMPORTE TOTAL DE LA VENTA': ['sum', 'mean', 'count']
})
print(summary)
```

### 3. Find Electronic Invoices
```python
# Filter electronic invoices
electronic = df[df['MODALIDAD'] == '3']
print(f"Electronic invoices: {len(electronic)}")
print(electronic[['NUM FACTURA', 'NOMBRE O RAZON SOCIAL', 'IMPORTE TOTAL DE LA VENTA']])
```

### 4. Sector Analysis
```python
# Revenue by business sector
sector_revenue = df.groupby('SECTOR')['IMPORTE TOTAL DE LA VENTA'].sum()
print("Revenue by sector:")
for sector, revenue in sector_revenue.items():
    print(f"  Sector {sector}: Bs. {revenue:,.2f}")
```

### 5. Compare with Local Inventory
```python
# Example: Compare with your system
local_invoices = load_from_your_system()  # Your function

# Find in tax system but not in local
tax_invoices = set(df['NUM FACTURA'])
local_invoices_set = set(local_invoices['invoice_number'])

missing_in_local = tax_invoices - local_invoices_set
missing_in_tax = local_invoices_set - tax_invoices

print(f"In tax system but not local: {len(missing_in_local)}")
print(f"In local but not tax system: {len(missing_in_tax)}")
```

---

## 🐛 Troubleshooting

### "No CSV file found"
**Solution:** Run with full scraping first:
```bash
uv run python -m src.main
```

### "Invalid authorization code"
**Solution:** Enable debug mode to see which rows fail:
```bash
uv run python -m src.main --skip-scraping --debug
```

### Need to process a specific file
```bash
uv run python -m src.main --skip-scraping --csv-path "data/processed/sales_20251006_095526/archivoVentas.csv"
```

---

## 📚 More Information

- **Full CUF Documentation**: [`docs/CUF_PROCESSING.md`](CUF_PROCESSING.md)
- **Implementation Summary**: [`docs/CUF_IMPLEMENTATION_SUMMARY.md`](CUF_IMPLEMENTATION_SUMMARY.md)
- **Main README**: [`README.md`](../README.md)
- **Source Code**: [`src/sales_processor.py`](../src/sales_processor.py)

---

## ⚡ Pro Tips

1. **Fast iteration**: Use `--skip-scraping` while developing validation logic
2. **Debug mode**: Add `--debug` to see first 5 processed records
3. **Analysis script**: Modify `analyze_cuf.py` for your specific needs
4. **Pandas power**: All standard pandas operations work on the processed CSV
5. **Backup originals**: Processed files are saved separately, originals are preserved

---

**Need help?** Check the full documentation or review the code examples above! 🚀

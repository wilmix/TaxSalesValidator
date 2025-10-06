"""Diagnostic script to identify missing rows during CUF processing."""

import pandas as pd
from pathlib import Path

# File paths
original_csv = Path("data/processed/sales_20251006_095431/archivoVentas.csv")
processed_csv = Path("data/processed/processed_siat_20251006_110510.csv")

print("=" * 80)
print("🔍 DIAGNOSTIC: Missing Rows Analysis")
print("=" * 80)

# Load both files
print("\n📂 Loading files...")
df_original = pd.read_csv(original_csv, encoding='utf-8')
df_processed = pd.read_csv(processed_csv, encoding='utf-8')

print(f"   Original: {len(df_original)} rows")
print(f"   Processed: {len(df_processed)} rows")
print(f"   Difference: {len(df_original) - len(df_processed)} rows lost")

# Check if there are duplicate rows in the original
print("\n🔍 Checking for duplicates in original...")
duplicates = df_original.duplicated(subset=['CODIGO DE AUTORIZACIÓN'], keep=False)
if duplicates.any():
    print(f"   ⚠️  Found {duplicates.sum()} duplicate CUF codes in original")
    print("\n   Duplicate CUF codes:")
    dup_cufs = df_original[duplicates]['CODIGO DE AUTORIZACIÓN'].value_counts()
    for cuf, count in dup_cufs.items():
        print(f"      {cuf}: {count} times")
else:
    print("   ✓ No duplicates found")

# Compare NRO. field (should be unique)
print("\n🔍 Comparing by NRO. field...")
original_nros = set(df_original['NRO.'].astype(str))
processed_nros = set(df_processed['NRO.'].astype(str))
missing_nros = original_nros - processed_nros

if missing_nros:
    print(f"   ❌ Missing {len(missing_nros)} records by NRO.")
    print("\n   Missing NRO. values:")
    for nro in sorted(missing_nros, key=lambda x: int(x) if x.isdigit() else 0):
        print(f"      NRO. {nro}")
    
    # Show details of missing records
    print("\n   📋 Details of missing records:")
    missing_records = df_original[df_original['NRO.'].astype(str).isin(missing_nros)]
    for idx, row in missing_records.iterrows():
        print(f"\n      Record {row['NRO.']}:")
        print(f"         Fecha: {row['FECHA DE LA FACTURA']}")
        print(f"         Factura: {row['Nro. DE LA FACTURA']}")
        print(f"         CUF: {row['CODIGO DE AUTORIZACIÓN']}")
        print(f"         CUF length: {len(str(row['CODIGO DE AUTORIZACIÓN']))}")
        print(f"         Cliente: {row['NOMBRE O RAZON SOCIAL']}")
        print(f"         Monto: {row['IMPORTE TOTAL DE LA VENTA']}")
else:
    print("   ✓ All records present")

# Check CUF codes
print("\n🔍 Comparing by CUF codes...")
original_cufs = set(df_original['CODIGO DE AUTORIZACIÓN'].astype(str))
processed_cufs = set(df_processed['CODIGO DE AUTORIZACIÓN'].astype(str))
missing_cufs = original_cufs - processed_cufs

if missing_cufs:
    print(f"   ❌ Missing {len(missing_cufs)} records by CUF")
    print("\n   Missing CUF codes:")
    for cuf in missing_cufs:
        print(f"      {cuf} (length: {len(cuf)})")
else:
    print("   ✓ All CUF codes present")

# Check for empty CUF fields in processed file
print("\n🔍 Checking CUF extraction quality in processed file...")
cuf_fields = ['SUCURSAL', 'MODALIDAD', 'TIPO EMISION', 'TIPO FACTURA', 
              'SECTOR', 'NUM FACTURA', 'PV', 'CODIGO AUTOVERIFICADOR']

for field in cuf_fields:
    if field in df_processed.columns:
        empty_count = (df_processed[field].astype(str).str.strip() == '').sum()
        if empty_count > 0:
            print(f"   ⚠️  {field}: {empty_count} empty values")
        else:
            print(f"   ✓ {field}: All populated")

# Summary
print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print(f"Original rows: {len(df_original)}")
print(f"Processed rows: {len(df_processed)}")
print(f"Lost rows: {len(df_original) - len(df_processed)}")
if len(missing_nros) > 0:
    print(f"Missing NROs: {', '.join(sorted(missing_nros, key=lambda x: int(x) if x.isdigit() else 0))}")
print("=" * 80)

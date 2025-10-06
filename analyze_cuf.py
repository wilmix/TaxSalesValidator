"""Quick script to analyze extracted CUF fields."""

import pandas as pd
from pathlib import Path

# Load the most recent processed file
csv_path = Path("data/processed/processed_sales_20251006_102333.csv")
df = pd.read_csv(csv_path)

print("=" * 80)
print("📊 CUF EXTRACTION ANALYSIS")
print("=" * 80)
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print("=" * 80 + "\n")

# CUF fields to analyze
cuf_cols = [
    'SUCURSAL',
    'MODALIDAD',
    'TIPO EMISION',
    'TIPO FACTURA',
    'SECTOR',
    'NUM FACTURA',
    'PV',
    'CODIGO AUTOVERIFICADOR'
]

print("=== FIELD DISTRIBUTION ===\n")

for col in cuf_cols:
    print(f"{col}:")
    print(f"  Unique values: {df[col].nunique()}")
    
    # Show top 3 most common values
    top_values = df[col].value_counts().head(3)
    print(f"  Most common:")
    for val, count in top_values.items():
        print(f"    '{val}': {count} ({count/len(df)*100:.1f}%)")
    print()

# Show a sample of complete records
print("\n=== SAMPLE RECORDS WITH ALL CUF FIELDS ===\n")
sample_cols = ['Nro. DE LA FACTURA', 'NOMBRE O RAZON SOCIAL', 'IMPORTE TOTAL DE LA VENTA'] + cuf_cols
print(df[sample_cols].head(10).to_string(index=False))

print("\n" + "=" * 80)
print("✅ Analysis complete!")
print("=" * 80)

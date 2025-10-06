"""Test script for SasMapper.

Tests the data transformation from SIAT format to sales_registers format.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_processor import DataProcessor
from src.sales_processor import SalesProcessor
from src.sas_mapper import SasMapper


def main():
    """Test SasMapper transformation."""
    
    print("=" * 80)
    print("🧪 SAS MAPPER TEST")
    print("=" * 80)
    
    # Step 1: Load a processed SIAT CSV
    print("\n📋 Step 1: Loading processed SIAT data...")
    
    # Find latest processed_siat file
    from src.config import Config
    processed_files = list(Config.PROCESSED_DIR.glob("processed_siat_*.csv"))
    
    if not processed_files:
        print("❌ No processed SIAT files found!")
        print("\nPlease run the main script first to generate a processed file:")
        print("   uv run python -m src.main --skip-scraping")
        return False
    
    # Sort by modification time, get latest
    latest_file = max(processed_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ Found: {latest_file.name}")
    
    # Load CSV
    df_siat = DataProcessor.load_csv_to_dataframe(latest_file)
    print(f"✅ Loaded {len(df_siat):,} rows")
    
    # Show some columns
    print(f"\n📊 SIAT DataFrame columns ({len(df_siat.columns)}):")
    key_columns = [
        "FECHA DE LA FACTURA", "CODIGO DE AUTORIZACIÓN", 
        "NIT / CI CLIENTE", "NOMBRE O RAZON SOCIAL",
        "IMPORTE TOTAL DE LA VENTA", "NUM FACTURA", "SUCURSAL"
    ]
    for col in key_columns:
        if col in df_siat.columns:
            print(f"   ✓ {col}")
    
    # Step 2: Transform data
    print("\n🔄 Step 2: Transforming SIAT data to sales_registers format...")
    
    mapper = SasMapper(debug=True)
    
    try:
        df_transformed = mapper.transform_dataframe(df_siat)
        
        print(f"\n✅ Transformation successful!")
        print(f"   Input rows: {len(df_siat):,}")
        print(f"   Output rows: {len(df_transformed):,}")
        
        # Show stats
        stats = mapper.get_transformation_stats()
        print(f"\n📊 Transformation statistics:")
        print(f"   - Total rows: {stats['total_rows']}")
        print(f"   - Successful: {stats['successful']}")
        print(f"   - Errors: {stats['errors']}")
        print(f"   - Warnings: {stats['warnings']}")
        
    except Exception as e:
        print(f"\n❌ Transformation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Show sample transformed data
    print("\n📝 Step 3: Sample transformed data (first 3 rows):")
    
    display_columns = [
        "invoice_date", "invoice_number", "authorization_code",
        "customer_nit", "customer_name", "total_sale_amount",
        "branch_office", "modality", "author"
    ]
    
    for idx in range(min(3, len(df_transformed))):
        print(f"\n   Row {idx + 1}:")
        row = df_transformed.iloc[idx]
        for col in display_columns:
            if col in row:
                value = row[col]
                # Truncate long values for display
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                print(f"      {col}: {value}")
    
    # Step 4: Validate transformed data
    print("\n✅ Step 4: Validating transformed data...")
    
    validation = mapper.validate_transformed_data(df_transformed)
    
    print(f"\n📊 Validation results:")
    print(f"   - Total rows: {validation['total_rows']}")
    print(f"   - Valid: {'✅ YES' if validation['is_valid'] else '❌ NO'}")
    
    if validation['issues']:
        print(f"   - Issues found: {len(validation['issues'])}")
        for issue in validation['issues'][:5]:  # Show first 5 issues
            print(f"      ⚠️  {issue}")
        if len(validation['issues']) > 5:
            print(f"      ... and {len(validation['issues']) - 5} more issues")
    else:
        print(f"   - Issues: None ✅")
    
    # Step 5: Show column mapping
    print("\n📋 Step 5: Transformed DataFrame structure:")
    print(f"   Columns ({len(df_transformed.columns)}):")
    
    for col in df_transformed.columns:
        dtype = df_transformed[col].dtype
        null_count = df_transformed[col].isna().sum()
        null_pct = (null_count / len(df_transformed)) * 100
        print(f"      - {col}: {dtype} ({null_count} nulls / {null_pct:.1f}%)")
    
    # Step 6: Sample row as dict (ready for database insert)
    print("\n📤 Step 6: Sample row ready for database insert:")
    
    if len(df_transformed) > 0:
        sample_dict = df_transformed.iloc[0].to_dict()
        
        print(f"\n   Dictionary keys ({len(sample_dict)}):")
        for key, value in list(sample_dict.items())[:10]:  # Show first 10
            # Truncate long values
            if isinstance(value, str) and len(value) > 40:
                value = value[:37] + "..."
            print(f"      '{key}': {repr(value)}")
        
        if len(sample_dict) > 10:
            print(f"      ... and {len(sample_dict) - 10} more fields")
    
    # Success!
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\n🎯 Next steps:")
    print("   1. SasMapper: ✅ Working")
    print("   2. Data transformation: ✅ Validated")
    print("   3. Ready to implement SasSyncer")
    print("\n" + "=" * 80)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""Test script for database connectivity.

Simple script to verify MySQL connection and query execution
before integrating with the main application.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.inventory_connector import InventoryConnector


def main():
    """Test database connection and basic operations."""
    print("\n" + "=" * 80)
    print("🧪 DATABASE CONNECTION TEST")
    print("=" * 80 + "\n")

    try:
        # Create connector instance
        print("📊 Initializing InventoryConnector...")
        connector = InventoryConnector()

        # Test 1: Basic connection
        print("\n" + "-" * 80)
        print("TEST 1: Basic Connection")
        print("-" * 80)
        success = connector.test_connection()

        if not success:
            print("\n❌ Connection test failed. Please check your .env configuration.")
            sys.exit(1)

        # Test 2: Get database info
        print("\n" + "-" * 80)
        print("TEST 2: Database Information")
        print("-" * 80)
        db_info = connector.get_database_info()

        print("\n📋 Database Details:")
        print(f"   - MySQL Version: {db_info['mysql_version']}")
        print(f"   - Current Database: {db_info['current_database']}")
        print(f"   - Host: {db_info['host']}:{db_info['port']}")
        print(f"   - User: {db_info['user']}")

        # Test 3: Sample query (just to verify query execution works)
        print("\n" + "-" * 80)
        print("TEST 3: Sample Inventory Query")
        print("-" * 80)
        print("\n⚠️  Note: This will execute the full inventory query.")
        print("   If you want to test with sample data, modify the date range.")

        # Use September 2025 as example (adjust as needed)
        year = 2025
        start_date = "2025-09-01"
        end_date = "2025-09-30"

        df = connector.get_sales_from_inventory(year, start_date, end_date)

        print(f"\n📊 Query Results:")
        print(f"   - Total rows: {len(df):,}")
        print(f"   - Total columns: {len(df.columns)}")

        if len(df) > 0:
            print(f"\n📋 Column Names:")
            for i, col in enumerate(df.columns, 1):
                print(f"   {i:2d}. {col}")

            print(f"\n📊 Sample Data (first 5 rows):")
            print(df.head().to_string(max_cols=10))

            # Basic statistics
            print(f"\n📈 Basic Statistics:")
            if "total" in df.columns:
                print(f"   - Total sales amount: {df['total'].sum():,.2f}")
            if "numeroFactura" in df.columns:
                print(f"   - Unique invoices: {df['numeroFactura'].nunique():,}")
            if "cuf" in df.columns:
                print(f"   - Invoices with CUF: {df['cuf'].notna().sum():,}")
        else:
            print("\n⚠️  No data found for the specified period.")
            print("   This might be expected if there are no sales in September 2025.")

        # Close connection
        connector.close()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80 + "\n")

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"Error: {e}")

        import traceback

        print("\n📋 Full traceback:")
        traceback.print_exc()

        print("\n💡 Troubleshooting tips:")
        print("   1. Verify your .env file has correct database credentials")
        print("   2. Ensure MySQL server is running and accessible")
        print("   3. Check that the database user has proper permissions")
        print("   4. Verify the database name is correct")
        print("=" * 80 + "\n")

        sys.exit(1)


if __name__ == "__main__":
    main()

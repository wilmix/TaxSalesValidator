"""Test script for SAS database connection.

Quick test to verify SAS database configuration and connectivity
before proceeding with full implementation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.sas_connector import SasConnector


def main():
    """Test SAS database connection."""
    
    print("=" * 80)
    print("🧪 SAS DATABASE CONNECTION TEST")
    print("=" * 80)
    
    # Step 1: Check configuration
    print("\n📋 Step 1: Checking SAS configuration...")
    
    if not Config.is_sas_configured():
        print("❌ SAS database not configured!")
        print("\nPlease add the following to your .env file:")
        print("   SAS_DB_HOST=localhost")
        print("   SAS_DB_PORT=3306")
        print("   SAS_DB_NAME=your_sas_database")
        print("   SAS_DB_USER=your_sas_user")
        print("   SAS_DB_PASSWORD=your_sas_password")
        return False
    
    print("✅ Configuration found:")
    print(f"   Host: {Config.SAS_DB_HOST}:{Config.SAS_DB_PORT}")
    print(f"   Database: {Config.SAS_DB_NAME}")
    print(f"   User: {Config.SAS_DB_USER}")
    print(f"   Batch Size: {Config.SAS_SYNC_BATCH_SIZE}")
    print(f"   Timeout: {Config.SAS_SYNC_TIMEOUT}s")
    
    # Step 2: Test connection
    print("\n🔗 Step 2: Testing database connection...")
    
    try:
        with SasConnector(debug=True) as connector:
            if not connector.test_connection():
                print("❌ Connection test failed!")
                return False
            
            print("✅ Connection successful!")
            
            # Step 3: Get database info
            print("\n📊 Step 3: Retrieving database information...")
            db_info = connector.get_database_info()
            
            print(f"   MySQL Version: {db_info['mysql_version']}")
            print(f"   Current Database: {db_info['current_database']}")
            print(f"   Host: {db_info['host']}:{db_info['port']}")
            print(f"   User: {db_info['user']}")
            
            # Step 4: Check sales_registers table
            print("\n📋 Step 4: Checking sales_registers table...")
            try:
                table_info = connector.get_table_info("sales_registers")
                
                print(f"   Table: {table_info['table_name']}")
                print(f"   Total rows: {table_info['row_count']:,}")
                print(f"   Total columns: {len(table_info['columns'])}")
                
                # Show key columns
                print("\n   Key columns:")
                key_cols = [
                    "id", "invoice_date", "invoice_number", 
                    "authorization_code", "customer_nit", "total_sale_amount"
                ]
                for col_info in table_info['columns']:
                    col_name = col_info.get('Field', col_info.get('COLUMN_NAME', ''))
                    if col_name in key_cols:
                        col_type = col_info.get('Type', col_info.get('COLUMN_TYPE', ''))
                        null = col_info.get('Null', col_info.get('IS_NULLABLE', ''))
                        print(f"      - {col_name}: {col_type} (NULL: {null})")
                
                # Show indexes
                print("\n   Indexes:")
                unique_indexes = set()
                for idx in table_info['indexes']:
                    key_name = idx.get('Key_name', idx.get('INDEX_NAME', ''))
                    if key_name not in unique_indexes:
                        unique_indexes.add(key_name)
                        non_unique = idx.get('Non_unique', 1)
                        index_type = "UNIQUE" if non_unique == 0 else "INDEX"
                        print(f"      - {key_name} ({index_type})")
                
                print("\n✅ Table structure verified!")
                
            except Exception as e:
                print(f"⚠️  Could not access sales_registers table: {e}")
                print("\n   Make sure:")
                print("   1. Table 'sales_registers' exists")
                print("   2. User has SELECT permission on the table")
                return False
            
            # Step 5: Test authorization_code uniqueness
            print("\n🔑 Step 5: Testing authorization_code uniqueness...")
            test_code = "TEST_" + "0" * 60  # 64 char test code
            exists = connector.check_duplicate_authorization_code(test_code)
            
            if exists:
                print(f"   Test code exists (unexpected): {test_code[:30]}...")
            else:
                print(f"   Test code does not exist (expected) ✅")
            
    except Exception as e:
        print(f"\n❌ Error during connection test: {e}")
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        return False
    
    # Success!
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\n🎯 Next steps:")
    print("   1. Configuration: ✅ Complete")
    print("   2. Connection: ✅ Working")
    print("   3. Table structure: ✅ Verified")
    print("   4. Ready to implement SasMapper")
    print("\n" + "=" * 80)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

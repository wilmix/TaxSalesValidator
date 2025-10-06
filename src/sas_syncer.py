"""SAS Syncer - Orchestration layer for SAS accounting system synchronization.

This module coordinates the sync process between validated SIAT data and the SAS
accounting database. It uses SasMapper for data transformation and SasConnector
for database operations.

Author: TaxSalesValidator
Created: 2025-01-06
"""

import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import pandas as pd

from src.config import Config
from src.sas_connector import SasConnector
from src.sas_mapper import SasMapper


logger = logging.getLogger(__name__)


class SasSyncError(Exception):
    """Custom exception for SAS sync errors."""
    pass


class SasSyncer:
    """Orchestrates synchronization of validated SIAT data to SAS accounting system.
    
    This class coordinates the entire sync process:
    1. Prerequisites check (validation success, SAS configured)
    2. Data transformation (SIAT → sales_registers format)
    3. Database synchronization (atomic UPSERT)
    4. Statistics and reporting
    
    Attributes:
        connector: SasConnector instance for database operations
        mapper: SasMapper instance for data transformation
        debug: Whether to enable debug logging
    """
    
    def __init__(self, debug: bool = False):
        """Initialize SasSyncer.
        
        Args:
            debug: Enable debug logging for detailed sync information
        """
        self.connector = SasConnector()
        self.mapper = SasMapper(debug=debug)
        self.debug = debug
        
        if self.debug:
            logger.setLevel(logging.DEBUG)
    
    def check_prerequisites(self, validation_passed: bool) -> tuple[bool, str]:
        """Check if all prerequisites for sync are met.
        
        Prerequisites:
        1. SAS database is configured (.env has all SAS_DB_* variables)
        2. Validation passed (no critical discrepancies between SIAT and inventory)
        3. SAS database connection is working
        
        Args:
            validation_passed: Whether the SIAT vs inventory validation succeeded
        
        Returns:
            Tuple of (prerequisites_met, message)
            - prerequisites_met: True if all checks pass
            - message: Description of check results or first failure
        """
        # Check 1: SAS configuration
        if not Config.is_sas_configured():
            return False, "❌ SAS database not configured. Please set SAS_DB_* variables in .env"
        
        # Check 2: Validation passed
        if not validation_passed:
            return False, "❌ Cannot sync: SIAT vs Inventory validation failed"
        
        # Check 3: Database connection
        logger.info("Testing SAS database connection...")
        if not self.connector.test_connection():
            return False, "❌ SAS database connection failed"
        
        return True, "✅ All prerequisites met"
    
    def sync_validated_data(
        self,
        df_siat: pd.DataFrame,
        dry_run: bool = False
    ) -> Dict:
        """Synchronize validated SIAT data to SAS accounting system.
        
        This is the main sync method that:
        1. Transforms SIAT DataFrame to sales_registers format
        2. Validates transformed data
        3. Performs atomic UPSERT to database (or simulates if dry_run=True)
        4. Returns detailed statistics
        
        Args:
            df_siat: SIAT DataFrame (processed_siat_*.csv format)
            dry_run: If True, only validate/transform but don't write to database
        
        Returns:
            Dictionary with sync results:
            {
                'success': bool,
                'total_rows': int,
                'inserted': int (if not dry_run),
                'updated': int (if not dry_run),
                'errors': int,
                'dry_run': bool,
                'message': str,
                'timestamp': str (ISO format),
                'transformation_stats': dict (from SasMapper),
                'validation_issues': list (if any)
            }
        
        Raises:
            SasSyncError: If transformation or database operation fails
        """
        start_time = datetime.now()
        
        result = {
            'success': False,
            'total_rows': len(df_siat),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'dry_run': dry_run,
            'message': '',
            'timestamp': start_time.isoformat(),
            'transformation_stats': {},
            'validation_issues': []
        }
        
        try:
            # Step 1: Transform data
            logger.info(f"{'[DRY RUN] ' if dry_run else ''}Transforming {len(df_siat):,} SIAT rows...")
            
            df_transformed = self.mapper.transform_dataframe(df_siat)
            
            transformation_stats = self.mapper.get_transformation_stats()
            result['transformation_stats'] = transformation_stats
            
            if transformation_stats['errors'] > 0:
                raise SasSyncError(
                    f"Transformation failed: {transformation_stats['errors']} errors"
                )
            
            logger.info(
                f"✅ Transformed {transformation_stats['successful']:,} rows successfully"
            )
            
            # Step 2: Validate transformed data
            logger.info("Validating transformed data...")
            
            validation = self.mapper.validate_transformed_data(df_transformed)
            
            if not validation['is_valid']:
                result['validation_issues'] = validation['issues']
                raise SasSyncError(
                    f"Validation failed: {len(validation['issues'])} issues found"
                )
            
            logger.info("✅ Validation passed")
            
            # Step 3: Sync to database (or simulate)
            if dry_run:
                # Dry run: just report what would happen
                logger.info("🔍 DRY RUN: Simulating database sync...")
                
                # Check for duplicates
                existing_count = 0
                sample_checks = min(10, len(df_transformed))
                
                for idx in range(sample_checks):
                    auth_code = df_transformed.iloc[idx]['authorization_code']
                    if self.connector.check_duplicate_authorization_code(auth_code):
                        existing_count += 1
                
                # Estimate inserts vs updates based on sample
                if sample_checks > 0:
                    duplicate_ratio = existing_count / sample_checks
                    estimated_updates = int(len(df_transformed) * duplicate_ratio)
                    estimated_inserts = len(df_transformed) - estimated_updates
                else:
                    estimated_inserts = len(df_transformed)
                    estimated_updates = 0
                
                result['success'] = True
                result['inserted'] = estimated_inserts
                result['updated'] = estimated_updates
                result['message'] = (
                    f"🔍 DRY RUN: Would sync {len(df_transformed):,} rows "
                    f"(~{estimated_inserts:,} new, ~{estimated_updates:,} updates)"
                )
                
                logger.info(result['message'])
                
            else:
                # Real sync: atomic UPSERT
                logger.info(f"💾 Syncing {len(df_transformed):,} rows to SAS database...")
                logger.info("⚠️  Using ATOMIC transaction (ALL-OR-NOTHING)")
                
                # Convert DataFrame to list of dicts
                records = df_transformed.to_dict('records')
                
                # Perform atomic UPSERT
                upsert_result = self.connector.upsert_records(records)
                
                if not upsert_result['success']:
                    raise SasSyncError(
                        f"Database UPSERT failed: {upsert_result.get('error', 'Unknown error')}"
                    )
                
                # Extract stats from upsert result
                result['success'] = True
                result['inserted'] = upsert_result.get('inserted', 0)
                result['updated'] = upsert_result.get('updated', 0)
                result['errors'] = upsert_result.get('errors', 0)
                
                result['message'] = (
                    f"✅ Successfully synced {result['inserted'] + result['updated']:,} rows "
                    f"({result['inserted']:,} new, {result['updated']:,} updates)"
                )
                
                logger.info(result['message'])
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            result['duration_seconds'] = duration
            
            logger.info(f"⏱️  Sync completed in {duration:.2f} seconds")
            
            return result
            
        except Exception as e:
            result['success'] = False
            result['message'] = f"❌ Sync failed: {str(e)}"
            result['errors'] = 1
            
            logger.error(result['message'], exc_info=self.debug)
            
            return result
    
    def get_sync_summary(self, sync_result: Dict) -> str:
        """Generate human-readable summary of sync results.
        
        Args:
            sync_result: Result dictionary from sync_validated_data()
        
        Returns:
            Formatted multi-line summary string
        """
        lines = []
        lines.append("=" * 80)
        
        if sync_result['dry_run']:
            lines.append("🔍 SAS SYNC DRY RUN SUMMARY")
        else:
            lines.append("💾 SAS SYNC SUMMARY")
        
        lines.append("=" * 80)
        
        # Status
        if sync_result['success']:
            lines.append(f"Status: ✅ SUCCESS")
        else:
            lines.append(f"Status: ❌ FAILED")
        
        # Mode
        if sync_result['dry_run']:
            lines.append(f"Mode: 🔍 Dry Run (no database changes)")
        else:
            lines.append(f"Mode: 💾 Real Sync (atomic transaction)")
        
        # Timestamp
        timestamp = sync_result.get('timestamp', '')
        if timestamp:
            lines.append(f"Timestamp: {timestamp}")
        
        # Statistics
        lines.append(f"\n📊 Statistics:")
        lines.append(f"   - Total rows: {sync_result['total_rows']:,}")
        
        if not sync_result['dry_run'] or sync_result['success']:
            lines.append(f"   - Inserted: {sync_result['inserted']:,}")
            lines.append(f"   - Updated: {sync_result['updated']:,}")
        
        if sync_result['errors'] > 0:
            lines.append(f"   - Errors: ❌ {sync_result['errors']:,}")
        
        # Duration
        duration = sync_result.get('duration_seconds', 0)
        if duration > 0:
            lines.append(f"   - Duration: ⏱️  {duration:.2f} seconds")
        
        # Transformation stats
        if sync_result.get('transformation_stats'):
            trans_stats = sync_result['transformation_stats']
            lines.append(f"\n🔄 Transformation:")
            lines.append(f"   - Successful: {trans_stats.get('successful', 0):,}")
            
            if trans_stats.get('errors', 0) > 0:
                lines.append(f"   - Errors: {trans_stats['errors']:,}")
            if trans_stats.get('warnings', 0) > 0:
                lines.append(f"   - Warnings: {trans_stats['warnings']:,}")
        
        # Validation issues
        if sync_result.get('validation_issues'):
            issues = sync_result['validation_issues']
            lines.append(f"\n⚠️  Validation Issues ({len(issues)}):")
            for issue in issues[:5]:  # Show first 5
                lines.append(f"   - {issue}")
            if len(issues) > 5:
                lines.append(f"   ... and {len(issues) - 5} more issues")
        
        # Message
        if sync_result.get('message'):
            lines.append(f"\n💬 {sync_result['message']}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def close(self):
        """Close database connection.
        
        Should be called when done with syncer, or use context manager.
        """
        if hasattr(self, 'connector'):
            self.connector.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close()
        return False  # Don't suppress exceptions


def main():
    """CLI entry point for testing SasSyncer."""
    import sys
    from src.data_processor import DataProcessor
    
    print("=" * 80)
    print("🧪 SAS SYNCER TEST")
    print("=" * 80)
    
    # Find latest processed SIAT file
    processed_files = list(Config.PROCESSED_DIR.glob("processed_siat_*.csv"))
    
    if not processed_files:
        print("\n❌ No processed SIAT files found!")
        print("Please run main script first to generate processed files.")
        sys.exit(1)
    
    latest_file = max(processed_files, key=lambda p: p.stat().st_mtime)
    print(f"\n📋 Loading: {latest_file.name}")
    
    df_siat = DataProcessor.load_csv_to_dataframe(latest_file)
    print(f"✅ Loaded {len(df_siat):,} rows")
    
    # Test with syncer
    print("\n🔄 Initializing SasSyncer...")
    with SasSyncer(debug=True) as syncer:
        
        # Check prerequisites
        print("\n📋 Checking prerequisites...")
        prereqs_met, message = syncer.check_prerequisites(validation_passed=True)
        print(f"{message}")
        
        if not prereqs_met:
            print("\n❌ Prerequisites not met. Cannot proceed.")
            sys.exit(1)
        
        # Dry run sync
        print("\n🔍 Running DRY RUN sync...")
        result = syncer.sync_validated_data(df_siat, dry_run=True)
        
        # Show summary
        print("\n" + syncer.get_sync_summary(result))
        
        if result['success']:
            print("\n✅ Test completed successfully!")
            print("\n🎯 Next: Ready for real sync integration into main.py")
        else:
            print("\n❌ Test failed!")
            sys.exit(1)


if __name__ == "__main__":
    main()

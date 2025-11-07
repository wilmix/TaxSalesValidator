"""Main orchestrator for TaxSalesValidator.

This module coordinates the entire scraping and processing workflow.
Entry point for the application.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import Config
from .data_processor import DataProcessor
from .file_manager import FileManager
from .inventory_connector import InventoryConnector
from .sales_processor import SalesProcessor
from .sales_validator import SalesValidator
from .sas_syncer import SasSyncer
from .web_scraper import WebScraper


def find_latest_csv() -> Optional[Path]:
    """Find the most recently created CSV file from SIAT scraping in processed directory.
    
    Excludes inventory and processed files to find only raw scraped data.

    Returns:
        Path to the most recent SIAT CSV file, or None if no files found
    """
    processed_dir = Config.PROCESSED_DIR
    
    if not processed_dir.exists():
        return None
    
    # Find all CSV files recursively, excluding our processed files
    csv_files = []
    for csv_file in processed_dir.rglob("*.csv"):
        # Exclude inventory and processed SIAT files
        if not any(pattern in csv_file.name for pattern in ["inventory_", "processed_"]):
            csv_files.append(csv_file)
    
    if not csv_files:
        return None
    
    # Sort by modification time, most recent first
    csv_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    return csv_files[0]


async def main(
    year: Optional[int] = None,
    month: Optional[str] = None,
    debug: bool = False,
    skip_scraping: bool = False,
    csv_path: Optional[Path] = None,
    sync_sas: bool = False,
    dry_run: bool = False,
    force_sync: bool = False
) -> None:
    """Main execution flow for the tax sales validator.

    Orchestrates the complete workflow organized in 3-4 phases:
    1. SIAT data retrieval (web scraping + processing)
    2. Inventory data retrieval
    3. Comparison and validation
    4. SAS sync (optional - only if --sync-sas flag is provided)

    Args:
        year: Year for the report (default: current year)
        month: Month to download report for (default: previous month)
        debug: Enable debug mode with detailed logging
        skip_scraping: Skip web scraping and use existing CSV file
        csv_path: Path to existing CSV file (used with skip_scraping)
        sync_sas: Synchronize validated data to SAS accounting system
        dry_run: Simulate SAS sync without writing to database
        force_sync: Force sync even with minor validation discrepancies (use with caution)
    """
    start_time = datetime.now()

    # Use current year if not specified
    if year is None:
        year = Config.get_current_year()

    # Use previous month if not specified
    if month is None:
        month = Config.get_previous_month()

    print("\n" + "=" * 80)
    print("🧾 TAX SALES VALIDATOR")
    print("=" * 80)
    print(f"📅 Period: {month} {year}")
    print(f"🕐 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    try:
        # =====================================================================
        # PHASE 1: SIAT DATA RETRIEVAL
        # =====================================================================
        print("=" * 80)
        print("PHASE 1: SIAT DATA RETRIEVAL")
        print("=" * 80 + "\n")

        # Handle skip_scraping mode
        if skip_scraping:
            if csv_path is None:
                csv_path = find_latest_csv()
                if csv_path is None:
                    raise FileNotFoundError(
                        "No CSV file found. Please run without --skip-scraping first "
                        "or specify a CSV file path."
                    )
            
            if debug:
                print("⚡ SKIP SCRAPING MODE - Using existing CSV")
                print(f"📁 CSV file: {csv_path}\n")
            
            if not FileManager.validate_csv_exists(csv_path):
                raise FileNotFoundError(f"CSV file not found or invalid: {csv_path}")
        else:
            # Web scraping and download
            print("🌐 Downloading SIAT report...")
            if debug:
                print("   (Browser automation in progress)")
            async with WebScraper(headless=not debug) as scraper:
                zip_path = await scraper.run_full_flow(year=year, month=month)
            
            if not zip_path.exists():
                raise FileNotFoundError(f"Downloaded ZIP file not found: {zip_path}")
            
            # Extract CSV
            csv_path = FileManager.extract_zip(zip_path)
            
            if not FileManager.validate_csv_exists(csv_path):
                raise FileNotFoundError(f"Extracted CSV file not found or invalid: {csv_path}")
            
            print("✅ Download complete")

        # Load and process SIAT data
        print("📊 Processing SIAT data...")
        df = DataProcessor.load_csv_to_dataframe(csv_path)
        
        if not DataProcessor.validate_dataframe(df, min_rows=1):
            raise ValueError("DataFrame validation failed")
        
        # Extract CUF information
        processor = SalesProcessor(debug=debug)
        df_siat = processor.extract_cuf_information(df)
        
        # Save processed SIAT data
        output_filename = f"processed_siat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path = Config.PROCESSED_DIR / output_filename
        processor.save_processed_data(df_siat, output_path)
        
        # Phase 1 Summary
        if debug:
            validation = processor.validate_extracted_data(df_siat)
            print("\n📋 CUF Extraction Validation:")
            for field, stats in validation.items():
                print(f"   - {field}: {stats['populated_rows']}/{stats['total_rows']} ({stats['fill_rate']})")
        
        print(f"✅ SIAT data retrieved: {len(df_siat):,} invoices")

        # =====================================================================
        # PHASE 2: INVENTORY DATA RETRIEVAL
        # =====================================================================
        print("\n" + "=" * 80)
        print("PHASE 2: INVENTORY DATA RETRIEVAL")
        print("=" * 80 + "\n")

        # Calculate date range from year and month
        start_date, end_date = Config.get_date_range_from_month(year, month)
        
        print(f"�️  Querying inventory database...")
        if debug:
            print(f"   - Date Range: {start_date} to {end_date}")

        # Query inventory database
        with InventoryConnector() as inventory:
            if not inventory.test_connection():
                raise ConnectionError("Failed to connect to inventory database")
            
            df_inventory = inventory.get_sales_from_inventory(
                year=year,
                start_date=start_date,
                end_date=end_date
            )

        # Save inventory data
        inventory_filename = f"inventory_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        inventory_path = Config.PROCESSED_DIR / inventory_filename
        df_inventory.to_csv(inventory_path, index=False, encoding="utf-8")
        
        # Phase 2 Summary
        print(f"✅ Inventory data retrieved: {len(df_inventory):,} invoices")
        if debug:
            if len(df_inventory) > 0:
                if "total" in df_inventory.columns:
                    total_amount = df_inventory["total"].sum()
                    print(f"   💰 Total amount: Bs. {total_amount:,.2f}")
                if "numeroFactura" in df_inventory.columns:
                    unique_invoices = df_inventory["numeroFactura"].nunique()
                    print(f"   🔢 Unique invoices: {unique_invoices:,}")

        # =====================================================================
        # PHASE 3: COMPARISON AND VALIDATION
        # =====================================================================
        print("\n" + "=" * 80)
        print("PHASE 3: COMPARISON AND VALIDATION")
        print("=" * 80 + "\n")
        
        print("🔍 Comparing SIAT vs Inventory data...")
        validator = SalesValidator(debug=debug)
        comparison, validation_stats = validator.validate(df_siat, df_inventory)
        
        # Generate Excel report
        report_filename = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        report_path = Config.PROCESSED_DIR / report_filename
        validator.generate_report(comparison, validation_stats, report_path)
        
        print(f"\n📄 Report generated: {report_path.name}")

        # Check if validation passed
        # CRITICAL validation: Amount difference must be < 0.5%
        # MINOR issues: Canceled/duplicate invoices in SIAT (only_siat) are acceptable
        validation_passed = (
            validation_stats.amount_difference_pct <= 0.5 and  # Amounts match within tolerance
            validation_stats.amount_mismatch_count == 0         # No individual amount mismatches
        )
        
        # Log validation result
        if debug:
            print(f"\n🔍 Validation Check:")
            print(f"   - Amount difference: {validation_stats.amount_difference_pct:.4f}% (threshold: 0.5%)")
            print(f"   - Amount mismatches: {validation_stats.amount_mismatch_count}")
            print(f"   - Only in SIAT (canceled/duplicates OK): {validation_stats.only_siat_count}")
            print(f"   - Only in Inventory: {validation_stats.only_inventory_count}")
            print(f"   - Validation passed: {validation_passed}")
        
        # =====================================================================
        # PHASE 4: SAS SYNC (OPTIONAL)
        # =====================================================================
        sync_result = None
        if sync_sas:
            print("\n" + "=" * 80)
            print("PHASE 4: SAS ACCOUNTING SYSTEM SYNC")
            print("=" * 80 + "\n")
            
            # Determine if we should proceed with sync
            should_sync = validation_passed or force_sync
            
            # If forcing sync with discrepancies, show warning
            if force_sync and not validation_passed:
                print("⚠️  WARNING: --force-sync enabled")
                print(f"   Syncing despite validation issues:")
                if validation_stats.amount_difference_pct > 0.5:
                    print(f"   ❌ Amount difference: {validation_stats.amount_difference_pct:.4f}% (> 0.5%)")
                if validation_stats.amount_mismatch_count > 0:
                    print(f"   ❌ Amount mismatches: {validation_stats.amount_mismatch_count} invoices")
                print(f"   ℹ️  Only in SIAT: {validation_stats.only_siat_count} (canceled/duplicates - will be synced)")
                print(f"   ℹ️  Only in Inventory: {validation_stats.only_inventory_count}")
                
                # Additional safety check for real sync (not dry-run)
                if not dry_run:
                    print("\n⚠️  CAUTION: This will write to the SAS database!")
                    print("   Amount validation failed but --force-sync is enabled.")
                    print("   Recommend using --dry-run first to verify data.\n")
            elif not validation_passed and not force_sync:
                print("ℹ️  Note: Canceled/duplicate invoices in SIAT will be included in sync")
                print(f"   - {validation_stats.only_siat_count} invoices only in SIAT (likely canceled)")
                if validation_stats.amount_difference_pct <= 0.5 and validation_stats.amount_mismatch_count == 0:
                    print("   - Amounts match perfectly ✅")
                    print("   - Proceeding with sync (canceled invoices will be included)")
            
            # Check prerequisites
            with SasSyncer(debug=debug) as syncer:
                prereqs_met, prereq_message = syncer.check_prerequisites(should_sync)
                
                if not prereqs_met:
                    print(f"{prereq_message}")
                    if not validation_passed and not force_sync:
                        print("💡 Tip: Validation failed due to amount discrepancies")
                        print(f"   - Amount difference: {validation_stats.amount_difference_pct:.4f}%")
                        if validation_stats.amount_mismatch_count > 0:
                            print(f"   - Amount mismatches: {validation_stats.amount_mismatch_count} invoices")
                        print("   Use --force-sync only if you've verified these are acceptable")
                    print("⚠️  Skipping SAS sync due to unmet prerequisites")
                else:
                    # Perform sync (real or dry run)
                    mode = "🔍 DRY RUN" if dry_run else "💾 REAL SYNC"
                    print(f"{mode}: Syncing validated SIAT data to SAS...")
                    
                    sync_result = syncer.sync_validated_data(df_siat, dry_run=dry_run)
                    
                    # Show summary
                    print("\n" + syncer.get_sync_summary(sync_result))
                    
                    if not sync_result['success']:
                        print("⚠️  SAS sync failed, but main validation completed successfully")

        # Success Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 80)
        print("✅ SUCCESS")
        print("=" * 80)
        print(f"⏱️  Execution time: {duration:.2f} seconds")
        print(f"� Period: {month} {year} ({start_date} to {end_date})")
        print(f"� SIAT: {len(df_siat):,} invoices")
        print(f"📊 Inventory: {len(df_inventory):,} invoices")
        print(f"� Report: {report_path.name}")
        
        # SAS sync status (if attempted)
        if sync_result:
            if sync_result['success']:
                if sync_result['dry_run']:
                    print(f"🔍 SAS Sync: Dry run successful")
                else:
                    print(f"💾 SAS Sync: {sync_result['inserted'] + sync_result['updated']:,} rows synced")
            else:
                print(f"⚠️  SAS Sync: Failed (see details above)")
        
        if debug:
            if not skip_scraping:
                print(f"\n📁 Files generated:")
                print(f"   - ZIP: {zip_path}")
                print(f"   - CSV: {csv_path}")
                print(f"   - SIAT processed: {output_path}")
                print(f"   - Inventory: {inventory_path}")
                print(f"   - Report: {report_path}")
            else:
                print(f"\n📁 Files generated:")
                print(f"   - SIAT processed: {output_path}")
                print(f"   - Inventory: {inventory_path}")
                print(f"   - Report: {report_path}")
        print("=" * 80 + "\n")

        # Optional: Clean up old files (older than 7 days) only if we did scraping
        if not skip_scraping and debug:
            print("🧹 Cleaning up old files...")
            deleted_count = FileManager.cleanup_old_files(
                Config.DOWNLOAD_DIR, days=7, pattern="*.zip", dry_run=False
            )
            if deleted_count > 0:
                print(f"✅ Cleaned up {deleted_count} old file(s)\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)

    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 80)
        print("❌ ERROR - Process failed")
        print("=" * 80)
        print(f"⏱️  Failed after: {duration:.2f} seconds")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Error message: {str(e)}")

        if debug:
            import traceback

            print("\n📋 Full traceback:")
            traceback.print_exc()

        print("=" * 80 + "\n")

        sys.exit(1)


def run() -> None:
    """Entry point for running the application."""
    import argparse

    parser = argparse.ArgumentParser(
        description="TaxSalesValidator - Automated tax sales report scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download previous month report for current year (default)
  python -m src.main

  # Download specific month and year
  python -m src.main --year 2024 --month OCTUBRE

  # Download September 2025
  python -m src.main --year 2025 --month SEPTIEMBRE

  # Enable debug mode
  python -m src.main --debug

  # Skip scraping and process existing CSV (for testing)
  python -m src.main --skip-scraping

  # Process specific CSV file
  python -m src.main --skip-scraping --csv-path "data/processed/sales_20251006_095526/archivoVentas.csv"

  # Full example with all parameters
  python -m src.main --year 2024 --month DICIEMBRE --debug
        """,
    )

    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=f"Year for the report (default: current year {Config.get_current_year()})",
    )

    parser.add_argument(
        "--month",
        type=str,
        default=None,
        help=f"Month to download in Spanish (default: previous month {Config.get_previous_month()})",
    )

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode (show browser, detailed logs)"
    )

    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="Skip web scraping and use existing CSV file (for testing processing logic)"
    )

    parser.add_argument(
        "--csv-path",
        type=str,
        default=None,
        help="Path to existing CSV file (used with --skip-scraping)"
    )

    parser.add_argument(
        "--sync-sas",
        action="store_true",
        help="Synchronize validated SIAT data to SAS accounting system (requires SAS_DB_* configuration)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate SAS sync without writing to database (use with --sync-sas)"
    )

    parser.add_argument(
        "--force-sync",
        action="store_true",
        help="Force SAS sync even with minor validation discrepancies (use with caution, requires --sync-sas)"
    )

    args = parser.parse_args()

    # Convert csv_path string to Path if provided
    csv_path_obj = Path(args.csv_path) if args.csv_path else None

    # Validate flag combinations
    if args.force_sync and not args.sync_sas:
        parser.error("--force-sync requires --sync-sas flag")

    # Run async main function
    asyncio.run(
        main(
            year=args.year,
            month=args.month,
            debug=args.debug,
            skip_scraping=args.skip_scraping,
            csv_path=csv_path_obj,
            sync_sas=args.sync_sas,
            dry_run=args.dry_run,
            force_sync=args.force_sync
        )
    )


if __name__ == "__main__":
    run()
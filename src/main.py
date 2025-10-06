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
    csv_path: Optional[Path] = None
) -> None:
    """Main execution flow for the tax sales validator.

    Orchestrates the complete workflow:
    1. Web scraping and download (or skip if csv_path provided)
    2. File extraction
    3. Data loading into DataFrame
    4. CUF information extraction

    Args:
        year: Year for the report (default: current year)
        month: Month to download report for (default: previous month)
        debug: Enable debug mode with detailed logging
        skip_scraping: Skip web scraping and use existing CSV file
        csv_path: Path to existing CSV file (used with skip_scraping)
    """
    start_time = datetime.now()

    # Use current year if not specified
    if year is None:
        year = Config.get_current_year()

    # Use previous month if not specified
    if month is None:
        month = Config.get_previous_month()

    print("\n" + "=" * 80)
    print("🧾 TAX SALES VALIDATOR - Starting")
    print("=" * 80)
    print(f"📅 Target period: {month} {year}")
    print(f"🕐 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    try:
        # Handle skip_scraping mode
        if skip_scraping:
            if csv_path is None:
                # Find the most recent CSV file
                csv_path = find_latest_csv()
                if csv_path is None:
                    raise FileNotFoundError(
                        "No CSV file found. Please run without --skip-scraping first "
                        "or specify a CSV file path."
                    )

            print("=" * 80)
            print("⚡ SKIP SCRAPING MODE - Using existing CSV")
            print("=" * 80)
            print(f"📁 CSV file: {csv_path}")
            print("=" * 80 + "\n")

            # Verify CSV file exists
            if not FileManager.validate_csv_exists(csv_path):
                raise FileNotFoundError(f"CSV file not found or invalid: {csv_path}")

        else:
            # Phase 1: Web Scraping and Download
            print("=" * 80)
            print("PHASE 1: WEB SCRAPING AND DOWNLOAD")
            print("=" * 80 + "\n")

            async with WebScraper(headless=not debug) as scraper:
                zip_path = await scraper.run_full_flow(year=year, month=month)

            # Verify ZIP file exists
            if not zip_path.exists():
                raise FileNotFoundError(f"Downloaded ZIP file not found: {zip_path}")

            # Display ZIP file info
            zip_info = FileManager.get_file_info(zip_path)
            print(f"\n📦 ZIP File Info:")
            print(f"   - Name: {zip_info['name']}")
            print(f"   - Size: {zip_info['size_mb']} MB")
            print(f"   - Downloaded: {zip_info['created'].strftime('%Y-%m-%d %H:%M:%S')}")

            # Phase 2: File Extraction
            print("\n" + "=" * 80)
            print("PHASE 2: FILE EXTRACTION")
            print("=" * 80 + "\n")

            csv_path = FileManager.extract_zip(zip_path)

            # Verify CSV file exists
            if not FileManager.validate_csv_exists(csv_path):
                raise FileNotFoundError(f"Extracted CSV file not found or invalid: {csv_path}")

        # Display CSV file info
        csv_info = FileManager.get_file_info(csv_path)
        print(f"\n📄 CSV File Info:")
        print(f"   - Name: {csv_info['name']}")
        print(f"   - Size: {csv_info['size_mb']} MB")
        print(f"   - Rows (approx): {csv_info['size_bytes'] // 100:,}")  # Rough estimate

        # Phase 3: Data Loading
        print("\n" + "=" * 80)
        print("PHASE 3: DATA LOADING")
        print("=" * 80 + "\n")

        df = DataProcessor.load_csv_to_dataframe(csv_path)

        # Validate DataFrame
        if not DataProcessor.validate_dataframe(df, min_rows=1):
            raise ValueError("DataFrame validation failed")

        # Get and display summary
        summary = DataProcessor.get_dataframe_summary(df)

        print(f"\n📊 DataFrame Summary:")
        print(f"   - Rows: {summary['rows']:,}")
        print(f"   - Columns: {summary['columns']}")
        print(f"   - Memory: {summary['memory_usage_mb']} MB")

        if "date_range" in summary:
            print(f"   - Date Range: {summary['date_range']['min']} to {summary['date_range']['max']}")

        # Print detailed info if debug mode
        if debug:
            DataProcessor.print_dataframe_info(df, sample_rows=10)

        # Phase 4: CUF Processing
        print("\n" + "=" * 80)
        print("PHASE 4: CUF INFORMATION EXTRACTION")
        print("=" * 80 + "\n")

        processor = SalesProcessor(debug=debug)
        df_siat = processor.extract_cuf_information(df)

        # Display validation results
        validation = processor.validate_extracted_data(df_siat)
        print("\n📋 CUF Extraction Validation:")
        for field, stats in validation.items():
            print(f"   - {field}: {stats['populated_rows']}/{stats['total_rows']} ({stats['fill_rate']})")

        # Save processed data with SIAT suffix for clarity
        output_filename = f"processed_siat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path = Config.PROCESSED_DIR / output_filename
        processor.save_processed_data(df_siat, output_path)

        # Phase 5: Inventory Data Retrieval
        print("\n" + "=" * 80)
        print("PHASE 5: INVENTORY DATA RETRIEVAL")
        print("=" * 80 + "\n")

        # Calculate date range from year and month
        start_date, end_date = Config.get_date_range_from_month(year, month)
        print(f"📅 Querying inventory for period:")
        print(f"   - Year: {year}")
        print(f"   - Month: {month}")
        print(f"   - Date Range: {start_date} to {end_date}")

        # Query inventory database
        with InventoryConnector() as inventory:
            # Test connection first
            if not inventory.test_connection():
                raise ConnectionError("Failed to connect to inventory database")

            # Get inventory sales data
            df_inventory = inventory.get_sales_from_inventory(
                year=year,
                start_date=start_date,
                end_date=end_date
            )

        # Display inventory summary
        print(f"\n📊 Inventory Data Summary:")
        print(f"   - Total rows: {len(df_inventory):,}")
        print(f"   - Total columns: {len(df_inventory.columns)}")
        
        if len(df_inventory) > 0:
            # Basic statistics
            if "total" in df_inventory.columns:
                total_amount = df_inventory["total"].sum()
                print(f"   - Total sales amount: Bs. {total_amount:,.2f}")
            
            if "numeroFactura" in df_inventory.columns:
                unique_invoices = df_inventory["numeroFactura"].nunique()
                print(f"   - Unique invoices: {unique_invoices:,}")
            
            if "cuf" in df_inventory.columns:
                invoices_with_cuf = df_inventory["cuf"].notna().sum()
                print(f"   - Invoices with CUF: {invoices_with_cuf:,}")
            
            # Date range
            if "fechaFac" in df_inventory.columns:
                min_date = df_inventory["fechaFac"].min()
                max_date = df_inventory["fechaFac"].max()
                print(f"   - Date range: {min_date} to {max_date}")

        # Save inventory data
        inventory_filename = f"inventory_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        inventory_path = Config.PROCESSED_DIR / inventory_filename
        df_inventory.to_csv(inventory_path, index=False, encoding="utf-8")
        print(f"\n💾 Inventory data saved: {inventory_path}")

        # Success Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 80)
        print("✅ SUCCESS - All phases completed")
        print("=" * 80)
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        if not skip_scraping:
            print(f"📁 ZIP file: {zip_path}")
        print(f"📁 CSV file: {csv_path}")
        print(f"📁 SIAT processed file: {output_path}")
        print(f"� Inventory file: {inventory_path}")
        print(f"📊 SIAT data: {summary['rows']:,} rows × {len(df_siat.columns)} columns (with CUF fields)")
        print(f"� Inventory data: {len(df_inventory):,} rows × {len(df_inventory.columns)} columns")
        print(f"�📅 Period: {month} {year} ({start_date} to {end_date})")
        print("=" * 80 + "\n")
        
        print("🎯 Ready for Phase 6: Invoice Comparison and Validation")
        print("   Both datasets loaded and ready for comparison:")
        print(f"   - df_siat: SIAT tax report data ({len(df_siat)} rows)")
        print(f"   - df_inventory: Inventory system data ({len(df_inventory)} rows)")
        print("=" * 80 + "\n")

        # Optional: Clean up old files (older than 7 days) only if we did scraping
        if not skip_scraping:
            print("🧹 Cleaning up old files...")
            deleted_count = FileManager.cleanup_old_files(
                Config.DOWNLOAD_DIR, days=7, pattern="*.zip", dry_run=False
            )
            if deleted_count > 0:
                print(f"✅ Cleaned up {deleted_count} old file(s)")

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

    args = parser.parse_args()

    # Convert csv_path string to Path if provided
    csv_path_obj = Path(args.csv_path) if args.csv_path else None

    # Run async main function
    asyncio.run(
        main(
            year=args.year,
            month=args.month,
            debug=args.debug,
            skip_scraping=args.skip_scraping,
            csv_path=csv_path_obj
        )
    )


if __name__ == "__main__":
    run()

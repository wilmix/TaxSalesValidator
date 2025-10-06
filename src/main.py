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
from .web_scraper import WebScraper


async def main(
    year: Optional[int] = None,
    month: Optional[str] = None,
    debug: bool = False
) -> None:
    """Main execution flow for the tax sales validator.

    Orchestrates the complete workflow:
    1. Web scraping and download
    2. File extraction
    3. Data loading into DataFrame

    Args:
        year: Year for the report (default: current year)
        month: Month to download report for (default: previous month)
        debug: Enable debug mode with detailed logging
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

        # Phase 3: Data Loading and Processing
        print("\n" + "=" * 80)
        print("PHASE 3: DATA LOADING AND PROCESSING")
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

        # Success Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("=" * 80)
        print("✅ SUCCESS - All phases completed")
        print("=" * 80)
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print(f"📁 ZIP file: {zip_path}")
        print(f"📁 CSV file: {csv_path}")
        print(f"📊 Data loaded: {summary['rows']:,} rows × {summary['columns']} columns")
        print(f"📅 Period: {month} {year}")
        print("=" * 80 + "\n")

        # Optional: Clean up old files (older than 7 days)
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

    args = parser.parse_args()

    # Run async main function
    asyncio.run(main(year=args.year, month=args.month, debug=args.debug))


if __name__ == "__main__":
    run()

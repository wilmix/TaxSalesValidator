"""Data processor module for TaxSalesValidator.

This module handles CSV reading and DataFrame operations using Pandas.
Responsibility: All data transformation and analysis.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

from .config import Config


class DataProcessor:
    """Processes sales data from CSV files into pandas DataFrames.

    Responsibilities:
    - Load CSV files with proper encoding detection
    - Validate DataFrame structure
    - Provide data summaries
    - Prepare data for validation
    """

    @staticmethod
    def load_csv_to_dataframe(csv_path: Path, encoding: Optional[str] = None) -> pd.DataFrame:
        """Load CSV file into a pandas DataFrame.

        Automatically tries multiple encodings if not specified.

        Args:
            csv_path: Path to the CSV file
            encoding: Specific encoding to use (default: auto-detect)

        Returns:
            DataFrame containing the CSV data

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            pd.errors.EmptyDataError: If CSV file is empty
            UnicodeDecodeError: If all encoding attempts fail
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        print(f"📊 Loading CSV into DataFrame: {csv_path.name}")

        # If encoding specified, use it directly
        if encoding:
            df = pd.read_csv(
                csv_path,
                encoding=encoding,
                on_bad_lines='skip',  # Skip malformed lines
                low_memory=False
            )
            print(f"✅ CSV loaded with encoding: {encoding}")
            return df

        # Try multiple encodings
        for enc in Config.CSV_ENCODING_OPTIONS:
            try:
                df = pd.read_csv(
                    csv_path,
                    encoding=enc,
                    on_bad_lines='skip',  # Skip malformed lines
                    low_memory=False
                )
                print(f"✅ CSV loaded with encoding: {enc}")
                return df
            except UnicodeDecodeError:
                print(f"⚠️  Failed to load with encoding: {enc}")
                continue

        # If all encodings fail
        raise UnicodeDecodeError(
            "utf-8",
            b"",
            0,
            1,
            f"Could not load CSV with any of: {Config.CSV_ENCODING_OPTIONS}",
        )

    @staticmethod
    def validate_dataframe(df: pd.DataFrame, min_rows: int = 1) -> bool:
        """Validate that DataFrame has expected structure.

        Args:
            df: DataFrame to validate
            min_rows: Minimum number of rows expected

        Returns:
            True if DataFrame is valid, False otherwise
        """
        if df is None:
            print("❌ DataFrame is None")
            return False

        if df.empty:
            print("❌ DataFrame is empty")
            return False

        if len(df) < min_rows:
            print(f"⚠️  DataFrame has fewer than {min_rows} rows: {len(df)}")
            return False

        print(f"✅ DataFrame validation passed: {len(df)} rows")
        return True

    @staticmethod
    def get_dataframe_summary(df: pd.DataFrame) -> dict:
        """Get summary statistics and metadata about the DataFrame.

        Args:
            df: DataFrame to summarize

        Returns:
            Dictionary with summary information
        """
        summary = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
            "null_counts": df.isnull().sum().to_dict(),
            "dtypes": df.dtypes.astype(str).to_dict(),
        }

        # Add date range if date columns exist
        date_columns = df.select_dtypes(include=["datetime64"]).columns
        if len(date_columns) > 0:
            first_date_col = date_columns[0]
            summary["date_range"] = {
                "column": first_date_col,
                "min": str(df[first_date_col].min()),
                "max": str(df[first_date_col].max()),
            }

        # Add numeric summaries if numeric columns exist
        numeric_columns = df.select_dtypes(include=["number"]).columns
        if len(numeric_columns) > 0:
            summary["numeric_columns"] = numeric_columns.tolist()

        return summary

    @staticmethod
    def print_dataframe_info(df: pd.DataFrame, sample_rows: int = 5) -> None:
        """Print detailed information about the DataFrame.

        Args:
            df: DataFrame to print info for
            sample_rows: Number of sample rows to display
        """
        print("\n" + "=" * 80)
        print("📊 DATAFRAME INFORMATION")
        print("=" * 80)

        # Basic info
        print(f"\n📏 Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

        # Column info
        print(f"\n📋 Columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
            print(f"  {i:2d}. {col:40s} ({df[col].dtype}) - {null_count} nulls ({null_pct:.1f}%)")

        # Memory usage
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        print(f"\n💾 Memory usage: {memory_mb:.2f} MB")

        # Sample data
        if len(df) > 0:
            print(f"\n📝 First {min(sample_rows, len(df))} rows:")
            print(df.head(sample_rows).to_string())

            print(f"\n📝 Last {min(sample_rows, len(df))} rows:")
            print(df.tail(sample_rows).to_string())

        # Summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            print(f"\n📈 Summary statistics (numeric columns):")
            print(df[numeric_cols].describe().to_string())

        print("\n" + "=" * 80 + "\n")

    @staticmethod
    def export_to_excel(df: pd.DataFrame, output_path: Path) -> None:
        """Export DataFrame to Excel file.

        Args:
            df: DataFrame to export
            output_path: Path where Excel file will be saved

        Raises:
            ImportError: If openpyxl not installed
        """
        print(f"📤 Exporting DataFrame to Excel: {output_path.name}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_excel(output_path, index=False, engine="openpyxl")

        print(f"✅ Excel file created: {output_path}")

    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize column names.

        Converts to lowercase, replaces spaces with underscores, removes special characters.

        Args:
            df: DataFrame with columns to clean

        Returns:
            DataFrame with cleaned column names
        """
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace(r"[^\w_]", "", regex=True)
        )

        print(f"✅ Column names cleaned")

        return df

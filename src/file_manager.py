"""File manager module for TaxSalesValidator.

This module handles file operations: ZIP extraction, CSV file management, and cleanup.
Responsibility: All file system operations.
"""

import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import Config


class FileManager:
    """Manages file operations for downloaded ZIP and CSV files.

    Responsibilities:
    - Extract CSV from ZIP archives
    - Validate file integrity
    - Clean up old files
    - Provide file metadata
    """

    @staticmethod
    def extract_zip(zip_path: Path) -> Path:
        """Extract CSV file from ZIP archive.

        Args:
            zip_path: Path to the ZIP file

        Returns:
            Path to the extracted CSV file

        Raises:
            FileNotFoundError: If ZIP file doesn't exist
            zipfile.BadZipFile: If ZIP file is corrupted
            ValueError: If no CSV file found in ZIP
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        print(f"📦 Extracting CSV from ZIP: {zip_path.name}")

        # Generate timestamped output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Config.PROCESSED_DIR / f"sales_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract ZIP contents
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Get list of files in ZIP
            file_list = zip_ref.namelist()

            # Find CSV file (should be only one)
            csv_files = [f for f in file_list if f.lower().endswith(".csv")]

            if not csv_files:
                raise ValueError(f"No CSV file found in ZIP: {zip_path}")

            # Extract the CSV file
            csv_filename = csv_files[0]
            zip_ref.extract(csv_filename, output_dir)

            extracted_csv_path = output_dir / csv_filename

        return extracted_csv_path

    @staticmethod
    def get_latest_download(directory: Path = Config.DOWNLOAD_DIR) -> Optional[Path]:
        """Get the most recently downloaded ZIP file.

        Args:
            directory: Directory to search for ZIP files

        Returns:
            Path to the latest ZIP file, or None if no files found
        """
        zip_files = list(directory.glob("*.zip"))

        if not zip_files:
            return None

        # Sort by modification time, newest first
        latest_file = max(zip_files, key=lambda p: p.stat().st_mtime)

        return latest_file

    @staticmethod
    def validate_csv_exists(csv_path: Path) -> bool:
        """Validate that CSV file exists and is readable.

        Args:
            csv_path: Path to the CSV file

        Returns:
            True if file exists and is readable, False otherwise
        """
        if not csv_path.exists():
            print(f"⚠️  CSV file not found: {csv_path}")
            return False

        if not csv_path.is_file():
            print(f"⚠️  Path is not a file: {csv_path}")
            return False

        if csv_path.stat().st_size == 0:
            print(f"⚠️  CSV file is empty: {csv_path}")
            return False

        return True

    @staticmethod
    def get_file_info(file_path: Path) -> dict:
        """Get metadata information about a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file metadata (size, created, modified)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = file_path.stat()

        return {
            "name": file_path.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
        }

    @staticmethod
    def cleanup_old_files(
        directory: Path, days: int = 7, pattern: str = "*.zip", dry_run: bool = False
    ) -> int:
        """Delete files older than specified days.

        Args:
            directory: Directory to clean up
            days: Delete files older than this many days
            pattern: File pattern to match (e.g., "*.zip", "*.csv")
            dry_run: If True, only print what would be deleted

        Returns:
            Number of files deleted (or would be deleted in dry_run mode)
        """
        if not directory.exists():
            print(f"⚠️  Directory not found: {directory}")
            return 0

        cutoff_date = datetime.now() - timedelta(days=days)
        files_to_delete = []

        # Find files matching pattern and older than cutoff
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    files_to_delete.append(file_path)

        if not files_to_delete:
            print(f"ℹ️  No files older than {days} days found in {directory}")
            return 0

        # Delete or report files
        for file_path in files_to_delete:
            if dry_run:
                print(f"🔍 Would delete: {file_path.name}")
            else:
                file_path.unlink()
                print(f"🗑️  Deleted: {file_path.name}")

        action = "Would delete" if dry_run else "Deleted"
        print(f"✅ {action} {len(files_to_delete)} old file(s)")

        return len(files_to_delete)

    @staticmethod
    def ensure_directory_structure() -> None:
        """Ensure all necessary directories exist."""
        Config.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        Config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

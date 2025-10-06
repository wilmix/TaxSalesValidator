"""SAS Database Connector for TaxSalesValidator.

This module handles MySQL database connection and operations
for the SAS (Sistema de Administración y Servicios) accounting system.
Following SRP: Only responsible for database connectivity and CRUD operations.
"""

from typing import Dict, List, Optional

import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import Config


class SasConnector:
    """MySQL database connector for SAS accounting system.

    Handles connection management and data synchronization operations
    for the sales_registers table in the SAS database.
    """

    def __init__(self, debug: bool = False) -> None:
        """Initialize the SAS connector with configuration from environment.
        
        Args:
            debug: Enable debug mode with detailed logging
        """
        self.host = Config.SAS_DB_HOST
        self.port = Config.SAS_DB_PORT
        self.database = Config.SAS_DB_NAME
        self.user = Config.SAS_DB_USER
        self.password = Config.SAS_DB_PASSWORD
        self.debug = debug
        self._engine: Optional[Engine] = None

    def _log(self, message: str) -> None:
        """Log message if debug mode is enabled.
        
        Args:
            message: Message to log
        """
        if self.debug:
            print(f"[SasConnector] {message}")

    def _create_connection_string(self) -> str:
        """Create SQLAlchemy connection string for MySQL.

        Returns:
            Connection string in format: mysql+pymysql://user:pass@host:port/db
        """
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?charset=utf8mb4"
        )

    def _get_engine(self) -> Engine:
        """Get or create SQLAlchemy engine.

        Returns:
            SQLAlchemy Engine instance

        Raises:
            Exception: If database connection fails
        """
        if self._engine is None:
            try:
                connection_string = self._create_connection_string()
                self._engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,  # Verify connections before using
                    pool_recycle=3600,  # Recycle connections after 1 hour
                    echo=self.debug,  # Log SQL queries if debug enabled
                )
                self._log("Database engine created successfully")
            except Exception as e:
                self._log(f"Failed to create database engine: {e}")
                raise

        return self._engine

    def test_connection(self) -> bool:
        """Test database connectivity.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            engine = self._get_engine()
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                success = row and row[0] == 1
                if success:
                    self._log("Connection test successful")
                else:
                    self._log("Connection test failed - unexpected result")
                return success
        except Exception as e:
            self._log(f"Connection test failed: {e}")
            return False

    def get_database_info(self) -> Dict[str, str]:
        """Get basic database information.

        Returns:
            Dictionary with database version and connection info

        Raises:
            Exception: If query fails
        """
        try:
            engine = self._get_engine()
            with engine.connect() as connection:
                # Get MySQL version
                version_result = connection.execute(text("SELECT VERSION() as version"))
                version = version_result.fetchone()[0]

                # Get current database
                db_result = connection.execute(text("SELECT DATABASE() as db"))
                current_db = db_result.fetchone()[0]

                info = {
                    "mysql_version": version,
                    "current_database": current_db,
                    "host": self.host,
                    "port": str(self.port),
                    "user": self.user,
                }
                
                self._log(f"Database info retrieved: {current_db} on {self.host}")
                return info
        except Exception as e:
            self._log(f"Failed to get database info: {e}")
            raise

    def get_table_info(self, table_name: str = "sales_registers") -> Dict:
        """Get information about a specific table.
        
        Args:
            table_name: Name of the table to inspect
        
        Returns:
            Dictionary with table information (columns, indexes, row count)
        
        Raises:
            Exception: If query fails
        """
        try:
            engine = self._get_engine()
            with engine.connect() as connection:
                # Get column information
                columns_query = text(f"DESCRIBE {table_name}")
                columns_result = connection.execute(columns_query)
                columns = [dict(row._mapping) for row in columns_result]
                
                # Get row count
                count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
                count_result = connection.execute(count_query)
                row_count = count_result.fetchone()[0]
                
                # Get indexes
                indexes_query = text(f"SHOW INDEX FROM {table_name}")
                indexes_result = connection.execute(indexes_query)
                indexes = [dict(row._mapping) for row in indexes_result]
                
                info = {
                    "table_name": table_name,
                    "columns": columns,
                    "row_count": row_count,
                    "indexes": indexes
                }
                
                self._log(f"Table info retrieved: {table_name} ({row_count} rows)")
                return info
        except Exception as e:
            self._log(f"Failed to get table info: {e}")
            raise

    def check_duplicate_authorization_code(self, authorization_code: str) -> bool:
        """Check if an authorization code already exists in the database.
        
        Args:
            authorization_code: The CUF/authorization code to check
        
        Returns:
            True if the code exists, False otherwise
        """
        try:
            engine = self._get_engine()
            with engine.connect() as connection:
                query = text(
                    "SELECT COUNT(*) as count FROM sales_registers "
                    "WHERE authorization_code = :auth_code"
                )
                result = connection.execute(query, {"auth_code": authorization_code})
                count = result.fetchone()[0]
                
                exists = count > 0
                if exists:
                    self._log(f"Authorization code exists: {authorization_code[:20]}...")
                
                return exists
        except Exception as e:
            self._log(f"Error checking duplicate: {e}")
            raise

    def upsert_records(
        self, 
        records: List[Dict], 
        batch_size: Optional[int] = None
    ) -> Dict[str, int]:
        """Insert or update multiple records using UPSERT strategy with ATOMIC transaction.
        
        **IMPORTANT: ALL OR NOTHING strategy**
        - Uses a SINGLE transaction for ALL records
        - Processes in batches for progress reporting only
        - If ANY error occurs, ENTIRE transaction is rolled back
        - Database remains unchanged if sync fails
        
        Uses INSERT ... ON DUPLICATE KEY UPDATE for MySQL.
        
        Args:
            records: List of dictionaries containing record data
            batch_size: Number of records per batch for progress display (default: from config)
        
        Returns:
            Dictionary with sync statistics (inserted, updated, errors)
        
        Raises:
            Exception: If synchronization fails (triggers ROLLBACK of ALL changes)
        """
        if batch_size is None:
            batch_size = Config.SAS_SYNC_BATCH_SIZE
        
        stats = {
            "inserted": 0,
            "updated": 0,
            "errors": 0,
            "total_processed": 0
        }
        
        if not records:
            self._log("No records to sync")
            return stats
        
        self._log("=" * 60)
        self._log("🔒 ATOMIC TRANSACTION MODE: ALL OR NOTHING")
        self._log(f"Starting UPSERT for {len(records)} records (batch size: {batch_size})")
        self._log("If any error occurs, ALL changes will be rolled back")
        self._log("=" * 60)
        
        engine = self._get_engine()
        
        try:
            # BEGIN TRANSACTION - Everything happens inside this block
            with engine.begin() as connection:
                self._log("✅ Transaction started")
                
                # Process in batches (for progress display only)
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(records) + batch_size - 1) // batch_size
                    
                    self._log(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} records)...")
                    
                    for record in batch:
                        try:
                            # Build UPSERT query
                            query = self._build_upsert_query()
                            
                            # Execute upsert (still in transaction, not committed yet)
                            result = connection.execute(text(query), record)
                            
                            # Determine if it was INSERT or UPDATE
                            # rowcount = 1 for INSERT, 2 for UPDATE
                            if result.rowcount == 1:
                                stats["inserted"] += 1
                            elif result.rowcount == 2:
                                stats["updated"] += 1
                            
                            stats["total_processed"] += 1
                            
                        except Exception as e:
                            # ANY error triggers rollback of EVERYTHING
                            error_msg = (
                                f"❌ ERROR in record {record.get('authorization_code', 'UNKNOWN')[:20]}...: {e}\n"
                                f"🔄 ROLLING BACK ALL {stats['total_processed']} previous changes..."
                            )
                            self._log(error_msg)
                            raise  # Re-raise to trigger rollback
                
                # If we reach here, ALL batches processed successfully
                # Commit happens automatically at end of 'with' block
                self._log("=" * 60)
                self._log("✅ All records processed successfully")
                self._log(f"💾 COMMITTING transaction: {stats['inserted']} inserted, {stats['updated']} updated")
                self._log("=" * 60)
                
        except Exception as e:
            # Rollback happens automatically on exception
            self._log("=" * 60)
            self._log(f"❌ TRANSACTION FAILED - ALL CHANGES ROLLED BACK")
            self._log(f"Error: {str(e)}")
            self._log(f"Database remains unchanged (0 records affected)")
            self._log("=" * 60)
            raise
        
        return stats

    def _build_upsert_query(self) -> str:
        """Build the UPSERT SQL query for sales_registers table.
        
        Returns:
            SQL query string with placeholders
        """
        # Column names for INSERT
        columns = [
            "invoice_date", "invoice_number", "authorization_code",
            "customer_nit", "complement", "customer_name",
            "total_sale_amount", "ice_amount", "iehd_amount", "ipj_amount",
            "fees", "other_non_vat_items", "exports_exempt_operations",
            "zero_rate_taxed_sales", "subtotal",
            "discounts_bonuses_rebates_subject_to_vat", "gift_card_amount",
            "debit_tax_base_amount", "debit_tax", "status", "control_code",
            "sale_type", "right_to_tax_credit", "consolidation_status",
            "branch_office", "modality", "emission_type", "invoice_type",
            "sector", "author"
        ]
        
        # Build placeholders for VALUES
        placeholders = ", ".join([f":{col}" for col in columns])
        columns_str = ", ".join(columns)
        
        # Build UPDATE clause (exclude unique key and timestamps)
        update_columns = [col for col in columns if col not in ["authorization_code", "author"]]
        update_clause = ", ".join([f"{col} = VALUES({col})" for col in update_columns])
        
        query = f"""
        INSERT INTO sales_registers ({columns_str})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
            {update_clause},
            updated_at = CURRENT_TIMESTAMP
        """
        
        return query

    def close(self) -> None:
        """Close database connection and dispose of engine."""
        if self._engine is not None:
            self._log("Closing database connection")
            self._engine.dispose()
            self._engine = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed."""
        self.close()

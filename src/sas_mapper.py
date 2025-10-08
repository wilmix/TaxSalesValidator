"""SAS Data Mapper for TaxSalesValidator.

This module handles data transformation from SIAT format to SAS sales_registers format.
Following SRP: Only responsible for data mapping and validation.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

import pandas as pd


class SasMapper:
    """Maps SIAT DataFrame to SAS sales_registers format.
    
    Responsibilities:
    - Transform SIAT column names to sales_registers column names
    - Convert data types (strings to decimals, dates, etc.)
    - Handle NULL/empty values
    - Compute derived fields (right_to_tax_credit)
    - Validate transformed data
    """
    
    # SIAT column -> sales_registers column mapping
    FIELD_MAPPING = {
        # Direct mappings from SIAT CSV
        "FECHA DE LA FACTURA": "invoice_date",
        "CODIGO DE AUTORIZACIÓN": "authorization_code",
        "NIT / CI CLIENTE": "customer_nit",
        "COMPLEMENTO": "complement",
        "NOMBRE O RAZON SOCIAL": "customer_name",
        "IMPORTE TOTAL DE LA VENTA": "total_sale_amount",
        "IMPORTE ICE": "ice_amount",
        "IMPORTE IEHD": "iehd_amount",
        "IMPORTE IPJ": "ipj_amount",
        "TASAS": "fees",
        "OTROS NO SUJETOS AL IVA": "other_non_vat_items",
        "EXPORTACIONES Y OPERACIONES EXENTAS": "exports_exempt_operations",
        "VENTAS GRAVADAS A TASA CERO": "zero_rate_taxed_sales",
        "SUBTOTAL": "subtotal",
        "DESCUENTOS BONIFICACIONES Y REBAJAS SUJETAS AL IVA": "discounts_bonuses_rebates_subject_to_vat",
        "IMPORTE GIFT CARD": "gift_card_amount",
        "IMPORTE BASE PARA DEBITO FISCAL": "debit_tax_base_amount",
        "DEBITO FISCAL": "debit_tax",
        "ESTADO": "status",
        "CODIGO DE CONTROL": "control_code",
        "TIPO DE VENTA": "sale_type",
        "ESTADO CONSOLIDACION": "consolidation_status",
        
        # From CUF extraction
        "NUM FACTURA": "invoice_number",
        "SUCURSAL": "branch_office",
        "MODALIDAD": "modality",
        "TIPO EMISION": "emission_type",
        "TIPO FACTURA": "invoice_type",
        "SECTOR": "sector",
    }
    
    # Decimal fields that need conversion
    DECIMAL_FIELDS = [
        "total_sale_amount", "ice_amount", "iehd_amount", "ipj_amount",
        "fees", "other_non_vat_items", "exports_exempt_operations",
        "zero_rate_taxed_sales", "subtotal",
        "discounts_bonuses_rebates_subject_to_vat", "gift_card_amount",
        "debit_tax_base_amount", "debit_tax"
    ]
    
    # Fields that can be NULL
    NULLABLE_FIELDS = [
        "complement", "control_code", "status", "right_to_tax_credit",
        "branch_office", "modality", "emission_type", "invoice_type", "sector"
    ]
    
    def __init__(self, debug: bool = False):
        """Initialize the SasMapper.
        
        Args:
            debug: Enable debug mode with detailed logging
        """
        self.debug = debug
        self.transformation_stats = {
            "total_rows": 0,
            "successful": 0,
            "errors": 0,
            "warnings": 0
        }
    
    def _log(self, message: str) -> None:
        """Log message if debug mode is enabled.
        
        Args:
            message: Message to log
        """
        if self.debug:
            print(f"[SasMapper] {message}")
    
    def transform_dataframe(self, df_siat: pd.DataFrame) -> pd.DataFrame:
        """Transform entire SIAT DataFrame to sales_registers format.
        
        Args:
            df_siat: SIAT DataFrame with CUF fields already extracted
        
        Returns:
            DataFrame in sales_registers format ready for sync
        
        Raises:
            ValueError: If required columns are missing
        """
        self._log("=" * 60)
        self._log("Starting DataFrame transformation")
        self._log(f"Input rows: {len(df_siat)}")
        
        # Validate required columns exist
        self._validate_siat_columns(df_siat)
        
        # Create new DataFrame for transformed data
        transformed_rows = []
        
        self.transformation_stats["total_rows"] = len(df_siat)
        
        for index, row in df_siat.iterrows():
            try:
                transformed_row = self._transform_row(row, index)
                transformed_rows.append(transformed_row)
                self.transformation_stats["successful"] += 1
                
                if self.debug and (index + 1) % 100 == 0:
                    self._log(f"  ✓ Transformed {index + 1}/{len(df_siat)} rows")
                    
            except Exception as e:
                self.transformation_stats["errors"] += 1
                self._log(f"  ⚠️  Error transforming row {index}: {e}")
                # Continue with other rows
        
        df_transformed = pd.DataFrame(transformed_rows)
        
        self._log("=" * 60)
        self._log(f"Transformation complete:")
        self._log(f"  - Successful: {self.transformation_stats['successful']}")
        self._log(f"  - Errors: {self.transformation_stats['errors']}")
        self._log(f"  - Output rows: {len(df_transformed)}")
        self._log("=" * 60)
        
        return df_transformed
    
    def _validate_siat_columns(self, df: pd.DataFrame) -> None:
        """Validate that required SIAT columns exist.
        
        Args:
            df: SIAT DataFrame to validate
        
        Raises:
            ValueError: If required columns are missing
        """
        required_columns = [
            "FECHA DE LA FACTURA",
            "CODIGO DE AUTORIZACIÓN",
            "NIT / CI CLIENTE",
            "NOMBRE O RAZON SOCIAL",
            "IMPORTE TOTAL DE LA VENTA",
            "NUM FACTURA",  # From CUF extraction
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {', '.join(missing_columns)}\n"
                f"Available columns: {', '.join(df.columns)}"
            )
        
        self._log(f"✅ All required columns present ({len(required_columns)} validated)")
    
    def _transform_row(self, row: pd.Series, index: int) -> Dict:
        """Transform a single row from SIAT to sales_registers format.
        
        Args:
            row: Row from SIAT DataFrame
            index: Row index for logging
        
        Returns:
            Dictionary with sales_registers fields
        """
        transformed = {}
        
        # 1. Map direct fields
        for siat_col, sas_col in self.FIELD_MAPPING.items():
            if siat_col in row.index:
                value = row[siat_col]
                
                # Handle decimal conversions
                if sas_col in self.DECIMAL_FIELDS:
                    transformed[sas_col] = self._to_decimal(value, sas_col)
                
                # Handle date conversion
                elif sas_col == "invoice_date":
                    transformed[sas_col] = self._to_date(value)
                
                # Handle string fields with length limits
                elif sas_col == "customer_name":
                    transformed[sas_col] = self._truncate_string(value, 240)
                elif sas_col == "customer_nit":
                    transformed[sas_col] = self._clean_nit(value, 15)
                elif sas_col == "authorization_code":
                    transformed[sas_col] = self._truncate_string(value, 64)
                elif sas_col == "invoice_number":
                    transformed[sas_col] = self._normalize_invoice_number(value)
                elif sas_col == "complement":
                    transformed[sas_col] = self._truncate_string(value, 5) if pd.notna(value) else None
                elif sas_col == "control_code":
                    transformed[sas_col] = self._normalize_control_code(value)
                
                # Handle varchar fields
                elif sas_col in ["status", "sale_type", "consolidation_status"]:
                    transformed[sas_col] = str(value) if pd.notna(value) else ""
                
                # Handle small varchar fields from CUF with normalization
                elif sas_col == "branch_office":
                    transformed[sas_col] = self._normalize_branch_office(value)
                elif sas_col == "sector":
                    transformed[sas_col] = self._normalize_sector(value)
                elif sas_col in ["modality", "emission_type", "invoice_type"]:
                    transformed[sas_col] = self._truncate_string(value, 10) if pd.notna(value) else None
                
                else:
                    # Default: convert to string
                    transformed[sas_col] = str(value) if pd.notna(value) else None
        
        # 2. Compute derived fields
        transformed["right_to_tax_credit"] = self._compute_right_to_tax_credit(
            transformed.get("debit_tax", Decimal("0.00"))
        )
        
        # 3. Add metadata fields
        transformed["author"] = "TaxSalesValidator"
        transformed["obs"] = None
        transformed["observations"] = None
        
        return transformed
    
    def _to_decimal(self, value, field_name: str) -> Decimal:
        """Convert value to Decimal(14,2).
        
        Args:
            value: Value to convert
            field_name: Field name for logging
        
        Returns:
            Decimal value with 2 decimal places, or 0.00 if conversion fails
        """
        if pd.isna(value) or value == "" or value is None:
            return Decimal("0.00")
        
        try:
            # Remove any whitespace and convert
            if isinstance(value, str):
                value = value.strip()
            
            decimal_value = Decimal(str(value))
            
            # Round to 2 decimal places
            return decimal_value.quantize(Decimal("0.01"))
            
        except (InvalidOperation, ValueError) as e:
            self._log(f"  ⚠️  Could not convert '{value}' to decimal for {field_name}: {e}")
            self.transformation_stats["warnings"] += 1
            return Decimal("0.00")
    
    def _to_date(self, value) -> Optional[str]:
        """Convert value to date string in YYYY-MM-DD format.
        
        Args:
            value: Value to convert (can be string or datetime)
        
        Returns:
            Date string in YYYY-MM-DD format, or None if conversion fails
        """
        if pd.isna(value) or value == "" or value is None:
            return None
        
        try:
            # If already a datetime object
            if isinstance(value, (datetime, pd.Timestamp)):
                return value.strftime("%Y-%m-%d")
            
            # Try parsing string
            if isinstance(value, str):
                # Try common formats
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                
                # If no format worked, try pandas parser
                dt = pd.to_datetime(value)
                return dt.strftime("%Y-%m-%d")
            
            return None
            
        except Exception as e:
            self._log(f"  ⚠️  Could not convert '{value}' to date: {e}")
            self.transformation_stats["warnings"] += 1
            return None
    
    def _truncate_string(self, value, max_length: int) -> Optional[str]:
        """Truncate string to maximum length.
        
        Args:
            value: Value to truncate
            max_length: Maximum length
        
        Returns:
            Truncated string or None if value is null
        """
        if pd.isna(value) or value == "" or value is None:
            return None
        
        str_value = str(value).strip()
        
        if len(str_value) > max_length:
            self._log(f"  ⚠️  Truncating string from {len(str_value)} to {max_length} chars")
            self.transformation_stats["warnings"] += 1
            return str_value[:max_length]
        
        return str_value if str_value else None
    
    def _clean_nit(self, value, max_length: int = 15) -> str:
        """Clean and format NIT/CI field.
        
        Removes spaces, dashes, and dots. Truncates to max length.
        
        Args:
            value: NIT value to clean
            max_length: Maximum length
        
        Returns:
            Cleaned NIT string
        """
        if pd.isna(value) or value == "" or value is None:
            return ""
        
        # Convert to string and clean
        nit = str(value).strip().upper()
        nit = nit.replace(" ", "").replace("-", "").replace(".", "")
        
        # Truncate if necessary
        if len(nit) > max_length:
            self._log(f"  ⚠️  Truncating NIT from {len(nit)} to {max_length} chars: {nit}")
            self.transformation_stats["warnings"] += 1
            nit = nit[:max_length]
        
        return nit
    
    def _normalize_invoice_number(self, value) -> str:
        """Normalize invoice number to consistent format.
        
        Removes leading zeros but ensures it's a valid invoice number.
        Examples: "0000006737" -> "6737", "9297" -> "9297"
        
        Args:
            value: Raw invoice number from CUF
            
        Returns:
            Normalized invoice number as string
        """
        if pd.isna(value) or value == "" or value is None:
            return ""
        
        # Convert to string and remove leading zeros
        str_value = str(value).strip().lstrip('0')
        
        # If it becomes empty (was all zeros), return original
        if not str_value:
            return str(value).strip()
        
        # Ensure it fits within 15 characters
        if len(str_value) > 15:
            self._log(f"  ⚠️  Invoice number too long: {str_value}")
            self.transformation_stats["warnings"] += 1
            return str_value[:15]
        
        return str_value
    
    def _normalize_control_code(self, value) -> str:
        """Normalize control code.
        
        If empty/null in SIAT CSV, return '0'.
        Otherwise, return the value from SIAT CSV.
        
        Args:
            value: Raw control code from SIAT CSV
            
        Returns:
            '0' if empty/null, otherwise the original value
        """
        if pd.isna(value) or value == "" or value is None:
            return "0"
        
        # Return the original value if it exists
        return str(value).strip()
    
    def _normalize_branch_office(self, value) -> str:
        """Normalize branch office to consistent format.
        
        Removes leading zeros for consistency.
        Examples: "0000" -> "0", "0005" -> "5"
        
        Args:
            value: Raw branch office from CUF
            
        Returns:
            Normalized branch office as string
        """
        if pd.isna(value) or value == "" or value is None:
            return ""
        
        # Convert to string and remove leading zeros
        str_value = str(value).strip().lstrip('0')
        
        # If it becomes empty (was all zeros), return "0"
        if not str_value:
            return "0"
        
        return str_value
    
    def _normalize_sector(self, value) -> str:
        """Normalize sector to consistent format.
        
        Removes leading zeros for consistency.
        Examples: "01" -> "1", "1" -> "1"
        
        Args:
            value: Raw sector from CUF
            
        Returns:
            Normalized sector as string
        """
        if pd.isna(value) or value == "" or value is None:
            return ""
        
        # Convert to string and remove leading zeros
        str_value = str(value).strip().lstrip('0')
        
        # If it becomes empty (was all zeros), return "0"
        if not str_value:
            return "0"
        
        return str_value
    
    def _compute_right_to_tax_credit(self, debit_tax: Decimal) -> Optional[int]:
        """Compute if invoice has right to tax credit.
        
        Logic: If debit_tax > 0, then has right to credit (1), else 0 or NULL.
        
        Args:
            debit_tax: Debit tax amount
        
        Returns:
            1 if has right to credit, 0 if not, None if not applicable
        """
        if debit_tax is None:
            return None
        
        try:
            return 1 if debit_tax > Decimal("0.00") else 0
        except:
            return None
    
    def get_transformation_stats(self) -> Dict:
        """Get statistics about the transformation.
        
        Returns:
            Dictionary with transformation statistics
        """
        return self.transformation_stats.copy()
    
    def validate_transformed_data(self, df: pd.DataFrame) -> Dict:
        """Validate transformed DataFrame.
        
        Args:
            df: Transformed DataFrame to validate
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            "total_rows": len(df),
            "issues": [],
            "is_valid": True
        }
        
        # Check required fields are not null
        required_not_null = [
            "invoice_date", "invoice_number", "authorization_code",
            "customer_nit", "customer_name", "total_sale_amount"
        ]
        
        for field in required_not_null:
            if field in df.columns:
                null_count = df[field].isna().sum()
                if null_count > 0:
                    validation["issues"].append(
                        f"{field}: {null_count} null values (required field)"
                    )
                    validation["is_valid"] = False
        
        # Check decimal fields are valid
        for field in self.DECIMAL_FIELDS:
            if field in df.columns:
                # Check for any non-numeric after transformation
                try:
                    df[field].astype(float)
                except:
                    validation["issues"].append(
                        f"{field}: Contains non-numeric values"
                    )
                    validation["is_valid"] = False
        
        # Check string length limits
        length_checks = {
            "authorization_code": 64,
            "customer_nit": 15,
            "customer_name": 240,
            "invoice_number": 15,
        }
        
        for field, max_len in length_checks.items():
            if field in df.columns:
                too_long = df[field].astype(str).str.len() > max_len
                if too_long.any():
                    count = too_long.sum()
                    validation["issues"].append(
                        f"{field}: {count} values exceed {max_len} characters"
                    )
                    validation["is_valid"] = False
        
        self._log(f"Validation: {'✅ PASS' if validation['is_valid'] else '❌ FAIL'}")
        if validation["issues"]:
            for issue in validation["issues"]:
                self._log(f"  ⚠️  {issue}")
        
        return validation

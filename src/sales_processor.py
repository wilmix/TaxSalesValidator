"""Sales data processor for extracting CUF information.

This module contains the SalesProcessor class that handles the extraction
of detailed information from the CUF (Código Único de Facturación) field.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional


class SalesProcessor:
    """Process sales data and extract information from CUF codes.

    This class is responsible for parsing the CODIGO DE AUTORIZACIÓN (CUF)
    field and extracting specific information like branch, modality, invoice
    type, etc.

    The CUF extraction follows this process:
    1. Validate the authorization code is at least 42 characters
    2. Convert first 42 hex characters to decimal integer
    3. Convert decimal to string
    4. Extract substring from position 27 onwards (minimum 24 chars)
    5. Parse fixed positions for specific fields
    """

    # CUF field positions (after position 27)
    CUF_FIELDS = {
        'SUCURSAL': (0, 4),           # Branch office code
        'MODALIDAD': (4, 5),           # Modality
        'TIPO EMISION': (5, 6),        # Emission type
        'TIPO FACTURA': (6, 7),        # Invoice type
        'SECTOR': (7, 9),              # Document sector
        'NUM FACTURA': (9, 19),        # Invoice number
        'PV': (19, 23),                # Point of sale
        'CODIGO AUTOVERIFICADOR': (23, 24)  # Auto-verification code
    }

    def __init__(self, debug: bool = False):
        """Initialize the SalesProcessor.

        Args:
            debug: Enable debug mode for detailed logging
        """
        self.debug = debug
        self.processed_count = 0
        self.error_count = 0

    def extract_cuf_information(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract CUF information from authorization codes.

        Processes the 'CODIGO DE AUTORIZACIÓN' column and extracts multiple
        fields according to the CUF specification.

        Args:
            df: DataFrame containing the 'CODIGO DE AUTORIZACIÓN' column

        Returns:
            DataFrame with additional columns containing extracted CUF info

        Raises:
            ValueError: If 'CODIGO DE AUTORIZACIÓN' column is not found
        """
        if 'CODIGO DE AUTORIZACIÓN' not in df.columns:
            raise ValueError(
                "Column 'CODIGO DE AUTORIZACIÓN' not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

        print("\n" + "=" * 80)
        print("📊 EXTRACTING CUF INFORMATION")
        print("=" * 80)
        print(f"Total rows to process: {len(df)}")
        print("=" * 80 + "\n")

        # Initialize new columns
        for field_name in self.CUF_FIELDS.keys():
            df[field_name] = ''

        # Process each row
        for index, row in df.iterrows():
            try:
                self._process_single_cuf(df, index, row)
                self.processed_count += 1

                # Show progress every 100 rows
                if (index + 1) % 100 == 0:
                    print(f"  ✓ Processed {index + 1} rows...")

            except Exception as e:
                self.error_count += 1
                error_msg = (
                    f"Error processing authorization code at row {index}: "
                    f"{str(e)}"
                )
                if self.debug:
                    print(f"  ⚠️  {error_msg}")

        # Summary
        print("\n" + "-" * 80)
        print(f"✅ Successfully processed: {self.processed_count} rows")
        print(f"⚠️  Errors encountered: {self.error_count} rows")
        print(f"📈 Success rate: {(self.processed_count / len(df) * 100):.2f}%")
        print("-" * 80 + "\n")

        return df

    def _process_single_cuf(
        self,
        df: pd.DataFrame,
        index: int,
        row: pd.Series
    ) -> None:
        """Process a single CUF code and extract information.

        Args:
            df: DataFrame to update with extracted values
            index: Row index to process
            row: Row data containing the authorization code
        """
        codigo = row['CODIGO DE AUTORIZACIÓN']

        # Validate authorization code
        if not isinstance(codigo, str) or len(codigo) < 42:
            if self.debug:
                print(
                    f"  ⚠️  Row {index}: Invalid code length "
                    f"({len(codigo) if isinstance(codigo, str) else 'N/A'})"
                )
            return

        # Step 1: Extract hexadecimal (first 42 characters)
        hexadecimal = codigo[:42]

        # Step 2: Convert hexadecimal to decimal
        try:
            decimal = int(hexadecimal, 16)
        except ValueError as e:
            if self.debug:
                print(f"  ⚠️  Row {index}: Invalid hexadecimal format - {e}")
            return

        # Step 3: Convert decimal to string
        cadena = str(decimal)

        # Step 4: Extract substring from position 27
        if len(cadena) <= 27:
            if self.debug:
                print(
                    f"  ⚠️  Row {index}: Decimal string too short "
                    f"(length: {len(cadena)})"
                )
            return

        cadena = cadena[27:]

        # Step 5: Verify minimum length for field extraction
        if len(cadena) < 24:
            if self.debug:
                print(
                    f"  ⚠️  Row {index}: Substring too short for field "
                    f"extraction (length: {len(cadena)})"
                )
            return

        # Step 6: Extract each field from fixed positions
        extracted_data = self._extract_fields_from_string(cadena)

        # Step 7: Assign values to DataFrame
        for field_name, value in extracted_data.items():
            df.at[index, field_name] = value

        if self.debug and index < 5:  # Show first 5 for debugging
            print(f"  ✓ Row {index}: {extracted_data}")

    def _extract_fields_from_string(self, cadena: str) -> Dict[str, str]:
        """Extract all fields from the CUF string.

        Args:
            cadena: String to extract fields from (after position 27)

        Returns:
            Dictionary with field names and extracted values
        """
        extracted = {}

        for field_name, (start, end) in self.CUF_FIELDS.items():
            if len(cadena) > start:
                # Extract substring, handling cases where string is shorter
                extracted[field_name] = cadena[start:min(end, len(cadena))]
            else:
                extracted[field_name] = ''

        return extracted

    def get_processing_stats(self) -> Dict[str, int]:
        """Get processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'success_rate': (
                (self.processed_count / (self.processed_count + self.error_count))
                if (self.processed_count + self.error_count) > 0
                else 0
            )
        }

    def validate_extracted_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """Validate the extracted CUF data.

        Args:
            df: DataFrame with extracted CUF fields

        Returns:
            Dictionary with validation results
        """
        validation_results = {}

        for field_name in self.CUF_FIELDS.keys():
            if field_name in df.columns:
                non_empty = df[field_name].astype(str).str.len() > 0
                validation_results[field_name] = {
                    'total_rows': len(df),
                    'populated_rows': non_empty.sum(),
                    'empty_rows': (~non_empty).sum(),
                    'fill_rate': f"{(non_empty.sum() / len(df) * 100):.2f}%"
                }

        return validation_results

    def save_processed_data(
        self,
        df: pd.DataFrame,
        output_path: Path
    ) -> Path:
        """Save the processed DataFrame to CSV.

        Args:
            df: DataFrame to save
            output_path: Path to save the CSV file

        Returns:
            Path to the saved file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        file_size = output_path.stat().st_size
        print(f"\n💾 Processed data saved: {output_path}")
        print(f"   File size: {file_size / 1024:.2f} KB")
        print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
        
        return output_path

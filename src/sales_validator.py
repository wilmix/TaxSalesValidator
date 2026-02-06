"""Invoice comparison and validation module.

This module handles the comparison between SIAT tax reports and inventory
system data, identifying matches, discrepancies, and generating reports.
"""

import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class ComparisonResult:
    """Container for comparison results.
    
    Attributes:
        matched_invoices: DataFrame with invoices found in both systems
        only_in_siat: DataFrame with invoices only in SIAT
        only_in_inventory: DataFrame with invoices only in inventory
        amount_mismatches: DataFrame with invoices where amounts differ
        customer_mismatches: DataFrame with invoices where customer data differs
        other_mismatches: DataFrame with other field discrepancies
    """
    matched_invoices: pd.DataFrame
    only_in_siat: pd.DataFrame
    only_in_inventory: pd.DataFrame
    amount_mismatches: pd.DataFrame
    customer_mismatches: pd.DataFrame
    other_mismatches: pd.DataFrame


@dataclass
class ComparisonStats:
    """Statistics about the comparison.

    Attributes:
        total_siat: Total invoices in SIAT (after filtering)
        total_inventory: Total invoices in inventory
        matched_count: Number of matched invoices
        only_siat_count: Number of invoices only in SIAT
        only_inventory_count: Number of invoices only in inventory
        amount_mismatch_count: Number of amount discrepancies
        customer_mismatch_count: Number of customer discrepancies
        other_mismatch_count: Number of other discrepancies
        match_rate: Percentage of matched invoices
        total_siat_amount: Total amount in SIAT (Bs.) - VALID invoices only
        total_inventory_amount: Total amount in inventory (Bs.)
        amount_difference: Absolute difference in amounts (Bs.)
        amount_difference_pct: Percentage difference in amounts
        only_siat_valid_count: Number of valid (not canceled) invoices only in SIAT
        only_siat_canceled_count: Number of canceled invoices only in SIAT
        only_siat_valid_amount: Sum of amounts for valid invoices only in SIAT (Bs.)
        branch_breakdown_siat: Dict with breakdown by branch {branch_code: {'count': int, 'amount': float}}
        branch_breakdown_inventory: Dict with breakdown by branch {branch_code: {'count': int, 'amount': float}}
    """
    total_siat: int
    total_inventory: int
    matched_count: int
    only_siat_count: int
    only_inventory_count: int
    amount_mismatch_count: int
    customer_mismatch_count: int
    other_mismatch_count: int
    match_rate: float
    total_siat_amount: float
    total_inventory_amount: float
    amount_difference: float
    amount_difference_pct: float
    only_siat_valid_count: int
    only_siat_canceled_count: int
    only_siat_valid_amount: float
    branch_breakdown_siat: Dict[str, Dict[str, float]]
    branch_breakdown_inventory: Dict[str, Dict[str, float]]


class SalesValidator:
    """Validator for comparing SIAT tax reports with inventory data.
    
    This class implements the comparison logic between tax authority reports
    and local inventory system, following these principles:
    
    - Match by CUF (primary key)
    - Filter SIAT data by MODALIDAD = 2 (INVENTARIOS only)
    - Compare specified fields field-by-field
    - Categorize discrepancies clearly
    - Generate comprehensive reports
    """
    
    # Field mapping: SIAT column -> Inventory column
    FIELD_MAPPING = {
        "CODIGO DE AUTORIZACIÓN": "cuf",
        "FECHA DE LA FACTURA": "fechaFac",
        "Nro. DE LA FACTURA": "numeroFactura",
        "NIT / CI CLIENTE": "ClienteNit",
        "NOMBRE O RAZON SOCIAL": "ClienteFactura",
        "IMPORTE TOTAL DE LA VENTA": "total",
        "ESTADO": "estado",
        "SUCURSAL": "codigoSucursal"
    }
    
    # Tolerance for amount comparison (in bolivianos)
    AMOUNT_TOLERANCE = 0.01
    
    def __init__(self, debug: bool = False):
        """Initialize the validator.
        
        Args:
            debug: Enable debug mode with detailed logging
        """
        self.debug = debug
        self._log("SalesValidator initialized")
    
    def _is_invoice_canceled(self, row: pd.Series) -> bool:
        """Check if an invoice is canceled based on ESTADO field.

        An invoice is considered VALID only if ESTADO == "VALIDA" (case-insensitive).
        All other states (ANULADA, etc.) are considered canceled/invalid.

        This is the most robust approach: instead of checking for all possible
        canceled values, we only consider "VALIDA" as valid - everything else is
        treated as canceled/invalid.

        Args:
            row: A pandas Series representing a single invoice row

        Returns:
            True if invoice is canceled/invalid (ESTADO != "VALIDA"),
            False if invoice is valid (ESTADO == "VALIDA")
        """
        if "ESTADO" not in row.index:
            return False

        estado = str(row.get("ESTADO", "")).strip().upper()

        # Only "VALIDA" is considered valid - everything else is canceled/invalid
        return estado != "VALIDA"

    def _filter_inventory_by_siat_estado(
        self,
        df_inventory: pd.DataFrame,
        df_siat: pd.DataFrame
    ) -> pd.DataFrame:
        """Filter inventory to exclude invoices that are ANULADAS in SIAT.

        This ensures fair comparison: we only compare invoices that are VALIDA in SIAT
        with their corresponding entries in Inventory. Invoices that are ANULADAS in SIAT
        should be excluded from both sides of the comparison.

        Args:
            df_inventory: Inventory DataFrame with "cuf" column
            df_siat: SIAT DataFrame with "CODIGO DE AUTORIZACIÓN" and "ESTADO" columns

        Returns:
            Filtered inventory DataFrame (only invoices that are VALIDA in SIAT)
        """
        if df_inventory.empty or df_siat.empty:
            return df_inventory

        # Get SIAT CUFs that are VALIDA (not canceled)
        siat_cuf_col = "CODIGO DE AUTORIZACIÓN"
        inv_cuf_col = "cuf"

        if siat_cuf_col not in df_siat.columns or inv_cuf_col not in df_inventory.columns:
            self._log("Warning: Missing CUF columns for filtering")
            return df_inventory

        # Filter SIAT to get only VALIDA invoices
        df_siat_valid = df_siat[~df_siat.apply(self._is_invoice_canceled, axis=1)].copy()
        valid_cufs = set(df_siat_valid[siat_cuf_col].dropna())

        # Filter inventory to only include CUFs that are VALIDA in SIAT
        original_count = len(df_inventory)
        df_inventory_filtered = df_inventory[df_inventory[inv_cuf_col].isin(valid_cufs)].copy()
        filtered_count = len(df_inventory_filtered)
        excluded_count = original_count - filtered_count

        self._log(f"Filtered inventory by SIAT ESTADO (VALIDA only):")
        self._log(f"  - Original inventory rows: {original_count}")
        self._log(f"  - Filtered inventory rows: {filtered_count}")
        self._log(f"  - Excluded rows (ANULADAS in SIAT): {excluded_count}")

        return df_inventory_filtered
    
    def _log(self, message: str) -> None:
        """Log message if debug mode is enabled.

        Args:
            message: Message to log
        """
        if self.debug:
            print(f"[SalesValidator] {message}")

    def _calculate_branch_breakdown(
        self,
        df: pd.DataFrame,
        amount_col: str,
        branch_col: str
    ) -> Dict[str, Dict[str, float]]:
        """Calculate breakdown by branch (sucursal) - VALID invoices only.

        Branch codes:
        - 0 = CENTRAL
        - 5 = SANTA CRUZ
        - 6 = POTOSI

        Args:
            df: DataFrame with branch and amount columns
            amount_col: Name of the amount column
            branch_col: Name of the branch column

        Returns:
            Dict with format: {branch_code: {'count': int, 'amount': float, 'canceled_count': int}}
            Only includes VALID invoices in count/amount (excludes ANULADAS)
            But also reports canceled_count for transparency
        """
        breakdown = {}

        if branch_col not in df.columns or amount_col not in df.columns:
            self._log(f"Warning: Missing columns for branch breakdown")
            return breakdown

        # Separate VALID and CANCELED invoices
        df_all = df.copy()
        df_valid = df_all.copy()
        df_canceled = pd.DataFrame()

        if "ESTADO" in df.columns:
            mask_canceled = df_all.apply(self._is_invoice_canceled, axis=1)
            df_valid = df_all[~mask_canceled]
            df_canceled = df_all[mask_canceled]
            self._log(f"  - Branch breakdown: {len(df_all)} total → {len(df_valid)} VALID (excluded {len(df_canceled)} ANULADAS)")

        # Get all unique branches from both valid and canceled
        all_branches = set()
        if not df_valid.empty:
            all_branches.update(df_valid[branch_col].dropna().unique())
        if not df_canceled.empty:
            all_branches.update(df_canceled[branch_col].dropna().unique())

        # Group by branch
        for branch_code in all_branches:
            if pd.isna(branch_code):
                continue

            # Count and sum for VALID invoices
            branch_data_valid = df_valid[df_valid[branch_col] == branch_code]
            count_valid = len(branch_data_valid)

            try:
                amount_valid = branch_data_valid[amount_col].astype(float).sum()
            except (ValueError, TypeError):
                self._log(f"Warning: Could not calculate amount for branch {branch_code}")
                amount_valid = 0.0

            # Count CANCELED invoices (don't sum amounts)
            count_canceled = 0
            if not df_canceled.empty:
                branch_data_canceled = df_canceled[df_canceled[branch_col] == branch_code]
                count_canceled = len(branch_data_canceled)

            # Convert numpy types to native Python types for JSON serialization
            branch_key = str(int(branch_code)) if not pd.isna(branch_code) else "unknown"
            breakdown[branch_key] = {
                'count': int(count_valid),
                'amount': float(amount_valid),
                'canceled_count': int(count_canceled)
            }

        return breakdown
    
    def filter_siat_by_modality(
        self, 
        df_siat: pd.DataFrame,
        modality: str = "2"
    ) -> pd.DataFrame:
        """Filter SIAT data to include only specified modality.
        
        MODALIDAD codes:
        - 2 = INVENTARIOS (Computerized inventory-based invoices)
        - 3 = ALQUILERES (Rental property invoices)
        
        Args:
            df_siat: SIAT DataFrame with MODALIDAD column
            modality: Modality code to filter (default: "2" for INVENTARIOS)
        
        Returns:
            Filtered DataFrame containing only specified modality
        """
        if "MODALIDAD" not in df_siat.columns:
            self._log("Warning: MODALIDAD column not found. Returning original DataFrame.")
            return df_siat
        
        original_count = len(df_siat)
        filtered_df = df_siat[df_siat["MODALIDAD"] == modality].copy()
        filtered_count = len(filtered_df)
        
        excluded_count = original_count - filtered_count
        
        self._log(f"Filtered SIAT data by MODALIDAD = {modality}")
        self._log(f"  - Original rows: {original_count}")
        self._log(f"  - Filtered rows: {filtered_count}")
        self._log(f"  - Excluded rows: {excluded_count} (MODALIDAD != {modality})")
        
        return filtered_df
    
    def match_invoices_by_cuf(
        self,
        df_siat: pd.DataFrame,
        df_inventory: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Match invoices using CUF as primary key.
        
        Args:
            df_siat: SIAT DataFrame with CUF in "CODIGO DE AUTORIZACIÓN"
            df_inventory: Inventory DataFrame with CUF in "cuf"
        
        Returns:
            Tuple of (matched, only_siat, only_inventory) DataFrames
        """
        self._log("Starting invoice matching by CUF...")
        
        # Get CUF columns
        siat_cuf_col = "CODIGO DE AUTORIZACIÓN"
        inv_cuf_col = "cuf"
        
        # Ensure CUF columns exist
        if siat_cuf_col not in df_siat.columns:
            raise ValueError(f"SIAT DataFrame missing column: {siat_cuf_col}")
        if inv_cuf_col not in df_inventory.columns:
            raise ValueError(f"Inventory DataFrame missing column: {inv_cuf_col}")
        
        # Remove rows with null CUF
        siat_with_cuf = df_siat[df_siat[siat_cuf_col].notna()].copy()
        inv_with_cuf = df_inventory[df_inventory[inv_cuf_col].notna()].copy()
        
        self._log(f"  - SIAT rows with CUF: {len(siat_with_cuf)}")
        self._log(f"  - Inventory rows with CUF: {len(inv_with_cuf)}")
        
        # Get CUF sets
        siat_cufs = set(siat_with_cuf[siat_cuf_col])
        inv_cufs = set(inv_with_cuf[inv_cuf_col])
        
        # Find matches and differences
        matched_cufs = siat_cufs & inv_cufs
        only_siat_cufs = siat_cufs - inv_cufs
        only_inv_cufs = inv_cufs - siat_cufs
        
        self._log(f"  - Matched CUFs: {len(matched_cufs)}")
        self._log(f"  - Only in SIAT: {len(only_siat_cufs)}")
        self._log(f"  - Only in Inventory: {len(only_inv_cufs)}")
        
        # Create result DataFrames
        matched = siat_with_cuf[siat_with_cuf[siat_cuf_col].isin(matched_cufs)].copy()
        only_siat = siat_with_cuf[siat_with_cuf[siat_cuf_col].isin(only_siat_cufs)].copy()
        only_inventory = inv_with_cuf[inv_with_cuf[inv_cuf_col].isin(only_inv_cufs)].copy()
        
        return matched, only_siat, only_inventory
    
    def compare_fields(
        self,
        df_siat: pd.DataFrame,
        df_inventory: pd.DataFrame
    ) -> ComparisonResult:
        """Compare fields between matched invoices.
        
        Performs detailed field-by-field comparison for invoices that exist
        in both systems, identifying specific discrepancies.
        
        Args:
            df_siat: SIAT DataFrame (should contain only matched invoices)
            df_inventory: Inventory DataFrame
        
        Returns:
            ComparisonResult with categorized discrepancies
        """
        self._log("Starting field comparison...")
        
        # Prepare for merge
        siat_cuf_col = "CODIGO DE AUTORIZACIÓN"
        inv_cuf_col = "cuf"
        
        # Create merge key
        df_siat_temp = df_siat.copy()
        df_inv_temp = df_inventory.copy()
        
        # Merge on CUF
        merged = pd.merge(
            df_siat_temp,
            df_inv_temp,
            left_on=siat_cuf_col,
            right_on=inv_cuf_col,
            how="inner",
            suffixes=("_siat", "_inv")
        )
        
        self._log(f"  - Merged rows: {len(merged)}")
        
        if len(merged) == 0:
            self._log("  - No matched invoices to compare")
            return ComparisonResult(
                matched_invoices=pd.DataFrame(),
                only_in_siat=pd.DataFrame(),
                only_in_inventory=pd.DataFrame(),
                amount_mismatches=pd.DataFrame(),
                customer_mismatches=pd.DataFrame(),
                other_mismatches=pd.DataFrame()
            )
        
        # Initialize lists for categorized discrepancies
        amount_mismatch_indices = []
        customer_mismatch_indices = []
        other_mismatch_indices = []
        perfect_match_indices = []
        
        # Compare each row
        for idx, row in merged.iterrows():
            has_mismatch = False
            mismatch_types = []
            
            # Compare amount
            siat_amount = row.get("IMPORTE TOTAL DE LA VENTA", 0)
            inv_amount = row.get("total", 0)
            
            try:
                siat_amount = float(siat_amount)
                inv_amount = float(inv_amount)
                
                if abs(siat_amount - inv_amount) > self.AMOUNT_TOLERANCE:
                    amount_mismatch_indices.append(idx)
                    has_mismatch = True
                    mismatch_types.append("amount")
            except (ValueError, TypeError):
                self._log(f"  - Warning: Could not compare amounts for CUF {row.get(siat_cuf_col)}")
            
            # Compare customer NIT - normalize format
            siat_nit = str(row.get("NIT / CI CLIENTE", "")).strip().upper()
            inv_nit = str(row.get("ClienteNit", "")).strip().upper()
            
            # Remove common formatting (spaces, dashes, dots)
            siat_nit_clean = siat_nit.replace(" ", "").replace("-", "").replace(".", "")
            inv_nit_clean = inv_nit.replace(" ", "").replace("-", "").replace(".", "")
            
            if siat_nit_clean != inv_nit_clean:
                customer_mismatch_indices.append(idx)
                has_mismatch = True
                mismatch_types.append("customer")
                self._log(f"  - NIT mismatch: SIAT='{siat_nit}', INV='{inv_nit}'")
            
            # Compare other fields (invoice number, branch, date, etc.)
            other_field_mismatch = False
            
            # Invoice number - use NUM FACTURA from CUF extraction
            try:
                siat_invoice = int(float(row.get("NUM FACTURA", 0)))
                inv_invoice = int(float(row.get("numeroFactura", 0)))
                if siat_invoice != inv_invoice:
                    other_field_mismatch = True
                    self._log(f"  - Invoice mismatch: SIAT={siat_invoice}, INV={inv_invoice}")
            except (ValueError, TypeError):
                self._log(f"  - Warning: Could not compare invoice numbers for CUF {row.get(siat_cuf_col)}")
            
            # Branch - use SUCURSAL from CUF extraction
            try:
                siat_branch = int(float(row.get("SUCURSAL", -1)))
                inv_branch = int(float(row.get("codigoSucursal", -1)))
                if siat_branch != inv_branch:
                    other_field_mismatch = True
                    self._log(f"  - Branch mismatch: SIAT={siat_branch}, INV={inv_branch}")
            except (ValueError, TypeError):
                self._log(f"  - Warning: Could not compare branches for CUF {row.get(siat_cuf_col)}")
            
            if other_field_mismatch:
                other_mismatch_indices.append(idx)
                has_mismatch = True
                mismatch_types.append("other")
            
            # Track perfect matches
            if not has_mismatch:
                perfect_match_indices.append(idx)
        
        # Create categorized DataFrames
        amount_mismatches = merged.loc[amount_mismatch_indices] if amount_mismatch_indices else pd.DataFrame()
        customer_mismatches = merged.loc[customer_mismatch_indices] if customer_mismatch_indices else pd.DataFrame()
        other_mismatches = merged.loc[other_mismatch_indices] if other_mismatch_indices else pd.DataFrame()
        perfect_matches = merged.loc[perfect_match_indices] if perfect_match_indices else pd.DataFrame()
        
        self._log(f"  - Perfect matches: {len(perfect_matches)}")
        self._log(f"  - Amount mismatches: {len(amount_mismatches)}")
        self._log(f"  - Customer mismatches: {len(customer_mismatches)}")
        self._log(f"  - Other mismatches: {len(other_mismatches)}")
        
        return ComparisonResult(
            matched_invoices=perfect_matches,
            only_in_siat=pd.DataFrame(),  # Populated elsewhere
            only_in_inventory=pd.DataFrame(),  # Populated elsewhere
            amount_mismatches=amount_mismatches,
            customer_mismatches=customer_mismatches,
            other_mismatches=other_mismatches
        )
    
    def validate(
        self,
        df_siat: pd.DataFrame,
        df_inventory: pd.DataFrame
    ) -> Tuple[ComparisonResult, ComparisonStats]:
        """Perform full validation comparing SIAT and inventory data.
        
        This is the main entry point for validation. It:
        1. Filters SIAT data by MODALIDAD = 2 (INVENTARIOS)
        2. Matches invoices by CUF
        3. Compares fields for matched invoices
        4. Categorizes discrepancies
        5. Generates statistics
        
        Args:
            df_siat: SIAT DataFrame with CUF fields extracted
            df_inventory: Inventory DataFrame from MySQL
        
        Returns:
            Tuple of (ComparisonResult, ComparisonStats)
        """
        # Step 1: Filter SIAT by modality
        df_siat_filtered = self.filter_siat_by_modality(df_siat, modality="2")
        
        # Step 2: Match by CUF
        matched_siat, only_siat, only_inventory = self.match_invoices_by_cuf(
            df_siat_filtered, df_inventory
        )
        
        # Step 3: Compare fields for matched invoices
        comparison = self.compare_fields(matched_siat, df_inventory)
        
        # Add only_siat and only_inventory to comparison result
        comparison.only_in_siat = only_siat
        comparison.only_in_inventory = only_inventory
        
        # Step 3b: Analyze only_siat invoices - separate valid vs canceled
        only_siat_valid_count = 0
        only_siat_canceled_count = 0
        only_siat_valid_amount = 0.0
        
        if len(only_siat) > 0:
            for idx, row in only_siat.iterrows():
                if self._is_invoice_canceled(row):
                    only_siat_canceled_count += 1
                else:
                    only_siat_valid_count += 1
                    # Sum the amount of valid only-in-SIAT invoices
                    try:
                        amount = float(row.get("IMPORTE TOTAL DE LA VENTA", 0.0))
                        only_siat_valid_amount += amount
                    except (ValueError, TypeError):
                        self._log(f"Warning: Could not parse amount for valid only-in-SIAT invoice")
        
        # Step 4: Calculate statistics
        total_matched = len(comparison.matched_invoices)
        match_rate = (total_matched / len(df_siat_filtered) * 100) if len(df_siat_filtered) > 0 else 0.0

        # Calculate total amounts from MATCHED invoices - ONLY VALID (exclude ANULADAS)
        matched_siat_amount = 0.0
        total_inventory_amount = 0.0

        # Sum amounts from MATCHED invoices in SIAT - ONLY VALID
        if len(comparison.matched_invoices) > 0 and "IMPORTE TOTAL DE LA VENTA" in comparison.matched_invoices.columns:
            try:
                # Filter only VALID invoices (exclude ANULADAS)
                valid_matched = comparison.matched_invoices[
                    ~comparison.matched_invoices.apply(self._is_invoice_canceled, axis=1)
                ]
                matched_siat_amount = valid_matched["IMPORTE TOTAL DE LA VENTA"].astype(float).sum()
                self._log(f"  - Matched SIAT amount (VALID only): Bs. {matched_siat_amount:,.2f}")
                self._log(f"  - Excluded {len(comparison.matched_invoices) - len(valid_matched)} ANULADAS from matched")
            except (ValueError, TypeError):
                self._log("Warning: Could not calculate SIAT total amount for matched invoices")

        # Sum amounts from MATCHED invoices in inventory - ONLY those that are VALID in SIAT
        # This ensures fair comparison: we exclude invoices that are ANULADAS in SIAT from both sides
        if len(comparison.matched_invoices) > 0 and "total" in comparison.matched_invoices.columns:
            try:
                # Use the same filter as SIAT - only invoices that are VALIDA in SIAT
                valid_matched = comparison.matched_invoices[
                    ~comparison.matched_invoices.apply(self._is_invoice_canceled, axis=1)
                ]
                total_inventory_amount = valid_matched["total"].astype(float).sum()
                self._log(f"  - Matched Inventory amount (VALID in SIAT only): Bs. {total_inventory_amount:,.2f}")
            except (ValueError, TypeError):
                self._log("Warning: Could not calculate inventory total amount for matched invoices")

        # Calculate TRUE total SIAT amount including valid only-in-SIAT invoices
        # This is the correct business logic: SIAT total (VALID) = matched VALID + valid unmatched
        total_siat_amount = matched_siat_amount + only_siat_valid_amount

        # Calculate difference using TRUE totals (VALID only)
        amount_difference = abs(total_siat_amount - total_inventory_amount)
        amount_difference_pct = 0.0
        if total_inventory_amount > 0:
            amount_difference_pct = (amount_difference / total_inventory_amount) * 100
        
        # Step 5: Calculate branch breakdown
        branch_breakdown_siat = self._calculate_branch_breakdown(
            df_siat_filtered,
            amount_col="IMPORTE TOTAL DE LA VENTA",
            branch_col="SUCURSAL"
        )

        # Filter inventory to exclude invoices that are ANULADAS in SIAT
        # This ensures fair comparison: SIAT VALIDAS vs Inventory (excluding ANULADAS in SIAT)
        df_inventory_filtered = self._filter_inventory_by_siat_estado(
            df_inventory, df_siat_filtered
        )

        branch_breakdown_inventory = self._calculate_branch_breakdown(
            df_inventory_filtered,
            amount_col="total",
            branch_col="codigoSucursal"
        )

        stats = ComparisonStats(
            total_siat=len(df_siat_filtered),
            total_inventory=len(df_inventory),
            matched_count=total_matched,
            only_siat_count=len(only_siat),
            only_inventory_count=len(only_inventory),
            amount_mismatch_count=len(comparison.amount_mismatches),
            customer_mismatch_count=len(comparison.customer_mismatches),
            other_mismatch_count=len(comparison.other_mismatches),
            match_rate=match_rate,
            total_siat_amount=total_siat_amount,
            total_inventory_amount=total_inventory_amount,
            amount_difference=amount_difference,
            amount_difference_pct=amount_difference_pct,
            only_siat_valid_count=only_siat_valid_count,
            only_siat_canceled_count=only_siat_canceled_count,
            only_siat_valid_amount=only_siat_valid_amount,
            branch_breakdown_siat=branch_breakdown_siat,
            branch_breakdown_inventory=branch_breakdown_inventory
        )
        
        # Display summary
        self._display_summary(stats)
        
        return comparison, stats
    
    def _display_summary(self, stats: ComparisonStats) -> None:
        """Display validation summary.
        
        Args:
            stats: Comparison statistics
        """
        print("\n" + "=" * 80)
        print("📋 VALIDATION SUMMARY")
        print("=" * 80)
        
        print(f"\n📊 Dataset Sizes:")
        print(f"   - SIAT (MODALIDAD=2): {stats.total_siat} invoices")
        print(f"   - Inventory: {stats.total_inventory} invoices")
        
        print(f"\n💰 Total Amounts (VALID invoices only):")
        print(f"   - SIAT Total: Bs. {stats.total_siat_amount:,.2f}")
        if stats.only_siat_valid_amount > 0:
            print(f"   - Only in SIAT (valid, not in Inventory): Bs. {stats.only_siat_valid_amount:,.2f}")
        print(f"   - Inventory Total: Bs. {stats.total_inventory_amount:,.2f}")
        print(f"   - Difference: Bs. {stats.amount_difference:,.2f} ({stats.amount_difference_pct:.4f}%)")

        # Branch breakdown mapping
        branch_names = {
            "0": "CENTRAL",
            "5": "SANTA CRUZ",
            "6": "POTOSI"
        }

        print(f"\n🏢 Breakdown by Branch (VALID invoices only):")

        # Collect all unique branch codes from both systems
        all_branches = sorted(set(
            list(stats.branch_breakdown_siat.keys()) +
            list(stats.branch_breakdown_inventory.keys())
        ))

        if all_branches:
            for branch_code in all_branches:
                branch_name = branch_names.get(branch_code, f"Branch {branch_code}")
                print(f"   📍 {branch_name} (Sucursal {branch_code}):")

                # SIAT data
                siat_data = stats.branch_breakdown_siat.get(branch_code, {'count': 0, 'amount': 0.0, 'canceled_count': 0})
                siat_count = siat_data['count']
                siat_amount = siat_data['amount']
                siat_canceled = siat_data.get('canceled_count', 0)

                # Inventory data
                inv_data = stats.branch_breakdown_inventory.get(branch_code, {'count': 0, 'amount': 0.0, 'canceled_count': 0})
                inv_count = inv_data['count']
                inv_amount = inv_data['amount']

                # Calculate difference
                count_diff = siat_count - inv_count
                amount_diff = siat_amount - inv_amount
                amount_diff_pct = 0.0
                if inv_amount > 0:
                    amount_diff_pct = (amount_diff / inv_amount) * 100

                print(f"      • SIAT:      {siat_count:4d} VALID invoices | Bs. {siat_amount:12,.2f}")
                if siat_canceled > 0:
                    print(f"                 {siat_canceled:4d} ANULADAS (excluded from totals)")
                print(f"      • Inventory: {inv_count:4d} invoices | Bs. {inv_amount:12,.2f}")

                # Show difference with color indicator
                if abs(amount_diff_pct) <= 0.5:
                    status = "✅"
                else:
                    status = "⚠️"

                print(f"      • Difference: {count_diff:+4d} invoices | Bs. {amount_diff:+12,.2f} ({amount_diff_pct:+.4f}%) {status}")
        else:
            print(f"   ℹ️  No branch data available")
        
        print(f"\n✅ Matches:")
        print(f"   - Perfect matches: {stats.matched_count} ({stats.match_rate:.2f}%)")
        
        print(f"\n⚠️  Discrepancies:")
        print(f"   - Only in SIAT: {stats.only_siat_count}")
        if stats.only_siat_count > 0:
            print(f"     • Valid (not canceled): {stats.only_siat_valid_count}")
            print(f"     • Canceled: {stats.only_siat_canceled_count}")
        print(f"   - Only in Inventory: {stats.only_inventory_count}")
        print(f"   - Amount mismatches: {stats.amount_mismatch_count}")
        print(f"   - Customer mismatches: {stats.customer_mismatch_count}")
        print(f"   - Other field mismatches: {stats.other_mismatch_count}")
        
        # Determine status based on critical factors
        # Critical issues:
        # 1. Valid (not canceled) invoices only in SIAT
        # 2. Amount difference > 0.5% (overall)
        # 3. Any branch with amount difference > 0.5%
        has_valid_only_siat = stats.only_siat_valid_count > 0
        amount_critical = stats.amount_difference_pct > 0.5
        has_amount_mismatches = stats.amount_mismatch_count > 0

        # Check branch-level validation
        branches_with_issues = []
        for branch_code in stats.branch_breakdown_siat.keys():
            siat_data = stats.branch_breakdown_siat.get(branch_code, {'count': 0, 'amount': 0.0})
            inv_data = stats.branch_breakdown_inventory.get(branch_code, {'count': 0, 'amount': 0.0})

            siat_amount = siat_data['amount']
            inv_amount = inv_data['amount']

            if inv_amount > 0:
                branch_diff_pct = abs((siat_amount - inv_amount) / inv_amount) * 100
                if branch_diff_pct > 0.5:
                    branches_with_issues.append({
                        'code': branch_code,
                        'name': branch_names.get(branch_code, f"Branch {branch_code}"),
                        'diff_pct': branch_diff_pct
                    })

        branch_critical = len(branches_with_issues) > 0

        # Non-critical issues
        only_siat_all_canceled = (stats.only_siat_count > 0 and
                                  stats.only_siat_valid_count == 0 and
                                  stats.only_siat_canceled_count > 0)
        total_other_issues = (
            stats.only_inventory_count +
            stats.customer_mismatch_count +
            stats.other_mismatch_count
        )

        print(f"\n🎯 Overall Status:")
        if has_valid_only_siat:
            print(f"   ❌ CRITICAL - Valid invoices found ONLY in SIAT (not in inventory)")
            print(f"      These {stats.only_siat_valid_count} invoice(s) must exist in Inventory or be marked as Canceled")
        elif branch_critical:
            print(f"   ❌ CRITICAL - Branch validation failed: {len(branches_with_issues)} branch(es) exceed 0.5% threshold")
            for branch_issue in branches_with_issues:
                print(f"      • {branch_issue['name']} (Sucursal {branch_issue['code']}): {branch_issue['diff_pct']:.4f}%")
        elif amount_critical:
            print(f"   ❌ CRITICAL - Overall amount difference exceeds threshold (>0.5%)")
            print(f"      Difference: Bs. {stats.amount_difference:,.2f} ({stats.amount_difference_pct:.4f}%)")
        elif has_amount_mismatches:
            print(f"   ❌ CRITICAL - Amount mismatches found: {stats.amount_mismatch_count} invoices with different amounts")
        elif only_siat_all_canceled and stats.amount_difference_pct <= 0.5:
            print(f"   ✅ ACCEPTABLE - Only in SIAT: all {stats.only_siat_canceled_count} are canceled (amounts match)")
        elif total_other_issues == 0:
            print("   ✅ PERFECT - No discrepancies found! All branches validated.")
        elif total_other_issues <= 5:
            print(f"   ✅ ACCEPTABLE - {total_other_issues} minor discrepancies (amounts match, all branches OK)")
        else:
            print(f"   ⚠️  MINOR ISSUES - {total_other_issues} discrepancies detected (amounts match, all branches OK)")

        print("=" * 80)
    
    def generate_report(
        self,
        comparison: ComparisonResult,
        stats: ComparisonStats,
        output_path: Path
    ) -> None:
        """Generate Excel report with detailed comparison results.
        
        Creates a multi-sheet Excel file with:
        - Summary sheet
        - Perfect matches
        - Only in SIAT
        - Only in Inventory
        - Amount mismatches
        - Customer mismatches
        - Other mismatches
        
        Args:
            comparison: Comparison results
            stats: Comparison statistics
            output_path: Path where to save the Excel file
        """
        self._log(f"Generating report: {output_path}")
        
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Summary sheet
            summary_data = {
                "Metric": [
                    "Total SIAT (MODALIDAD=2)",
                    "Total Inventory",
                    "Perfect Matches",
                    "Match Rate (%)",
                    "",
                    "SIAT Total Amount (Bs.) - VALID only",
                    "Inventory Total Amount (Bs.)",
                    "Amount Difference (Bs.)",
                    "Amount Difference (%)",
                    "",
                    "Only in SIAT",
                    "Only in Inventory",
                    "Amount Mismatches",
                    "Customer Mismatches",
                    "Other Mismatches",
                    "Total Issues"
                ],
                "Value": [
                    stats.total_siat,
                    stats.total_inventory,
                    stats.matched_count,
                    f"{stats.match_rate:.2f}",
                    "",
                    f"{stats.total_siat_amount:,.2f}",
                    f"{stats.total_inventory_amount:,.2f}",
                    f"{stats.amount_difference:,.2f}",
                    f"{stats.amount_difference_pct:.4f}",
                    "",
                    stats.only_siat_count,
                    stats.only_inventory_count,
                    stats.amount_mismatch_count,
                    stats.customer_mismatch_count,
                    stats.other_mismatch_count,
                    (stats.only_siat_count + stats.only_inventory_count +
                     stats.amount_mismatch_count + stats.customer_mismatch_count +
                     stats.other_mismatch_count)
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

            # Branch breakdown sheet
            branch_names = {"0": "CENTRAL", "5": "SANTA CRUZ", "6": "POTOSI"}
            all_branches = sorted(set(
                list(stats.branch_breakdown_siat.keys()) +
                list(stats.branch_breakdown_inventory.keys())
            ))

            branch_data = {
                "Branch Code": [],
                "Branch Name": [],
                "SIAT Count (VALID)": [],
                "SIAT Canceled": [],
                "SIAT Amount (Bs.)": [],
                "Inventory Count": [],
                "Inventory Amount (Bs.)": [],
                "Count Difference": [],
                "Amount Difference (Bs.)": [],
                "Amount Difference (%)": [],
                "Status": []
            }

            for branch_code in all_branches:
                branch_name = branch_names.get(branch_code, f"Branch {branch_code}")
                siat_data = stats.branch_breakdown_siat.get(branch_code, {'count': 0, 'amount': 0.0, 'canceled_count': 0})
                inv_data = stats.branch_breakdown_inventory.get(branch_code, {'count': 0, 'amount': 0.0, 'canceled_count': 0})

                siat_count = siat_data['count']
                siat_amount = siat_data['amount']
                siat_canceled = siat_data.get('canceled_count', 0)
                inv_count = inv_data['count']
                inv_amount = inv_data['amount']

                count_diff = siat_count - inv_count
                amount_diff = siat_amount - inv_amount
                amount_diff_pct = 0.0
                if inv_amount > 0:
                    amount_diff_pct = (amount_diff / inv_amount) * 100

                status = "OK" if abs(amount_diff_pct) <= 0.5 else "WARNING"

                branch_data["Branch Code"].append(branch_code)
                branch_data["Branch Name"].append(branch_name)
                branch_data["SIAT Count (VALID)"].append(siat_count)
                branch_data["SIAT Canceled"].append(siat_canceled)
                branch_data["SIAT Amount (Bs.)"].append(f"{siat_amount:,.2f}")
                branch_data["Inventory Count"].append(inv_count)
                branch_data["Inventory Amount (Bs.)"].append(f"{inv_amount:,.2f}")
                branch_data["Count Difference"].append(count_diff)
                branch_data["Amount Difference (Bs.)"].append(f"{amount_diff:,.2f}")
                branch_data["Amount Difference (%)"].append(f"{amount_diff_pct:.4f}")
                branch_data["Status"].append(status)

            pd.DataFrame(branch_data).to_excel(writer, sheet_name="Branch Breakdown", index=False)
            
            # Perfect matches
            if not comparison.matched_invoices.empty:
                comparison.matched_invoices.to_excel(writer, sheet_name="Perfect Matches", index=False)
            
            # Only in SIAT
            if not comparison.only_in_siat.empty:
                comparison.only_in_siat.to_excel(writer, sheet_name="Only in SIAT", index=False)
            
            # Only in Inventory
            if not comparison.only_in_inventory.empty:
                comparison.only_in_inventory.to_excel(writer, sheet_name="Only in Inventory", index=False)
            
            # Amount mismatches
            if not comparison.amount_mismatches.empty:
                comparison.amount_mismatches.to_excel(writer, sheet_name="Amount Mismatches", index=False)
            
            # Customer mismatches
            if not comparison.customer_mismatches.empty:
                comparison.customer_mismatches.to_excel(writer, sheet_name="Customer Mismatches", index=False)
            
            # Other mismatches
            if not comparison.other_mismatches.empty:
                comparison.other_mismatches.to_excel(writer, sheet_name="Other Mismatches", index=False)

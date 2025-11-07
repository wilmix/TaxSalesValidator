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
        total_siat_amount: Total amount in SIAT (Bs.)
        total_inventory_amount: Total amount in inventory (Bs.)
        amount_difference: Absolute difference in amounts (Bs.)
        amount_difference_pct: Percentage difference in amounts
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
    
    def _log(self, message: str) -> None:
        """Log message if debug mode is enabled.
        
        Args:
            message: Message to log
        """
        if self.debug:
            print(f"[SalesValidator] {message}")
    
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
        
        # Step 4: Calculate statistics
        total_matched = len(comparison.matched_invoices)
        match_rate = (total_matched / len(df_siat_filtered) * 100) if len(df_siat_filtered) > 0 else 0.0
        
        # Calculate total amounts for validation
        total_siat_amount = 0.0
        total_inventory_amount = 0.0
        
        # Sum amounts from SIAT (MODALIDAD=2 only)
        if "IMPORTE TOTAL DE LA VENTA" in df_siat_filtered.columns:
            try:
                total_siat_amount = df_siat_filtered["IMPORTE TOTAL DE LA VENTA"].astype(float).sum()
            except (ValueError, TypeError):
                self._log("Warning: Could not calculate SIAT total amount")
        
        # Sum amounts from inventory
        if "total" in df_inventory.columns:
            try:
                total_inventory_amount = df_inventory["total"].astype(float).sum()
            except (ValueError, TypeError):
                self._log("Warning: Could not calculate inventory total amount")
        
        # Calculate difference
        amount_difference = abs(total_siat_amount - total_inventory_amount)
        amount_difference_pct = 0.0
        if total_inventory_amount > 0:
            amount_difference_pct = (amount_difference / total_inventory_amount) * 100
        
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
            amount_difference_pct=amount_difference_pct
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
        
        print(f"\n💰 Total Amounts:")
        print(f"   - SIAT Total: Bs. {stats.total_siat_amount:,.2f}")
        print(f"   - Inventory Total: Bs. {stats.total_inventory_amount:,.2f}")
        print(f"   - Difference: Bs. {stats.amount_difference:,.2f} ({stats.amount_difference_pct:.4f}%)")
        
        print(f"\n✅ Matches:")
        print(f"   - Perfect matches: {stats.matched_count} ({stats.match_rate:.2f}%)")
        
        print(f"\n⚠️  Discrepancies:")
        print(f"   - Only in SIAT: {stats.only_siat_count}")
        print(f"   - Only in Inventory: {stats.only_inventory_count}")
        print(f"   - Amount mismatches: {stats.amount_mismatch_count}")
        print(f"   - Customer mismatches: {stats.customer_mismatch_count}")
        print(f"   - Other field mismatches: {stats.other_mismatch_count}")
        
        # Determine status based on amounts (critical) and counts (minor)
        total_issues = (
            stats.only_siat_count + 
            stats.only_inventory_count + 
            stats.amount_mismatch_count + 
            stats.customer_mismatch_count + 
            stats.other_mismatch_count
        )
        
        # Critical: amount difference > 0.5%
        amount_critical = stats.amount_difference_pct > 0.5
        
        print(f"\n🎯 Overall Status:")
        if amount_critical:
            print(f"   ❌ CRITICAL - Amount difference exceeds threshold (>{0.5:.2f}%)")
            print(f"      Difference: Bs. {stats.amount_difference:,.2f} ({stats.amount_difference_pct:.4f}%)")
        elif stats.amount_mismatch_count > 0:
            print(f"   ⚠️  AMOUNT MISMATCHES - {stats.amount_mismatch_count} invoices with different amounts")
        elif total_issues == 0:
            print("   ✅ PERFECT - No discrepancies found!")
        elif total_issues <= 5:
            print(f"   ✅ ACCEPTABLE - {total_issues} minor discrepancies (amounts match)")
        else:
            print(f"   ⚠️  MINOR ISSUES - {total_issues} discrepancies detected (amounts match)")
        
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
                    "SIAT Total Amount (Bs.)",
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

"""Verify that NOVIEMBRE 2025 has 3 records with 'No existe en inventarios' observation."""

from datetime import datetime
from src.config import Config
from src.sas_connector import SasConnector
from sqlalchemy import text


def main():
    """Verify observations for NOVIEMBRE 2025."""
    connector = SasConnector()
    
    try:
        # Get the engine from connector
        engine = connector._get_engine()
        
        # Query for NOVIEMBRE 2025 records with "No existe en inventarios" observation
        query = """
        SELECT 
            id,
            invoice_date,
            invoice_number,
            authorization_code,
            customer_name,
            total_sale_amount,
            observations,
            created_at
        FROM sales_registers
        WHERE 
            YEAR(invoice_date) = 2025 
            AND MONTH(invoice_date) = 11
            AND observations LIKE '%No existe en inventarios%'
        ORDER BY invoice_date, invoice_number
        """
        
        with engine.connect() as connection:
            result = connection.execute(text(query))
            records = result.fetchall()
            
            print("=" * 100)
            print("🔍 VERIFICACIÓN: Observaciones de NOVIEMBRE 2025")
            print("=" * 100)
            print(f"\n✅ Total de registros con 'No existe en inventarios': {len(records)}")
            print()
            
            if len(records) > 0:
                print("📋 Detalles:")
                print("-" * 100)
                for i, record in enumerate(records, 1):
                    print(f"\n{i}. Factura: {record[2]} (CUF: {record[3][:16]}...)")
                    print(f"   Fecha: {record[1]}")
                    print(f"   Cliente: {record[4]}")
                    print(f"   Monto: Bs. {record[5]:,.2f}")
                    print(f"   Observación: {record[6]}")
                    print(f"   Sincronizado: {record[7]}")
                
                print("\n" + "=" * 100)
                if len(records) == 3:
                    print("✅ CORRECTO: Se encontraron exactamente 3 registros con observación.")
                else:
                    print(f"⚠️  ADVERTENCIA: Se esperaban 3 registros, pero se encontraron {len(records)}")
                print("=" * 100)
            else:
                print("⚠️  ADVERTENCIA: No se encontraron registros con la observación esperada.")
                print("=" * 100)
                
                # Show all NOVIEMBRE 2025 records to debug
                print("\n🔍 DEBUG: Todos los registros de NOVIEMBRE 2025:")
                debug_query = """
                SELECT 
                    invoice_number,
                    authorization_code,
                    customer_name,
                    observations
                FROM sales_registers
                WHERE YEAR(invoice_date) = 2025 AND MONTH(invoice_date) = 11
                ORDER BY invoice_date, invoice_number
                """
                debug_result = connection.execute(text(debug_query))
                debug_records = debug_result.fetchall()
                print(f"Total de registros en NOVIEMBRE 2025: {len(debug_records)}")
                for record in debug_records[:10]:  # Show first 10
                    obs = record[3] if record[3] else "sin observación"
                    print(f"  - {record[0]}: {obs}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pass


if __name__ == "__main__":
    main()

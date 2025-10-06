# 🗄️ Inventory Database Integration

## Overview

This document describes the integration between TaxSalesValidator and the local MySQL inventory system for invoice comparison and validation.

## Architecture

The inventory integration follows **Single Responsibility Principle (SRP)** with dedicated module:

```
src/
  ├── inventory_connector.py  # MySQL connectivity and queries
  └── config.py              # Database configuration from .env
```

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```env
# MySQL Database Credentials (Inventory System)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
DB_USER=your_db_username
DB_PASSWORD=your_db_password
```

### Connection Details

- **Library**: SQLAlchemy 2.0+ with PyMySQL driver
- **Connection String**: `mysql+pymysql://user:pass@host:port/database`
- **Features**:
  - Connection pooling with pre-ping (automatic reconnection)
  - Connection recycling (1 hour)
  - Context manager support for resource cleanup

## Usage

### Basic Connection Test

```bash
# Test database connectivity
uv run python test_db_connection.py
```

Expected output:
```
✅ Database connection test successful
   - Host: localhost:3306
   - Database: your_database
   - User: your_user
```

### Query Inventory Sales

```python
from src.inventory_connector import InventoryConnector

# Create connector instance
with InventoryConnector() as connector:
    # Test connection
    connector.test_connection()
    
    # Get sales data for September 2025
    df = connector.get_sales_from_inventory(
        year=2025,
        start_date="2025-09-01",
        end_date="2025-09-30"
    )
    
    print(f"Retrieved {len(df)} invoices")
```

## SQL Query

The inventory query retrieves comprehensive sales information including:

### Retrieved Fields (34 columns)

| Field | Description |
|-------|-------------|
| `codigoSucursal` | Branch office code |
| `codigoPuntoVenta` | Point of sale code |
| `numeroFactura` | Invoice number |
| `fechaFac` | Invoice date |
| `ClienteNit` | Customer NIT |
| `ClienteFactura` | Customer name |
| `total` | Total amount |
| `vendedor` | Salesperson name |
| `estado` | Invoice status (anulada) |
| `pagada` | Payment status |
| `cuf` | CUF (Código Único de Facturación) |
| `codigoRecepcion` | Reception code from SIAT |
| `fechaEmisionSiat` | SIAT emission date |
| ... | (31 more fields) |

### Query Logic

```sql
-- Set date range variables
SET @year=2025, @ini='2025-09-01', @end='2025-09-30';

-- Main query joins 15+ tables
SELECT fs.codigoSucursal, fs.codigoPuntoVenta, f.nFactura, ...
FROM factura_egresos fe
INNER JOIN factura f ON f.idFactura = fe.idFactura
INNER JOIN factura_siat fs ON fs.factura_id = f.idFactura
-- ... (multiple joins for complete invoice data)
WHERE f.fechaFac BETWEEN @ini AND @end
  AND (f.lote = 0 OR f.lote = '138')
GROUP BY fe.idFactura
ORDER BY f.fechaFac DESC, f.nFactura DESC;
```

**Key Filters**:
- Date range: `fechaFac BETWEEN @ini AND @end`
- Batch filter: `lote = 0 OR lote = '138'` (standard invoices)
- Active CUIS only: `cuis.active = 1`

## API Reference

### Class: `InventoryConnector`

#### Methods

##### `__init__() -> None`
Initialize connector with configuration from environment.

##### `test_connection() -> bool`
Test database connectivity.

**Returns**: `True` if connection successful, `False` otherwise

##### `get_database_info() -> dict`
Get MySQL version and connection information.

**Returns**: Dictionary with database details:
```python
{
    'mysql_version': '8.0.43',
    'current_database': 'your_db',
    'host': 'localhost',
    'port': 3306,
    'user': 'your_user'
}
```

##### `get_sales_from_inventory(year: int, start_date: str, end_date: str) -> pd.DataFrame`
Execute inventory sales query and return DataFrame.

**Parameters**:
- `year`: Year for the report (e.g., 2025)
- `start_date`: Start date in format `'YYYY-MM-DD'`
- `end_date`: End date in format `'YYYY-MM-DD'`

**Returns**: Pandas DataFrame with 34 columns

**Example**:
```python
df = connector.get_sales_from_inventory(
    year=2025,
    start_date="2025-09-01",
    end_date="2025-09-30"
)
```

##### `close() -> None`
Close database connection and dispose of engine.

#### Context Manager

```python
# Automatic connection cleanup
with InventoryConnector() as connector:
    df = connector.get_sales_from_inventory(...)
# Connection automatically closed
```

## Integration with Main Flow

The inventory connector will be integrated as **Phase 5** in `main.py`:

```
Phase 1: Web Scraping      → Download ZIP from SIAT
Phase 2: File Extraction   → Extract CSV
Phase 3: Data Loading      → Load tax report to DataFrame
Phase 4: CUF Extraction    → Parse CUF fields
Phase 5: Inventory Query   → Load inventory sales (NEW)
Phase 6: Comparison        → Compare tax vs inventory (FUTURE)
```

## Testing

### Connection Test
```bash
uv run python test_db_connection.py
```

### Expected Results
- ✅ Connection test passes
- ✅ Database info retrieved
- ✅ Query executes successfully
- ✅ DataFrame with sales data returned

### Sample Test Output
```
📊 Query Results:
   - Total rows: 21
   - Total columns: 34
   
📈 Basic Statistics:
   - Total sales amount: 259,139.90
   - Unique invoices: 21
   - Invoices with CUF: 21
```

## Troubleshooting

### Connection Failed

**Error**: `Failed to create database engine`

**Solutions**:
1. Verify `.env` has correct credentials
2. Check MySQL server is running
3. Test connection: `mysql -u user -p -h host database`
4. Verify user has SELECT permissions

### Query Timeout

**Error**: Query takes too long

**Solutions**:
1. Add indexes on `fechaFac`, `lote`, `idFactura`
2. Reduce date range for testing
3. Check MySQL query execution plan: `EXPLAIN SELECT ...`

### No Data Retrieved

**Issue**: Query returns 0 rows

**Possible Causes**:
1. No sales in specified date range
2. Filter conditions too restrictive (`lote = 0 OR lote = '138'`)
3. Missing data in joined tables

**Debugging**:
```python
# Test with broader filters
df = connector.get_sales_from_inventory(
    year=2024,  # Try previous year
    start_date="2024-01-01",  # Broader range
    end_date="2024-12-31"
)
```

## Security

### Credentials
- ✅ Store in `.env` (gitignored)
- ✅ Use environment variables in production
- ❌ Never hardcode in source code

### Permissions
Minimum required MySQL privileges:
```sql
GRANT SELECT ON your_database.* TO 'your_user'@'localhost';
```

### Connection Security
- Use SSL/TLS for remote connections
- Limit user to SELECT only (read-only)
- Use strong passwords

## Next Steps

1. ✅ Database configuration
2. ✅ Connection module
3. ✅ Query implementation
4. ⏳ Integration with main.py
5. ⏳ Comparison logic (Phase 6)
6. ⏳ Discrepancy reporting

## Related Documentation

- [`src/inventory_connector.py`](../src/inventory_connector.py) - Source code
- [`test_db_connection.py`](../test_db_connection.py) - Test script
- [`README.md`](../README.md) - Main documentation
- [`docs/CUF_PROCESSING.md`](CUF_PROCESSING.md) - CUF extraction guide

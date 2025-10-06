"""Inventory Database Connector for TaxSalesValidator.

This module handles MySQL database connection and query execution
for retrieving sales data from the local inventory system.
Following SRP: Only responsible for database connectivity and queries.
"""

from typing import Optional

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import Config


class InventoryConnector:
    """MySQL database connector for inventory system queries.

    Handles connection management and data retrieval from the local
    inventory database.
    """

    def __init__(self) -> None:
        """Initialize the inventory connector with configuration from environment."""
        self.host = Config.DB_HOST
        self.port = Config.DB_PORT
        self.database = Config.DB_NAME
        self.user = Config.DB_USER
        self.password = Config.DB_PASSWORD
        self._engine: Optional[Engine] = None

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
                    echo=False,  # Set to True for SQL debugging
                )
            except Exception as e:
                print(f"❌ Failed to create database engine: {e}")
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
                if row and row[0] == 1:
                    return True
                return False
        except Exception as e:
            return False

    def get_database_info(self) -> dict:
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

                return {
                    "mysql_version": version,
                    "current_database": current_db,
                    "host": self.host,
                    "port": self.port,
                    "user": self.user,
                }
        except Exception as e:
            print(f"❌ Failed to get database info: {e}")
            raise

    def get_sales_from_inventory(
        self, year: int, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Execute inventory sales query and return results as DataFrame.

        Args:
            year: Year for the report (e.g., 2025)
            start_date: Start date in format 'YYYY-MM-DD' (e.g., '2025-09-01')
            end_date: End date in format 'YYYY-MM-DD' (e.g., '2025-09-30')

        Returns:
            Pandas DataFrame with sales data from inventory system

        Raises:
            Exception: If query execution fails
        """
        # SQL query from the user requirements
        query = """
        SET @year=:year, @ini = :start_date, @end = :end_date;

        SELECT
          fs.codigoSucursal,
          fs.codigoPuntoVenta,
          f.`idFactura`,
          f.`lote`,
          df.`manual`,
          f.`nFactura` numeroFactura,
          f.`fechaFac`,
          f.`ClienteNit`,
          c.email emailCliente,
          f.`ClienteFactura`,
          t.`sigla`,
          f.`total`,
          CONCAT(u.first_name, ' ', u.last_name) AS vendedor,
          f.`anulada` estado,
          f.fecha, 
          f.glosa,
          p.idPago,
          p.`numPago`,
          f.`pagada`,
          f.almacen idAlmacen,
          e.clientePedido pedido,
          CASE
            WHEN f.moneda = 1 THEN 'BOB'
            WHEN f.moneda = 2 THEN CONCAT('$', 'U$')
          END moneda,
          CASE
            WHEN f.`anulada` = 1 THEN 'ANULADA'
            WHEN f.`pagada` = 0 THEN 'NO PAGADA'
            WHEN f.`pagada` = 1 THEN 'PAGADA'
            WHEN f.`pagada` = 2 THEN 'PAGO PARCIAL'
          END pagadaF,
          CONCAT(ua.first_name, ' ', ua.last_name) emisor,
          tp.tipoPago,
          fs.codigoRecepcion,
          fs.cuf,
          fs.cafc,
          fs.pedido,
          sp.descripcion metodoPago,
          fs.leyenda,
          fs.fechaEmision fechaEmisionSiat,
          f.lote,
          a.almacen
        FROM
          factura_egresos fe
          INNER JOIN egresos e on e.idegresos = fe.idegresos
          INNER JOIN factura f on f.idFactura = fe.idFactura
          LEFT JOIN pago_factura pf ON f.idFactura = pf.idFactura
          LEFT JOIN pago p ON p.idPago = pf.idPago
          INNER JOIN tmovimiento t on e.tipomov = t.id
          INNER JOIN datosfactura df on df.idDatosFactura = f.lote
          INNER JOIN users u on u.id = e.vendedor
          INNER JOIN users ua ON ua.id = f.autor
          INNER JOIN tipoPago tp ON tp.id = f.tipoPago
          INNER JOIN factura_siat fs ON fs.factura_id = f.idFactura
          INNER JOIN clientes c ON c.idCliente = f.cliente
          INNER JOIN siat_sincro_tipo_metodo_pago sp ON sp.codigoClasificador = fs.codigoMetodoPago
          INNER JOIN siat_cuis cuis ON cuis.sucursal = fs.codigoSucursal
          AND cuis.codigoPuntoVenta = fs.codigoPuntoVenta
          AND cuis.active = 1
          INNER JOIN almacenes a ON a.idalmacen = f.almacen
        WHERE
          f.fechaFac BETWEEN @ini AND @end
          AND (
            f.lote = 0
            OR f.lote = '138'
          )
        GROUP BY
          fe.idFactura
        ORDER BY
          f.`fechaFac` DESC,
          f.`nFactura` DESC,
          f.idFactura DESC;
        """

        try:
            engine = self._get_engine()

            # Note: MySQL variables (@year, @ini, @end) need to be set in the session
            # We'll use pandas read_sql with proper parameter handling
            
            # First, set the variables in the connection
            with engine.connect() as connection:
                connection.execute(
                    text(f"SET @year=:year, @ini = :start_date, @end = :end_date"),
                    {"year": year, "start_date": start_date, "end_date": end_date}
                )
                connection.commit()
            
            # Now execute the main query using pandas
            query_text = """
                SELECT
                  fs.codigoSucursal,
                  fs.codigoPuntoVenta,
                  f.`idFactura`,
                  f.`lote`,
                  df.`manual`,
                  f.`nFactura` numeroFactura,
                  f.`fechaFac`,
                  f.`ClienteNit`,
                  c.email emailCliente,
                  f.`ClienteFactura`,
                  t.`sigla`,
                  f.`total`,
                  CONCAT(u.first_name, ' ', u.last_name) AS vendedor,
                  f.`anulada` estado,
                  f.fecha, 
                  f.glosa,
                  p.idPago,
                  p.`numPago`,
                  f.`pagada`,
                  f.almacen idAlmacen,
                  e.clientePedido pedido,
                  CASE
                    WHEN f.moneda = 1 THEN 'BOB'
                    WHEN f.moneda = 2 THEN CONCAT('$', 'U$')
                  END moneda,
                  CASE
                    WHEN f.`anulada` = 1 THEN 'ANULADA'
                    WHEN f.`pagada` = 0 THEN 'NO PAGADA'
                    WHEN f.`pagada` = 1 THEN 'PAGADA'
                    WHEN f.`pagada` = 2 THEN 'PAGO PARCIAL'
                  END pagadaF,
                  CONCAT(ua.first_name, ' ', ua.last_name) emisor,
                  tp.tipoPago,
                  fs.codigoRecepcion,
                  fs.cuf,
                  fs.cafc,
                  fs.pedido,
                  sp.descripcion metodoPago,
                  fs.leyenda,
                  fs.fechaEmision fechaEmisionSiat,
                  f.lote,
                  a.almacen
                FROM
                  factura_egresos fe
                  INNER JOIN egresos e on e.idegresos = fe.idegresos
                  INNER JOIN factura f on f.idFactura = fe.idFactura
                  LEFT JOIN pago_factura pf ON f.idFactura = pf.idFactura
                  LEFT JOIN pago p ON p.idPago = pf.idPago
                  INNER JOIN tmovimiento t on e.tipomov = t.id
                  INNER JOIN datosfactura df on df.idDatosFactura = f.lote
                  INNER JOIN users u on u.id = e.vendedor
                  INNER JOIN users ua ON ua.id = f.autor
                  INNER JOIN tipoPago tp ON tp.id = f.tipoPago
                  INNER JOIN factura_siat fs ON fs.factura_id = f.idFactura
                  INNER JOIN clientes c ON c.idCliente = f.cliente
                  INNER JOIN siat_sincro_tipo_metodo_pago sp ON sp.codigoClasificador = fs.codigoMetodoPago
                  INNER JOIN siat_cuis cuis ON cuis.sucursal = fs.codigoSucursal
                  AND cuis.codigoPuntoVenta = fs.codigoPuntoVenta
                  AND cuis.active = 1
                  INNER JOIN almacenes a ON a.idalmacen = f.almacen
                WHERE
                  f.fechaFac BETWEEN @ini AND @end
                  AND (
                    f.lote = 0
                    OR f.lote = '138'
                  )
                GROUP BY
                  fe.idFactura
                ORDER BY
                  f.`fechaFac` DESC,
                  f.`nFactura` DESC,
                  f.idFactura DESC
            """
            
            df = pd.read_sql(query_text, engine)

            return df

        except Exception as e:
            raise

    def close(self) -> None:
        """Close database connection and dispose of engine."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed."""
        self.close()


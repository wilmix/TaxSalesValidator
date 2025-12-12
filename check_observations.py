#!/usr/bin/env python3
"""Verificar observaciones en SAS para NOVIEMBRE 2025."""

import pandas as pd
from sqlalchemy import create_engine, text, inspect

# Conectar a la base de datos SAS
engine = create_engine('mysql+pymysql://root:root@localhost:3306/sas_local')

print("=" * 80)
print("📊 VERIFICACIÓN DE OBSERVACIONES EN SAS")
print("=" * 80)

# Primero, listar todas las tablas
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\n📋 Tablas disponibles en sas_local: {tables}")

with engine.connect() as conn:
    # Buscar la tabla correcta
    if 'sales_transactions' in tables:
        table_name = 'sales_transactions'
    elif 'transactions' in tables:
        table_name = 'transactions'
    elif 'sales' in tables:
        table_name = 'sales'
    else:
        print(f"❌ No se encontró tabla de ventas. Tablas disponibles: {tables}")
        exit(1)
    
    print(f"\n✅ Usando tabla: {table_name}")
    
    # Consultar registros con observación 'No existe en inventarios'
    query_all = f'''
    SELECT 
        DATE(fecha) as fecha,
        MONTH(fecha) as mes,
        YEAR(fecha) as ano,
        COUNT(*) as cantidad
    FROM {table_name}
    WHERE observations = 'No existe en inventarios'
    GROUP BY DATE(fecha), MONTH(fecha), YEAR(fecha)
    ORDER BY fecha DESC
    LIMIT 20
    '''
    
    df_all = pd.read_sql(text(query_all), conn)
    print('\n📅 Últimas fechas con observación "No existe en inventarios":')
    print(df_all.to_string(index=False))
    
    # Filtrar solo NOVIEMBRE 2025
    query_nov = f'''
    SELECT 
        cuf,
        fecha,
        numeroFactura,
        observations
    FROM {table_name}
    WHERE observations = 'No existe en inventarios'
    AND MONTH(fecha) = 11
    AND YEAR(fecha) = 2025
    ORDER BY fecha
    '''
    
    df_nov = pd.read_sql(text(query_nov), conn)
    print(f'\n✅ Registros en NOVIEMBRE 2025: {len(df_nov)}')
    if len(df_nov) > 0:
        print(df_nov.to_string(index=False))
    
    # Resumen por mes/año
    query_summary = f'''
    SELECT 
        YEAR(fecha) as ano,
        MONTH(fecha) as mes,
        COUNT(*) as cantidad
    FROM {table_name}
    WHERE observations = 'No existe en inventarios'
    GROUP BY YEAR(fecha), MONTH(fecha)
    ORDER BY ano DESC, mes DESC
    '''
    
    df_summary = pd.read_sql(text(query_summary), conn)
    print('\n📈 Resumen por mes/año:')
    print(df_summary.to_string(index=False))

print("\n" + "=" * 80)

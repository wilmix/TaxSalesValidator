#!/usr/bin/env python
"""Verify that observations were synced correctly to SAS."""

import pandas as pd
from src.sas_connector import SasConnector

try:
    connector = SasConnector(debug=False)
    engine = connector._get_engine()
    
    # Query para ver registros con observaciones
    query = '''
    SELECT authorization_code, observations, customer_name 
    FROM sales_registers 
    WHERE observations IS NOT NULL 
    ORDER BY created_at DESC 
    LIMIT 10
    '''
    
    df = pd.read_sql(query, engine)
    
    if len(df) > 0:
        print('✅ Registros encontrados con observaciones:\n')
        for i, row in df.iterrows():
            print(f'{i+1}. CUF: {row["authorization_code"]}')
            print(f'   Observación: {row["observations"]}')
            print(f'   Cliente: {row["customer_name"]}')
            print()
    else:
        print('❌ No se encontraron registros con observaciones')
        
    # Contar cuántos registros tienen observaciones
    count_query = 'SELECT COUNT(*) as total FROM sales_registers WHERE observations IS NOT NULL'
    count_df = pd.read_sql(count_query, engine)
    print(f'\n📊 Total de registros con observaciones: {count_df.iloc[0]["total"]}')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

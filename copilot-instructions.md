# Instrucciones de Copilot para Web Scraping y Descarga CSV

## 🎯 Objetivo del Proyecto

Crear un script de Python minimalista, robusto y asíncrono (usando asyncio y playwright.async_api) que implemente el siguiente flujo en la página de impuestos.gob.bo:

### Flujo del Proyecto

1. Navegar e iniciar sesión con credenciales específicas.
2. Navegar al módulo "Registro de Ventas".
3. Seleccionar el mes de SEPTIEMBRE como periodo de búsqueda.
4. Descargar el reporte en formato CSV.
5. Procesar el archivo CSV con Pandas.
6. Comparar/Validar la información de ventas con un sistema de inventario local.
7. **(OPCIONAL)** Sincronizar datos validados al sistema contable SAS (con --sync-sas flag).

### Fases Implementadas

- **Fase 1**: Descarga y procesamiento de datos SIAT (web scraping + CUF extraction)
- **Fase 2**: Consulta de base de datos de inventario local (MySQL)
- **Fase 3**: Comparación y validación (SIAT vs Inventario)
- **Fase 4**: Sincronización a sistema contable SAS (opcional, atomic transactions)

## 💡 Principios Fundamentales (KISS, DRY, SOLID)

### KISS (Keep It Simple, Stupid)

- **Asincronía Clara**: El código debe usar playwright.async_api y asyncio de la manera más legible posible.
- **Funciones Atómicas**: Cada función debe ejecutar un solo paso del flujo de forma clara (e.g., login(), navigate_to_reports(), download_csv()).

### DRY (Don't Repeat Yourself)

- **Configuración Única**: Los selectores (getByRole, locator), la URL base y las credenciales NO deben estar hardcodeados en la lógica del scraper. Deben ser pasados como argumentos o cargados desde un único punto de configuración.
- **Cierre de Recursos**: Asegurar que el contexto del navegador y el navegador mismo se cierren siempre, idealmente usando async with para manejo automático.

### SOLID - Single Responsibility Principle (SRP)

El script debe estar dividido en bloques lógicos principales, estrictamente separados:

**Core Modules (Phases 1-3):**
1. **config.py**: Almacena selectores, credenciales y configuración general.
2. **web_scraper.py / WebScraper**: Contiene solo la lógica de interacción web (Playwright).
3. **file_manager.py / FileManager**: Contiene solo la lógica de manejo de archivos CSV (guardar, limpiar, verificar).
4. **data_processor.py / DataProcessor**: Contiene solo la lógica de lectura y preparación del DataFrame de Pandas.
5. **sales_validator.py / SalesValidator**: Contiene solo la lógica de comparación de filas entre el CSV y los datos de inventario local.

**SAS Integration Modules (Phase 4):**
6. **sas_connector.py / SasConnector**: Conexión y operaciones de base de datos MySQL (SAS) con transacciones atómicas.
7. **sas_mapper.py / SasMapper**: Transformación de datos SIAT a formato sales_registers (35 campos).
8. **sas_syncer.py / SasSyncer**: Orquestación del sync (prerequisites check, transform, upsert, stats).

## 🇬🇧 Convención de Nombres (DRY)

**MANDATORIO**: Todo el código (nombres de archivos, módulos, clases, funciones y variables) debe estar escrito en inglés utilizando snake_case o PascalCase según corresponda. (Ej: def download_report_csv en lugar de def descargar_reporte_csv).

## 🛠 Pautas Técnicas

- **Librerías**: playwright.async_api, pathlib, pandas.
- **Locators**: Utiliza los locators generados por Codegen (getByRole, locator) ya que son robustos, pero asegúrate de pasarlos como variables/configuración.
- **Descarga**: Usa el patrón robusto page.waitForEvent('download') para capturar la descarga de CSV. La descarga debe guardarse en una ruta definida por pathlib.
- **Manejo de Errores**: Incluir manejo de excepciones (try/except) para fallas de navegación o errores de autenticación.
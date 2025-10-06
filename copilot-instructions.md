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

## 💡 Principios Fundamentales (KISS, DRY, SOLID)

### KISS (Keep It Simple, Stupid)

- **Asincronía Clara**: El código debe usar playwright.async_api y asyncio de la manera más legible posible.
- **Funciones Atómicas**: Cada función debe ejecutar un solo paso del flujo de forma clara (e.g., login(), navigate_to_reports(), download_csv()).

### DRY (Don't Repeat Yourself)

- **Configuración Única**: Los selectores (getByRole, locator), la URL base y las credenciales NO deben estar hardcodeados en la lógica del scraper. Deben ser pasados como argumentos o cargados desde un único punto de configuración.
- **Cierre de Recursos**: Asegurar que el contexto del navegador y el navegador mismo se cierren siempre, idealmente usando async with para manejo automático.

### SOLID - Single Responsibility Principle (SRP)

El script debe estar dividido en al menos 5 bloques lógicos principales, estrictamente separados:

1. **config.py**: Almacena selectores y credenciales.
2. **scraper.py / WebScraper**: Contiene solo la lógica de interacción web (Playwright).
3. **file_manager.py / FileManager**: Contiene solo la lógica de manejo de archivos CSV (guardar, limpiar, verificar).
4. **data_processor.py / DataProcessor**: Contiene solo la lógica de lectura y preparación del DataFrame de Pandas.
5. **validator.py / SalesValidator**: Contiene solo la lógica de comparación de filas entre el CSV y los datos de inventario local.

## 🇬🇧 Convención de Nombres (DRY)

**MANDATORIO**: Todo el código (nombres de archivos, módulos, clases, funciones y variables) debe estar escrito en inglés utilizando snake_case o PascalCase según corresponda. (Ej: def download_report_csv en lugar de def descargar_reporte_csv).

## 🛠 Pautas Técnicas

- **Librerías**: playwright.async_api, pathlib, pandas.
- **Locators**: Utiliza los locators generados por Codegen (getByRole, locator) ya que son robustos, pero asegúrate de pasarlos como variables/configuración.
- **Descarga**: Usa el patrón robusto page.waitForEvent('download') para capturar la descarga de CSV. La descarga debe guardarse en una ruta definida por pathlib.
- **Manejo de Errores**: Incluir manejo de excepciones (try/except) para fallas de navegación o errores de autenticación.
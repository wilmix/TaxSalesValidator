"""Configuration module for TaxSalesValidator.

This module loads environment variables and stores all constants used throughout the application.
Following DRY principle: single source of truth for all configuration.
"""

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
ROOT_DIR: Final[Path] = Path(__file__).parent.parent.absolute()


class Config:
    """Central configuration class storing all application constants."""

    # ==================== ENVIRONMENT VARIABLES ====================
    USER_EMAIL: str = os.getenv("USER_EMAIL", "")
    USER_PASSWORD: str = os.getenv("USER_PASSWORD", "")
    USER_NIT: str = os.getenv("USER_NIT", "")

    # MySQL Database Configuration (Inventory System)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # SAS Database Configuration (Accounting System - Optional)
    SAS_DB_HOST: str = os.getenv("SAS_DB_HOST", "localhost")
    SAS_DB_PORT: int = int(os.getenv("SAS_DB_PORT", "3306"))
    SAS_DB_NAME: str = os.getenv("SAS_DB_NAME", "")
    SAS_DB_USER: str = os.getenv("SAS_DB_USER", "")
    SAS_DB_PASSWORD: str = os.getenv("SAS_DB_PASSWORD", "")
    
    # SAS Sync Configuration
    SAS_SYNC_BATCH_SIZE: int = int(os.getenv("SAS_SYNC_BATCH_SIZE", "100"))
    SAS_SYNC_TIMEOUT: int = int(os.getenv("SAS_SYNC_TIMEOUT", "300"))

    # Optional configuration
    HEADLESS_MODE: bool = os.getenv("HEADLESS_MODE", "true").lower() == "true"
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "60"))
    PAGE_TIMEOUT: int = int(os.getenv("PAGE_TIMEOUT", "30"))

    # ==================== URLS ====================
    LOGIN_URL: Final[str] = (
        "https://login.impuestos.gob.bo/realms/login2/protocol/openid-connect/auth"
        "?client_id=app-frontend"
        "&redirect_uri=https%3A%2F%2Fsiat.impuestos.gob.bo%2Fv2%2Flauncher%2F"
        "&state=383c2e56-bae1-455b-8fb2-0352db1c05f1"
        "&response_mode=fragment"
        "&response_type=code"
        "&scope=openid"
        "&nonce=2434bad9-66a4-4fdb-87cd-65e6c0167293"
    )

    # ==================== PLAYWRIGHT SELECTORS (from Codegen) ====================
    # Login page selectors
    SELECTOR_USERNAME: Final[dict] = {"role": "textbox", "name": "Usuario o email"}
    SELECTOR_PASSWORD: Final[dict] = {"role": "textbox", "name": "Correo Contraseña"}
    SELECTOR_NIT: Final[dict] = {"role": "textbox", "name": "NIT/CUR/CI"}
    SELECTOR_LOGIN_BUTTON: Final[dict] = {"role": "button", "name": "INGRESAR"}

    # Navigation selectors
    SELECTOR_BILLING_SYSTEM: Final[dict] = {
        "role": "heading",
        "name": "SISTEMA DE FACTURACIÓN",
        "exact": True,
    }
    SELECTOR_PURCHASES_SALES_MENU: Final[str] = "#mat-menu-panel-6 h4"
    SELECTOR_PURCHASES_SALES_TEXT: Final[str] = "Registro de Compras y Ventas"
    SELECTOR_CONSULTAS_LINK: Final[dict] = {"role": "link", "name": " CONSULTAS "}
    SELECTOR_CONSULTAS_SUBMENU_LINK: Final[dict] = {"role": "link", "name": " Consultas"}

    # Consultas page selectors - Filter configuration
    SELECTOR_TIPO_CONSULTA_LABEL: Final[str] = '[id="formPrincipal:txtConsulta_label"]'
    SELECTOR_TIPO_CONSULTA_OPTION: Final[dict] = {"role": "option", "name": "CONSULTA VENTAS", "exact": True}
    
    SELECTOR_TIPO_ESPECIFICACION_LABEL: Final[str] = '[id="formPrincipal:ddlEspecificiacionVenta_label"]'
    SELECTOR_TIPO_ESPECIFICACION_OPTION: Final[dict] = {"role": "option", "name": "FACTURA ESTANDAR"}
    
    SELECTOR_GESTION_LABEL: Final[str] = '[id="formPrincipal:txtGestion_label"]'
    # Year will be dynamic based on parameter
    
    SELECTOR_PERIODO_SPAN: Final[str] = '[id="formPrincipal:txtPeriodo"] span'
    SELECTOR_PERIODO_LABEL: Final[str] = '[id="formPrincipal:txtPeriodo_label"]'
    # Month will be dynamic based on parameter
    
    SELECTOR_SEARCH_BUTTON: Final[dict] = {"role": "button", "name": " Buscar"}
    SELECTOR_DOWNLOAD_BUTTON: Final[dict] = {
        "role": "button",
        "name": " Descargar Consulta Csv",
    }

    # Logout selectors
    SELECTOR_USER_MENU: Final[dict] = {"role": "link", "name": "willy@hergo.com.bo"}
    SELECTOR_LOGOUT_BUTTON: Final[dict] = {"role": "button", "name": "Cerrar sesión"}
    SELECTOR_CONFIRM_LOGOUT: Final[dict] = {"role": "button", "name": "Si", "exact": True}

    # ==================== FILE PATHS ====================
    DATA_DIR: Final[Path] = ROOT_DIR / "data"
    DOWNLOAD_DIR: Final[Path] = DATA_DIR / "downloads"
    PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
    LOGS_DIR: Final[Path] = ROOT_DIR / "logs"

    # ==================== BROWSER CONFIGURATION ====================
    BROWSER_ARGS: Final[list[str]] = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ]

    VIEWPORT_SIZE: Final[dict] = {"width": 1920, "height": 1080}

    # ==================== DATA PROCESSING ====================
    CSV_ENCODING_OPTIONS: Final[list[str]] = ["utf-8", "latin-1", "iso-8859-1"]
    
    # Default values for filters
    DEFAULT_YEAR: int = 2025
    DEFAULT_MONTH: Final[str] = "PREVIOUS_MONTH"  # Will calculate previous month dynamically
    DEFAULT_TIPO_CONSULTA: Final[str] = "CONSULTA VENTAS"
    DEFAULT_TIPO_ESPECIFICACION: Final[str] = "FACTURA ESTANDAR"
    
    # Spanish month names (for selector)
    MONTH_NAMES: Final[dict[int, str]] = {
        1: "ENERO",
        2: "FEBRERO",
        3: "MARZO",
        4: "ABRIL",
        5: "MAYO",
        6: "JUNIO",
        7: "JULIO",
        8: "AGOSTO",
        9: "SEPTIEMBRE",
        10: "OCTUBRE",
        11: "NOVIEMBRE",
        12: "DICIEMBRE",
    }
    
    @staticmethod
    def get_previous_month() -> str:
        """Get previous month name in Spanish.
        
        Returns:
            Spanish name of the previous month (e.g., "SEPTIEMBRE")
        """
        from datetime import datetime
        
        current_date = datetime.now()
        # Calculate previous month
        if current_date.month == 1:
            previous_month = 12
        else:
            previous_month = current_date.month - 1
            
        return Config.MONTH_NAMES[previous_month]
    
    @staticmethod
    def get_current_year() -> int:
        """Get current year.
        
        Returns:
            Current year as integer
        """
        from datetime import datetime
        return datetime.now().year
    
    @staticmethod
    def get_date_range_from_month(year: int, month_name: str) -> tuple[str, str]:
        """Calculate start and end date from year and Spanish month name.
        
        Args:
            year: Year for the date range (e.g., 2025)
            month_name: Spanish month name in uppercase (e.g., "SEPTIEMBRE")
        
        Returns:
            Tuple of (start_date, end_date) in format 'YYYY-MM-DD'
            Example: (2025-09-01', '2025-09-30')
        
        Raises:
            ValueError: If month_name is not valid
        """
        from calendar import monthrange
        
        # Reverse lookup: month name -> month number
        month_number = None
        for num, name in Config.MONTH_NAMES.items():
            if name == month_name.upper():
                month_number = num
                break
        
        if month_number is None:
            raise ValueError(
                f"Invalid month name: {month_name}. "
                f"Valid months: {', '.join(Config.MONTH_NAMES.values())}"
            )
        
        # Calculate first and last day of the month
        start_date = f"{year}-{month_number:02d}-01"
        _, last_day = monthrange(year, month_number)
        end_date = f"{year}-{month_number:02d}-{last_day:02d}"
        
        return start_date, end_date

    # ==================== VALIDATION ====================
    @classmethod
    def validate(cls) -> None:
        """Validate that all required environment variables are set.

        Raises:
            ValueError: If any required environment variable is missing.
        """
        required_vars = {
            "USER_EMAIL": cls.USER_EMAIL,
            "USER_PASSWORD": cls.USER_PASSWORD,
            "USER_NIT": cls.USER_NIT,
            "DB_HOST": cls.DB_HOST,
            "DB_NAME": cls.DB_NAME,
            "DB_USER": cls.DB_USER,
            "DB_PASSWORD": cls.DB_PASSWORD,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please create a .env file based on .env.example"
            )
    
    @classmethod
    def is_sas_configured(cls) -> bool:
        """Check if SAS database is configured.
        
        Returns:
            True if all required SAS database variables are set, False otherwise
        """
        return bool(
            cls.SAS_DB_HOST and
            cls.SAS_DB_NAME and
            cls.SAS_DB_USER and
            cls.SAS_DB_PASSWORD
        )

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Validate configuration on import
Config.validate()
Config.ensure_directories()

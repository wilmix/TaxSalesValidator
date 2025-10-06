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
    SELECTOR_SALES_LINK: Final[dict] = {"role": "link", "name": " VENTAS "}
    SELECTOR_SALES_REGISTRY_LINK: Final[dict] = {"role": "link", "name": " Registro de Ventas"}

    # Sales report page selectors
    SELECTOR_PERIOD_PANEL: Final[str] = '[id="formPrincipal:pnlCriterios_content"] div'
    SELECTOR_PERIOD_LABEL: Final[str] = '[id="formPrincipal:txtPeriodo_label"]'
    SELECTOR_MONTH_OPTION: Final[dict] = {"role": "option", "name": "SEPTIEMBRE"}
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
    DEFAULT_MONTH: Final[str] = "SEPTIEMBRE"

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
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please create a .env file based on .env.example"
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

# 📋 TaxSalesValidator - Project Development Plan

## 🎯 Project Overview

**Objective**: Create a minimal, robust, and asynchronous Python scraper using Playwright to:
1. Login to impuestos.gob.bo
2. Navigate to "Registro de Ventas" (Sales Report)
3. Select SEPTEMBER as the search period
4. Download ZIP file containing CSV report
5. Extract and process CSV with Pandas
6. Load data into DataFrame for future validation against local inventory

**Phase 1 Scope**: Web scraping → ZIP download → CSV extraction → DataFrame loading

---

## 🏗️ Architecture & Design Principles

### KISS (Keep It Simple, Stupid)
- Clear asynchronous flow with `playwright.async_api` and `asyncio`
- One function = one responsibility (atomic functions)
- Readable code over clever tricks

### DRY (Don't Repeat Yourself)
- Single source of truth for configuration (`.env` + `config.py`)
- No hardcoded selectors or credentials in business logic
- Reusable utility functions

### SOLID Principles
**Single Responsibility Principle (SRP)** - Each module has ONE job:

| Module | Responsibility | Dependencies |
|--------|---------------|-------------|
| `config.py` | Load environment variables and store constants | `dotenv`, `pathlib` |
| `web_scraper.py` | Browser automation and web interaction | `playwright.async_api` |
| `file_manager.py` | ZIP extraction and CSV file handling | `zipfile`, `pathlib` |
| `data_processor.py` | CSV reading and DataFrame operations | `pandas` |
| `main.py` | Orchestrate the entire flow | All above modules |

---

## 📁 Project Structure

```
TaxSalesValidator/
├── .env                      # Environment variables (IGNORED by git)
├── .env.example              # Template for environment setup
├── .gitignore                # Python, uv, and sensitive files
├── README.md                 # User documentation
├── PLAN.md                   # This file
├── pyproject.toml            # UV dependency management
├── uv.lock                   # Lock file for reproducible builds
│
├── src/
│   ├── __init__.py
│   ├── config.py             # Configuration loader
│   ├── web_scraper.py        # WebScraper class (Playwright logic)
│   ├── file_manager.py       # FileManager class (ZIP/CSV handling)
│   ├── data_processor.py     # DataProcessor class (Pandas operations)
│   └── main.py               # Entry point / orchestrator
│
├── data/                     # Downloaded files storage
│   ├── downloads/            # Raw ZIP files
│   └── processed/            # Extracted CSV files
│
└── tests/                    # Unit and integration tests (future)
    └── __init__.py
```

---

## 🔧 Technical Stack

### Core Dependencies (uv managed)
- **Python**: 3.11+
- **playwright**: Async browser automation
- **pandas**: Data manipulation and CSV processing
- **python-dotenv**: Environment variable management
- **pathlib**: Modern file path handling (stdlib)
- **zipfile**: ZIP extraction (stdlib)
- **asyncio**: Asynchronous programming (stdlib)

### Development Dependencies
- **pytest**: Testing framework (future phase)
- **pytest-asyncio**: Async test support (future phase)

---

## 🚀 Development Phases

### **Phase 1: Web Scraping & Data Extraction** ⭐ CURRENT FOCUS

#### 1.1 Project Initialization
- [x] Create project structure
- [x] Initialize `uv` project with `pyproject.toml`
- [x] Setup `.env.example` and `.gitignore`
- [x] Initialize git repository

#### 1.2 Configuration Module (`config.py`)
**Purpose**: Centralize all configuration and eliminate hardcoding

**Implementation**:
```python
# config.py structure
class Config:
    # Environment variables
    USER_EMAIL: str
    USER_PASSWORD: str
    USER_NIT: str
    
    # URLs
    LOGIN_URL: str = "https://login.impuestos.gob.bo/realms/login2/..."
    
    # Selectors (from Codegen)
    SELECTOR_USERNAME: dict
    SELECTOR_PASSWORD: dict
    SELECTOR_NIT: dict
    # ... etc
    
    # File paths
    DOWNLOAD_DIR: Path
    PROCESSED_DIR: Path
```

**Environment Variables (.env)**:
```env
USER_EMAIL=willy@hergo.com.bo
USER_PASSWORD=Hergo10
USER_NIT=1000991026
```

#### 1.3 Web Scraper Module (`web_scraper.py`)
**Purpose**: Handle ALL browser interactions with Playwright

**Class Structure**:
```python
class WebScraper:
    async def __aenter__() / __aexit__()  # Context manager for browser lifecycle
    
    async def login()                      # Authenticate user
    async def navigate_to_sales_report()   # Go to "Registro de Ventas"
    async def select_month(month: str)     # Select period (SEPTIEMBRE)
    async def search_report()              # Click "Buscar" button
    async def download_zip() -> Path       # Download ZIP and return path
    async def logout()                     # Close session gracefully
```

**Key Features**:
- Use `async with playwright.async_api.async_playwright()` for resource management
- Implement `page.wait_for_event('download')` pattern for robust downloads
- Error handling for timeouts, network issues, login failures
- Headless mode by default (configurable)

#### 1.4 File Manager Module (`file_manager.py`)
**Purpose**: Handle ZIP extraction and CSV file operations

**Class Structure**:
```python
class FileManager:
    def extract_zip(zip_path: Path) -> Path       # Extract ZIP, return CSV path
    def get_latest_download() -> Path | None      # Find most recent file
    def cleanup_old_files(days: int = 7)          # Maintain clean data directory
    def validate_csv_exists(csv_path: Path) -> bool
```

**Key Features**:
- Use `zipfile` library for extraction
- Implement file validation (size, extension, readability)
- Organize files by timestamp for traceability

#### 1.5 Data Processor Module (`data_processor.py`)
**Purpose**: Read CSV and prepare DataFrame for analysis

**Class Structure**:
```python
class DataProcessor:
    def load_csv_to_dataframe(csv_path: Path) -> pd.DataFrame
    def validate_dataframe(df: pd.DataFrame) -> bool  # Check columns, data types
    def get_dataframe_summary(df: pd.DataFrame) -> dict  # Stats for logging
```

**Key Features**:
- Handle encoding issues (UTF-8, Latin-1)
- Validate expected columns from tax authority CSV
- Type conversions for dates, amounts, etc.

#### 1.6 Main Orchestrator (`main.py`)
**Purpose**: Coordinate the entire flow using asyncio

**Flow**:
```python
async def main():
    1. Load configuration
    2. Initialize WebScraper context manager
    3. Execute scraping flow:
       - Login
       - Navigate to sales report
       - Select September
       - Download ZIP
       - Logout
    4. Extract ZIP with FileManager
    5. Load CSV to DataFrame with DataProcessor
    6. Log success metrics (rows, columns, file size)
    7. Return DataFrame for further processing
```

**Error Handling Strategy**:
- Wrap each phase in try/except blocks
- Log errors with context (timestamp, step, error message)
- Clean up browser resources even on failure
- Save partial results when possible

---

### **Phase 2: Data Processing & Validation** (Future)

#### 2.1 Sales Validator Module (`validator.py`)
- Compare CSV data against local inventory database
- Identify discrepancies (missing sales, mismatched amounts)
- Generate validation report

#### 2.2 Inventory Integration
- Connect to local inventory system (DB/API/CSV)
- Normalize data formats for comparison
- Handle date range matching

---

### **Phase 3: Automation & Reporting** (Future)

#### 3.1 Scheduling
- Add cron/scheduled task support
- Monthly automatic downloads
- Email notifications

#### 3.2 Reporting
- Generate Excel/PDF reports
- Dashboard with validation metrics
- Historical trend analysis

---

## 📝 Coding Standards

### Naming Conventions
- **ALL code in ENGLISH** (mandatory)
- **Functions/Variables**: `snake_case` (e.g., `download_report_csv`)
- **Classes**: `PascalCase` (e.g., `WebScraper`, `FileManager`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `LOGIN_URL`, `MAX_RETRIES`)
- **Files**: `snake_case.py`

### Code Style
- **Type hints**: Use for all function signatures
- **Docstrings**: Google style for classes and public methods
- **Line length**: Max 100 characters
- **Imports**: Standard library → Third-party → Local (separated by blank lines)

### Example Function:
```python
async def download_zip(self, timeout: int = 30) -> Path:
    """
    Download the sales report ZIP file from the tax authority portal.
    
    Args:
        timeout: Maximum seconds to wait for download completion
        
    Returns:
        Path object pointing to the downloaded ZIP file
        
    Raises:
        TimeoutError: If download exceeds timeout period
        FileNotFoundError: If downloaded file cannot be located
    """
    # Implementation
```

---

## 🔒 Security & Best Practices

### Sensitive Data
- **NEVER commit** `.env` to git
- Use `.env.example` as template with placeholder values
- Rotate credentials periodically
- Consider using keyring/vault for production

### Error Logging
- Log to file: `logs/scraper_YYYYMMDD.log`
- Include timestamps, severity levels
- Don't log sensitive data (passwords, full NITs)

### Browser Configuration
- Use headless mode in production
- Set reasonable timeouts (30s for navigation, 60s for downloads)
- Clear browser cache/cookies between runs
- Handle CAPTCHA/MFA scenarios (future consideration)

---

## 🧪 Testing Strategy (Future Phase)

### Unit Tests
- Mock Playwright interactions
- Test CSV parsing with sample files
- Validate configuration loading

### Integration Tests
- End-to-end flow in test environment
- Use recorded HAR files for reproducibility

---

## 📊 Success Metrics (Phase 1)

**Deliverables**:
- ✅ Successfully login to impuestos.gob.bo
- ✅ Navigate to "Registro de Ventas"
- ✅ Select SEPTEMBER and trigger search
- ✅ Download ZIP file (validated by file existence)
- ✅ Extract CSV from ZIP
- ✅ Load CSV into pandas DataFrame
- ✅ Log DataFrame shape and sample data

**Performance Targets**:
- Total execution time: < 60 seconds
- Download success rate: > 95%
- Zero credential leaks in logs/code

---

## 🛠️ Development Commands

### Setup
```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project and install dependencies
uv init
uv add playwright pandas python-dotenv
uv run playwright install chromium

# Setup environment
cp .env.example .env
# Edit .env with actual credentials
```

### Run
```bash
# Execute scraper
uv run python src/main.py

# With debug mode
uv run python src/main.py --debug
```

### Git Workflow
```bash
# Initialize repository
git init
git add .
git commit -m "Initial project structure"

# Feature branch workflow
git checkout -b feature/web-scraper
# ... make changes ...
git commit -m "Implement WebScraper with login and download"
git checkout main
git merge feature/web-scraper
```

---

## 🚦 Current Status

**Phase**: 1.1 - Project Initialization  
**Next Steps**:
1. Create folder structure
2. Initialize uv project
3. Setup configuration files
4. Begin WebScraper implementation

**Estimated Timeline**:
- Phase 1 complete: 2-3 days
- Basic scraper working: Day 1
- File processing + DataFrame: Day 2
- Testing + documentation: Day 3

---

## 📚 References

- [Playwright Python Docs](https://playwright.dev/python/docs/intro)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Python Async Best Practices](https://docs.python.org/3/library/asyncio.html)

---

**Last Updated**: 2025-10-06  
**Version**: 1.0.0  
**Status**: 🟢 Active Development

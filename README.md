# 🧾 TaxSalesValidator

> **Automated web scraper for downloading and processing sales reports from the Bolivian Tax Authority (impuestos.gob.bo)**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-async-green.svg)](https://playwright.dev/python/)
[![UV](https://img.shields.io/badge/package%20manager-uv-orange.svg)](https://github.com/astral-sh/uv)

---

## 📖 Overview

TaxSalesValidator is a Python-based automation tool that:
1. **Authenticates** to the Bolivian Tax Authority portal (SIAT)
2. **Navigates** to the Sales Registry module ("Registro de Ventas")
3. **Downloads** monthly sales reports in CSV format (packaged in ZIP)
4. **Processes** the data using Pandas for validation and analysis
5. **Validates** sales records against local inventory systems (future feature)

### Why This Project?

- **Eliminate Manual Work**: No more repetitive login → navigate → download cycles
- **Data Accuracy**: Automated extraction reduces human error
- **Audit Trail**: Timestamped downloads and processing logs
- **Extensible**: Built with SOLID principles for easy feature additions

---

## ✨ Features

### Phase 1 (Current - MVP)
- ✅ Async web scraping with Playwright
- ✅ Secure credential management via `.env`
- ✅ Robust ZIP download and extraction
- ✅ CSV to Pandas DataFrame conversion
- ✅ Configurable month selection (default: SEPTIEMBRE)
- ✅ Automatic browser cleanup and error handling

### Phase 2 (Planned)
- ⏳ Sales data validation against local inventory
- ⏳ Discrepancy reporting (Excel/PDF)
- ⏳ Scheduled monthly execution
- ⏳ Email notifications

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** installed
- **UV package manager** ([install guide](https://github.com/astral-sh/uv#installation))
- Valid credentials for impuestos.gob.bo (SIAT)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/TaxSalesValidator.git
cd TaxSalesValidator

# 2. Install dependencies with UV
uv sync

# 3. Install Playwright browsers
uv run playwright install chromium

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your actual credentials
```

### Configuration

Edit the `.env` file with your tax portal credentials:

```env
# .env
USER_EMAIL=your.email@company.com
USER_PASSWORD=YourSecurePassword
USER_NIT=1234567890
```

⚠️ **IMPORTANT**: Never commit the `.env` file to version control!

---

## 💻 Usage

### Basic Execution

```bash
# Run the scraper (downloads September report by default)
uv run python src/main.py
```

### Advanced Options

```bash
# Download a specific month
uv run python src/main.py --month OCTUBRE

# Enable verbose logging
uv run python src/main.py --debug

# Specify custom download directory
uv run python src/main.py --output-dir ./custom_data
```

### Expected Output

```
🔐 Logging in to impuestos.gob.bo...
✅ Authentication successful

📂 Navigating to Sales Registry module...
✅ Navigation complete

📅 Selecting period: SEPTIEMBRE...
✅ Period selected

⬇️  Downloading report...
✅ ZIP downloaded: data/downloads/sales_report_20251006_143022.zip

📦 Extracting CSV from ZIP...
✅ CSV extracted: data/processed/sales_20251006_143022.csv

📊 Loading data into DataFrame...
✅ DataFrame loaded: 1,247 rows × 23 columns

Summary:
  - Total records: 1,247
  - Date range: 2024-09-01 to 2024-09-30
  - Total sales amount: Bs. 2,456,789.50
```

---

## 📁 Project Structure

```
TaxSalesValidator/
├── .env                      # Your credentials (DO NOT COMMIT)
├── .env.example              # Template for setup
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── PLAN.md                   # Detailed development plan
├── pyproject.toml            # UV dependencies
├── uv.lock                   # Dependency lock file
│
├── src/
│   ├── __init__.py
│   ├── config.py             # Configuration loader
│   ├── web_scraper.py        # Playwright automation
│   ├── file_manager.py       # ZIP/CSV file handling
│   ├── data_processor.py     # Pandas data processing
│   └── main.py               # Application entry point
│
├── data/
│   ├── downloads/            # Downloaded ZIP files
│   └── processed/            # Extracted CSV files
│
├── logs/                     # Execution logs
│
└── tests/                    # Unit and integration tests
    └── __init__.py
```

---

## 🏗️ Architecture

This project follows **SOLID principles** with clear separation of concerns:

| Module | Responsibility |
|--------|---------------|
| `config.py` | Load environment variables and store constants |
| `web_scraper.py` | Browser automation (login, navigation, download) |
| `file_manager.py` | File operations (ZIP extraction, cleanup) |
| `data_processor.py` | CSV parsing and DataFrame operations |
| `main.py` | Orchestrate the entire workflow |

### Design Principles

- **KISS**: Simple, readable async/await flow
- **DRY**: Single source of truth for configuration
- **SRP**: Each class has ONE clear responsibility
- **Type Safety**: Full type hints for better IDE support
- **Error Handling**: Graceful failures with detailed logging

---

## 🔧 Development

### Setup Development Environment

```bash
# Install dev dependencies
uv add --dev pytest pytest-asyncio black ruff

# Format code
uv run black src/

# Lint code
uv run ruff check src/
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src tests/
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add: brief description of changes"

# Push and create PR
git push origin feature/your-feature-name
```

---

## 🔒 Security

### Credential Management

- **Local Development**: Use `.env` file (gitignored)
- **Production**: Use environment variables or secret management services
- **Never** hardcode credentials in source code
- **Rotate** passwords regularly

### Data Privacy

- CSV files contain sensitive tax information
- Store downloaded files securely
- Implement automatic cleanup of old files
- Consider encrypting stored data

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Login Fails
```
Error: Login failed - invalid credentials
```
**Solution**: Verify your `.env` credentials are correct

#### 2. Download Timeout
```
Error: TimeoutError waiting for download
```
**Solution**: Check internet connection or increase timeout in `config.py`

#### 3. Playwright Browser Not Found
```
Error: Executable doesn't exist at /path/to/chromium
```
**Solution**: Run `uv run playwright install chromium`

#### 4. CSV Encoding Issues
```
Error: UnicodeDecodeError
```
**Solution**: The script automatically tries UTF-8 and Latin-1 encodings

### Debug Mode

Enable detailed logging to diagnose issues:

```bash
uv run python src/main.py --debug
```

This will:
- Show browser window (non-headless)
- Log all HTTP requests
- Save screenshots on errors
- Print detailed stack traces

---

## 📊 Dependencies

### Core Libraries

- **playwright** (1.40+): Browser automation
- **pandas** (2.1+): Data manipulation
- **python-dotenv** (1.0+): Environment variable management

### Development Tools

- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking (optional)

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Follow** the coding standards (see `PLAN.md`)
4. **Write** tests for new features
5. **Commit** with clear messages (`git commit -m 'Add: amazing feature'`)
6. **Push** to the branch (`git push origin feature/AmazingFeature`)
7. **Open** a Pull Request

### Code Standards

- All code in **English**
- Use **type hints**
- Follow **PEP 8** style guide
- Write **docstrings** for public methods
- Keep functions **under 50 lines**

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- [Playwright Python](https://playwright.dev/python/) for excellent browser automation
- [UV](https://github.com/astral-sh/uv) for fast Python package management
- [Pandas](https://pandas.pydata.org/) for powerful data processing
- Bolivian Tax Authority (SIN) for providing the SIAT portal

---

## 📅 Roadmap

### Version 1.0 (Current)
- [x] Basic web scraping functionality
- [x] ZIP download and extraction
- [x] CSV to DataFrame conversion

### Version 1.1 (Next)
- [ ] Sales validation against inventory
- [ ] Excel report generation
- [ ] Unit test coverage (>80%)

### Version 2.0 (Future)
- [ ] Scheduled execution (cron jobs)
- [ ] Email notifications
- [ ] Web dashboard for monitoring
- [ ] Multi-month batch downloads
- [ ] Historical data comparison

---

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [PLAN.md](PLAN.md) for architecture details
3. Open an [issue](https://github.com/yourusername/TaxSalesValidator/issues) on GitHub
4. Contact the maintainer via email

---

**Made with ❤️ and Python** | **Automation for Tax Compliance**

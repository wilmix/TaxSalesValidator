# 🚀 Quick Setup Guide

## Step-by-Step Installation

### 1. Install UV Package Manager

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Dependencies

```bash
# Navigate to project directory
cd TaxSalesValidator

# Install Python dependencies with UV
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# On Windows: notepad .env
# On macOS/Linux: nano .env
```

**Edit the `.env` file:**
```env
USER_EMAIL=your.email@company.com
USER_PASSWORD=YourSecurePassword
USER_NIT=1234567890
```

### 4. Run the Scraper

```bash
# Download September report (default)
uv run python -m src.main

# Download specific month
uv run python -m src.main --month OCTUBRE

# Enable debug mode (shows browser)
uv run python -m src.main --debug
```

---

## Troubleshooting

### UV Not Found
```bash
# Add UV to PATH (Windows PowerShell)
$env:Path += ";$env:USERPROFILE\.cargo\bin"

# Add UV to PATH (macOS/Linux)
export PATH="$HOME/.cargo/bin:$PATH"
```

### Import Errors
```bash
# Reinstall dependencies
uv sync --reinstall
```

### Playwright Browser Not Found
```bash
# Reinstall browsers
uv run playwright install chromium --force
```

---

## Next Steps After Setup

1. **Test Run**: Execute `uv run python -m src.main --debug` to see the browser in action
2. **Review Output**: Check `data/downloads/` for ZIP files and `data/processed/` for CSV files
3. **Customize**: Edit `src/config.py` to change months or timeouts
4. **Automate**: Schedule with cron (Linux/macOS) or Task Scheduler (Windows)

---

## Project Structure Overview

```
TaxSalesValidator/
├── src/
│   ├── config.py          # ⚙️ Configuration (URLs, selectors, credentials)
│   ├── web_scraper.py     # 🌐 Browser automation (Playwright)
│   ├── file_manager.py    # 📁 File operations (ZIP extraction)
│   ├── data_processor.py  # 📊 Data processing (Pandas)
│   └── main.py            # 🎯 Main orchestrator
├── data/
│   ├── downloads/         # 📦 Downloaded ZIP files
│   └── processed/         # 📄 Extracted CSV files
└── logs/                  # 📝 Error logs and screenshots
```

---

## Common Commands

```bash
# Run with specific month
uv run python -m src.main --month ENERO
uv run python -m src.main --month FEBRERO
uv run python -m src.main --month MARZO
# ... etc

# Check project structure
tree  # Linux/macOS
Get-ChildItem -Recurse  # Windows PowerShell

# View recent downloads
ls -lh data/downloads/  # Linux/macOS
dir data\downloads  # Windows

# Clean old files (manual)
uv run python -c "from src.file_manager import FileManager; FileManager.cleanup_old_files(FileManager.Config.DOWNLOAD_DIR, days=7, pattern='*.zip', dry_run=False)"
```

---

## Development Commands

```bash
# Format code
uv run black src/

# Lint code
uv run ruff check src/

# Run tests (when available)
uv run pytest

# Update dependencies
uv sync --upgrade
```

---

**Need Help?** Check [README.md](README.md) or [PLAN.md](PLAN.md) for detailed documentation.

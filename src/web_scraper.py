"""Web scraper module for TaxSalesValidator.

This module handles all browser automation using Playwright.
Responsibility: Login, navigation, and file download from impuestos.gob.bo
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Download, Page, async_playwright

from .config import Config


class WebScraper:
    """Async web scraper for the Bolivian Tax Authority portal (SIAT).

    This class manages browser lifecycle and implements the complete scraping flow:
    - Authentication
    - Navigation to Sales Registry
    - Month selection
    - ZIP file download
    - Session logout

    Usage:
        async with WebScraper() as scraper:
            zip_path = await scraper.run_full_flow(month="SEPTIEMBRE")
    """

    def __init__(self, headless: bool = Config.HEADLESS_MODE) -> None:
        """Initialize the web scraper.

        Args:
            headless: Whether to run browser in headless mode (default from Config)
        """
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self) -> "WebScraper":
        """Context manager entry: Initialize browser."""
        await self._initialize_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit: Clean up browser resources."""
        await self._cleanup_browser()

    async def _initialize_browser(self) -> None:
        """Initialize Playwright browser and create context."""
        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=Config.BROWSER_ARGS,
        )

        self._context = await self._browser.new_context(
            viewport=Config.VIEWPORT_SIZE,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        # Set default timeouts
        self._context.set_default_timeout(Config.PAGE_TIMEOUT * 1000)

        self._page = await self._context.new_page()

        print("✅ Browser initialized")

    async def _cleanup_browser(self) -> None:
        """Close browser and clean up resources."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        print("✅ Browser closed")

    async def login(self) -> None:
        """Authenticate to the tax portal.

        Raises:
            TimeoutError: If login page doesn't load or elements not found
            ValueError: If page is not initialized
        """
        if not self._page:
            raise ValueError("Browser not initialized. Use 'async with' context manager.")

        print("🔐 Logging in to impuestos.gob.bo...")

        # Navigate to login page
        await self._page.goto(Config.LOGIN_URL, wait_until="domcontentloaded")

        # Fill login form
        await self._page.get_by_role(**Config.SELECTOR_USERNAME).click()
        await self._page.get_by_role(**Config.SELECTOR_USERNAME).fill(Config.USER_EMAIL)

        await self._page.get_by_role(**Config.SELECTOR_PASSWORD).click()
        await self._page.get_by_role(**Config.SELECTOR_PASSWORD).fill(Config.USER_PASSWORD)

        await self._page.get_by_role(**Config.SELECTOR_NIT).click()
        await self._page.get_by_role(**Config.SELECTOR_NIT).fill(Config.USER_NIT)

        # Submit login
        await self._page.get_by_role(**Config.SELECTOR_LOGIN_BUTTON).click()

        # Wait for successful login (billing system heading appears)
        await self._page.get_by_role(**Config.SELECTOR_BILLING_SYSTEM).wait_for(
            state="visible", timeout=10000
        )

        print("✅ Authentication successful")

    async def navigate_to_sales_report(self) -> None:
        """Navigate from dashboard to Sales Registry module.

        Raises:
            TimeoutError: If navigation elements not found
            ValueError: If page is not initialized
        """
        if not self._page:
            raise ValueError("Browser not initialized. Use 'async with' context manager.")

        print("📂 Navigating to Sales Registry module...")

        # Click on billing system heading to open menu
        await self._page.get_by_role(**Config.SELECTOR_BILLING_SYSTEM).click()

        # Wait for menu panel and click on "Registro de Compras y Ventas"
        menu_item = self._page.locator(Config.SELECTOR_PURCHASES_SALES_MENU).filter(
            has_text=Config.SELECTOR_PURCHASES_SALES_TEXT
        )
        await menu_item.click()

        # Click on "VENTAS" link
        await self._page.get_by_role(**Config.SELECTOR_SALES_LINK).click()

        # Click on "Registro de Ventas"
        await self._page.get_by_role(**Config.SELECTOR_SALES_REGISTRY_LINK).click()

        # Wait for page to load (period panel appears)
        await self._page.locator(Config.SELECTOR_PERIOD_PANEL).first.wait_for(
            state="visible", timeout=10000
        )

        print("✅ Navigation complete")

    async def select_month(self, month: str = Config.DEFAULT_MONTH) -> None:
        """Select the report period (month).

        Args:
            month: Month name in Spanish (e.g., "SEPTIEMBRE", "OCTUBRE")

        Raises:
            TimeoutError: If month selector not found
            ValueError: If page is not initialized
        """
        if not self._page:
            raise ValueError("Browser not initialized. Use 'async with' context manager.")

        print(f"📅 Selecting period: {month}...")

        # Click on period dropdown
        await self._page.locator(Config.SELECTOR_PERIOD_LABEL).click()

        # Small delay to ensure dropdown is open
        await asyncio.sleep(0.5)

        # Select the specified month
        month_selector = {"role": "option", "name": month}
        await self._page.get_by_role(**month_selector).click()

        print(f"✅ Period selected: {month}")

    async def search_report(self) -> None:
        """Click the search button to load report data.

        Raises:
            TimeoutError: If search button not found
            ValueError: If page is not initialized
        """
        if not self._page:
            raise ValueError("Browser not initialized. Use 'async with' context manager.")

        print("🔍 Searching for report...")

        await self._page.get_by_role(**Config.SELECTOR_SEARCH_BUTTON).click()

        # Wait for results to load (download button appears)
        await self._page.get_by_role(**Config.SELECTOR_DOWNLOAD_BUTTON).wait_for(
            state="visible", timeout=15000
        )

        print("✅ Report loaded")

    async def download_zip(self) -> Path:
        """Download the sales report ZIP file.

        Returns:
            Path to the downloaded ZIP file

        Raises:
            TimeoutError: If download doesn't complete within timeout
            ValueError: If page is not initialized
        """
        if not self._page:
            raise ValueError("Browser not initialized. Use 'async with' context manager.")

        print("⬇️  Downloading report...")

        # Set up download event listener BEFORE clicking button
        async with self._page.expect_download(
            timeout=Config.DOWNLOAD_TIMEOUT * 1000
        ) as download_info:
            await self._page.get_by_role(**Config.SELECTOR_DOWNLOAD_BUTTON).click()

        download: Download = await download_info.value

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sales_report_{timestamp}.zip"
        destination_path = Config.DOWNLOAD_DIR / filename

        # Save the downloaded file
        await download.save_as(destination_path)

        print(f"✅ ZIP downloaded: {destination_path}")

        return destination_path

    async def logout(self) -> None:
        """Logout from the tax portal.

        Raises:
            TimeoutError: If logout elements not found
            ValueError: If page is not initialized
        """
        if not self._page:
            raise ValueError("Browser not initialized. Use 'async with' context manager.")

        print("🚪 Logging out...")

        # Click user menu (email link)
        user_menu = self._page.get_by_role(
            **{"role": "link", "name": Config.USER_EMAIL}
        )
        await user_menu.click()

        # Click logout button
        await self._page.get_by_role(**Config.SELECTOR_LOGOUT_BUTTON).click()

        # Confirm logout
        await self._page.get_by_role(**Config.SELECTOR_CONFIRM_LOGOUT).click()

        print("✅ Logout successful")

    async def run_full_flow(self, month: str = Config.DEFAULT_MONTH) -> Path:
        """Execute the complete scraping flow.

        Args:
            month: Month to download report for (default: SEPTIEMBRE)

        Returns:
            Path to the downloaded ZIP file

        Raises:
            Exception: Any error during the scraping process
        """
        try:
            await self.login()
            await self.navigate_to_sales_report()
            await self.select_month(month)
            await self.search_report()
            zip_path = await self.download_zip()
            await self.logout()

            return zip_path

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            # Take screenshot for debugging if page exists
            if self._page:
                screenshot_path = Config.LOGS_DIR / f"error_{datetime.now():%Y%m%d_%H%M%S}.png"
                await self._page.screenshot(path=screenshot_path)
                print(f"📸 Error screenshot saved: {screenshot_path}")
            raise

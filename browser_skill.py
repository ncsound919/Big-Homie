"""
Browser Control Skill
Headless browser automation using Playwright for web scraping, testing, and automation
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


@dataclass
class BrowserTask:
    """A browser automation task"""

    url: str
    actions: list[dict[str, Any]]
    wait_for: Optional[str] = None
    screenshot: bool = False
    extract: Optional[list[str]] = None


@dataclass
class BrowserResult:
    """Result of browser automation"""

    success: bool
    url: str
    title: str
    content: Optional[str] = None
    screenshot_path: Optional[str] = None
    extracted_data: Optional[dict] = None
    error: Optional[str] = None


class BrowserSkill:
    """
    Advanced browser automation skill

    Capabilities:
    - Navigate to URLs
    - Fill forms
    - Click elements
    - Extract data
    - Take screenshots
    - Handle authentication
    - Execute JavaScript
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def __aenter__(self):
        """Context manager entry - start browser"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close browser"""
        await self.close()

    async def start(self, headless: bool = True):
        """Start browser instance"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080}, user_agent="Mozilla/5.0 (Big Homie Agent)"
            )
            self.page = await self.context.new_page()
            logger.info("Browser started")

    async def close(self):
        """Close browser instance"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        logger.info("Browser closed")

    async def navigate(self, url: str, wait_for: Optional[str] = None) -> BrowserResult:
        """
        Navigate to a URL

        Args:
            url: URL to visit
            wait_for: Optional CSS selector to wait for

        Returns:
            BrowserResult with page info
        """
        try:
            if not self.page:
                await self.start()

            await self.page.goto(url, wait_until="domcontentloaded")

            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=10000)

            title = await self.page.title()
            content = await self.page.content()

            return BrowserResult(success=True, url=self.page.url, title=title, content=content)

        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return BrowserResult(success=False, url=url, title="", error=str(e))

    async def click(self, selector: str, wait: bool = True) -> bool:
        """
        Click an element

        Args:
            selector: CSS selector
            wait: Wait for element to be visible

        Returns:
            Success status
        """
        try:
            if wait:
                await self.page.wait_for_selector(selector, state="visible", timeout=5000)

            await self.page.click(selector)
            logger.debug(f"Clicked: {selector}")
            return True

        except Exception as e:
            logger.error(f"Click failed: {selector} - {e}")
            return False

    async def fill(self, selector: str, text: str, wait: bool = True) -> bool:
        """
        Fill a form field

        Args:
            selector: CSS selector
            text: Text to enter
            wait: Wait for element

        Returns:
            Success status
        """
        try:
            if wait:
                await self.page.wait_for_selector(selector, state="visible", timeout=5000)

            await self.page.fill(selector, text)
            logger.debug(f"Filled: {selector}")
            return True

        except Exception as e:
            logger.error(f"Fill failed: {selector} - {e}")
            return False

    async def extract_text(self, selector: str) -> Optional[str]:
        """
        Extract text from an element

        Args:
            selector: CSS selector

        Returns:
            Extracted text or None
        """
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
            return None

        except Exception as e:
            logger.error(f"Extract failed: {selector} - {e}")
            return None

    async def extract_multiple(self, selector: str, attribute: Optional[str] = None) -> list[str]:
        """
        Extract text/attributes from multiple elements

        Args:
            selector: CSS selector
            attribute: Optional attribute name (href, src, etc.)

        Returns:
            List of extracted values
        """
        try:
            elements = await self.page.query_selector_all(selector)

            if attribute:
                return [
                    await elem.get_attribute(attribute)
                    for elem in elements
                    if await elem.get_attribute(attribute)
                ]
            else:
                texts = [await elem.text_content() for elem in elements]
                return [text for text in texts if text]

        except Exception as e:
            logger.error(f"Extract multiple failed: {selector} - {e}")
            return []

    async def screenshot(self, path: Optional[str] = None, full_page: bool = True) -> Optional[str]:
        """
        Take screenshot

        Args:
            path: Optional save path (auto-generated if None)
            full_page: Capture full page or just viewport

        Returns:
            Screenshot path or None
        """
        try:
            if not path:
                timestamp = asyncio.get_event_loop().time()
                path = f"screenshot_{timestamp}.png"

            await self.page.screenshot(path=path, full_page=full_page)
            logger.info(f"Screenshot saved: {path}")
            return path

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    async def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript

        Args:
            script: JavaScript code to execute

        Returns:
            Script result
        """
        try:
            result = await self.page.evaluate(script)
            return result

        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return None

    async def get_cookies(self) -> list[dict]:
        """Get all cookies"""
        if self.context:
            return await self.context.cookies()
        return []

    async def set_cookies(self, cookies: list[dict]):
        """Set cookies"""
        if self.context:
            await self.context.add_cookies(cookies)

    async def execute_task(self, task: BrowserTask) -> BrowserResult:
        """
        Execute a complex browser automation task

        Args:
            task: BrowserTask with URL and actions

        Returns:
            BrowserResult with all requested data
        """
        try:
            # Navigate to URL
            result = await self.navigate(task.url, task.wait_for)
            if not result.success:
                return result

            # Execute actions
            for action in task.actions:
                action_type = action.get("type")

                if action_type == "click":
                    await self.click(action["selector"])

                elif action_type == "fill":
                    await self.fill(action["selector"], action["text"])

                elif action_type == "wait":
                    await asyncio.sleep(action.get("seconds", 1))

                elif action_type == "wait_for":
                    await self.page.wait_for_selector(action["selector"])

                elif action_type == "script":
                    await self.execute_script(action["script"])

            # Extract data if requested
            extracted = {}
            if task.extract:
                for selector in task.extract:
                    extracted[selector] = await self.extract_text(selector)

            # Take screenshot if requested
            screenshot_path = None
            if task.screenshot:
                screenshot_path = await self.screenshot()

            return BrowserResult(
                success=True,
                url=self.page.url,
                title=await self.page.title(),
                content=await self.page.content(),
                screenshot_path=screenshot_path,
                extracted_data=extracted if extracted else None,
            )

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return BrowserResult(success=False, url=task.url, title="", error=str(e))


# Convenience functions


async def quick_navigate(url: str, screenshot: bool = False) -> BrowserResult:
    """Quick navigation helper"""
    async with BrowserSkill() as browser:
        result = await browser.navigate(url)
        if screenshot and result.success:
            result.screenshot_path = await browser.screenshot()
    return result


async def quick_scrape(url: str, selectors: dict[str, str]) -> dict[str, Optional[str]]:
    """
    Quick scraping helper

    Args:
        url: URL to scrape
        selectors: Dict of {name: css_selector}

    Returns:
        Dict of {name: extracted_text}
    """
    async with BrowserSkill() as browser:
        await browser.navigate(url)

        results = {}
        for name, selector in selectors.items():
            results[name] = await browser.extract_text(selector)

    return results


# Global browser instance (reusable for efficiency)
browser_skill = BrowserSkill()

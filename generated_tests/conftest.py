"""
Конфигурация pytest и фикстуры для тестов
"""

import pytest
from playwright.sync_api import Page, Browser, BrowserContext


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Настройки запуска браузера"""
    return {
        "headless": False,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ],
    }


@pytest.fixture(scope="session")
def browser(browser_type_launch_args):
    """Фикстура браузера"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(**browser_type_launch_args)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """Фикстура контекста браузера"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080}, ignore_https_errors=True
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Фикстура страницы"""
    page = context.new_page()
    yield page
    page.close()

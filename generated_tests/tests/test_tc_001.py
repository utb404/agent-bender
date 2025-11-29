import pytest
from playwright.sync_api import Page, expect


# Определение класса для модели страницы установки Playwright
class PlaywrightInstallationPage:
    def __init__(self, page: Page):
        self.page = page
        # Локатор для заголовка с текстом 'Installation'
        self.heading_installation = page.locator("h1", has_text="Installation")
        # Локатор для вводного текста о Playwright для end-to-end тестирования
        self.intro_text = page.locator(
            "p",
            has_text="Playwright was created specifically to accommodate the needs of end-to-end testing"
        )


# Определение класса с тестами
class TestPlaywrightInstallationPage:
    # Фикстура для инициализации страницы установки Playwright
    @pytest.fixture(scope="function")
    def playwright_installation_page(self, page: Page) -> PlaywrightInstallationPage:
        # Переход на страницу установки Playwright для Python
        page.goto("https://playwright.dev/python/docs/intro")
        return PlaywrightInstallationPage(page)

    # Тест-кейс для проверки заголовка и текстов на странице установки Playwright
    def test_page_title_and_content(
        self, playwright_installation_page: PlaywrightInstallationPage
    ):
        page = playwright_installation_page.page

        # Проверка, что заголовок страницы содержит 'Installation | Playwright Python'
        expect(page).to_have_title("Installation | Playwright Python")

        # Проверка наличия заголовка с текстом 'Installation'
        expect(playwright_installation_page.heading_installation).to_be_visible()

        # Проверка наличия вводного текста про Playwright для end-to-end тестирования
        expect(playwright_installation_page.intro_text).to_be_visible()

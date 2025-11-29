from playwright.sync_api import Page, expect


class BasePage:
    def __init__(self, page: Page):
        self.page = page


class UnknownPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Локаторы элементов на странице
        self._page_title = self.page.locator("#page_title")
        self._heading = self.page.locator("h1#heading")
        self._text_content = self.page.locator("p#text_content")

    def verify_text_content(self):
        """
        Проверяет, что на странице присутствует вводный текст про Playwright для end-to-end тестирования.
        """
        expect(self._text_content).to_have_text(
            "Playwright was created specifically to accommodate the needs of end-to-end testing"
        )

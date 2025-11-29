from playwright.sync_api import Page, expect


class BasePage:
    def __init__(self, page: Page):
        self.page = page


class IntroPage(BasePage):
    """
    Класс-объект страницы вводного руководства по Playwright для Python.
    Наследуется от базового класса BasePage.
    """

    def __init__(self, page: Page):
        super().__init__(page)
        self._url = "https://playwright.dev/python/docs/intro"

    def navigate(self) -> None:
        """
        Переходит на страницу вводного руководства по Playwright для Python.
        """
        self.page.goto(self._url)

    def validate_url(self) -> None:
        """
        Проверяет, что текущий URL соответствует ожидаемому URL страницы.
        """
        expect(self.page).to_have_url(self._url)

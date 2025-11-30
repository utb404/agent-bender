"""CDP (Chrome DevTools Protocol) helper для улучшения селекторов и анализа DOM."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from playwright.sync_api import Browser, Page, CDPSession


logger = logging.getLogger(__name__)


@dataclass
class ElementInfo:
    """Информация об элементе DOM."""
    
    selector: str
    tag_name: str
    attributes: Dict[str, str]
    text_content: Optional[str] = None
    is_visible: bool = True
    is_interactive: bool = False
    suggested_selectors: List[str] = None
    
    def __post_init__(self):
        if self.suggested_selectors is None:
            self.suggested_selectors = []


@dataclass
class CDPAnalysisResult:
    """Результат анализа через CDP."""
    
    improved_selectors: Dict[str, str]  # оригинальный селектор -> улучшенный
    element_info: Dict[str, ElementInfo]  # селектор -> информация об элементе
    dom_snapshot: Optional[Dict[str, Any]] = None
    network_requests: List[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.network_requests is None:
            self.network_requests = []


class CDPHelper:
    """
    Вспомогательный класс для работы с Chrome DevTools Protocol.
    
    Используется для:
    - Анализа DOM и улучшения селекторов
    - Захвата сетевых запросов
    - Мониторинга производительности
    - Генерации более точных локаторов
    """
    
    def __init__(
        self,
        browser: Optional[Browser] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация CDP helper.
        
        Args:
            browser: Экземпляр браузера Playwright (опционально).
            logger: Логгер.
        """
        self.browser = browser
        self._logger = logger or logging.getLogger(__name__)
        self._cdp_sessions: Dict[str, CDPSession] = {}
        self._network_requests: List[Dict[str, Any]] = []
    
    def analyze_page_for_selectors(
        self,
        page: Page,
        target_selectors: List[str],
        url: Optional[str] = None
    ) -> CDPAnalysisResult:
        """
        Анализ страницы для улучшения селекторов.
        
        Args:
            page: Страница Playwright.
            target_selectors: Список селекторов для анализа.
            url: URL страницы (если нужно перейти).
        
        Returns:
            CDPAnalysisResult: Результат анализа с улучшенными селекторами.
        """
        try:
            # Переход на страницу, если указан URL
            if url:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle", timeout=10000)
            
            # Получение CDP сессии
            cdp_session = page.context.new_cdp_session(page)
            self._cdp_sessions[page.url] = cdp_session
            
            # Анализ DOM
            dom_snapshot = self._get_dom_snapshot(cdp_session)
            
            # Анализ каждого селектора
            improved_selectors = {}
            element_info = {}
            
            for selector in target_selectors:
                try:
                    # Проверка существования элемента
                    element = page.locator(selector).first
                    if element.count() == 0:
                        self._logger.warning("Элемент не найден: %s", selector)
                        continue
                    
                    # Получение информации об элементе
                    info = self._analyze_element(page, element, selector, cdp_session)
                    element_info[selector] = info
                    
                    # Генерация улучшенных селекторов
                    improved = self._improve_selector(page, element, selector, info)
                    if improved and improved != selector:
                        improved_selectors[selector] = improved
                        self._logger.info("Улучшен селектор: %s -> %s", selector, improved)
                    else:
                        improved_selectors[selector] = selector
                
                except Exception as e:
                    self._logger.warning("Ошибка при анализе селектора %s: %s", selector, e)
                    improved_selectors[selector] = selector
            
            return CDPAnalysisResult(
                improved_selectors=improved_selectors,
                element_info=element_info,
                dom_snapshot=dom_snapshot
            )
        
        except Exception as e:
            self._logger.error("Ошибка при анализе страницы через CDP: %s", e)
            # Возвращаем результат с оригинальными селекторами
            return CDPAnalysisResult(
                improved_selectors={s: s for s in target_selectors},
                element_info={}
            )
    
    def _get_dom_snapshot(self, cdp_session: CDPSession) -> Optional[Dict[str, Any]]:
        """Получение снимка DOM через CDP."""
        try:
            # Используем DOM.getDocument для получения структуры DOM
            result = cdp_session.send("DOM.getDocument", {"depth": 3})
            return result
        except Exception as e:
            self._logger.warning("Не удалось получить DOM snapshot: %s", e)
            return None
    
    def _analyze_element(
        self,
        page: Page,  # noqa: ARG002
        element: Any,
        selector: str,
        cdp_session: CDPSession  # noqa: ARG002
    ) -> ElementInfo:
        """
        Анализ конкретного элемента.
        
        Args:
            page: Страница Playwright.
            element: Локатор элемента.
            selector: Оригинальный селектор.
            cdp_session: CDP сессия.
        
        Returns:
            ElementInfo: Информация об элементе.
        """
        try:
            # Получение базовой информации
            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            text_content = element.inner_text() if element.count() > 0 else None
            
            # Получение атрибутов
            attributes = element.evaluate("""
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            """)
            
            # Проверка видимости и интерактивности
            is_visible = element.is_visible() if element.count() > 0 else False
            is_interactive = self._is_interactive_element(tag_name, attributes)
            
            # Генерация предложенных селекторов
            suggested = self._generate_suggested_selectors(tag_name, attributes)
            
            return ElementInfo(
                selector=selector,
                tag_name=tag_name,
                attributes=attributes,
                text_content=text_content,
                is_visible=is_visible,
                is_interactive=is_interactive,
                suggested_selectors=suggested
            )
        
        except Exception as e:
            self._logger.warning("Ошибка при анализе элемента %s: %s", selector, e)
            return ElementInfo(
                selector=selector,
                tag_name="unknown",
                attributes={},
                is_visible=False,
                is_interactive=False
            )
    
    def _improve_selector(
        self,
        page: Page,
        element: Any,  # noqa: ARG002
        original_selector: str,
        element_info: ElementInfo
    ) -> str:
        """
        Улучшение селектора на основе анализа элемента.
        
        Приоритет селекторов:
        1. data-testid (если есть)
        2. id (если уникален)
        3. name (для форм)
        4. role + accessible name
        5. Комбинация тега + атрибутов
        6. Оригинальный селектор
        
        Args:
            page: Страница Playwright.
            element: Локатор элемента.
            original_selector: Оригинальный селектор.
            element_info: Информация об элементе.
        
        Returns:
            str: Улучшенный селектор.
        """
        attrs = element_info.attributes
        
        # 1. data-testid - лучший вариант для тестирования
        if "data-testid" in attrs:
            testid = attrs["data-testid"]
            if self._is_selector_unique(page, f'[data-testid="{testid}"]'):
                return f'[data-testid="{testid}"]'
        
        # 2. id - если уникален
        if "id" in attrs and attrs["id"]:
            element_id = attrs["id"]
            if self._is_selector_unique(page, f'#{element_id}'):
                return f'#{element_id}'
        
        # 3. name - для элементов форм
        if element_info.tag_name in ["input", "select", "textarea", "button"]:
            if "name" in attrs and attrs["name"]:
                name = attrs["name"]
                tag_selector = f'{element_info.tag_name}[name="{name}"]'
                if self._is_selector_unique(page, tag_selector):
                    return tag_selector
        
        # 4. role + accessible name
        if "role" in attrs:
            role = attrs["role"]
            if element_info.text_content:
                # Пробуем найти по role и тексту
                role_selector = f'[role="{role}"]'
                # Это не идеально, но лучше чем ничего
                if self._is_selector_unique(page, role_selector):
                    return role_selector
        
        # 5. Комбинация тега + важных атрибутов
        if attrs:
            # Ищем уникальные атрибуты
            for attr_name in ["type", "placeholder", "aria-label"]:
                if attr_name in attrs and attrs[attr_name]:
                    combined = f'{element_info.tag_name}[{attr_name}="{attrs[attr_name]}"]'
                    if self._is_selector_unique(page, combined):
                        return combined
        
        # 6. Возвращаем оригинальный селектор, если не удалось улучшить
        return original_selector
    
    def _is_selector_unique(self, page: Page, selector: str) -> bool:
        """Проверка уникальности селектора на странице."""
        try:
            count = page.locator(selector).count()
            return count == 1
        except (ValueError, AttributeError):
            return False
    
    def _is_interactive_element(self, tag_name: str, attributes: Dict[str, str]) -> bool:
        """Проверка, является ли элемент интерактивным."""
        interactive_tags = ["a", "button", "input", "select", "textarea", "label"]
        if tag_name in interactive_tags:
            return True
        
        # Проверка role
        role = attributes.get("role", "")
        interactive_roles = ["button", "link", "textbox", "checkbox", "radio", "menuitem"]
        if role in interactive_roles:
            return True
        
        # Проверка наличия обработчиков событий
        if any(attr.startswith("on") for attr in attributes.keys()):
            return True
        
        return False
    
    def _generate_suggested_selectors(
        self,
        tag_name: str,
        attributes: Dict[str, str],
        text_content: Optional[str] = None  # noqa: ARG002
    ) -> List[str]:
        """Генерация предложенных селекторов для элемента."""
        suggestions = []
        
        # data-testid
        if "data-testid" in attributes:
            suggestions.append(f'[data-testid="{attributes["data-testid"]}"]')
        
        # id
        if "id" in attributes and attributes["id"]:
            suggestions.append(f'#{attributes["id"]}')
        
        # name для форм
        if tag_name in ["input", "select", "textarea"] and "name" in attributes:
            suggestions.append(f'{tag_name}[name="{attributes["name"]}"]')
        
        # type для input
        if tag_name == "input" and "type" in attributes:
            type_attr = attributes["type"]
            if "name" in attributes:
                suggestions.append(f'input[type="{type_attr}"][name="{attributes["name"]}"]')
            else:
                suggestions.append(f'input[type="{type_attr}"]')
        
        # aria-label
        if "aria-label" in attributes:
            suggestions.append(f'[aria-label="{attributes["aria-label"]}"]')
        
        # role
        if "role" in attributes:
            suggestions.append(f'[role="{attributes["role"]}"]')
        
        return suggestions
    
    def enable_network_monitoring(self, page: Page) -> None:
        """
        Включение мониторинга сетевых запросов.
        
        Args:
            page: Страница Playwright.
        """
        try:
            cdp_session = page.context.new_cdp_session(page)
            cdp_session.send("Network.enable")
            
            # Подписка на события (упрощенная версия)
            # В реальной реализации нужно использовать правильные CDP события
            self._cdp_sessions[page.url] = cdp_session
            self._logger.info("Мониторинг сетевых запросов включен")
        
        except Exception as e:
            self._logger.warning("Не удалось включить мониторинг сети: %s", e)
    
    def get_network_requests(self) -> List[Dict[str, Any]]:
        """Получение списка захваченных сетевых запросов."""
        return self._network_requests.copy()
    
    def enable_performance_monitoring(self, page: Page) -> Dict[str, Any]:
        """
        Включение мониторинга производительности.
        
        Args:
            page: Страница Playwright.
        
        Returns:
            Dict: Метрики производительности.
        """
        try:
            cdp_session = page.context.new_cdp_session(page)
            
            # Включение Performance domain
            cdp_session.send("Performance.enable")
            
            # Получение метрик
            metrics = cdp_session.send("Performance.getMetrics")
            
            return {
                "metrics": metrics.get("metrics", []),
                "timestamp": metrics.get("timestamp")
            }
        
        except Exception as e:
            self._logger.warning("Не удалось получить метрики производительности: %s", e)
            return {}
    
    def cleanup(self) -> None:
        """Очистка ресурсов и закрытие CDP сессий."""
        for url, session in self._cdp_sessions.items():
            try:
                session.detach()
            except Exception as e:
                self._logger.warning("Ошибка при закрытии CDP сессии для %s: %s", url, e)
        
        self._cdp_sessions.clear()
        self._network_requests.clear()


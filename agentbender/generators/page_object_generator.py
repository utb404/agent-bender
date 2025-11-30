"""Page Object generator."""

from typing import Dict, Any, Optional, List
import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import re

from agentbender.models.test_case import TestCase, TestStep
from agentbender.models.config import GenerationOptions
from agentbender.providers.base_provider import BaseLLMProvider
from agentbender.core.prompt_builder import PromptBuilder
from agentbender.utils.formatter import CodeFormatter
from agentbender.utils.cdp_helper import CDPHelper, CDPAnalysisResult


logger = logging.getLogger(__name__)


class PageObjectGenerator:
    """Генератор Page Object классов."""
    
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        template_dir: Optional[Path] = None,
        formatter: Optional[CodeFormatter] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация генератора Page Objects.
        
        Args:
            llm_provider: Провайдер LLM.
            template_dir: Директория с шаблонами.
            formatter: Форматтер кода.
            logger: Логгер.
        """
        self.llm_provider = llm_provider
        self.formatter = formatter or CodeFormatter()
        self.logger = logger or logging.getLogger(__name__)
        
        # Настройка Jinja2
        if template_dir and Path(template_dir).exists():
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            template_path = Path(__file__).parent.parent / "templates"
            self.env = Environment(loader=FileSystemLoader(template_path))
        
        self.prompt_builder = PromptBuilder()
    
    def generate_from_test_case(
        self,
        test_case: TestCase,
        context: Optional[Any] = None,
        options: Optional[GenerationOptions] = None
    ) -> Dict[str, str]:
        """
        Генерация Page Objects из тест-кейса.
        
        Args:
            test_case: Тест-кейс.
            context: Контекст генерации.
            options: Опции генерации.
        
        Returns:
            Dict[str, str]: Словарь Page Objects (имя класса -> код).
        """
        options = options or GenerationOptions()
        
        # Анализ тест-кейса для определения страниц
        pages_info = self._analyze_pages(test_case)
        
        # Улучшение селекторов через CDP, если включено
        if options.use_cdp:
            pages_info = self._improve_selectors_with_cdp(pages_info, options)
        
        page_objects = {}
        
        for page_name, page_info in pages_info.items():
            try:
                page_code = self.generate(
                    page_name=page_name,
                    elements=page_info["elements"],
                    actions=page_info["actions"],
                    url=page_info.get("url"),
                    context=context,
                    options=options,
                    cdp_analysis=page_info.get("cdp_analysis")
                )
                
                class_name = self._page_name_to_class_name(page_name)
                page_objects[class_name] = page_code
                
            except Exception as e:
                self.logger.error(f"Ошибка при генерации Page Object для {page_name}: {e}")
                # Генерация из шаблона как fallback
                page_code = self._generate_from_template(
                    page_name,
                    page_info["elements"],
                    page_info["actions"],
                    page_info.get("url")
                )
                class_name = self._page_name_to_class_name(page_name)
                page_objects[class_name] = page_code
        
        return page_objects
    
    def generate(
        self,
        page_name: str,
        elements: Dict[str, str],
        actions: Dict[str, Any],
        url: Optional[str] = None,
        context: Optional[Any] = None,
        options: Optional[GenerationOptions] = None,
        cdp_analysis: Optional[CDPAnalysisResult] = None
    ) -> str:
        """
        Генерация Page Object класса.
        
        Args:
            page_name: Название страницы.
            elements: Словарь элементов (имя -> селектор).
            actions: Словарь действий.
            url: URL страницы (опционально).
            context: Контекст генерации.
            options: Опции генерации.
            cdp_analysis: Результат CDP анализа (опционально).
        
        Returns:
            str: Код Page Object класса.
        """
        options = options or GenerationOptions()
        
        # Построение промпта
        if context:
            self.prompt_builder.add_context(context)
        
        prompt = self.prompt_builder.build_page_object_prompt(
            page_name=page_name,
            elements=elements,
            actions=actions,
            options=options,
            cdp_analysis=cdp_analysis
        )
        
        # Генерация через LLM
        try:
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=PromptBuilder.SYSTEM_PROMPT,
                temperature=options.temperature or 0.7,
                max_tokens=options.max_tokens
            )
            
            code = response.content
            code = self._extract_code_from_markdown(code)
            code = self.formatter.format(code)
            
            return code
        
        except Exception as e:
            self.logger.error(f"Ошибка при генерации Page Object через LLM: {e}")
            # Fallback на шаблон
            return self._generate_from_template(page_name, elements, actions, url)
    
    def _analyze_pages(self, test_case: TestCase) -> Dict[str, Dict[str, Any]]:
        """
        Анализ тест-кейса для определения страниц и элементов.
        
        Args:
            test_case: Тест-кейс.
        
        Returns:
            Dict: Информация о страницах.
        """
        pages_info = {}
        
        for step in test_case.steps:
            # Определение страницы по URL или действию
            page_name = "UnknownPage"
            url = None
            
            if step.action == "navigate" and step.value:
                url = step.value
                # Извлечение имени страницы из URL
                page_name = self._extract_page_name_from_url(url)
            
            if page_name not in pages_info:
                pages_info[page_name] = {
                    "elements": {},
                    "actions": {},
                    "url": url
                }
            
            # Извлечение элементов и действий
            if step.target:
                element_name = self._extract_element_name(step.target)
                pages_info[page_name]["elements"][element_name] = step.target
            
            if step.action:
                action_name = self._action_to_method_name(step.action, step.target)
                pages_info[page_name]["actions"][action_name] = {
                    "action": step.action,
                    "target": step.target,
                    "value": step.value,
                    "description": step.description
                }
        
        return pages_info
    
    def _improve_selectors_with_cdp(
        self,
        pages_info: Dict[str, Dict[str, Any]],
        options: GenerationOptions
    ) -> Dict[str, Dict[str, Any]]:
        """
        Улучшение селекторов через CDP анализ.
        
        Args:
            pages_info: Информация о страницах.
            options: Опции генерации.
        
        Returns:
            Dict: Обновленная информация о страницах с улучшенными селекторами.
        """
        if not options.use_cdp:
            return pages_info
        
        try:
            from playwright.sync_api import sync_playwright
            
            cdp_helper = CDPHelper(logger=self.logger)
            improved_pages_info = {}
            
            with sync_playwright() as p:
                # Запуск браузера
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                
                for page_name, page_info in pages_info.items():
                    url = page_info.get("url")
                    if not url:
                        # Если нет URL, пропускаем CDP анализ
                        improved_pages_info[page_name] = page_info
                        continue
                    
                    try:
                        page = context.new_page()
                        
                        # Анализ селекторов через CDP
                        target_selectors = list(page_info["elements"].values())
                        if target_selectors:
                            cdp_result = cdp_helper.analyze_page_for_selectors(
                                page=page,
                                target_selectors=target_selectors,
                                url=url
                            )
                            
                            # Обновление селекторов
                            improved_elements = {}
                            for element_name, original_selector in page_info["elements"].items():
                                improved_selector = cdp_result.improved_selectors.get(
                                    original_selector,
                                    original_selector
                                )
                                improved_elements[element_name] = improved_selector
                            
                            # Обновление actions с улучшенными селекторами
                            improved_actions = {}
                            for action_name, action_info in page_info["actions"].items():
                                action_target = action_info.get("target")
                                if action_target and action_target in cdp_result.improved_selectors:
                                    improved_action_info = action_info.copy()
                                    improved_action_info["target"] = cdp_result.improved_selectors[action_target]
                                    improved_actions[action_name] = improved_action_info
                                else:
                                    improved_actions[action_name] = action_info
                            
                            improved_pages_info[page_name] = {
                                "elements": improved_elements,
                                "actions": improved_actions,
                                "url": url,
                                "cdp_analysis": cdp_result
                            }
                            
                            self.logger.info(
                                f"CDP анализ для {page_name}: улучшено {len(cdp_result.improved_selectors)} селекторов"
                            )
                        else:
                            improved_pages_info[page_name] = page_info
                        
                        page.close()
                    
                    except Exception as e:
                        self.logger.warning(
                            f"Ошибка при CDP анализе для {page_name}: {e}. Используются оригинальные селекторы."
                        )
                        improved_pages_info[page_name] = page_info
                
                browser.close()
                cdp_helper.cleanup()
            
            return improved_pages_info
        
        except ImportError:
            self.logger.warning("Playwright не установлен. CDP анализ пропущен.")
            return pages_info
        except Exception as e:
            self.logger.warning(f"Ошибка при инициализации CDP: {e}. Используются оригинальные селекторы.")
            return pages_info
    
    def _extract_page_name_from_url(self, url: str) -> str:
        """Извлечение имени страницы из URL."""
        # Простая логика: берем последнюю часть пути
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            return path_parts[-1].capitalize() + "Page"
        return "HomePage"
    
    def _extract_element_name(self, selector: str) -> str:
        """Извлечение имени элемента из селектора."""
        # Простая логика: берем атрибут name или id, или последнюю часть селектора
        if "name=" in selector:
            match = re.search(r"name=['\"]([^'\"]+)['\"]", selector)
            if match:
                return match.group(1).replace("-", "_")
        
        if "id=" in selector:
            match = re.search(r"id=['\"]([^'\"]+)['\"]", selector)
            if match:
                return match.group(1).replace("-", "_")
        
        # Fallback: используем последнюю часть селектора
        parts = selector.split(".")
        if parts:
            return parts[-1].replace("-", "_").replace("'", "").replace('"', "")
        
        return "element"
    
    def _action_to_method_name(self, action: str, target: Optional[str] = None) -> str:
        """Преобразование действия в имя метода."""
        action_map = {
            "navigate": "navigate",
            "fill": "fill",
            "click": "click",
            "verify": "verify",
            "select": "select",
        }
        
        base_name = action_map.get(action, action)
        
        if target:
            element_name = self._extract_element_name(target)
            if base_name == "fill":
                return f"fill_{element_name}"
            elif base_name == "click":
                return f"click_{element_name}"
        
        return base_name
    
    def _page_name_to_class_name(self, page_name: str) -> str:
        """Преобразование имени страницы в имя класса."""
        # Убираем "Page" если есть, и добавляем снова с правильным регистром
        name = page_name.replace("Page", "").replace("page", "")
        return name.capitalize() + "Page"
    
    def _extract_code_from_markdown(self, text: str) -> str:
        """Извлечение кода из markdown блоков."""
        code_block_pattern = r"```(?:python)?\n?(.*?)```"
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        return text.strip()
    
    def _generate_from_template(
        self,
        page_name: str,
        elements: Dict[str, str],
        actions: Dict[str, Any],
        url: Optional[str] = None
    ) -> str:
        """Генерация из шаблона (fallback)."""
        try:
            template = self.env.get_template("page_object_template.py.j2")
            
            # Преобразование actions в формат для шаблона
            methods = {}
            for action_name, action_info in actions.items():
                methods[action_name] = {
                    "description": action_info.get("description", ""),
                    "action": action_info.get("action"),
                    "target": self._extract_element_name(action_info.get("target", "")),
                    "value": action_info.get("value"),
                    "params": None,
                    "return_type": None
                }
            
            class_name = self._page_name_to_class_name(page_name)
            
            code = template.render(
                page_name=page_name,
                page_class_name=class_name,
                elements=elements,
                methods=methods,
                url=url
            )
            
            return self.formatter.format(code)
        except Exception as e:
            self.logger.error(f"Ошибка при генерации из шаблона: {e}")
            raise


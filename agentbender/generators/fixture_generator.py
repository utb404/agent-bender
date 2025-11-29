"""Fixture generator."""

from typing import Optional
import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from agentbender.models.config import GenerationOptions, PlaywrightConfig
from agentbender.utils.formatter import CodeFormatter


logger = logging.getLogger(__name__)


class FixtureGenerator:
    """Генератор фикстур pytest."""
    
    def __init__(
        self,
        template_dir: Optional[Path] = None,
        formatter: Optional[CodeFormatter] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация генератора фикстур.
        
        Args:
            template_dir: Директория с шаблонами.
            formatter: Форматтер кода.
            logger: Логгер.
        """
        self.formatter = formatter or CodeFormatter()
        self.logger = logger or logging.getLogger(__name__)
        
        # Настройка Jinja2
        if template_dir and Path(template_dir).exists():
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            template_path = Path(__file__).parent.parent / "templates"
            self.env = Environment(loader=FileSystemLoader(template_path))
    
    def generate(
        self,
        playwright_config: Optional[PlaywrightConfig] = None,
        options: Optional[GenerationOptions] = None
    ) -> str:
        """
        Генерация фикстур.
        
        Args:
            playwright_config: Конфигурация Playwright.
            options: Опции генерации.
        
        Returns:
            str: Код фикстур.
        """
        playwright_config = playwright_config or PlaywrightConfig()
        
        try:
            template = self.env.get_template("fixture_template.py.j2")
            
            code = template.render(
                browser=playwright_config.browser,
                headless=playwright_config.headless,
                viewport_width=playwright_config.viewport_width,
                viewport_height=playwright_config.viewport_height
            )
            
            return self.formatter.format(code)
        except Exception as e:
            self.logger.error(f"Ошибка при генерации фикстур: {e}")
            raise
    
    def generate_base_page(self) -> str:
        """
        Генерация базового класса BasePage.
        
        Returns:
            str: Код базового класса.
        """
        try:
            template = self.env.get_template("base_page_template.py.j2")
            code = template.render()
            return self.formatter.format(code)
        except Exception as e:
            self.logger.error(f"Ошибка при генерации BasePage: {e}")
            raise
    
    def generate_config_files(
        self,
        gpn_qa_utils_enabled: bool = True
    ) -> dict:
        """
        Генерация конфигурационных файлов.
        
        Args:
            gpn_qa_utils_enabled: Включена ли интеграция с gpn_qa_utils.
        
        Returns:
            dict: Словарь с конфигурационными файлами (имя файла -> содержимое).
        """
        try:
            template = self.env.get_template("config_template.py.j2")
            
            # Рендеринг шаблона для получения всех конфигов
            rendered = template.render(gpn_qa_utils_enabled=gpn_qa_utils_enabled)
            
            # Парсинг конфигов из шаблона (упрощенная версия)
            # В реальной реализации можно использовать более сложную логику
            config_files = {
                "pytest.ini": self._extract_config_section(rendered, "pytest_ini"),
                "requirements.txt": self._extract_config_section(rendered, "requirements_txt"),
            }
            
            return config_files
        except Exception as e:
            self.logger.error(f"Ошибка при генерации конфигурационных файлов: {e}")
            return {}
    
    def _extract_config_section(self, text: str, section_name: str) -> str:
        """Извлечение секции конфига из шаблона (упрощенная версия)."""
        # В реальной реализации нужно более сложное извлечение
        # Здесь возвращаем базовые конфиги
        if section_name == "pytest_ini":
            return """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
"""
        elif section_name == "requirements_txt":
            return """pytest>=7.4.0
playwright>=1.40.0
"""
        return ""


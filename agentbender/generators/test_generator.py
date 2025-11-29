"""Test code generator."""

from typing import Dict, Any, Optional
import logging
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path

from agentbender.models.test_case import TestCase
from agentbender.models.config import GenerationOptions
from agentbender.providers.base_provider import BaseLLMProvider
from agentbender.core.prompt_builder import PromptBuilder
from agentbender.utils.formatter import CodeFormatter


logger = logging.getLogger(__name__)


class TestCodeGenerator:
    """Генератор тестового кода."""
    
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        template_dir: Optional[Path] = None,
        formatter: Optional[CodeFormatter] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация генератора тестов.
        
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
            # Использование встроенных шаблонов
            template_path = Path(__file__).parent.parent / "templates"
            self.env = Environment(loader=FileSystemLoader(template_path))
        
        self.prompt_builder = PromptBuilder()
    
    def generate(
        self,
        test_case: TestCase,
        page_objects: Dict[str, str],
        context: Optional[Any] = None,
        options: Optional[GenerationOptions] = None
    ) -> str:
        """
        Генерация тестового кода.
        
        Args:
            test_case: Тест-кейс.
            page_objects: Словарь Page Objects (имя класса -> код).
            context: Контекст генерации.
            options: Опции генерации.
        
        Returns:
            str: Сгенерированный код теста.
        """
        options = options or GenerationOptions()
        
        # Построение промпта
        if context:
            self.prompt_builder.add_context(context)
        
        prompt = self.prompt_builder.build_test_prompt(test_case, options)
        
        # Генерация через LLM
        try:
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=PromptBuilder.SYSTEM_PROMPT,
                temperature=options.temperature or 0.7,
                max_tokens=options.max_tokens
            )
            
            code = response.content
            
            # Извлечение кода из markdown блоков, если есть
            code = self._extract_code_from_markdown(code)
            
            # Форматирование кода
            code = self.formatter.format(code)
            
            return code
        
        except Exception as e:
            self.logger.error(f"Ошибка при генерации теста: {e}")
            # Fallback на шаблон
            return self._generate_from_template(test_case, page_objects, options)
    
    def _extract_code_from_markdown(self, text: str) -> str:
        """Извлечение кода из markdown блоков."""
        import re
        
        # Поиск блоков кода в markdown
        code_block_pattern = r"```(?:python)?\n?(.*?)```"
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Если блоков нет, возвращаем весь текст
        return text.strip()
    
    def _generate_from_template(
        self,
        test_case: TestCase,
        page_objects: Dict[str, str],
        options: GenerationOptions
    ) -> str:
        """Генерация из шаблона (fallback)."""
        try:
            template = self.env.get_template("test_template.py.j2")
            
            code = template.render(
                test_case=test_case,
                page_objects=page_objects,
                use_fixtures=options.generate_fixtures,
                gpn_qa_utils_enabled=True  # Можно вынести в опции
            )
            
            return self.formatter.format(code)
        except Exception as e:
            self.logger.error(f"Ошибка при генерации из шаблона: {e}")
            raise


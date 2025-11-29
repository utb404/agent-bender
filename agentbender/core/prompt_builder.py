"""Prompt builder for LLM requests."""

from typing import Optional, Dict, Any
import logging

from agentbender.models.test_case import TestCase
from agentbender.models.config import GenerationContext, GenerationOptions


logger = logging.getLogger(__name__)


class PromptBuilder:
    """Построитель промптов для LLM."""
    
    SYSTEM_PROMPT = """Ты — эксперт по автоматизации тестирования веб-приложений.
Твоя задача — генерировать качественные автотесты на Python с использованием
Playwright и паттерна Page Object Model.

Требования:
- Использовать Playwright для автоматизации браузера
- Применять паттерн Page Object Model
- Использовать библиотеку @gpn_qa_utils для вспомогательных функций (если доступна)
- Следовать корпоративным стандартам кодирования
- Генерировать читаемый и поддерживаемый код
- Добавлять подробные комментарии и docstrings
- Использовать фикстуры pytest
- Включить валидации через expect() из Playwright
"""
    
    def __init__(
        self,
        context: Optional[GenerationContext] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация построителя.
        
        Args:
            context: Контекст генерации.
            logger: Логгер.
        """
        self.context = context
        self.logger = logger or logging.getLogger(__name__)
    
    def build_test_prompt(
        self,
        test_case: TestCase,
        options: GenerationOptions
    ) -> str:
        """
        Построение промпта для генерации теста.
        
        Args:
            test_case: Тест-кейс.
            options: Опции генерации.
        
        Returns:
            str: Промпт для LLM.
        """
        prompt_parts = []
        
        # Основная информация о тест-кейсе
        prompt_parts.append(f"Сгенерируй автотест на основе следующего тест-кейса:\n")
        prompt_parts.append(f"Тест-кейс ID: {test_case.id}")
        prompt_parts.append(f"Название: {test_case.title}")
        prompt_parts.append(f"Описание: {test_case.description}\n")
        
        # Шаги тест-кейса
        prompt_parts.append("Шаги:")
        for step in test_case.steps:
            step_desc = f"  {step.step_number}. {step.description}"
            if step.action:
                step_desc += f" (действие: {step.action})"
            if step.target:
                step_desc += f" (цель: {step.target})"
            if step.value:
                step_desc += f" (значение: {step.value})"
            prompt_parts.append(step_desc)
        
        prompt_parts.append(f"\nОжидаемый результат: {test_case.expected_result}")
        
        # Предусловия
        if test_case.preconditions:
            prompt_parts.append("\nПредусловия:")
            for precondition in test_case.preconditions:
                prompt_parts.append(f"  - {precondition}")
        
        # Контекст
        if self.context:
            context_text = self._build_context_text()
            if context_text:
                prompt_parts.append(f"\nДополнительный контекст:\n{context_text}")
        
        # Требования к коду
        prompt_parts.append("\nТребования к коду:")
        prompt_parts.append("- Использовать класс Test{test_class_name}")
        prompt_parts.append("- Применить Page Object Model")
        prompt_parts.append("- Добавить подробные комментарии")
        prompt_parts.append("- Использовать фикстуры pytest")
        prompt_parts.append("- Включить валидации через expect()")
        
        if options.test_style:
            if options.test_style.docstring_style == "google":
                prompt_parts.append("- Использовать Google-style docstrings")
            if options.test_style.include_type_hints:
                prompt_parts.append("- Добавить type hints")
        
        # Формат ответа
        prompt_parts.append("\nВерни только Python код теста без дополнительных объяснений.")
        prompt_parts.append("Код должен быть готов к использованию и следовать всем требованиям выше.")
        
        return "\n".join(prompt_parts)
    
    def build_page_object_prompt(
        self,
        page_name: str,
        elements: Dict[str, str],
        actions: Dict[str, Any],
        options: GenerationOptions
    ) -> str:
        """
        Построение промпта для генерации Page Object.
        
        Args:
            page_name: Название страницы.
            elements: Словарь элементов (имя -> селектор).
            actions: Словарь действий.
            options: Опции генерации.
        
        Returns:
            str: Промпт для LLM.
        """
        prompt_parts = []
        
        prompt_parts.append(f"Сгенерируй Page Object класс для страницы: {page_name}\n")
        
        # Элементы страницы
        prompt_parts.append("Элементы страницы:")
        for element_name, selector in elements.items():
            prompt_parts.append(f"  - {element_name}: {selector}")
        
        # Действия на странице
        if actions:
            prompt_parts.append("\nДействия на странице:")
            for action_name, action_info in actions.items():
                prompt_parts.append(f"  - {action_name}: {action_info}")
        
        # Требования
        prompt_parts.append("\nТребования:")
        prompt_parts.append("- Наследоваться от BasePage")
        prompt_parts.append("- Инкапсулировать все локаторы")
        prompt_parts.append("- Создать методы для всех действий")
        prompt_parts.append("- Добавить методы валидации")
        prompt_parts.append("- Использовать приватные атрибуты для локаторов (с префиксом _)")
        
        prompt_parts.append("\nВерни только Python код класса без дополнительных объяснений.")
        
        return "\n".join(prompt_parts)
    
    def _build_context_text(self) -> str:
        """Построение текста контекста для промпта."""
        if not self.context:
            return ""
        
        context_parts = []
        
        # Исходный код
        if self.context.source_code:
            context_parts.append("Исходный код приложения:")
            for file_path, content in list(self.context.source_code.items())[:5]:  # Ограничение
                context_parts.append(f"\nФайл: {file_path}")
                context_parts.append(content[:500] + "..." if len(content) > 500 else content)
        
        # API контракты
        if self.context.api_contracts:
            context_parts.append("\nAPI контракты:")
            for contract in self.context.api_contracts[:3]:  # Ограничение
                context_parts.append(f"  {contract.method} {contract.endpoint}")
        
        # Требования
        if self.context.requirements:
            context_parts.append("\nТребования:")
            for req in self.context.requirements[:5]:  # Ограничение
                context_parts.append(f"  - {req}")
        
        return "\n".join(context_parts)
    
    def add_context(self, context: GenerationContext) -> "PromptBuilder":
        """Добавление контекста в промпт."""
        self.context = context
        return self


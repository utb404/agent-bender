"""Step generator for converting descriptive steps to structured steps."""

from typing import List, Dict, Any, Optional
import logging
import json
import re

from agentbender.models.test_case import TestCase, TestStep
from agentbender.models.config import GenerationOptions
from agentbender.providers.base_provider import BaseLLMProvider
from agentbender.utils.formatter import CodeFormatter


logger = logging.getLogger(__name__)


class StepGenerator:
    """Генератор структурированных шагов из описаний действий."""
    
    SYSTEM_PROMPT = """Ты — эксперт по автоматизации тестирования веб-приложений.
Твоя задача — преобразовать описание действия на естественном языке в структурированный шаг теста.

Структурированный шаг должен содержать:
- action: тип действия (navigate, fill, click, verify, select, wait, download, upload и т.д.)
- target: селектор элемента или URL (если применимо)
- value: значение для действия (текст для fill, опция для select и т.д.)

Типы действий:
- navigate: переход на URL или страницу
- fill: заполнение поля ввода
- click: клик по элементу
- verify: проверка состояния элемента или страницы
- select: выбор опции в выпадающем списке
- wait: ожидание элемента или события
- download: скачивание файла
- upload: загрузка файла
- scroll: прокрутка страницы
- hover: наведение на элемент
- double_click: двойной клик
- right_click: правый клик

Для селекторов используй приоритет:
1. data-testid (если есть)
2. id
3. name
4. role и aria-label
5. CSS селекторы (классы, теги)
6. XPath (только если другие не подходят)

Верни результат в формате JSON с полями: action, target (если применимо), value (если применимо).
"""
    
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        formatter: Optional[CodeFormatter] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация генератора шагов.
        
        Args:
            llm_provider: Провайдер LLM.
            formatter: Форматтер кода.
            logger: Логгер.
        """
        self.llm_provider = llm_provider
        self.formatter = formatter or CodeFormatter()
        self.logger = logger or logging.getLogger(__name__)
    
    def generate_structured_steps(
        self,
        test_case: TestCase,
        options: Optional[GenerationOptions] = None
    ) -> List[TestStep]:
        """
        Генерация структурированных шагов из описательных.
        
        Args:
            test_case: Тест-кейс с описательными шагами.
            options: Опции генерации.
        
        Returns:
            List[TestStep]: Список структурированных шагов.
        """
        options = options or GenerationOptions()
        
        structured_steps = []
        
        for step in test_case.steps:
            # Преобразуем описательный шаг в структурированный через LLM
            try:
                structured_step = self._convert_descriptive_to_structured(
                    step=step,
                    test_case=test_case,
                    options=options
                )
                structured_steps.append(structured_step)
            except Exception as e:
                self.logger.warning(
                    f"Ошибка при преобразовании шага {step.step_number}: {e}. "
                    f"Используется fallback преобразование."
                )
                # Создаем структурированный шаг с базовым action на основе описания
                structured_step = self._fallback_convert(step)
                structured_steps.append(structured_step)
        
        return structured_steps
    
    def _convert_descriptive_to_structured(
        self,
        step: TestStep,
        test_case: TestCase,
        options: GenerationOptions
    ) -> TestStep:
        """
        Преобразование описательного шага в структурированный через LLM.
        
        Args:
            step: Описательный шаг.
            test_case: Тест-кейс (для контекста).
            options: Опции генерации.
        
        Returns:
            TestStep: Структурированный шаг.
        """
        # Построение промпта
        prompt = self._build_step_conversion_prompt(step, test_case)
        
        # Генерация через LLM
        try:
            response = self.llm_provider.generate(
                prompt=prompt,
                system_prompt=self.SYSTEM_PROMPT,
                temperature=options.temperature or 0.3,  # Низкая температура для более точных результатов
                max_tokens=options.max_tokens or 500
            )
            
            # Парсинг ответа
            structured_data = self._parse_llm_response(response.content)
            
            # Создание структурированного шага с добавлением action/target/value
            structured_step = TestStep(
                step_number=step.step_number,
                id=step.id,
                name=step.name,
                description=step.description,
                expectedResult=step.expectedResult or structured_data.get("expectedResult"),
                action=structured_data.get("action"),
                target=structured_data.get("target"),
                value=structured_data.get("value"),
                status=step.status,
                bugLink=step.bugLink,
                skipReason=step.skipReason,
                attachments=step.attachments
            )
            
            return structured_step
        
        except Exception as e:
            self.logger.error(f"Ошибка при преобразовании шага через LLM: {e}")
            raise
    
    def _build_step_conversion_prompt(
        self,
        step: TestStep,
        test_case: TestCase
    ) -> str:
        """
        Построение промпта для преобразования шага.
        
        Args:
            step: Описательный шаг.
            test_case: Тест-кейс (для контекста).
        
        Returns:
            str: Промпт для LLM.
        """
        prompt_parts = []
        
        prompt_parts.append("Преобразуй следующее описание действия в структурированный шаг теста:\n")
        prompt_parts.append(f"Тест-кейс: {test_case.display_title}")
        prompt_parts.append(f"Описание тест-кейса: {test_case.description}\n")
        
        prompt_parts.append(f"Шаг {step.step_number}:")
        if step.name:
            prompt_parts.append(f"Название: {step.name}")
        prompt_parts.append(f"Описание: {step.description}")
        if step.expectedResult:
            prompt_parts.append(f"Ожидаемый результат: {step.expectedResult}")
        
        prompt_parts.append("\nВерни JSON с полями:")
        prompt_parts.append("- action: тип действия (navigate, fill, click, verify и т.д.)")
        prompt_parts.append("- target: селектор элемента или URL (если применимо)")
        prompt_parts.append("- value: значение для действия (если применимо)")
        prompt_parts.append("\nПример ответа:")
        prompt_parts.append('{"action": "click", "target": "button[data-testid=\\"download-btn\\"]", "value": null}')
        
        return "\n".join(prompt_parts)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Парсинг ответа LLM в структурированные данные.
        
        Args:
            response: Ответ от LLM.
        
        Returns:
            Dict: Структурированные данные шага.
        """
        # Попытка извлечь JSON из ответа
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Попытка найти JSON блок в markdown
        code_block_pattern = r"```(?:json)?\n?(\{.*?\})\n?```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # Попытка парсинга всего ответа как JSON
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
        
        # Fallback: извлечение данных через регулярные выражения
        result = {}
        
        # Поиск action
        action_match = re.search(r'"action"\s*:\s*"([^"]+)"', response)
        if action_match:
            result["action"] = action_match.group(1)
        
        # Поиск target
        target_match = re.search(r'"target"\s*:\s*"([^"]+)"', response)
        if target_match:
            result["target"] = target_match.group(1)
        
        # Поиск value
        value_match = re.search(r'"value"\s*:\s*(?:"([^"]+)"|null)', response)
        if value_match:
            result["value"] = value_match.group(1) if value_match.group(1) else None
        
        return result
    
    def _fallback_convert(self, step: TestStep) -> TestStep:
        """
        Резервное преобразование шага на основе простых правил.
        
        Args:
            step: Описательный шаг.
        
        Returns:
            TestStep: Структурированный шаг с базовым action.
        """
        description_lower = step.description.lower()
        
        # Определение action на основе ключевых слов
        action = None
        target = None
        value = None
        
        if any(word in description_lower for word in ["зайти", "открыть", "перейти", "навигация"]):
            action = "navigate"
            # Попытка извлечь URL из описания
            url_match = re.search(r'https?://[^\s]+', step.description)
            if url_match:
                target = "url"
                value = url_match.group(0)
        elif any(word in description_lower for word in ["скачать", "загрузить", "download"]):
            action = "download"
        elif any(word in description_lower for word in ["ввести", "заполнить", "fill"]):
            action = "fill"
        elif any(word in description_lower for word in ["нажать", "клик", "click"]):
            action = "click"
        elif any(word in description_lower for word in ["проверить", "verify", "ожидать"]):
            action = "verify"
        elif any(word in description_lower for word in ["выбрать", "select"]):
            action = "select"
        else:
            # По умолчанию - действие на основе описания
            action = "execute"
        
        return TestStep(
            step_number=step.step_number,
            id=step.id,
            name=step.name,
            description=step.description,
            expectedResult=step.expectedResult,
            action=action,
            target=target,
            value=value,
            status=step.status,
            bugLink=step.bugLink,
            skipReason=step.skipReason,
            attachments=step.attachments
        )


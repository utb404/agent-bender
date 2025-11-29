"""Parser for test cases."""

import json
from pathlib import Path
from typing import Union, Dict, Any, Optional
import logging

from agentbender.models.test_case import TestCase, TestStep
from agentbender.models.results import ValidationReport, ValidationError, ValidationWarning


logger = logging.getLogger(__name__)


class TestCaseParser:
    """Парсер тест-кейсов из различных форматов."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Инициализация парсера.
        
        Args:
            logger: Логгер для записи операций.
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def parse(
        self,
        test_case: Union[TestCase, Dict[str, Any], str, Path]
    ) -> TestCase:
        """
        Парсинг тест-кейса из различных форматов.
        
        Args:
            test_case: Тест-кейс в виде объекта TestCase, словаря, JSON-строки или пути к файлу.
        
        Returns:
            TestCase: Распарсенный тест-кейс.
        
        Raises:
            ValidationError: При некорректном формате тест-кейса.
            FileNotFoundError: Если файл не найден.
        """
        if isinstance(test_case, TestCase):
            return test_case
        
        if isinstance(test_case, (str, Path)):
            path = Path(test_case)
            if path.exists():
                return self.parse_from_file(path)
            else:
                # Попытка парсинга как JSON строки
                try:
                    data = json.loads(test_case)
                    return self._parse_from_dict(data)
                except json.JSONDecodeError as e:
                    from agentbender.models.results import ValidationError
                    raise ValidationError(
                        code="INVALID_JSON",
                        message=f"Некорректный JSON: {e}",
                        severity="error"
                    )
        
        if isinstance(test_case, dict):
            return self._parse_from_dict(test_case)
        
        from agentbender.models.results import ValidationError
        raise ValidationError(
            code="UNSUPPORTED_FORMAT",
            message=f"Неподдерживаемый формат: {type(test_case)}",
            severity="error"
        )
    
    def parse_from_file(self, file_path: Union[str, Path]) -> TestCase:
        """
        Парсинг тест-кейса из JSON файла.
        
        Args:
            file_path: Путь к JSON файлу.
        
        Returns:
            TestCase: Распарсенный тест-кейс.
        
        Raises:
            FileNotFoundError: Если файл не найден.
            ValidationError: При некорректном формате файла.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")
        
        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
            return self._parse_from_dict(data)
        except json.JSONDecodeError as e:
            from agentbender.models.results import ValidationError
            raise ValidationError(
                code="INVALID_JSON",
                message=f"Некорректный JSON в файле {path}: {e}",
                severity="error"
            )
        except Exception as e:
            from agentbender.models.results import ValidationError
            raise ValidationError(
                code="PARSE_ERROR",
                message=f"Ошибка при парсинге файла {path}: {e}",
                severity="error"
            )
    
    def _parse_from_dict(self, data: Dict[str, Any]) -> TestCase:
        """
        Парсинг тест-кейса из словаря.
        
        Args:
            data: Словарь с данными тест-кейса.
        
        Returns:
            TestCase: Распарсенный тест-кейс.
        
        Raises:
            ValidationError: При некорректном формате данных.
        """
        # Поддержка вложенной структуры с ключом "test_case"
        if "test_case" in data:
            data = data["test_case"]
        
        # Валидация обязательных полей
        required_fields = ["id", "title", "description", "steps", "expected_result"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            from agentbender.models.results import ValidationError
            raise ValidationError(
                code="MISSING_FIELDS",
                message=f"Отсутствуют обязательные поля: {', '.join(missing_fields)}",
                severity="error"
            )
        
        # Парсинг шагов
        steps = []
        if isinstance(data["steps"], list):
            for i, step_data in enumerate(data["steps"]):
                try:
                    step = TestStep(**step_data)
                    if step.step_number is None:
                        step.step_number = i + 1
                    steps.append(step)
                except Exception as e:
                    self.logger.warning(f"Ошибка при парсинге шага {i+1}: {e}")
                    # Продолжаем парсинг остальных шагов
        else:
            from agentbender.models.results import ValidationError
            raise ValidationError(
                code="INVALID_STEPS",
                message="Поле 'steps' должно быть списком",
                field="steps",
                severity="error"
            )
        
        if not steps:
            from agentbender.models.results import ValidationError
            raise ValidationError(
                code="EMPTY_STEPS",
                message="Тест-кейс должен содержать хотя бы один шаг",
                field="steps",
                severity="error"
            )
        
        # Создание объекта TestCase
        try:
            test_case = TestCase(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                steps=steps,
                expected_result=data["expected_result"],
                preconditions=data.get("preconditions"),
                tags=data.get("tags"),
                priority=data.get("priority"),
            )
            return test_case
        except Exception as e:
            from agentbender.models.results import ValidationError
            raise ValidationError(
                code="CREATE_ERROR",
                message=f"Ошибка при создании объекта TestCase: {e}",
                severity="error"
            )
    
    def validate(self, test_case: TestCase) -> ValidationReport:
        """
        Валидация тест-кейса.
        
        Args:
            test_case: Тест-кейс для валидации.
        
        Returns:
            ValidationReport: Отчет о валидации.
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Проверка обязательных полей
        if not test_case.id:
            errors.append(ValidationError(
                code="EMPTY_ID",
                message="ID тест-кейса не может быть пустым",
                field="id",
                severity="error"
            ))
        
        if not test_case.title:
            errors.append(ValidationError(
                code="EMPTY_TITLE",
                message="Название тест-кейса не может быть пустым",
                field="title",
                severity="error"
            ))
        
        if not test_case.steps:
            errors.append(ValidationError(
                code="NO_STEPS",
                message="Тест-кейс должен содержать хотя бы один шаг",
                field="steps",
                severity="error"
            ))
        
        # Проверка шагов
        for i, step in enumerate(test_case.steps):
            if not step.action:
                errors.append(ValidationError(
                    code="EMPTY_ACTION",
                    message=f"Шаг {i+1} не содержит действия",
                    field=f"steps[{i}].action",
                    severity="error"
                ))
            
            if not step.description:
                warnings.append(ValidationWarning(
                    code="MISSING_DESCRIPTION",
                    message=f"Шаг {i+1} не содержит описания",
                    field=f"steps[{i}].description",
                    suggestion="Добавьте описание шага для лучшего понимания"
                ))
        
        # Проверка ожидаемого результата
        if not test_case.expected_result:
            warnings.append(ValidationWarning(
                code="MISSING_EXPECTED_RESULT",
                message="Отсутствует ожидаемый результат",
                field="expected_result",
                suggestion="Добавьте описание ожидаемого результата"
            ))
        
        # Предложения по улучшению
        if not test_case.tags:
            suggestions.append("Добавьте теги для лучшей организации тестов")
        
        if not test_case.priority:
            suggestions.append("Укажите приоритет тест-кейса")
        
        is_valid = len(errors) == 0
        
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )


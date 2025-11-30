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
        
        Поддерживает два формата:
        1. Структурированный: с явными action/target/value в шагах
        2. Описательный: с описаниями действий на естественном языке
        
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
        if "id" not in data:
            from agentbender.models.results import ValidationError
            raise ValidationError(
                code="MISSING_ID",
                message="Отсутствует обязательное поле 'id'",
                severity="error"
            )
        
        if "steps" not in data:
            from agentbender.models.results import ValidationError
            raise ValidationError(
                code="MISSING_STEPS",
                message="Отсутствует обязательное поле 'steps'",
                severity="error"
            )
        
        # Парсинг шагов
        steps = []
        if isinstance(data["steps"], list):
            for i, step_data in enumerate(data["steps"]):
                try:
                    # Нормализация данных шага (удаляет action/target/value из входного JSON)
                    normalized_step = self._normalize_step_data(step_data, i + 1)
                    # Создаем TestStep без полей action/target/value (они будут заполнены StepGenerator)
                    # Важно: исключаем action/target/value из словаря перед созданием TestStep
                    step_dict = {k: v for k, v in normalized_step.items() 
                                if k not in ["action", "target", "value"]}
                    # Создаем TestStep с явно указанными None для action/target/value
                    # (они должны заполняться только StepGenerator, а не из входного JSON)
                    # ВАЖНО: всегда устанавливаем action/target/value в None, даже если они были в исходных данных
                    step_dict_with_none = dict(step_dict)  # Создаем новый словарь
                    step_dict_with_none["action"] = None
                    step_dict_with_none["target"] = None
                    step_dict_with_none["value"] = None
                    # Убеждаемся, что исходные данные не попали в словарь
                    assert "action" not in step_dict or step_dict["action"] is None
                    step = TestStep.model_validate(step_dict_with_none, strict=False)
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
        
        # Нормализация данных тест-кейса
        normalized_data = self._normalize_test_case_data(data)
        
        # Создание объекта TestCase
        try:
            test_case = TestCase(**normalized_data)
            return test_case
        except Exception as e:
            error = ValidationError(
                code="CREATE_ERROR",
                message=f"Ошибка при создании объекта TestCase: {e}",
                severity="error"
            )
            raise ValueError(f"{error.code}: {error.message}") from e
    
    def _normalize_step_data(self, step_data: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """
        Нормализация данных шага для формата test_case.json.
        
        Args:
            step_data: Исходные данные шага.
            step_number: Номер шага.
        
        Returns:
            Dict: Нормализованные данные шага.
        """
        normalized = step_data.copy()
        
        # Установка номера шага, если не указан
        if "step_number" not in normalized and "id" in normalized:
            try:
                normalized["step_number"] = int(normalized["id"])
            except (ValueError, TypeError):
                normalized["step_number"] = step_number
        elif "step_number" not in normalized:
            normalized["step_number"] = step_number
        
        # Если нет description, но есть name - используем name как description
        if "description" not in normalized and "name" in normalized:
            normalized["description"] = normalized["name"]
        
        # Удаляем поля структурированного формата, если они присутствуют
        # (они не используются в описательном формате)
        normalized.pop("action", None)
        normalized.pop("target", None)
        normalized.pop("value", None)
        
        return normalized
    
    def _normalize_test_case_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Нормализация данных тест-кейса для поддержки разных форматов.
        
        Args:
            data: Исходные данные тест-кейса.
        
        Returns:
            Dict: Нормализованные данные тест-кейса.
        """
        normalized = data.copy()
        
        # Нормализация названия
        if "title" not in normalized and "name" in normalized:
            normalized["title"] = normalized["name"]
        elif "title" not in normalized:
            normalized["title"] = normalized.get("id", "Untitled")
        
        # Нормализация описания
        if "description" not in normalized:
            normalized["description"] = normalized.get("name", "")
        
        # Нормализация ожидаемого результата
        if "expected_result" not in normalized and "expectedResult" in normalized:
            normalized["expected_result"] = normalized["expectedResult"]
        elif "expected_result" not in normalized:
            normalized["expected_result"] = ""
        
        # Нормализация предусловий
        if "preconditions" in normalized:
            if isinstance(normalized["preconditions"], str):
                if normalized["preconditions"].strip():
                    normalized["preconditions"] = [
                        p.strip() for p in normalized["preconditions"].split("\n") if p.strip()
                    ]
                else:
                    normalized["preconditions"] = None
        elif "preconditions_text" in normalized:
            preconditions_text = normalized["preconditions_text"]
            if preconditions_text and isinstance(preconditions_text, str) and preconditions_text.strip():
                normalized["preconditions"] = [
                    p.strip() for p in preconditions_text.split("\n") if p.strip()
                ]
        
        # Нормализация тегов
        if "tags" in normalized:
            if isinstance(normalized["tags"], str):
                if normalized["tags"].strip():
                    normalized["tags"] = [t.strip() for t in normalized["tags"].split(",") if t.strip()]
                else:
                    normalized["tags"] = None
        elif "tags_text" in normalized:
            tags_text = normalized["tags_text"]
            if tags_text and isinstance(tags_text, str) and tags_text.strip():
                normalized["tags"] = [t.strip() for t in tags_text.split(",") if t.strip()]
        
        # Нормализация ID
        if "testCaseId" in normalized and "id" not in normalized:
            normalized["id"] = normalized["testCaseId"]
        
        return normalized
    
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
            if not step.description:
                errors.append(ValidationError(
                    code="EMPTY_DESCRIPTION",
                    message=f"Шаг {i+1} не содержит описания",
                    field=f"steps[{i}].description",
                    severity="error"
                ))
        
        # Проверка ожидаемого результата
        if not test_case.display_expected_result:
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


"""Code validator for generated tests."""

import ast
import re
from typing import List, Optional
import logging

from agentbender.models.test_case import TestCase
from agentbender.models.results import ValidationReport, ValidationError, ValidationWarning


logger = logging.getLogger(__name__)


class CodeValidator:
    """Валидатор сгенерированного кода."""
    
    def __init__(
        self,
        validation_level: str = "basic",
        logger: Optional[logging.Logger] = None
    ):
        """
        Инициализация валидатора.
        
        Args:
            validation_level: Уровень валидации ("basic", "strict", "none").
            logger: Логгер для записи операций.
        """
        self.validation_level = validation_level
        self.logger = logger or logging.getLogger(__name__)
    
    def validate(
        self,
        code: str,
        test_case: Optional[TestCase] = None
    ) -> ValidationReport:
        """
        Валидация кода теста.
        
        Args:
            code: Код для валидации.
            test_case: Исходный тест-кейс (для сравнения).
        
        Returns:
            ValidationReport: Отчет о валидации.
        """
        if self.validation_level == "none":
            return ValidationReport(is_valid=True)
        
        errors = []
        warnings = []
        
        # Валидация синтаксиса
        syntax_errors = self.validate_syntax(code)
        errors.extend(syntax_errors)
        
        if self.validation_level in ["basic", "strict"]:
            # Валидация структуры
            structure_errors = self.validate_structure(code)
            errors.extend(structure_errors)
            
            # Валидация использования Playwright
            playwright_errors = self.validate_playwright_usage(code)
            errors.extend(playwright_errors)
            
            # Валидация паттерна Page Object
            po_warnings = self.validate_page_object_pattern(code)
            warnings.extend(po_warnings)
        
        if self.validation_level == "strict" and test_case:
            # Проверка покрытия тест-кейса
            coverage_warnings = self.validate_test_coverage(code, test_case)
            warnings.extend(coverage_warnings)
        
        is_valid = len(errors) == 0
        
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def validate_syntax(self, code: str) -> List[ValidationError]:
        """Валидация синтаксиса Python."""
        errors = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(ValidationError(
                code="SYNTAX_ERROR",
                message=f"Синтаксическая ошибка: {e.msg}",
                field=f"line_{e.lineno}",
                severity="error",
                suggestion=f"Исправьте синтаксическую ошибку на строке {e.lineno}"
            ))
        except Exception as e:
            errors.append(ValidationError(
                code="PARSE_ERROR",
                message=f"Ошибка при парсинге кода: {e}",
                severity="error"
            ))
        
        return errors
    
    def validate_structure(self, code: str) -> List[ValidationError]:
        """Валидация структуры теста."""
        errors = []
        
        try:
            tree = ast.parse(code)
            
            # Проверка наличия импортов pytest и playwright
            has_pytest = False
            has_playwright = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "pytest":
                            has_pytest = True
                        if alias.name == "playwright":
                            has_playwright = True
                elif isinstance(node, ast.ImportFrom):
                    if node.module == "pytest":
                        has_pytest = True
                    if node.module == "playwright":
                        has_playwright = True
            
            if not has_pytest:
                errors.append(ValidationError(
                    code="MISSING_PYTEST",
                    message="Отсутствует импорт pytest",
                    severity="error",
                    suggestion="Добавьте: import pytest"
                ))
            
            if not has_playwright:
                errors.append(ValidationError(
                    code="MISSING_PLAYWRIGHT",
                    message="Отсутствует импорт playwright",
                    severity="error",
                    suggestion="Добавьте: from playwright.sync_api import Page, expect"
                ))
            
            # Проверка наличия тестовых функций или классов
            has_test_function = False
            has_test_class = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith("test_"):
                        has_test_function = True
                elif isinstance(node, ast.ClassDef):
                    if node.name.startswith("Test"):
                        has_test_class = True
            
            if not has_test_function and not has_test_class:
                errors.append(ValidationError(
                    code="NO_TEST_FUNCTIONS",
                    message="Отсутствуют тестовые функции или классы",
                    severity="error",
                    suggestion="Добавьте функции, начинающиеся с 'test_' или классы, начинающиеся с 'Test'"
                ))
        
        except Exception as e:
            self.logger.warning(f"Ошибка при валидации структуры: {e}")
        
        return errors
    
    def validate_playwright_usage(self, code: str) -> List[ValidationError]:
        """Валидация использования Playwright."""
        errors = []
        
        # Проверка наличия основных методов Playwright
        playwright_patterns = [
            (r"page\.goto", "Использование page.goto()"),
            (r"page\.locator", "Использование page.locator()"),
            (r"expect\(", "Использование expect() для проверок"),
        ]
        
        found_patterns = []
        for pattern, description in playwright_patterns:
            if re.search(pattern, code):
                found_patterns.append(description)
        
        if not found_patterns:
            errors.append(ValidationError(
                code="NO_PLAYWRIGHT_USAGE",
                message="Код не использует основные методы Playwright",
                severity="error",
                suggestion="Используйте методы page.goto(), page.locator() и expect()"
            ))
        
        return errors
    
    def validate_page_object_pattern(self, code: str) -> List[ValidationWarning]:
        """Валидация соответствия паттерну Page Object."""
        warnings = []
        
        # Проверка наличия импортов Page Objects
        has_page_object_import = re.search(r"from\s+pages\.\w+\s+import", code)
        
        if not has_page_object_import:
            warnings.append(ValidationWarning(
                code="NO_PAGE_OBJECT",
                message="Код не использует паттерн Page Object Model",
                suggestion="Рассмотрите возможность использования Page Objects для лучшей организации кода"
            ))
        
        # Проверка прямого использования селекторов в тестах
        direct_selectors = re.findall(r'page\.locator\(["\'].*["\']\)', code)
        if len(direct_selectors) > 3:
            warnings.append(ValidationWarning(
                code="TOO_MANY_DIRECT_SELECTORS",
                message="Слишком много прямых селекторов в тесте",
                suggestion="Вынесите селекторы в Page Object классы"
            ))
        
        return warnings
    
    def validate_test_coverage(
        self,
        code: str,
        test_case: TestCase
    ) -> List[ValidationWarning]:
        """Проверка покрытия тест-кейса."""
        warnings = []
        
        # Простая проверка: есть ли в коде упоминания шагов из тест-кейса
        step_keywords = []
        for step in test_case.steps:
            # Извлечение ключевых слов из описания шага
            keywords = step.description.lower().split()[:3]  # Первые 3 слова
            step_keywords.extend(keywords)
        
        # Проверка наличия ключевых слов в коде
        code_lower = code.lower()
        found_keywords = [kw for kw in step_keywords if kw in code_lower]
        
        if len(found_keywords) < len(step_keywords) * 0.5:
            warnings.append(ValidationWarning(
                code="LOW_COVERAGE",
                message="Низкое покрытие шагов тест-кейса в коде",
                suggestion="Убедитесь, что все шаги тест-кейса реализованы в коде"
            ))
        
        return warnings


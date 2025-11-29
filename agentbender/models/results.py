"""Models for generation results."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from pathlib import Path
import uuid

from agentbender.models.test_case import TestCase
from agentbender.providers.base_provider import LLMResponse


@dataclass
class ValidationError:
    """Ошибка валидации."""
    
    code: str
    message: str
    field: Optional[str] = None
    severity: Literal["error", "critical"] = "error"
    suggestion: Optional[str] = None


@dataclass
class ValidationWarning:
    """Предупреждение валидации."""
    
    code: str
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Отчет о валидации тест-кейса или сгенерированного кода."""
    
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def has_errors(self) -> bool:
        """Проверка наличия ошибок."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Проверка наличия предупреждений."""
        return len(self.warnings) > 0


@dataclass
class QualityMetrics:
    """Метрики качества сгенерированного кода."""
    
    # Метрики кода
    code_complexity: float
    test_coverage_estimate: float
    maintainability_index: float
    
    # Метрики соответствия стандартам
    style_compliance: float
    pattern_compliance: float
    
    # Метрики LLM
    confidence_score: Optional[float] = None
    generation_quality: Optional[float] = None


@dataclass
class GenerationResult:
    """Результат генерации тестов."""
    
    # Исходный тест-кейс (обязательные поля без значений по умолчанию)
    test_case: TestCase
    
    # Сгенерированный код
    test_code: str  # Код теста
    
    # Идентификатор генерации
    generation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page_objects: Dict[str, str] = field(default_factory=dict)  # Ключ - имя класса, значение - код
    fixtures: Optional[str] = None  # Код фикстур
    helpers: Optional[str] = None  # Код вспомогательных утилит
    config_files: Dict[str, str] = field(default_factory=dict)  # conftest.py, pytest.ini и т.д.
    
    # Метаданные
    generated_at: datetime = field(default_factory=datetime.now)
    generation_time: float = 0.0  # Время генерации в секундах
    model_used: str = ""
    tokens_used: Optional[int] = None
    
    # Отчеты
    validation_report: Optional[ValidationReport] = None
    quality_metrics: Optional[QualityMetrics] = None
    
    # Сырые ответы LLM (опционально)
    raw_llm_responses: Optional[List[LLMResponse]] = None
    
    # Ошибки и предупреждения
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Статус
    status: Literal["success", "partial", "failed"] = "success"
    
    def save_to_directory(self, directory: Path) -> Path:
        """Сохранение результатов в директорию."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        # Сохранение тестового кода
        tests_dir = directory / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / f"test_{self.test_case.id.lower().replace('-', '_')}.py"
        test_file.write_text(self.test_code, encoding="utf-8")
        
        # Сохранение Page Objects
        if self.page_objects:
            pages_dir = directory / "pages"
            pages_dir.mkdir(exist_ok=True)
            (pages_dir / "__init__.py").touch()
            
            for class_name, code in self.page_objects.items():
                page_file = pages_dir / f"{class_name.lower().replace('page', '')}_page.py"
                page_file.write_text(code, encoding="utf-8")
        
        # Сохранение фикстур
        if self.fixtures:
            conftest_file = directory / "conftest.py"
            conftest_file.write_text(self.fixtures, encoding="utf-8")
        
        # Сохранение вспомогательных утилит
        if self.helpers:
            utils_dir = directory / "utils"
            utils_dir.mkdir(exist_ok=True)
            (utils_dir / "__init__.py").touch()
            helpers_file = utils_dir / "helpers.py"
            helpers_file.write_text(self.helpers, encoding="utf-8")
        
        # Сохранение конфигурационных файлов
        for filename, content in self.config_files.items():
            config_file = directory / filename
            config_file.write_text(content, encoding="utf-8")
        
        return directory
    
    def get_file_structure(self) -> Dict[str, str]:
        """Получение структуры файлов для сохранения."""
        structure = {
            f"tests/test_{self.test_case.id.lower().replace('-', '_')}.py": self.test_code,
        }
        
        if self.page_objects:
            for class_name, code in self.page_objects.items():
                structure[f"pages/{class_name.lower().replace('page', '')}_page.py"] = code
        
        if self.fixtures:
            structure["conftest.py"] = self.fixtures
        
        if self.helpers:
            structure["utils/helpers.py"] = self.helpers
        
        structure.update(self.config_files)
        
        return structure
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация результата в словарь."""
        return {
            "generation_id": self.generation_id,
            "test_case": {
                "id": self.test_case.id,
                "title": self.test_case.title,
                "description": self.test_case.description,
            },
            "status": self.status,
            "generated_at": self.generated_at.isoformat(),
            "generation_time": self.generation_time,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "warnings": self.warnings,
            "errors": self.errors,
            "validation_report": {
                "is_valid": self.validation_report.is_valid if self.validation_report else None,
                "errors_count": len(self.validation_report.errors) if self.validation_report else 0,
                "warnings_count": len(self.validation_report.warnings) if self.validation_report else 0,
            } if self.validation_report else None,
            "quality_metrics": {
                "code_complexity": self.quality_metrics.code_complexity,
                "test_coverage_estimate": self.quality_metrics.test_coverage_estimate,
                "maintainability_index": self.quality_metrics.maintainability_index,
                "style_compliance": self.quality_metrics.style_compliance,
                "pattern_compliance": self.quality_metrics.pattern_compliance,
                "confidence_score": self.quality_metrics.confidence_score,
                "generation_quality": self.quality_metrics.generation_quality,
            } if self.quality_metrics else None,
        }


@dataclass
class GenerationStatus:
    """Статус асинхронной генерации."""
    
    generation_id: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    progress: float = 0.0  # 0.0 - 1.0
    message: Optional[str] = None
    result: Optional[GenerationResult] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация статуса в словарь."""
        return {
            "generation_id": self.generation_id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


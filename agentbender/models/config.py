"""Configuration models for AgentBender."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
from enum import Enum
import yaml


@dataclass
class LLMConfig:
    """Конфигурация LLM провайдера."""
    
    provider: Literal["ollama", "openai", "anthropic"] = "ollama"
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    
    # Настройки для Ollama
    ollama_api_key: Optional[str] = None
    
    # Настройки для других провайдеров
    api_key: Optional[str] = None
    
    # Настройки логирования запросов
    log_requests: bool = True
    log_responses: bool = False
    trace_requests: bool = False


@dataclass
class ValidationConfig:
    """Конфигурация валидации."""
    
    level: Literal["basic", "strict", "none"] = "basic"
    validate_syntax: bool = True
    validate_structure: bool = True
    validate_playwright_usage: bool = True
    validate_page_object_pattern: bool = True
    validate_test_coverage: bool = True


@dataclass
class PerformanceConfig:
    """Конфигурация производительности."""
    
    max_workers: int = 4
    enable_async: bool = True
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 час
    batch_prompts: bool = True
    prompt_compression: bool = False
    max_prompt_length: int = 8000
    max_response_length: int = 4000


@dataclass
class LoggingConfig:
    """Конфигурация логирования."""
    
    level: str = "INFO"
    format: str = "json"
    file: Optional[Path] = None
    enable_tracing: bool = False


@dataclass
class GPNQAUtilsConfig:
    """Конфигурация интеграции с gpn_qa_utils."""
    
    enabled: bool = True
    import_path: str = "from gpn_qa_utils import helpers"


@dataclass
class PlaywrightConfig:
    """Конфигурация Playwright."""
    
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = True
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080


@dataclass
class GenerationConfig:
    """Конфигурация генератора тестов."""
    
    # LLM настройки
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Настройки генерации
    output_dir: Path = field(default_factory=lambda: Path("./generated_tests"))
    template_dir: Optional[Path] = None
    code_style: Literal["black", "autopep8", "none"] = "black"
    use_cdp: bool = False
    
    # Настройки валидации
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    
    # Настройки производительности
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Настройки логирования
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Интеграция с gpn_qa_utils
    gpn_qa_utils: GPNQAUtilsConfig = field(default_factory=GPNQAUtilsConfig)
    
    # Playwright настройки
    playwright: PlaywrightConfig = field(default_factory=PlaywrightConfig)
    
    @classmethod
    def from_yaml(cls, file_path: Path) -> "GenerationConfig":
        """Загрузка конфигурации из YAML файла."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationConfig":
        """Создание конфигурации из словаря."""
        llm_data = data.get("llm", {})
        llm_config = LLMConfig(**llm_data)
        
        validation_data = data.get("validation", {})
        validation_config = ValidationConfig(**validation_data)
        
        performance_data = data.get("performance", {})
        performance_config = PerformanceConfig(**performance_data)
        
        logging_data = data.get("logging", {})
        if "file" in logging_data and logging_data["file"]:
            logging_data["file"] = Path(logging_data["file"])
        logging_config = LoggingConfig(**logging_data)
        
        gpn_qa_utils_data = data.get("gpn_qa_utils", {})
        gpn_qa_utils_config = GPNQAUtilsConfig(**gpn_qa_utils_data)
        
        playwright_data = data.get("playwright", {})
        playwright_config = PlaywrightConfig(**playwright_data)
        
        output_dir = Path(data.get("output_dir", "./generated_tests"))
        template_dir = Path(data.get("template_dir")) if data.get("template_dir") else None
        
        return cls(
            llm=llm_config,
            output_dir=output_dir,
            template_dir=template_dir,
            code_style=data.get("code_style", "black"),
            use_cdp=data.get("use_cdp", False),
            validation=validation_config,
            performance=performance_config,
            logging=logging_config,
            gpn_qa_utils=gpn_qa_utils_config,
            playwright=playwright_config,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация конфигурации в словарь."""
        return {
            "llm": {
                "provider": self.llm.provider,
                "base_url": self.llm.base_url,
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
                "max_retries": self.llm.max_retries,
                "retry_delay": self.llm.retry_delay,
                "retry_backoff": self.llm.retry_backoff,
                "log_requests": self.llm.log_requests,
                "log_responses": self.llm.log_responses,
                "trace_requests": self.llm.trace_requests,
            },
            "output_dir": str(self.output_dir),
            "template_dir": str(self.template_dir) if self.template_dir else None,
            "code_style": self.code_style,
            "use_cdp": self.use_cdp,
            "validation": {
                "level": self.validation.level,
                "validate_syntax": self.validation.validate_syntax,
                "validate_structure": self.validation.validate_structure,
                "validate_playwright_usage": self.validation.validate_playwright_usage,
                "validate_page_object_pattern": self.validation.validate_page_object_pattern,
                "validate_test_coverage": self.validation.validate_test_coverage,
            },
            "performance": {
                "max_workers": self.performance.max_workers,
                "enable_async": self.performance.enable_async,
                "enable_caching": self.performance.enable_caching,
                "cache_ttl": self.performance.cache_ttl,
                "batch_prompts": self.performance.batch_prompts,
                "prompt_compression": self.performance.prompt_compression,
                "max_prompt_length": self.performance.max_prompt_length,
                "max_response_length": self.performance.max_response_length,
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file": str(self.logging.file) if self.logging.file else None,
                "enable_tracing": self.logging.enable_tracing,
            },
            "gpn_qa_utils": {
                "enabled": self.gpn_qa_utils.enabled,
                "import_path": self.gpn_qa_utils.import_path,
            },
            "playwright": {
                "browser": self.playwright.browser,
                "headless": self.playwright.headless,
                "timeout": self.playwright.timeout,
                "viewport_width": self.playwright.viewport_width,
                "viewport_height": self.playwright.viewport_height,
            },
        }


@dataclass
class APIContract:
    """API контракт для контекста генерации."""
    
    endpoint: str
    method: str
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    description: Optional[str] = None


@dataclass
class Specification:
    """Спецификация для контекста генерации."""
    
    title: str
    content: str
    type: Literal["functional", "technical", "ui", "api"] = "functional"
    version: Optional[str] = None


@dataclass
class GenerationContext:
    """
    Контекст для генерации тестов.
    
    Содержит дополнительную информацию, которая может помочь LLM
    сгенерировать более точные и релевантные тесты.
    """
    
    # Исходный код приложения
    source_code: Optional[Dict[str, str]] = None
    # Ключ - путь к файлу, значение - содержимое
    
    # API контракты и спецификации
    api_contracts: Optional[List[APIContract]] = None
    specifications: Optional[List[Specification]] = None
    
    # Требования и документация
    requirements: Optional[List[str]] = None
    documentation: Optional[Dict[str, str]] = None
    
    # Существующие Page Objects (для реиспользования)
    existing_page_objects: Optional[Dict[str, str]] = None
    
    # Дополнительные метаданные
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_directory(
        cls,
        directory: Path,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> "GenerationContext":
        """Создание контекста из директории с исходным кодом."""
        from pathlib import Path
        import fnmatch
        
        directory = Path(directory)
        source_code = {}
        
        include_patterns = include_patterns or ["*.py", "*.ts", "*.js"]
        exclude_patterns = exclude_patterns or ["__pycache__", "*.pyc", "node_modules"]
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Проверка паттернов включения
                if not any(fnmatch.fnmatch(file_path.name, pattern) for pattern in include_patterns):
                    continue
                
                # Проверка паттернов исключения
                if any(fnmatch.fnmatch(str(file_path), pattern) for pattern in exclude_patterns):
                    continue
                
                try:
                    content = file_path.read_text(encoding="utf-8")
                    relative_path = str(file_path.relative_to(directory))
                    source_code[relative_path] = content
                except Exception:
                    continue
        
        return cls(source_code=source_code)
    
    def add_source_file(self, file_path: Path, content: str) -> None:
        """Добавление файла исходного кода в контекст."""
        if self.source_code is None:
            self.source_code = {}
        self.source_code[str(file_path)] = content
    
    def add_api_contract(self, contract: APIContract) -> None:
        """Добавление API контракта."""
        if self.api_contracts is None:
            self.api_contracts = []
        self.api_contracts.append(contract)


@dataclass
class TestStyle:
    """Стиль генерируемых тестов."""
    
    # Структура тестов
    use_classes: bool = True
    use_fixtures: bool = True
    use_helpers: bool = True
    
    # Стиль кода
    docstring_style: Literal["google", "numpy", "sphinx", "none"] = "google"
    comment_style: Literal["detailed", "minimal", "none"] = "detailed"
    
    # Assertions
    assertion_style: Literal["expect", "assert", "both"] = "expect"
    
    # Именование
    naming_convention: Literal["snake_case", "camelCase"] = "snake_case"
    
    # Дополнительные настройки
    include_type_hints: bool = True
    include_logging: bool = True


@dataclass
class GenerationOptions:
    """
    Опции генерации, переопределяющие настройки из конфигурации.
    
    Используется для точечной настройки генерации без изменения
    основной конфигурации.
    """
    
    # Переопределение LLM настроек
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    # Настройки качества
    quality_level: Literal["fast", "balanced", "high"] = "balanced"
    detail_level: Literal["minimal", "standard", "detailed"] = "standard"
    
    # Стиль тестов
    test_style: Optional[TestStyle] = None
    
    # Кастомные шаблоны
    custom_templates: Optional[Dict[str, str]] = None
    
    # Дополнительные настройки
    generate_page_objects: bool = True
    generate_fixtures: bool = True
    generate_helpers: bool = True
    use_cdp: Optional[bool] = None
    
    # Настройки валидации
    skip_validation: bool = False
    validation_level: Literal["basic", "strict", "none"] = "basic"


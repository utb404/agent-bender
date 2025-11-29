# API Design Document: AgentBender

## Документ дизайна API и архитектуры библиотеки AgentBender

**Версия:** 1.0  
**Дата:** 2024  
**Автор:** Senior Python Developer / Lead Test Automation Engineer

---

## Оглавление

1. [Концепция библиотеки](#1-концепция-библиотеки)
2. [Интерфейс и API](#2-интерфейс-и-api)
3. [Интеграция с LLM](#3-интеграция-с-llm)
4. [Генерация и валидация тестов](#4-генерация-и-валидация-тестов)
5. [Нефункциональные требования](#5-нефункциональные-требования)
6. [Примеры использования](#6-примеры-использования)

---

## 1. Концепция библиотеки

### 1.1 Назначение и сценарии использования

**AgentBender** — библиотека для автоматической генерации UI-автотестов на основе тест-кейсов с использованием LLM. Библиотека поддерживает три основных сценария использования:

#### Сценарий 1: Встраивание в существующий сервис (API)

Библиотека может быть встроена в микросервис или веб-приложение, предоставляющее REST API для генерации тестов. Сервис может обрабатывать запросы от различных клиентов (веб-интерфейс, CI/CD пайплайны, другие сервисы).

**Пример архитектуры:**
```
┌─────────────┐
│  Web App    │
│  (FastAPI)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  AgentBender    │
│  API Layer      │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  Test Generator  │
│  Core            │
└─────────────────┘
```

#### Сценарий 2: Использование через CLI

Библиотека предоставляет командный интерфейс для генерации тестов из командной строки. Подходит для интеграции в CI/CD пайплайны, локальной разработки и автоматизации.

#### Сценарий 3: Встраивание в интерфейс

Библиотека может быть встроена в веб-интерфейс или IDE плагин, предоставляя интерактивный опыт генерации тестов с возможностью предпросмотра и редактирования.

### 1.2 Архитектурные принципы

- **Модульность**: Каждый компонент может использоваться независимо
- **Расширяемость**: Поддержка плагинов и кастомных провайдеров
- **Надежность**: Обработка ошибок и деградационные режимы
- **Observability**: Полное логирование и трассировка операций
- **Производительность**: Кэширование, параллелизация, оптимизация запросов

---

## 2. Интерфейс и API

### 2.1 Основной публичный API

#### 2.1.1 Класс `TestGenerator`

Главный класс библиотеки, отвечающий за генерацию тестов.

```python
class TestGenerator:
    """
    Основной класс для генерации автотестов из тест-кейсов.
    
    Пример использования:
        >>> config = GenerationConfig(...)
        >>> generator = TestGenerator(config=config)
        >>> result = generator.generate(test_case)
    """
    
    def __init__(
        self,
        config: Optional[GenerationConfig] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        logger: Optional[Logger] = None
    ) -> None:
        """
        Инициализация генератора тестов.
        
        Args:
            config: Конфигурация генерации. Если не указана, используется дефолтная.
            llm_provider: Провайдер LLM. Если не указан, создается на основе config.
            logger: Логгер для записи операций. Если не указан, используется стандартный.
        
        Raises:
            ConfigurationError: При некорректной конфигурации.
            ProviderConnectionError: При невозможности подключиться к LLM провайдеру.
        """
    
    def generate(
        self,
        test_case: Union[TestCase, Dict[str, Any], str],
        context: Optional[GenerationContext] = None,
        options: Optional[GenerationOptions] = None
    ) -> GenerationResult:
        """
        Генерация тестового кода из тест-кейса.
        
        Args:
            test_case: Тест-кейс в виде объекта TestCase, словаря или JSON-строки.
            context: Дополнительный контекст для генерации (код приложения, спецификации).
            options: Опции генерации (переопределяют настройки из config).
        
        Returns:
            GenerationResult: Результат генерации, содержащий код тестов, метаданные и отчеты.
        
        Raises:
            ValidationError: При некорректном формате тест-кейса.
            GenerationError: При ошибке генерации кода.
            LLMError: При ошибке взаимодействия с LLM.
        """
    
    def generate_batch(
        self,
        test_cases: List[Union[TestCase, Dict[str, Any], str]],
        context: Optional[GenerationContext] = None,
        options: Optional[GenerationOptions] = None,
        max_workers: Optional[int] = None
    ) -> List[GenerationResult]:
        """
        Параллельная генерация тестов из нескольких тест-кейсов.
        
        Args:
            test_cases: Список тест-кейсов для генерации.
            context: Общий контекст для всех тест-кейсов.
            options: Опции генерации.
            max_workers: Максимальное количество параллельных воркеров. 
                        Если None, используется значение из config.
        
        Returns:
            List[GenerationResult]: Список результатов генерации для каждого тест-кейса.
        
        Raises:
            ValidationError: При некорректном формате хотя бы одного тест-кейса.
        """
    
    def generate_from_file(
        self,
        file_path: Union[str, Path],
        context: Optional[GenerationContext] = None,
        options: Optional[GenerationOptions] = None
    ) -> GenerationResult:
        """
        Генерация тестов из JSON файла с тест-кейсом.
        
        Args:
            file_path: Путь к JSON файлу с тест-кейсом.
            context: Дополнительный контекст для генерации.
            options: Опции генерации.
        
        Returns:
            GenerationResult: Результат генерации.
        
        Raises:
            FileNotFoundError: Если файл не найден.
            ValidationError: При некорректном формате файла.
        """
    
    def generate_from_directory(
        self,
        directory: Union[str, Path],
        pattern: str = "*.json",
        context: Optional[GenerationContext] = None,
        options: Optional[GenerationOptions] = None,
        max_workers: Optional[int] = None
    ) -> List[GenerationResult]:
        """
        Генерация тестов из всех JSON файлов в директории.
        
        Args:
            directory: Путь к директории с JSON файлами.
            pattern: Паттерн для поиска файлов (по умолчанию "*.json").
            context: Общий контекст для всех тест-кейсов.
            options: Опции генерации.
            max_workers: Максимальное количество параллельных воркеров.
        
        Returns:
            List[GenerationResult]: Список результатов генерации.
        """
    
    def validate_test_case(
        self,
        test_case: Union[TestCase, Dict[str, Any], str]
    ) -> ValidationReport:
        """
        Валидация тест-кейса без генерации кода.
        
        Args:
            test_case: Тест-кейс для валидации.
        
        Returns:
            ValidationReport: Отчет о валидации с найденными проблемами и предложениями.
        """
    
    def get_generation_status(
        self,
        generation_id: str
    ) -> Optional[GenerationStatus]:
        """
        Получение статуса асинхронной генерации.
        
        Args:
            generation_id: Идентификатор генерации.
        
        Returns:
            GenerationStatus или None, если генерация не найдена.
        """
```

#### 2.1.2 Модели данных

##### `GenerationConfig`

```python
@dataclass
class GenerationConfig:
    """Конфигурация генератора тестов."""
    
    # LLM настройки
    llm: LLMConfig
    
    # Настройки генерации
    output_dir: Path = Path("./generated_tests")
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
    def from_yaml(cls, file_path: Union[str, Path]) -> "GenerationConfig":
        """Загрузка конфигурации из YAML файла."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationConfig":
        """Создание конфигурации из словаря."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация конфигурации в словарь."""
```

##### `LLMConfig`

```python
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
    log_responses: bool = False  # По умолчанию не логируем ответы (могут быть большими)
    trace_requests: bool = False
```

##### `GenerationContext`

```python
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
        directory: Union[str, Path],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> "GenerationContext":
        """Создание контекста из директории с исходным кодом."""
    
    def add_source_file(self, file_path: Union[str, Path], content: str) -> None:
        """Добавление файла исходного кода в контекст."""
    
    def add_api_contract(self, contract: APIContract) -> None:
        """Добавление API контракта."""
```

##### `GenerationOptions`

```python
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
```

##### `TestStyle`

```python
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
```

##### `GenerationResult`

```python
@dataclass
class GenerationResult:
    """Результат генерации тестов."""
    
    # Идентификатор генерации
    generation_id: str
    
    # Исходный тест-кейс
    test_case: TestCase
    
    # Сгенерированный код
    test_code: str  # Код теста
    page_objects: Dict[str, str]  # Ключ - имя класса, значение - код
    fixtures: Optional[str] = None  # Код фикстур
    helpers: Optional[str] = None  # Код вспомогательных утилит
    config_files: Dict[str, str] = field(default_factory=dict)  # conftest.py, pytest.ini и т.д.
    
    # Метаданные
    generated_at: datetime
    generation_time: float  # Время генерации в секундах
    model_used: str
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
    
    def save_to_directory(self, directory: Union[str, Path]) -> Path:
        """Сохранение результатов в директорию."""
    
    def get_file_structure(self) -> Dict[str, str]:
        """Получение структуры файлов для сохранения."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация результата в словарь."""
```

##### `ValidationReport`

```python
@dataclass
class ValidationReport:
    """Отчет о валидации тест-кейса или сгенерированного кода."""
    
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def has_errors(self) -> bool:
        """Проверка наличия ошибок."""
    
    def has_warnings(self) -> bool:
        """Проверка наличия предупреждений."""


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
```

##### `QualityMetrics`

```python
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
```

### 2.2 Передача исходного контекста

#### 2.2.1 Через `GenerationContext`

Пользователь может передать контекст следующими способами:

```python
# Способ 1: Из директории с исходным кодом
context = GenerationContext.from_directory(
    directory="./src",
    include_patterns=["*.py", "*.ts", "*.js"],
    exclude_patterns=["__pycache__", "*.pyc"]
)

# Способ 2: Программно
context = GenerationContext(
    source_code={
        "pages/login.py": "...",
        "pages/dashboard.py": "..."
    },
    api_contracts=[
        APIContract(
            endpoint="/api/login",
            method="POST",
            request_schema={...},
            response_schema={...}
        )
    ],
    requirements=[
        "Пользователь должен иметь возможность авторизоваться",
        "Система должна валидировать учетные данные"
    ]
)

# Способ 3: Из файла спецификации
context = GenerationContext.from_spec_file("spec.yaml")

# Использование
result = generator.generate(test_case, context=context)
```

#### 2.2.2 Модели для контекста

```python
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
```

### 2.3 Настройки генерации

#### 2.3.1 Уровни качества

```python
class QualityLevel(Enum):
    """Уровни качества генерации."""
    
    FAST = "fast"  # Быстрая генерация, минимальная валидация
    BALANCED = "balanced"  # Баланс скорости и качества (по умолчанию)
    HIGH = "high"  # Максимальное качество, расширенная валидация
```

#### 2.3.2 Уровни детализации

```python
class DetailLevel(Enum):
    """Уровни детализации генерируемых тестов."""
    
    MINIMAL = "minimal"  # Минимальные комментарии, базовая структура
    STANDARD = "standard"  # Стандартные комментарии, полная структура (по умолчанию)
    DETAILED = "detailed"  # Подробные комментарии, расширенная документация
```

#### 2.3.3 Пример настройки

```python
# Создание опций генерации
options = GenerationOptions(
    quality_level="high",
    detail_level="detailed",
    temperature=0.3,  # Более детерминированные ответы
    test_style=TestStyle(
        docstring_style="google",
        comment_style="detailed",
        assertion_style="expect"
    ),
    use_cdp=True,  # Использовать CDP для улучшения селекторов
    validation_level="strict"
)

result = generator.generate(test_case, options=options)
```

### 2.4 Формат возвращаемых результатов

#### 2.4.1 Структура `GenerationResult`

Результат генерации содержит:

1. **Сгенерированный код**:
   - `test_code`: Код теста
   - `page_objects`: Словарь Page Object классов
   - `fixtures`: Код фикстур
   - `helpers`: Вспомогательные утилиты
   - `config_files`: Конфигурационные файлы

2. **Метаданные**:
   - Время генерации
   - Использованная модель
   - Количество токенов

3. **Отчеты**:
   - `validation_report`: Отчет о валидации
   - `quality_metrics`: Метрики качества

4. **Сырые данные** (опционально):
   - `raw_llm_responses`: Сырые ответы LLM для анализа

#### 2.4.2 Пример использования результата

```python
result = generator.generate(test_case)

# Проверка статуса
if result.status == "success":
    # Сохранение в директорию
    output_path = result.save_to_directory("./generated_tests")
    print(f"Тесты сохранены в {output_path}")
    
    # Получение структуры файлов
    file_structure = result.get_file_structure()
    # {
    #     "tests/test_login.py": "...",
    #     "pages/login_page.py": "...",
    #     ...
    # }
    
    # Проверка валидации
    if result.validation_report and result.validation_report.has_errors():
        for error in result.validation_report.errors:
            print(f"Ошибка: {error.message}")
    
    # Метрики качества
    if result.quality_metrics:
        print(f"Оценка качества: {result.quality_metrics.generation_quality}")
```

---

## 3. Интеграция с LLM

### 3.1 Абстракция провайдера

#### 3.1.1 Базовый интерфейс `BaseLLMProvider`

```python
class BaseLLMProvider(ABC):
    """Базовый интерфейс для LLM провайдеров."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Генерация ответа от LLM.
        
        Args:
            prompt: Основной промпт.
            system_prompt: Системный промпт (опционально).
            temperature: Температура генерации.
            max_tokens: Максимальное количество токенов.
            **kwargs: Дополнительные параметры провайдера.
        
        Returns:
            LLMResponse: Ответ от LLM.
        
        Raises:
            LLMError: При ошибке взаимодействия с LLM.
        """
    
    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Потоковая генерация ответа.
        
        Yields:
            str: Части ответа по мере генерации.
        """
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности провайдера."""
    
    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Получение информации о модели."""
```

#### 3.1.2 Реализация `OllamaProvider`

```python
class OllamaProvider(BaseLLMProvider):
    """Провайдер для Ollama (локальный и удаленный)."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 300,
        api_key: Optional[str] = None,
        logger: Optional[Logger] = None
    ) -> None:
        """
        Инициализация Ollama провайдера.
        
        Args:
            base_url: URL Ollama сервера.
            model: Имя модели.
            timeout: Таймаут запроса в секундах.
            api_key: API ключ (если требуется).
            logger: Логгер.
        """
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Реализация генерации через Ollama API."""
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """Реализация потоковой генерации."""
    
    def is_available(self) -> bool:
        """Проверка доступности Ollama сервера."""
    
    def get_model_info(self) -> ModelInfo:
        """Получение информации о модели Ollama."""
```

#### 3.1.3 Модель ответа `LLMResponse`

```python
@dataclass
class LLMResponse:
    """Ответ от LLM."""
    
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация ответа."""
```

### 3.2 Формат промптов

#### 3.2.1 Структура промпта

Промпты структурированы следующим образом:

```
[System Prompt]
Системные инструкции и контекст библиотеки.

[Context Section]
Дополнительный контекст (код, спецификации, требования).

[Task Section]
Конкретная задача генерации.

[Output Format Section]
Требования к формату ответа (JSON схема).
```

#### 3.2.2 Шаблоны промптов

```python
class PromptTemplate:
    """Шаблон промпта для генерации."""
    
    SYSTEM_PROMPT = """
    Ты — эксперт по автоматизации тестирования веб-приложений.
    Твоя задача — генерировать качественные автотесты на Python с использованием
    Playwright и паттерна Page Object Model.
    
    Требования:
    - Использовать Playwright для автоматизации браузера
    - Применять паттерн Page Object Model
    - Использовать библиотеку @gpn_qa_utils для вспомогательных функций
    - Следовать корпоративным стандартам кодирования
    - Генерировать читаемый и поддерживаемый код
    """
    
    TEST_GENERATION_PROMPT = """
    Сгенерируй автотест на основе следующего тест-кейса:
    
    Тест-кейс ID: {test_case_id}
    Название: {test_case_title}
    Описание: {test_case_description}
    
    Шаги:
    {test_steps}
    
    Ожидаемый результат: {expected_result}
    
    Дополнительный контекст:
    {context}
    
    Требования к коду:
    - Использовать класс Test{class_name}
    - Применить Page Object Model
    - Добавить подробные комментарии
    - Использовать фикстуры pytest
    - Включить валидации через expect()
    """
    
    PAGE_OBJECT_PROMPT = """
    Сгенерируй Page Object класс для страницы: {page_name}
    
    Элементы страницы:
    {elements}
    
    Действия на странице:
    {actions}
    
    Требования:
    - Наследоваться от BasePage
    - Инкапсулировать все локаторы
    - Создать методы для всех действий
    - Добавить методы валидации
    """
```

#### 3.2.3 Построение промпта

```python
class PromptBuilder:
    """Построитель промптов для LLM."""
    
    def __init__(
        self,
        template: PromptTemplate,
        context: Optional[GenerationContext] = None
    ) -> None:
        """Инициализация построителя."""
    
    def build_test_prompt(
        self,
        test_case: TestCase,
        options: GenerationOptions
    ) -> str:
        """Построение промпта для генерации теста."""
    
    def build_page_object_prompt(
        self,
        page_info: PageInfo,
        options: GenerationOptions
    ) -> str:
        """Построение промпта для генерации Page Object."""
    
    def add_context(self, context: GenerationContext) -> "PromptBuilder":
        """Добавление контекста в промпт."""
    
    def add_examples(self, examples: List[str]) -> "PromptBuilder":
        """Добавление примеров в промпт."""
```

### 3.3 Структурированные JSON-ответы

#### 3.3.1 Схема ответа

LLM должен возвращать структурированный JSON:

```json
{
  "test_code": "...",
  "page_objects": {
    "LoginPage": "...",
    "DashboardPage": "..."
  },
  "fixtures": "...",
  "metadata": {
    "confidence": 0.95,
    "notes": "..."
  }
}
```

#### 3.3.2 Парсинг ответов

```python
class LLMResponseParser:
    """Парсер ответов от LLM."""
    
    def parse_test_response(
        self,
        response: LLMResponse
    ) -> ParsedTestResponse:
        """
        Парсинг ответа с тестовым кодом.
        
        Raises:
            ParseError: При ошибке парсинга JSON.
        """
    
    def parse_page_object_response(
        self,
        response: LLMResponse
    ) -> ParsedPageObjectResponse:
        """Парсинг ответа с Page Object."""
    
    def extract_code_blocks(
        self,
        text: str
    ) -> List[CodeBlock]:
        """Извлечение блоков кода из текста."""
```

### 3.4 Стратегия ретраев

#### 3.4.1 Реализация ретраев

```python
class RetryStrategy:
    """Стратегия повторных попыток для LLM запросов."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0
    ) -> None:
        """
        Инициализация стратегии.
        
        Args:
            max_retries: Максимальное количество попыток.
            initial_delay: Начальная задержка в секундах.
            backoff_factor: Множитель для экспоненциальной задержки.
            max_delay: Максимальная задержка в секундах.
        """
    
    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Выполнение функции с ретраями.
        
        Raises:
            MaxRetriesExceeded: При превышении максимального количества попыток.
        """
    
    def should_retry(self, exception: Exception) -> bool:
        """Определение необходимости повторной попытки."""
```

#### 3.4.2 Типы ошибок для ретраев

```python
class RetryableError(Exception):
    """Ошибка, при которой стоит повторить запрос."""
    pass

class NonRetryableError(Exception):
    """Ошибка, при которой повтор не поможет."""
    pass

class TimeoutError(RetryableError):
    """Таймаут запроса."""
    pass

class RateLimitError(RetryableError):
    """Превышение лимита запросов."""
    pass

class InvalidResponseError(NonRetryableError):
    """Некорректный ответ от LLM."""
    pass
```

### 3.5 Логирование и трассировка

#### 3.5.1 Структура логирования

```python
@dataclass
class LLMRequestLog:
    """Лог запроса к LLM."""
    
    request_id: str
    timestamp: datetime
    provider: str
    model: str
    prompt_length: int
    system_prompt_length: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация лога."""


@dataclass
class LLMResponseLog:
    """Лог ответа от LLM."""
    
    request_id: str
    timestamp: datetime
    response_length: int
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    generation_time: float
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация лога."""
```

#### 3.5.2 Трассировка запросов

```python
class LLMTracer:
    """Трассировка запросов к LLM для дебага и аналитики."""
    
    def __init__(
        self,
        logger: Logger,
        enable_tracing: bool = True,
        storage: Optional[TraceStorage] = None
    ) -> None:
        """Инициализация трассировщика."""
    
    def trace_request(
        self,
        request: LLMRequestLog
    ) -> str:
        """
        Начало трассировки запроса.
        
        Returns:
            str: ID запроса для связи с ответом.
        """
    
    def trace_response(
        self,
        request_id: str,
        response: LLMResponseLog
    ) -> None:
        """Завершение трассировки запроса."""
    
    def get_trace(
        self,
        request_id: str
    ) -> Optional[LLMTrace]:
        """Получение полной трассировки запроса."""
    
    def export_traces(
        self,
        file_path: Union[str, Path],
        format: Literal["json", "csv"] = "json"
    ) -> None:
        """Экспорт трассировок в файл."""
```

#### 3.5.3 Хранилище трассировок

```python
class TraceStorage(ABC):
    """Абстракция хранилища трассировок."""
    
    @abstractmethod
    def save(self, trace: LLMTrace) -> None:
        """Сохранение трассировки."""
    
    @abstractmethod
    def get(self, request_id: str) -> Optional[LLMTrace]:
        """Получение трассировки."""
    
    @abstractmethod
    def query(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[LLMTrace]:
        """Запрос трассировок по фильтрам."""


class InMemoryTraceStorage(TraceStorage):
    """Хранилище трассировок в памяти."""
    pass


class FileTraceStorage(TraceStorage):
    """Хранилище трассировок в файле."""
    pass
```

### 3.6 Обработка ошибок и нестабильности LLM

#### 3.6.1 Типы ошибок

```python
class LLMError(Exception):
    """Базовый класс для ошибок LLM."""
    pass

class LLMConnectionError(LLMError):
    """Ошибка подключения к LLM."""
    pass

class LLMTimeoutError(LLMError):
    """Таймаут запроса к LLM."""
    pass

class LLMRateLimitError(LLMError):
    """Превышение лимита запросов."""
    pass

class LLMInvalidResponseError(LLMError):
    """Некорректный ответ от LLM."""
    pass

class LLMPartialResponseError(LLMError):
    """Частичный ответ от LLM."""
    pass
```

#### 3.6.2 Обработчик ошибок

```python
class LLMErrorHandler:
    """Обработчик ошибок LLM."""
    
    def __init__(
        self,
        retry_strategy: RetryStrategy,
        fallback_provider: Optional[BaseLLMProvider] = None,
        logger: Optional[Logger] = None
    ) -> None:
        """Инициализация обработчика."""
    
    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[LLMResponse]:
        """
        Обработка ошибки с применением стратегии ретраев.
        
        Returns:
            LLMResponse или None, если все попытки исчерпаны.
        """
    
    def handle_timeout(
        self,
        request: LLMRequestLog
    ) -> Optional[LLMResponse]:
        """Обработка таймаута."""
    
    def handle_partial_response(
        self,
        partial_response: str,
        context: Dict[str, Any]
    ) -> Optional[LLMResponse]:
        """Обработка частичного ответа."""
    
    def fallback_to_provider(
        self,
        provider: BaseLLMProvider,
        prompt: str
    ) -> Optional[LLMResponse]:
        """Переключение на резервный провайдер."""
```

#### 3.6.3 Деградационный режим

```python
class DegradedModeHandler:
    """Обработчик деградационного режима при недоступности LLM."""
    
    def __init__(
        self,
        template_engine: TemplateEngine,
        logger: Optional[Logger] = None
    ) -> None:
        """Инициализация обработчика."""
    
    def generate_without_llm(
        self,
        test_case: TestCase,
        options: GenerationOptions
    ) -> GenerationResult:
        """
        Генерация тестов без использования LLM (только шаблоны).
        
        Используется когда LLM недоступен, но нужно сгенерировать
        базовую структуру тестов.
        """
```

---

## 4. Генерация и валидация тестов

### 4.1 Пайплайн генерации

#### 4.1.1 Основной пайплайн

```
Входные данные (TestCase)
    │
    ▼
[1] Парсинг и валидация
    │
    ▼
[2] Извлечение контекста
    │
    ▼
[3] Анализ тест-кейса
    │
    ├─► Определение страниц
    ├─► Определение действий
    └─► Определение проверок
    │
    ▼
[4] Генерация промптов
    │
    ├─► Промпт для теста
    ├─► Промпты для Page Objects
    └─► Промпт для фикстур
    │
    ▼
[5] Вызов LLM
    │
    ├─► Генерация теста
    ├─► Генерация Page Objects
    └─► Генерация фикстур
    │
    ▼
[6] Парсинг ответов
    │
    ▼
[7] Пост-обработка
    │
    ├─► Валидация кода
    ├─► Форматирование
    └─► Интеграция компонентов
    │
    ▼
[8] Генерация структуры проекта
    │
    ▼
[9] Финальная валидация
    │
    ▼
Результат (GenerationResult)
```

#### 4.1.2 Реализация пайплайна

```python
class GenerationPipeline:
    """Пайплайн генерации тестов."""
    
    def __init__(
        self,
        parser: TestCaseParser,
        llm_provider: BaseLLMProvider,
        prompt_builder: PromptBuilder,
        code_generator: CodeGenerator,
        validator: CodeValidator,
        formatter: CodeFormatter,
        logger: Optional[Logger] = None
    ) -> None:
        """Инициализация пайплайна."""
    
    def execute(
        self,
        test_case: Union[TestCase, Dict[str, Any], str],
        context: Optional[GenerationContext] = None,
        options: Optional[GenerationOptions] = None
    ) -> GenerationResult:
        """
        Выполнение полного пайплайна генерации.
        
        Returns:
            GenerationResult: Результат генерации.
        """
    
    def _parse_test_case(
        self,
        test_case: Union[TestCase, Dict[str, Any], str]
    ) -> TestCase:
        """Шаг 1: Парсинг тест-кейса."""
    
    def _analyze_test_case(
        self,
        test_case: TestCase
    ) -> TestCaseAnalysis:
        """Шаг 3: Анализ тест-кейса."""
    
    def _generate_prompts(
        self,
        test_case: TestCase,
        analysis: TestCaseAnalysis,
        context: Optional[GenerationContext],
        options: GenerationOptions
    ) -> Dict[str, str]:
        """Шаг 4: Генерация промптов."""
    
    def _call_llm(
        self,
        prompts: Dict[str, str],
        options: GenerationOptions
    ) -> Dict[str, LLMResponse]:
        """Шаг 5: Вызов LLM."""
    
    def _parse_responses(
        self,
        responses: Dict[str, LLMResponse]
    ) -> ParsedResponses:
        """Шаг 6: Парсинг ответов."""
    
    def _post_process(
        self,
        parsed_responses: ParsedResponses,
        test_case: TestCase,
        options: GenerationOptions
    ) -> PostProcessedCode:
        """Шаг 7: Пост-обработка."""
    
    def _generate_structure(
        self,
        code: PostProcessedCode,
        test_case: TestCase
    ) -> ProjectStructure:
        """Шаг 8: Генерация структуры проекта."""
    
    def _final_validation(
        self,
        structure: ProjectStructure,
        test_case: TestCase
    ) -> ValidationReport:
        """Шаг 9: Финальная валидация."""
```

### 4.2 Валидация тестов

#### 4.2.1 Валидатор кода

```python
class CodeValidator:
    """Валидатор сгенерированного кода."""
    
    def __init__(
        self,
        validation_level: Literal["basic", "strict", "none"] = "basic",
        logger: Optional[Logger] = None
    ) -> None:
        """Инициализация валидатора."""
    
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
    
    def validate_syntax(self, code: str) -> List[ValidationError]:
        """Валидация синтаксиса Python."""
    
    def validate_structure(self, code: str) -> List[ValidationError]:
        """Валидация структуры теста."""
    
    def validate_playwright_usage(self, code: str) -> List[ValidationError]:
        """Валидация использования Playwright."""
    
    def validate_page_object_pattern(self, code: str) -> List[ValidationError]:
        """Валидация соответствия паттерну Page Object."""
    
    def validate_test_coverage(
        self,
        code: str,
        test_case: TestCase
    ) -> List[ValidationWarning]:
        """Проверка покрытия тест-кейса."""
```

#### 4.2.2 Уровни валидации

```python
class ValidationLevel(Enum):
    """Уровни валидации."""
    
    NONE = "none"  # Валидация отключена
    BASIC = "basic"  # Базовая валидация (синтаксис, структура)
    STRICT = "strict"  # Строгая валидация (все проверки + качество кода)
```

### 4.3 Пост-обработка кода

#### 4.3.1 Форматирование

```python
class CodeFormatter:
    """Форматтер кода."""
    
    def __init__(
        self,
        style: Literal["black", "autopep8", "none"] = "black",
        logger: Optional[Logger] = None
    ) -> None:
        """Инициализация форматтера."""
    
    def format(self, code: str) -> str:
        """Форматирование кода."""
    
    def format_file(self, file_path: Union[str, Path]) -> None:
        """Форматирование файла."""
```

#### 4.3.2 Интеграция компонентов

```python
class CodeIntegrator:
    """Интегратор сгенерированных компонентов."""
    
    def integrate(
        self,
        test_code: str,
        page_objects: Dict[str, str],
        fixtures: Optional[str] = None
    ) -> IntegratedCode:
        """
        Интеграция компонентов в единую структуру.
        
        Returns:
            IntegratedCode: Интегрированный код с разрешенными зависимостями.
        """
    
    def resolve_imports(
        self,
        code: str,
        available_modules: List[str]
    ) -> str:
        """Разрешение импортов в коде."""
    
    def merge_page_objects(
        self,
        existing: Dict[str, str],
        new: Dict[str, str]
    ) -> Dict[str, str]:
        """Объединение существующих и новых Page Objects."""
```

---

## 5. Нефункциональные требования

### 5.1 Производительность

#### 5.1.1 Целевые метрики

- **Время генерации одного теста**: < 30 секунд (при использовании локального Ollama)
- **Время генерации батча (10 тестов)**: < 5 минут (с параллелизацией)
- **Пропускная способность**: > 20 тестов/час (на одной модели)

#### 5.1.2 Оптимизации

```python
@dataclass
class PerformanceConfig:
    """Конфигурация производительности."""
    
    # Параллелизация
    max_workers: int = 4
    enable_async: bool = True
    
    # Кэширование
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 час
    
    # Оптимизация запросов
    batch_prompts: bool = True
    prompt_compression: bool = False
    
    # Лимиты
    max_prompt_length: int = 8000
    max_response_length: int = 4000
```

#### 5.1.3 Кэширование

```python
class GenerationCache:
    """Кэш для генерации тестов."""
    
    def __init__(
        self,
        ttl: int = 3600,
        max_size: int = 1000
    ) -> None:
        """Инициализация кэша."""
    
    def get(
        self,
        cache_key: str
    ) -> Optional[GenerationResult]:
        """Получение из кэша."""
    
    def set(
        self,
        cache_key: str,
        result: GenerationResult
    ) -> None:
        """Сохранение в кэш."""
    
    def generate_key(
        self,
        test_case: TestCase,
        options: GenerationOptions
    ) -> str:
        """Генерация ключа кэша."""
```

### 5.2 Масштабируемость

#### 5.2.1 Предполагаемые объемы

- **Размер тест-кейса**: до 100 шагов
- **Количество тест-кейсов в батче**: до 100
- **Размер контекста**: до 10 MB исходного кода
- **Количество одновременных запросов**: до 50

#### 5.2.2 Архитектура масштабирования

```python
class ScalableGenerator:
    """Масштабируемый генератор с поддержкой распределенной обработки."""
    
    def __init__(
        self,
        config: GenerationConfig,
        queue: Optional[TaskQueue] = None
    ) -> None:
        """Инициализация с поддержкой очереди задач."""
    
    def generate_async(
        self,
        test_case: TestCase,
        context: Optional[GenerationContext] = None,
        options: Optional[GenerationOptions] = None
    ) -> str:
        """
        Асинхронная генерация с возвратом ID задачи.
        
        Returns:
            str: ID задачи для отслеживания статуса.
        """
    
    def get_result(self, task_id: str) -> Optional[GenerationResult]:
        """Получение результата по ID задачи."""
```

### 5.3 Безопасность

#### 5.3.1 Валидация входных данных

```python
class SecurityValidator:
    """Валидатор безопасности."""
    
    def validate_input(
        self,
        test_case: TestCase,
        context: Optional[GenerationContext] = None
    ) -> SecurityReport:
        """
        Валидация входных данных на безопасность.
        
        Проверяет:
        - Отсутствие инъекций в промпты
        - Валидность JSON структуры
        - Размер данных
        - Подозрительные паттерны
        """
    
    def sanitize_prompt(self, prompt: str) -> str:
        """Санитизация промпта от потенциально опасных конструкций."""
    
    def validate_generated_code(self, code: str) -> SecurityReport:
        """Валидация сгенерированного кода на безопасность."""
```

#### 5.3.2 Санитизация кода

```python
class CodeSanitizer:
    """Санитизатор сгенерированного кода."""
    
    DANGEROUS_PATTERNS = [
        r"eval\(",
        r"exec\(",
        r"__import__\(",
        r"subprocess\.",
        r"os\.system\(",
        # ... другие паттерны
    ]
    
    def sanitize(self, code: str) -> str:
        """Удаление потенциально опасных конструкций."""
    
    def check_patterns(self, code: str) -> List[str]:
        """Проверка на наличие опасных паттернов."""
```

### 5.4 Логирование и observability

#### 5.4.1 Структура логирования

```python
class StructuredLogger:
    """Структурированный логгер для observability."""
    
    def log_generation_start(
        self,
        test_case_id: str,
        options: GenerationOptions
    ) -> None:
        """Логирование начала генерации."""
    
    def log_generation_complete(
        self,
        test_case_id: str,
        result: GenerationResult
    ) -> None:
        """Логирование завершения генерации."""
    
    def log_llm_request(
        self,
        request: LLMRequestLog
    ) -> None:
        """Логирование запроса к LLM."""
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> None:
        """Логирование ошибки."""
```

#### 5.4.2 Метрики

```python
@dataclass
class GenerationMetrics:
    """Метрики генерации."""
    
    # Время
    total_time: float
    llm_time: float
    validation_time: float
    
    # Ресурсы
    tokens_used: Optional[int] = None
    memory_used: Optional[float] = None
    
    # Качество
    validation_score: Optional[float] = None
    quality_score: Optional[float] = None
    
    # Статус
    success: bool
    errors_count: int = 0
    warnings_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация метрик."""
```

#### 5.4.3 Экспорт метрик

```python
class MetricsExporter:
    """Экспортер метрик для мониторинга."""
    
    def export(
        self,
        metrics: GenerationMetrics,
        format: Literal["json", "prometheus", "statsd"] = "json"
    ) -> str:
        """Экспорт метрик в указанном формате."""
```

### 5.5 Ограничения и предположения

#### 5.5.1 Ограничения по ресурсам

- **Память**: до 2 GB на процесс генерации
- **CPU**: поддержка многоядерной обработки
- **Диск**: до 100 MB на сгенерированный проект
- **Сеть**: поддержка работы в офлайн-режиме (локальный Ollama)

#### 5.5.2 Ограничения по времени

- **Таймаут LLM запроса**: 300 секунд (5 минут)
- **Таймаут генерации теста**: 600 секунд (10 минут)
- **Таймаут валидации**: 60 секунд

#### 5.5.3 Предположения

- LLM провайдер доступен и стабилен
- Достаточно ресурсов для работы модели
- Входные данные в корректном формате
- Playwright установлен и настроен
- Библиотека @gpn_qa_utils доступна

---

## 6. Примеры использования

### 6.1 Базовое использование (Python API)

```python
from agentbender import TestGenerator, GenerationConfig, LLMConfig

# Создание конфигурации
config = GenerationConfig(
    llm=LLMConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        model="llama3",
        temperature=0.7
    ),
    output_dir="./generated_tests"
)

# Создание генератора
generator = TestGenerator(config=config)

# Генерация теста
test_case = {
    "id": "TC-001",
    "title": "Авторизация пользователя",
    "steps": [...]
}

result = generator.generate(test_case)

# Сохранение результатов
if result.status == "success":
    output_path = result.save_to_directory("./generated_tests")
    print(f"Тесты сохранены в {output_path}")
```

### 6.2 Использование с контекстом

```python
from agentbender import GenerationContext

# Создание контекста из директории
context = GenerationContext.from_directory(
    directory="./src",
    include_patterns=["*.py"]
)

# Добавление API контрактов
context.add_api_contract(
    APIContract(
        endpoint="/api/login",
        method="POST",
        request_schema={...},
        response_schema={...}
    )
)

# Генерация с контекстом
result = generator.generate(test_case, context=context)
```

### 6.3 Параллельная генерация

```python
# Генерация батча тестов
test_cases = [test_case_1, test_case_2, test_case_3]

results = generator.generate_batch(
    test_cases,
    max_workers=4
)

# Обработка результатов
for result in results:
    if result.status == "success":
        result.save_to_directory(f"./generated_tests/{result.test_case.id}")
```

### 6.4 Использование через CLI

```bash
# Базовая генерация
agentbender generate --input test_case.json --output ./tests

# С конфигурацией
agentbender generate \
    --input test_case.json \
    --config config.yaml \
    --output ./tests

# С опциями
agentbender generate \
    --input test_case.json \
    --model llama3:8b \
    --temperature 0.3 \
    --quality high \
    --use-cdp
```

### 6.5 Использование в веб-сервисе (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from agentbender import TestGenerator, GenerationConfig

app = FastAPI()
generator = TestGenerator(config=GenerationConfig.from_yaml("config.yaml"))

@app.post("/api/generate")
async def generate_test(test_case: dict):
    try:
        result = generator.generate(test_case)
        return {
            "status": result.status,
            "generation_id": result.generation_id,
            "test_code": result.test_code,
            "metrics": result.quality_metrics.to_dict() if result.quality_metrics else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{generation_id}")
async def get_status(generation_id: str):
    status = generator.get_generation_status(generation_id)
    if not status:
        raise HTTPException(status_code=404, detail="Generation not found")
    return status.to_dict()
```

---

## Заключение

Данный документ описывает детальный дизайн API и архитектуру библиотеки AgentBender для генерации автотестов с использованием LLM. Все компоненты спроектированы с учетом требований из ARCHITECTURE.md и обеспечивают:

- Гибкость использования (API, CLI, встраивание)
- Надежность (обработка ошибок, ретраи, деградационные режимы)
- Производительность (кэширование, параллелизация)
- Безопасность (валидация, санитизация)
- Observability (логирование, метрики, трассировка)

Библиотека готова к реализации с учетом всех описанных интерфейсов и требований.


"""Main test generator class."""

import time
from pathlib import Path
from typing import Union, Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import glob

from agentbender.models.test_case import TestCase
from agentbender.models.config import (
    GenerationConfig,
    GenerationContext,
    GenerationOptions,
)
from agentbender.models.results import (
    GenerationResult,
    ValidationReport,
    GenerationStatus,
    QualityMetrics,
)
from agentbender.providers.base_provider import BaseLLMProvider
from agentbender.providers.ollama_provider import OllamaProvider
from agentbender.core.parser import TestCaseParser
from agentbender.core.validator import CodeValidator
from agentbender.generators.test_generator import TestCodeGenerator
from agentbender.generators.page_object_generator import PageObjectGenerator
from agentbender.generators.fixture_generator import FixtureGenerator
from agentbender.utils.formatter import CodeFormatter
from agentbender.utils.file_manager import FileManager


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Ошибка конфигурации."""
    pass


class ProviderConnectionError(Exception):
    """Ошибка подключения к провайдеру."""
    pass


class GenerationError(Exception):
    """Ошибка генерации."""
    pass


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
        logger: Optional[logging.Logger] = None
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
        self.config = config or GenerationConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # Создание провайдера LLM
        if llm_provider:
            self.llm_provider = llm_provider
        else:
            if self.config.llm.provider == "ollama":
                self.llm_provider = OllamaProvider(
                    base_url=self.config.llm.base_url,
                    model=self.config.llm.model,
                    timeout=self.config.llm.timeout,
                    api_key=self.config.llm.ollama_api_key or self.config.llm.api_key,
                    logger=self.logger
                )
            else:
                raise ConfigurationError(
                    f"Неподдерживаемый провайдер LLM: {self.config.llm.provider}"
                )
        
        # Проверка доступности провайдера
        if not self.llm_provider.is_available():
            raise ProviderConnectionError(
                f"Провайдер LLM недоступен: {self.config.llm.provider}"
            )
        
        # Инициализация компонентов
        self.parser = TestCaseParser(logger=self.logger)
        self.validator = CodeValidator(
            validation_level=self.config.validation.level,
            logger=self.logger
        )
        self.formatter = CodeFormatter(
            style=self.config.code_style,
            logger=self.logger
        )
        self.file_manager = FileManager(logger=self.logger)
        
        # Генераторы
        template_dir = self.config.template_dir
        self.test_generator = TestCodeGenerator(
            llm_provider=self.llm_provider,
            template_dir=template_dir,
            formatter=self.formatter,
            logger=self.logger
        )
        self.page_object_generator = PageObjectGenerator(
            llm_provider=self.llm_provider,
            template_dir=template_dir,
            formatter=self.formatter,
            logger=self.logger
        )
        self.fixture_generator = FixtureGenerator(
            template_dir=template_dir,
            formatter=self.formatter,
            logger=self.logger
        )
        
        # Хранилище статусов (для асинхронных операций)
        self._generation_statuses: Dict[str, GenerationStatus] = {}
    
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
        start_time = time.time()
        
        try:
            # Парсинг тест-кейса
            parsed_test_case = self.parser.parse(test_case)
            
            # Валидация тест-кейса
            validation_report = self.parser.validate(parsed_test_case)
            if not validation_report.is_valid:
                if options and options.skip_validation:
                    self.logger.warning("Валидация пропущена, но тест-кейс содержит ошибки")
                else:
                    error_messages = [f"{e.code}: {e.message}" for e in validation_report.errors]
                    raise GenerationError(
                        f"Тест-кейс не прошел валидацию: {'; '.join(error_messages)}"
                    )
            
            # Объединение опций
            final_options = self._merge_options(options)
            
            # Генерация Page Objects
            page_objects = {}
            if final_options.generate_page_objects:
                try:
                    page_objects = self.page_object_generator.generate_from_test_case(
                        test_case=parsed_test_case,
                        context=context,
                        options=final_options
                    )
                except Exception as e:
                    self.logger.warning(f"Ошибка при генерации Page Objects: {e}")
            
            # Генерация тестового кода
            test_code = self.test_generator.generate(
                test_case=parsed_test_case,
                page_objects=page_objects,
                context=context,
                options=final_options
            )
            
            # Генерация фикстур
            fixtures = None
            if final_options.generate_fixtures:
                try:
                    fixtures = self.fixture_generator.generate(
                        playwright_config=self.config.playwright,
                        options=final_options
                    )
                except Exception as e:
                    self.logger.warning(f"Ошибка при генерации фикстур: {e}")
            
            # Генерация конфигурационных файлов
            config_files = {}
            try:
                config_files = self.fixture_generator.generate_config_files(
                    gpn_qa_utils_enabled=self.config.gpn_qa_utils.enabled
                )
            except Exception as e:
                self.logger.warning(f"Ошибка при генерации конфигурационных файлов: {e}")
            
            # Генерация BasePage
            base_page_code = self.fixture_generator.generate_base_page()
            if base_page_code:
                config_files["pages/base_page.py"] = base_page_code
            
            # Валидация сгенерированного кода
            code_validation = None
            if not final_options.skip_validation:
                code_validation = self.validator.validate(
                    code=test_code,
                    test_case=parsed_test_case
                )
            
            # Вычисление метрик качества (упрощенная версия)
            quality_metrics = self._calculate_quality_metrics(test_code, code_validation)
            
            generation_time = time.time() - start_time
            
            # Создание результата
            result = GenerationResult(
                test_case=parsed_test_case,
                test_code=test_code,
                page_objects=page_objects,
                fixtures=fixtures,
                config_files=config_files,
                generation_time=generation_time,
                model_used=self.config.llm.model,
                validation_report=code_validation,
                quality_metrics=quality_metrics,
                status="success" if (not code_validation or code_validation.is_valid) else "partial"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Ошибка при генерации теста: {e}")
            raise GenerationError(f"Ошибка генерации: {e}") from e
    
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
        max_workers = max_workers or self.config.performance.max_workers
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.generate, tc, context, options): tc
                for tc in test_cases
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Ошибка при генерации теста: {e}")
                    # Создание результата с ошибкой
                    test_case = futures[future]
                    try:
                        parsed = self.parser.parse(test_case)
                        error_result = GenerationResult(
                            test_case=parsed,
                            test_code="",
                            status="failed",
                            errors=[str(e)]
                        )
                        results.append(error_result)
                    except Exception:
                        # Если не удалось распарсить, пропускаем
                        pass
        
        return results
    
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
        return self.generate(
            test_case=file_path,
            context=context,
            options=options
        )
    
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
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Директория не найдена: {directory}")
        
        # Поиск файлов
        files = list(directory.glob(pattern))
        
        if not files:
            self.logger.warning(f"Файлы по паттерну '{pattern}' не найдены в {directory}")
            return []
        
        return self.generate_batch(
            test_cases=files,
            context=context,
            options=options,
            max_workers=max_workers
        )
    
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
        parsed = self.parser.parse(test_case)
        return self.parser.validate(parsed)
    
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
        return self._generation_statuses.get(generation_id)
    
    def _merge_options(self, options: Optional[GenerationOptions]) -> GenerationOptions:
        """Объединение опций генерации с конфигурацией."""
        if not options:
            return GenerationOptions()
        
        # Применение значений из config, если не указаны в options
        merged = GenerationOptions(
            model=options.model or self.config.llm.model,
            temperature=options.temperature or self.config.llm.temperature,
            max_tokens=options.max_tokens or self.config.llm.max_tokens,
            quality_level=options.quality_level,
            detail_level=options.detail_level,
            test_style=options.test_style,
            custom_templates=options.custom_templates,
            generate_page_objects=options.generate_page_objects,
            generate_fixtures=options.generate_fixtures,
            generate_helpers=options.generate_helpers,
            use_cdp=options.use_cdp if options.use_cdp is not None else self.config.use_cdp,
            skip_validation=options.skip_validation,
            validation_level=options.validation_level or self.config.validation.level,
        )
        
        return merged
    
    def _calculate_quality_metrics(
        self,
        code: str,
        validation_report: Optional[ValidationReport]
    ) -> QualityMetrics:
        """Вычисление метрик качества кода (упрощенная версия)."""
        # Упрощенные метрики
        code_complexity = len(code.split("\n")) / 100.0  # Простая метрика
        test_coverage_estimate = 0.8  # Заглушка
        maintainability_index = 0.7  # Заглушка
        style_compliance = 0.9 if validation_report and validation_report.is_valid else 0.5
        pattern_compliance = 0.8  # Заглушка
        
        return QualityMetrics(
            code_complexity=min(code_complexity, 1.0),
            test_coverage_estimate=test_coverage_estimate,
            maintainability_index=maintainability_index,
            style_compliance=style_compliance,
            pattern_compliance=pattern_compliance,
            confidence_score=0.85,
            generation_quality=0.8
        )


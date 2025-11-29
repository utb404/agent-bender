"""CLI interface for AgentBender."""

import json
import sys
from pathlib import Path
from typing import Optional
import click
import logging

from agentbender import TestGenerator, GenerationConfig, GenerationOptions
from agentbender.models.config import GenerationContext


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """AgentBender - Генератор автотестов с использованием LLM."""
    pass


@cli.command()
@click.option(
    "--input", "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Путь к JSON файлу с тест-кейсом"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default="./generated_tests",
    help="Директория для сохранения сгенерированных тестов"
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Путь к YAML файлу с конфигурацией"
)
@click.option(
    "--model", "-m",
    help="Модель LLM для использования"
)
@click.option(
    "--temperature", "-t",
    type=float,
    help="Температура генерации (0.0-1.0)"
)
@click.option(
    "--quality",
    type=click.Choice(["fast", "balanced", "high"], case_sensitive=False),
    default="balanced",
    help="Уровень качества генерации"
)
@click.option(
    "--use-cdp",
    is_flag=True,
    help="Использовать CDP для улучшения селекторов"
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Пропустить валидацию сгенерированного кода"
)
@click.option(
    "--context-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Директория с исходным кодом для контекста"
)
def generate(
    input: Path,
    output: Path,
    config: Optional[Path],
    model: Optional[str],
    temperature: Optional[float],
    quality: str,
    use_cdp: bool,
    skip_validation: bool,
    context_dir: Optional[Path]
):
    """Генерация тестов из тест-кейса."""
    try:
        # Загрузка конфигурации
        if config:
            gen_config = GenerationConfig.from_yaml(config)
        else:
            gen_config = GenerationConfig()
        
        # Переопределение настроек из командной строки
        if model:
            gen_config.llm.model = model
        if temperature is not None:
            gen_config.llm.temperature = temperature
        if use_cdp:
            gen_config.use_cdp = True
        
        # Создание генератора
        generator = TestGenerator(config=gen_config)
        
        # Создание контекста
        context = None
        if context_dir:
            context = GenerationContext.from_directory(context_dir)
        
        # Опции генерации
        options = GenerationOptions(
            quality_level=quality,
            use_cdp=use_cdp if use_cdp else None,
            skip_validation=skip_validation
        )
        
        click.echo(f"Генерация тестов из {input}...")
        
        # Генерация
        result = generator.generate(
            test_case=input,
            context=context,
            options=options
        )
        
        # Сохранение результатов
        output_path = result.save_to_directory(output)
        
        click.echo(f"✓ Тесты успешно сгенерированы и сохранены в {output_path}")
        click.echo(f"  Статус: {result.status}")
        click.echo(f"  Время генерации: {result.generation_time:.2f} сек")
        click.echo(f"  Модель: {result.model_used}")
        
        if result.validation_report:
            if result.validation_report.has_errors():
                click.echo(f"  ⚠ Ошибки валидации: {len(result.validation_report.errors)}")
            if result.validation_report.has_warnings():
                click.echo(f"  ⚠ Предупреждения: {len(result.validation_report.warnings)}")
        
        if result.errors:
            click.echo(f"  ✗ Ошибки: {len(result.errors)}")
            for error in result.errors:
                click.echo(f"    - {error}")
        
    except Exception as e:
        click.echo(f"✗ Ошибка: {e}", err=True)
        logger.exception("Ошибка при генерации тестов")
        sys.exit(1)


@cli.command()
@click.option(
    "--input", "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Путь к JSON файлу с тест-кейсом"
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Путь к YAML файлу с конфигурацией"
)
def validate(
    input: Path,
    config: Optional[Path]
):
    """Валидация тест-кейса без генерации."""
    try:
        # Загрузка конфигурации
        if config:
            gen_config = GenerationConfig.from_yaml(config)
        else:
            gen_config = GenerationConfig()
        
        # Создание генератора
        generator = TestGenerator(config=gen_config)
        
        # Валидация
        report = generator.validate_test_case(input)
        
        if report.is_valid:
            click.echo("✓ Тест-кейс валиден")
        else:
            click.echo("✗ Тест-кейс содержит ошибки:")
            for error in report.errors:
                click.echo(f"  - [{error.code}] {error.message}")
                if error.field:
                    click.echo(f"    Поле: {error.field}")
        
        if report.has_warnings():
            click.echo("\n⚠ Предупреждения:")
            for warning in report.warnings:
                click.echo(f"  - [{warning.code}] {warning.message}")
        
        if report.suggestions:
            click.echo("\n💡 Предложения:")
            for suggestion in report.suggestions:
                click.echo(f"  - {suggestion}")
        
        sys.exit(0 if report.is_valid else 1)
        
    except Exception as e:
        click.echo(f"✗ Ошибка: {e}", err=True)
        logger.exception("Ошибка при валидации")
        sys.exit(1)


@cli.command()
@click.option(
    "--input", "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Директория с JSON файлами тест-кейсов"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default="./generated_tests",
    help="Директория для сохранения сгенерированных тестов"
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Путь к YAML файлу с конфигурацией"
)
@click.option(
    "--pattern", "-p",
    default="*.json",
    help="Паттерн для поиска файлов"
)
@click.option(
    "--workers", "-w",
    type=int,
    help="Количество параллельных воркеров"
)
def batch(
    input: Path,
    output: Path,
    config: Optional[Path],
    pattern: str,
    workers: Optional[int]
):
    """Генерация тестов из всех JSON файлов в директории."""
    try:
        # Загрузка конфигурации
        if config:
            gen_config = GenerationConfig.from_yaml(config)
        else:
            gen_config = GenerationConfig()
        
        # Создание генератора
        generator = TestGenerator(config=gen_config)
        
        click.echo(f"Генерация тестов из директории {input}...")
        
        # Генерация
        results = generator.generate_from_directory(
            directory=input,
            pattern=pattern,
            max_workers=workers
        )
        
        # Сохранение результатов
        success_count = 0
        failed_count = 0
        
        for result in results:
            if result.status == "success":
                result.save_to_directory(output / result.test_case.id)
                success_count += 1
            else:
                failed_count += 1
        
        click.echo(f"\n✓ Успешно сгенерировано: {success_count}")
        if failed_count > 0:
            click.echo(f"✗ Ошибок: {failed_count}")
        
    except Exception as e:
        click.echo(f"✗ Ошибка: {e}", err=True)
        logger.exception("Ошибка при пакетной генерации")
        sys.exit(1)


def main():
    """Точка входа CLI."""
    cli()


if __name__ == "__main__":
    main()


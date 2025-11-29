"""
AgentBender - Library for automatic generation of UI autotests using LLM.

Основной модуль библиотеки для генерации автотестов на основе тест-кейсов
с использованием Large Language Models.
"""

__version__ = "1.0.0"

from agentbender.core.generator import TestGenerator
from agentbender.models.config import (
    GenerationConfig,
    LLMConfig,
    GenerationContext,
    GenerationOptions,
    TestStyle,
)
from agentbender.models.test_case import TestCase, TestStep
from agentbender.models.results import (
    GenerationResult,
    ValidationReport,
    QualityMetrics,
)

__all__ = [
    "TestGenerator",
    "GenerationConfig",
    "LLMConfig",
    "GenerationContext",
    "GenerationOptions",
    "TestStyle",
    "TestCase",
    "TestStep",
    "GenerationResult",
    "ValidationReport",
    "QualityMetrics",
]


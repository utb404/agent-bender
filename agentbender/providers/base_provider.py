"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Iterator, Dict, Any
from datetime import datetime


@dataclass
class ModelInfo:
    """Информация о модели LLM."""
    
    name: str
    provider: str
    max_tokens: Optional[int] = None
    supports_streaming: bool = True
    supports_system_prompt: bool = True
    metadata: Dict[str, Any] = None


@dataclass
class LLMResponse:
    """Ответ от LLM."""
    
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация ответа."""
        return {
            "content": self.content,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata,
        }


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
        pass
    
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
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверка доступности провайдера."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Получение информации о модели."""
        pass


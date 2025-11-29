"""Ollama LLM provider implementation."""

import httpx
from typing import Optional, Iterator
from datetime import datetime
import logging

from agentbender.providers.base_provider import (
    BaseLLMProvider,
    LLMResponse,
    ModelInfo,
)
from agentbender.models.config import LLMConfig


logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Провайдер для Ollama (локальный и удаленный)."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 300,
        api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None
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
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.api_key = api_key
        self.logger = logger or logging.getLogger(__name__)
        self._client = httpx.Client(timeout=timeout)
        self._model_info: Optional[ModelInfo] = None
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Реализация генерации через Ollama API."""
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            if temperature is not None:
                payload["options"] = {
                    "temperature": temperature,
                }
                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens
            
            # Добавление дополнительных параметров
            if kwargs:
                if "options" not in payload:
                    payload["options"] = {}
                payload["options"].update(kwargs)
            
            self.logger.debug(f"Отправка запроса к Ollama: {url}, модель: {self.model}")
            
            response = self._client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            content = data.get("response", "")
            tokens_used = data.get("eval_count")  # Ollama возвращает eval_count как использованные токены
            
            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                finish_reason=data.get("done_reason"),
                metadata={
                    "context": data.get("context"),
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                    "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count"),
                }
            )
        
        except httpx.HTTPError as e:
            self.logger.error(f"Ошибка HTTP при запросе к Ollama: {e}")
            raise LLMConnectionError(f"Ошибка подключения к Ollama: {e}") from e
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при генерации через Ollama: {e}")
            raise LLMError(f"Ошибка генерации: {e}") from e
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """Реализация потоковой генерации."""
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            if temperature is not None:
                payload["options"] = {
                    "temperature": temperature,
                }
                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens
            
            if kwargs:
                if "options" not in payload:
                    payload["options"] = {}
                payload["options"].update(kwargs)
            
            with self._client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    try:
                        import json
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
        
        except httpx.HTTPError as e:
            self.logger.error(f"Ошибка HTTP при потоковом запросе к Ollama: {e}")
            raise LLMConnectionError(f"Ошибка подключения к Ollama: {e}") from e
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при потоковой генерации через Ollama: {e}")
            raise LLMError(f"Ошибка генерации: {e}") from e
    
    def is_available(self) -> bool:
        """Проверка доступности Ollama сервера."""
        try:
            url = f"{self.base_url}/api/tags"
            response = self._client.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_model_info(self) -> ModelInfo:
        """Получение информации о модели Ollama."""
        if self._model_info is None:
            try:
                # Попытка получить информацию о модели
                url = f"{self.base_url}/api/show"
                response = self._client.post(url, json={"name": self.model}, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self._model_info = ModelInfo(
                        name=self.model,
                        provider="ollama",
                        max_tokens=data.get("modelfile", {}).get("num_predict"),
                        supports_streaming=True,
                        supports_system_prompt=True,
                        metadata=data
                    )
                else:
                    # Fallback на базовую информацию
                    self._model_info = ModelInfo(
                        name=self.model,
                        provider="ollama",
                        supports_streaming=True,
                        supports_system_prompt=True,
                    )
            except Exception as e:
                self.logger.warning(f"Не удалось получить информацию о модели: {e}")
                self._model_info = ModelInfo(
                    name=self.model,
                    provider="ollama",
                    supports_streaming=True,
                    supports_system_prompt=True,
                )
        
        return self._model_info
    
    def __del__(self):
        """Закрытие клиента при удалении объекта."""
        if hasattr(self, "_client"):
            try:
                self._client.close()
            except Exception:
                pass


# Исключения для LLM провайдеров
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


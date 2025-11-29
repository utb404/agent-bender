"""Models for test cases."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TestStep(BaseModel):
    """Шаг тест-кейса."""
    
    step_number: Optional[int] = None
    action: str = Field(..., description="Действие (navigate, fill, click, verify и т.д.)")
    target: Optional[str] = Field(None, description="Целевой элемент или URL")
    value: Optional[str] = Field(None, description="Значение для действия (например, текст для fill)")
    description: str = Field(..., description="Описание шага")
    
    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "action": "navigate",
                "target": "url",
                "value": "https://example.com/login",
                "description": "Открыть страницу входа"
            }
        }


class TestCase(BaseModel):
    """Модель тест-кейса."""
    
    id: str = Field(..., description="Уникальный идентификатор тест-кейса")
    title: str = Field(..., description="Название тест-кейса")
    description: str = Field(..., description="Описание тест-кейса")
    steps: List[TestStep] = Field(..., description="Список шагов тест-кейса")
    expected_result: str = Field(..., description="Ожидаемый результат")
    preconditions: Optional[List[str]] = Field(None, description="Предусловия")
    tags: Optional[List[str]] = Field(None, description="Теги тест-кейса")
    priority: Optional[str] = Field(None, description="Приоритет (High, Medium, Low)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "TC-001",
                "title": "Авторизация пользователя",
                "description": "Проверка успешной авторизации пользователя",
                "steps": [
                    {
                        "step_number": 1,
                        "action": "navigate",
                        "target": "url",
                        "value": "https://example.com/login",
                        "description": "Открыть страницу входа"
                    }
                ],
                "expected_result": "Пользователь успешно авторизован",
                "preconditions": ["Пользователь зарегистрирован"],
                "tags": ["authentication", "smoke"],
                "priority": "High"
            }
        }


"""Models for test cases."""

from typing import Optional, List
from pydantic import BaseModel, Field


class TestStep(BaseModel):
    """Шаг тест-кейса с описанием действия на естественном языке.
    
    Формат соответствует test_case.json - шаги содержат только описания действий,
    без явных локаторов и элементов. Локаторы и действия извлекаются через LLM.
    
    Поля action, target, value заполняются автоматически StepGenerator
    и используются только для внутренней генерации кода.
    """
    
    step_number: Optional[int] = None
    id: Optional[str] = Field(None, description="ID шага (альтернативное поле для step_number)")
    name: Optional[str] = Field(None, description="Название шага")
    description: str = Field(..., description="Описание действия на естественном языке")
    expectedResult: Optional[str] = Field(None, description="Ожидаемый результат шага")
    # Поля, заполняемые StepGenerator для генерации кода (не из входного JSON)
    action: Optional[str] = Field(None, description="Действие, извлеченное из описания через LLM")
    target: Optional[str] = Field(None, description="Селектор элемента, извлеченный из описания через LLM")
    value: Optional[str] = Field(None, description="Значение для действия, извлеченное из описания через LLM")
    # Дополнительные поля из исходного формата
    status: Optional[str] = Field(None, description="Статус шага")
    bugLink: Optional[str] = Field(None, description="Ссылка на баг")
    skipReason: Optional[str] = Field(None, description="Причина пропуска")
    attachments: Optional[str] = Field(None, description="Вложения")
    
    @property
    def is_structured(self) -> bool:
        """Проверка, содержит ли шаг структурированные данные (action/target/value)."""
        return self.action is not None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1",
                "name": "Шаг 1",
                "description": "Выполнить действие на странице",
                "expectedResult": "Действие выполнено успешно"
            }
        }


class TestCase(BaseModel):
    """Модель тест-кейса с описаниями действий на естественном языке.
    
    Формат соответствует test_case.json - шаги содержат только описания действий,
    без явных локаторов и элементов.
    """
    
    id: str = Field(..., description="Уникальный идентификатор тест-кейса")
    title: Optional[str] = Field(None, description="Название тест-кейса")
    name: Optional[str] = Field(None, description="Название тест-кейса (альтернативное поле)")
    description: str = Field(..., description="Описание тест-кейса")
    steps: List[TestStep] = Field(..., description="Список шагов тест-кейса")
    expected_result: Optional[str] = Field(None, description="Ожидаемый результат")
    expectedResult: Optional[str] = Field(None, description="Ожидаемый результат (альтернативное поле)")
    preconditions: Optional[List[str]] = Field(None, description="Предусловия")
    preconditions_text: Optional[str] = Field(None, description="Предусловия в виде текста")
    tags: Optional[List[str]] = Field(None, description="Теги тест-кейса")
    tags_text: Optional[str] = Field(None, description="Теги в виде строки")
    priority: Optional[str] = Field(None, description="Приоритет (High, Medium, Low)")
    # Дополнительные поля из исходного формата
    testLayer: Optional[str] = Field(None, description="Слой тестирования")
    severity: Optional[str] = Field(None, description="Серьезность")
    environment: Optional[str] = Field(None, description="Окружение")
    browser: Optional[str] = Field(None, description="Браузер")
    owner: Optional[str] = Field(None, description="Владелец")
    author: Optional[str] = Field(None, description="Автор")
    reviewer: Optional[str] = Field(None, description="Ревьюер")
    testCaseId: Optional[str] = Field(None, description="ID тест-кейса (альтернативное поле)")
    issueLinks: Optional[str] = Field(None, description="Ссылки на задачи")
    testCaseLinks: Optional[str] = Field(None, description="Ссылки на тест-кейсы")
    testType: Optional[str] = Field(None, description="Тип теста")
    epic: Optional[str] = Field(None, description="Эпик")
    feature: Optional[str] = Field(None, description="Фича")
    story: Optional[str] = Field(None, description="История")
    component: Optional[str] = Field(None, description="Компонент")
    
    @property
    def display_title(self) -> str:
        """Получить название тест-кейса (из title или name)."""
        return self.title or self.name or self.id
    
    @property
    def display_expected_result(self) -> str:
        """Получить ожидаемый результат (из expected_result или expectedResult)."""
        return self.expected_result or self.expectedResult or ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "TC001",
                "name": "Пример тест-кейса",
                "description": "Описание тест-кейса",
                "steps": [
                    {
                        "id": "1",
                        "name": "Шаг 1",
                        "description": "Выполнить действие на странице",
                        "expectedResult": "Действие выполнено успешно"
                    }
                ],
                "expectedResult": "Тест-кейс выполнен успешно"
            }
        }


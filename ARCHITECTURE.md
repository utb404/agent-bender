# ARCHITECTURE.md

## Обзор библиотеки

**AgentBender** — библиотека для автоматической генерации автотестов на основе тест-кейсов с применением технологий Large Language Models (LLM). Библиотека предназначена для создания качественных, поддерживаемых и соответствующих корпоративным стандартам автотестов с использованием паттерна Page Object Model и лучших практик автоматизации тестирования.

## Миссия

Генерация автотестов, соответствующих корпоративным шаблонам и лучшим практикам разработки автотестов, с минимальным участием человека в процессе создания тестового кода.

## Целевая аудитория

- QA-инженеры, автоматизирующие тестирование веб-приложений
- Команды разработки, внедряющие практики тест-драйвен разработки
- Организации, требующие стандартизации подходов к автоматизации тестирования

## Технологический стек

### Основные технологии
- **Python 3.9+** — основной язык разработки библиотеки
- **Playwright** — фреймворк для автоматизации браузера
- **@gpn_qa_utils** — корпоративная библиотека утилит для тестирования
- **Ollama** — провайдер LLM (локальный и удаленный)
- **CDP (Chrome DevTools Protocol)** — для расширенной работы с браузером (опционально)

### Зависимости
- `playwright` — автоматизация браузера
- `ollama` — клиент для работы с Ollama API
- `pydantic` — валидация данных и моделей
- `jinja2` — шаблонизация кода
- `pyyaml` — работа с конфигурационными файлами

## Архитектура системы

### Высокоуровневая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentBender Library                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Input      │    │   LLM        │    │   Output     │  │
│  │   Parser     │───▶│   Engine     │───▶│   Generator  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                    │          │
│         │                   │                    │          │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐    │
│  │  Test Case  │    │   Ollama    │    │  Test Code  │    │
│  │  Validator  │    │  Provider   │    │  Formatter  │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Template Engine & Code Generator            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Page Object Model Generator                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         CDP Integration (Optional)                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Компоненты системы

#### 1. Input Parser (Парсер входных данных)
**Ответственность:** Парсинг и валидация JSON тест-кейсов

**Функциональность:**
- Валидация структуры JSON тест-кейсов
- Нормализация данных тест-кейсов
- Извлечение метаданных (приоритет, теги, окружение)
- Поддержка различных форматов тест-кейсов

**Модели данных:**
```python
class TestCase(BaseModel):
    id: str
    title: str
    description: str
    steps: List[TestStep]
    expected_result: str
    preconditions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None

class TestStep(BaseModel):
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    description: str
```

#### 2. LLM Engine (Движок LLM)
**Ответственность:** Взаимодействие с Ollama для генерации кода

**Функциональность:**
- Управление подключением к Ollama (локальное/удаленное)
- Выбор и переключение моделей
- Формирование промптов для генерации кода
- Обработка ответов LLM
- Управление контекстом и историей диалога
- Retry-логика и обработка ошибок

**Конфигурация:**
```python
class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    temperature: float = 0.7
    timeout: int = 300
    max_retries: int = 3
```

#### 3. Template Engine (Движок шаблонов)
**Ответственность:** Генерация кода по корпоративным шаблонам

**Функциональность:**
- Управление шаблонами тестов
- Управление шаблонами Page Object
- Подстановка сгенерированного кода в шаблоны
- Применение корпоративных стандартов форматирования
- Интеграция с @gpn_qa_utils

**Шаблоны:**
- Шаблон тест-класса
- Шаблон Page Object класса
- Шаблон фикстур и конфигурации
- Шаблон вспомогательных утилит

#### 4. Page Object Model Generator (Генератор Page Object)
**Ответственность:** Генерация Page Object классов

**Функциональность:**
- Анализ тест-кейсов для выявления страниц
- Генерация селекторов элементов
- Создание методов взаимодействия с элементами
- Применение паттерна Page Object
- Генерация локаторов с использованием best practices

**Структура Page Object:**
```python
class BasePage:
    """Базовый класс для всех Page Object"""
    
class LoginPage(BasePage):
    """Page Object для страницы входа"""
    # Локаторы
    # Методы взаимодействия
    # Валидационные методы
```

#### 5. Code Generator (Генератор кода)
**Ответственность:** Генерация финального кода автотестов

**Функциональность:**
- Генерация тестовых методов
- Интеграция с Playwright
- Использование @gpn_qa_utils
- Генерация фикстур и конфигурации
- Форматирование кода согласно стандартам

#### 6. CDP Integration (Интеграция CDP)
**Ответственность:** Расширенная работа с браузером через CDP

**Функциональность:**
- Захват сетевых запросов
- Мониторинг производительности
- Анализ DOM для улучшения селекторов
- Генерация более точных локаторов
- Отладка и трассировка действий

**Использование:**
- Опциональный компонент
- Активируется при необходимости
- Улучшает качество генерируемых селекторов

#### 7. Output Formatter (Форматтер вывода)
**Ответственность:** Форматирование и сохранение сгенерированного кода

**Функциональность:**
- Форматирование кода (black, autopep8)
- Структурирование файлов проекта
- Генерация директорий и файлов
- Создание конфигурационных файлов
- Генерация документации

## Структура проекта

```
agentbender/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── parser.py              # Парсер тест-кейсов
│   ├── llm_engine.py          # Движок LLM
│   ├── code_generator.py      # Генератор кода
│   └── validator.py           # Валидатор данных
├── generators/
│   ├── __init__.py
│   ├── test_generator.py      # Генератор тестов
│   ├── page_object_generator.py  # Генератор Page Object
│   └── fixture_generator.py   # Генератор фикстур
├── templates/
│   ├── test_template.py.j2    # Шаблон теста
│   ├── page_object_template.py.j2  # Шаблон Page Object
│   ├── fixture_template.py.j2 # Шаблон фикстур
│   └── config_template.py.j2  # Шаблон конфигурации
├── providers/
│   ├── __init__.py
│   ├── ollama_provider.py     # Провайдер Ollama
│   └── base_provider.py       # Базовый класс провайдера
├── utils/
│   ├── __init__.py
│   ├── cdp_helper.py          # Утилиты CDP
│   ├── formatter.py           # Форматирование кода
│   └── file_manager.py        # Управление файлами
├── models/
│   ├── __init__.py
│   ├── test_case.py           # Модели тест-кейсов
│   └── config.py              # Модели конфигурации
└── cli/
    ├── __init__.py
    └── main.py                # CLI интерфейс
```

## Формат входных данных (JSON тест-кейсы)

### Пример структуры тест-кейса

```json
{
  "test_case": {
    "id": "TC-001",
    "title": "Авторизация пользователя",
    "description": "Проверка успешной авторизации пользователя с валидными данными",
    "priority": "High",
    "tags": ["authentication", "smoke"],
    "preconditions": [
      "Пользователь зарегистрирован в системе",
      "Браузер открыт"
    ],
    "steps": [
      {
        "step_number": 1,
        "action": "navigate",
        "target": "url",
        "value": "https://example.com/login",
        "description": "Открыть страницу входа"
      },
      {
        "step_number": 2,
        "action": "fill",
        "target": "input[name='username']",
        "value": "test_user",
        "description": "Ввести имя пользователя"
      },
      {
        "step_number": 3,
        "action": "fill",
        "target": "input[name='password']",
        "value": "password123",
        "description": "Ввести пароль"
      },
      {
        "step_number": 4,
        "action": "click",
        "target": "button[type='submit']",
        "description": "Нажать кнопку входа"
      },
      {
        "step_number": 5,
        "action": "verify",
        "target": "dashboard",
        "description": "Проверить переход на главную страницу"
      }
    ],
    "expected_result": "Пользователь успешно авторизован и перенаправлен на главную страницу"
  }
}
```

## Формат выходных данных

### Структура генерируемого проекта

```
generated_tests/
├── conftest.py                 # Конфигурация pytest и фикстуры
├── pytest.ini                  # Конфигурация pytest
├── requirements.txt            # Зависимости проекта
├── pages/
│   ├── __init__.py
│   ├── base_page.py           # Базовый Page Object
│   ├── login_page.py          # Page Object для страницы входа
│   └── dashboard_page.py      # Page Object для главной страницы
├── tests/
│   ├── __init__.py
│   ├── test_login.py          # Сгенерированные тесты
│   └── test_dashboard.py
└── utils/
    ├── __init__.py
    └── helpers.py             # Вспомогательные утилиты
```

### Пример сгенерированного теста

```python
import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from gpn_qa_utils import helpers


@pytest.mark.smoke
@pytest.mark.authentication
class TestLogin:
    """Тест-кейс TC-001: Авторизация пользователя"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Подготовка тестового окружения"""
        self.login_page = LoginPage(page)
        self.dashboard_page = DashboardPage(page)
    
    def test_user_authentication(self, page: Page):
        """
        Проверка успешной авторизации пользователя с валидными данными
        
        Предусловия:
        - Пользователь зарегистрирован в системе
        - Браузер открыт
        """
        # Шаг 1: Открыть страницу входа
        self.login_page.navigate()
        
        # Шаг 2: Ввести имя пользователя
        self.login_page.fill_username("test_user")
        
        # Шаг 3: Ввести пароль
        self.login_page.fill_password("password123")
        
        # Шаг 4: Нажать кнопку входа
        self.login_page.click_submit()
        
        # Шаг 5: Проверить переход на главную страницу
        expect(self.dashboard_page.page).to_have_url("https://example.com/dashboard")
        expect(self.dashboard_page.user_menu).to_be_visible()
```

### Пример сгенерированного Page Object

```python
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page Object для страницы входа"""
    
    def __init__(self, page: Page):
        super().__init__(page)
        self.url = "https://example.com/login"
        
        # Локаторы элементов
        self._username_input = page.locator("input[name='username']")
        self._password_input = page.locator("input[name='password']")
        self._submit_button = page.locator("button[type='submit']")
        self._error_message = page.locator(".error-message")
    
    def navigate(self) -> None:
        """Открыть страницу входа"""
        self.page.goto(self.url)
        self.wait_for_page_load()
    
    def fill_username(self, username: str) -> None:
        """Ввести имя пользователя"""
        self._username_input.fill(username)
    
    def fill_password(self, password: str) -> None:
        """Ввести пароль"""
        self._password_input.fill(password)
    
    def click_submit(self) -> None:
        """Нажать кнопку входа"""
        self._submit_button.click()
    
    def is_error_visible(self) -> bool:
        """Проверить наличие сообщения об ошибке"""
        return self._error_message.is_visible()
```

## Принципы и паттерны

### 1. Page Object Model (POM)
- Каждая страница представлена отдельным классом
- Локаторы инкапсулированы в классе
- Методы взаимодействия с элементами вынесены в Page Object
- Базовый класс для общих методов

### 2. Separation of Concerns
- Разделение ответственности между компонентами
- Парсинг, генерация, форматирование — отдельные модули
- Легкая расширяемость и тестируемость

### 3. Template Method Pattern
- Использование шаблонов для генерации кода
- Легкая кастомизация через шаблоны
- Соответствие корпоративным стандартам

### 4. Strategy Pattern
- Различные провайдеры LLM (расширяемость)
- Различные стратегии генерации кода
- Плагинная архитектура

### 5. Builder Pattern
- Пошаговая сборка тестового проекта
- Гибкая конфигурация генерации

## Конфигурация

### Файл конфигурации (config.yaml)

```yaml
ollama:
  base_url: "http://localhost:11434"
  model: "llama3"
  temperature: 0.7
  timeout: 300
  max_retries: 3

generation:
  output_dir: "./generated_tests"
  template_dir: "./templates"
  use_cdp: false
  code_style: "black"
  
templates:
  test_template: "test_template.py.j2"
  page_object_template: "page_object_template.py.j2"
  fixture_template: "fixture_template.py.j2"

gpn_qa_utils:
  enabled: true
  import_path: "from gpn_qa_utils import helpers"

playwright:
  browser: "chromium"
  headless: true
  timeout: 30000
```

## API библиотеки

### Основной интерфейс

```python
from agentbender import TestGenerator, OllamaConfig

# Конфигурация
config = OllamaConfig(
    base_url="http://localhost:11434",
    model="llama3",
    temperature=0.7
)

# Создание генератора
generator = TestGenerator(config=config)

# Генерация тестов из JSON файла
generator.generate_from_file("test_cases.json")

# Генерация тестов из словаря
test_case = {...}  # JSON структура
generator.generate(test_case)

# Генерация с кастомными шаблонами
generator.generate(
    test_case,
    custom_templates={"test": "custom_test.py.j2"}
)
```

### CLI интерфейс

```bash
# Генерация из файла
agentbender generate --input test_cases.json --output ./tests

# Генерация с кастомной конфигурацией
agentbender generate --input test_cases.json --config config.yaml

# Генерация с выбором модели
agentbender generate --input test_cases.json --model llama3:8b

# Генерация с использованием CDP
agentbender generate --input test_cases.json --use-cdp
```

## Обработка ошибок

### Типы ошибок и стратегии обработки

1. **Ошибки парсинга JSON**
   - Валидация структуры
   - Детальные сообщения об ошибках
   - Предложения по исправлению

2. **Ошибки подключения к Ollama**
   - Retry-логика с экспоненциальной задержкой
   - Fallback на локальный Ollama
   - Детальное логирование

3. **Ошибки генерации кода**
   - Валидация сгенерированного кода
   - Повторная генерация при ошибках
   - Частичная генерация при критических ошибках

4. **Ошибки форматирования**
   - Автоматическое исправление синтаксиса
   - Предупреждения о потенциальных проблемах

## Расширяемость

### Плагинная архитектура

Библиотека поддерживает расширение через плагины:

1. **Кастомные провайдеры LLM**
   - Реализация интерфейса `BaseProvider`
   - Интеграция других LLM сервисов

2. **Кастомные генераторы**
   - Расширение функциональности генерации
   - Добавление новых типов тестов

3. **Кастомные шаблоны**
   - Замена стандартных шаблонов
   - Добавление новых шаблонов

### Пример расширения

```python
from agentbender.providers import BaseProvider

class CustomLLMProvider(BaseProvider):
    """Кастомный провайдер LLM"""
    
    def generate_code(self, prompt: str) -> str:
        # Реализация генерации кода
        pass
```

## Тестирование библиотеки

### Стратегия тестирования

1. **Unit-тесты**
   - Тестирование отдельных компонентов
   - Моки для LLM провайдера
   - Тестирование парсеров и валидаторов

2. **Integration-тесты**
   - Тестирование взаимодействия компонентов
   - Тестирование с реальным Ollama (опционально)

3. **E2E тесты**
   - Генерация тестов и проверка их выполнения
   - Валидация качества сгенерированного кода

## Производительность

### Оптимизации

1. **Кэширование**
   - Кэширование промптов
   - Кэширование шаблонов
   - Кэширование сгенерированного кода

2. **Параллелизация**
   - Параллельная генерация нескольких тестов
   - Асинхронная работа с Ollama

3. **Инкрементальная генерация**
   - Генерация только измененных тестов
   - Обновление существующих тестов

## Безопасность

### Меры безопасности

1. **Валидация входных данных**
   - Защита от инъекций в промпты
   - Валидация JSON структуры

2. **Безопасность подключений**
   - Поддержка TLS для удаленных подключений
   - Аутентификация при необходимости

3. **Санитизация кода**
   - Проверка сгенерированного кода на безопасность
   - Удаление потенциально опасных конструкций

## Логирование и мониторинг

### Уровни логирования

- **DEBUG** — детальная информация о процессе генерации
- **INFO** — основные этапы генерации
- **WARNING** — предупреждения о потенциальных проблемах
- **ERROR** — ошибки генерации

### Метрики

- Время генерации теста
- Количество использованных токенов LLM
- Успешность генерации
- Качество сгенерированного кода

## Документация

### Типы документации

1. **API документация**
   - Автогенерация через Sphinx
   - Примеры использования

2. **Руководство пользователя**
   - Пошаговые инструкции
   - Примеры использования

3. **Руководство разработчика**
   - Архитектура библиотеки
   - Инструкции по расширению

## Roadmap

### Версия 1.0 (MVP)
- [x] Базовая генерация тестов из JSON
- [x] Интеграция с Ollama
- [x] Генерация Page Object
- [x] Базовые шаблоны

### Версия 1.1
- [ ] Поддержка нескольких провайдеров LLM
- [ ] Улучшенная генерация селекторов
- [ ] Интеграция CDP
- [ ] Расширенная валидация

### Версия 2.0
- [ ] Поддержка других фреймворков (Selenium, Cypress)
- [ ] Визуальный редактор тест-кейсов
- [ ] Интеграция с системами управления тест-кейсами
- [ ] AI-ассистент для улучшения тестов

## Лицензия

[Указать лицензию]

## Контакты и поддержка

[Контактная информация]


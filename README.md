# AgentBender

Библиотека для автоматической генерации UI-автотестов на основе тест-кейсов с использованием Large Language Models (LLM).

## Описание

AgentBender — это библиотека, которая автоматически генерирует качественные автотесты на Python с использованием Playwright и паттерна Page Object Model на основе JSON тест-кейсов. Библиотека использует LLM (например, Ollama) для генерации кода, соответствующего корпоративным стандартам и лучшим практикам автоматизации тестирования.

## Основные возможности

- 🚀 Автоматическая генерация тестов из JSON тест-кейсов
- 🤖 Интеграция с LLM (Ollama, OpenAI, Anthropic)
- 📄 Генерация Page Object Model классов
- 🎯 Валидация тест-кейсов и сгенерированного кода
- 🔧 Настраиваемые шаблоны и стили кода
- 📦 Генерация фикстур и конфигурационных файлов
- 🎨 Поддержка различных стилей кода (black, autopep8)
- 🔄 Параллельная генерация нескольких тестов
- 📊 Метрики качества сгенерированного кода

## Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd AgentBender

# Установка зависимостей
pip install -r requirements.txt

# Установка библиотеки
pip install -e .
```

## Требования

- Python 3.9+
- Playwright
- Ollama (или другой LLM провайдер)

## Быстрый старт

### 1. Подготовка тест-кейса

Создайте JSON файл с тест-кейсом:

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

### 2. Использование через CLI

```bash
# Базовая генерация
agentbender generate --input test_case.json --output ./generated_tests

# С конфигурацией
agentbender generate \
    --input test_case.json \
    --config config.yaml \
    --output ./generated_tests

# С опциями
agentbender generate \
    --input test_case.json \
    --model llama3:8b \
    --temperature 0.3 \
    --quality high \
    --use-cdp
```

### 3. Использование через Python API

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
    "description": "...",
    "steps": [...],
    "expected_result": "..."
}

result = generator.generate(test_case)

# Сохранение результатов
if result.status == "success":
    output_path = result.save_to_directory("./generated_tests")
    print(f"Тесты сохранены в {output_path}")
```

## Конфигурация

Создайте файл `config.yaml`:

```yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434"
  model: "llama3"
  temperature: 0.7
  timeout: 300
  max_retries: 3

generation:
  output_dir: "./generated_tests"
  code_style: "black"
  use_cdp: false

validation:
  level: "basic"
  validate_syntax: true
  validate_structure: true

performance:
  max_workers: 4
  enable_caching: true
  cache_ttl: 3600

playwright:
  browser: "chromium"
  headless: true
  timeout: 30000
```

## Структура проекта

```
agentbender/
├── __init__.py
├── core/              # Основные компоненты
│   ├── generator.py   # Главный класс TestGenerator
│   ├── parser.py      # Парсер тест-кейсов
│   ├── validator.py   # Валидатор кода
│   └── prompt_builder.py
├── generators/        # Генераторы кода
│   ├── test_generator.py
│   ├── page_object_generator.py
│   └── fixture_generator.py
├── models/            # Модели данных
│   ├── test_case.py
│   ├── config.py
│   └── results.py
├── providers/         # LLM провайдеры
│   ├── base_provider.py
│   └── ollama_provider.py
├── templates/         # Шаблоны Jinja2
│   ├── test_template.py.j2
│   ├── page_object_template.py.j2
│   └── fixture_template.py.j2
├── utils/            # Утилиты
│   ├── formatter.py
│   └── file_manager.py
└── cli/              # CLI интерфейс
    └── main.py
```

## Документация

Подробная документация доступна в файлах:
- `API_DESIGN.md` - Детальное описание API
- `ARCHITECTURE.md` - Архитектура библиотеки

## Лицензия

[Указать лицензию]

## Контакты

[Контактная информация]

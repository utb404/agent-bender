# Быстрый старт AgentBender

## Проект успешно установлен и готов к использованию!

### Активация виртуального окружения

```bash
source venv/bin/activate
```

### Проверка работы

Проверьте, что команда доступна:
```bash
agentbender --help
```

### Генерация тестов

#### 1. Использование примера тест-кейса

В проекте уже есть пример тест-кейса: `example_test_case.json`

Для генерации тестов используйте:
```bash
agentbender generate \
    --input example_test_case.json \
    --output ./generated_tests \
    --config config.yaml
```

#### 2. Использование своего тест-кейса

Создайте JSON файл с тест-кейсом в формате:
```json
{
  "test_case": {
    "id": "TC-001",
    "title": "Название теста",
    "description": "Описание теста",
    "steps": [
      {
        "step_number": 1,
        "action": "navigate",
        "target": "url",
        "value": "https://example.com",
        "description": "Описание шага"
      }
    ],
    "expected_result": "Ожидаемый результат"
  }
}
```

Затем запустите генерацию:
```bash
agentbender generate --input ваш_тест_кейс.json --output ./generated_tests
```

### Валидация тест-кейса

Перед генерацией можно проверить корректность тест-кейса:
```bash
agentbender validate --input example_test_case.json
```

### Пакетная генерация

Для генерации тестов из всех JSON файлов в директории:
```bash
agentbender batch --input ./test_cases_dir --output ./generated_tests
```

### Конфигурация

Проект использует файл `config.yaml` для настройки:
- LLM провайдер (Ollama)
- Модель для генерации
- Параметры генерации
- Настройки валидации

Убедитесь, что Ollama сервер доступен по адресу, указанному в `config.yaml`.

### Результаты

Сгенерированные тесты будут сохранены в указанную директорию со следующей структурой:
```
generated_tests/
├── tests/
│   └── test_tc_001.py
├── pages/
│   └── *.py (Page Objects)
├── conftest.py
└── другие конфигурационные файлы
```


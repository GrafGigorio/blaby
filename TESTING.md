# Testing Guidelines

Руководство по тестированию проекта Voice AI Assistant.

## Типы тестов

### 1. Unit Tests (Модульные тесты)

Тестирование отдельных модулей и функций.

**Что тестировать**:
- Функции модулей (STT, LLM, TTS)
- Вспомогательные функции
- Валидация входных данных
- Обработка ошибок

**Примеры**:
- `test_stt_module.py`: Тестирование распознавания речи
- `test_llm_module.py`: Тестирование генерации ответов
- `test_tts_module.py`: Тестирование синтеза речи
- `test_state_manager.py`: Тестирование управления состояниями

### 2. Integration Tests (Интеграционные тесты)

Тестирование взаимодействия между модулями.

**Что тестировать**:
- Интеграция STT → LLM → TTS
- API endpoints
- WebSocket соединения
- Работа с файловой системой

### 3. End-to-End Tests (E2E тесты)

Тестирование полного потока приложения.

**Что тестировать**:
- Полный цикл голосового диалога
- Взаимодействие через веб-интерфейс
- Работа с браузером

## Настройка тестового окружения

### Установка зависимостей для тестирования

```bash
pip install pytest pytest-asyncio pytest-cov
pip install httpx  # Для тестирования FastAPI
```

### Структура тестов

```
tests/
├── __init__.py
├── conftest.py          # Конфигурация pytest
├── unit/
│   ├── test_stt_module.py
│   ├── test_llm_module.py
│   ├── test_tts_module.py
│   └── test_state_manager.py
├── integration/
│   ├── test_api.py
│   ├── test_websocket.py
│   └── test_pipeline.py
└── e2e/
    └── test_full_dialog.py
```

### pytest.ini

Создайте `pytest.ini` в корне проекта:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

## Unit Tests

### Тестирование STT Module

```python
# tests/unit/test_stt_module.py
import pytest
from pathlib import Path
from stt_module import STTModule

@pytest.fixture
def stt_module():
    """Фикстура для STT модуля"""
    return STTModule(model_size="tiny")  # Используем tiny для быстрых тестов

def test_transcribe_existing_file(stt_module, tmp_path):
    """Тест распознавания речи из существующего файла"""
    # Создаем тестовый аудио файл (нужен реальный файл)
    audio_path = tmp_path / "test.wav"
    # ... создание или копирование тестового файла ...
    
    result = stt_module.transcribe(str(audio_path), language="ru")
    assert result is not None
    assert isinstance(result, str)

def test_transcribe_nonexistent_file(stt_module):
    """Тест обработки несуществующего файла"""
    result = stt_module.transcribe("nonexistent.wav", language="ru")
    assert result == ""  # Должен вернуть пустую строку при ошибке
```

### Тестирование LLM Module

```python
# tests/unit/test_llm_module.py
import pytest
from llm_module import LLMModule

@pytest.fixture
def llm_module():
    """Фикстура для LLM модуля"""
    return LLMModule(model_name="gpt-oss:20b")

def test_generate_response(llm_module):
    """Тест генерации ответа"""
    response = llm_module.generate_response("Привет", system_prompt="Ты помощник")
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_history_management(llm_module):
    """Тест управления историей"""
    assert len(llm_module.conversation_history) == 0
    
    llm_module.generate_response("Первое сообщение")
    assert len(llm_module.conversation_history) == 2  # user + assistant
    
    llm_module.clear_history()
    assert len(llm_module.conversation_history) == 0

def test_history_limit(llm_module):
    """Тест ограничения истории (10 сообщений)"""
    for i in range(15):
        llm_module.generate_response(f"Сообщение {i}")
    
    # История должна содержать только последние 10 сообщений
    assert len(llm_module.conversation_history) <= 12  # 10 + 2 последних
```

### Тестирование State Manager

```python
# tests/unit/test_state_manager.py
import pytest
from state_manager import StateManager, DialogState

@pytest.fixture
def state_manager():
    return StateManager()

def test_initial_state(state_manager):
    """Тест начального состояния"""
    assert state_manager.current_state == DialogState.IDLE

def test_state_transitions(state_manager):
    """Тест переходов состояний"""
    state_manager.start_listening()
    assert state_manager.current_state == DialogState.LISTENING
    
    state_manager.start_processing()
    assert state_manager.current_state == DialogState.PROCESSING
    
    state_manager.start_speaking()
    assert state_manager.current_state == DialogState.SPEAKING

def test_can_interrupt(state_manager):
    """Тест возможности прерывания"""
    state_manager.start_speaking()
    assert state_manager.can_interrupt() == True
    
    state_manager.start_listening()
    assert state_manager.can_interrupt() == False

def test_transcript_update(state_manager):
    """Тест обновления транскрипции"""
    state_manager.update_transcript("Привет", is_partial=True)
    assert state_manager.get_current_transcript() == "Привет"
    
    state_manager.update_transcript("Привет мир", is_partial=False)
    assert state_manager.get_current_transcript() == "Привет мир"
```

### Тестирование TTS Module

```python
# tests/unit/test_tts_module.py
import pytest
import asyncio
from pathlib import Path
from tts_module import TTSModule

@pytest.fixture
def tts_module():
    return TTSModule()

@pytest.mark.asyncio
async def test_synthesize_async(tts_module, tmp_path):
    """Тест асинхронного синтеза речи"""
    output_path = tmp_path / "test_output.wav"
    result = await tts_module.synthesize_async(
        "Привет мир",
        str(output_path),
        language="ru"
    )
    assert result == True
    assert output_path.exists()
```

## Integration Tests

### Тестирование API Endpoints

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Тест главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_clear_history_endpoint():
    """Тест очистки истории"""
    response = client.post("/api/clear-history")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_voice_chat_endpoint(tmp_path):
    """Тест голосового чата (требует реальный аудио файл)"""
    # Создаем тестовый аудио файл
    test_audio = tmp_path / "test.wav"
    # ... создание или копирование тестового файла ...
    
    with open(test_audio, "rb") as f:
        response = client.post(
            "/api/voice-chat",
            files={"audio": f}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "user_text" in data
    assert "ai_response" in data
    assert "audio_url" in data
```

### Тестирование WebSocket

```python
# tests/integration/test_websocket.py
import pytest
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_websocket_connection():
    """Тест WebSocket соединения"""
    with client.websocket_connect("/ws/voice") as websocket:
        # Отправка start_listening
        websocket.send_json({"type": "start_listening"})
        
        # Получение ответа
        data = websocket.receive_json()
        assert data["type"] == "state"
        assert data["state"] == "listening"

def test_websocket_audio_chunk():
    """Тест отправки аудио чанка"""
    with client.websocket_connect("/ws/voice") as websocket:
        websocket.send_json({"type": "start_listening"})
        websocket.receive_json()  # Пропускаем state
        
        # Отправка тестового аудио чанка
        import base64
        test_audio = b"\x00" * 1024  # Тестовые данные
        base64_audio = base64.b64encode(test_audio).decode()
        
        websocket.send_json({
            "type": "audio_chunk",
            "data": base64_audio
        })
        
        # Можем получить partial_transcript или ничего
        # (зависит от качества тестового аудио)
```

## E2E Tests

### Использование Playwright

```python
# tests/e2e/test_full_dialog.py
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(scope="session")
def app_url():
    return "http://localhost:8000"

def test_page_loads(page: Page, app_url):
    """Тест загрузки страницы"""
    page.goto(app_url)
    expect(page.locator("h1")).to_contain_text("Голосовой Ассистент")

def test_start_dialog_button(page: Page, app_url):
    """Тест кнопки начала диалога"""
    page.goto(app_url)
    button = page.locator("button.start-btn")
    expect(button).to_be_visible()
    
    button.click()
    # Проверяем изменение состояния
    status = page.locator("#status")
    expect(status).to_contain_text("Слушаю")

def test_websocket_connection(page: Page, app_url):
    """Тест WebSocket соединения"""
    page.goto(app_url)
    
    # Открываем консоль браузера для проверки
    page.on("console", lambda msg: print(f"Console: {msg.text}"))
    
    # Нажимаем кнопку начала диалога
    page.locator("button.start-btn").click()
    
    # Ждем изменения состояния
    status = page.locator("#status")
    expect(status).to_contain_text("Слушаю", timeout=5000)
```

## Запуск тестов

### Запуск всех тестов

```bash
pytest
```

### Запуск с покрытием

```bash
pytest --cov=. --cov-report=html
```

### Запуск конкретного теста

```bash
pytest tests/unit/test_stt_module.py
```

### Запуск с подробным выводом

```bash
pytest -v
```

### Запуск асинхронных тестов

```bash
pytest --asyncio-mode=auto
```

## Тестовые данные

### Подготовка тестовых аудио файлов

1. Создайте директорию `tests/fixtures/`
2. Добавьте минимальные тестовые WAV файлы
3. Убедитесь, что файлы не слишком большие

### Мокирование

Для тестов, которые не требуют реальных моделей:

```python
from unittest.mock import Mock, patch

@patch('stt_module.whisper.load_model')
def test_stt_module_with_mock(mock_load_model):
    """Тест с мокированием Whisper модели"""
    mock_model = Mock()
    mock_model.transcribe.return_value = {"text": "Тестовый текст"}
    mock_load_model.return_value = mock_model
    
    stt = STTModule(model_size="tiny")
    result = stt.transcribe("test.wav", language="ru")
    assert result == "Тестовый текст"
```

## Continuous Integration

### GitHub Actions пример

Создайте `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

### 1. Изоляция тестов

- Каждый тест должен быть независимым
- Используйте фикстуры для подготовки данных
- Очищайте состояние после каждого теста

### 2. Использование фикстур

```python
@pytest.fixture(autouse=True)
def setup_test_environment(tmp_path):
    """Автоматическая настройка тестового окружения"""
    # Настройка
    yield
    # Очистка
```

### 3. Параметризация тестов

```python
@pytest.mark.parametrize("model_size", ["tiny", "base", "small"])
def test_different_models(model_size):
    stt = STTModule(model_size=model_size)
    # Тест с разными моделями
```

### 4. Тестирование граничных случаев

- Пустые входные данные
- Очень длинные входные данные
- Невалидные форматы файлов
- Ошибки сети

### 5. Тестирование производительности

```python
import time

def test_performance():
    start = time.time()
    # Выполнение операции
    result = expensive_operation()
    duration = time.time() - start
    assert duration < 5.0  # Должно выполняться менее 5 секунд
```

## Checklist для тестирования

- [ ] Unit тесты для всех модулей
- [ ] Интеграционные тесты для API
- [ ] Тесты обработки ошибок
- [ ] Тесты граничных случаев
- [ ] E2E тесты основных сценариев
- [ ] Тесты производительности (при необходимости)
- [ ] Покрытие кода > 70%
- [ ] Все тесты проходят перед коммитом

## Отладка тестов

### Вывод отладочной информации

```bash
pytest -s  # Вывод print statements
pytest -v  # Подробный вывод
pytest --pdb  # Запуск отладчика при ошибке
```

### Логирование в тестах

```python
import logging

def test_with_logging(caplog):
    with caplog.at_level(logging.INFO):
        # Код теста
        pass
    assert "expected message" in caplog.text
```

## Дополнительные ресурсы

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Playwright Documentation](https://playwright.dev/python/)


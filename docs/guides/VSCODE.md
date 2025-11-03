# Руководство по VS Code для разработки проекта

Полное руководство по настройке и использованию Visual Studio Code для разработки голосового ассистента.

## Быстрый старт

1. Откройте проект в VS Code
2. Установите рекомендуемые расширения (появится уведомление)
3. Выберите интерпретатор Python: `./venv/bin/python`
4. Нажмите `F5` для запуска отладки

## Конфигурации отладки

Нажмите `F5` или выберите `Run and Debug` на боковой панели.

### 🔥 FastAPI: Development (Auto-reload) [РЕКОМЕНДУЕТСЯ]

**Главная конфигурация для разработки.**

- Автоматическая перезагрузка при изменении кода
- Debug logging (подробные логи)
- Порт: 8000
- Можно ставить breakpoints в любом месте кода

**Использование:**
1. Нажмите `F5`
2. Выберите эту конфигурацию
3. Откройте http://localhost:8000
4. Изменяйте код - сервер перезагрузится автоматически

**Breakpoints работают в:**
- `main.py` - основной код приложения
- `api/*.py` - API endpoints
- `core/*.py` - модули STT, LLM, TTS
- `utils/*.py` - утилиты

### 🚀 FastAPI: Production Mode

Запуск без auto-reload (как в продакшене).

**Когда использовать:**
- Тестирование производительности
- Проверка поведения без перезагрузок
- Финальное тестирование перед деплоем

### 🧪 Test: Whisper STT Module

Отладка модуля распознавания речи Whisper.

**Требует:** файл `test_stt.py` в корне проекта

**Пример test_stt.py:**
```python
from core.stt_module import STTModule
from config import DEFAULT_STT_MODEL

stt = STTModule(model_size=DEFAULT_STT_MODEL)
audio_file = "uploads/input_test.wav"
text = stt.transcribe(audio_file, language="ru")
print(f"Распознанный текст: {text}")
```

### 🧪 Test: LLM Module

Отладка модуля языковой модели.

**Пример test_llm.py:**
```python
from core.llm_module import LLMModule
from config import DEFAULT_LLM_MODEL

llm = LLMModule(model_name=DEFAULT_LLM_MODEL)
response = llm.generate_response("Привет, как дела?")
print(f"Ответ LLM: {response}")
```

### 🧪 Test: TTS Module

Отладка модуля синтеза речи.

**Пример test_tts.py:**
```python
import asyncio
from core.tts_module import TTSModule

async def test():
    tts = TTSModule()
    await tts.synthesize_async(
        "Привет мир",
        "outputs/test_output.wav",
        language="ru"
    )
    print("TTS завершен: outputs/test_output.wav")

asyncio.run(test())
```

### 🐛 Debug: Current File

Отладка текущего открытого файла.

**Использование:**
1. Откройте любой Python файл
2. Нажмите `F5`
3. Выберите эту конфигурацию

### 📡 FastAPI: Port 8080

Запуск на альтернативном порту 8080.

**Когда использовать:**
- Порт 8000 занят другим приложением
- Запуск нескольких экземпляров

## Задачи (Tasks)

Нажмите `Cmd+Shift+P` (Mac) или `Ctrl+Shift+P` (Windows/Linux), введите "Tasks: Run Task"

### 🚀 Start FastAPI Server

Запустить FastAPI сервер без отладки.

```bash
python main.py
```

### 🔥 Start FastAPI with Auto-reload

Запустить с auto-reload через uvicorn.

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 📥 Install Vosk Model (Full)

Установить полную модель Vosk для лучшего качества.

```bash
./install_vosk.sh
```

### 📦 Install Python Dependencies

Установить все зависимости из requirements.txt.

```bash
pip install -r requirements.txt
```

### 🧹 Clean Python Cache

Очистить кеш Python (__pycache__, *.pyc).

```bash
find . -type d -name '__pycache__' -exec rm -rf {} +
```

### 🧪 Run All Tests

Запустить все тесты с pytest.

```bash
pytest -v
```

### 🎨 Format Code with Black

Отформатировать весь код с помощью Black.

```bash
black .
```

### ✅ Check Code with Flake8

Проверить код на ошибки стиля.

```bash
flake8 . --max-line-length=120
```

### 🔍 Check Ollama Status

Проверить статус Ollama.

```bash
ollama list && pgrep -x ollama
```

### 🚀 Start Ollama

Запустить Ollama server.

```bash
ollama serve
```

### 📊 Check Project Status

Проверить статус всего проекта (Python, пакеты, модели, Ollama).

### 🗑️ Clean Audio Files

Удалить все аудио файлы из uploads/ и outputs/.

```bash
rm -f uploads/*.wav && rm -f outputs/*.wav
```

## Настройки проекта

### Python Analysis

Настроены пути для автокомплита и импортов:
```json
"python.analysis.extraPaths": [
    "${workspaceFolder}",
    "${workspaceFolder}/api",
    "${workspaceFolder}/core",
    "${workspaceFolder}/utils"
]
```

**Что это даёт:**
- IntelliSense для всех модулей
- Автокомплит импортов
- Переход к определениям (F12)

### Форматирование

- **Инструмент:** Black
- **Длина строки:** 120 символов
- **Автоформатирование:** При сохранении (Cmd+S)

**Настройка:**
```json
"python.formatting.provider": "black",
"python.formatting.blackArgs": ["--line-length=120"],
"editor.formatOnSave": true
```

### Линтинг

- **Инструмент:** Flake8
- **Правила:** Максимальная длина строки 120, игнорируем E203, W503

**Установка:**
```bash
pip install flake8 black
```

### Исключения из поиска

Следующие директории исключены из поиска для ускорения:
- `__pycache__`
- `venv`
- `models` (большие ML модели)
- `uploads` (временные аудио)
- `outputs` (сгенерированные аудио)

## Горячие клавиши

### Отладка

| Клавиша | Действие |
|---------|----------|
| `F5` | Запустить отладку |
| `Shift+F5` | Остановить отладку |
| `Cmd/Ctrl+Shift+F5` | Перезапустить отладку |
| `F9` | Поставить/убрать breakpoint |
| `F10` | Шаг через (step over) |
| `F11` | Шаг в функцию (step into) |
| `Shift+F11` | Выйти из функции (step out) |

### Редактирование

| Клавиша | Действие |
|---------|----------|
| `Cmd/Ctrl+S` | Сохранить и отформатировать |
| `Cmd/Ctrl+Shift+P` | Палитра команд |
| `Cmd/Ctrl+P` | Быстрый поиск файла |
| `Cmd/Ctrl+Shift+F` | Поиск по всему проекту |
| `F12` | Перейти к определению |
| `Alt+F12` | Посмотреть определение |
| `Shift+F12` | Найти все использования |

### Терминал

| Клавиша | Действие |
|---------|----------|
| `Ctrl+`` | Открыть/закрыть терминал |
| `Cmd/Ctrl+Shift+`` | Создать новый терминал |

## Рекомендуемые расширения

### Обязательные

1. **Python** (ms-python.python) - Основное расширение Python
2. **Pylance** (ms-python.vscode-pylance) - Быстрый language server
3. **Black Formatter** (ms-python.black-formatter) - Форматирование кода

### Полезные

4. **GitLens** (eamodio.gitlens) - Расширенная работа с Git
5. **Thunder Client** (rangav.vscode-thunder-client) - Тестирование API
6. **Error Lens** (usernamehw.errorlens) - Показ ошибок прямо в коде
7. **TODO Highlight** (wayou.vscode-todo-highlight) - Подсветка TODO

### Опциональные

8. **GitHub Copilot** (github.copilot) - AI-помощник в написании кода
9. **Material Icon Theme** (PKief.material-icon-theme) - Красивые иконки файлов

**Установка:**
VS Code предложит установить рекомендуемые расширения при открытии проекта.

## Типичные задачи

### Запустить проект для разработки

1. Откройте проект в VS Code
2. Нажмите `F5`
3. Выберите "🔥 FastAPI: Development (Auto-reload)"
4. Откройте http://localhost:8000

### Отладить конкретный endpoint

1. Откройте файл с endpoint (например, `api/voice_chat.py`)
2. Поставьте breakpoint (клик слева от номера строки)
3. Запустите отладку (`F5`)
4. Сделайте запрос к endpoint (через браузер или Thunder Client)
5. VS Code остановится на breakpoint

### Отладить модуль STT/LLM/TTS

1. Создайте тестовый файл (например, `test_stt.py`)
2. Напишите тестовый код
3. Поставьте breakpoints
4. Выберите конфигурацию "🧪 Test: Whisper STT Module"
5. Нажмите `F5`

### Проверить код перед коммитом

```bash
# Запустите задачи по очереди
Tasks: Run Task → 🎨 Format Code with Black
Tasks: Run Task → ✅ Check Code with Flake8
Tasks: Run Task → 🧪 Run All Tests
```

### Очистить проект

```bash
Tasks: Run Task → 🧹 Clean Python Cache
Tasks: Run Task → 🗑️ Clean Audio Files
```

## Troubleshooting

### Проблема: Импорты не работают

**Решение:**
1. Проверьте, что выбран правильный интерпретатор: `./venv/bin/python`
2. Перезагрузите VS Code: `Cmd/Ctrl+Shift+P` → "Developer: Reload Window"
3. Проверьте PYTHONPATH в терминале: `echo $PYTHONPATH`

### Проблема: Breakpoints не срабатывают

**Решение:**
1. Убедитесь, что запущена конфигурация с отладкой (не задача)
2. Проверьте, что `justMyCode: false` в launch.json
3. Перезапустите отладку (`Shift+F5`, затем `F5`)

### Проблема: Auto-reload не работает

**Решение:**
1. Используйте конфигурацию "🔥 FastAPI: Development (Auto-reload)"
2. Проверьте, что используется uvicorn с флагом `--reload`
3. Проверьте, что файлы сохраняются (`Cmd/Ctrl+S`)

### Проблема: Форматирование не работает при сохранении

**Решение:**
1. Установите Black: `pip install black`
2. Установите расширение "Black Formatter"
3. Проверьте настройку: `"editor.formatOnSave": true`

## Дополнительные ресурсы

- [Официальная документация VS Code Python](https://code.visualstudio.com/docs/python/python-tutorial)
- [Отладка в VS Code](https://code.visualstudio.com/docs/editor/debugging)
- [Tasks в VS Code](https://code.visualstudio.com/docs/editor/tasks)

## Полезные команды из палитры

Нажмите `Cmd/Ctrl+Shift+P` и введите:

- "Python: Select Interpreter" - Выбрать интерпретатор Python
- "Developer: Reload Window" - Перезагрузить VS Code
- "Preferences: Open Settings (JSON)" - Открыть настройки JSON
- "Tasks: Run Task" - Запустить задачу
- "Git: Clone" - Клонировать репозиторий
- "Terminal: Create New Terminal" - Создать новый терминал

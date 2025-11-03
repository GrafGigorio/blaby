# Voice AI Assistant

Локальный голосовой ассистент с использованием Ollama (gpt-oss:20b).

## Компоненты

- **STT:** OpenAI Whisper `medium` (высокое качество) + Vosk (потоковое распознавание)
- **LLM:** Ollama (gpt-oss:20b)
- **TTS:** Microsoft Edge TTS
- **Backend:** FastAPI
- **Frontend:** HTML/JavaScript

### Качество распознавания речи

Проект настроен для максимального качества распознавания:
- **Whisper medium** - точность ~98% на русском языке
- **Vosk full model** - распознавание в реальном времени с высокой точностью

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. **Установите Vosk модель для потокового распознавания:**
```bash
./install_vosk.sh
```
   Или скачайте вручную: см. [INSTALL_VOSK.md](INSTALL_VOSK.md)

3. Убедитесь, что Ollama запущена:
```bash
ollama serve
```

4. Запустите приложение:
```bash
python main.py
```

5. Откройте браузер: http://localhost:8000

**Примечание:** Whisper модель скачается автоматически при первом запуске.

## Использование

1. Нажмите кнопку микрофона
2. Говорите свой вопрос
3. Получите голосовой ответ от AI

## Разработка в VS Code

Проект полностью настроен для работы в VS Code:

### Быстрый старт отладки
1. Откройте проект в VS Code
2. Нажмите `F5`
3. Выберите: **🔥 FastAPI: Development (Auto-reload) [РЕКОМЕНДУЕТСЯ]**
4. Откройте http://localhost:8000

### Доступные конфигурации отладки
- 🔥 **Development (Auto-reload)** - Основная для разработки с авто-перезагрузкой
- 🚀 **Production Mode** - Режим без авто-перезагрузки
- 🧪 **Test Modules** - Отладка отдельных модулей (STT, LLM, TTS)
- 🐛 **Debug Current File** - Отладка текущего файла

### Задачи (Tasks)
Нажмите `Cmd/Ctrl+Shift+P` → "Tasks: Run Task"
- 🚀 Start FastAPI Server
- 📥 Install Vosk Model
- 🧹 Clean Python Cache
- 🎨 Format Code with Black
- И многое другое...

### Полное руководство
📖 **[VS Code Guide](docs/guides/VSCODE.md)** - Подробное руководство по отладке, задачам, горячим клавишам и настройкам

## Документация

### Быстрый старт
- **[Быстрый старт](docs/guides/QUICKSTART.md)** - Как быстро запустить проект
- **[Установка](docs/guides/SETUP.md)** - Подробная инструкция по установке и настройке
- **[Настройка STT моделей](docs/guides/STT_MODELS.md)** - Руководство по улучшению качества распознавания речи

### Архитектура и API
- **[Обзор проекта](docs/PROJECT_SUMMARY.md)** - Общее описание проекта и компонентов
- **[Архитектура](docs/architecture/ARCHITECTURE.md)** - Детальное описание архитектуры системы
- **[API Documentation](api/README.md)** - Документация REST и WebSocket API endpoints

### Разработка и тестирование
- **[VS Code Guide](docs/guides/VSCODE.md)** - Полное руководство по разработке в VS Code (отладка, задачи, горячие клавиши)
- **[Руководство разработчика](docs/guides/DEVELOPMENT.md)** - Правила разработки и лучшие практики
- **[Внесение вклада](docs/guides/CONTRIBUTING.md)** - Руководство по внесению вклада
- **[Тестирование](docs/testing/TESTING.md)** - Руководство по тестированию
- **[Руководство по рефакторингу](docs/guides/REFACTORING_GUIDE.md)** - Процесс рефакторинга кода

### Модули
- **[Core Modules](core/README.md)** - Документация основных модулей (STT, LLM, TTS)
- **[Utils](utils/README.md)** - Документация вспомогательных утилит

### Для AI-ассистентов
- **[CLAUDE.md](CLAUDE.md)** - Инструкции для Claude Code

### Полная документация
- **[docs/](docs/)** - Вся документация проекта

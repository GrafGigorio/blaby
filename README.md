# Voice AI Assistant

Локальный голосовой ассистент с использованием Ollama (gpt-oss:20b).

## Компоненты

- **STT:** OpenAI Whisper (локально) + Vosk (для потокового распознавания)
- **LLM:** Ollama (gpt-oss:20b)
- **TTS:** Microsoft Edge TTS
- **Backend:** FastAPI
- **Frontend:** HTML/JavaScript

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Убедитесь, что Ollama запущена:
```bash
ollama serve
```

3. Запустите приложение:
```bash
python main.py
```

4. Откройте браузер: http://localhost:8000

## Использование

1. Нажмите кнопку микрофона
2. Говорите свой вопрос
3. Получите голосовой ответ от AI

## Отладка в VS Code

Проект настроен для отладки в VS Code:
- Нажмите `F5` для запуска отладки
- Выберите конфигурацию: "Python: FastAPI with Uvicorn" (с auto-reload)
- Установите breakpoints в любом месте кода

Подробности см. в [DEVELOPMENT.md](DEVELOPMENT.md#отладка-в-vs-code)

## Документация

- **[SETUP.md](SETUP.md)** - Подробная инструкция по установке и настройке
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Обзор проекта и всех компонентов
- **[API.md](API.md)** - Документация API endpoints и WebSocket протокола
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Детальное описание архитектуры системы
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Правила разработки и лучшие практики
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Руководство по внесению вклада
- **[TESTING.md](TESTING.md)** - Руководство по тестированию
- **[CLAUDE.md](CLAUDE.md)** - Документация для AI-ассистентов (Claude Code)

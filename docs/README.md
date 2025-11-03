# Документация проекта blaBy

Полная документация голосового AI ассистента.

## Обзор проекта

- [Сводка проекта](PROJECT_SUMMARY.md) - Подробное описание проекта

## Быстрый старт

- [Быстрый старт](guides/QUICKSTART.md) - Как быстро запустить проект
- [Установка и настройка](guides/SETUP.md) - Детальная инструкция по установке

## Архитектура

- [Архитектура системы](architecture/ARCHITECTURE.md) - Описание архитектуры и компонентов

## Руководства разработчика

- [Руководство по разработке](guides/DEVELOPMENT.md) - Инструкции для разработчиков
- [Руководство по рефакторингу](guides/REFACTORING_GUIDE.md) - Процесс рефакторинга кода
- [Руководство по внесению вклада](guides/CONTRIBUTING.md) - Как участвовать в разработке

## Тестирование

- [Тестирование](testing/TESTING.md) - Общая информация о тестировании
- [Руководство по тестированию](testing/TESTING_GUIDE.md) - Детальное руководство по тестам

## Документация модулей

- [API Endpoints](../api/README.md) - Документация REST и WebSocket API
- [Core Modules](../core/README.md) - Документация основных модулей (STT, LLM, TTS)
- [Utils](../utils/README.md) - Документация вспомогательных модулей

## Структура проекта

```
blaBy/
├── api/           # REST и WebSocket API endpoints
├── core/          # Основные модули (STT, LLM, TTS, Actions)
├── utils/         # Вспомогательные утилиты
├── static/        # Веб-интерфейс
├── docs/          # Вся документация проекта
│   ├── architecture/  # Архитектурная документация
│   ├── guides/        # Руководства для разработчиков
│   └── testing/       # Документация по тестированию
├── main.py        # Точка входа FastAPI приложения
└── config.py      # Конфигурация приложения
```

## Технологии

- **Backend**: FastAPI (Python)
- **STT**: OpenAI Whisper (локально)
- **LLM**: Ollama (локально)
- **TTS**: Microsoft Edge TTS
- **Frontend**: Vanilla HTML/JavaScript + Web Audio API

## Полезные ссылки

- [README](../README.md) - Главная страница проекта
- [Claude Instructions](../CLAUDE.md) - Инструкции для Claude Code

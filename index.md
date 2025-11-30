# Voice AI Assistant

## Обзор

Локальный голосовой ассистент для разговорного взаимодействия с AI. Работает офлайн (кроме Edge TTS). Пользователь говорит вопрос — получает голосовой ответ.

**Стек**: FastAPI + Whisper/Vosk + Ollama + Edge TTS

## Быстрый старт

```bash
# Установка
pip install -r requirements.txt
./install_vosk.sh

# Запуск Ollama
ollama serve

# Запуск приложения
python main.py
# Откройте http://localhost:8000
```

## Модули

- [Core](docs/core/index.md) — STT, LLM, TTS, State Manager
- [API](docs/api/index.md) — REST и WebSocket endpoints
- [Utils](docs/utils/index.md) — вспомогательные утилиты

## Конфигурация

| Параметр | Файл | Описание |
|----------|------|----------|
| Whisper модель | `config.py` | tiny/base/small/medium/large |
| LLM модель | `config.py` | любая из `ollama list` |
| TTS голос | `core/tts_module.py` | Edge TTS голос |
| Системный промпт | `main.py` | поведение ассистента |

## Архитектура

```
Browser → FastAPI → STT → LLM → TTS → Audio Response
              ↓
         WebSocket (потоковый режим)
              ↓
         Vosk (realtime STT)
```

**Детали**: [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)

## Структура проекта

```
blaBy/
├── main.py          # FastAPI приложение
├── config.py        # Конфигурация
├── core/            # Основные модули
├── api/             # API endpoints
├── utils/           # Утилиты
├── static/          # Web интерфейс
├── docs/            # Документация
└── start.sh         # Скрипт запуска
```

## Требования

- Python 3.8+
- 8GB RAM минимум
- Ollama (запущен)
- Интернет для Edge TTS

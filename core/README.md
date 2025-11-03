# Core Modules

Основные модули системы голосового ассистента.

## Модули

### action_manager.py
Управление действиями и командами ассистента.
- Обработка специальных команд (подключение к интернету, управление системой)
- Интеграция с внешними сервисами

### llm_module.py
Интеграция с языковой моделью (Ollama).
- Генерация ответов с использованием локальной LLM
- Управление контекстом беседы
- Поддержка истории сообщений

### state_manager.py
Управление состоянием приложения.
- Отслеживание текущего состояния ассистента
- Координация между модулями

### stt_module.py
Распознавание речи (Speech-to-Text) с использованием Whisper.
- Использует OpenAI Whisper для локального распознавания
- Поддержка нескольких языков
- Автоматическое определение доступных ресурсов (CUDA/CPU)
- **Текущая модель:** medium (для лучшего качества)

### stt_streaming_module.py
Потоковое распознавание речи в реальном времени с использованием Vosk.
- WebSocket интеграция для стриминга аудио
- Низкая задержка обработки
- Continuous speech recognition
- **Рекомендуемая модель:** vosk-model-ru-0.42 (1.5 ГБ) для лучшего качества

**📖 Подробное руководство по настройке STT моделей:** [docs/guides/STT_MODELS.md](../../docs/guides/STT_MODELS.md)

### tts_module.py
Синтез речи (Text-to-Speech).
- Использует Microsoft Edge TTS
- Поддержка нескольких языков и голосов
- Асинхронная генерация аудио

## Использование

Все модули инициализируются при запуске приложения и доступны через глобальные переменные в `main.py`.

```python
from core.stt_module import STTModule
from core.llm_module import LLMModule
from core.tts_module import TTSModule

# Инициализация
stt = STTModule(model_size="medium")  # Используем medium для лучшего качества
llm = LLMModule(model_name="gpt-oss:20b")
tts = TTSModule()

# Использование
text = stt.transcribe("audio.wav", language="ru")
response = llm.generate_response(text)
await tts.synthesize_async(response, "output.wav", language="ru")
```

## Зависимости

- **whisper**: Локальное распознавание речи
- **ollama**: Локальная языковая модель
- **edge-tts**: Синтез речи (требует интернет)

## Конфигурация

Параметры модулей настраиваются через `config.py` в корне проекта.

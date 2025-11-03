# Архитектура проекта

Этот документ описывает архитектуру Voice AI Assistant.

## Обзор системы

Voice AI Assistant - это локальное веб-приложение для голосового взаимодействия с AI. Система работает полностью офлайн (кроме Edge TTS, который требует интернет).

### Компоненты

```
┌─────────────────┐
│  Web Browser    │
│  (Frontend)     │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────────────────────────┐
│      FastAPI Backend (main.py)      │
│  ┌───────────────────────────────┐  │
│  │   REST API Endpoints          │  │
│  │   - POST /api/voice-chat      │  │
│  │   - GET /api/audio/{filename} │  │
│  │   - POST /api/clear-history   │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   WebSocket Endpoint          │  │
│  │   - /ws/voice                 │  │
│  └───────────────────────────────┘  │
└────────┬────────────────────────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌─────────┐
│  STT   │ │ LLM  │ │  TTS   │ │  State  │
│ Module │ │Module│ │ Module │ │ Manager │
└────────┘ └──────┘ └────────┘ └─────────┘
    │         │          │
    ▼         ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐
│Whisper │ │Ollama│ │Edge TTS│
│  Vosk  │ │      │ │        │
└────────┘ └──────┘ └────────┘
```

## Модули системы

### 1. STT Module (stt_module.py)

**Ответственность**: Преобразование речи в текст

**Технологии**: OpenAI Whisper

**Основные методы**:
- `__init__(model_size)`: Загрузка Whisper модели
- `transcribe(audio_path, language)`: Распознавание речи из файла

**Особенности**:
- Поддержка различных размеров моделей (tiny/base/small/medium/large)
- Автоматическое определение устройства (CPU/GPU)
- Поддержка русского и английского языков

### 2. Streaming STT Module (stt_streaming_module.py)

**Ответственность**: Потоковое распознавание речи в реальном времени

**Технологии**: Vosk

**Основные методы**:
- `__init__(model_path, sample_rate)`: Загрузка Vosk модели
- `create_recognizer()`: Создание нового распознавателя
- `process_chunk(recognizer, audio_chunk)`: Обработка аудио чанка
- `finalize(recognizer)`: Получение финального результата

**Особенности**:
- Потоковая обработка аудио
- Возвращает промежуточные и финальные результаты
- Использует локальную модель Vosk (vosk-model-small-ru-0.22)

### 3. LLM Module (llm_module.py)

**Ответственность**: Генерация ответов от AI

**Технологии**: Ollama

**Основные методы**:
- `__init__(model_name)`: Инициализация подключения к Ollama
- `generate_response(user_input, system_prompt)`: Генерация ответа
- `clear_history()`: Очистка истории разговора

**Особенности**:
- Сохраняет историю разговора (последние 10 сообщений)
- Использует системный промпт для настройки поведения
- По умолчанию использует модель `gpt-oss:20b`

### 4. TTS Module (tts_module.py)

**Ответственность**: Преобразование текста в речь

**Технологии**: Microsoft Edge TTS

**Основные методы**:
- `__init__()`: Инициализация TTS модуля
- `synthesize_async(text, output_path, language)`: Асинхронный синтез речи
- `synthesize(text, output_path, language)`: Синхронная обертка

**Особенности**:
- Использует качественные нейронные голоса
- Поддержка русского (ru-RU-SvetlanaNeural) и английского (en-US-JennyNeural)
- Асинхронная генерация для неблокирующей работы

### 5. State Manager (state_manager.py)

**Ответственность**: Управление состояниями диалога

**Состояния**:
- `IDLE`: Ожидание
- `LISTENING`: Слушание пользователя
- `PROCESSING`: Обработка запроса (STT + LLM + TTS)
- `SPEAKING`: Воспроизведение ответа

**Основные методы**:
- `transition_to(new_state)`: Переход в новое состояние
- `can_interrupt()`: Проверка возможности прерывания
- `update_transcript(text, is_partial)`: Обновление транскрипции
- `add_to_history(role, text)`: Добавление в историю
- `mark_silence_start()`: Отметка начала тишины
- `get_silence_duration()`: Получение длительности тишины

**Особенности**:
- Управляет жизненным циклом диалога
- Отслеживает промежуточные и финальные транскрипции
- Помогает детектировать конец фразы пользователя

### 6. Main Application (main.py)

**Ответственность**: Координация всех компонентов

**Endpoints**:

1. **REST API**:
   - `GET /`: Главная страница (serves index.html)
   - `POST /api/voice-chat`: Обработка голосового запроса (legacy)
   - `GET /api/audio/{filename}`: Получение сгенерированного аудио
   - `POST /api/clear-history`: Очистка истории разговора

2. **WebSocket**:
   - `WS /ws/voice`: Потоковый голосовой диалог

**Lifespan Events**:
- `startup`: Инициализация всех модулей (STT, Streaming STT, LLM, TTS)
- `shutdown`: Очистка ресурсов

## Потоки данных

### Legacy Flow (REST API)

```
User Voice
    ↓
Browser MediaRecorder
    ↓
POST /api/voice-chat (multipart/form-data)
    ↓
Save to uploads/input_{timestamp}.wav
    ↓
STT Module (Whisper)
    ↓
Transcribed Text
    ↓
LLM Module (Ollama)
    ↓
AI Response Text
    ↓
TTS Module (Edge TTS)
    ↓
Save to outputs/output_{timestamp}.wav
    ↓
Return JSON {user_text, ai_response, audio_url}
    ↓
Browser plays audio
```

### Streaming Flow (WebSocket)

```
User Voice
    ↓
Browser AudioContext (16kHz PCM)
    ↓
VAD (Voice Activity Detection)
    ↓
Send PCM chunks via WebSocket
    ↓
Streaming STT Module (Vosk)
    ↓
Partial/Final Transcripts
    ↓
Speech End Detection
    ↓
Final Transcript
    ↓
LLM Module (Ollama)
    ↓
AI Response
    ↓
TTS Module (Edge TTS)
    ↓
Audio File Generated
    ↓
Send audio_url via WebSocket
    ↓
Browser plays audio
    ↓
Speaking Finished
    ↓
Return to LISTENING state
```

## Протокол WebSocket

### Сообщения от клиента

```javascript
// Начало прослушивания
{ type: "start_listening" }

// Аудио чанк (base64 encoded PCM)
{ type: "audio_chunk", data: "base64_audio_data" }

// Конец речи (детектирован клиентом)
{ type: "speech_end" }

// Воспроизведение завершено
{ type: "speaking_finished" }

// Прерывание воспроизведения
{ type: "interrupt" }

// Остановка диалога
{ type: "stop" }
```

### Сообщения от сервера

```javascript
// Изменение состояния
{ type: "state", state: "listening" | "processing" | "speaking" }

// Промежуточный текст распознавания
{ type: "partial_transcript", text: "..." }

// Финальный текст пользователя
{ type: "final_transcript", text: "..." }

// Ответ AI
{ type: "ai_response", text: "...", audio_url: "/api/audio/..." }

// Ошибка
{ type: "error", message: "..." }
```

## Frontend Architecture

### Основные компоненты

1. **Audio Capture**: 
   - MediaRecorder API
   - AudioContext для обработки
   - ScriptProcessor для захвата PCM

2. **VAD (Voice Activity Detection)**:
   - Анализ громкости аудио
   - Детекция начала и конца речи
   - Порог: 15% громкости
   - Тишина: 500ms для завершения фразы

3. **WebSocket Client**:
   - Управление соединением
   - Отправка аудио чанков
   - Обработка сообщений сервера

4. **UI State Management**:
   - Отображение статуса (idle/listening/processing/speaking)
   - История разговора
   - Промежуточные транскрипции
   - Визуализация звука

### Состояния UI

- `idle`: Готов к работе
- `listening`: Слушает пользователя (красный индикатор)
- `processing`: Обрабатывает запрос (фиолетовый индикатор)
- `speaking`: Воспроизводит ответ (зеленый индикатор)

## Управление ресурсами

### Инициализация модулей

- Все модули инициализируются один раз при старте приложения
- Модели загружаются в память и переиспользуются
- Это оптимизирует время отклика

### Управление аудио файлами

- Входные файлы: `uploads/input_{timestamp}.wav`
- Выходные файлы: `outputs/output_{timestamp}.wav`
- Файлы не удаляются автоматически (требуется ручная очистка)

### Управление памятью

- История разговора ограничена 10 последними сообщениями
- WebSocket recognizers создаются заново для каждой фразы
- Аудио контексты закрываются после использования

## Безопасность

### Валидация

- Проверка формата аудио файлов
- Ограничение размера файлов
- Валидация WebSocket сообщений

### Изоляция

- Каждое WebSocket соединение имеет свой StateManager
- Ошибки в одном соединении не влияют на другие
- Временные файлы изолированы по timestamp

## Масштабируемость

### Текущие ограничения

- Один процесс на одну сессию (FastAPI single-threaded)
- Модели загружаются в память одного процесса
- Не поддерживает горизонтальное масштабирование

### Возможные улучшения

- Использование ASGI workers (uvicorn workers)
- Вынос моделей в отдельные сервисы
- Использование очередей для обработки запросов
- Kubernetes/Docker для оркестрации

## Зависимости

### Критические зависимости

- `fastapi`: Веб-фреймворк
- `openai-whisper`: STT (legacy)
- `vosk`: Streaming STT
- `ollama`: LLM
- `edge-tts`: TTS

### Системные требования

- Python 3.8+
- Минимум 8GB RAM
- Ollama должен быть запущен
- Интернет для Edge TTS

## Диаграмма последовательности

### WebSocket диалог

```
Client                Server                Modules
  │                     │                     │
  │──start_listening───>│                     │
  │<──state:listening───│                     │
  │                     │                     │
  │──audio_chunk───────>│                     │
  │                     │──process_chunk─────>│ Vosk
  │<──partial_transcript│<──result───────────│
  │                     │                     │
  │──speech_end────────>│                     │
  │                     │──finalize──────────>│ Vosk
  │<──final_transcript──│<──final_text───────│
  │                     │                     │
  │<──state:processing──│                     │
  │                     │──generate_response─>│ Ollama
  │                     │<──ai_text───────────│
  │                     │──synthesize────────>│ Edge TTS
  │                     │<──audio_file───────│
  │<──ai_response───────│                     │
  │<──state:speaking────│                     │
  │                     │                     │
  │──speaking_finished─>│                     │
  │<──state:listening───│                     │
  │                     │                     │
```

## Расширение архитектуры

### Добавление нового модуля

1. Создайте новый файл модуля (например, `new_module.py`)
2. Реализуйте интерфейс модуля
3. Инициализируйте в `main.py` lifespan startup
4. Используйте в соответствующих endpoints
5. Обновите документацию

### Добавление нового endpoint

1. Создайте функцию-обработчик в `main.py`
2. Добавьте декоратор `@app.get/post/websocket`
3. Обработайте входные данные
4. Используйте необходимые модули
5. Верните ответ
6. Обновите документацию API

## Мониторинг и отладка

### Логирование

- Используются print statements для логирования
- Префиксы для категоризации: `[STT]`, `[LLM]`, `[TTS]`
- Номера этапов: `[1]`, `[2]`, `[3]`, `[4]`

### Отладка

- WebSocket соединения логируют все сообщения
- Состояния StateManager логируются при переходах
- Ошибки логируются с traceback

## Заключение

Архитектура проекта спроектирована для:
- Локальной работы без интернета (кроме Edge TTS)
- Простоты понимания и модификации
- Модульности и расширяемости
- Производительности на CPU и GPU


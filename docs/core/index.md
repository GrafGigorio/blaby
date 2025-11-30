# Core Modules

## Назначение

Основные модули обработки голосового пайплайна: распознавание речи, генерация ответов, синтез речи.

## API

### stt_module.py — Speech-to-Text (Whisper)

```python
from core.stt_module import STTModule

stt = STTModule(model_size="medium")  # tiny/base/small/medium/large
text = stt.transcribe("audio.wav", language="ru")
```

### stt_streaming_module.py — Streaming STT (Vosk)

```python
from core.stt_streaming_module import StreamingSTTModule

stt = StreamingSTTModule(model_path="models/vosk-model-ru")
recognizer = stt.create_recognizer()
result = stt.process_chunk(recognizer, audio_chunk)  # partial/final
final = stt.finalize(recognizer)
```

### llm_module.py — Language Model (Ollama)

```python
from core.llm_module import LLMModule

llm = LLMModule(model_name="gpt-oss:20b")
response = llm.generate_response("Привет!", system_prompt="...")
llm.clear_history()  # очистка контекста
```

### tts_module.py — Text-to-Speech (Edge TTS)

```python
from core.tts_module import TTSModule

tts = TTSModule()
await tts.synthesize_async("Текст", "output.wav", language="ru")
```

### state_manager.py — Управление состоянием

```python
from core.state_manager import StateManager

state = StateManager()
state.transition_to("listening")  # idle → listening → processing → speaking
state.update_transcript("текст", is_partial=True)
```

### action_manager.py — Команды и действия

Обработка специальных команд ассистента.

## Примеры

```python
# Полный пайплайн
text = stt.transcribe("input.wav", "ru")
response = llm.generate_response(text)
await tts.synthesize_async(response, "output.wav", "ru")
```

## См. также

- [API endpoints](../api/index.md)
- [Архитектура](../architecture/ARCHITECTURE.md)

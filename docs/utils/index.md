# Utils

## Назначение

Вспомогательные модули для поддержки основной функциональности.

## API

### port_manager.py — Управление портами

```python
from utils.port_manager import find_free_port

port = find_free_port(start_port=8000)
```

### text_cleaning.py — Очистка текста для TTS

```python
from utils.text_cleaning import clean_text_for_tts

text = "TECH:info Привет!"
clean = clean_text_for_tts(text)  # "Привет!"
```

**Функции:**
- `clean_text_for_tts(text)` — основная очистка
- `remove_tech_blocks(text)` — удаление TECH блоков
- `remove_json_structures(text)` — удаление JSON
- `normalize_whitespace(text)` — нормализация пробелов

## Примеры

```python
# Очистка ответа LLM перед озвучиванием
response = llm.generate_response(user_input)
clean_response = clean_text_for_tts(response)
await tts.synthesize_async(clean_response, "out.wav", "ru")
```

## См. также

- [Core modules](../core/index.md)

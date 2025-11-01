# Voice AI Assistant

Локальный голосовой ассистент с использованием Ollama (gpt-oss:20b).

## Компоненты

- **STT:** OpenAI Whisper (локально)
- **LLM:** Ollama (gpt-oss:20b)
- **TTS:** Coqui TTS (локально)
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

# API

## Назначение

REST и WebSocket endpoints для голосового взаимодействия.

## API

### REST Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Web интерфейс |
| POST | `/api/voice-chat` | Голосовой запрос (legacy) |
| GET | `/api/audio/{filename}` | Получение аудио |
| POST | `/api/clear-history` | Очистка истории |

### WebSocket

**Endpoint**: `ws://localhost:8000/ws/voice`

**Клиент → Сервер:**
```json
{ "type": "start_listening" }
{ "type": "audio_chunk", "data": "base64_pcm" }
{ "type": "speech_end" }
{ "type": "speaking_finished" }
{ "type": "interrupt" }
{ "type": "stop" }
```

**Сервер → Клиент:**
```json
{ "type": "state", "state": "listening|processing|speaking" }
{ "type": "partial_transcript", "text": "..." }
{ "type": "final_transcript", "text": "..." }
{ "type": "ai_response", "text": "...", "audio_url": "..." }
{ "type": "error", "message": "..." }
```

## Примеры

### REST (Python)

```python
import requests

with open('audio.wav', 'rb') as f:
    r = requests.post('http://localhost:8000/api/voice-chat', files={'audio': f})
    print(r.json()['ai_response'])
```

### WebSocket (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/voice');
ws.onopen = () => ws.send(JSON.stringify({ type: 'start_listening' }));
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'ai_response') {
        new Audio(data.audio_url).play();
    }
};
```

## OpenAPI

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## См. также

- [Core modules](../core/index.md)
- [Архитектура](../architecture/ARCHITECTURE.md)

# API Documentation

Документация API для Voice AI Assistant.

## Базовый URL

```
http://localhost:8000
```

## REST API Endpoints

### 1. Главная страница

**GET** `/`

Возвращает HTML интерфейс приложения.

**Response**: HTML страница (`static/index.html`)

**Пример**:
```bash
curl http://localhost:8000/
```

---

### 2. Голосовой чат (Legacy)

**POST** `/api/voice-chat`

Обрабатывает голосовой запрос пользователя и возвращает ответ AI.

**Content-Type**: `multipart/form-data`

**Request Body**:
- `audio`: Audio file (WAV format, multipart/form-data)

**Response**:
```json
{
  "user_text": "Распознанный текст пользователя",
  "ai_response": "Ответ от AI",
  "audio_url": "/api/audio/output_20250101_120000.wav"
}
```

**Status Codes**:
- `200`: Успешная обработка
- `400`: Ошибка распознавания речи или невалидный запрос
- `500`: Внутренняя ошибка сервера

**Пример**:
```bash
curl -X POST http://localhost:8000/api/voice-chat \
  -F "audio=@recording.wav"
```

**Workflow**:
1. Принимает аудио файл
2. Сохраняет в `uploads/input_{timestamp}.wav`
3. Распознает речь через Whisper STT
4. Генерирует ответ через Ollama LLM
5. Синтезирует речь через Edge TTS
6. Сохраняет в `outputs/output_{timestamp}.wav`
7. Возвращает JSON с результатами

---

### 3. Получение аудио файла

**GET** `/api/audio/{filename}`

Возвращает сгенерированный аудио файл.

**Parameters**:
- `filename` (path): Имя аудио файла из `outputs/`

**Response**: Audio file (WAV format, `audio/wav`)

**Status Codes**:
- `200`: Файл найден
- `404`: Файл не найден

**Пример**:
```bash
curl http://localhost:8000/api/audio/output_20250101_120000.wav \
  -o response.wav
```

**Browser Example**:
```javascript
const audioUrl = '/api/audio/output_20250101_120000.wav';
const audio = new Audio(audioUrl);
audio.play();
```

---

### 4. Очистка истории разговора

**POST** `/api/clear-history`

Очищает историю разговора в LLM модуле.

**Response**:
```json
{
  "status": "success",
  "message": "История очищена"
}
```

**Пример**:
```bash
curl -X POST http://localhost:8000/api/clear-history
```

**JavaScript Example**:
```javascript
fetch('/api/clear-history', {
  method: 'POST'
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## WebSocket API

### Endpoint

**WebSocket** `/ws/voice`

Потоковый голосовой диалог через WebSocket.

**Protocol**: WebSocket (ws:// или wss://)

**Connection URL**:
```javascript
const wsUrl = `ws://localhost:8000/ws/voice`;
const ws = new WebSocket(wsUrl);
```

---

### Сообщения от клиента

#### 1. Начало прослушивания

```json
{
  "type": "start_listening"
}
```

**Описание**: Запускает режим прослушивания на сервере.

**Когда отправлять**: После установления WebSocket соединения.

**Response**: 
```json
{
  "type": "state",
  "state": "listening"
}
```

---

#### 2. Аудио чанк

```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_pcm_audio"
}
```

**Описание**: Отправляет чанк аудио данных (PCM, 16kHz, 16-bit, base64 encoded).

**Когда отправлять**: Непрерывно во время записи речи пользователя.

**Формат аудио**:
- Формат: PCM (Linear PCM)
- Частота дискретизации: 16000 Hz
- Разрядность: 16-bit
- Каналы: Mono
- Кодирование: Base64

**JavaScript Example**:
```javascript
// Конвертация Float32Array в Int16Array
const int16Array = new Int16Array(float32Array.length);
for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
}

// Конвертация в base64
const bytes = new Uint8Array(int16Array.buffer);
const base64Audio = btoa(String.fromCharCode.apply(null, bytes));

// Отправка
ws.send(JSON.stringify({
    type: 'audio_chunk',
    data: base64Audio
}));
```

---

#### 3. Конец речи

```json
{
  "type": "speech_end"
}
```

**Описание**: Сигнализирует серверу о конце речи пользователя (детектировано клиентом).

**Когда отправлять**: После детекции конца речи через VAD на клиенте.

**Response**: Начинается обработка запроса.

---

#### 4. Воспроизведение завершено

```json
{
  "type": "speaking_finished"
}
```

**Описание**: Уведомляет сервер об окончании воспроизведения ответа.

**Когда отправлять**: После завершения воспроизведения аудио ответа.

**Response**:
```json
{
  "type": "state",
  "state": "listening"
}
```

**JavaScript Example**:
```javascript
audioElement.addEventListener('ended', () => {
    ws.send(JSON.stringify({ type: 'speaking_finished' }));
});
```

---

#### 5. Прерывание

```json
{
  "type": "interrupt"
}
```

**Описание**: Прерывает текущее воспроизведение ответа и возвращается к прослушиванию.

**Когда отправлять**: Когда пользователь начинает говорить во время воспроизведения ответа.

**Response**:
```json
{
  "type": "state",
  "state": "listening"
}
```

---

#### 6. Остановка диалога

```json
{
  "type": "stop"
}
```

**Описание**: Останавливает диалог и закрывает соединение.

**Когда отправлять**: Когда пользователь хочет завершить диалог.

**Response**: WebSocket соединение закрывается.

---

### Сообщения от сервера

#### 1. Изменение состояния

```json
{
  "type": "state",
  "state": "listening" | "processing" | "speaking"
}
```

**Описание**: Уведомляет клиента об изменении состояния диалога.

**Состояния**:
- `listening`: Сервер слушает пользователя
- `processing`: Сервер обрабатывает запрос (STT + LLM + TTS)
- `speaking`: Сервер воспроизводит ответ

---

#### 2. Промежуточный текст

```json
{
  "type": "partial_transcript",
  "text": "Промежуточный распознанный текст..."
}
```

**Описание**: Промежуточный результат распознавания речи (обновляется в реальном времени).

**Когда приходит**: Во время распознавания речи через Vosk.

---

#### 3. Финальный текст пользователя

```json
{
  "type": "final_transcript",
  "text": "Финальный распознанный текст"
}
```

**Описание**: Финальный распознанный текст пользователя.

**Когда приходит**: После обработки всей фразы пользователя.

---

#### 4. Ответ AI

```json
{
  "type": "ai_response",
  "text": "Текст ответа от AI",
  "audio_url": "/api/audio/output_20250101_120000.wav"
}
```

**Описание**: Ответ от AI с URL аудио файла.

**Когда приходит**: После генерации ответа и синтеза речи.

**Использование**:
```javascript
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'ai_response') {
        // Отобразить текст
        displayMessage(data.text);
        
        // Воспроизвести аудио
        const audio = new Audio(data.audio_url);
        audio.play();
    }
};
```

---

#### 5. Ошибка

```json
{
  "type": "error",
  "message": "Описание ошибки"
}
```

**Описание**: Сообщение об ошибке.

**Когда приходит**: При возникновении ошибки в обработке.

---

## Полный пример WebSocket соединения

```javascript
// Подключение
const ws = new WebSocket('ws://localhost:8000/ws/voice');

// Обработчики
ws.onopen = () => {
    console.log('Connected');
    ws.send(JSON.stringify({ type: 'start_listening' }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case 'state':
            console.log('State:', data.state);
            break;
        case 'partial_transcript':
            console.log('Partial:', data.text);
            break;
        case 'final_transcript':
            console.log('Final:', data.text);
            break;
        case 'ai_response':
            console.log('AI:', data.text);
            const audio = new Audio(data.audio_url);
            audio.onended = () => {
                ws.send(JSON.stringify({ type: 'speaking_finished' }));
            };
            audio.play();
            break;
        case 'error':
            console.error('Error:', data.message);
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('Disconnected');
};

// Отправка аудио чанков
function sendAudioChunk(audioData) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'audio_chunk',
            data: audioData // base64 encoded PCM
        }));
    }
}

// Остановка
function stopDialog() {
    ws.send(JSON.stringify({ type: 'stop' }));
    ws.close();
}
```

---

## Обработка ошибок

### REST API

Все ошибки возвращаются в формате:
```json
{
  "detail": "Описание ошибки"
}
```

**Типичные ошибки**:
- `400 Bad Request`: Невалидный запрос или формат файла
- `404 Not Found`: Файл или ресурс не найден
- `500 Internal Server Error`: Внутренняя ошибка сервера

### WebSocket

Ошибки отправляются как сообщения типа `error`:
```json
{
  "type": "error",
  "message": "Описание ошибки"
}
```

После ошибки WebSocket соединение может быть закрыто.

---

## Ограничения

### Размер файлов

- Максимальный размер аудио файла (REST API): Зависит от настроек FastAPI
- Размер чанка (WebSocket): Рекомендуется 4096 samples (≈256ms при 16kHz)

### Частота отправки

- WebSocket чанки: Рекомендуется отправлять каждые 100-200ms
- Не превышайте пропускную способность соединения

### Таймауты

- WebSocket: Без таймаута (соединение остается открытым)
- REST API: Зависит от настроек сервера

---

## Версионирование

Текущая версия API: **v1**

API endpoint не включает версию в URL. При добавлении новых версий используйте префикс `/api/v2/`.

---

## OpenAPI / Swagger

FastAPI автоматически генерирует документацию OpenAPI:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Примеры использования

### Python клиент (REST API)

```python
import requests

# Голосовой чат
with open('recording.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/voice-chat',
        files={'audio': f}
    )
    result = response.json()
    print(result['ai_response'])
```

### Python клиент (WebSocket)

```python
import asyncio
import websockets
import json

async def voice_chat():
    uri = "ws://localhost:8000/ws/voice"
    async with websockets.connect(uri) as websocket:
        # Начало прослушивания
        await websocket.send(json.dumps({"type": "start_listening"}))
        
        # Получение ответов
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(voice_chat())
```

---

## Дополнительные ресурсы

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Web Audio API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)


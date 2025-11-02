"""
Главный файл FastAPI приложения для голосового ассистента
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
import os
import json
import asyncio
import socket
import subprocess
import base64
from datetime import datetime
from contextlib import asynccontextmanager

from stt_module import STTModule
from llm_module import LLMModule
from tts_module import TTSModule
from stt_streaming_module import StreamingSTTModule
from state_manager import StateManager, DialogState
import re

# Директории для файлов
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def clean_text_from_markdown(text: str) -> str:
    """
    Очищает текст от markdown форматирования (звездочки, подчеркивания и т.д.)
    ВАЖНО: Сохраняет ВСЕ пробелы между словами и добавляет пробелы там, где они нужны.
    
    Args:
        text: исходный текст
        
    Returns:
        очищенный текст
    """
    if not text:
        return text
    
    # Удаляем символы форматирования, заменяя их на пробел если они между буквами
    # Это предотвращает склеивание слов: "слово*слово" -> "слово слово"
    
    # Звездочки: если между буквами/словами, заменяем на пробел, иначе просто удаляем
    # Сохраняем пробелы вокруг звездочек
    text = re.sub(r'(\S)\*{1,3}(\S)', r'\1 \2', text)  # Между буквами -> пробел
    text = re.sub(r'\s*\*{1,3}\s*', ' ', text)  # Со звездочками вокруг -> пробел
    text = re.sub(r'\*{1,3}', '', text)  # Остальные звездочки просто удаляем
    
    # Подчеркивания: аналогично
    text = re.sub(r'(\S)_{1,3}(\S)', r'\1 \2', text)  # Между буквами -> пробел
    text = re.sub(r'\s*_{1,3}\s*', ' ', text)  # Со подчеркиваниями вокруг -> пробел
    text = re.sub(r'_{1,3}', '', text)  # Остальные подчеркивания удаляем
    
    # Обратные кавычки: аналогично
    text = re.sub(r'(\S)`+(\S)', r'\1 \2', text)  # Между буквами -> пробел
    text = re.sub(r'\s*`+\s*', ' ', text)  # С кавычками вокруг -> пробел
    text = re.sub(r'`+', '', text)  # Остальные кавычки удаляем
    
    # Удаляем квадратные скобки ссылок [текст](url), заменяем только на текст
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Удаляем хештеги
    text = re.sub(r'#+', '', text)
    
    # Добавляем пробелы в критических местах для предотвращения склеивания слов
    
    # 1. Строчная + заглавная = граница слова
    text = re.sub(r'([а-яё])([А-ЯЁ])', r'\1 \2', text)
    
    # 2. После знаков препинания без пробелов
    text = re.sub(r'([,.!?;:])([А-ЯЁа-яё])', r'\1 \2', text)
    
    # Удаляем множественные пробелы подряд (оставляем двойной для пауз в речи)
    text = re.sub(r' {3,}', '  ', text)
    
    # Убираем только пробелы в самом начале и конце строки
    text = text.strip()
    
    return text

# Глобальные экземпляры модулей
stt_module = None
llm_module = None
tts_module = None
streaming_stt_module = None


def kill_process_on_port(port: int):
    """
    Завершает процесс, занимающий указанный порт
    
    Args:
        port: номер порта для проверки
    """
    try:
        # Проверяем если порт занят
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            # Порт занят, ищем и убиваем процесс
            print(f"⚠️  Порт {port} занят, пытаемся завершить процесс...")
            
            # Для macOS/Linux используем lsof
            if os.name == 'posix':
                try:
                    # Находим PID процесса на порту
                    result = subprocess.run(
                        ['lsof', '-ti', f':{port}'],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            if pid:
                                print(f"🔪 Завершаем процесс PID: {pid}")
                                subprocess.run(['kill', '-9', pid], check=False)
                        print(f"✅ Процессы на порту {port} завершены")
                    else:
                        print(f"ℹ️  Процесс на порту {port} не найден")
                except Exception as e:
                    print(f"⚠️  Не удалось завершить процесс: {e}")
            
            # Для Windows используем netstat
            elif os.name == 'nt':
                try:
                    result = subprocess.run(
                        ['netstat', '-ano'],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    for line in result.stdout.split('\n'):
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) > 0:
                                pid = parts[-1]
                                print(f"🔪 Завершаем процесс PID: {pid}")
                                subprocess.run(['taskkill', '/F', '/PID', pid], check=False)
                                print(f"✅ Процесс на порту {port} завершен")
                                break
                except Exception as e:
                    print(f"⚠️  Не удалось завершить процесс: {e}")
    except Exception as e:
        print(f"⚠️  Ошибка проверки порта {port}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    global stt_module, llm_module, tts_module, streaming_stt_module

    print("=" * 50)
    print("Инициализация голосового ассистента...")
    print("=" * 50)

    try:
        # Инициализируем STT (оригинальный Whisper для старого API)
        stt_module = STTModule(model_size="base")

        # Инициализируем Streaming STT (Vosk для WebSocket)
        streaming_stt_module = StreamingSTTModule()

        # Инициализируем LLM
        llm_module = LLMModule(model_name="gpt-oss:20b")

        # Инициализируем TTS
        tts_module = TTSModule()

        print("=" * 50)
        print("Все модули успешно загружены!")
        print("Сервер готов к работе")
        print("=" * 50)

    except Exception as e:
        print(f"Ошибка инициализации: {e}")
        raise

    yield

    # Shutdown
    print("Завершение работы приложения...")


# Инициализация FastAPI с lifespan
app = FastAPI(title="Voice AI Assistant", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница с веб-интерфейсом"""
    html_path = Path("static/index.html")
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(content=get_default_html())


@app.post("/api/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    """
    Основной эндпоинт для голосового чата

    1. Принимает аудио файл
    2. Распознает речь (STT)
    3. Генерирует ответ (LLM)
    4. Синтезирует речь (TTS)
    5. Возвращает аудио ответ
    """
    try:
        # Сохраняем входящий аудио файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_audio_path = UPLOAD_DIR / f"input_{timestamp}.wav"

        with open(input_audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)

        print(f"\n[1] Получен аудио файл: {input_audio_path}")

        # Распознаем речь
        print("[2] Распознавание речи...")
        user_text = stt_module.transcribe(str(input_audio_path), language="ru")

        if not user_text:
            raise HTTPException(status_code=400, detail="Не удалось распознать речь")

        print(f"[2] Распознанный текст: {user_text}")

        # Генерируем ответ от LLM (асинхронно)
        print("[3] Генерация ответа от AI...")
        ai_response = await llm_module.generate_response_async(user_text, system_prompt=None)
        # Передаем ответ как есть, без изменений
        print(f"[3] Ответ AI: {ai_response}")

        # Синтезируем речь
        print("[4] Синтез речи...")
        output_audio_path = OUTPUT_DIR / f"output_{timestamp}.wav"
        success = await tts_module.synthesize_async(ai_response, str(output_audio_path), language="ru")

        if not success or not output_audio_path.exists():
            raise HTTPException(status_code=500, detail="Ошибка синтеза речи")

        print(f"[4] Аудио ответ готов: {output_audio_path}")

        # Возвращаем результат
        return {
            "user_text": user_text,
            "ai_response": ai_response,
            "audio_url": f"/api/audio/{output_audio_path.name}"
        }

    except Exception as e:
        print(f"Ошибка обработки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """Получение аудио файла"""
    audio_path = OUTPUT_DIR / filename
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Аудио файл не найден")
    return FileResponse(audio_path, media_type="audio/wav")


@app.post("/api/clear-history")
async def clear_history():
    """Очистка истории разговора"""
    llm_module.clear_history()
    return {"status": "success", "message": "История очищена"}


@app.get("/api/models")
async def get_models():
    """Получение списка доступных моделей Ollama"""
    try:
        import ollama
        models = ollama.list()
        # Извлекаем имена моделей (models - это ListResponse с атрибутом models)
        model_list = [model.model for model in models.models]
        current_model = llm_module.model_name
        return {
            "status": "success",
            "models": model_list,
            "current_model": current_model
        }
    except Exception as e:
        print(f"Ошибка получения списка моделей: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/set-model")
async def set_model(model_data: dict):
    """Смена активной модели LLM"""
    try:
        model_name = model_data.get("model_name")
        if not model_name:
            raise HTTPException(status_code=400, detail="Не указано имя модели")

        # Меняем модель в LLM модуле
        llm_module.set_model(model_name)

        return {
            "status": "success",
            "message": f"Модель изменена на {model_name}",
            "current_model": model_name
        }
    except Exception as e:
        print(f"Ошибка смены модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint для потокового голосового диалога

    Протокол обмена сообщениями:
    Клиент → Сервер:
        - {"type": "audio_chunk", "data": base64_audio} - чанк аудио
        - {"type": "start_listening"} - начать слушать
        - {"type": "stop"} - остановить диалог

    Сервер → Клиент:
        - {"type": "state", "state": "listening|processing|speaking"} - изменение состояния
        - {"type": "partial_transcript", "text": "..."} - промежуточный результат STT
        - {"type": "final_transcript", "text": "..."} - финальный текст пользователя
        - {"type": "ai_response", "text": "...", "audio_url": "..."} - ответ ассистента
        - {"type": "error", "message": "..."} - ошибка
    """
    await websocket.accept()
    print("✅ WebSocket соединение установлено")

    # Создаем state manager для этой сессии
    state = StateManager()
    recognizer = None
    silence_timer = None
    last_transcript = ""

    # Константы для детекции завершенности
    SILENCE_THRESHOLD = 1.5  # секунды тишины после речи

    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()
            message_type = data.get("type")
            print(f"📩 Получено сообщение: {message_type}")

            if message_type == "start_listening":
                # Очищаем историю при начале нового диалога
                print("🧹 Очистка истории LLM...")
                llm_module.clear_history()

                # Начинаем слушать
                print("🎧 Начало прослушивания...")
                state.start_listening()
                recognizer = streaming_stt_module.create_recognizer()
                last_transcript = ""

                await websocket.send_json({
                    "type": "state",
                    "state": "listening"
                })

            elif message_type == "audio_chunk":
                # Получен чанк аудио (не логируем каждый чанк)
                if state.current_state != DialogState.LISTENING:
                    continue

                try:
                    # Декодируем base64 аудио
                    audio_data = base64.b64decode(data.get("data", ""))

                    # Обрабатываем аудио через streaming STT
                    result = streaming_stt_module.process_chunk(recognizer, audio_data)

                    if result["partial"]:
                        # Промежуточный результат
                        if result["text"]:
                            last_transcript = result["text"]
                            state.update_transcript(result["text"], is_partial=True)
                            print(f"🔤 Промежуточный текст: '{result['text']}'")
                            await websocket.send_json({
                                "type": "partial_transcript",
                                "text": result["text"]
                            })
                            # Сбрасываем таймер тишины
                            state.reset_silence()
                    else:
                        # Финальный результат от Vosk
                        if result["text"]:
                            last_transcript = result["text"]
                            state.update_transcript(result["text"], is_partial=False)
                            print(f"✅ Vosk вернул финальный текст: '{result['text']}'")
                except Exception as audio_error:
                    print(f"⚠️ Ошибка обработки аудио: {audio_error}")
                    import traceback
                    traceback.print_exc()
                    # Не прерываем весь WebSocket из-за одного плохого чанка
                    continue

            elif message_type == "speech_end":
                # Клиент детектировал конец речи
                print("🔇 Конец речи детектирован")

                # Проверяем что мы в режиме listening
                if state.current_state != DialogState.LISTENING:
                    print(f"⚠️ Игнорируем speech_end - текущее состояние: {state.current_state.value}")
                    continue

                state.mark_silence_start()

                # Ждем SILENCE_THRESHOLD секунд
                await asyncio.sleep(SILENCE_THRESHOLD)

                # Проверяем что тишина все еще продолжается
                if state.get_silence_duration() and state.get_silence_duration() >= SILENCE_THRESHOLD:
                    # Получаем финальный текст
                    final_text = streaming_stt_module.finalize(recognizer)
                    if not final_text:
                        final_text = last_transcript

                    print(f"📝 Финальный текст: '{final_text}'")

                    if final_text and final_text.strip():
                        # Отправляем финальный текст клиенту
                        await websocket.send_json({
                            "type": "final_transcript",
                            "text": final_text
                        })

                        # Добавляем в историю
                        state.add_to_history("user", final_text)

                        # Переходим к обработке
                        state.start_processing()
                        await websocket.send_json({
                            "type": "state",
                            "state": "processing"
                        })

                        # Переходим в состояние говорения для потоковой передачи
                        state.start_speaking()
                        await websocket.send_json({
                            "type": "state",
                            "state": "speaking"
                        })

                        # Начинаем потоковую генерацию ответа
                        print("🤖 Начало потоковой генерации ответа...")
                        
                        full_response = ""
                        text_buffer = ""
                        
                        # Отправляем начало потока
                        await websocket.send_json({
                            "type": "stream_start"
                        })
                        
                        # Потоковая генерация от LLM и TTS
                        async for text_chunk in llm_module.generate_response_stream(final_text, system_prompt=None):
                            # Логируем оригинальный чанк для отладки
                            print(f"📝 Оригинальный чанк от LLM: '{text_chunk}' (длина: {len(text_chunk)})")
                            
                            # Передаем текст как есть, без изменений
                            full_response += text_chunk
                            text_buffer += text_chunk
                            
                            # Отправляем текстовый чанк для отображения
                            if text_chunk:  # Отправляем только если есть текст
                                await websocket.send_json({
                                    "type": "text_chunk",
                                    "text": text_chunk
                                })
                            
                            # Накопляем текст до предложения (до точки, восклицательного или вопросительного знака)
                            # или до определенного размера (50 символов)
                            if len(text_buffer) >= 50 or any(punct in text_buffer for punct in ['.', '!', '?', '。']):
                                # Находим границу предложения
                                sentence_end = -1
                                for punct in ['.', '!', '?', '。']:
                                    pos = text_buffer.rfind(punct)
                                    if pos > sentence_end:
                                        sentence_end = pos
                                
                                if sentence_end >= 0:
                                    sentence = text_buffer[:sentence_end + 1]
                                    text_buffer = text_buffer[sentence_end + 1:]
                                else:
                                    # Если не нашли предложение, берем первые 50 символов
                                    sentence = text_buffer[:50]
                                    text_buffer = text_buffer[50:]
                                
                                # Синтезируем предложение в аудио
                                if sentence.strip():
                                    print(f"🔊 Синтез: '{sentence[:30]}...'")
                                    try:
                                        chunk_count = 0
                                        async for audio_chunk in tts_module.synthesize_stream(sentence, language="ru"):
                                            chunk_count += 1
                                            # Отправляем аудио чанк клиенту (base64)
                                            audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')
                                            print(f"📦 Отправка аудио чанка #{chunk_count}, размер: {len(audio_base64)} символов (байт данных: {len(audio_chunk)})")
                                            await websocket.send_json({
                                                "type": "audio_chunk",
                                                "data": audio_base64
                                            })
                                        print(f"✅ Синтез завершен, отправлено {chunk_count} чанков")
                                    except Exception as tts_error:
                                        print(f"⚠️ Ошибка TTS: {tts_error}")
                                        import traceback
                                        traceback.print_exc()
                        
                        # Обрабатываем остаток буфера
                        if text_buffer.strip():
                            print(f"🔊 Финальный синтез: '{text_buffer[:30]}...'")
                            try:
                                chunk_count = 0
                                async for audio_chunk in tts_module.synthesize_stream(text_buffer, language="ru"):
                                    chunk_count += 1
                                    audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')
                                    print(f"📦 Отправка финального аудио чанка #{chunk_count}, размер: {len(audio_base64)} символов")
                                    await websocket.send_json({
                                        "type": "audio_chunk",
                                        "data": audio_base64
                                    })
                                print(f"✅ Финальный синтез завершен, отправлено {chunk_count} чанков")
                            except Exception as tts_error:
                                print(f"⚠️ Ошибка финального TTS: {tts_error}")
                                import traceback
                                traceback.print_exc()
                        
                        # Сохраняем полный ответ как есть, без изменений
                        if full_response:
                            state.add_to_history("assistant", full_response)
                            print(f"💬 Полный ответ AI: {full_response}")
                        else:
                            full_response = ""
                        
                        # Отправляем конец потока
                        await websocket.send_json({
                            "type": "stream_end",
                            "text": full_response
                        })
                    else:
                        print("⚠️ Пустой финальный текст, игнорируем")
                        # Создаем новый recognizer для следующей фразы
                        recognizer = streaming_stt_module.create_recognizer()
                        last_transcript = ""

            elif message_type == "speaking_finished":
                # Воспроизведение ответа завершено, возвращаемся к прослушиванию
                print("🔄 Получено speaking_finished, текущее состояние:", state.current_state.value)
                print("🔄 Возврат к прослушиванию...")
                
                # Проверяем что мы в состоянии speaking
                if state.current_state != DialogState.SPEAKING:
                    print(f"⚠️ Предупреждение: speaking_finished получен в состоянии {state.current_state.value}, но продолжаем...")
                
                state.start_listening()

                # ВАЖНО: Создаем НОВЫЙ recognizer для новой фразы
                recognizer = streaming_stt_module.create_recognizer()
                last_transcript = ""
                print("✅ Новый recognizer создан, готов к следующей фразе")
                print(f"✅ Состояние изменено на: {state.current_state.value}")

                await websocket.send_json({
                    "type": "state",
                    "state": "listening"
                })
                print("✅ Отправлено состояние 'listening' клиенту")

            elif message_type == "interrupt":
                # Прерывание воспроизведения
                print(f"⚠️ Получен interrupt, текущее состояние: {state.current_state.value}")
                if state.can_interrupt():
                    print("⚠️ Прерывание воспроизведения разрешено, возврат к прослушиванию...")
                    state.start_listening()

                    # Создаем новый recognizer
                    recognizer = streaming_stt_module.create_recognizer()
                    last_transcript = ""
                    print("✅ Новый recognizer создан после прерывания")

                    await websocket.send_json({
                        "type": "state",
                        "state": "listening"
                    })
                else:
                    print(f"❌ Прерывание НЕ разрешено в состоянии {state.current_state.value}")

            elif message_type == "stop":
                # Остановка диалога
                print("⏹️ Остановка диалога")
                state.reset()
                break

    except WebSocketDisconnect:
        print("❌ WebSocket отключен")
    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        print("👋 Завершение WebSocket соединения")


def get_default_html():
    """HTML по умолчанию если нет static/index.html"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice AI Assistant</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>Voice AI Assistant</h1>
        <p>Загрузка интерфейса...</p>
        <p>Если вы видите это сообщение, создайте файл static/index.html</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    print("\nЗапуск Voice AI Assistant...")
    print("После загрузки откройте: http://localhost:8000\n")
    
    # Завершаем процесс на порту 8000 если он занят
    kill_process_on_port(8000)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

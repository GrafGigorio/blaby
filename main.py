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
from action_manager import ActionManager
import re

# Директории для файлов
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def clean_text_from_markdown(text: str) -> str:
    """
    Очищает текст от markdown форматирования (звездочки, подчеркивания и т.д.)
    и технической информации между маркерами <TECH>...</TECH>
    ВАЖНО: Сохраняет ВСЕ пробелы между словами и добавляет пробелы там, где они нужны.
    
    Args:
        text: исходный текст
        
    Returns:
        очищенный текст
    """
    if not text:
        return text
    
    # ВАЖНО: Сначала удаляем технические блоки между маркерами <TECH>...</TECH>
    # Это позволяет исключить JSON и другую техническую информацию из озвучки
    # Поддерживаем как полные теги <TECH>...</TECH>, так и открывающие/закрывающие отдельно
    text = re.sub(r'<TECH>.*?</TECH>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Удаляем незакрытые теги (на случай если они разорваны потоковой передачей)
    text = re.sub(r'<TECH>.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'.*?</TECH>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
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
    
    # Наклонные черты: удаляем полностью (TTS произносит их как "наклонная черта")
    text = re.sub(r'(\S)[/\\]+(\S)', r'\1 \2', text)  # Между буквами -> пробел
    text = re.sub(r'\s*[/\\]+\s*', ' ', text)  # Со слешами вокруг -> пробел
    text = re.sub(r'[/\\]+', '', text)  # Остальные слеши удаляем
    
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

# Монтируем директорию static для раздачи статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")


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
        # Очищаем текст от markdown и спецсимволов перед синтезом
        cleaned_response = clean_text_from_markdown(ai_response)
        success = await tts_module.synthesize_async(cleaned_response, str(output_audio_path), language="ru")

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


def get_system_prompt_for_action(action_manager: ActionManager) -> str:
    """
    Получить системный промпт для работы с действиями
    
    Args:
        action_manager: экземпляр ActionManager
        
    Returns:
        Системный промпт
    """
    return action_manager.get_system_prompt()


async def send_greeting_directly(websocket, state, generation_interrupted, tts_module, llm_module=None):
    """
    Отправляет приветствие напрямую, без ожидания LLM
    
    Args:
        websocket: WebSocket соединение
        state: StateManager для управления состоянием
        generation_interrupted: Event для проверки прерывания
        tts_module: TTSModule для синтеза речи
        llm_module: LLMModule для сохранения истории (опционально)
    """
    try:
        greeting_text = "Здравствуйте! Меня зовут Ася, я работаю в телеком компании. Чем могу помочь?"
        
        print("👋 Отправка приветствия напрямую...")
        
        # Отправляем начало потока
        await websocket.send_json({
            "type": "stream_start"
        })
        
        # Сразу отправляем текст приветствия для отображения
        await websocket.send_json({
            "type": "text_chunk",
            "text": greeting_text
        })
        
        # Очищаем текст от markdown и спецсимволов
        cleaned_greeting = clean_text_from_markdown(greeting_text)
        
        # Синтезируем речь и отправляем аудио чанки
        chunk_count = 0
        async for audio_chunk in tts_module.synthesize_stream(cleaned_greeting, language="ru"):
            # Проверяем прерывание
            if generation_interrupted.is_set():
                print("⚠️ Приветствие прервано!")
                return
            
            chunk_count += 1
            audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')
            await websocket.send_json({
                "type": "audio_chunk",
                "data": audio_base64
            })
        
        print(f"✅ Приветствие отправлено, отправлено {chunk_count} аудио чанков")
        
        # Отправляем конец потока
        await websocket.send_json({
            "type": "stream_end",
            "text": greeting_text
        })
        
        # Сохраняем приветствие в историю StateManager и LLM (для контекста)
        # Добавляем как сообщение ассистента в историю
        # Это нужно для того, чтобы LLM знал, что приветствие уже было отправлено
        state.add_to_history("assistant", greeting_text)
        # Также добавляем в историю LLM модуля
        if llm_module:
            llm_module.conversation_history.append({
                "role": "assistant",
                "content": greeting_text
            })
        
    except Exception as e:
        print(f"❌ Ошибка отправки приветствия: {e}")
        import traceback
        traceback.print_exc()
        raise


async def generate_and_send_response(websocket, final_text, state, generation_interrupted, action_manager: ActionManager = None, system_prompt_override: str = None):
    """Генерирует ответ AI и отправляет клиенту с проверкой прерывания"""
    try:
        # Начинаем потоковую генерацию ответа
        print("🤖 Начало потоковой генерации ответа...")
        
        full_response = ""
        text_buffer = ""
        
        # Получаем системный промпт если есть action_manager или override
        system_prompt = system_prompt_override
        if system_prompt is None and action_manager:
            system_prompt = get_system_prompt_for_action(action_manager)
        
        # Отправляем начало потока
        await websocket.send_json({
            "type": "stream_start"
        })
        
        # Потоковая генерация от LLM и TTS с проверкой прерывания
        chunk_num = 0
        tech_buffer = ""  # Буфер для накопления TECH блока
        tech_tag_open = False  # Флаг открытого TECH тега
        
        async for text_chunk in llm_module.generate_response_stream(final_text, system_prompt=system_prompt):
            # Проверяем флаг прерывания
            if generation_interrupted.is_set():
                print("⚠️ Генерация прервана!")
                return
            
            chunk_num += 1
            # Логируем оригинальный чанк для отладки
            print(f"📝 Оригинальный чанк от LLM #{chunk_num}: '{text_chunk}' (длина: {len(text_chunk)})")
            
            # Передаем текст как есть, без изменений в full_response
            full_response += text_chunk
            
            # Обрабатываем TECH блоки - разделяем обычный текст и технический блок
            remaining = text_chunk
            text_for_buffer = ""  # Текст для добавления в text_buffer (без TECH блоков)
            
            while remaining:
                if not tech_tag_open:
                    # Ищем открывающий тег <TECH>
                    tech_start = remaining.upper().find('<TECH>')
                    if tech_start >= 0:
                        # Текст до TECH добавляем в буфер
                        text_for_buffer += remaining[:tech_start]
                        # Начинаем TECH блок
                        tech_tag_open = True
                        tech_buffer = remaining[tech_start + 6:]  # +6 для длины '<TECH>'
                        remaining = ""
                    else:
                        # TECH тега нет - весь текст обычный
                        text_for_buffer += remaining
                        remaining = ""
                else:
                    # TECH блок открыт - ищем закрывающий тег
                    tech_end = remaining.upper().find('</TECH>')
                    if tech_end >= 0:
                        # Закрываем TECH блок
                        tech_buffer += remaining[:tech_end]
                        tech_tag_open = False
                        tech_buffer = ""  # Очищаем буфер TECH блока
                        remaining = remaining[tech_end + 7:]  # +7 для длины '</TECH>'
                    else:
                        # Закрывающего тега нет - накапливаем в TECH буфер
                        tech_buffer += remaining
                        remaining = ""
            
            # Добавляем только обычный текст (без TECH блоков) в text_buffer
            if text_for_buffer:
                text_buffer += text_for_buffer
                # Отправляем текстовый чанк для отображения (только обычный текст)
                await websocket.send_json({
                    "type": "text_chunk",
                    "text": text_for_buffer
                })
            
            # Накопляем текст до предложения (до точки, восклицательного или вопросительного знака)
            # или до определенного размера (200 символов для лучшего качества TTS)
            if len(text_buffer) >= 200 or any(punct in text_buffer for punct in ['.', '!', '?', '。']):
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
                    # Если не нашли предложение, ищем последний пробел перед 200 символами
                    # чтобы не разрывать слова
                    cutoff = 200
                    if len(text_buffer) > cutoff:
                        # Ищем последний пробел
                        last_space = text_buffer.rfind(' ', 0, cutoff + 1)
                        if last_space > cutoff // 2:  # Найден пробел во второй половине
                            cutoff = last_space + 1
                    
                    sentence = text_buffer[:cutoff]
                    text_buffer = text_buffer[cutoff:]
                
                # Синтезируем предложение в аудио
                if sentence.strip():
                    # Предварительно пытаемся удалить JSON если есть action_manager
                    sentence_for_tts = sentence
                    if action_manager:
                        # Пытаемся найти и удалить JSON из предложения
                        _, cleaned = action_manager.parse_llm_response(sentence)
                        if cleaned != sentence:
                            sentence_for_tts = cleaned
                    # Очищаем текст от markdown и спецсимволов перед синтезом
                    cleaned_sentence = clean_text_from_markdown(sentence_for_tts)
                    print(f"🔊 Синтез: '{cleaned_sentence[:30]}...' (было: '{sentence[:30]}...')")
                    try:
                        chunk_count = 0
                        async for audio_chunk in tts_module.synthesize_stream(cleaned_sentence, language="ru"):
                            # Проверяем прерывание перед отправкой каждого аудио чанка
                            if generation_interrupted.is_set():
                                print("⚠️ TTS прерван!")
                                return
                            
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
        
        # Обрабатываем незакрытый TECH блок после завершения цикла (если остался)
        if tech_tag_open and tech_buffer and action_manager:
            try:
                # Пытаемся извлечь JSON из незакрытого TECH блока
                json_match = re.search(r'\{.*\}', tech_buffer, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed_data = json.loads(json_str)
                    if isinstance(parsed_data, dict) and ("action" in parsed_data or "stage" in parsed_data):
                        print(f"📊 Найден JSON в незакрытом TECH блоке: {parsed_data}")
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ Не удалось распарсить JSON из незакрытого TECH блока: {e}")
        
        # Обрабатываем остаток буфера (только если не было прерывания)
        if not generation_interrupted.is_set() and text_buffer.strip():
            # Предварительно пытаемся удалить JSON если есть action_manager
            buffer_for_tts = text_buffer
            if action_manager:
                _, cleaned = action_manager.parse_llm_response(text_buffer)
                if cleaned != text_buffer:
                    buffer_for_tts = cleaned
            # Очищаем текст от markdown и спецсимволов перед синтезом
            cleaned_buffer = clean_text_from_markdown(buffer_for_tts)
            print(f"🔊 Финальный синтез: '{cleaned_buffer[:30]}...' (было: '{text_buffer[:30]}...')")
            try:
                chunk_count = 0
                async for audio_chunk in tts_module.synthesize_stream(cleaned_buffer, language="ru"):
                    # Проверяем прерывание
                    if generation_interrupted.is_set():
                        print("⚠️ Финальный TTS прерван!")
                        return
                    
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
        
        # Парсим JSON из полного ответа если есть action_manager
        cleaned_response_for_history = full_response
        action_data = None
        if action_manager and not generation_interrupted.is_set() and full_response:
            parsed_data, cleaned_text = action_manager.parse_llm_response(full_response)
            if parsed_data:
                print(f"📊 Распарсенные данные действия: {parsed_data}")
                # Обновляем состояние action_manager
                action_data = action_manager.update_from_parsed_data(parsed_data)
                # Используем очищенный текст для истории и TTS
                cleaned_response_for_history = cleaned_text
                # Отправляем action_data клиенту
                await websocket.send_json({
                    "type": "action_data",
                    "data": action_data
                })
                print(f"📤 Отправлены данные действия клиенту: {action_data}")
        
        # Сохраняем очищенный ответ в историю (только если не было прерывания)
        if not generation_interrupted.is_set() and cleaned_response_for_history:
            state.add_to_history("assistant", cleaned_response_for_history)
            print(f"💬 Полный ответ AI (очищенный): {cleaned_response_for_history}")
        elif generation_interrupted.is_set():
            print("⚠️ Генерация была прервана, ответ не сохранен в историю")
        
        # Отправляем конец потока
        await websocket.send_json({
            "type": "stream_end",
            "text": cleaned_response_for_history if not generation_interrupted.is_set() else ""
        })
    except asyncio.CancelledError:
        print("⚠️ Генерация отменена")
        raise
    except Exception as e:
        print(f"❌ Критическая ошибка при генерации ответа: {e}")
        import traceback
        traceback.print_exc()
        
        # Пытаемся уведомить клиента об ошибке
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Ошибка генерации ответа: {str(e)}"
            })
            # Возвращаемся в состояние listening
            await websocket.send_json({
                "type": "state",
                "state": "listening"
            })
        except:
            pass  # Если не удалось отправить, просто игнорируем


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
    # Создаем action manager для этой сессии
    action_manager = ActionManager()
    recognizer = None
    silence_timer = None
    last_transcript = ""

    # Константы для детекции завершенности
    SILENCE_THRESHOLD = 1.5  # секунды тишины после речи

    # Флаг для прерывания генерации
    generation_interrupted = asyncio.Event()
    generation_task = None
    greeting_sent = False  # Флаг для отслеживания отправленного приветствия

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
                # Сбрасываем action_manager
                action_manager.reset()
                greeting_sent = False

                # Начинаем слушать
                print("🎧 Начало прослушивания...")
                state.start_listening()
                recognizer = streaming_stt_module.create_recognizer()
                last_transcript = ""

                await websocket.send_json({
                    "type": "state",
                    "state": "listening"
                })
                
                # Автоматическое приветствие от Аси - отправляем напрямую, без ожидания LLM
                if not greeting_sent:
                    print("👋 Отправка приветствия от Аси напрямую...")
                    greeting_sent = True
                    
                    # Переходим в состояние speaking
                    state.start_speaking()
                    await websocket.send_json({
                        "type": "state",
                        "state": "speaking"
                    })
                    generation_interrupted.clear()
                    
                    # Отправляем приветствие напрямую, без LLM
                    try:
                        await send_greeting_directly(websocket, state, generation_interrupted, tts_module, llm_module)
                    except Exception as greeting_error:
                        print(f"❌ Ошибка приветствия: {greeting_error}")
                        import traceback
                        traceback.print_exc()
                    # После приветствия возвращаемся в listening
                    state.start_listening()
                    await websocket.send_json({
                        "type": "state",
                        "state": "listening"
                    })
                    recognizer = streaming_stt_module.create_recognizer()
                    last_transcript = ""

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
                print(f"🔇 Текущее состояние: {state.current_state.value}")
                print(f"🔇 Последний промежуточный транскрипт: '{last_transcript}'")

                try:
                    # Проверяем что мы в режиме listening
                    if state.current_state != DialogState.LISTENING:
                        print(f"⚠️ Игнорируем speech_end - текущее состояние: {state.current_state.value}")
                        continue

                    state.mark_silence_start()

                    # Ждем SILENCE_THRESHOLD секунд для финализации распознавания
                    print(f"⏳ Ожидание {SILENCE_THRESHOLD} сек для финализации распознавания...")
                    await asyncio.sleep(SILENCE_THRESHOLD)

                    # Проверяем что тишина все еще продолжается
                    silence_duration = state.get_silence_duration()
                    print(f"⏳ Длительность тишины: {silence_duration} сек")
                    
                    if silence_duration and silence_duration >= SILENCE_THRESHOLD:
                        # Получаем финальный текст
                        print("📝 Финализация распознавания...")
                        try:
                            final_text = streaming_stt_module.finalize(recognizer)
                            print(f"📝 Текст после finalize: '{final_text}'")
                            if not final_text or not final_text.strip():
                                print(f"⚠️ finalize вернул пустой текст, используем last_transcript: '{last_transcript}'")
                                final_text = last_transcript
                        except Exception as finalize_error:
                            print(f"⚠️ Ошибка при finalize: {finalize_error}")
                            import traceback
                            traceback.print_exc()
                            final_text = last_transcript

                        print(f"📝 Финальный текст для обработки: '{final_text}'")
                        print(f"📝 Длина финального текста: {len(final_text) if final_text else 0} символов")

                        if final_text and final_text.strip():
                            # Фильтруем слишком короткие или неразборчивые тексты
                            cleaned_text = final_text.strip()
                            # Проверяем на слишком короткие тексты (менее 2 символов) или только спецсимволов
                            if len(cleaned_text) < 2 or cleaned_text.lower() in ['непонятно', 'непонятно почему', 'непонятно oy']:
                                print(f"⚠️ Текст слишком короткий или неразборчивый: '{cleaned_text}', возвращаемся к прослушиванию")
                                # Создаем новый recognizer для следующей фразы
                                recognizer = streaming_stt_module.create_recognizer()
                                last_transcript = ""
                                
                                # ВАЖНО: Возвращаемся в состояние listening
                                state.start_listening()
                                await websocket.send_json({
                                    "type": "state",
                                    "state": "listening"
                                })
                                print("✅ Возвращено состояние 'listening' после пустого/неразборчивого текста")
                            else:
                                # Отправляем финальный текст клиенту
                                await websocket.send_json({
                                    "type": "final_transcript",
                                    "text": cleaned_text
                                })

                                # Добавляем в историю
                                state.add_to_history("user", cleaned_text)

                                # Переходим к обработке
                                print("🔄 Переход к обработке запроса...")
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

                                # Сбрасываем флаг прерывания для новой генерации
                                generation_interrupted.clear()
                                
                                # Запускаем генерацию в отдельной задаче, чтобы не блокировать получение interrupt
                                print("🚀 Запуск генерации ответа...")
                                try:
                                    generation_task = asyncio.create_task(
                                        generate_and_send_response(websocket, cleaned_text, state, generation_interrupted, action_manager)
                                    )
                                    print("✅ Задача генерации создана успешно")
                                except Exception as task_error:
                                    print(f"❌ Ошибка создания задачи генерации: {task_error}")
                                    import traceback
                                    traceback.print_exc()
                                    # Возвращаемся в listening при ошибке создания задачи
                                    state.start_listening()
                                    await websocket.send_json({
                                        "type": "state",
                                        "state": "listening"
                                    })
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": f"Ошибка запуска генерации: {str(task_error)}"
                                    })
                        else:
                            print("⚠️ Пустой финальный текст, возвращаемся к прослушиванию")
                            # Создаем новый recognizer для следующей фразы
                            recognizer = streaming_stt_module.create_recognizer()
                            last_transcript = ""
                            
                            # ВАЖНО: Возвращаемся в состояние listening
                            state.start_listening()
                            await websocket.send_json({
                                "type": "state",
                                "state": "listening"
                            })
                            print("✅ Возвращено состояние 'listening' после пустого текста")
                    else:
                        print(f"⚠️ Тишина прервана (длительность: {silence_duration} сек), игнорируем speech_end")
                except Exception as speech_end_error:
                    print(f"❌ Критическая ошибка при обработке speech_end: {speech_end_error}")
                    import traceback
                    traceback.print_exc()
                    # Пытаемся вернуться в listening и уведомить клиента
                    try:
                        state.start_listening()
                        await websocket.send_json({
                            "type": "state",
                            "state": "listening"
                        })
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Ошибка обработки речи: {str(speech_end_error)}"
                        })
                        recognizer = streaming_stt_module.create_recognizer()
                        last_transcript = ""
                        print("✅ Восстановлено состояние после ошибки")
                    except Exception as recovery_error:
                        print(f"❌ Ошибка восстановления после speech_end: {recovery_error}")
                        raise  # Поднимаем исключение, что приведет к закрытию WebSocket

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
                    
                    # Устанавливаем флаг прерывания
                    generation_interrupted.set()
                    print("🚩 Флаг прерывания установлен")
                    
                    # Отменяем задачу генерации если она выполняется
                    if generation_task and not generation_task.done():
                        print("⏹️ Отмена задачи генерации...")
                        generation_task.cancel()
                        try:
                            await generation_task
                        except asyncio.CancelledError:
                            print("✅ Задача генерации отменена")
                        except Exception as e:
                            print(f"⚠️ Ошибка при отмене задачи генерации: {e}")
                    
                    # Очищаем задачу
                    generation_task = None
                    
                    state.start_listening()

                    # Создаем новый recognizer
                    recognizer = streaming_stt_module.create_recognizer()
                    last_transcript = ""
                    print("✅ Новый recognizer создан после прерывания")

                    await websocket.send_json({
                        "type": "state",
                        "state": "listening"
                    })
                    print("✅ Отправлено состояние 'listening' после прерывания")
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

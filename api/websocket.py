"""
WebSocket API для потокового голосового диалога
"""
import asyncio
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core import StateManager, DialogState, ActionManager
from config import SILENCE_THRESHOLD
from .websocket_helpers import send_greeting_directly, generate_and_send_response

router = APIRouter()

# Глобальные ссылки на модули (будут установлены в main.py)
streaming_stt_module = None
llm_module = None
tts_module = None


def init_modules(streaming_stt, llm, tts):
    """Инициализация модулей"""
    global streaming_stt_module, llm_module, tts_module
    streaming_stt_module = streaming_stt
    llm_module = llm
    tts_module = tts


@router.websocket("/ws/voice")
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

    # Создаем state manager для этой сессии
    state = StateManager()
    # Создаем action manager для этой сессии
    action_manager = ActionManager()
    recognizer = None
    last_transcript = ""

    # Флаг для прерывания генерации
    generation_interrupted = asyncio.Event()
    generation_task = None
    greeting_sent = False  # Флаг для отслеживания отправленного приветствия

    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "start_listening":
                # Очищаем историю при начале нового диалога
                llm_module.clear_history()
                action_manager.reset()
                greeting_sent = False

                # Начинаем слушать
                state.start_listening()
                recognizer = streaming_stt_module.create_recognizer()
                last_transcript = ""

                await websocket.send_json({
                    "type": "state",
                    "state": "listening"
                })

                # Автоматическое приветствие от Аси - отправляем напрямую, без ожидания LLM
                if not greeting_sent:
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
                # Получен чанк аудио
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
                except Exception as audio_error:
                    print(f"⚠️ Ошибка обработки аудио: {audio_error}")
                    import traceback
                    traceback.print_exc()
                    # Не прерываем весь WebSocket из-за одного плохого чанка
                    continue

            elif message_type == "speech_end":
                # Клиент детектировал конец речи
                try:
                    # Проверяем что мы в режиме listening
                    if state.current_state != DialogState.LISTENING:
                        continue

                    state.mark_silence_start()

                    # Ждем SILENCE_THRESHOLD секунд для финализации распознавания
                    await asyncio.sleep(SILENCE_THRESHOLD)

                    # Проверяем что тишина все еще продолжается
                    silence_duration = state.get_silence_duration()

                    if silence_duration and silence_duration >= SILENCE_THRESHOLD:
                        # Получаем финальный текст
                        try:
                            final_text = streaming_stt_module.finalize(recognizer)
                            if not final_text or not final_text.strip():
                                final_text = last_transcript
                        except Exception as finalize_error:
                            print(f"⚠️ Ошибка при finalize: {finalize_error}")
                            final_text = last_transcript

                        if final_text and final_text.strip():
                            # Фильтруем слишком короткие или неразборчивые тексты
                            cleaned_text = final_text.strip()
                            # Проверяем на слишком короткие тексты (менее 2 символов) или только спецсимволов
                            if len(cleaned_text) < 2 or cleaned_text.lower() in ['непонятно', 'непонятно почему', 'непонятно oy']:
                                # Создаем новый recognizer для следующей фразы
                                recognizer = streaming_stt_module.create_recognizer()
                                last_transcript = ""

                                # ВАЖНО: Возвращаемся в состояние listening
                                state.start_listening()
                                await websocket.send_json({
                                    "type": "state",
                                    "state": "listening"
                                })
                            else:
                                # Отправляем финальный текст клиенту
                                await websocket.send_json({
                                    "type": "final_transcript",
                                    "text": cleaned_text
                                })

                                # Добавляем в историю
                                state.add_to_history("user", cleaned_text)

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

                                # Сбрасываем флаг прерывания для новой генерации
                                generation_interrupted.clear()

                                # Запускаем генерацию в отдельной задаче
                                try:
                                    generation_task = asyncio.create_task(
                                        generate_and_send_response(websocket, cleaned_text, state,
                                                                 generation_interrupted, llm_module,
                                                                 tts_module, action_manager)
                                    )
                                except Exception as task_error:
                                    print(f"❌ Ошибка создания задачи генерации: {task_error}")
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
                            # Создаем новый recognizer для следующей фразы
                            recognizer = streaming_stt_module.create_recognizer()
                            last_transcript = ""

                            # ВАЖНО: Возвращаемся в состояние listening
                            state.start_listening()
                            await websocket.send_json({
                                "type": "state",
                                "state": "listening"
                            })
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
                    except Exception as recovery_error:
                        print(f"❌ Ошибка восстановления после speech_end: {recovery_error}")
                        raise

            elif message_type == "speaking_finished":
                # Воспроизведение ответа завершено, возвращаемся к прослушиванию
                state.start_listening()

                # ВАЖНО: Создаем НОВЫЙ recognizer для новой фразы
                recognizer = streaming_stt_module.create_recognizer()
                last_transcript = ""

                await websocket.send_json({
                    "type": "state",
                    "state": "listening"
                })

            elif message_type == "interrupt":
                # Прерывание воспроизведения
                if state.can_interrupt():
                    # Устанавливаем флаг прерывания
                    generation_interrupted.set()

                    # Отменяем задачу генерации если она выполняется
                    if generation_task and not generation_task.done():
                        generation_task.cancel()
                        try:
                            await generation_task
                        except asyncio.CancelledError:
                            pass
                        except Exception as e:
                            print(f"⚠️ Ошибка при отмене задачи генерации: {e}")

                    # Очищаем задачу
                    generation_task = None

                    state.start_listening()

                    # Создаем новый recognizer
                    recognizer = streaming_stt_module.create_recognizer()
                    last_transcript = ""

                    await websocket.send_json({
                        "type": "state",
                        "state": "listening"
                    })

            elif message_type == "stop":
                # Остановка диалога
                state.reset()
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

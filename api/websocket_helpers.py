"""
Вспомогательные функции для WebSocket endpoints
"""
import base64
import asyncio
import json
import re


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
    from utils import clean_text_from_markdown

    try:
        greeting_text = "Здравствуйте! Меня зовут Ася, я работаю в телеком компании. Чем могу помочь?"

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
        async for audio_chunk in tts_module.synthesize_stream(cleaned_greeting, language="ru"):
            # Проверяем прерывание
            if generation_interrupted.is_set():
                return

            audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')
            await websocket.send_json({
                "type": "audio_chunk",
                "data": audio_base64
            })

        # Отправляем конец потока
        await websocket.send_json({
            "type": "stream_end",
            "text": greeting_text
        })

        # Сохраняем приветствие в историю StateManager и LLM (для контекста)
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


def get_system_prompt_for_action(action_manager):
    """
    Получить системный промпт для работы с действиями

    Args:
        action_manager: экземпляр ActionManager

    Returns:
        Системный промпт
    """
    return action_manager.get_system_prompt()


async def generate_and_send_response(websocket, final_text, state, generation_interrupted,
                                    llm_module, tts_module, action_manager=None,
                                    system_prompt_override=None):
    """Генерирует ответ AI и отправляет клиенту с проверкой прерывания"""
    from utils import clean_text_from_markdown

    try:
        # Начинаем потоковую генерацию ответа
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
        tech_buffer = ""  # Буфер для накопления TECH блока
        tech_tag_open = False  # Флаг открытого TECH тега

        async for text_chunk in llm_module.generate_response_stream(final_text, system_prompt=system_prompt):
            # Проверяем флаг прерывания
            if generation_interrupted.is_set():
                return

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
                    try:
                        async for audio_chunk in tts_module.synthesize_stream(cleaned_sentence, language="ru"):
                            # Проверяем прерывание перед отправкой каждого аудио чанка
                            if generation_interrupted.is_set():
                                return

                            # Отправляем аудио чанк клиенту (base64)
                            audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')
                            await websocket.send_json({
                                "type": "audio_chunk",
                                "data": audio_base64
                            })
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
            except (json.JSONDecodeError, Exception):
                pass

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
            try:
                async for audio_chunk in tts_module.synthesize_stream(cleaned_buffer, language="ru"):
                    # Проверяем прерывание
                    if generation_interrupted.is_set():
                        return

                    audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')
                    await websocket.send_json({
                        "type": "audio_chunk",
                        "data": audio_base64
                    })
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
                # Обновляем состояние action_manager
                action_data = action_manager.update_from_parsed_data(parsed_data)
                # Используем очищенный текст для истории и TTS
                cleaned_response_for_history = cleaned_text
                # Отправляем action_data клиенту
                await websocket.send_json({
                    "type": "action_data",
                    "data": action_data
                })

        # Сохраняем очищенный ответ в историю (только если не было прерывания)
        if not generation_interrupted.is_set() and cleaned_response_for_history:
            state.add_to_history("assistant", cleaned_response_for_history)

        # Отправляем конец потока
        await websocket.send_json({
            "type": "stream_end",
            "text": cleaned_response_for_history if not generation_interrupted.is_set() else ""
        })
    except asyncio.CancelledError:
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

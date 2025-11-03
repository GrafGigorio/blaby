"""
REST API endpoint для голосового чата (старый API)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
from pathlib import Path

from config import UPLOAD_DIR, OUTPUT_DIR

router = APIRouter()

# Глобальные ссылки на модули (будут установлены в main.py)
stt_module = None
llm_module = None
tts_module = None


def init_modules(stt, llm, tts):
    """Инициализация модулей"""
    global stt_module, llm_module, tts_module
    stt_module = stt
    llm_module = llm
    tts_module = tts


@router.post("/api/voice-chat")
async def voice_chat(audio: UploadFile = File(...)):
    """
    Основной эндпоинт для голосового чата

    1. Принимает аудио файл
    2. Распознает речь (STT)
    3. Генерирует ответ (LLM)
    4. Синтезирует речь (TTS)
    5. Возвращает аудио ответ
    """
    from utils import clean_text_from_markdown

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


@router.post("/api/clear-history")
async def clear_history():
    """Очистка истории разговора"""
    llm_module.clear_history()
    return {"status": "success", "message": "История очищена"}

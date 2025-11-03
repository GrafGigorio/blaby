"""
Конфигурация приложения
"""
from pathlib import Path

# Директории
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
STATIC_DIR = BASE_DIR / "static"

# Создаем директории если не существуют
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Настройки сервера
HOST = "0.0.0.0"
PORT = 8000

# Настройки моделей
DEFAULT_STT_MODEL = "medium"  # tiny, base, small, medium, large
DEFAULT_LLM_MODEL = "gpt-oss:20b"
DEFAULT_TTS_VOICE_RU = "ru-RU-SvetlanaNeural"
DEFAULT_TTS_VOICE_EN = "en-US-JennyNeural"

# Настройки Vosk (для потокового распознавания)
VOSK_MODEL_PATH = BASE_DIR / "models" / "vosk-model-ru-0.42"  # Полная модель для лучшего качества
# Альтернатива (маленькая модель): "vosk-model-small-ru-0.22"

# Настройки VAD (Voice Activity Detection)
SILENCE_THRESHOLD = 1.5  # секунды тишины после речи

# Настройки LLM
MAX_CONVERSATION_HISTORY = 10  # максимальное количество сообщений в истории

# Системный промпт по умолчанию
DEFAULT_SYSTEM_PROMPT = "Ты - полезный голосовой ассистент. Отвечай кратко и по делу, поскольку твой ответ будет озвучен."

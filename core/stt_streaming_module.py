"""
Streaming Speech-to-Text модуль используя Vosk
"""
import json
import os
import urllib.request
import zipfile
import shutil
from pathlib import Path
from vosk import Model, KaldiRecognizer
from config import VOSK_MODEL_PATH, BASE_DIR


def download_vosk_model(model_name="vosk-model-small-ru-0.22", models_dir=None):
    """
    Автоматически скачивает и распаковывает модель Vosk

    Args:
        model_name: имя модели для скачивания
        models_dir: директория для моделей (по умолчанию BASE_DIR / "models")

    Returns:
        Path: путь к распакованной модели

    Raises:
        Exception: если не удалось скачать или распаковать модель
    """
    if models_dir is None:
        models_dir = BASE_DIR / "models"

    models_dir.mkdir(exist_ok=True)

    model_path = models_dir / model_name

    # Если модель уже существует, возвращаем путь
    if model_path.exists():
        return model_path

    print(f"📥 Модель {model_name} не найдена. Начинаем загрузку...")

    # URL модели
    model_url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    zip_path = models_dir / f"{model_name}.zip"

    try:
        # Скачиваем архив
        print(f"Скачивание из {model_url}...")
        print("Это может занять несколько минут (размер ~45 МБ для small, ~1.5 ГБ для full)...")

        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100) if total_size > 0 else 0
            print(f"\rПрогресс: {percent:.1f}%", end='', flush=True)

        urllib.request.urlretrieve(model_url, zip_path, show_progress)
        print("\n✅ Загрузка завершена")

        # Распаковываем
        print(f"📦 Распаковка {model_name}.zip...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        print("✅ Распаковка завершена")

        # Удаляем архив
        zip_path.unlink()

        # Проверяем что модель распаковалась
        if not model_path.exists():
            raise FileNotFoundError(f"Модель не была распакована в {model_path}")

        print(f"✅ Модель {model_name} успешно установлена в {model_path}")
        return model_path

    except Exception as e:
        # Очищаем частично скачанные файлы
        if zip_path.exists():
            zip_path.unlink()
        if model_path.exists():
            shutil.rmtree(model_path, ignore_errors=True)
        raise Exception(f"Не удалось скачать модель: {e}")


def find_available_vosk_model(preferred_path=None, models_dir=None):
    """
    Находит доступную модель Vosk, при необходимости скачивает указанную модель

    Args:
        preferred_path: предпочтительный путь к модели (из config)
        models_dir: директория для моделей

    Returns:
        Path: путь к доступной модели
    """
    if models_dir is None:
        models_dir = BASE_DIR / "models"

    # Сначала проверяем предпочтительную модель
    if preferred_path and preferred_path.exists():
        return preferred_path

    # Если предпочтительной модели нет, пытаемся скачать её
    if preferred_path:
        model_name = preferred_path.name
        print(f"⚠️  Указанная модель {model_name} не найдена")
        print(f"📥 Автоматически скачиваем указанную модель {model_name}...")
        try:
            return download_vosk_model(model_name, models_dir)
        except Exception as e:
            print(f"❌ Не удалось скачать указанную модель {model_name}: {e}")
            print("ℹ️  Пытаемся использовать альтернативную модель...")
            # Если скачивание не удалось, используем альтернативу как fallback
            pass

    # Fallback: проверяем альтернативные модели (сначала маленькая, потом большая)
    alternative_models = ["vosk-model-small-ru-0.22", "vosk-model-ru-0.42"]

    for model_name in alternative_models:
        model_path = models_dir / model_name
        if model_path.exists():
            print(f"ℹ️  Используем найденную альтернативную модель {model_name}")
            return model_path

    # Если ничего не найдено и нет предпочтительной, скачиваем маленькую модель
    print("⚠️  Ни одна модель Vosk не найдена")
    print(f"📥 Автоматически скачиваем vosk-model-small-ru-0.22...")
    return download_vosk_model("vosk-model-small-ru-0.22", models_dir)


class StreamingSTTModule:
    def __init__(self, model_path=None, sample_rate=16000):
        """
        Инициализация Vosk модели для потокового распознавания

        Args:
            model_path: путь к модели Vosk (если None, используется из config.VOSK_MODEL_PATH)
            sample_rate: частота дискретизации аудио (по умолчанию 16000 Hz)
        """
        if model_path is None:
            model_path = VOSK_MODEL_PATH

        # Автоматически находим или скачиваем модель, если её нет
        if not os.path.exists(model_path):
            model_path = find_available_vosk_model(preferred_path=model_path)

        print(f"Загрузка Vosk модели из {model_path}...")
        print(f"Размер модели: {model_path.name}")
        self.model = Model(str(model_path))
        self.sample_rate = sample_rate
        print("Vosk модель загружена успешно ✓")

    def create_recognizer(self):
        """
        Создать новый распознаватель для потока

        Returns:
            KaldiRecognizer instance
        """
        return KaldiRecognizer(self.model, self.sample_rate)

    def process_chunk(self, recognizer, audio_chunk):
        """
        Обработать чанк аудио

        Args:
            recognizer: KaldiRecognizer instance
            audio_chunk: байты аудио данных

        Returns:
            dict: {
                "partial": bool - промежуточный результат или финальный,
                "text": str - распознанный текст,
                "is_final": bool - является ли результат финальным
            }
        """
        if recognizer.AcceptWaveform(audio_chunk):
            # Финальный результат
            result = json.loads(recognizer.Result())
            text = result.get("text", "")
            return {
                "partial": False,
                "text": text.strip(),
                "is_final": True
            }
        else:
            # Промежуточный результат
            partial_result = json.loads(recognizer.PartialResult())
            text = partial_result.get("partial", "")
            return {
                "partial": True,
                "text": text.strip(),
                "is_final": False
            }

    def finalize(self, recognizer):
        """
        Получить финальный результат из распознавателя

        Args:
            recognizer: KaldiRecognizer instance

        Returns:
            str: финальный распознанный текст
        """
        final_result = json.loads(recognizer.FinalResult())
        return final_result.get("text", "").strip()

    def is_sentence_complete(self, text):
        """
        Проверить, является ли предложение завершенным

        Args:
            text: распознанный текст

        Returns:
            bool: True если предложение завершено (есть знаки препинания)
        """
        if not text:
            return False

        # Проверяем наличие завершающих знаков препинания
        ending_punctuation = ['.', '!', '?', '...']
        return any(text.strip().endswith(punct) for punct in ending_punctuation)

"""
Streaming Speech-to-Text модуль используя Vosk
"""
import json
import os
from pathlib import Path
from vosk import Model, KaldiRecognizer


class StreamingSTTModule:
    def __init__(self, model_path=None, sample_rate=16000):
        """
        Инициализация Vosk модели для потокового распознавания

        Args:
            model_path: путь к модели Vosk (если None, используется models/vosk-model-small-ru-0.22)
            sample_rate: частота дискретизации аудио (по умолчанию 16000 Hz)
        """
        if model_path is None:
            model_path = Path(__file__).parent / "models" / "vosk-model-small-ru-0.22"

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Модель Vosk не найдена по пути: {model_path}")

        print(f"Загрузка Vosk модели из {model_path}...")
        self.model = Model(str(model_path))
        self.sample_rate = sample_rate
        print("Vosk модель загружена успешно")

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

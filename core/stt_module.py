"""
Speech-to-Text модуль используя OpenAI Whisper
"""
import whisper
import torch
from pathlib import Path


class STTModule:
    def __init__(self, model_size="base"):
        """
        Инициализация Whisper модели

        Args:
            model_size: размер модели (tiny, base, small, medium, large)
                       base - хороший баланс скорости и качества
        """
        print(f"Загрузка Whisper модели ({model_size})...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model(model_size, device=self.device)
        print(f"Whisper модель загружена на {self.device}")

    def transcribe(self, audio_path: str, language: str = "ru") -> str:
        """
        Распознавание речи из аудио файла

        Args:
            audio_path: путь к аудио файлу
            language: язык распознавания (ru, en, etc.)

        Returns:
            Распознанный текст
        """
        try:
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=False  # для CPU
            )
            return result["text"].strip()
        except Exception as e:
            print(f"Ошибка распознавания: {e}")
            return ""

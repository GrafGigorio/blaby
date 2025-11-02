"""
Text-to-Speech модуль используя Edge TTS
"""
import edge_tts
import asyncio
from pathlib import Path


class TTSModule:
    def __init__(self):
        """
        Инициализация Edge TTS
        Используем Microsoft Edge TTS API для качественного русского голоса
        """
        print("Инициализация TTS модуля (Edge TTS)...")
        # Используем женский русский голос
        self.voice = "ru-RU-SvetlanaNeural"
        print(f"TTS модуль готов (голос: {self.voice})")

    async def synthesize_async(self, text: str, output_path: str, language: str = "ru") -> bool:
        """
        Синтез речи из текста (асинхронный метод)

        Args:
            text: текст для озвучивания
            output_path: путь для сохранения аудио файла
            language: язык синтеза

        Returns:
            True если успешно, False если ошибка
        """
        try:
            # Создаем директорию если не существует
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Выбираем голос в зависимости от языка
            voice = self.voice
            if language == "en":
                voice = "en-US-JennyNeural"

            # Генерируем аудио асинхронно
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

            print(f"Аудио сохранено: {output_path}")
            return True

        except Exception as e:
            print(f"Ошибка синтеза речи: {e}")
            return False

    async def synthesize_stream(self, text: str, language: str = "ru"):
        """
        Потоковый синтез речи из текста (асинхронный генератор)

        Args:
            text: текст для озвучивания
            language: язык синтеза

        Yields:
            bytes: чанки аудио данных в формате MP3 (совместимо с Safari)
        """
        try:
            # Выбираем голос в зависимости от языка
            voice = self.voice
            if language == "en":
                voice = "en-US-JennyNeural"

            # Создаем Communicate объект с MP3 форматом для совместимости с Safari
            # audio-24khz-48kbitrate-mono-mp3 - хорошее качество и небольшой размер
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate="+0%",
                volume="+0%",
                pitch="+0Hz"
            )

            # Edge TTS возвращает генератор чанков
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]

        except Exception as e:
            print(f"Ошибка потокового синтеза речи: {e}")
            raise

    def synthesize(self, text: str, output_path: str, language: str = "ru") -> bool:
        """
        Синхронная обертка для синтеза речи (для обратной совместимости)
        """
        try:
            # Получаем или создаем event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Нет активного event loop, создаем новый
                return asyncio.run(self.synthesize_async(text, output_path, language))
            else:
                # Уже есть event loop, используем run_until_complete в новом потоке
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.synthesize_async(text, output_path, language)
                    )
                    return future.result()
        except Exception as e:
            print(f"Ошибка синтеза речи: {e}")
            return False

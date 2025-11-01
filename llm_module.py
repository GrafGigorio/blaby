"""
LLM модуль для работы с Ollama
"""
import ollama
from typing import List, Dict


class LLMModule:
    def __init__(self, model_name: str = "gpt-oss:20b"):
        """
        Инициализация Ollama клиента

        Args:
            model_name: имя модели в Ollama
        """
        self.model_name = model_name
        self.conversation_history: List[Dict[str, str]] = []
        print(f"LLM модуль инициализирован с моделью: {model_name}")

    def generate_response(self, user_input: str, system_prompt: str = None) -> str:
        """
        Генерация ответа от LLM

        Args:
            user_input: текст от пользователя
            system_prompt: системный промпт (опционально)

        Returns:
            Ответ от модели
        """
        try:
            # Добавляем сообщение пользователя в историю
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })

            # Формируем сообщения для модели
            messages = []

            # Добавляем системный промпт если есть
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            # Добавляем историю (последние 10 сообщений)
            messages.extend(self.conversation_history[-10:])

            # Получаем ответ от Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=messages
            )

            assistant_message = response['message']['content']

            # Сохраняем ответ в историю
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            print(f"Ошибка генерации ответа: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса."

    def clear_history(self):
        """Очистка истории разговора"""
        self.conversation_history = []
        print("История разговора очищена")

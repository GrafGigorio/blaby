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
        # Создаем асинхронный клиент для неблокирующих запросов
        self.async_client = ollama.AsyncClient()
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

    async def generate_response_async(self, user_input: str, system_prompt: str = None) -> str:
        """
        Асинхронная генерация ответа от LLM (неблокирующий метод)

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

            # Получаем ответ от Ollama асинхронно
            response = await self.async_client.chat(
                model=self.model_name,
                messages=messages
            )

            assistant_message = response.message.content

            # Сохраняем ответ в историю
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except Exception as e:
            print(f"Ошибка генерации ответа: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса."

    async def generate_response_stream(self, user_input: str, system_prompt: str = None):
        """
        Потоковая генерация ответа от LLM (асинхронный генератор)
        
        Args:
            user_input: текст от пользователя
            system_prompt: системный промпт (опционально)
            
        Yields:
            str: части ответа по мере генерации
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
            
            # Получаем потоковый ответ от Ollama
            full_response = ""
            async for chunk in await self.async_client.chat(
                model=self.model_name,
                messages=messages,
                stream=True
            ):
                content = chunk.message.content
                if content:
                    full_response += content
                    yield content
            
            # Сохраняем полный ответ в историю
            if full_response:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                
        except Exception as e:
            print(f"Ошибка потоковой генерации ответа: {e}")
            yield "Извините, произошла ошибка при обработке вашего запроса."

    def clear_history(self):
        """Очистка истории разговора"""
        self.conversation_history = []
        print("История разговора очищена")

    def set_model(self, model_name: str):
        """
        Смена активной модели

        Args:
            model_name: имя новой модели в Ollama
        """
        self.model_name = model_name
        print(f"Модель изменена на: {model_name}")

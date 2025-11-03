"""
Action Manager - модуль для управления действиями и извлечения данных из JSON-ответов LLM
"""
import json
import re
from typing import Dict, Optional, Any


class ActionManager:
    """Менеджер действий для обработки подключения интернета"""
    
    # Конфигурация тарифов
    TARIFFS = {
        "Краснодар": {
            "Зеленый": {"speed": "10 Гбит/с", "price": 100},
            "Желтый": {"speed": "20 Гбит/с", "price": 200},
            "Красный": {"speed": "30 Гбит/с", "price": 300}
        },
        "Станица Выселки": {
            "Аметист": {"speed": "10 Гбит/с", "price": 110},
            "Топаз": {"speed": "20 Гбит/с", "price": 220},
            "Брильянт": {"speed": "30 Гбит/с", "price": 330}
        }
    }
    
    def __init__(self):
        """Инициализация ActionManager"""
        self.current_action = None  # "internet_connection" | None
        self.current_stage = None  # "city_selection" | "tariff_selection" | "contact_info" | None
        self.collected_data = {
            "city": None,
            "tariff": None,
            "name": None,
            "phone": None,
            "address": None
        }
    
    def reset(self):
        """Сброс состояния действия"""
        self.current_action = None
        self.current_stage = None
        self.collected_data = {
            "city": None,
            "tariff": None,
            "name": None,
            "phone": None,
            "address": None
        }
    
    def get_tariffs_for_city(self, city: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Получить тарифы для города
        
        Args:
            city: название города
            
        Returns:
            Словарь тарифов или None если город не найден
        """
        return self.TARIFFS.get(city)
    
    def get_system_prompt(self) -> str:
        """
        Получить системный промпт для LLM
        
        Returns:
            Системный промпт с инструкциями
        """
        tariffs_info = ""
        for city, tariffs in self.TARIFFS.items():
            tariffs_info += f"\n{city}:\n"
            for name, info in tariffs.items():
                tariffs_info += f"  - {name}: {info['speed']}, {info['price']} рублей в месяц\n"
        
        return f"""Ты - Ася, голосовой ассистент телеком компании. Ты работаешь в компании, которая предоставляет услуги интернета.

При знакомстве с новым клиентом представься: "Здравствуйте! Меня зовут Ася, я работаю в телеком компании. Чем могу помочь?"

Твоя главная задача - помочь клиентам подключить интернет. Ты вежлива, дружелюбна и профессиональна.

ТЫ ОБЯЗАНА ВСЕГДА ВОЗВРАЩАТЬ ОТВЕТ В ФОРМАТЕ JSON. Каждый твой ответ должен содержать JSON объект в следующем формате:

{{
  "action": "internet_connection" | null,
  "stage": "city_selection" | "tariff_selection" | "contact_info" | null,
  "data": {{
    "city": "Краснодар" | "Станица Выселки" | null,
    "tariff": название тарифа | null,
    "name": имя клиента | null,
    "phone": телефон клиента | null,
    "address": адрес клиента | null
  }},
  "response_text": "текст для озвучивания пользователю (БЕЗ JSON, просто обычный текст)"
}}

КРИТИЧЕСКИ ВАЖНО - ФОРМАТ ОТВЕТА:
Весь JSON должен быть обернут в специальные маркеры технической информации:
<TECH>
{{ JSON здесь }}
</TECH>
А текст для озвучивания должен быть ВНЕ этих маркеров.

Пример правильного ответа:
Конечно! Я могу помочь вам подключить интернет. <TECH>{{"action":"internet_connection","stage":"city_selection","data":{{"city":null,"tariff":null,"name":null,"phone":null,"address":null}},"response_text":"В каком городе вы хотите подключить интернет?"}}</TECH> В каком городе вы хотите подключить интернет?

ПРАВИЛА РАБОТЫ:
1. Если пользователь хочет подключить интернет, устанавливай action: "internet_connection"
2. Этапы работы:
   - city_selection: спрашивай в каком городе нужно подключить интернет
   - tariff_selection: после выбора города предлагай тарифы для этого города
   - contact_info: после выбора тарифа спрашивай контактные данные (имя, телефон, адрес)
3. Всегда обновляй поля data в JSON с полученными данными от пользователя
4. В response_text пиши только текст для озвучивания, БЕЗ упоминания JSON
5. ВСЕГДА оборачивай JSON в <TECH>...</TECH> маркеры, чтобы он не озвучивался

ДОСТУПНЫЕ ТАРИФЫ:
{tariffs_info}

ВАЖНО: JSON должен быть валидным! Всегда экранируй кавычки внутри строк, используй правильные типы данных."""

    def parse_llm_response(self, text: str) -> tuple[Optional[Dict[str, Any]], str]:
        """
        Парсинг ответа от LLM для извлечения JSON
        
        Args:
            text: текст ответа от LLM
            
        Returns:
            Кортеж (parsed_data, cleaned_text) где:
            - parsed_data: распарсенный JSON объект или None
            - cleaned_text: текст без JSON для TTS
        """
        # Сначала пытаемся найти JSON в технических маркерах <TECH>...</TECH>
        tech_pattern = r'<TECH>(.*?)</TECH>'
        tech_matches = re.findall(tech_pattern, text, re.DOTALL | re.IGNORECASE)
        
        parsed_data = None
        cleaned_text = text
        
        # Пытаемся распарсить JSON из технических блоков
        for tech_content in tech_matches:
            # Ищем JSON внутри технического блока
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, tech_content, re.DOTALL)
            
            for match in json_matches:
                try:
                    # Пытаемся распарсить JSON
                    data = json.loads(match)
                    if isinstance(data, dict) and "response_text" in data:
                        parsed_data = data
                        # Заменяем JSON на текст для озвучивания
                        cleaned_text = data.get("response_text", cleaned_text)
                        # Удаляем весь технический блок из текста
                        cleaned_text = re.sub(r'<TECH>.*?</TECH>', '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
                        break
                except json.JSONDecodeError:
                    continue
            
            if parsed_data:
                break
        
        # Если JSON не найден в технических блоках, пытаемся найти его в тексте напрямую
        if parsed_data is None:
            # JSON может быть в фигурных скобках {...}
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, cleaned_text, re.DOTALL)
            
            for match in matches:
                try:
                    # Пытаемся распарсить JSON
                    data = json.loads(match)
                    if isinstance(data, dict) and "response_text" in data:
                        parsed_data = data
                        # Заменяем JSON на текст для озвучивания
                        cleaned_text = data.get("response_text", cleaned_text)
                        # Удаляем JSON из текста, если он там остался
                        cleaned_text = re.sub(re.escape(match), "", cleaned_text, flags=re.DOTALL).strip()
                        break
                except json.JSONDecodeError:
                    continue
        
        # Если JSON не найден, пытаемся найти его в многострочном формате
        if parsed_data is None:
            # Ищем JSON между ```json и ``` или просто в фигурных скобках
            json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            json_block_match = re.search(json_block_pattern, cleaned_text, re.DOTALL)
            if json_block_match:
                try:
                    data = json.loads(json_block_match.group(1))
                    if isinstance(data, dict) and "response_text" in data:
                        parsed_data = data
                        cleaned_text = data.get("response_text", cleaned_text)
                        cleaned_text = re.sub(re.escape(json_block_match.group(0)), "", cleaned_text, flags=re.DOTALL).strip()
                except json.JSONDecodeError:
                    pass
        
        # ВАЖНО: Удаляем все оставшиеся технические блоки, даже если они не содержат JSON
        # Это гарантирует, что никакая техническая информация не попадет в TTS
        cleaned_text = re.sub(r'<TECH>.*?</TECH>', '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        # Удаляем незакрытые теги (на случай если они разорваны потоковой передачей)
        cleaned_text = re.sub(r'<TECH>.*', '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        cleaned_text = re.sub(r'.*?</TECH>', '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        
        return parsed_data, cleaned_text
    
    def update_from_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновить состояние на основе распарсенных данных
        
        Args:
            parsed_data: распарсенный JSON объект
            
        Returns:
            Обновленные данные для отправки клиенту
        """
        # Обновляем действие
        if parsed_data.get("action"):
            self.current_action = parsed_data["action"]
        
        # Обновляем этап
        if parsed_data.get("stage"):
            self.current_stage = parsed_data["stage"]
        
        # Обновляем собранные данные
        data = parsed_data.get("data", {})
        if data.get("city"):
            self.collected_data["city"] = data["city"]
        if data.get("tariff"):
            self.collected_data["tariff"] = data["tariff"]
        if data.get("name"):
            self.collected_data["name"] = data["name"]
        if data.get("phone"):
            self.collected_data["phone"] = data["phone"]
        if data.get("address"):
            self.collected_data["address"] = data["address"]
        
        # Формируем ответ для клиента
        return {
            "action": self.current_action,
            "stage": self.current_stage,
            "data": self.collected_data.copy(),
            "is_complete": self.is_data_complete()
        }
    
    def is_data_complete(self) -> bool:
        """
        Проверить, все ли данные собраны для заявки
        
        Returns:
            True если все данные собраны
        """
        return (
            self.current_action == "internet_connection" and
            self.collected_data["city"] is not None and
            self.collected_data["tariff"] is not None and
            self.collected_data["name"] is not None and
            self.collected_data["phone"] is not None and
            self.collected_data["address"] is not None
        )
    
    def get_tariff_info(self, city: str, tariff: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о тарифе
        
        Args:
            city: город
            tariff: название тарифа
            
        Returns:
            Информация о тарифе или None
        """
        city_tariffs = self.get_tariffs_for_city(city)
        if city_tariffs:
            return city_tariffs.get(tariff)
        return None


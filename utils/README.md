# Utility Modules

Вспомогательные модули для поддержки основной функциональности.

## Модули

### port_manager.py
Управление портами для веб-сервера.
- Автоматический поиск свободных портов
- Проверка доступности портов
- Конфигурация сетевых параметров

### text_cleaning.py
Обработка и очистка текста.
- Удаление технических маркеров (TECH блоков)
- Форматирование текста для TTS
- Фильтрация JSON и служебной информации
- Предобработка текста перед озвучиванием

## Использование

### Port Manager

```python
from utils.port_manager import find_free_port

port = find_free_port(start_port=8000)
print(f"Using port: {port}")
```

### Text Cleaning

```python
from utils.text_cleaning import clean_text_for_tts

text = "TECH:system_info Привет! Как дела?"
cleaned = clean_text_for_tts(text)
# Результат: "Привет! Как дела?"
```

## Функции Text Cleaning

- `clean_text_for_tts(text)` - Основная функция очистки текста
  - Удаляет TECH блоки
  - Удаляет JSON структуры
  - Удаляет технические маркеры
  - Нормализует пробелы

- `remove_tech_blocks(text)` - Удаление блоков с маркером TECH
- `remove_json_structures(text)` - Удаление JSON объектов из текста
- `normalize_whitespace(text)` - Нормализация пробелов и переносов строк

## Назначение

Эти модули обеспечивают:
- Гибкость в управлении сетевыми параметрами
- Чистоту озвучиваемого текста
- Отделение технической информации от пользовательского контента

# Установка Vosk модели для потокового распознавания

## Быстрая установка (рекомендуется)

Для лучшего качества распознавания установите полную модель:

```bash
# Создайте директорию для моделей (если не существует)
mkdir -p models

# Перейдите в директорию
cd models

# Скачайте модель (1.5 ГБ)
curl -O https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip

# Распакуйте
unzip vosk-model-ru-0.42.zip

# Удалите архив (опционально)
rm vosk-model-ru-0.42.zip

# Вернитесь в корень проекта
cd ..
```

## Альтернатива: Легкая модель

Если у вас ограниченное место на диске или слабый ПК:

```bash
mkdir -p models
cd models
curl -O https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
unzip vosk-model-small-ru-0.22.zip
rm vosk-model-small-ru-0.22.zip
cd ..
```

И измените в `config.py`:
```python
VOSK_MODEL_PATH = BASE_DIR / "models" / "vosk-model-small-ru-0.22"
```

## Проверка установки

После установки структура должна быть:
```
blaBy/
└── models/
    └── vosk-model-ru-0.42/
        ├── am/
        ├── graph/
        ├── ivector/
        └── conf/
```

## Что дальше?

1. Запустите приложение: `python main.py`
2. Модель загрузится автоматически при первом использовании WebSocket
3. Проверьте в консоли сообщение "Vosk модель загружена успешно ✓"

## Дополнительная информация

Подробное руководство: [docs/guides/STT_MODELS.md](docs/guides/STT_MODELS.md)

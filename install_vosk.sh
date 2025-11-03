#!/bin/bash

# Скрипт установки Vosk модели для распознавания речи

echo "==================================="
echo "Установка Vosk модели"
echo "==================================="
echo ""

# Проверяем наличие директории models
if [ ! -d "models" ]; then
    echo "Создаём директорию models/"
    mkdir -p models
fi

cd models

# Спрашиваем пользователя какую модель установить
echo "Выберите модель для установки:"
echo "1) vosk-model-ru-0.42 (1.5 ГБ) - Лучшее качество [РЕКОМЕНДУЕТСЯ]"
echo "2) vosk-model-small-ru-0.22 (45 МБ) - Быстрая работа"
echo ""
read -p "Введите номер (1 или 2): " choice

case $choice in
    1)
        MODEL_NAME="vosk-model-ru-0.42"
        MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip"
        MODEL_SIZE="1.5 ГБ"
        ;;
    2)
        MODEL_NAME="vosk-model-small-ru-0.22"
        MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
        MODEL_SIZE="45 МБ"
        ;;
    *)
        echo "Неверный выбор. Выход."
        exit 1
        ;;
esac

echo ""
echo "Выбрана модель: $MODEL_NAME ($MODEL_SIZE)"
echo ""

# Проверяем, не установлена ли уже модель
if [ -d "$MODEL_NAME" ]; then
    echo "⚠️  Модель $MODEL_NAME уже установлена!"
    read -p "Переустановить? (y/n): " reinstall
    if [ "$reinstall" != "y" ]; then
        echo "Установка отменена."
        exit 0
    fi
    rm -rf "$MODEL_NAME"
fi

# Скачиваем модель
echo "📥 Скачивание модели..."
echo "URL: $MODEL_URL"
echo ""

if command -v curl &> /dev/null; then
    curl -# -O "$MODEL_URL"
elif command -v wget &> /dev/null; then
    wget --show-progress "$MODEL_URL"
else
    echo "❌ Ошибка: curl или wget не найдены. Установите один из них."
    exit 1
fi

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при скачивании модели."
    exit 1
fi

# Распаковываем
echo ""
echo "📦 Распаковка..."
unzip -q "$MODEL_NAME.zip"

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при распаковке."
    exit 1
fi

# Удаляем архив
rm "$MODEL_NAME.zip"

cd ..

# Обновляем config.py (если выбрана маленькая модель)
if [ "$choice" = "2" ]; then
    echo ""
    echo "⚠️  Не забудьте обновить config.py:"
    echo "VOSK_MODEL_PATH = BASE_DIR / \"models\" / \"$MODEL_NAME\""
fi

echo ""
echo "✅ Модель $MODEL_NAME успешно установлена!"
echo ""
echo "Структура:"
echo "models/"
echo "└── $MODEL_NAME/"
echo "    ├── am/"
echo "    ├── graph/"
echo "    ├── ivector/"
echo "    └── conf/"
echo ""
echo "Теперь можно запустить приложение: python main.py"
echo ""

#!/bin/bash

echo "==================================="
echo "Voice AI Assistant - Запуск"
echo "==================================="

# Проверяем, запущена ли Ollama
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama не запущена. Запускаем..."
    ollama serve &
    sleep 3
fi

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости если нужно
if [ ! -f "venv/.installed" ]; then
    echo "📥 Установка зависимостей (это может занять некоторое время)..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.installed
fi

# Запускаем приложение
echo "🚀 Запуск приложения..."
echo "Откройте в браузере: http://localhost:8000"
echo "==================================="
python main.py

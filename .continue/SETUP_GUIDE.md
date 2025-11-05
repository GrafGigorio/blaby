# 🚀 Полное руководство по настройке Continue с LM Studio

## Для Mac M4 Max (48GB RAM)

---

## 📋 Оглавление

1. [Установка и настройка LM Studio](#1-установка-и-настройка-lm-studio)
2. [Скачивание рекомендуемых моделей](#2-скачивание-рекомендуемых-моделей)
3. [Запуск Local Server](#3-запуск-local-server)
4. [Настройка Continue](#4-настройка-continue)
5. [Тестирование](#5-тестирование)
6. [Дополнительные MCP серверы](#6-дополнительные-mcp-серверы)
7. [Решение проблем](#7-решение-проблем)

---

## 1. Установка и настройка LM Studio

### Шаг 1.1: Установка (если ещё не установлен)

1. Скачайте LM Studio с официального сайта: https://lmstudio.ai/
2. Установите приложение в `/Applications/`
3. Запустите LM Studio

### Шаг 1.2: Первоначальная настройка

1. При первом запуске LM Studio попросит выбрать папку для моделей
2. Рекомендую: `/Users/grafgrigorio/.lmstudio/models/` (по умолчанию)
3. Модели занимают много места - убедитесь что на диске достаточно свободного места
   - Минимум: 50GB
   - Рекомендовано: 100GB+

---

## 2. Скачивание рекомендуемых моделей

### Шаг 2.1: Обязательные модели

#### 🎯 **Hermes-3-Llama-3.1-8B** (для Agent режима)

1. В LM Studio нажмите на иконку **🔍 Search** в левом меню
2. Введите: `NousResearch/Hermes-3-Llama-3.1-8B`
3. Найдите версию с квантизацией **Q5_K_M** или **Q6_K**
   - `Hermes-3-Llama-3.1-8B-Q5_K_M.gguf` (~6GB) ⭐ Рекомендовано
   - `Hermes-3-Llama-3.1-8B-Q6_K.gguf` (~7GB) - максимальное качество
4. Нажмите кнопку **Download**
5. Дождитесь завершения загрузки

#### 💪 **Qwen2.5-Coder-32B** (основная рабочая модель)

1. В Search введите: `Qwen/Qwen2.5-Coder-32B-Instruct`
2. Выберите квантизацию **Q5_K_M**
   - `qwen2.5-coder-32b-instruct-q5_k_m.gguf` (~23GB)
3. Download → дождитесь загрузки

#### ⚡ **StarCoder2-3B** (для автокомплита)

1. Search: `bigcode/starcoder2-3b`
2. Квантизация: **Q6_K**
   - `starcoder2-3b-q6_k.gguf` (~2GB)
3. Download

**Итого загрузок: ~31GB**
**Время загрузки:** 15-30 минут (зависит от интернета)

### Шаг 2.2: Дополнительные модели (опционально)

#### 🧠 **Mistral-Small-Instruct-2409** (продвинутый Agent)

1. Search: `mistralai/Mistral-Small-Instruct-2409`
2. Квантизация: **Q5_K_M** (~16GB)
3. Download

#### 🔍 **DeepSeek-Coder-V2-16B**

1. Search: `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`
2. Квантизация: **Q5_K_M** (~11GB)
3. Download

---

## 3. Запуск Local Server

### Шаг 3.1: Загрузка модели в сервер

1. В LM Studio нажмите на иконку **💻 Local Server** в левом меню
2. В выпадающем списке "Select a model to load" выберите:
   - **Hermes-3-Llama-3.1-8B-Q5_K_M.gguf** (начните с этой)
3. Нажмите кнопку **Load Model**
4. Дождитесь сообщения "Model loaded successfully"

### Шаг 3.2: Настройка сервера

В разделе **Server Options**:

```
Port: 1234  (оставьте по умолчанию)
CORS: Enabled  ✅
API Key: (оставьте пустым для локальной разработки)
```

**Важные настройки для M4 Max:**

- **GPU Offload:** 100% (используйте всю мощь Metal)
- **Context Length:** 8192 или 16384 (зависит от модели)
- **Temperature:** 0.7 (можно настроить в Continue)
- **Max Tokens:** 4096

### Шаг 3.3: Запуск сервера

1. Нажмите большую зелёную кнопку **Start Server**
2. Вы должны увидеть:
   ```
   ✅ Server running on http://localhost:1234
   ```
3. Сервер готов принимать запросы!

### Шаг 3.4: Тестирование сервера

Откройте терминал и выполните:

```bash
curl http://localhost:1234/v1/models

# Должен вернуть JSON с информацией о модели
```

Если видите JSON ответ - сервер работает! ✅

---

## 4. Настройка Continue

### Шаг 4.1: Активация новой конфигурации

```bash
cd /Users/grafgrigorio/claude_projects/blaBy

# Сохраните старую конфигурацию на всякий случай
cp .continue/config.yaml .continue/config.yaml.backup

# Активируйте LM Studio конфиг
cp .continue/lmstudio-config.yaml .continue/config.yaml
```

### Шаг 4.2: Проверка конфигурации

Откройте `.continue/config.yaml` и убедитесь что:

1. `provider: lmstudio` для всех моделей
2. `apiBase: http://localhost:1234/v1` везде правильный
3. `model:` совпадает с именем загруженной модели

**Пример для Hermes:**
```yaml
- name: 🤖 Agent (Hermes 8B)
  provider: lmstudio
  model: hermes-3-llama-3.1-8b  # ← Должен совпадать с именем в LM Studio
  apiBase: http://localhost:1234/v1
```

**Важно:** Имя модели (`model:`) должно соответствовать тому, что показывает LM Studio.
Проверить можно так:

```bash
curl http://localhost:1234/v1/models | grep -o '"id":"[^"]*"'
# Скопируйте id и вставьте в конфиг
```

### Шаг 4.3: Перезапуск VS Code

1. Полностью закройте VS Code: `Cmd + Q`
2. Откройте заново
3. Continue автоматически загрузит новую конфигурацию

---

## 5. Тестирование

### Тест 5.1: Проверка подключения

1. В VS Code откройте Continue: `Cmd + L`
2. В выпадающем списке моделей выберите: **🤖 Agent (Hermes 8B)**
3. Напишите простой запрос: "Привет, ты работаешь?"
4. Должен прийти ответ от модели

### Тест 5.2: Проверка Chat режима

```
Запрос: Объясни что такое async/await в Python
```

Модель должна дать развёрнутый ответ.

### Тест 5.3: Проверка Agent режима (с MCP tools)

```
Запрос: Найди все файлы Python в проекте и скажи что делает main.py
```

Модель должна:
1. Использовать Filesystem MCP для поиска файлов
2. Прочитать main.py
3. Объяснить его функции

Вы увидите в процессе выполнения:
```
🔧 Using tool: filesystem_list_files
🔧 Using tool: filesystem_read_file
```

### Тест 5.4: Проверка Context7 MCP

```
Запрос: Покажи пример использования FastAPI для создания POST endpoint
```

Модель должна использовать Context7 для получения актуальной документации FastAPI.

### Тест 5.5: Проверка автокомплита

1. Откройте любой Python файл
2. Начните писать функцию:
   ```python
   def calculate_sum(a, b):
   ```
3. Нажмите `Tab` - должно предложить автокомплит

---

## 6. Дополнительные MCP серверы

См. подробное руководство: `.continue/mcpServers/RECOMMENDED_MCP_SERVERS.md`

### Быстрая установка приоритетных серверов:

```bash
# Git MCP Server
cat > .continue/mcpServers/git.yaml << 'EOF'
name: Git MCP Server
version: 0.0.1
schema: v1
mcpServers:
  - name: Git
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-git"
      - "/Users/grafgrigorio/claude_projects/blaBy"
    env: {}
EOF

# Memory MCP Server
cat > .continue/mcpServers/memory.yaml << 'EOF'
name: Memory MCP Server
version: 0.0.1
schema: v1
mcpServers:
  - name: Memory
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-memory"
    env: {}
EOF

# Перезапустите VS Code
```

---

## 7. Решение проблем

### ❌ Проблема: "Failed to connect to http://localhost:1234"

**Решение:**
1. Проверьте что LM Studio запущен
2. Убедитесь что Local Server активен (зелёная кнопка "Stop Server" видна)
3. Проверьте в терминале:
   ```bash
   curl http://localhost:1234/v1/models
   ```
4. Если не отвечает - перезапустите Local Server в LM Studio

---

### ❌ Проблема: "Model not found"

**Решение:**
1. Проверьте что модель загружена в Local Server (не просто скачана!)
2. Сравните имя модели в конфиге с реальным именем:
   ```bash
   curl -s http://localhost:1234/v1/models | python3 -c "import sys, json; print(json.load(sys.stdin)['data'][0]['id'])"
   ```
3. Скопируйте точное имя в `.continue/config.yaml`

---

### ❌ Проблема: "Function calling not supported"

**Решение:**
1. Убедитесь что используете модель с поддержкой tools:
   - ✅ Hermes-3-Llama-3.1-8B
   - ✅ Mistral-Small-Instruct-2409
   - ❌ Обычные модели без "instruct" в названии
2. Для Chat режима это нормально - function calling нужен только для Agent/Plan

---

### ❌ Проблема: Медленная работа

**Решение:**
1. Проверьте GPU offload в LM Studio (должно быть 100%)
2. Используйте меньшие модели (7B-8B вместо 32B)
3. Снизьте Context Length до 4096
4. Используйте Q4_K_M квантизацию вместо Q6_K

Проверить использование GPU:
```bash
# В другом терминале пока идёт генерация
sudo powermetrics --samplers gpu_power -i 500 -n 1
```

Должна быть высокая активность GPU.

---

### ❌ Проблема: MCP серверы не работают

**Решение:**
1. Проверьте что модель поддерживает function calling
2. Убедитесь что роль `agent` или `plan` включена в конфиг
3. Проверьте логи MCP серверов:
   ```bash
   # В VS Code
   Cmd + Shift + P → "Developer: Show Logs" → "Continue"
   ```
4. Попробуйте переустановить MCP сервер:
   ```bash
   rm -rf ~/.npm/_npx
   # Перезапустите VS Code
   ```

---

### ⚠️ Проблема: Out of Memory

**Симптомы:**
- LM Studio вылетает
- Система тормозит
- Swap использование >10GB

**Решение:**
1. Закройте другие тяжёлые приложения (Chrome, Docker, etc.)
2. Используйте только одну модель одновременно
3. Выберите меньшие модели:
   - Вместо 32B → 16B
   - Вместо Q6_K → Q4_K_M
4. Снизьте Context Length в LM Studio
5. Мониторьте память:
   ```bash
   while true; do
     echo "=== Memory Usage ==="
     ps aux | grep "LM Studio" | grep -v grep | awk '{sum+=$6} END {print "LM Studio: " sum/1024/1024 " GB"}'
     vm_stat | grep "Pages active" | awk '{print "Active: " $3*4096/1024/1024/1024 " GB"}'
     sleep 2
   done
   ```

---

### 🔧 Проблема: Ошибки установки MCP серверов

**Решение:**
1. Обновите Node.js:
   ```bash
   node --version  # Должна быть >= 18.0.0

   # Если старая версия
   brew install node
   ```

2. Очистите кэш npx:
   ```bash
   rm -rf ~/.npm/_npx
   npm cache clean --force
   ```

3. Проверьте интернет соединение (MCP серверы скачиваются при первом запуске)

---

## 📊 Мониторинг производительности

### Скорость генерации

Ожидаемые показатели на M4 Max:

| Модель | Размер | Квантизация | Токены/сек |
|--------|--------|-------------|------------|
| StarCoder2-3B | 3B | Q6_K | 150+ |
| Hermes-3 | 8B | Q5_K_M | 50-80 |
| DeepSeek | 16B | Q5_K_M | 40-60 |
| Qwen2.5-Coder | 32B | Q5_K_M | 25-35 |

Замерить скорость:
1. В LM Studio → Chat
2. Напишите запрос
3. Внизу справа увидите "XX tok/s"

---

## 🎯 Рекомендуемый workflow

### Для быстрой разработки:
1. Используйте **Hermes-3-8B** для Agent задач (с MCP)
2. Используйте **Qwen2.5-7B** для простых вопросов
3. **StarCoder2-3B** для автокомплита

### Для сложных задач:
1. Переключитесь на **Qwen2.5-32B** для основной работы
2. **Mistral-Small-22B** для архитектурных решений
3. **Hermes-3-8B** оставьте для MCP операций

### Переключение моделей в LM Studio:
1. Остановите сервер (Stop Server)
2. Выберите другую модель
3. Load Model
4. Start Server
5. В Continue автоматически подхватится новая модель

---

## 📚 Полезные ссылки

- **LM Studio документация:** https://lmstudio.ai/docs
- **Continue документация:** https://docs.continue.dev
- **MCP Protocol:** https://modelcontextprotocol.io
- **Hermes-3 документация:** https://www.nous-research.com/
- **Qwen2.5-Coder:** https://github.com/QwenLM/Qwen2.5-Coder

---

## ✅ Чеклист успешной настройки

- [ ] LM Studio установлен и запущен
- [ ] Скачана минимум одна модель с function calling (Hermes-3)
- [ ] Local Server запущен на порту 1234
- [ ] `curl http://localhost:1234/v1/models` возвращает JSON
- [ ] `.continue/config.yaml` обновлён (скопирован из lmstudio-config.yaml)
- [ ] VS Code перезапущен
- [ ] Continue открывается (Cmd + L)
- [ ] Модель отвечает на простые вопросы
- [ ] Agent режим работает (использует MCP инструменты)
- [ ] Автокомплит предлагает варианты (Tab)
- [ ] Установлены дополнительные MCP серверы (Git, Memory)

---

## 🎉 Готово!

Теперь у вас настроена полноценная локальная среда разработки с AI ассистентом!

**Следующие шаги:**
1. Изучите команды Continue: https://docs.continue.dev/features
2. Настройте дополнительные MCP серверы по необходимости
3. Экспериментируйте с разными моделями
4. Настройте кастомные команды под ваш workflow

**Нужна помощь?**
- Документация Continue в проекте: `.continue/`
- Рекомендации по MCP: `.continue/mcpServers/RECOMMENDED_MCP_SERVERS.md`
- Конфигурация: `.continue/config.yaml`

Happy coding! 🚀

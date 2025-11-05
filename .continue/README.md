# Continue Configuration

Настройки Continue для проекта blaBy - локальный голосовой AI ассистент.

---

## 📁 Структура

```
.continue/
├── README.md                          # Этот файл
├── QUICK_START.md                     # ⚡ Быстрый старт (5 минут)
├── SETUP_GUIDE.md                     # 📖 Полное руководство
├── config.yaml                        # ⚙️ Активная конфигурация
├── lmstudio-config.yaml              # 🚀 Конфигурация для LM Studio
├── m4-local.yaml                      # 🗄️ Старая Ollama конфигурация (бэкап)
├── mcpServers/                        # MCP серверы
│   ├── RECOMMENDED_MCP_SERVERS.md    # 📋 Список рекомендуемых серверов
│   ├── context7.yaml                  # Документация библиотек
│   ├── playwright.yaml                # Автоматизация браузера
│   ├── filesystem.yaml                # Файловые операции
│   ├── brave-search.yaml              # Поиск в интернете
│   ├── git.yaml                       # (создайте для Git операций)
│   └── memory.yaml                    # (создайте для долговременной памяти)
└── rules/
    └── chat-mode-rules.md             # Правила для Chat режима
```

---

## 🚀 Быстрый старт

**Новый пользователь?** Начните с: **[QUICK_START.md](QUICK_START.md)** (5 минут)

**Нужны детали?** Читайте: **[SETUP_GUIDE.md](SETUP_GUIDE.md)** (полное руководство)

---

## ⚙️ Конфигурации

### Активная конфигурация: `config.yaml`

Это файл, который Continue использует прямо сейчас.

**Текущий статус:**
- Если вы уже выполнили быстрый старт: LM Studio конфигурация
- Если ещё нет: Ollama конфигурация (без поддержки function calling)

### LM Studio конфигурация: `lmstudio-config.yaml`

**Рекомендованная конфигурация** для локальной разработки на Mac M4 Max.

**Возможности:**
- ✅ Agent режим с function calling
- ✅ Plan режим
- ✅ Поддержка MCP инструментов
- ✅ Оптимизировано для M4 Max (48GB)

**Модели:**
- 🤖 Hermes-3-8B - Agent с function calling
- 🧠 Mistral-Small-22B - Продвинутый Agent
- ⚡ Qwen2.5-Coder-7B - Быстрый Chat
- 💪 Qwen2.5-Coder-32B - Мощный Chat
- 🔍 DeepSeek-16B - Специализированный

**Активация:**
```bash
cp .continue/lmstudio-config.yaml .continue/config.yaml
# Перезапустите VS Code
```

### Ollama конфигурация: `m4-local.yaml`

Старая конфигурация (бэкап). Использует Ollama модели.

**Ограничения:**
- ❌ Нет Agent режима
- ❌ Нет function calling
- ❌ Только Chat режим

**Модели:**
- Qwen2.5-Coder 7B/32B
- DeepSeek-Coder 16B
- Llama3.1 8B

**Восстановление (если нужно вернуться):**
```bash
cp .continue/m4-local.yaml .continue/config.yaml
# Перезапустите VS Code
```

---

## 🔧 MCP Серверы

MCP (Model Context Protocol) - это инструменты которые AI может использовать.

### ✅ Уже настроены:

1. **Context7** - Документация библиотек
   - Получает актуальные примеры кода
   - FastAPI, Whisper, Ollama и тд

2. **Playwright** - Автоматизация браузера
   - Тестирование веб-интерфейса
   - Скриншоты

3. **Filesystem** - Файловые операции
   - Чтение/запись файлов
   - Навигация по проекту

4. **Brave Search** - Поиск в интернете
   - Актуальная информация
   - Решение проблем

### 📦 Рекомендуемые для установки:

См. **[mcpServers/RECOMMENDED_MCP_SERVERS.md](mcpServers/RECOMMENDED_MCP_SERVERS.md)**

**Приоритетные:**
- **Git MCP** - git операции через AI
- **Memory MCP** - долговременная память между сеансами
- **Sequential Thinking** - улучшенное планирование

---

## 📊 Рекомендуемые модели для M4 Max

### Tier 1: Обязательные

| Модель | Размер | Назначение | Скорость |
|--------|--------|------------|----------|
| Hermes-3-Llama-3.1-8B | 6GB | Agent + Tools | 50-80 tok/s |
| Qwen2.5-Coder-32B | 23GB | Основная работа | 25-35 tok/s |
| StarCoder2-3B | 2GB | Автокомплит | 150+ tok/s |

**Итого:** ~31GB

### Tier 2: Дополнительные

| Модель | Размер | Назначение | Скорость |
|--------|--------|------------|----------|
| Mistral-Small-22B | 16GB | Продвинутый Agent | 30-45 tok/s |
| DeepSeek-V2-16B | 11GB | Альтернатива | 40-60 tok/s |

---

## 🎯 Режимы работы

### Chat Mode
Обычное общение с AI. Подходит для:
- Вопросы о коде
- Объяснения
- Генерация кода
- Рефакторинг

**Модели:** Любые

### Agent Mode ⭐
AI автоматически использует инструменты (MCP). Подходит для:
- Поиск и анализ файлов
- Получение документации
- Комплексные задачи
- Автоматизация workflow

**Модели:** Только с function calling (Hermes, Mistral)

### Plan Mode
AI планирует и выполняет сложные многошаговые задачи.

**Модели:** Только с function calling

---

## 🔑 Основные команды

### В VS Code:
- `Cmd + L` - Открыть Continue чат
- `Cmd + I` - Inline редактирование
- `Cmd + Shift + L` - Сменить модель
- `Tab` - Автокомплит

### В Continue чате:
- `@filename` - Включить файл в контекст
- `/explain` - Объяснить код
- `/refactor` - Рефакторинг
- `/test` - Написать тесты
- `/fix` - Исправить ошибку

---

## 📈 Мониторинг

### Проверить что LM Studio работает:
```bash
curl http://localhost:1234/v1/models
```

### Проверить текущую модель:
```bash
curl -s http://localhost:1234/v1/models | python3 -m json.tool
```

### Посмотреть использование памяти:
```bash
ps aux | grep "LM Studio" | grep -v grep | awk '{print $6/1024/1024 " GB"}'
```

---

## ⚠️ Troubleshooting

### Continue не видит модель
1. Убедитесь что Local Server запущен в LM Studio
2. Проверьте порт: `curl http://localhost:1234/v1/models`
3. Сравните имя модели в конфиге с реальным

### MCP инструменты не работают
1. Проверьте что модель поддерживает function calling (Hermes, Mistral)
2. Убедитесь что роль `agent` включена в конфиге
3. Посмотрите логи: VS Code → Developer → Show Logs → Continue

### Медленная работа
1. GPU offload = 100% в LM Studio
2. Используйте меньшие модели (7-8B)
3. Q4_K_M квантизация вместо Q6_K

---

## 📚 Документация

### В этой директории:
- **[QUICK_START.md](QUICK_START.md)** - Быстрая настройка (5 минут)
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Полное руководство
- **[mcpServers/RECOMMENDED_MCP_SERVERS.md](mcpServers/RECOMMENDED_MCP_SERVERS.md)** - MCP серверы

### Внешние ссылки:
- [Continue Docs](https://docs.continue.dev)
- [LM Studio Docs](https://lmstudio.ai/docs)
- [MCP Protocol](https://modelcontextprotocol.io)

---

## 🔄 Обновление конфигурации

Конфигурация Continue горячо перезагружается, но для надёжности:

```bash
# После изменения config.yaml или MCP серверов:
# 1. Сохраните файл
# 2. Полностью закройте VS Code (Cmd + Q)
# 3. Откройте снова
```

---

## 🎓 Советы по использованию

### Для максимальной производительности:
1. Держите в RAM 2-3 модели одновременно
2. Hermes-3 для Agent задач + Qwen-32B для основной работы
3. StarCoder2 для автокомплита

### Переключение между моделями в LM Studio:
1. Stop Server
2. Load другую модель
3. Start Server
4. Continue автоматически подхватит новую

### Экономия памяти:
- Используйте Q4_K_M вместо Q5_K_M (жертвуя качеством)
- Закрывайте Chrome и другие тяжёлые приложения
- Снижайте Context Length до 4096

---

## 🆘 Нужна помощь?

1. **Быстрые вопросы:** См. [QUICK_START.md](QUICK_START.md)
2. **Проблемы:** См. [SETUP_GUIDE.md](SETUP_GUIDE.md) → Troubleshooting
3. **MCP:** См. [mcpServers/RECOMMENDED_MCP_SERVERS.md](mcpServers/RECOMMENDED_MCP_SERVERS.md)

---

## ✅ Статус настройки

Чеклист для проверки:

- [ ] LM Studio установлен
- [ ] Hermes-3-8B скачан
- [ ] Local Server запущен
- [ ] `.continue/config.yaml` активирован (скопирован из lmstudio-config.yaml)
- [ ] VS Code перезапущен
- [ ] Continue отвечает на вопросы
- [ ] Agent режим работает (использует MCP)
- [ ] Дополнительные MCP установлены (Git, Memory)

**Всё работает?** Поздравляю! 🎉

**Что-то не так?** Читайте [SETUP_GUIDE.md](SETUP_GUIDE.md) секция Troubleshooting.

---

Последнее обновление: 2025-11-04

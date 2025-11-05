# Настройка MCP (Model Context Protocol) для Continue

## 📋 Что такое MCP?

Model Context Protocol (MCP) — это стандартизированный протокол, который позволяет AI моделям взаимодействовать с внешними инструментами и сервисами. В контексте Continue, MCP серверы расширяют возможности локальных моделей, предоставляя доступ к:

- 📚 Документации библиотек (Context7)
- 🌐 Автоматизации браузера (Playwright)
- 📁 Файловой системе
- 🔧 Различным API и сервисам

## ✅ Что уже настроено

В конфигурации Continue добавлены следующие MCP серверы:

### 1. Context7

**Назначение:** Получение актуальной документации библиотек

**Использование:**

- Поиск документации по FastAPI, Whisper, Ollama и другим библиотекам
- Получение примеров кода и best practices
- Проверка актуальных API и функций

**Примеры запросов:**

```
Найди документацию по FastAPI WebSocket endpoints
Как использовать Whisper для потокового распознавания?
Покажи примеры использования Ollama API
```

### 2. Playwright

**Назначение:** Автоматизация браузера и тестирование веб-интерфейса

**Использование:**

- Тестирование веб-интерфейса приложения
- Автоматизация действий в браузере
- Создание скриншотов для документации
- Отладка JavaScript ошибок

**Примеры запросов:**

```
Протестируй веб-интерфейс приложения на http://localhost:8000
Сделай скриншот главной страницы
Проверь, что кнопка микрофона работает
Найди JavaScript ошибки в консоли
```

### 3. Filesystem

**Назначение:** Расширенная работа с файлами проекта

**Использование:**

- Чтение и запись файлов
- Поиск файлов по паттернам
- Создание директорий
- Управление файловой системой проекта

**Примеры запросов:**

```
Найди все Python файлы в проекте
Прочитай содержимое requirements.txt
Создай новый файл config.py
```

### 4. Git

**Назначение:** Работа с локальным git репозиторием

**Использование:**

- Просмотр истории коммитов
- Создание коммитов
- Работа с ветками
- Просмотр diff изменений

**Примеры запросов:**

```
Покажи последние 5 коммитов
Какие файлы изменены в текущей ветке?
Создай коммит с текущими изменениями
```

### 5. Brave Search

**Назначение:** Поиск информации в интернете

**Использование:**

- Поиск актуальной информации
- Решение проблем через поиск
- Получение документации и примеров

**Примеры запросов:**

```
Найди информацию о последних обновлениях FastAPI
Как решить проблему с Whisper на macOS?
```

## 🔧 Настройка MCP серверов

### Текущая конфигурация

MCP серверы настроены локально для проекта в `.continue/mcpServers/`:

Каждый сервер настроен в отдельном YAML файле:

- `context7.yaml` - Документация библиотек
- `playwright.yaml` - Автоматизация браузера
- `filesystem.yaml` - Работа с файлами проекта
- `git.yaml` - Работа с локальным git
- `brave-search.yaml` - Поиск в интернете

### Добавление новых MCP серверов

Для добавления нового MCP сервера создайте файл в `.continue/mcpServers/`:

#### Пример: создание нового сервера

Создайте файл `.continue/mcpServers/my-server.yaml`:

```yaml
name: My MCP Server
version: 0.0.1
schema: v1
mcpServers:
  - name: My Server
    command: npx
    args:
      - -y
      - "@package/name"
    env:
      API_KEY: "your-api-key"
```

#### Примеры готовых серверов:

**Filesystem MCP** (`.continue/mcpServers/filesystem.yaml`):

```yaml
name: Filesystem MCP Server
version: 0.0.1
schema: v1
mcpServers:
  - name: Filesystem
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-filesystem"
      - "/path/to/project"
```

**Git MCP** (`.continue/mcpServers/git.yaml`):

```yaml
name: Git MCP Server
version: 0.0.1
schema: v1
mcpServers:
  - name: Git
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-git"
```

**GitHub MCP** (для интеграции с GitHub):

```yaml
name: GitHub MCP Server
version: 0.0.1
schema: v1
mcpServers:
  - name: GitHub
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-github"
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your_token_here"
```

## 🚀 Использование MCP в Continue

### Автоматическое использование

Continue автоматически использует настроенные MCP серверы при работе с моделями. Просто запрашивайте функциональность:

**Примеры:**

```
# Использование Context7
"Найди документацию по FastAPI middleware"
"Как использовать async/await в FastAPI?"

# Использование Playwright
"Протестируй веб-интерфейс и проверь, что все работает"
"Сделай скриншот приложения и покажи мне"
```

### Проверка работы MCP

1. **Откройте Continue в VS Code**
2. **Откройте чат** (`Cmd+L`)
3. **Попробуйте запрос:**
   ```
   Используя Context7, найди документацию по FastAPI WebSocket
   ```
4. **Или:**
   ```
   Используя Playwright, открой http://localhost:8000 и сделай скриншот
   ```

### Диагностика проблем

Если MCP серверы не работают:

1. **Проверьте наличие Node.js:**

   ```bash
   node --version
   npm --version
   ```

2. **Проверьте установку MCP серверов:**

   ```bash
   npx -y @modelcontextprotocol/server-context7 --help
   npx -y @modelcontextprotocol/server-playwright --help
   ```

3. **Проверьте логи Continue:**

   - Откройте палитру команд (`Cmd+Shift+P`)
   - Выполните: `Continue: Show Logs`
   - Ищите ошибки связанные с MCP

4. **Перезапустите VS Code** после изменения конфигурации MCP

## 📚 Доступные MCP серверы

### Официальные серверы от Model Context Protocol:

1. **Context7** - Документация библиотек
2. **Playwright** - Автоматизация браузера
3. **Filesystem** - Работа с файлами
4. **GitHub** - Интеграция с GitHub
5. **PostgreSQL** - Работа с БД
6. **Slack** - Интеграция со Slack
7. **Brave Search** - Поиск в интернете
8. **Puppeteer** - Альтернатива Playwright

### Поиск других MCP серверов:

- [MCP Registry](https://github.com/modelcontextprotocol/servers)
- [npm search](https://www.npmjs.com/search?q=@modelcontextprotocol/server)

## 🔒 Безопасность

⚠️ **Важные моменты:**

1. **Токены доступа:** Никогда не коммитьте токены в git

   - Используйте переменные окружения
   - Добавьте `.continue/config.yaml` в `.gitignore` если содержит секреты

2. **Filesystem MCP:** Ограничьте доступ к нужным директориям

   ```yaml
   mcpServers:
     filesystem:
       command: "npx"
       args:
         - "-y"
         - "@modelcontextprotocol/server-filesystem"
         - "/safe/path"
   ```

3. **Проверка серверов:** Используйте только проверенные MCP серверы

## 📝 Примеры использования

### Context7 - Поиск документации

```
Запрос: "Найди документацию по FastAPI WebSocket и покажи примеры"

AI автоматически:
1. Использует Context7 для поиска документации
2. Находит релевантные примеры
3. Показывает код и объясняет использование
```

### Playwright - Тестирование

```
Запрос: "Протестируй веб-интерфейс приложения на localhost:8000"

AI автоматически:
1. Открывает браузер через Playwright
2. Переходит на localhost:8000
3. Тестирует функциональность
4. Делает скриншоты
5. Проверяет консоль на ошибки
6. Предоставляет отчет
```

## 🎯 Рекомендации

1. **Для разработки:** Используйте Context7 для быстрого доступа к документации
2. **Для тестирования:** Используйте Playwright для автоматизации тестов
3. **Для отладки:** Используйте Playwright для проверки веб-интерфейса
4. **Для документации:** Используйте Playwright для создания скриншотов

## 📖 Дополнительные ресурсы

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Continue MCP Documentation](https://docs.continue.dev/mcp)
- [MCP Servers Registry](https://github.com/modelcontextprotocol/servers)

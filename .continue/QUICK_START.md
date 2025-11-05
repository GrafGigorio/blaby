# ⚡ Быстрый старт Continue + LM Studio

## 5-минутная настройка для Mac M4 Max

---

## 🎯 Шаг 1: Скачайте модель в LM Studio (3 мин)

1. Откройте **LM Studio**
2. Нажмите **🔍 Search**
3. Введите: `NousResearch/Hermes-3-Llama-3.1-8B`
4. Скачайте версию **Q5_K_M** (~6GB)

> Пока скачивается - переходите к шагу 2

---

## 🎯 Шаг 2: Активируйте конфигурацию (30 сек)

```bash
cd /Users/grafgrigorio/claude_projects/blaBy

# Бэкап старого конфига
cp .continue/config.yaml .continue/config.yaml.backup

# Активация LM Studio конфига
cp .continue/lmstudio-config.yaml .continue/config.yaml
```

---

## 🎯 Шаг 3: Запустите Local Server (1 мин)

1. В LM Studio → **💻 Local Server**
2. Выберите **Hermes-3-Llama-3.1-8B-Q5_K_M.gguf**
3. Нажмите **Load Model** (подождите загрузки)
4. Нажмите **Start Server** (зелёная кнопка)
5. Убедитесь что видите: `✅ Server running on http://localhost:1234`

---

## 🎯 Шаг 4: Перезапустите VS Code (10 сек)

```bash
# Полностью закройте VS Code
Cmd + Q

# Откройте снова
code .
```

---

## 🎯 Шаг 5: Тест! (30 сек)

1. В VS Code нажмите: `Cmd + L`
2. Выберите модель: **🤖 Agent (Hermes 8B)**
3. Напишите: `Привет! Найди все Python файлы в проекте`
4. Если модель ответила и использовала MCP инструменты - ВСЁ РАБОТАЕТ! ✅

---

## 🚀 Готово!

Теперь у вас работает локальный AI с поддержкой function calling!

### Следующие шаги:

1. **Скачайте дополнительные модели** (опционально):
   - Qwen2.5-Coder-32B (мощная модель для кода)
   - StarCoder2-3B (для автокомплита)

2. **Установите дополнительные MCP серверы**:
   ```bash
   # Git MCP
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

   # Memory MCP
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

## 📚 Документация

- **Полное руководство:** `.continue/SETUP_GUIDE.md`
- **MCP серверы:** `.continue/mcpServers/RECOMMENDED_MCP_SERVERS.md`
- **Конфигурация:** `.continue/lmstudio-config.yaml`

---

## ❌ Проблемы?

### "Failed to connect"
→ Убедитесь что Local Server запущен в LM Studio

### "Model not found"
→ Проверьте что модель загружена в Local Server (не просто скачана)

### Медленно работает
→ Проверьте GPU offload = 100% в LM Studio

### MCP не работает
→ Убедитесь что используете модель с agent/plan ролью (Hermes-3, Mistral)

---

## 🎯 Основные команды Continue

- `Cmd + L` - Открыть чат
- `Cmd + I` - Inline редактирование
- `Tab` - Автокомплит
- `Cmd + Shift + L` - Выбрать другую модель

---

**Нужна помощь?** Читайте полное руководство: `.continue/SETUP_GUIDE.md`

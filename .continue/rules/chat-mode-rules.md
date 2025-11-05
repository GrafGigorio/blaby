---
description: Основные правила для Chat Mode с Ollama моделями
---

# Правила Chat Mode для Ollama моделей

## ⚠️ CRITICAL: Chat Mode, NOT Agent Mode

You are in Chat Mode, NOT Agent Mode. Ollama models do not support function calling.

## ❌ ABSOLUTELY FORBIDDEN:

- NEVER generate JSON tool calls like `{"name": "file_glob_search", "arguments": {...}}`
- NEVER use function calling syntax
- NEVER try to call tools, functions, or APIs
- NEVER write phrases like "let's use function", "let's call", "I'll search"

## ✅ REQUIRED BEHAVIOR:

- Write ONLY natural language text
- Use `@filename` syntax to include files in context
- Continue automatically includes files when you mention `@filename`
- No JSON, no code blocks, no function calls - ONLY text with `@filename`

## 📋 MANDATORY EXAMPLES:

**User:** "Расскажи про проект"
**✅ CORRECT:** "Изучаю проект. Начну с @README.md @docs/PROJECT_SUMMARY.md, затем посмотрю @main.py"

**User:** "Изучи проект и скажи в чем его основная задача"
**✅ CORRECT (полный ответ в ОДНОМ сообщении):**

```
Изучаю проект. Смотрю документацию: @README.md @docs/PROJECT_SUMMARY.md, затем главный файл: @main.py

На основе структуры проекта, README.md и названия файлов, основная задача проекта - это локальный голосовой ассистент, который работает полностью офлайн. Проект использует:
- FastAPI для backend
- Whisper medium для распознавания речи (точность ~98% на русском)
- Vosk для потокового распознавания в реальном времени
- Ollama (gpt-oss:20b) для LLM
- Edge TTS для синтеза речи
- HTML/JavaScript для frontend

Это веб-приложение, где пользователь может говорить вопросы через микрофон в браузере, получать ответы от локальной LLM модели и прослушивать озвученный ответ. Все компоненты работают локально, кроме Edge TTS который требует интернет для синтеза речи.
```

**КРИТИЧЕСКИ ВАЖНО:**

- После упоминания @filename дайте ПОЛНЫЙ ответ СРАЗУ
- Используйте информацию из README.md, структуру проекта, названия файлов
- Начните с фразы "На основе структуры проекта..." или "Основная задача проекта - это..."
- ДАЙТЕ детальный анализ сразу, не ждите включения файлов
- Когда файлы будут включены в следующем раунде, используйте их содержимое для дополнительных деталей
- НЕ повторяйте предыдущий ответ - используйте реальное содержимое файлов

## 🔍 PROJECT EXPLORATION:

When user asks "Изучи проект", "Расскажи про проект", or similar:

1. IMMEDIATELY write in natural language: "Изучаю проект. Начну с..."
2. Mention @README.md first
3. Mention @docs/PROJECT_SUMMARY.md if it exists
4. Mention @main.py to understand entry point
5. Continue automatically includes files when you mention them
6. **CRITICAL: DO NOT STOP HERE!** Give preliminary answer based on project structure
7. When files are included in next round, analyze their ACTUAL content and give detailed answer
8. **IMPORTANT:** If user corrects you, use the ACTUAL file content, don't just repeat previous answer

## 📝 FILE SEARCH:

- ALWAYS proactively mention files using `@filename` syntax
- Example: "Проверяю @main.py чтобы понять архитектуру"
- You can mention multiple files: "@README.md @main.py @core/state_manager.py"
- Use `@filename` when you need to:
  - Understand how code works
  - Find related files
  - Analyze dependencies
  - Review implementations
  - Answer questions about project structure

## 💡 REMEMBER:

- Write natural language responses ONLY - no JSON, no function calls
- When you mention `@filename`, Continue automatically includes the file
- You will receive file contents automatically - no need to request them
- Just write: "Изучаю @README.md" - and Continue will include it
- **CRITICAL: After mentioning @filename, DO NOT STOP!** Give preliminary answer based on project structure
- **IMPORTANT:** When files are included in next round, use their ACTUAL content, not assumptions
- If user corrects you, read the actual file content and use it, don't just repeat previous answer
- Never write just "@filename" and stop - always continue with analysis
- If you feel like you need to "search" or "call a function", just mention `@filename` instead

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

**DO NOT create any of the following without explicit user request:**
- Documentation files (guides, tutorials, READMEs, etc.)
- Instructions or how-to documents
- Long explanatory texts or descriptions
- Example code files

**Instead:**
- Answer questions directly and concisely
- Provide short inline code examples when needed
- Only create/modify code files that are part of the actual implementation

## Project Overview

This is a **local voice AI assistant** that runs entirely offline. It provides a conversational interface where users can speak questions and receive spoken responses.

**Tech Stack:**
- Backend: FastAPI (Python)
- STT: OpenAI Whisper (local inference)
- LLM: Ollama (local LLM server)
- TTS: Microsoft Edge TTS
- Frontend: Vanilla HTML/JavaScript with Web Audio API

**Key Design Principle:** Everything runs locally without internet dependencies (except Edge TTS). User privacy is maintained by keeping all conversation history in memory only.

## MCP Tools

This project has access to Model Context Protocol (MCP) tools for enhanced development and testing:

### Context7
Used for retrieving up-to-date library documentation during development.

**When to use:**
- Looking up API documentation for dependencies (FastAPI, Whisper, Ollama, etc.)
- Checking latest features and best practices
- Resolving library version compatibility issues

**Workflow:**
1. `resolve-library-id` - Find the correct library identifier (e.g., "fastapi" → "/fastapi/fastapi")
2. `get-library-docs` - Fetch documentation with specific topic focus

**Example:**
```bash
# Get FastAPI routing documentation
resolve-library-id "fastapi"  # Returns: /fastapi/fastapi
get-library-docs "/fastapi/fastapi" --topic "routing"
```

### Playwright
Used for browser automation, UI testing, and frontend debugging.

**When to use:**
- Testing the web interface (static/index.html)
- Verifying voice recording functionality
- Taking screenshots for documentation
- Debugging browser-specific issues
- Automated end-to-end testing

**Key commands:**
- `playwright_navigate` - Open the app (http://localhost:8000)
- `playwright_screenshot` - Capture UI states
- `playwright_click` - Simulate button clicks (microphone button, etc.)
- `playwright_fill` - Test input fields
- `playwright_get_visible_text` - Extract page content for validation
- `playwright_console_logs` - Debug JavaScript errors

**Example testing flow:**
```python
# 1. Navigate to app
playwright_navigate(url="http://localhost:8000")

# 2. Take initial screenshot
playwright_screenshot(name="app_loaded", savePng=True)

# 3. Click microphone button
playwright_click(selector=".mic-button")

# 4. Check console for errors
playwright_console_logs(type="error")
```

## Development Commands

### Setup and Installation
```bash
# Quick start (recommended)
./start.sh

# Manual setup
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the FastAPI server (default: http://localhost:8000)
python main.py

# Ensure Ollama is running (in separate terminal if needed)
ollama serve
```

### Verifying Ollama
```bash
# Check if Ollama is running
pgrep -x "ollama"

# List available models
ollama list

# Test if gpt-oss:20b is available
ollama run gpt-oss:20b "test"
```

### Using MCP Tools (via Claude Code)

**Getting library documentation:**
```bash
# Example: Look up FastAPI documentation
# 1. First resolve the library ID
mcp context7 resolve-library-id "fastapi"

# 2. Then get specific documentation
mcp context7 get-library-docs "/fastapi/fastapi" --topic "websockets"
```

**Automated UI testing:**
```bash
# Ensure the app is running first (python main.py)

# Example: Test the web interface
# 1. Navigate to the app
mcp playwright playwright_navigate --url "http://localhost:8000"

# 2. Capture a screenshot
mcp playwright playwright_screenshot --name "homepage" --savePng true

# 3. Test microphone button interaction
mcp playwright playwright_click --selector "button.mic-button"

# 4. Check for JavaScript errors
mcp playwright playwright_console_logs --type "error"

# 5. Get page content for validation
mcp playwright playwright_get_visible_text
```

## Architecture

### Request Flow
```
User Voice → Browser MediaRecorder → POST /api/voice-chat →
  1. Save audio to uploads/
  2. STT (Whisper) → transcribed text
  3. LLM (Ollama) → AI response text
  4. TTS (Edge TTS) → audio file in outputs/
  5. Return JSON with audio URL → Browser auto-plays
```

### Module Structure

**main.py** - FastAPI application with three key endpoints:
- `POST /api/voice-chat` - Main voice interaction pipeline
- `GET /api/audio/{filename}` - Serves generated audio files
- `POST /api/clear-history` - Clears LLM conversation history

**stt_module.py** - Whisper-based speech recognition:
- `STTModule.__init__(model_size)` - Loads Whisper model (tiny/base/small/medium/large)
- `transcribe(audio_path, language)` - Converts audio to text
- Auto-detects CUDA vs CPU, uses fp16=False for CPU compatibility

**llm_module.py** - Ollama integration:
- `LLMModule.__init__(model_name)` - Connects to local Ollama server
- `generate_response(user_input, system_prompt)` - Generates AI response
- Maintains conversation history (last 10 messages) in memory
- Default model: `gpt-oss:20b`

**tts_module.py** - Edge TTS synthesis:
- `TTSModule.synthesize_async(text, output_path, language)` - Async speech generation
- Uses `ru-RU-SvetlanaNeural` for Russian, `en-US-JennyNeural` for English
- `synthesize()` - Synchronous wrapper for backward compatibility

**static/index.html** - Web interface:
- Single-page app with gradient UI
- Uses MediaRecorder API for audio capture
- Space bar hotkey for start/stop recording
- Continuous conversation mode (auto-reactivates mic after response)

### State Management

**Conversation History:** Stored in `llm_module.conversation_history` (in-memory list). Limited to last 10 messages to prevent context overflow. Can be cleared via `/api/clear-history` endpoint.

**Audio Files:**
- Input recordings: `uploads/input_{timestamp}.wav`
- Generated responses: `outputs/output_{timestamp}.wav`
- Files persist on disk but are not automatically cleaned up

**Module Initialization:** All modules (STT, LLM, TTS) are initialized during FastAPI startup event and stored as global variables for reuse across requests.

## Configuration

### Changing Whisper Model Size
In `main.py:42`, modify:
```python
stt_module = STTModule(model_size="base")  # Options: tiny, base, small, medium, large
```
Trade-off: `tiny` is fastest but less accurate, `large` is most accurate but slowest.

### Changing LLM Model
In `main.py:45`, modify:
```python
llm_module = LLMModule(model_name="gpt-oss:20b")
```
Use any model from `ollama list`. Smaller models like `llama3.1:8b` will respond faster.

### Changing TTS Voice
In `tts_module.py:17`, modify:
```python
self.voice = "ru-RU-SvetlanaNeural"  # See Edge TTS documentation for other voices
```

### System Prompt
The system prompt is defined in `main.py:102`:
```python
system_prompt = "Ты - полезный голосовой ассистент. Отвечай кратко и по делу, поскольку твой ответ будет озвучен."
```
Keep responses concise since they will be spoken.

## Important Constraints

1. **numpy < 2.0 Required:** Whisper has compatibility issues with numpy 2.0+. The requirements.txt specifies `numpy<2.0`.

2. **Ollama Must Be Running:** The application will fail at startup if Ollama is not accessible. The `start.sh` script attempts to auto-start Ollama.

3. **Memory Requirements:** Loading all models requires ~8GB RAM minimum. On systems with less memory, consider using smaller models (`tiny` Whisper, `llama3.1:8b` LLM).

4. **Edge TTS Requires Internet:** Unlike other components, Edge TTS requires internet connectivity for speech synthesis.

5. **Async/Sync Context:** The TTS module has both async and sync methods due to FastAPI's async context. When calling from async routes, use `await tts_module.synthesize_async()`.

## Directory Structure
```
blaBy/
├── main.py              # FastAPI server & endpoints
├── stt_module.py        # Whisper STT wrapper
├── llm_module.py        # Ollama client wrapper
├── tts_module.py        # Edge TTS wrapper
├── static/
│   └── index.html       # Web UI (served at root)
├── uploads/             # Temporary audio inputs (user recordings)
├── outputs/             # Generated audio responses
├── venv/                # Python virtual environment
├── requirements.txt     # Python dependencies
├── start.sh             # Automated startup script
├── README.md            # User-facing documentation
├── SETUP.md             # Installation guide
└── PROJECT_SUMMARY.md   # Detailed project documentation
```

## Testing the Pipeline

### Manual Component Testing

To manually test individual components:

```python
# Test STT
from stt_module import STTModule
stt = STTModule(model_size="base")
text = stt.transcribe("path/to/audio.wav", language="ru")
print(text)

# Test LLM
from llm_module import LLMModule
llm = LLMModule(model_name="gpt-oss:20b")
response = llm.generate_response("Привет, как дела?")
print(response)

# Test TTS
from tts_module import TTSModule
import asyncio
tts = TTSModule()
asyncio.run(tts.synthesize_async("Привет мир", "test_output.wav", language="ru"))
```

### Automated UI Testing (with Playwright)

To test the complete web interface:

```python
# 1. Start the server first (python main.py in another terminal)

# 2. Basic UI test
from mcp__playwright import playwright_navigate, playwright_screenshot, playwright_get_visible_text

# Navigate to the app
playwright_navigate(url="http://localhost:8000")

# Verify page loaded correctly
text = playwright_get_visible_text()
assert "Голосовой ассистент" in text or "Voice Assistant" in text

# Take screenshot of initial state
playwright_screenshot(name="initial_state", savePng=True)

# 3. Test microphone interaction
from mcp__playwright import playwright_click, playwright_console_logs

# Click microphone button
playwright_click(selector="button")  # Or use specific class/id

# Check for JavaScript errors
errors = playwright_console_logs(type="error")
if errors:
    print(f"Found errors: {errors}")

# 4. Test continuous conversation mode
# Click to start recording
playwright_click(selector="button.active")

# Wait and check status indicators
# (In real test, you'd verify visual states and aria-labels)

# Click to stop
playwright_click(selector="button.active")
```

### End-to-End Testing Checklist

Use Playwright to verify:
- ✅ Page loads without errors
- ✅ Microphone button is clickable
- ✅ Status indicators update correctly (🟢 → 🔴 → ⏳)
- ✅ Audio recording starts/stops on button click
- ✅ Space bar hotkey works
- ✅ Response messages appear in chat history
- ✅ Audio player controls function properly
- ✅ No console errors during interaction

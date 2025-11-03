# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **local voice AI assistant** that runs entirely offline. It provides a conversational interface where users can speak questions and receive spoken responses.

**Tech Stack:**
- Backend: FastAPI (Python)
- STT: OpenAI Whisper (local inference)
- LLM: Ollama (local LLM server)
- TTS: Microsoft Edge TTS
- Frontend: Vanilla HTML/JavaScript with Web Audio API

**Key Design Principle:** Everything runs locally without internet dependencies (except Edge TTS). User privacy is maintained by keeping all conversation history in memory only.

## Documentation Structure

This project has comprehensive documentation organized by topic:

- **[README.md](README.md)** - Main project overview and quick links
- **[docs/](docs/)** - All detailed documentation
  - **[docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Complete project overview
  - **[docs/architecture/](docs/architecture/)** - Architecture documentation
  - **[docs/guides/](docs/guides/)** - Development guides (SETUP, QUICKSTART, DEVELOPMENT, CONTRIBUTING, REFACTORING)
  - **[docs/testing/](docs/testing/)** - Testing documentation
- **[api/README.md](api/README.md)** - API endpoints documentation (REST & WebSocket)
- **[core/README.md](core/README.md)** - Core modules documentation (STT, LLM, TTS, Actions, State)
- **[utils/README.md](utils/README.md)** - Utility modules documentation (text cleaning, port management)

When working with a specific module, always check if it has a README.md in its directory.

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

### Key Features After Refactoring

1. **Modular Structure**: Code organized into `api/`, `core/`, `utils/` directories
2. **WebSocket Support**: Real-time streaming STT and TTS via WebSocket
3. **Centralized Config**: All settings in `config.py`
4. **Text Cleaning**: Automatic removal of TECH blocks and JSON from TTS output
5. **Action System**: Special commands handling (internet access, system control)
6. **Improved Frontend**: Modular JavaScript with separate audio/websocket/UI modules

### Request Flow

**REST API Flow:**
```
User Voice → Browser MediaRecorder → POST /api/voice-chat →
  1. Save audio to uploads/
  2. STT (Whisper) → transcribed text
  3. LLM (Ollama) → AI response text
  4. Text Cleaning (remove TECH blocks, JSON)
  5. TTS (Edge TTS) → audio file in outputs/
  6. Return JSON with audio URL → Browser auto-plays
```

**WebSocket Streaming Flow:**
```
User Voice → Browser MediaRecorder → WebSocket /ws/voice →
  1. Stream audio chunks in real-time
  2. Streaming STT → partial transcriptions
  3. LLM generates response (streaming or complete)
  4. Text Cleaning
  5. TTS → stream audio chunks back
  6. Browser plays audio as it arrives
```

### Module Structure

**main.py** - FastAPI application entry point
- Initializes all modules and configures routes
- WebSocket support for real-time streaming

**api/** - API endpoints:
- `api/voice_chat.py` - REST endpoint for voice interactions
- `api/websocket.py` - WebSocket endpoint for streaming STT/TTS
- `api/models.py` - Pydantic models for request/response validation

**core/** - Core modules:
- `core/stt_module.py` - Whisper-based speech recognition
  - `STTModule.__init__(model_size)` - Loads Whisper model
  - `transcribe(audio_path, language)` - Converts audio to text
  - Auto-detects CUDA vs CPU, uses fp16=False for CPU compatibility
- `core/stt_streaming_module.py` - Real-time streaming STT
- `core/llm_module.py` - Ollama LLM integration
  - `LLMModule.__init__(model_name)` - Connects to local Ollama
  - `generate_response(user_input, system_prompt)` - Generates AI response
  - Maintains conversation history (last 10 messages)
  - Default model: `gpt-oss:20b`
- `core/tts_module.py` - Edge TTS synthesis
  - `TTSModule.synthesize_async(text, output_path, language)` - Async speech generation
  - Uses `ru-RU-SvetlanaNeural` for Russian, `en-US-JennyNeural` for English
- `core/action_manager.py` - Special actions and commands handler
- `core/state_manager.py` - Application state management

**utils/** - Utility modules:
- `utils/text_cleaning.py` - Text preprocessing for TTS (removes TECH blocks, JSON)
- `utils/port_manager.py` - Network port management

**static/** - Web interface:
- `static/index.html` - Single-page app with gradient UI
- `static/js/` - JavaScript modules for WebSocket, audio recording
- `static/css/` - Styling
- Uses MediaRecorder API and Web Audio API
- Space bar hotkey for start/stop recording
- Continuous conversation mode with streaming support

### State Management

**Conversation History:**
- Stored in `core/llm_module.py` as `conversation_history` (in-memory list)
- Limited to last 10 messages to prevent context overflow
- Can be cleared via `/api/clear-history` endpoint

**Application State:**
- Managed by `core/state_manager.py`
- Tracks current assistant state (idle, listening, processing, speaking)
- Coordinates between modules for proper workflow

**Action System:**
- Handled by `core/action_manager.py`
- Processes special commands (e.g., "подключи интернет")
- Can trigger external actions and provide feedback

**Audio Files:**
- Input recordings: `uploads/input_{timestamp}.wav`
- Generated responses: `outputs/output_{timestamp}.wav`
- Files persist on disk but are not automatically cleaned up

**Module Initialization:**
- All modules (STT, LLM, TTS, Actions, State) are initialized during FastAPI startup
- Stored as global variables for reuse across requests
- Configuration loaded from `config.py`

## Configuration

Configuration is centralized in `config.py` at the project root.

### Changing Whisper Model Size
In `config.py`, modify:
```python
DEFAULT_STT_MODEL = "base"  # Options: tiny, base, small, medium, large
```
Trade-off: `tiny` is fastest but less accurate, `large` is most accurate but slowest.

### Changing LLM Model
In `config.py`, modify:
```python
DEFAULT_LLM_MODEL = "gpt-oss:20b"
```
Use any model from `ollama list`. Smaller models like `llama3.1:8b` will respond faster.

### Other Configuration Options
Available in `config.py`:
- `HOST`, `PORT` - Server settings
- `DEFAULT_TTS_VOICE_RU`, `DEFAULT_TTS_VOICE_EN` - TTS voice settings
- `SILENCE_THRESHOLD` - VAD (Voice Activity Detection) threshold
- `MAX_CONVERSATION_HISTORY` - Maximum messages in conversation history
- `DEFAULT_SYSTEM_PROMPT` - Default system prompt for LLM

### Changing TTS Voice
TTS voice settings are in `config.py`:
```python
DEFAULT_TTS_VOICE_RU = "ru-RU-SvetlanaNeural"
DEFAULT_TTS_VOICE_EN = "en-US-JennyNeural"
```
Or modify directly in `core/tts_module.py` if you need more control. See Edge TTS documentation for available voices.

### System Prompt
The system prompt is defined in `config.py`:
```python
DEFAULT_SYSTEM_PROMPT = "Ты - полезный голосовой ассистент. Отвечай кратко и по делу, поскольку твой ответ будет озвучен."
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
├── main.py                 # FastAPI application entry point
├── config.py               # Centralized configuration
├── start.sh                # Automated startup script
├── requirements.txt        # Python dependencies
│
├── api/                    # API endpoints
│   ├── voice_chat.py       # REST API for voice interactions
│   ├── websocket.py        # WebSocket for streaming
│   ├── websocket_helpers.py
│   ├── models.py           # Pydantic models
│   └── README.md           # API documentation
│
├── core/                   # Core modules
│   ├── stt_module.py       # Whisper STT wrapper
│   ├── stt_streaming_module.py
│   ├── llm_module.py       # Ollama LLM client
│   ├── tts_module.py       # Edge TTS wrapper
│   ├── action_manager.py   # Actions handler
│   ├── state_manager.py    # State management
│   └── README.md           # Core modules documentation
│
├── utils/                  # Utility modules
│   ├── text_cleaning.py    # Text preprocessing
│   ├── port_manager.py     # Port management
│   └── README.md           # Utils documentation
│
├── static/                 # Frontend
│   ├── index.html          # Main web UI
│   ├── js/                 # JavaScript modules
│   │   ├── audio.js
│   │   ├── websocket.js
│   │   └── ui.js
│   ├── css/                # Stylesheets
│   └── pcm-processor.js    # Audio processing worker
│
├── docs/                   # Documentation
│   ├── README.md           # Documentation index
│   ├── PROJECT_SUMMARY.md
│   ├── architecture/       # Architecture docs
│   ├── guides/             # Developer guides
│   └── testing/            # Testing docs
│
├── uploads/                # Temporary audio inputs
├── outputs/                # Generated audio responses
├── models/                 # Downloaded ML models
├── venv/                   # Python virtual environment
│
├── README.md               # Main project readme
└── CLAUDE.md               # This file (AI assistant instructions)
```

## Testing the Pipeline

### Manual Component Testing

To manually test individual components:

```python
# Test STT
from core.stt_module import STTModule
stt = STTModule(model_size="base")
text = stt.transcribe("path/to/audio.wav", language="ru")
print(text)

# Test LLM
from core.llm_module import LLMModule
llm = LLMModule(model_name="gpt-oss:20b")
response = llm.generate_response("Привет, как дела?")
print(response)

# Test TTS
from core.tts_module import TTSModule
import asyncio
tts = TTSModule()
asyncio.run(tts.synthesize_async("Привет мир", "test_output.wav", language="ru"))

# Test Text Cleaning
from utils.text_cleaning import clean_text_for_tts
text = "TECH:debug Привет! {\"json\": \"data\"}"
cleaned = clean_text_for_tts(text)
print(cleaned)  # Output: "Привет!"
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

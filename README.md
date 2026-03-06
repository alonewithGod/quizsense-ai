# QuizSense AI

Real-time lecture assistant that listens through your microphone, detects likely questions, and shows short bilingual answers in English and Korean.

## Features
- Real-time microphone input
- Fast local speech-to-text with `faster-whisper`
- Simple question detection
- Short English answer generation with Korean translation
- Q&A history panel in the UI
- Export Q&A history as JSON
- Local LLM support through Ollama

## Tech Stack
- Python
- Tkinter
- faster-whisper
- Ollama

## Project Structure
```text
quizzesense_ai.py
requirements.txt
README.md
.gitignore
```

## Prerequisites
Install these first:
1. **Python 3.10+**
2. **Ollama** installed and running locally
3. A downloaded Ollama model, for example:
   ```bash
   ollama run llama3.1:8b
   ```

## Installation
Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

## How to Run
Start Ollama first, then run:

```bash
python quizzesense_ai.py
```

## Default Settings
The current code uses:
- Whisper model: `base`
- Ollama model: `llama3.1:8b`
- Device: `cpu`

You can change these values near the top of `quizzesense_ai.py` in the configuration section.

## Notes
- This app listens through your microphone, not system audio.
- It works best when the lecture is mostly in English, because transcription is currently fixed to `language="en"`.
- Question detection is rule-based, so it may miss some questions or trigger on non-questions.
- Generated answers depend on the local Ollama model quality and speed.

## Recommended Next Improvements
- Add start / stop buttons in the UI
- Add model selection in settings
- Save full transcript optionally
- Improve question detection with context-aware logic
- Package as a desktop app with PyInstaller
- Build a web version with FastAPI + frontend

## License
Choose a license before publishing publicly. If you want others to freely use and modify it, MIT is a simple choice.

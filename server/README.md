# VeriFact Backend

AI-powered fact-checking API for the VeriFact Chrome extension.

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# 4. Run the dev server
uvicorn app.main:app --reload

# 5. Open the auto-generated docs
# http://localhost:8000/docs
```

## Project Structure

```
verifact-backend/
├── app/
│   ├── main.py              # App entry point, CORS, router registration
│   ├── dependencies.py      # Shared HTTP clients (dependency injection)
│   ├── routers/
│   │   ├── fact_check.py    # POST /api/fact-check
│   │   └── transcribe.py    # POST /api/transcribe
│   ├── services/
│   │   ├── text_cleaner.py  # Text cleaning utilities
│   │   ├── claim_extractor.py  # Groq API — claim extraction
│   │   ├── fact_checker.py     # Gemini API — verification
│   │   └── transcriber.py      # Groq Whisper — transcription
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response models
│   └── prompts/
│       ├── claim_extraction.md
│       └── fact_verification.md
├── requirements.txt
├── .env.example
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/fact-check` | Fact-check highlighted text |
| POST | `/api/transcribe` | Transcribe audio/video file |
| GET | `/health` | Health check |

## Implementation Checklist

- [ ] Get Groq API key from https://console.groq.com
- [ ] Get Gemini API key from https://aistudio.google.com
- [ ] Uncomment the API call in `services/claim_extractor.py`
- [ ] Uncomment the API call in `services/fact_checker.py`
- [ ] Uncomment the API call in `services/transcriber.py`
- [ ] Test via http://localhost:8000/docs
- [ ] Handle JSON parsing edge cases (malformed LLM responses)
- [ ] Add asyncio.gather() for parallel claim verification
- [ ] Deploy to Railway/Render

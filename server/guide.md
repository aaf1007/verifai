# VeriFact Server — Beginner's Guide to the Codebase

## How it works

The server is a **FastAPI backend** — a Python web server that the Chrome extension calls. When you highlight text and right-click → "Fact-check this", the extension sends an HTTP POST request to this server, which runs a 4-step pipeline and returns a JSON result.

---

## The 4-step pipeline

```
User's highlighted text
        ↓
[1] text_cleaner.py     → strips invisible unicode chars, collapses whitespace
        ↓
[2] claim_extractor.py  → sends text to Groq (LLaMA 3.3 70B) to pull out
                          individual factual claims (ignores opinions)
        ↓
[3] fact_checker.py     → for each claim, asks Gemini 2.5 Flash (with live
                          Google Search) to return a verdict + evidence sources
        ↓
[4] fact_check.py       → aggregates all verdicts into one overall verdict
                          and builds a human-readable summary → sends back JSON
```

---

## How FastAPI wires it all together

FastAPI uses three concepts that appear everywhere:

- **Routers** (`routers/`) — define URL endpoints (`POST /api/fact-check`). They receive requests, call services, and return responses.
- **Services** (`services/`) — pure business logic. No HTTP knowledge. Each does one job (clean, extract, verify, transcribe).
- **Dependencies** (`dependencies.py`) — shared objects (the Groq and Gemini clients) that FastAPI injects into routers automatically via `Depends()`. This avoids creating a new API connection on every request.

---

## Key FastAPI concept to internalize

When a request hits `POST /api/fact-check`, FastAPI automatically:

1. Deserializes the JSON body into `FactCheckRequest` (and rejects bad input with 422 before your code runs)
2. Calls `get_groq_client()` and `get_gemini_client()` and injects the results into the function
3. Serializes your returned `FactCheckResponse` back to JSON

You never write `json.loads(request.body)` or `json.dumps(response)` — Pydantic + FastAPI handle all of that.

---

## What's implemented vs placeholder

| File | Status | Notes |
|------|--------|-------|
| `services/fact_checker.py` | Fully implemented | Gemini + Google Search Grounding works |
| `services/claim_extractor.py` | Placeholder | Groq API call is commented out (TODO); currently passes raw text through as a single claim |
| `services/transcriber.py` | Placeholder | Whisper call is commented out; returns a dummy response |

---

## Recommended reading order

### 1. `app/models/schemas.py`
Start here. This defines every data shape in the system. Understanding `FactCheckRequest`, `ClaimAnalysis`, and `FactCheckResponse` first means every other file will make immediate sense. You'll know what data flows where.

### 2. `app/main.py`
Short file. Shows how FastAPI starts up, configures CORS (so the browser extension can talk to it), and mounts the routers. Gives you the skeleton of the app.

### 3. `app/dependencies.py`
Explains the singleton client pattern and FastAPI's `Depends()` system. Once you get this, the function signatures in all routers make sense.

### 4. `app/services/text_cleaner.py`
Simplest service. Pure Python, no external calls. Good warmup before the API-heavy ones.

### 5. `app/prompts/claim_extraction.md`
Read the prompt before the code that uses it. You'll understand what Groq is supposed to return — a JSON array of `{claim, checkability}` objects.

### 6. `app/services/claim_extractor.py`
The real API call is commented out (TODO). The structure shows you how it *will* work — reads the prompt, calls Groq, parses the JSON array back.

### 7. `app/prompts/fact_verification.md`
Same idea — read the prompt before the service. This tells Gemini to return `{verdict, confidence, explanation, domain}` as JSON.

### 8. `app/services/fact_checker.py`
The most important and fully implemented service. Shows:
- `client.aio` (async Gemini calls)
- Google Search Grounding
- How sources are pulled from `grounding_metadata` (not the model's text — more reliable)
- Graceful JSON parse failure handling (degrades to `UNVERIFIABLE` instead of crashing)

### 9. `app/routers/fact_check.py`
Now you can read the full pipeline end-to-end. This is the "conductor" — it calls clean → extract → verify in sequence, handles errors with `HTTPException`, and assembles the final `FactCheckResponse`.

### 10. `app/routers/transcribe.py` + `app/services/transcriber.py`
Optional stretch feature. The router is real but the service is a placeholder. Read last since it's independent of the main pipeline.

---

## File map at a glance

```
app/
├── main.py               # App entry point — startup, CORS, router registration
├── dependencies.py       # Shared Groq + Gemini clients (singleton pattern + DI)
├── models/
│   └── schemas.py        # All Pydantic data models (request/response shapes)
├── routers/
│   ├── fact_check.py     # POST /api/fact-check — orchestrates the pipeline
│   └── transcribe.py     # POST /api/transcribe — audio/video transcription
├── services/
│   ├── text_cleaner.py   # Step 1: clean raw text (no external calls)
│   ├── claim_extractor.py # Step 2: extract claims via Groq (partially implemented)
│   ├── fact_checker.py   # Step 3: verify claims via Gemini (fully implemented)
│   └── transcriber.py    # Optional: transcribe audio via Groq Whisper (placeholder)
└── prompts/
    ├── claim_extraction.md   # System prompt for Groq — what to extract and how
    └── fact_verification.md  # System prompt for Gemini — how to fact-check and format output
```

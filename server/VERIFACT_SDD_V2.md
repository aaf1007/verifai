# VeriFact — Software Design Document

## 1. Overview

VeriFact is an AI-powered Chrome extension that enables users to fact-check claims they encounter while browsing the web. Users highlight suspicious text on any webpage, right-click to trigger a fact-check, and receive a verdict with sourced citations displayed in a popup bubble near the selection. The system uses Groq for fast claim extraction, Google Gemini API with Google Search Grounding for web-based verification with citations, and optionally Groq-hosted Whisper for audio/video transcription.

**Target SDGs:** SDG 16 (Peace, Justice and Strong Institutions), SDG 3 (Good Health), SDG 4 (Quality Education)

---

## 2. Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CHROME EXTENSION                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ content.js   │  │ background.js│  │ popup.html/js    │  │
│  │              │  │ (service     │  │ (toolbar popup    │  │
│  │ - Captures   │  │  worker)     │  │  for full         │  │
│  │   selection  │←→│              │  │  results view)    │  │
│  │ - Injects    │  │ - Context    │  │                   │  │
│  │   popup      │  │   menu       │  │                   │  │
│  │   bubble     │  │ - API calls  │  │                   │  │
│  │ - Shows      │  │ - Message    │  │                   │  │
│  │   results    │  │   routing    │  │                   │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────┘  │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │ POST /api/fact-check
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ app/main.py — CORS, router registration, lifespan   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │ ROUTERS         │  │ SERVICES                        │  │
│  │                 │  │                                  │  │
│  │ fact_check.py   │  │ text_cleaner.py    (pure Python) │  │
│  │ POST /api/      │  │ claim_extractor.py (→ Groq API) │  │
│  │   fact-check    │  │ fact_checker.py    (→ Gemini API)│  │
│  │                 │  │ transcriber.py     (→ Groq Whi) │  │
│  │ transcribe.py   │  │                                  │  │
│  │ POST /api/      │  └─────────────────────────────────┘  │
│  │   transcribe    │                                        │
│  └─────────────────┘  ┌─────────────────────────────────┐  │
│                        │ MODELS                          │  │
│  ┌─────────────────┐  │                                  │  │
│  │ DEPENDENCIES    │  │ schemas.py (Pydantic models)     │  │
│  │                 │  │ - FactCheckRequest               │  │
│  │ dependencies.py │  │ - ExtractedClaim                 │  │
│  │ - Groq client   │  │ - ClaimAnalysis                  │  │
│  │ - Gemini client │  │ - FactCheckResponse              │  │
│  └─────────────────┘  │ - TranscribeResponse             │  │
│                        └─────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PROMPTS                                              │   │
│  │ prompts/claim_extraction.md                          │   │
│  │ prompts/fact_verification.md                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow (Pipeline)

```
User highlights text on webpage
        │
        ▼
[1. TEXT CLEANING] ─── text_cleaner.py
        │   - Strip invisible Unicode chars (\u200b, \u200d, \u00ad)
        │   - Collapse whitespace
        │   - Trim and truncate to 2000 chars
        ▼
[2. CLAIM EXTRACTION] ─── claim_extractor.py → Groq API
        │   - Model: llama-3.3-70b-versatile
        │   - Input: cleaned text + optional context
        │   - Output: JSON array of {claim, checkability} objects
        │   - Filters out opinions, predictions, subjective statements
        ▼
[3. FACT VERIFICATION] ─── fact_checker.py → Gemini API (with Google Search Grounding)
        │   - Model: gemini-2.5-flash
        │   - Input: one claim at a time
        │   - Output: verdict JSON + groundingMetadata with source URLs
        │   - Gemini searches Google in real-time before responding
        │   - Sources come from grounding metadata, not LLM text
        ▼
[4. AGGREGATION] ─── fact_check.py router
        │   - Combine individual verdicts into overall_verdict
        │   - Build human-readable summary
        │   - Return FactCheckResponse
        ▼
Results displayed in popup bubble near selection
```

### 2.3 Optional Whisper Branch

```
User provides audio/video URL or file
        │
        ▼
[TRANSCRIPTION] ─── transcriber.py → Groq Whisper API
        │   - Model: whisper-large-v3-turbo
        │   - Multipart form upload (NOT JSON)
        │   - Max 25MB free tier
        ▼
Transcribed text → enters pipeline at step [1. TEXT CLEANING]
```

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Chrome Extension (Manifest V3) | Content script, service worker, popup |
| Frontend UI | HTML/CSS/JS (Vanilla) | Popup bubble and toolbar popup |
| Backend | FastAPI (Python 3.11+) | REST API, pipeline orchestration |
| HTTP Client | httpx (async) | Groq API calls |
| Gemini SDK | google-genai | Gemini API calls with grounding |
| Claim Extraction | Groq API (LLaMA 3.3 70B) | Fast claim parsing and classification |
| Fact Verification | Google Gemini 2.5 Flash + Google Search Grounding | Grounded web research with citations |
| Transcription | Groq-hosted Whisper Large v3 | Audio/video speech-to-text |
| Data Validation | Pydantic v2 | Request/response schema enforcement |
| Config | pydantic-settings | Environment variable management |
| Deployment | Railway or Render | Backend hosting |

---

## 4. Project Structure

```
verifact/
├── extension/                    # Chrome Extension
│   ├── manifest.json             # Manifest V3 config
│   ├── content.js                # Injected into pages — selection capture + bubble rendering
│   ├── background.js             # Service worker — context menu + API calls
│   ├── popup.html                # Toolbar popup — full results view
│   ├── popup.js                  # Toolbar popup logic
│   ├── styles.css                # Injected styles for popup bubble
│   └── icons/                    # Extension icons (16, 48, 128)
│
├── backend/                      # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # App entry, CORS, router registration
│   │   ├── dependencies.py       # Shared httpx clients (DI)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── fact_check.py     # POST /api/fact-check
│   │   │   └── transcribe.py     # POST /api/transcribe
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── text_cleaner.py   # Text cleaning pipeline
│   │   │   ├── claim_extractor.py # Groq integration
│   │   │   ├── fact_checker.py   # Gemini API integration
│   │   │   └── transcriber.py    # Groq Whisper integration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py        # All Pydantic models
│   │   └── prompts/
│   │       ├── claim_extraction.md
│   │       └── fact_verification.md
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
```

---

## 5. API Design

### 5.1 POST /api/fact-check

**Request:**
```json
{
  "text": "string (required, 1-2000 chars)",
  "url": "string | null (source page URL)",
  "context": "string | null (surrounding paragraph, max 5000 chars)",
  "model": "string (default: gemini-2.5-flash)"
}
```

**Response:**
```json
{
  "overall_verdict": "TRUE | FALSE | MOSTLY_TRUE | MOSTLY_FALSE | UNVERIFIABLE",
  "summary": "Analyzed 3 claims. 2 verified as true. 1 found to be false.",
  "claims": [
    {
      "statement": "The extracted claim text",
      "verdict": "TRUE | FALSE | MOSTLY_TRUE | MOSTLY_FALSE | UNVERIFIABLE",
      "confidence": 0.0 - 1.0,
      "explanation": "Evidence-based explanation",
      "sources": ["https://source1.com", "https://source2.com"],
      "domain": "health | science | politics | history | finance | technology | sports | geography | other",
      "checkability": "high | medium | low"
    }
  ],
  "checked_at": "2026-03-27T12:00:00Z",
  "source_url": "https://original-page.com/article"
}
```

**Error responses:**
- `400`: Empty text after cleaning
- `502`: External API error (Groq or Gemini)
- `504`: External API timeout

### 5.2 POST /api/transcribe

**Request:** Multipart form data with audio file (max 25MB). Supported: mp3, mp4, m4a, wav, webm.

**Response:**
```json
{
  "text": "Full transcription text",
  "language": "en",
  "duration_seconds": 34.5
}
```

### 5.3 GET /health

**Response:** `{"status": "ok", "service": "verifact"}`

---

## 6. Data Models (Pydantic Schemas)

```python
# app/models/schemas.py

class Verdict(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    MOSTLY_TRUE = "MOSTLY_TRUE"
    MOSTLY_FALSE = "MOSTLY_FALSE"
    UNVERIFIABLE = "UNVERIFIABLE"

class Checkability(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class FactCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    url: str | None = None
    context: str | None = Field(None, max_length=5000)
    model: str = "gemini-2.5-flash"

class ExtractedClaim(BaseModel):
    claim: str
    checkability: Checkability = Checkability.MEDIUM

class ClaimAnalysis(BaseModel):
    statement: str
    verdict: Verdict
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    sources: list[str] = []
    domain: str = "other"
    checkability: Checkability = Checkability.MEDIUM

class FactCheckResponse(BaseModel):
    overall_verdict: Verdict
    summary: str
    claims: list[ClaimAnalysis]
    checked_at: datetime
    source_url: str | None = None

class TranscribeResponse(BaseModel):
    text: str
    language: str | None = None
    duration_seconds: float | None = None
```

---

## 7. Service Implementation Details

### 7.1 text_cleaner.py

Pure Python utility — no external API calls.

- Strip invisible Unicode characters: `\u200b`, `\u200c`, `\u200d`, `\u200e`, `\u200f`, `\ufeff`, `\u00ad`, `\u2060`, `\u180e`
- Collapse multiple whitespace characters into single spaces
- Trim leading/trailing whitespace
- Truncate to 2000 characters

### 7.2 claim_extractor.py → Groq API

- **Endpoint:** `POST https://api.groq.com/openai/v1/chat/completions`
- **Model:** `llama-3.3-70b-versatile`
- **Temperature:** 0.1 (low for consistent extraction)
- **Max tokens:** 1024
- **System prompt:** loaded from `prompts/claim_extraction.md`
- **User message:** The cleaned text. If context is provided, format as `"Highlighted text: {text}\n\nSurrounding context: {context}"`
- **Expected response:** JSON array of `{"claim": "...", "checkability": "high|medium|low"}` objects
- **Parsing:** Strip markdown code fences if present. Find first `[` and last `]`. Parse with `json.loads()`. Handle `json.JSONDecodeError` gracefully.
- **Fallback:** If parsing fails, treat the entire text as a single claim with `checkability: "medium"`

### 7.3 fact_checker.py → Google Gemini API (with Google Search Grounding)

- **SDK:** `google-genai` (official Google Generative AI SDK)
- **Client:** `genai.Client(api_key=GEMINI_API_KEY)` — sync creation, NOT async
- **Method:** `client.models.generate_content()` (sync) or `client.aio.models.generate_content()` (async)
- **Model:** `gemini-2.5-flash`
- **Grounding:** Pass `tools=[types.Tool(google_search=types.GoogleSearch())]` in config to enable Google Search Grounding
- **System prompt:** loaded from `prompts/fact_verification.md`
- **User message:** `"Fact-check this claim: {claim}"`
- **Expected response text:** JSON object with `verdict`, `confidence`, `explanation`, `domain`
- **Source URLs:** Extract from `response.candidates[0].grounding_metadata.grounding_chunks` — these are the actual Google Search results, NOT from the LLM text. This is more reliable than parsing URLs from model output.
- **Parsing:** Strip markdown code fences from response.text. Find first `{` and last `}`. Parse as dict. Map to `ClaimAnalysis` model.
- **Verdict mapping:** If Gemini returns an unrecognized verdict string, default to `UNVERIFIABLE`
- **Process claims sequentially first.** Optimize with `asyncio.gather()` using `client.aio` later.
- **Free tier:** 500 grounded requests per day on Flash models. 1,500 RPD on Pro models.

**Key code pattern:**
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"Fact-check this claim: {claim}",
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.1,
    ),
)

# Text response (contains your verdict JSON)
content = response.text

# Grounding sources (actual Google Search URLs)
grounding = response.candidates[0].grounding_metadata
sources = []
if grounding and grounding.grounding_chunks:
    sources = [chunk.web.uri for chunk in grounding.grounding_chunks if chunk.web]
```

### 7.4 transcriber.py → Groq Whisper API

- **Endpoint:** `POST https://api.groq.com/openai/v1/audio/transcriptions`
- **Model:** `whisper-large-v3-turbo`
- **Format:** Multipart form data (NOT JSON). Use `data={}` for model/format, `files={}` for the audio file.
- **Response format:** `verbose_json` (includes language and duration)
- **Max file size:** 25MB (free tier), 100MB (dev tier)

### 7.5 dependencies.py — Client Management

- Create reusable `httpx.AsyncClient` for Groq (with base_url and auth headers)
- Create `genai.Client` for Gemini (sync creation — just holds API key config)
- Set appropriate timeouts: 15s for Groq (fast), Gemini timeout handled by SDK
- Expose via FastAPI dependency injection: `Depends(get_groq_client)`, `Depends(get_gemini_client)`
- Clean up httpx client on app shutdown via lifespan handler
- **Note:** `get_gemini_client()` is a sync function (not async) because `genai.Client()` just creates a config object, no network call

---

## 8. Chrome Extension Details

### 8.1 manifest.json

```json
{
  "manifest_version": 3,
  "name": "VeriFact",
  "version": "0.1.0",
  "description": "AI-powered fact-checking for any webpage",
  "permissions": ["contextMenus", "activeTab", "storage"],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "css": ["styles.css"]
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### 8.2 background.js (Service Worker)

Responsibilities:
- Register context menu item on install: `chrome.contextMenus.create({ id: "verifact-check", title: "VeriFact — Fact-check this", contexts: ["selection"] })`
- Listen for context menu clicks: `chrome.contextMenus.onClicked.addListener()`
- When triggered: get selected text from `info.selectionText`, send POST to backend, forward results to content script via `chrome.tabs.sendMessage()`
- Store backend URL in `chrome.storage.local` for configurability

### 8.3 content.js (Content Script)

Responsibilities:
- Listen for messages from service worker via `chrome.runtime.onMessage.addListener()`
- On receiving results: create a popup bubble `<div>` with `position: absolute`
- Position the bubble near the user's selection using `window.getSelection().getRangeAt(0).getBoundingClientRect()`
- Render verdict badges, confidence bars, explanations, and source links
- Show loading state while waiting for results
- Handle "no claims found" and error states
- Provide "Expand" button that signals the toolbar popup to open with full details

### 8.4 popup.html / popup.js (Toolbar Popup)

Responsibilities:
- Full detailed results view (same data as bubble, more space)
- Session history of recent fact-checks (stored in `chrome.storage.session`)
- Settings (backend URL configuration)

### 8.5 User Interaction Flow

1. User browses a webpage normally
2. User highlights suspicious text by dragging
3. User right-clicks → context menu shows "VeriFact — Fact-check this"
4. User clicks the menu item
5. Content script shows a small loading bubble near the selection
6. Service worker sends text to FastAPI backend
7. Backend runs pipeline: clean → extract claims → verify each claim
8. Backend returns FactCheckResponse JSON
9. Service worker forwards results to content script
10. Content script renders the popup bubble with verdicts, explanations, sources
11. User can click "Expand" to see full details in the toolbar popup

---

## 9. User Stories (MoSCoW)

### Must Have
| ID | Story | Acceptance Criteria | Epic |
|----|-------|-------------------|------|
| M1 | As a user, I want to highlight text and right-click to fact-check via context menu | Context menu appears with "VeriFact" on right-click with selection. Sends text to backend. | Extension Core |
| M2 | As a user, I want to see results in a popup bubble near my selection with verdict badges | Bubble appears within 10s. Verdicts shown as color-coded badges (green/red/yellow). | Extension UI |
| M3 | As a user, I want each verdict to include an explanation and source links | Each claim shows explanation text and at least 1 clickable source URL. | Extension UI |
| M4 | As a developer, I want a FastAPI backend with /api/fact-check returning structured JSON | Returns valid JSON matching FactCheckResponse schema. Handles errors with proper HTTP codes. | Backend API |
| M5 | As a developer, I want Groq to extract individual claims and classify their checkability | Returns array of ExtractedClaim objects. Filters opinions. Classifies as high/medium/low. | Claim Extraction |
| M6 | As a developer, I want Gemini with Google Search Grounding to verify each claim with citations | Each claim gets verdict, confidence, explanation, and sources from Gemini grounding metadata. | Fact Verification |
| M7 | As a user, I want text cleaned before processing (whitespace, invisible chars, truncation) | Text cleaned before API calls. Max 2000 chars. | Text Processing |

### Should Have
| ID | Story | Acceptance Criteria | Epic |
|----|-------|-------------------|------|
| S1 | As a user, I want a loading indicator while fact-check is in progress | Loading bubble appears immediately, disappears when results load. | Extension UI |
| S2 | As a user, I want surrounding paragraph context sent for better accuracy | parentElement.textContent sent as optional context field. | Text Processing |
| S3 | As a user, I want session history of recent fact-checks | Last 10 checks stored in chrome.storage.session. Viewable in toolbar popup. | Extension UI |
| S4 | As a user, I want to click the extension icon to see full results | Toolbar popup shows detailed view of most recent fact-check. | Extension UI |
| S5 | As a developer, I want error handling with user-friendly messages | Errors shown as descriptive messages, not raw JSON. Covers timeout, rate limit, empty text. | Error Handling |
| S6 | As a user, I want confidence scores as visual bars | Confidence shown as colored progress bar next to each claim. | Extension UI |

### Could Have
| ID | Story | Acceptance Criteria | Epic |
|----|-------|-------------------|------|
| C1 | As a user, I want to fact-check audio/video by providing a file | Upload audio file. Transcribed via Whisper. Text enters fact-check pipeline. | Transcription |
| C2 | As a user, I want checkability indicators showing how reliable each check is | "high/medium/low" badge per claim from extraction stage. | Extension UI |
| C3 | As a user, I want domain labels showing what category each claim belongs to | Domain badge (health, science, politics, etc.) per claim from verification. | Extension UI |
| C4 | As a developer, I want parallel claim verification for speed | asyncio.gather() verifies multiple claims concurrently. | Performance |
| C5 | As a user, I want to export results as shareable text | Copy-to-clipboard button with formatted summary. | Export |

### Won't Have (v1)
| ID | Story | Rationale |
|----|-------|-----------|
| W1 | Auto-scan entire pages for misinformation | Too complex for v1. Rate limits, claim extraction at scale, UX concerns. |
| W2 | Inline annotations highlighting claims directly on the page | Complex DOM manipulation, CSS conflicts across sites. Revisit v2. |
| W3 | User accounts and authentication | Not needed for MVP. Extension works without login. |
| W4 | Dashboard with analytics and trending misinformation | Requires database and separate frontend. Stretch for v2. |

---

## 10. Iteration Plan

### Iteration 1 — Backend Pipeline (Week 1-2)
- [ ] Set up FastAPI project with Pydantic schemas
- [ ] Implement text_cleaner.py
- [ ] Implement claim_extractor.py with Groq API call
- [ ] Implement fact_checker.py with Gemini API + Google Search Grounding
- [ ] Wire up /api/fact-check endpoint end-to-end
- [ ] Implement JSON parsing with fence-stripping and error handling
- [ ] Test full pipeline via /docs Swagger UI

### Iteration 2 — Chrome Extension (Week 2-3)
- [ ] Create Manifest V3 extension shell
- [ ] Implement background.js with context menu registration
- [ ] Implement content.js with selection capture
- [ ] Build popup bubble UI with verdict rendering
- [ ] Add loading and error states
- [ ] Wire extension to backend API
- [ ] Implement context capture (surrounding paragraph)

### Iteration 3 — Polish & Stretch (Week 3-4)
- [ ] Build toolbar popup with full results view
- [ ] Add session history
- [ ] Add confidence bar visualizations
- [ ] Add checkability and domain badges
- [ ] Implement Whisper transcription endpoint (stretch)
- [ ] Deploy backend to Railway/Render
- [ ] End-to-end testing and demo preparation

---

## 11. Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| Response Time | End-to-end result within 10 seconds for single-claim highlights |
| Reliability | Graceful degradation if APIs are unavailable. User-friendly error messages. |
| Security | API keys in env vars only. CORS restricted to extension origin. |
| Privacy | No user data stored in v1. Text sent for processing only, not persisted. |
| Compatibility | Chrome 120+ with Manifest V3 |
| Accessibility | WCAG 2.1 AA contrast. Keyboard navigable popup. |

---

## 12. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| LLM hallucination in verdicts | Medium | Gemini grounds responses via Google Search. Confidence scores flag uncertainty. |
| API rate limits | Medium | Client-side rate limiting. Informative error messages. |
| Claim extraction misses nuance | High | Iterate prompts. Use context. Accept v1 imperfections, prioritize transparency. |
| JSON parsing failures from LLM | High | Fence-stripping. Fallback to treating full text as single claim. |
| Extension breaks on complex sites | Medium | window.getSelection() is browser-native and reliable. Avoid DOM manipulation in v1. |
| API cost overrun | Low | Monitor usage. Set daily limits in backend. |

---

## 13. External API Reference

### Groq (Claim Extraction + Whisper)
- **Base URL:** `https://api.groq.com/openai/v1`
- **Auth:** `Authorization: Bearer {GROQ_API_KEY}`
- **Chat endpoint:** `POST /chat/completions`
- **Whisper endpoint:** `POST /audio/transcriptions`
- **Pricing:** ~$0.02-$0.11/hr for Whisper. LLM inference per-token.
- **Docs:** https://console.groq.com/docs

### Google Gemini (Fact Verification)
- **SDK:** `google-genai` (pip install google-genai)
- **Auth:** `genai.Client(api_key=GEMINI_API_KEY)`
- **Method:** `client.models.generate_content()` or `client.aio.models.generate_content()` (async)
- **Model:** `gemini-2.5-flash` (free tier, fast, grounding supported)
- **Grounding:** Pass `tools=[types.Tool(google_search=types.GoogleSearch())]` in GenerateContentConfig
- **Key feature:** Google Search Grounding — Gemini searches Google in real-time before responding. Source URLs returned via `groundingMetadata.grounding_chunks`, not from LLM text.
- **Free tier:** 500 grounded requests per day (Flash), 1,500 RPD (Pro). No credit card required.
- **Get API key:** https://aistudio.google.com → "Get API key" in sidebar
- **Docs:** https://ai.google.dev/gemini-api/docs/google-search

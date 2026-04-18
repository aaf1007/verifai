# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VerifAI is a two-part system: a **Chrome extension** (WXT + React + TypeScript) and a **FastAPI backend** (Python). Users highlight text on any webpage, right-click → "VerifAI: Verify Text", and receive a fact-check verdict in the extension popup.

## Repository Structure

```
verifai/
├── extension/          # Chrome extension (WXT + React)
└── server/             # FastAPI backend (Python)
```

## Extension (`extension/`)

### Commands

```bash
cd extension
npm install
npm run dev          # Dev mode with HMR (Chrome by default)
npm run dev:firefox  # Dev mode for Firefox
npm run build        # Production build → .output/chrome-mv3/
npm run zip          # Package for Chrome Web Store
npm run compile      # TypeScript type-check only (no emit)
```

Load the extension: go to `chrome://extensions` → Developer mode → Load unpacked → select `.output/chrome-mv3-dev/`.

### Architecture

- **`src/entrypoints/background.ts`** — Service worker. Registers the context menu, opens the popup, makes the `POST /api/fact-check` call, and persists results to `browser.storage.local` as `verifaiResults` (array of `ResultEntry`).
- **`src/entrypoints/popup/`** — Popup UI (React). `App.tsx` reads `verifaiResults` from storage and reactively updates on storage changes. Three tabs: Recent (latest result), History (all results reversed), Chat (placeholder).
- **`src/entrypoints/popup/components/ClaimCard.tsx`** — Exports `ClaimCard` (history card with expand-to-modal), `ClaimCardModal`, `ClaimCardContent` (shared accordion body), and `VerdictBadge`.
- **`src/entrypoints/popup/components/ClaimCardInline.tsx`** — `ClaimCardInline` for the Recent tab; handles loading/error/empty states, renders `ClaimCardContent` inline (no modal).
- **`src/components/ui/`** — Reusable UI primitives (tabs, spinner, border-beam).
- **`src/entrypoints/content.ts`** — Content script stub; currently unused beyond listening for `VERIFAI_CHECK` messages.

**UI libraries:** HeroUI (`@heroui/react`) for the Tabs component; Tailwind CSS v4; Motion for animations.

**State flow:** background writes to `storage.local` → popup listens via `browser.storage.onChanged` → React re-renders.

**`ResultEntry` shape** (defined in `App.tsx`, written by `background.ts`):
```ts
{ status: "loading" | "done" | "error"; result?: FactCheckResponse; message?: string }
```
Background writes a `loading` entry before opening the popup, then overwrites it with `done` or `error` once the API responds.

**API URL:** hardcoded as `http://localhost:8000` in `background.ts`. No env-var mechanism exists yet.

**Brand gradient:** defined as CSS variable `--gradient` in `App.css`. Applied to tab indicators via `[data-slot="indicator"]` and `.heading` class.

**Icon assets:** `public/verifai/` has `light-mode.png`, `dark-mode.png`, and sized icons. Extension icons are in `public/icon/`.

## Server (`server/`)

### Commands

```bash
cd server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Add GROQ_API_KEY and GEMINI_API_KEY
uvicorn app.main:app --reload   # Dev server at http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Architecture

- **`app/main.py`** — FastAPI entry point; registers CORS, routers, and lifespan (client cleanup).
- **`app/dependencies.py`** — Lazy singleton clients for Groq (httpx.AsyncClient) and Gemini (genai.Client), injected via `Depends()`.
- **`app/routers/fact_check.py`** — `POST /api/fact-check`: cleans text → extracts claims (Groq) → verifies each claim (Gemini with Search Grounding) → returns `FactCheckResponse`.
- **`app/routers/transcribe.py`** — `POST /api/transcribe`: Groq Whisper for audio/video.
- **`app/services/`** — `text_cleaner.py` (strips invisible chars, truncates to 2000 chars), `claim_extractor.py` (Groq), `fact_checker.py` (Gemini), `transcriber.py` (Groq Whisper).
- **`app/models/schemas.py`** — Pydantic models: `FactCheckRequest`, `ExtractedClaim`, `ClaimAnalysis`, `FactCheckResponse`, `TranscribeResponse`.
- **`app/prompts/`** — Markdown prompt files for claim extraction and fact verification.

**API ↔ Extension contract:** The extension POSTs `{ text, url?, context?, model? }` and expects `FactCheckResponse` — the TypeScript type in `background.ts` must stay in sync with the Pydantic schema in `schemas.py`.

## Environment Variables

```
GROQ_API_KEY=       # From https://console.groq.com
GEMINI_API_KEY=     # From https://aistudio.google.com
ALLOWED_ORIGINS=*   # Restrict to extension ID in production
```

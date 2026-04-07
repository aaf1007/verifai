<div align="center">
  <img src="extension/public/verifai/light-mode.png" alt="VerifAI" width="280" />
  <p><em>AI-powered fact-checking in your browser.</em></p>
</div>

---

VerifAI is a Chrome extension backed by a FastAPI service that helps users fact-check content without leaving the page. It turns highlighted text into structured claims, verifies them against grounded web results, and returns a clear verdict with explanations and source links.

## What It Does

- Fact-check highlighted text from any webpage
- Break results into individual claims with verdicts and sources
- Let users ask follow-up questions in the built-in chat view
- Include an experimental TikTok transcription and fact-checking flow that is still under development

## How It Works

1. The user highlights text in the browser and runs **VerifAI: Verify Text** from the context menu.
2. The extension sends the request to the local backend at `http://localhost:8000`.
3. The backend cleans the text, uses Groq to extract checkable claims, and uses Gemini with Google Search grounding to verify them.
4. The extension stores the response and shows it in the popup under Recent, History, and Chat.

For TikTok, the extension can also send captured video to the transcription pipeline before fact-checking the resulting transcript. That feature is still in development and should be treated as experimental.

## Run Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Groq API key
- A Gemini API key
- `ffmpeg` installed and available on your `PATH` if you want to use transcription features

### 1. Configure the backend

All API keys go in `server/.env`. The extension does not need its own API keys for local development.

Create the file from the example:

```bash
cd server
cp .env.example .env
```

Example `server/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
ALLOWED_ORIGINS=*
```

### 2. Start the backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Once it is running, you can confirm the API at `http://localhost:8000/health` or open the docs at `http://localhost:8000/docs`.

### 3. Start the extension

```bash
cd extension
npm install
npm run dev
```

Then open `chrome://extensions`, enable **Developer mode**, click **Load unpacked**, and select `extension/.output/chrome-mv3-dev/`.

### 4. Use the app

- Highlight text on a webpage
- Right-click and choose **VerifAI: Verify Text**
- Open the extension popup to review the latest result, past checks, and chat follow-ups

## Project Structure

| Directory | Description |
|-----------|-------------|
| [`extension/`](extension/) | Chrome extension built with WXT, React, and TypeScript |
| [`server/`](server/) | FastAPI backend for fact-checking, transcription, and chat |

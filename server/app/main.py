import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import close_clients
from app.routers import fact_check, transcribe


# Load .env before anything else
load_dotenv()


# ──────────────────────────────────────────────
# Lifespan: startup + shutdown events
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP — runs when the server starts
    print("VeriFact API starting up...")

    # Validate that API keys are set
    if not os.getenv("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY not set — claim extraction will fail")
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("WARNING: PERPLEXITY_API_KEY not set — fact verification will fail")

    yield  # App runs here

    # SHUTDOWN — runs when the server stops
    print("Shutting down, closing HTTP clients...")
    await close_clients()


# ──────────────────────────────────────────────
# Create the app
# ──────────────────────────────────────────────

app = FastAPI(
    title="VeriFact API",
    description="AI-powered fact-checking backend for the VeriFact Chrome extension",
    version="0.1.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# CORS — allow the Chrome extension to call this API
# ──────────────────────────────────────────────

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in allowed_origins.split(",")] if allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Register routers
# ──────────────────────────────────────────────

app.include_router(fact_check.router)
app.include_router(transcribe.router)


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "verifact"}

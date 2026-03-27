from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Fact Check
# ──────────────────────────────────────────────

class FactCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Highlighted text to fact-check")
    url: str | None = Field(None, description="Source page URL for context")
    context: str | None = Field(None, max_length=5000, description="Surrounding paragraph text")
    model: str = Field("sonar-pro", description="Perplexity model to use")


class ExtractedClaim(BaseModel):
    """Output from the claim extraction stage (Groq)."""
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
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    source_url: str | None = None


# ──────────────────────────────────────────────
# Transcription
# ──────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    text: str
    language: str | None = None
    duration_seconds: float | None = None

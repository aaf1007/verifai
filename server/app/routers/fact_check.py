from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_groq_client, get_perplexity_client
from app.models.schemas import FactCheckRequest, FactCheckResponse, Verdict
from app.services.claim_extractor import extract_claims
from app.services.fact_checker import verify_claims
from app.services.text_cleaner import clean_text


router = APIRouter(prefix="/api", tags=["fact-check"])


@router.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(
    request: FactCheckRequest,
    groq: httpx.AsyncClient = Depends(get_groq_client),
    perplexity: httpx.AsyncClient = Depends(get_perplexity_client),
):
    """
    Main fact-checking endpoint.

    Pipeline:
    1. Clean the highlighted text
    2. Extract individual claims via Groq
    3. Verify each claim via Perplexity Sonar
    4. Aggregate and return results
    """
    # Step 1: Clean the input text
    cleaned = clean_text(request.text)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Text is empty after cleaning")

    # Step 2: Extract claims
    try:
        claims = await extract_claims(groq, cleaned, request.context)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Claim extraction timed out")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")

    if not claims:
        return FactCheckResponse(
            overall_verdict=Verdict.UNVERIFIABLE,
            summary="No verifiable factual claims were found in the selected text.",
            claims=[],
            checked_at=datetime.utcnow(),
            source_url=request.url,
        )

    # Step 3: Verify each claim
    try:
        results = await verify_claims(perplexity, claims, request.model)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Fact verification timed out")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Perplexity API error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fact verification failed: {str(e)}")

    # Step 4: Aggregate results
    overall = _aggregate_verdict(results)
    summary = _build_summary(results)

    return FactCheckResponse(
        overall_verdict=overall,
        summary=summary,
        claims=results,
        checked_at=datetime.utcnow(),
        source_url=request.url,
    )


def _aggregate_verdict(claims) -> Verdict:
    """
    Determine overall verdict from individual claim verdicts.
    Simple logic: if any claim is FALSE, overall is DISPUTED.
    You can make this more sophisticated later.
    """
    verdicts = [c.verdict for c in claims]

    if Verdict.FALSE in verdicts:
        return Verdict.MOSTLY_FALSE
    if Verdict.MOSTLY_FALSE in verdicts:
        return Verdict.MOSTLY_FALSE
    if all(v == Verdict.TRUE for v in verdicts):
        return Verdict.TRUE
    if all(v == Verdict.UNVERIFIABLE for v in verdicts):
        return Verdict.UNVERIFIABLE
    return Verdict.MOSTLY_TRUE


def _build_summary(claims) -> str:
    """Build a human-readable summary of the fact-check results."""
    total = len(claims)
    true_count = sum(1 for c in claims if c.verdict in (Verdict.TRUE, Verdict.MOSTLY_TRUE))
    false_count = sum(1 for c in claims if c.verdict in (Verdict.FALSE, Verdict.MOSTLY_FALSE))
    unverified = sum(1 for c in claims if c.verdict == Verdict.UNVERIFIABLE)

    parts = []
    parts.append(f"Analyzed {total} claim{'s' if total != 1 else ''}.")
    if true_count:
        parts.append(f"{true_count} verified as true or mostly true.")
    if false_count:
        parts.append(f"{false_count} found to be false or misleading.")
    if unverified:
        parts.append(f"{unverified} could not be verified.")
    return " ".join(parts)

import json
from pathlib import Path

import httpx

from app.models.schemas import ClaimAnalysis, Verdict


# Load system prompt from file
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "fact_verification.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text()


async def verify_claim(client: httpx.AsyncClient, claim: str, model: str = "sonar-pro") -> ClaimAnalysis:
    """
    Verify a single claim using the Perplexity Sonar API.

    Args:
        client: The Perplexity httpx client (injected via Depends)
        claim: A single factual claim to verify
        model: Sonar model to use

    Returns:
        ClaimAnalysis with verdict, confidence, explanation, and sources
    """
    # ──────────────────────────────────────────────
    # TODO: This is where you make the actual API call
    #
    # response = await client.post(
    #     "/chat/completions",
    #     json={
    #         "model": model,
    #         "messages": [
    #             {"role": "system", "content": SYSTEM_PROMPT},
    #             {"role": "user", "content": f"Fact-check this claim: {claim}"},
    #         ],
    #     },
    # )
    # response.raise_for_status()
    # data = response.json()
    # content = data["choices"][0]["message"]["content"]
    #
    # # Parse the JSON response
    # result = json.loads(content)
    #
    # return ClaimAnalysis(
    #     statement=claim,
    #     verdict=Verdict(result["verdict"]),
    #     confidence=result["confidence"],
    #     explanation=result["explanation"],
    #     sources=result.get("sources", []),
    # )
    # ──────────────────────────────────────────────

    # PLACEHOLDER — remove this when you implement the above
    return ClaimAnalysis(
        statement=claim,
        verdict=Verdict.UNVERIFIABLE,
        confidence=0.0,
        explanation="Not yet implemented — replace this placeholder with the Perplexity API call above.",
        sources=[],
    )


async def verify_claims(client: httpx.AsyncClient, claims: list[str], model: str = "sonar-pro") -> list[ClaimAnalysis]:
    """
    Verify multiple claims. Processes sequentially for now.

    TODO (optimization): Use asyncio.gather() to verify claims in parallel
    once you've confirmed rate limits can handle it.
    """
    results = []
    for claim in claims:
        result = await verify_claim(client, claim, model)
        results.append(result)
    return results

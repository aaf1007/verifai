import json
from pathlib import Path

import httpx


# Load system prompt from file
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "claim_extraction.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text()

# Model to use on Groq
MODEL = "llama-3.3-70b-versatile"


async def extract_claims(client: httpx.AsyncClient, text: str, context: str | None = None) -> list[str]:
    """
    Send highlighted text to Groq and get back a list of factual claims.

    Args:
        client: The Groq httpx client (injected via Depends)
        text: Cleaned highlighted text from the user
        context: Optional surrounding paragraph for additional context

    Returns:
        List of claim strings extracted from the text
    """
    user_content = text
    if context:
        user_content = f"Highlighted text: {text}\n\nSurrounding context: {context}"

    # ──────────────────────────────────────────────
    # TODO: This is where you make the actual API call
    #
    # response = await client.post(
    #     "/chat/completions",
    #     json={
    #         "model": MODEL,
    #         "messages": [
    #             {"role": "system", "content": SYSTEM_PROMPT},
    #             {"role": "user", "content": user_content},
    #         ],
    #         "temperature": 0.1,  # low temp for consistent extraction
    #         "max_tokens": 1024,
    #     },
    # )
    # response.raise_for_status()
    # data = response.json()
    # content = data["choices"][0]["message"]["content"]
    #
    # # Parse the JSON array from the response
    # claims = json.loads(content)
    # return claims
    # ──────────────────────────────────────────────

    # PLACEHOLDER — remove this when you implement the above
    return [text]

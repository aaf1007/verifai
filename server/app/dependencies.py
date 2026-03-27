import os
import httpx


# ──────────────────────────────────────────────
# Shared HTTP clients (reused across requests)
# ──────────────────────────────────────────────

_groq_client: httpx.AsyncClient | None = None
_perplexity_client: httpx.AsyncClient | None = None


async def get_groq_client() -> httpx.AsyncClient:
    """Provides a reusable async HTTP client for the Groq API."""
    global _groq_client
    if _groq_client is None:
        _groq_client = httpx.AsyncClient(
            base_url="https://api.groq.com/openai/v1",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )
    return _groq_client


async def get_perplexity_client() -> httpx.AsyncClient:
    """Provides a reusable async HTTP client for the Perplexity API."""
    global _perplexity_client
    if _perplexity_client is None:
        _perplexity_client = httpx.AsyncClient(
            base_url="https://api.perplexity.ai",
            headers={
                "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    return _perplexity_client


async def close_clients():
    """Clean up HTTP clients on shutdown."""
    global _groq_client, _perplexity_client
    if _groq_client:
        await _groq_client.aclose()
        _groq_client = None
    if _perplexity_client:
        await _perplexity_client.aclose()
        _perplexity_client = None

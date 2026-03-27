import httpx

from app.models.schemas import TranscribeResponse


async def transcribe_audio(client: httpx.AsyncClient, file_bytes: bytes, filename: str) -> TranscribeResponse:
    """
    Transcribe audio using Groq-hosted Whisper.

    Args:
        client: The Groq httpx client
        file_bytes: Raw audio file bytes
        filename: Original filename (needed for content type detection)

    Returns:
        TranscribeResponse with transcription text and metadata
    """
    # ──────────────────────────────────────────────
    # TODO: Implement the Whisper API call
    #
    # Note: Whisper uses multipart form data, not JSON.
    # The endpoint is /audio/transcriptions (OpenAI-compatible).
    #
    # response = await client.post(
    #     "/audio/transcriptions",
    #     data={"model": "whisper-large-v3-turbo", "response_format": "verbose_json"},
    #     files={"file": (filename, file_bytes)},
    # )
    # response.raise_for_status()
    # data = response.json()
    #
    # return TranscribeResponse(
    #     text=data["text"],
    #     language=data.get("language"),
    #     duration_seconds=data.get("duration"),
    # )
    # ──────────────────────────────────────────────

    # PLACEHOLDER
    return TranscribeResponse(
        text="Transcription not yet implemented.",
        language=None,
        duration_seconds=None,
    )

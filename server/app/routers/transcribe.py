import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.dependencies import get_groq_client
from app.models.schemas import TranscribeResponse
from app.services.transcriber import transcribe_audio


router = APIRouter(prefix="/api", tags=["transcription"])

# 25MB limit (Groq free tier)
MAX_FILE_SIZE = 25 * 1024 * 1024

ALLOWED_TYPES = {"audio/mpeg", "audio/mp4", "audio/wav", "audio/webm", "audio/x-m4a", "video/mp4", "video/webm"}


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(..., description="Audio or video file to transcribe"),
    groq: httpx.AsyncClient = Depends(get_groq_client),
):
    """
    Transcribe audio/video content using Groq-hosted Whisper.
    The transcribed text can then be sent to /api/fact-check.
    """
    # Validate file type
    if file.content_type and file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: mp3, mp4, m4a, wav, webm",
        )

    # Read and validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: 25MB")

    # Transcribe
    try:
        result = await transcribe_audio(groq, contents, file.filename or "audio.wav")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Transcription timed out")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Whisper API error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    return result

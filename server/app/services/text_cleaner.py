import re

# Characters to strip — zero-width spaces, soft hyphens, etc.
INVISIBLE_CHARS = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u2060\u180e]"
)

MAX_TEXT_LENGTH = 2000


def clean_text(raw: str) -> str:
    """
    Clean user-highlighted text before sending to the pipeline.

    Steps:
    1. Strip invisible Unicode characters
    2. Collapse whitespace (multiple spaces, newlines, tabs → single space)
    3. Trim leading/trailing whitespace
    4. Truncate to MAX_TEXT_LENGTH characters
    """
    text = INVISIBLE_CHARS.sub("", raw)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    text = text[:MAX_TEXT_LENGTH]
    return text

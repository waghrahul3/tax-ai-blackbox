from utils.logger import get_logger

logger = get_logger(__name__)


def create_chunks(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks without external dependencies."""
    
    if not text:
        return []

    logger.info("Starting text chunking", extra={"text_length": len(text)})

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a natural boundary (newline or space)
        if end < len(text):
            newline = text.rfind('\n', start, end)
            space = text.rfind(' ', start, end)
            boundary = max(newline, space)
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap  # overlap with previous chunk

    logger.info(
        "Text chunking completed",
        extra={
            "chunk_count": len(chunks),
            "avg_chunk_size": sum(len(c) for c in chunks) // len(chunks) if chunks else 0
        }
    )

    return chunks
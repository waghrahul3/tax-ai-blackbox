from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger import get_logger

logger = get_logger(__name__)


def create_chunks(text):

    logger.info(
        "Starting text chunking",
        extra={"text_length": len(text)}
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200
    )

    logger.debug(
        "Text splitter configured",
        extra={"chunk_size": 2000, "chunk_overlap": 200}
    )

    chunks = splitter.split_text(text)

    logger.info(
        "Text chunking completed",
        extra={
            "chunk_count": len(chunks),
            "avg_chunk_size": sum(len(c) for c in chunks) // len(chunks) if chunks else 0,
            "total_chunks_length": sum(len(c) for c in chunks)
        }
    )

    for idx, chunk in enumerate(chunks):
        logger.debug(
            "Chunk created",
            extra={"chunk_index": idx, "chunk_length": len(chunk)}
        )

    return chunks
import asyncio
import base64

from langchain.messages import HumanMessage
from utils.logger import get_logger
from utils.image_handler import encode_image_for_claude

logger = get_logger(__name__)


async def summarize_chunks(
    chunks,
    llm,
    image_docs=None,
    use_base64=False,
    base64_collector=None,
    file_docs=None
):

    if image_docs is None:
        image_docs = []

    if file_docs is None:
        file_docs = []

    logger.info(
        "Starting content summarization",
        extra={"text_chunks": len(chunks), "images": len(image_docs)}
    )

    summaries = []

    if use_base64 and file_docs:

        logger.info(
            "Base64 attachment mode enabled",
            extra={"file_docs": len(file_docs)}
        )

        file_summaries = await _summarize_file_documents(
            file_docs,
            llm,
            base64_collector
        )
        summaries.extend(file_summaries)

    else:

        for idx, chunk in enumerate(chunks):

            logger.debug(
                "Preparing text chunk for summarization",
                extra={"chunk_index": idx, "chunk_length": len(chunk)}
            )

            message = _build_text_chunk_message(
                chunk,
                idx,
                use_base64,
                base64_collector
            )

            logger.debug(
                "Invoking LLM for text chunk",
                extra={
                    "chunk_index": idx,
                    "use_base64": use_base64,
                    "chunk_length": len(chunk)
                }
            )

            response = await llm.ainvoke([message])
            text_summary = _coerce_response_text(response)
            summaries.append(text_summary)

    for idx, image_doc in enumerate(image_docs):

        logger.debug(
            "Preparing image for vision analysis",
            extra={"image_index": idx, "file_name": image_doc.filename}
        )

        message = _build_image_message(image_doc)

        response = await llm.ainvoke([message])
        text_summary = _coerce_response_text(response)
        summaries.append(text_summary)

    logger.info(
        "Content summarization completed",
        extra={
            "response_count": len(summaries),
            "total_summary_length": sum(len(summary) for summary in summaries)
        }
    )

    for idx, summary in enumerate(summaries):
        source_type = "text" if idx < len(chunks) else "image"
        logger.debug(
            "Summary generated",
            extra={"index": idx, "source_type": source_type, "summary_length": len(summary)}
        )

    return summaries


def _coerce_response_text(response) -> str:

    content = getattr(response, "content", "")

    if isinstance(content, str):
        return content

    blocks = []

    if isinstance(content, list):
        for block in content:
            text = _extract_text_from_block(block)
            if text:
                blocks.append(text)
    else:
        text = _extract_text_from_block(content)
        if text:
            blocks.append(text)

    if not blocks:
        return str(content)

    return "\n".join(blocks)


def _extract_text_from_block(block) -> str:

    if not block:
        return ""

    if isinstance(block, str):
        return block

    if isinstance(block, dict):
        if block.get("type") == "text" and block.get("text"):
            return block["text"]
        return block.get("text", "")

    text_attr = getattr(block, "text", None)
    if isinstance(text_attr, str):
        return text_attr

    return ""


def _build_text_chunk_message(chunk: str, idx: int, use_base64: bool, base64_collector):

    chunk = chunk or ""

    if use_base64:
        encoded_chunk = base64.standard_b64encode(chunk.encode("utf-8")).decode("ascii") if chunk else ""
        if base64_collector is not None:
            base64_collector.append(
                {
                    "index": idx,
                    "encoded": encoded_chunk,
                    "original_length": len(chunk)
                }
            )
        return HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "The following string is a base64-encoded UTF-8 document chunk. "
                        "Decode it and produce a detailed summary with key facts, tables, and figures preserved."
                    )
                },
                {
                    "type": "text",
                    "text": encoded_chunk
                }
            ]
        )

    return HumanMessage(
        content=[
            {
                "type": "text",
                "text": f"Summarize this document chunk:\n\n{chunk}"
            }
        ]
    )


async def _summarize_file_documents(file_docs, llm, base64_collector):

    summaries = []

    for idx, doc in enumerate(file_docs):

        if not doc.source_path:
            logger.warning(
                "File document missing source path; skipping base64 attachment",
                extra={"file_name": doc.filename}
            )
            continue

        message, encoded_payload = await _build_file_message(doc)

        if message is None:
            continue

        logger.debug(
            "Invoking LLM for uploaded file",
            extra={"file_name": doc.filename, "source_path": doc.source_path}
        )

        response = await llm.ainvoke([message])
        text_summary = _coerce_response_text(response)
        summaries.append(text_summary)

        if base64_collector is not None and encoded_payload is not None:
            base64_collector.append(
                {
                    "index": idx,
                    "file_name": doc.filename,
                    "encoded": encoded_payload,
                    "source_path": doc.source_path,
                    "mime_type": doc.source_media_type or "application/octet-stream"
                }
            )

    return summaries


async def _build_file_message(doc):

    try:
        encoded_file = await asyncio.to_thread(_encode_file_from_path, doc.source_path)
    except FileNotFoundError:
        logger.error(
            "Uploaded file missing on disk; skipping",
            extra={"file_name": doc.filename, "source_path": doc.source_path}
        )
        return None, None
    except Exception:
        logger.exception(
            "Failed to encode uploaded file",
            extra={"file_name": doc.filename, "source_path": doc.source_path}
        )
        return None, None

    media_type = (doc.source_media_type or "application/octet-stream").lower()

    if media_type == "application/pdf":
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "Summarize the attached document. Extract key facts, amounts, and tables in detail."
                    )
                },
                {
                    "type": "file",
                    "mime_type": media_type,
                    "base64": encoded_file
                }
            ]
        )
        return message, encoded_file

    if media_type.startswith("image/"):
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "Extract all text and data from this image. If it's a tax document, extract all box numbers, labels, and values exactly as shown."
                    )
                },
                {
                    "type": "image",
                    "base64": encoded_file,
                    "mime_type": media_type
                }
            ]
        )
        return message, encoded_file

    text_content = (getattr(doc, "text_content", None) or "").strip()
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Summarize this document. Extract key facts, amounts, and tables in detail.\n\n"
                    f"{text_content}"
                )
            }
        ]
    )

    return message, encoded_file


def _encode_file_from_path(path: str) -> str:

    with open(path, "rb") as source:
        return base64.standard_b64encode(source.read()).decode("ascii")


def _build_image_message(image_doc):

    encoded_image, media_type = encode_image_for_claude(
        image_doc.image_data,
        image_doc.filename,
        image_doc.image_media_type
    )

    return HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Extract all text and data from this image. If it's a tax document, extract all box numbers, labels, and values exactly as shown."
                )
            },
            {
                "type": "image",
                "base64": encoded_image,
                "mime_type": media_type
            }
        ]
    )
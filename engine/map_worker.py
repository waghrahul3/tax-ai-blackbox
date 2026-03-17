import base64
from utils.logger import get_logger
from utils.image_handler import encode_image_for_claude

logger = get_logger(__name__)


async def summarize_chunks(chunks, llm, image_docs=None, use_base64=False, base64_collector=None):

    if image_docs is None:
        image_docs = []

    logger.info(
        "Starting content summarization",
        extra={"text_chunks": len(chunks), "images": len(image_docs)}
    )

    summaries = []

    for idx, chunk in enumerate(chunks):

        logger.debug(
            "Preparing text chunk for summarization",
            extra={"chunk_index": idx, "chunk_length": len(chunk)}
        )

        if use_base64:
            encoded_chunk = base64.standard_b64encode(chunk.encode("utf-8")).decode("ascii") if chunk else ""
            prompt = (
                "The following document chunk is provided as base64-encoded UTF-8 text. "
                "Decode it and produce a detailed summary with key facts, tables, and figures preserved.\n\n"
                f"Base64 chunk:\n{encoded_chunk}"
            )
            if base64_collector is not None:
                base64_collector.append(
                    {
                        "index": idx,
                        "encoded": encoded_chunk,
                        "original_length": len(chunk)
                    }
                )
        else:
            prompt = f"""
            Summarize this document chunk:

            {chunk}
            """

        logger.debug(
            "Invoking LLM for text chunk",
            extra={
                "chunk_index": idx,
                "use_base64": use_base64,
                "chunk_length": len(chunk)
            }
        )

        response = await llm.ainvoke(prompt)
        text_summary = _coerce_response_text(response)
        summaries.append(text_summary)

    for idx, image_doc in enumerate(image_docs):

        logger.debug(
            "Preparing image for vision analysis",
            extra={"image_index": idx, "file_name": image_doc.filename}
        )

        encoded_image, media_type = encode_image_for_claude(
            image_doc.image_data,
            image_doc.filename,
            image_doc.image_media_type
        )

        vision_message = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract all text and data from this image. If it's a tax document, extract all box numbers, labels, and values exactly as shown."
                    }
                ]
            }
        ]

        response = await llm.ainvoke(vision_message)
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
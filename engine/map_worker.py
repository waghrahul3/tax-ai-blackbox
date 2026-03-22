import asyncio
import base64

from utils.logger import get_logger
from utils.image_handler import encode_image_for_claude
from core.config import ENABLE_LLM_MAP_SUMMARIZATION, ANTHROPIC_MODEL

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
        extra={
            "text_chunks": len(chunks), 
            "images": len(image_docs),
            "llm_map_summarization_enabled": ENABLE_LLM_MAP_SUMMARIZATION
        }
    )

    summaries = []

    if ENABLE_LLM_MAP_SUMMARIZATION:
        logger.info("LLM map summarization is enabled - processing with AI")
        
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

                message_content = _build_text_chunk_message(
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

                response = await llm.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=64000,
                    messages=[{"role": "user", "content": message_content}],
                    stream=True
                )
                
                # Collect streamed response
                text_summary = ""
                async for chunk in response:
                    if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                        text_summary += chunk.delta.text
                    elif chunk.type == "content_block_stop":
                        break
                summaries.append(text_summary)

        for idx, image_doc in enumerate(image_docs):

            logger.debug(
                "Preparing image for vision analysis",
                extra={"image_index": idx, "file_name": image_doc.filename}
            )

            message_content = _build_image_message(image_doc)

            response = await llm.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=64000,
                messages=[{"role": "user", "content": message_content}],
                stream=True
            )
            
            # Collect streamed response
            text_summary = ""
            async for chunk in response:
                if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                    text_summary += chunk.delta.text
                elif chunk.type == "content_block_stop":
                    break
            summaries.append(text_summary)

    else:
        logger.info("LLM map summarization is disabled - using raw data")
        
        # Use raw chunks directly without LLM processing
        summaries.extend(chunks)
        
        # Add raw image content if available
        for idx, image_doc in enumerate(image_docs):
            if hasattr(image_doc, 'text_content') and image_doc.text_content:
                summaries.append(image_doc.text_content)
            else:
                # If no extracted text, add a placeholder
                summaries.append(f"[Image: {image_doc.filename}]")
            
            # Populate base64 collector for images if enabled
            if base64_collector is not None and hasattr(image_doc, 'source_path') and image_doc.source_path:
                try:
                    import base64
                    with open(image_doc.source_path, 'rb') as f:
                        image_content = f.read()
                        base64_content = base64.b64encode(image_content).decode('utf-8')
                        
                        # Determine media type
                        media_type = getattr(image_doc, 'source_media_type', 'image/jpeg')
                        
                        # Add to base64 collector
                        base64_collector.append({
                            "type": "image",
                            "media_type": media_type,
                            "filename": image_doc.filename,
                            "content": base64_content
                        })
                        
                        logger.debug(
                            "Added image to base64 collector in raw mode",
                            extra={
                                "filename": image_doc.filename,
                                "media_type": media_type,
                                "content_length": len(base64_content)
                            }
                        )
                except Exception as e:
                    logger.error(
                        "Failed to add image to base64 collector in raw mode",
                        extra={"filename": image_doc.filename, "error": str(e)}
                    )
        
        # Handle file docs in raw mode - still populate base64 collector if enabled
        if use_base64 and file_docs:
            logger.info(
                "Processing file docs in raw mode with base64 collection",
                extra={"file_docs": len(file_docs)}
            )
            
            for idx, file_doc in enumerate(file_docs):
                # Add text content to summaries
                if hasattr(file_doc, 'text_content') and file_doc.text_content:
                    summaries.append(file_doc.text_content)
                else:
                    summaries.append(f"[Document: {file_doc.filename}]")
                
                # Populate base64 collector for file attachments
                if base64_collector is not None:
                    try:
                        import base64
                        with open(file_doc.source_path, 'rb') as f:
                            file_content = f.read()
                            base64_content = base64.b64encode(file_content).decode('utf-8')
                            
                            media_type = getattr(file_doc, 'source_media_type', 'application/octet-stream')
                            
                            base64_collector.append({
                                "type": "file",
                                "media_type": media_type,
                                "filename": file_doc.filename,
                                "content": base64_content
                            })
                            
                            logger.debug(
                                "Added file to base64 collector in raw mode",
                                extra={
                                    "filename": file_doc.filename,
                                    "media_type": media_type,
                                    "content_length": len(base64_content)
                                }
                            )
                    except Exception as e:
                        logger.error(
                            "Failed to add file to base64 collector in raw mode",
                            extra={"filename": file_doc.filename, "error": str(e)}
                        )

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
        return [
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

    return [
        {
            "type": "text",
            "text": f"Summarize this document chunk:\n\n{chunk}"
        }
    ]


async def _summarize_file_documents(file_docs, llm, base64_collector):

    summaries = []
    
    logger.info(
        "Processing file documents",
        extra={
            "file_docs": len(file_docs),
            "llm_map_summarization_enabled": ENABLE_LLM_MAP_SUMMARIZATION
        }
    )

    for idx, doc in enumerate(file_docs):

        if not doc.source_path:
            logger.warning(
                "File document missing source path; skipping base64 attachment",
                extra={"file_name": doc.filename}
            )
            continue

        if ENABLE_LLM_MAP_SUMMARIZATION:
            # LLM-enabled path
            message_content, encoded_payload = await _build_file_message(doc)

            if message_content is None:
                continue

            logger.debug(
                "Invoking LLM for uploaded file",
                extra={"file_name": doc.filename, "source_path": doc.source_path}
            )

            response = await llm.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=64000,
                messages=[{"role": "user", "content": message_content}],
                stream=True
            )
            
            # Collect streamed response
            text_summary = ""
            async for chunk in response:
                if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                    text_summary += chunk.delta.text
                elif chunk.type == "content_block_stop":
                    break
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
        else:
            # Raw mode - no LLM calls
            logger.debug(
                "Processing file in raw mode without LLM",
                extra={"file_name": doc.filename, "source_path": doc.source_path}
            )
            
            # Add extracted text if available
            if hasattr(doc, 'text_content') and doc.text_content:
                summaries.append(doc.text_content)
            else:
                summaries.append(f"[Document: {doc.filename}]")
            
            # Still populate base64 collector for file attachments
            if base64_collector is not None:
                try:
                    import base64
                    with open(doc.source_path, 'rb') as f:
                        file_content = f.read()
                        base64_content = base64.b64encode(file_content).decode('utf-8')
                        
                        base64_collector.append({
                            "type": "file",
                            "media_type": doc.source_media_type or "application/octet-stream",
                            "filename": doc.filename,
                            "content": base64_content
                        })
                        
                        logger.debug(
                            "Added file to base64 collector in raw mode",
                            extra={
                                "filename": doc.filename,
                                "media_type": doc.source_media_type,
                                "content_length": len(base64_content)
                            }
                        )
                except Exception as e:
                    logger.error(
                        "Failed to add file to base64 collector in raw mode",
                        extra={"filename": doc.filename, "error": str(e)}
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
        content = [
            {
                "type": "text",
                "text": (
                    "Summarize the attached document. Extract key facts, amounts, and tables in detail."
                )
            },
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": encoded_file
                }
            }
        ]
        return content, encoded_file

    if media_type.startswith("image/"):
        content = [
            {
                "type": "text",
                "text": (
                    "Extract all text and data from this image. If it's a tax document, extract all box numbers, labels, and values exactly as shown."
                )
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": encoded_file
                }
            }
        ]
        return content, encoded_file

    text_content = (getattr(doc, "text_content", None) or "").strip()
    content = [
        {
            "type": "text",
            "text": (
                "Summarize this document. Extract key facts, amounts, and tables in detail.\n\n"
                f"{text_content}"
            )
        }
    ]

    return content, encoded_file


def _encode_file_from_path(path: str) -> str:

    with open(path, "rb") as source:
        return base64.standard_b64encode(source.read()).decode("ascii")


def _build_image_message(image_doc):

    encoded_image, media_type = encode_image_for_claude(
        image_doc.image_data,
        image_doc.filename,
        image_doc.image_media_type
    )

    return [
        {
            "type": "text",
            "text": (
                "Extract all text and data from this image. If it's a tax document, extract all box numbers, labels, and values exactly as shown."
            )
        },
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": encoded_image
            }
        }
    ]
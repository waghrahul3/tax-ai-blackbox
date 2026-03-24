import asyncio
import base64
import os

from utils.logger import get_logger
from core.config import ENABLE_LLM_MAP_SUMMARIZATION, ANTHROPIC_MODEL, MAX_TOKENS, ENABLE_PDF_BETA
from services.pdf_processing_service import get_pdf_service

logger = get_logger(__name__)


def _has_pdf_documents(file_docs: list = None, image_docs: list = None) -> bool:
    """Check if any documents are PDFs to determine if beta headers are needed."""
    if file_docs:
        for doc in file_docs:
            if hasattr(doc, 'source_media_type') and doc.source_media_type == 'application/pdf':
                return True
    if image_docs:
        for doc in image_docs:
            if hasattr(doc, 'source_media_type') and doc.source_media_type == 'application/pdf':
                return True
    return False


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

    # Check if PDF processing is needed for beta headers
    has_pdfs = _has_pdf_documents(file_docs, image_docs)
    
    # Define llm_with_beta at function level to ensure it's available everywhere
    llm_with_beta = llm
    if has_pdfs and ENABLE_PDF_BETA:
        from core.llm_factory import get_llm
        llm_with_beta = get_llm(include_beta_headers=True)

    logger.info(
        "Starting content summarization",
        extra={
            "text_chunks": len(chunks), 
            "images": len(image_docs),
            "llm_map_summarization_enabled": ENABLE_LLM_MAP_SUMMARIZATION,
            "has_pdf_documents": has_pdfs,
            "pdf_beta_enabled": ENABLE_PDF_BETA
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
                base64_collector,
                has_pdfs
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

                # Use appropriate client based on PDF detection
                active_llm = llm_with_beta if has_pdfs and ENABLE_PDF_BETA else llm
                
                response = await active_llm.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=MAX_TOKENS,
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
                logger.debug(
                    "Processing image in raw mode",
                    extra={"image_index": idx, "file_name": image_doc.filename, "processing_path": "raw_mode"}
                )
                try:
                    import base64
                    # ✅ Use already compressed image_data from document, don't re-read file
                    image_content = image_doc.image_data
                    media_type = getattr(image_doc, 'source_media_type', 'image/jpeg')
                    
                    # ✅ Only compress if image_data is still oversized (wasn't compressed in document loader)
                    if len(image_content) > 4_500_000:
                        logger.warning(
                            "Image still exceeds safe size limit; compressing before sending",
                            extra={"filename": image_doc.filename, "original_size": len(image_content)}
                        )
                        from utils.image_handler import compress_image_to_limit
                        try:
                            image_content, media_type = compress_image_to_limit(image_content)
                            logger.info(
                                "Image compressed",
                                extra={"filename": image_doc.filename, "compressed_size": len(image_content)}
                            )
                        except Exception as compress_error:
                            logger.error(
                                "Image compression failed, using original image",
                                extra={
                                    "filename": image_doc.filename, 
                                    "original_size": len(image_content),
                                    "error": str(compress_error)
                                }
                            )
                            # Fall back to original image_data without compression
                            media_type = getattr(image_doc, 'source_media_type', 'image/jpeg')
                    else:
                        media_type = getattr(image_doc, 'source_media_type', 'image/jpeg')
                        logger.debug(
                            "Image does not need compression",
                            extra={
                                "filename": image_doc.filename,
                                "image_size": len(image_content),
                                "compression_threshold": 4_500_000
                            }
                        )
                    
                    # ✅ Always encode and append, regardless of compression path
                    base64_content = base64.b64encode(image_content).decode('utf-8')
                    
                    # ✅ Check final base64 size before adding to collector
                    if len(base64_content) > 5_242_880:  # 5MB API limit
                        logger.error(
                            "Skipping oversized image from base64 collector",
                            extra={
                                "filename": image_doc.filename,
                                "base64_size": len(base64_content),
                                "limit": 5_242_880,
                                "size_mb": f"{len(base64_content) / 1024 / 1024:.2f}MB"
                            }
                        )
                        # Skip adding this oversized image to base64_collector
                        continue
                    
                    # Add to base64 collector - ✅ FIXED: Moved outside if/else to run regardless of compression
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
                            
                            # Determine media type
                            media_type = getattr(file_doc, 'source_media_type', None)
                            if not media_type:
                                # Fallback detection based on filename
                                filename_lower = file_doc.filename.lower()
                                if filename_lower.endswith('.pdf'):
                                    media_type = "application/pdf"
                                else:
                                    media_type = "application/octet-stream"
                            
                            base64_content = base64.b64encode(file_content).decode('utf-8')
                            
                            # ✅ Check final base64 size before adding to collector
                            if len(base64_content) > 5_242_880:  # 5MB API limit
                                logger.error(
                                    "Skipping oversized file from base64 collector",
                                    extra={
                                        "filename": file_doc.filename,
                                        "media_type": media_type,
                                        "base64_size": len(base64_content),
                                        "limit": 5_242_880,
                                        "size_mb": f"{len(base64_content) / 1024 / 1024:.2f}MB"
                                    }
                                )
                                # Skip adding this oversized file to base64_collector
                                continue
                            
                            base64_collector.append({
                                "type": "document",  # ✅ STANDARDIZED: Always use "document" for PDFs
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


def _build_text_chunk_message(chunk: str, idx: int, use_base64: bool, base64_collector: list) -> list:

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


async def _summarize_file_documents(file_docs, llm, base64_collector, has_pdfs=False):

    summaries = []
    
    # Create beta-enabled client if needed
    llm_with_beta = llm
    if has_pdfs and ENABLE_PDF_BETA:
        from core.llm_factory import get_llm
        llm_with_beta = get_llm(include_beta_headers=True)
    
    logger.info(
        "Processing file documents",
        extra={
            "file_docs": len(file_docs),
            "llm_map_summarization_enabled": ENABLE_LLM_MAP_SUMMARIZATION,
            "has_pdf_documents": has_pdfs,
            "pdf_beta_enabled": ENABLE_PDF_BETA
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

            # Use appropriate client based on PDF detection
            active_llm = llm_with_beta if has_pdfs and ENABLE_PDF_BETA else llm
            
            response = await active_llm.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=MAX_TOKENS,
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
                # Determine media type with proper PDF detection
                media_type = getattr(doc, 'source_media_type', None)
                if not media_type:
                    # Fallback detection based on filename
                    filename_lower = doc.filename.lower()
                    if filename_lower.endswith('.pdf'):
                        media_type = "application/pdf"
                    else:
                        media_type = "application/octet-stream"
                
                base64_collector.append(
                    {
                        "index": idx,
                        "file_name": doc.filename,
                        "encoded": encoded_payload,
                        "source_path": doc.source_path,
                        "media_type": media_type
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
                        
                        # Determine media type with proper PDF detection
                        media_type = getattr(doc, 'source_media_type', None)
                        if not media_type:
                            # Fallback detection based on filename
                            filename_lower = doc.filename.lower()
                            if filename_lower.endswith('.pdf'):
                                media_type = "application/pdf"
                            else:
                                media_type = "application/octet-stream"
                        
                        base64_content = base64.b64encode(file_content).decode('utf-8')
                        
                        base64_collector.append({
                            "type": "document",  # ✅ STANDARDIZED: Always use "document" for PDFs
                            "media_type": media_type,
                            "filename": doc.filename,
                            "content": base64_content
                        })
                        
                        logger.debug(
                            "Added file to base64 collector in raw mode",
                            extra={
                                "filename": doc.filename,
                                "media_type": media_type,
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

    # Determine media type with proper PDF detection
    media_type = getattr(doc, 'source_media_type', None)
    if not media_type:
        # Fallback detection based on filename
        filename_lower = doc.filename.lower()
        if filename_lower.endswith('.pdf'):
            media_type = "application/pdf"
        else:
            media_type = "application/octet-stream"
    else:
        media_type = media_type.lower()

    # Check if this PDF was processed with a password
    is_password_processed_pdf = (
        media_type == "application/pdf" and 
        getattr(doc, 'password_processed', False)
    )

    if is_password_processed_pdf:
        # Use PDF processing service to determine how to handle the file
        pdf_service = get_pdf_service()
        decrypted_path = getattr(doc, 'source_path', None)
        text_content = (getattr(doc, "text_content", None) or "").strip()
        
        # Check if we have a decrypted copy
        if decrypted_path and pdf_service.is_decrypted_file(decrypted_path) and os.path.exists(decrypted_path):
            logger.info(
                "Sending decrypted PDF copy to LLM",
                extra={"file_name": doc.filename, "decrypted_path": decrypted_path}
            )
            
            # Send the decrypted copy as a normal PDF document
            try:
                encoded_decrypted_file = await asyncio.to_thread(_encode_file_from_path, decrypted_path)
                content = [
                    {
                        "type": "text",
                        "text": (
                            "This document was password-protected and has been decrypted for processing. "
                            "Summarize the attached document. Extract key facts, amounts, and tables in detail."
                        )
                    },
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded_decrypted_file
                        }
                    }
                ]
                return content, encoded_decrypted_file
            except Exception as e:
                logger.warning(
                    "Failed to encode decrypted PDF, falling back to text",
                    extra={"file_name": doc.filename, "error": str(e)}
                )
                # Fall back to text-only mode
        
        # If no decrypted copy available or failed to use it, send extracted text only
        if not text_content:
            logger.warning(
                "Password-protected PDF has no extracted text to send",
                extra={"file_name": doc.filename}
            )
            return None, None
        
        logger.info(
            "Sending extracted text for password-protected PDF",
            extra={"file_name": doc.filename, "text_length": len(text_content)}
        )
        
        content = [
            {
                "type": "text",
                "text": (
                    "This document was password-protected and has been processed locally. "
                    "Summarize the extracted text content below:\n\n"
                    f"{text_content}"
                )
            }
        ]
        return content, None  # No encoded file for text-only mode

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
        return base64.standard_b64encode(source.read()).decode('ascii')

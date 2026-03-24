"""
reduce.py — Anthropic-native reduce phase (Python 3.12+)

Replaces LangChain usage with the official `anthropic` async client.
All original logic, flags, and logging are preserved exactly.
"""

import anthropic

from core.prompt_templates import get_prompt_template
from core.config import (
    ENABLE_LLM_SUMMARIZATION,
    ENABLE_BASE64_INPUT,
    ANTHROPIC_MODEL,
    MAX_TOKENS,
    ENABLE_PDF_BETA
)
from utils.logger import get_logger
from utils.file_manifest import build_file_manifest
from utils.file_registry import detect_file_info, FileRole

logger = get_logger(__name__)


def _has_pdf_attachments(base64_collector: list[dict] | None) -> bool:
    """Check if any attachments in base64_collector are PDFs."""
    if not base64_collector:
        return False
    
    for file_data in base64_collector:
        media_type = file_data.get("media_type") or file_data.get("mime_type", "")
        if media_type == "application/pdf":
            return True
    return False


async def reduce_summaries(
    summaries: list[str],
    llm: anthropic.AsyncAnthropic,          # pass an AsyncAnthropic client instance
    user_instruction: str | None,
    template_name: str | None = None,
    base64_collector: list[dict] | None = None,
    system_prompt: str | None = None,
) -> str:
    """
    Reduce/aggregate map-stage summaries into a final answer using the
    Anthropic Messages API.

    Parameters
    ----------
    summaries        : List of per-chunk summaries produced by the map stage.
    llm              : An instantiated ``anthropic.AsyncAnthropic`` client.
    user_instruction : Free-text instruction from the end user (may be None/blank).
    template_name    : Optional prompt-template name resolved via get_prompt_template().
    base64_collector : Optional list of dicts with keys  
                       ``{"type": "file"|"image", "media_type": str, "content": str}``.
    system_prompt    : Optional system prompt override (takes priority over
                       user_instruction for the system turn).

    Returns
    -------
    The model's text response as a plain string.
    """
    
    # Debug logging for base64_collector
    collector_count = len(base64_collector) if base64_collector else 0
    logger.debug(
        "Reduce worker started",
        extra={"base64_collector_count": collector_count}
    )
    if base64_collector:
        for i, item in enumerate(base64_collector):
            logger.debug(f"Collector entry {i}", extra={
                "type": item.get("type"),
                "filename": item.get("filename") or item.get("file_name"),
                "media_type": item.get("media_type"),
            })
    
    # Check if PDF processing is needed for beta headers
    has_pdfs = _has_pdf_attachments(base64_collector)

    logger.info(
        "Starting reduce phase",
        extra={
            "summary_count": len(summaries),
            "template_name": template_name,
            "has_user_prompt": bool(user_instruction),
            "user_prompt_length": len(user_instruction) if user_instruction else 0,
            "user_prompt_preview": (
                (user_instruction[:100] + "...")
                if user_instruction and len(user_instruction) > 100
                else user_instruction
            ),
            "has_system_prompt": system_prompt is not None,
            "system_prompt_length": len(system_prompt) if system_prompt else 0,
            "system_prompt_preview": (
                (system_prompt[:100] + "...")
                if system_prompt and len(system_prompt) > 100
                else system_prompt
            ),
            "llm_summarization_enabled": ENABLE_LLM_SUMMARIZATION,
            "base64_collector_count": len(base64_collector) if base64_collector else 0,
            "has_pdf_attachments": has_pdfs,
            "pdf_beta_enabled": ENABLE_PDF_BETA,
        },
    )

    combined = "\n".join(summaries)

    logger.debug("Combined summaries", extra={"combined_length": len(combined)})

    # ── Resolve the system prompt and user content based on logic ────────
    resolved_system: str = ""
    user_content_text: str = ""

    if system_prompt:
        # system_prompt has value → system gets system_prompt,
        # user gets user_instruction
        resolved_system = system_prompt
        if user_instruction:
            user_content_text = f"User instruction:\n{user_instruction}"
        logger.info(
            "Using system_prompt for system role and user_instruction for user role",
            extra={
                "system_prompt_length": len(resolved_system),
                "user_instruction_length": (
                    len(user_instruction) if user_instruction else 0
                ),
            }
        )
    else:
        # system_prompt is empty → system gets user_instruction, user content is minimal
        if user_instruction:
            resolved_system = user_instruction
            logger.info(
                "Using user_instruction for system role (system_prompt is empty)",
                extra={
                    "system_prompt_length": len(resolved_system),
                    "user_instruction_moved_to_system": True,
                }
            )
        else:
            logger.info(
                "No system_prompt or user_instruction provided",
                extra={"using_defaults": True}
            )

    # Add document summaries to user content if not in base64 mode
    if not ENABLE_BASE64_INPUT and combined:
        if user_content_text:
            user_content_text += f"\n\nDocument summaries:\n{combined}"
        else:
            user_content_text = f"Document summaries:\n{combined}"

    # Add file context to system prompt dynamically if we have attachments
    if base64_collector:
        counts = {"pdf": 0, "image": 0, "other": 0}
        roles  = {"reference": [], "source": [], "unknown": []}

        for idx, f in enumerate(base64_collector, 1):
            fname = f.get("filename") or f.get("file_name", "")
            mtype = f.get("media_type", "")
            info  = detect_file_info(fname, mtype, idx)

            if mtype == "application/pdf":
                counts["pdf"] += 1
            elif mtype.startswith("image/"):
                counts["image"] += 1
            else:
                counts["other"] += 1

            if info.role == FileRole.REFERENCE:
                roles["reference"].append(fname)
            elif info.role == FileRole.SOURCE:
                roles["source"].append(fname)
            else:
                roles["unknown"].append(fname)

        context_lines = [
            f"\nYou will receive {counts['pdf']} PDF(s) and {counts['image']} image(s)."
        ]
        if roles["reference"]:
            context_lines.append(
                f"Reference document(s): {', '.join(roles['reference'])}."
            )
        if roles["source"]:
            context_lines.append(
                f"Source document(s) to verify: {', '.join(roles['source'])}."
            )
        if roles["unknown"]:
            context_lines.append(
                f"Unclassified file(s) — determine role from content: {', '.join(roles['unknown'])}."
            )

        resolved_system += "\n" + "\n".join(context_lines)

    # ------------------------------------------------------------------
    # LLM path
    # ------------------------------------------------------------------
    if ENABLE_LLM_SUMMARIZATION:
        logger.info("LLM reduction is enabled - processing with AI")

        # ── Build the human-turn content list ─────────────────────────
        # The Anthropic Messages API accepts `content` as either a plain
        # string or a list of typed content blocks.

        human_content: list[dict] = []

        # 1. Text block - use the new user_content_text logic
        if ENABLE_BASE64_INPUT:
            # In base64 mode, only include user_content_text (may be empty)
            text_body = user_content_text
            logger.info(
                "Base64 input mode enabled - sending user content with file attachments",
                extra={"text_content_length": len(text_body)},
            )
        else:
            # In non-base64 mode, user_content_text already includes summaries
            text_body = user_content_text
            logger.info(
                "Base64 input mode disabled - sending user content with summaries",
                extra={"text_content_length": len(text_body)},
            )

        # Only add text block if there's actual content and no attachments
        if text_body.strip() and not base64_collector:
            human_content.append({"type": "text", "text": text_body})
        elif not base64_collector:
            logger.info(
                "No text content for user message - no attachments to process",
                extra={"has_attachments": bool(base64_collector)}
            )

        # 2. Optional base64 attachments (documents / images)
        if base64_collector:
            logger.info(
                "Including base64 file attachments in final LLM call",
                extra={"file_count": len(base64_collector)}
            )
            
            # ✅ 1. File manifest — always first so Claude has context before reading files
            manifest = build_file_manifest(base64_collector)
            if manifest:
                human_content.append({"type": "text", "text": manifest})

            # ✅ 2. User instruction
            if text_body.strip():
                human_content.append({"type": "text", "text": text_body})

            # ✅ 3. File attachments with titles
            for file_data in base64_collector:
                content    = file_data.get("content") or file_data.get("encoded", "")
                media_type = file_data.get("media_type", "")
                filename   = file_data.get("filename") or file_data.get("file_name", "")

                if media_type == "application/pdf":
                    human_content.append({
                        "type": "document",
                        "title": filename,       # ✅ Claude sees filename
                        "source": {
                            "type":       "base64",
                            "media_type": "application/pdf",
                            "data":       content,
                        }
                    })

                elif media_type.startswith("image/"):
                    human_content.append({
                        "type": "image",
                        "source": {
                            "type":       "base64",
                            "media_type": media_type,
                            "data":       content,
                        }
                    })

                else:
                    logger.warning(
                        "Skipping unsupported file type",
                        extra={"filename": filename, "media_type": media_type}
                    )

        # ── Resolve max_tokens from template or use global ─────────────────────
        max_tokens_to_use = MAX_TOKENS
        if template_name:
            template_config = get_prompt_template(template_name)
            if hasattr(template_config.primary_step, 'max_tokens'):
                max_tokens_to_use = template_config.primary_step.max_tokens
                logger.info(
                    "Using template-defined max_tokens",
                    extra={"max_tokens": max_tokens_to_use, "template": template_name}
                )

        logger.debug(
            "Formatted messages for LLM",
            extra={
                "human_content_blocks": len(human_content),
                "has_attachments": bool(base64_collector),
                "system_prompt_length": len(resolved_system),
                "user_content_length": len(user_content_text),
            },
        )

        # ── Call the Anthropic Messages API ───────────────────────────
        logger.debug("Invoking Anthropic LLM for final reduction")

        # Create beta-enabled client if needed
        llm_with_beta = llm
        if has_pdfs and ENABLE_PDF_BETA:
            from core.llm_factory import get_llm
            llm_with_beta = get_llm(include_beta_headers=True)
            logger.info(
                "Adding PDF beta headers to reduce phase",
                extra={
                    "pdf_attachments_count": sum(
                        1 for f in base64_collector or [] 
                        if (f.get("media_type") or f.get("mime_type", "")) == "application/pdf"
                    )
                }
            )

        # Use appropriate client based on PDF detection
        active_llm = llm_with_beta if has_pdfs and ENABLE_PDF_BETA else llm

        create_kwargs: dict = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": max_tokens_to_use,
            "messages": [
                {
                    "role": "user",
                    # Use plain string when there is only one text block and no
                    # attachments — keeps token overhead minimal.
                    "content": (
                        human_content[0]["text"]
                        if len(human_content) == 1 and human_content[0].get("type") == "text"
                        else human_content
                    ),
                }
            ],
            "stream": True
        }

        if resolved_system:
            create_kwargs["system"] = resolved_system


        stream = await active_llm.messages.create(**create_kwargs)

        # Collect streamed response
        result_text: str = ""
        async for chunk in stream:
            if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                result_text += chunk.delta.text
            elif chunk.type == "content_block_stop":
                break

        logger.info(
            "Reduce phase completed",
            extra={"response_length": len(result_text)},
        )

        return result_text

    # ------------------------------------------------------------------
    # Non-LLM path — return raw combined summaries
    # ------------------------------------------------------------------
    else:
        logger.info("LLM reduction is disabled - returning raw data only")
        logger.info("Raw reduction completed", extra={"result_length": len(combined)})
        return combined
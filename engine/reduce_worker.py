"""
reduce.py — Anthropic-native reduce phase (Python 3.12+)

Replaces LangChain usage with the official `anthropic` async client.
All original logic, flags, and logging are preserved exactly.
"""

import anthropic

from core.prompt_templates import get_prompt_template
from core.config import ENABLE_LLM_SUMMARIZATION, ENABLE_BASE64_INPUT, ANTHROPIC_MODEL, MAX_TOKENS, ENABLE_PDF_BETA
from utils.logger import get_logger

logger = get_logger(__name__)


def _has_pdf_attachments(base64_collector):
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
            "llm_summarization_enabled": ENABLE_LLM_SUMMARIZATION,
            "base64_collector_count": len(base64_collector) if base64_collector else 0,
            "has_pdf_attachments": has_pdfs,
            "pdf_beta_enabled": ENABLE_PDF_BETA,
            "has_system_prompt": system_prompt is not None,
            "system_prompt_length": len(system_prompt) if system_prompt else 0,
            "system_prompt_preview": (
                (system_prompt[:100] + "...")
                if system_prompt and len(system_prompt) > 100
                else system_prompt
            ),
        },
    )

    combined = "\n".join(summaries)

    logger.debug("Combined summaries", extra={"combined_length": len(combined)})

    # ------------------------------------------------------------------
    # LLM path
    # ------------------------------------------------------------------
    if ENABLE_LLM_SUMMARIZATION:
        logger.info("LLM reduction is enabled - processing with AI")

        # ── Build the human-turn content list ─────────────────────────
        # The Anthropic Messages API accepts `content` as either a plain
        # string or a list of typed content blocks.

        human_content: list[dict] = []

        # 1. Text block
        if ENABLE_BASE64_INPUT:
            # Include both document summaries AND user instruction in base64 mode
            text_body = (
                f"{user_instruction or ''}"
            )
            logger.info(
                "Base64 input mode enabled - sending summaries with file attachments",
                extra={"text_content_length": len(text_body)},
            )
        else:
            text_body = (
                f"You are provided with aggregated document summaries generated "
                f"from the map stage.\n{combined}\n\nUser instruction:\n"
                f"{user_instruction or ''}"
            )
            logger.info(
                "Base64 input mode disabled - sending combined summaries with user instruction",
                extra={"text_content_length": len(text_body)},
            )

        human_content.append({"type": "text", "text": text_body})

        # 2. Optional base64 attachments (documents / images)
        if base64_collector:
            logger.info(
                "Including base64 file attachments in final LLM call",
                extra={"file_count": len(base64_collector)},
            )
            for file_data in base64_collector:
                # Handle different data structures from map_worker
                if file_data.get("type") == "file":
                    content = file_data.get("content") or file_data.get("encoded", "")
                    media_type = file_data.get("media_type") or file_data.get("mime_type", "application/octet-stream")
                    
                    human_content.append(
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": content,
                            },
                        }
                    )
                elif file_data.get("type") == "image":
                    content = file_data.get("content") or file_data.get("encoded", "")
                    media_type = file_data.get("media_type") or file_data.get("mime_type", "image/jpeg")
                    
                    human_content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": content,
                            },
                        }
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

        # ── Resolve the system prompt ──────────────────────────────────
        resolved_system: str = ""

        if template_name:
            template_config = get_prompt_template(template_name)
            logger.info(
                "Using prompt template",
                extra={
                    "template_name": template_config.name,
                    "step_name": template_config.primary_step.name,
                },
            )
            primary_step = template_config.primary_step
            if hasattr(primary_step, "prompt") and primary_step.prompt:
                prompt_obj = primary_step.prompt
                resolved_system = (
                    prompt_obj.template
                    if hasattr(prompt_obj, "template")
                    else str(prompt_obj)
                )
            else:
                resolved_system = (
                    system_prompt if system_prompt else (user_instruction or "")
                )
        else:
            logger.info("Using prompt-only reduce mode without template")
            resolved_system = (
                system_prompt if system_prompt else (user_instruction or "")
            )

        logger.debug(
            "Formatted messages for LLM",
            extra={
                "human_content_blocks": len(human_content),
                "has_attachments": bool(base64_collector),
                "system_prompt_length": len(resolved_system),
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
                extra={"pdf_attachments_count": sum(1 for f in base64_collector or [] if (f.get("media_type") or f.get("mime_type", "")) == "application/pdf")}
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
                        if len(human_content) == 1
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
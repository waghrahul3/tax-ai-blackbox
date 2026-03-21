from core.prompt_templates import get_prompt_template
from core.config import ENABLE_LLM_SUMMARIZATION, ENABLE_BASE64_INPUT
from langchain_core.prompts import ChatPromptTemplate
from utils.logger import get_logger

logger = get_logger(__name__)

PROMPT_ONLY_TEMPLATE = ChatPromptTemplate.from_messages([
    (
        "system",
        "{user_instruction}"  
    ),
    (
        "human",
        "You are provided with aggregated document summaries generated from the map stage.\n"
        "{summaries}\n\n"
        "User instruction (may be blank):\n"
    )
])


async def reduce_summaries(summaries, llm, user_instruction, template_name=None, base64_collector=None, system_prompt=None):

    logger.info(
        "Starting reduce phase",
        extra={
            "summary_count": len(summaries),
            "template_name": template_name,
            "has_user_prompt": bool(user_instruction),
            "user_prompt_length": len(user_instruction) if user_instruction else 0,
            "user_prompt_preview": (user_instruction[:100] + "...") if user_instruction and len(user_instruction) > 100 else user_instruction,
            "llm_summarization_enabled": ENABLE_LLM_SUMMARIZATION,
            "base64_collector_count": len(base64_collector) if base64_collector else 0,
            "has_system_prompt": system_prompt is not None,
            "system_prompt_length": len(system_prompt) if system_prompt else 0,
            "system_prompt_preview": (system_prompt[:100] + "...") if system_prompt and len(system_prompt) > 100 else system_prompt
        }
    )

    combined = "\n".join(summaries)

    logger.debug(
        "Combined summaries",
        extra={"combined_length": len(combined)}
    )

    if ENABLE_LLM_SUMMARIZATION:
        logger.info("LLM reduction is enabled - processing with AI")
        
        # Build message content with optional base64 attachments
        message_content = []
        
        # Add text content
        if ENABLE_BASE64_INPUT:
            # When base64 is enabled, only send user instruction with file attachments
            text_content = f"{user_instruction or ''}"
            logger.info(
                "Base64 input mode enabled - sending only user instruction with file attachments",
                extra={"text_content_length": len(text_content)}
            )
        else:
            # When base64 is disabled, include combined summaries
            text_content = f"You are provided with aggregated document summaries generated from the map stage.\n{combined}\n\nUser instruction:\n{user_instruction or ''}"
            logger.info(
                "Base64 input mode disabled - sending combined summaries with user instruction",
                extra={"text_content_length": len(text_content)}
            )
        
        # Create initial content object with text
        content_object = {
            "type": "text",
            "text": text_content
        }
        
        # Add base64 file attachments if available
        if base64_collector and len(base64_collector) > 0:
            logger.info(
                "Including base64 file attachments in final LLM call",
                extra={"file_count": len(base64_collector)}
            )
            
            # Add files as a list to content object
            content_object["file_attachments"] = []
            for file_data in base64_collector:
                if file_data.get("type") == "file":
                    content_object["file_attachments"].append({
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": file_data.get("media_type", "application/octet-stream"),
                            "data": file_data.get("content", "")
                        }
                    })
                elif file_data.get("type") == "image":
                    content_object["file_attachments"].append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": file_data.get("media_type", "image/jpeg"),
                            "data": file_data.get("content", "")
                        }
                    })
        
        # Convert content object to message content
        message_content = content_object
        
        if template_name:
            template_config = get_prompt_template(template_name)

            logger.info(
                "Using prompt template",
                extra={
                    "template_name": template_config.name,
                    "step_name": template_config.primary_step.name
                }
            )

            primary_step = template_config.primary_step
            
            # Create custom messages with base64 attachments
            if hasattr(primary_step, 'prompt') and primary_step.prompt:
                # Use template prompt but replace with our content
                messages = [
                    ("system", primary_step.prompt.template if hasattr(primary_step.prompt, 'template') else ""),
                    ("human", message_content)
                ]
            else:
                # Fallback to standard format
                system_msg = system_prompt if system_prompt else (user_instruction or "")
                messages = [
                    ("system", system_msg),
                    ("human", message_content)
                ]
        else:
            logger.info("Using prompt-only reduce mode without template")
            
            # Use system_prompt if provided, otherwise use user_instruction
            system_msg = system_prompt if system_prompt else (user_instruction or "")
            messages = [
                ("system", system_msg),
                ("human", message_content)
            ]

        logger.debug(
            "Formatted messages for LLM",
            extra={"message_count": len(messages), "has_attachments": bool(base64_collector)}
        )

        logger.debug("Invoking LLM for final reduction")

        # Convert messages to LangChain format
        from langchain_core.messages import HumanMessage, SystemMessage
        
        langchain_messages = []
        for role, content in messages:
            if role == "system":
                if isinstance(content, str):
                    langchain_messages.append(SystemMessage(content=content))
                else:
                    # Handle complex content with attachments
                    langchain_messages.append(SystemMessage(content=str(content)))
            elif role == "human":
                if isinstance(content, str):
                    langchain_messages.append(HumanMessage(content=content))
                else:
                    # Handle complex content with attachments
                    langchain_messages.append(HumanMessage(content=content))

        response = await llm.ainvoke(langchain_messages)

        logger.info(
            "Reduce phase completed",
            extra={"response_length": len(response.content)}
        )

        return response.content
    else:
        logger.info("LLM reduction is disabled - returning raw data only")
        
        # When LLM is disabled, return only the combined raw data
        # Ignore user instruction since no LLM processing is available
        result = combined
            
        logger.info(
            "Raw reduction completed",
            extra={"result_length": len(result)}
        )
        
        return result
from core.prompt_templates import get_prompt_template
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


async def reduce_summaries(summaries, llm, user_instruction, template_name=None):

    logger.info(
        "Starting reduce phase",
        extra={
            "summary_count": len(summaries),
            "template_name": template_name,
            "has_user_instruction": bool(user_instruction)
        }
    )

    combined = "\n".join(summaries)

    logger.debug(
        "Combined summaries",
        extra={"combined_length": len(combined)}
    )

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
        messages = primary_step.format_messages(
            summaries=combined,
            user_instruction=user_instruction
        )
    else:
        logger.info("Using prompt-only reduce mode without template")
        messages = PROMPT_ONLY_TEMPLATE.format_messages(
            summaries=combined,
            user_instruction=(user_instruction or "").strip()
        )

    logger.debug(
        "Formatted messages for LLM",
        extra={"message_count": len(messages)}
    )

    logger.debug("Invoking LLM for final reduction")

    response = await llm.ainvoke(messages)

    logger.info(
        "Reduce phase completed",
        extra={"response_length": len(response.content)}
    )

    return response.content
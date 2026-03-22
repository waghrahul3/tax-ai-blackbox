import anthropic
from core.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, ENABLE_PDF_BETA, ANTHROPIC_BETA_HEADERS
from utils.logger import get_logger

logger = get_logger(__name__)


def get_llm(temperature=0.0, include_beta_headers=False):

    logger.debug(
        "Creating Anthropic client instance",
        extra={
            "model": ANTHROPIC_MODEL, 
            "temperature": temperature,
            "include_beta_headers": include_beta_headers,
            "pdf_beta_enabled": ENABLE_PDF_BETA
        }
    )

    client_kwargs = {
        "api_key": ANTHROPIC_API_KEY
    }
    
    # Add beta headers if enabled and requested
    if include_beta_headers and ENABLE_PDF_BETA:
        client_kwargs["default_headers"] = {
            "anthropic-beta": ",".join(ANTHROPIC_BETA_HEADERS)
        }
        logger.info(
            "PDF beta headers enabled for Anthropic client",
            extra={"beta_headers": ANTHROPIC_BETA_HEADERS}
        )

    return anthropic.AsyncAnthropic(**client_kwargs)
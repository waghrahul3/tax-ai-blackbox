import anthropic
from core.config import ANTHROPIC_API_KEY
from core.config import ANTHROPIC_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)


def get_llm(temperature=0.0):

    logger.debug(
        "Creating Anthropic client instance",
        extra={"model": ANTHROPIC_MODEL, "temperature": temperature}
    )

    return anthropic.AsyncAnthropic(
        api_key=ANTHROPIC_API_KEY
    )
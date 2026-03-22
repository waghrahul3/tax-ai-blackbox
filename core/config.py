import os
from dotenv import load_dotenv

load_dotenv()


def _get_float_env(var_name: str, default: float) -> float:

    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_bool_env(var_name: str, default: bool) -> bool:

    value = os.getenv(var_name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "64000"))
DEFAULT_TEMPERATURE = _get_float_env("LLM_TEMPERATURE", 0.0)
APP_VERSION = os.getenv("APP_VERSION", "0.0.0")
ENABLE_PANDAS_CLEANING = _get_bool_env("ENABLE_PANDAS_CLEANING", False)
ENABLE_CHUNKING = _get_bool_env("ENABLE_CHUNKING", True)
ENABLE_BASE64_INPUT = _get_bool_env("ENABLE_BASE64_INPUT", False)
ENABLE_LLM_SUMMARIZATION = _get_bool_env("ENABLE_LLM_SUMMARIZATION", True)
ENABLE_LLM_MAP_SUMMARIZATION = _get_bool_env("ENABLE_LLM_MAP_SUMMARIZATION", True)
ENABLE_PDF_BETA = _get_bool_env("ENABLE_PDF_BETA", True)

STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")

# Anthropic beta headers for PDF support and other beta features
# Format: comma-separated list, e.g., "pdfs-2024-09-25,prompt-caching-2024-07-31"
ANTHROPIC_BETA_HEADERS = os.getenv("ANTHROPIC_BETA_HEADERS", "pdfs-2024-09-25").split(",") if os.getenv("ANTHROPIC_BETA_HEADERS") else ["pdfs-2024-09-25"]
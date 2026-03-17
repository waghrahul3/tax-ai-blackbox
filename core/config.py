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


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")
DEFAULT_TEMPERATURE = _get_float_env("LLM_TEMPERATURE", 0.0)

STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")
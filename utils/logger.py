import logging
import sys
from typing import Optional

_LOG_LEVEL = logging.DEBUG

logging.basicConfig(
    level=_LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


def get_logger(name: Optional[str] = None) -> logging.Logger:

    return logging.getLogger(name or "tax_ai_agent")

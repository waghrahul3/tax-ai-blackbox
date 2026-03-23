"""Utility for extracting passwords from filenames."""

import re
from typing import Optional, List
from config.pdf_config import get_pdf_config
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_password_from_filename(filename: str) -> Optional[str]:
    """
    Extract password from filename using configurable patterns.
    
    Args:
        filename: The filename to extract password from
        
    Returns:
        Extracted password or None if no pattern found
    """
    if not filename:
        return None
    
    # Get configuration
    config = get_pdf_config()
    
    if not config.enable_password_extraction:
        logger.debug("Password extraction is disabled")
        return None
    
    if not config.validate_password_patterns():
        logger.warning("Invalid password patterns in configuration")
        return None
    
    logger.debug(
        "Attempting password extraction",
        extra={
            "filename": filename,
            "patterns": config.password_patterns,
            "case_sensitive": config.case_sensitive_patterns
        }
    )
    
    # Remove extension first
    name_without_ext = filename
    if "." in filename:
        name_without_ext = filename.rsplit(".", 1)[0]
    
    # Try each pattern
    for pattern in config.password_patterns:
        password = _extract_with_pattern(name_without_ext, pattern, config.case_sensitive_patterns)
        if password:
            logger.info(
                "Password extracted from filename",
                extra={
                    "filename": filename,
                    "pattern": pattern,
                    "password_length": len(password)
                }
            )
            return password
    
    logger.debug(
        "No password pattern matched",
        extra={"filename": filename, "patterns": config.password_patterns}
    )
    return None


def _extract_with_pattern(text: str, pattern: str, case_sensitive: bool) -> Optional[str]:
    """
    Extract password using a specific pattern.
    
    Args:
        text: Text to search in
        pattern: Pattern to search for
        case_sensitive: Whether matching should be case sensitive
        
    Returns:
        Extracted password or None
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    
    # Create regex pattern: everything after pattern until end
    regex_pattern = re.escape(pattern) + r"(.+)$"
    match = re.search(regex_pattern, text, flags)
    
    if match:
        password = match.group(1).strip()
        if password:  # Ensure password is not empty
            return password
    
    return None


def get_supported_patterns() -> List[str]:
    """
    Get list of supported password patterns from configuration.
    
    Returns:
        List of supported patterns
    """
    config = get_pdf_config()
    return config.password_patterns.copy()


def is_password_extraction_enabled() -> bool:
    """
    Check if password extraction is enabled.
    
    Returns:
        True if enabled, False otherwise
    """
    config = get_pdf_config()
    return config.enable_password_extraction

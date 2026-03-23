"""Legacy configuration compatibility layer - redirects to new config system."""

import os
from dotenv import load_dotenv

load_dotenv()

# Import new configuration system
from config.config_manager import get_config_manager

# Initialize configuration manager
_config_manager = get_config_manager()

# Legacy compatibility - redirect to new config system
def _get_legacy_config():
    """Get configuration values for backward compatibility."""
    feature_flags = _config_manager.feature_flags()
    api_limits = _config_manager.api_limits()
    llm_config = _config_manager.llm_config()
    app_config = _config_manager.app_config()
    
    return {
        # LLM Configuration
        "ANTHROPIC_API_KEY": llm_config.get_api_key(),
        "ANTHROPIC_MODEL": llm_config.get_default_model(),
        "MAX_TOKENS": api_limits.get_limit("max_tokens"),
        "DEFAULT_TEMPERATURE": llm_config.get_default_temperature(),
        "ANTHROPIC_BETA_HEADERS": llm_config.get_beta_headers(),
        
        # App Configuration
        "APP_VERSION": app_config.get_app_version(),
        
        # Feature Flags
        "ENABLE_PANDAS_CLEANING": feature_flags.is_enabled("pandas_cleaning"),
        "ENABLE_CHUNKING": feature_flags.is_enabled("chunking"),
        "ENABLE_BASE64_INPUT": feature_flags.is_enabled("base64_input"),
        "ENABLE_LLM_SUMMARIZATION": feature_flags.is_enabled("llm_summarization"),
        "ENABLE_LLM_MAP_SUMMARIZATION": feature_flags.is_enabled("llm_map_summarization"),
        "ENABLE_PDF_BETA": feature_flags.is_enabled("pdf_beta"),
        
        # Storage Configuration
        "STORAGE_TYPE": os.getenv("STORAGE_TYPE", "local")
    }

# Get legacy configuration values
_legacy_config = _get_legacy_config()

# Export legacy variables for backward compatibility
ANTHROPIC_API_KEY = _legacy_config["ANTHROPIC_API_KEY"]
ANTHROPIC_MODEL = _legacy_config["ANTHROPIC_MODEL"]
MAX_TOKENS = _legacy_config["MAX_TOKENS"]
DEFAULT_TEMPERATURE = _legacy_config["DEFAULT_TEMPERATURE"]
APP_VERSION = _legacy_config["APP_VERSION"]
ENABLE_PANDAS_CLEANING = _legacy_config["ENABLE_PANDAS_CLEANING"]
ENABLE_CHUNKING = _legacy_config["ENABLE_CHUNKING"]
ENABLE_BASE64_INPUT = _legacy_config["ENABLE_BASE64_INPUT"]
ENABLE_LLM_SUMMARIZATION = _legacy_config["ENABLE_LLM_SUMMARIZATION"]
ENABLE_LLM_MAP_SUMMARIZATION = _legacy_config["ENABLE_LLM_MAP_SUMMARIZATION"]
ENABLE_PDF_BETA = _legacy_config["ENABLE_PDF_BETA"]
STORAGE_TYPE = _legacy_config["STORAGE_TYPE"]
ANTHROPIC_BETA_HEADERS = _legacy_config["ANTHROPIC_BETA_HEADERS"]

# Legacy helper functions for backward compatibility
def _get_float_env(var_name: str, default: float) -> float:
    """Legacy helper function - redirects to config manager."""
    if var_name == "LLM_TEMPERATURE":
        return _config_manager.llm_config().get_default_temperature()
    
    # Fallback to environment variable for unknown variables
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_bool_env(var_name: str, default: bool) -> bool:
    """Legacy helper function - redirects to config manager."""
    # Map legacy variable names to feature flag names
    flag_mapping = {
        "ENABLE_PANDAS_CLEANING": "pandas_cleaning",
        "ENABLE_CHUNKING": "chunking",
        "ENABLE_BASE64_INPUT": "base64_input",
        "ENABLE_LLM_SUMMARIZATION": "llm_summarization",
        "ENABLE_LLM_MAP_SUMMARIZATION": "llm_map_summarization",
        "ENABLE_PDF_BETA": "pdf_beta"
    }
    
    if var_name in flag_mapping:
        return _config_manager.is_feature_enabled(flag_mapping[var_name])
    
    # Fallback to environment variable for unknown variables
    value = os.getenv(var_name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default

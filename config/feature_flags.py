"""Feature flags configuration for enabling/disabling functionality."""

import os
from typing import Dict, Any
from utils.logger import get_logger
from exceptions.base_exceptions import ConfigurationException


class FeatureFlags:
    """Centralized feature flags management."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._flags = self._load_feature_flags()
    
    def _load_feature_flags(self) -> Dict[str, bool]:
        """Load feature flags from environment variables."""
        flags = {
            "pandas_cleaning": self._get_bool_flag("ENABLE_PANDAS_CLEANING", False),
            "chunking": self._get_bool_flag("ENABLE_CHUNKING", True),
            "base64_input": self._get_bool_flag("ENABLE_BASE64_INPUT", False),
            "llm_summarization": self._get_bool_flag("ENABLE_LLM_SUMMARIZATION", True),
            "llm_map_summarization": self._get_bool_flag("ENABLE_LLM_MAP_SUMMARIZATION", True),
            "pdf_beta": self._get_bool_flag("ENABLE_PDF_BETA", True),
            "debug_mode": self._get_bool_flag("DEBUG_MODE", False),
            "rate_limiting": self._get_bool_flag("ENABLE_RATE_LIMITING", False),
            "request_logging": self._get_bool_flag("ENABLE_REQUEST_LOGGING", True),
            "file_compression": self._get_bool_flag("ENABLE_FILE_COMPRESSION", True),
            "template_caching": self._get_bool_flag("ENABLE_TEMPLATE_CACHING", True),
            "output_validation": self._get_bool_flag("ENABLE_OUTPUT_VALIDATION", True),
            "image_text_extraction": self._get_bool_flag("ENABLE_IMAGE_TEXT_EXTRACTION", True)
        }
        
        self.logger.info(
            "Feature flags loaded",
            extra={
                "flags_count": len(flags),
                "enabled_flags": [name for name, enabled in flags.items() if enabled],
                "disabled_flags": [name for name, enabled in flags.items() if not enabled]
            }
        )
        
        return flags
    
    def _get_bool_flag(self, env_var: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(env_var)
        if value is None:
            return default
        
        value = value.strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        elif value in {"0", "false", "no", "off"}:
            return False
        else:
            self.logger.warning(
                "Invalid boolean flag value, using default",
                extra={
                    "env_var": env_var,
                    "value": value,
                    "default": default
                }
            )
            return default
    
    def is_enabled(self, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            True if flag is enabled
            
        Raises:
            ConfigurationException: If flag doesn't exist
        """
        if flag_name not in self._flags:
            raise ConfigurationException(
                f"Feature flag '{flag_name}' does not exist",
                config_key=flag_name
            )
        
        return self._flags[flag_name]
    
    def is_disabled(self, flag_name: str) -> bool:
        """
        Check if a feature flag is disabled.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            True if flag is disabled
        """
        return not self.is_enabled(flag_name)
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        return self._flags.copy()
    
    def get_enabled_flags(self) -> Dict[str, bool]:
        """Get only enabled feature flags."""
        return {name: enabled for name, enabled in self._flags.items() if enabled}
    
    def get_disabled_flags(self) -> Dict[str, bool]:
        """Get only disabled feature flags."""
        return {name: enabled for name, enabled in self._flags.items() if not enabled}
    
    def validate_flag_dependencies(self) -> None:
        """Validate that feature flag dependencies are satisfied."""
        # Chunking requires LLM summarization
        if self.is_enabled("chunking") and self.is_disabled("llm_summarization"):
            self.logger.warning(
                "Chunking is enabled but LLM summarization is disabled",
                extra={
                    "chunking": True,
                    "llm_summarization": False
                }
            )
        
        # Base64 input requires file compression
        if self.is_enabled("base64_input") and self.is_disabled("file_compression"):
            self.logger.warning(
                "Base64 input is enabled but file compression is disabled",
                extra={
                    "base64_input": True,
                    "file_compression": False
                }
            )
        
        # PDF beta requires LLM summarization
        if self.is_enabled("pdf_beta") and self.is_disabled("llm_summarization"):
            self.logger.warning(
                "PDF beta is enabled but LLM summarization is disabled",
                extra={
                    "pdf_beta": True,
                    "llm_summarization": False
                }
            )
    
    def get_flag_summary(self) -> Dict[str, Any]:
        """Get a summary of feature flag status."""
        enabled_count = sum(1 for enabled in self._flags.values() if enabled)
        total_count = len(self._flags)
        
        return {
            "total_flags": total_count,
            "enabled_flags": enabled_count,
            "disabled_flags": total_count - enabled_count,
            "enable_percentage": (enabled_count / total_count) * 100 if total_count > 0 else 0,
            "flags": self._flags.copy()
        }

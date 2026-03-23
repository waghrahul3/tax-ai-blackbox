"""Central configuration manager for the application."""

from typing import Dict, Any
from utils.logger import get_logger
from exceptions.base_exceptions import ConfigurationException

from .feature_flags import FeatureFlags
from .api_limits import ApiLimits
from .file_processing_config import FileProcessingConfig
from .llm_config import LLMConfig
from .app_config import AppConfig


class ConfigManager:
    """Central configuration manager that coordinates all configuration modules."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._feature_flags = FeatureFlags()
        self._api_limits = ApiLimits()
        self._file_config = FileProcessingConfig()
        self._llm_config = LLMConfig()
        self._app_config = AppConfig()
        
        self._validate_all_configs()
    
    def _validate_all_configs(self) -> None:
        """Validate all configuration modules."""
        try:
            self._feature_flags.validate_flag_dependencies()
            self._api_limits.validate_limits()
            self.logger.info("All configuration modules validated successfully")
        except Exception as e:
            self.logger.error("Configuration validation failed", extra={"error": str(e)})
            raise ConfigurationException(f"Configuration validation failed: {str(e)}") from e
    
    # Feature flags access
    def feature_flags(self) -> FeatureFlags:
        """Get feature flags configuration."""
        return self._feature_flags
    
    def is_feature_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        return self._feature_flags.is_enabled(flag_name)
    
    def is_feature_disabled(self, flag_name: str) -> bool:
        """Check if a feature flag is disabled."""
        return self._feature_flags.is_disabled(flag_name)
    
    # API limits access
    def api_limits(self) -> ApiLimits:
        """Get API limits configuration."""
        return self._api_limits
    
    def get_api_limit(self, limit_name: str) -> int:
        """Get a specific API limit."""
        return self._api_limits.get_limit(limit_name)
    
    # File processing access
    def file_config(self) -> FileProcessingConfig:
        """Get file processing configuration."""
        return self._file_config
    
    def is_supported_file(self, extension: str, file_type: str = None) -> bool:
        """Check if a file extension is supported."""
        return self._file_config.is_supported_extension(extension, file_type)
    
    # LLM configuration access
    def llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        return self._llm_config
    
    def get_llm_model(self) -> str:
        """Get default LLM model."""
        return self._llm_config.get_default_model()
    
    def get_llm_api_key(self) -> str:
        """Get LLM API key."""
        api_key = self._llm_config.get_api_key()
        if not api_key:
            raise ConfigurationException("LLM API key is not configured", config_key="ANTHROPIC_API_KEY")
        return api_key
    
    # Application configuration access
    def app_config(self) -> AppConfig:
        """Get application configuration."""
        return self._app_config
    
    def get_app_version(self) -> str:
        """Get application version."""
        return self._app_config.get_app_version()
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self._app_config.is_production()
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self._app_config.is_debug()
    
    def get_complete_config(self) -> Dict[str, Any]:
        """Get complete configuration summary."""
        return {
            "app": self._app_config.get_config_summary(),
            "feature_flags": self._feature_flags.get_flag_summary(),
            "api_limits": self._api_limits.get_limits_summary(),
            "file_processing": self._file_config.get_config_summary(),
            "llm": self._llm_config.get_config_summary()
        }
    
    def get_runtime_config(self) -> Dict[str, Any]:
        """Get runtime configuration for services."""
        return {
            "app_version": self.get_app_version(),
            "environment": self._app_config.get_environment(),
            "debug_mode": self.is_debug(),
            "feature_flags": self._feature_flags.get_all_flags(),
            "api_limits": self._api_limits.get_all_limits(),
            "supported_file_extensions": self._file_config.get_supported_extensions(),
            "llm_model": self.get_llm_model(),
            "llm_beta_headers": self._llm_config.get_beta_headers()
        }
    
    def validate_request_config(self, file_count: int, total_size: int) -> None:
        """
        Validate request against configuration limits.
        
        Args:
            file_count: Number of files in request
            total_size: Total size of files in bytes
            
        Raises:
            ConfigurationException: If request exceeds limits
        """
        max_files = self._api_limits.get_limit("max_files_per_request")
        if file_count > max_files:
            raise ConfigurationException(
                f"Too many files in request: {file_count} > {max_files}",
                config_key="max_files_per_request"
            )
        
        max_file_size_mb = self._api_limits.get_limit("max_file_size_mb")
        max_size_bytes = max_file_size_mb * 1024 * 1024
        if total_size > max_size_bytes:
            raise ConfigurationException(
                f"Request size too large: {total_size} bytes > {max_size_bytes} bytes",
                config_key="max_file_size_mb"
            )
    
    def reload_config(self) -> None:
        """Reload all configuration modules."""
        self.logger.info("Reloading configuration modules")
        
        try:
            self._feature_flags = FeatureFlags()
            self._api_limits = ApiLimits()
            self._file_config = FileProcessingConfig()
            self._llm_config = LLMConfig()
            self._app_config = AppConfig()
            
            self._validate_all_configs()
            self.logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error("Failed to reload configuration", extra={"error": str(e)})
            raise ConfigurationException(f"Failed to reload configuration: {str(e)}") from e


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def initialize_config() -> ConfigManager:
    """Initialize the configuration manager."""
    return get_config_manager()

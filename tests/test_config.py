"""Unit tests for configuration management system."""

import pytest
import os
from unittest.mock import patch, Mock
from config.feature_flags import FeatureFlags
from config.api_limits import ApiLimits
from config.file_processing_config import FileProcessingConfig
from config.llm_config import LLMConfig
from config.app_config import AppConfig
from config.config_manager import ConfigManager
from exceptions.base_exceptions import ConfigurationException


class TestFeatureFlags:
    """Test cases for FeatureFlags."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear environment variables for clean testing
        for key in list(os.environ.keys()):
            if key.startswith("ENABLE_"):
                os.environ.pop(key, None)
        self.feature_flags = FeatureFlags()
    
    def test_default_feature_flags(self):
        """Test default feature flag values."""
        assert self.feature_flags.is_enabled("chunking") is True
        assert self.feature_flags.is_enabled("llm_summarization") is True
        assert self.feature_flags.is_enabled("pdf_beta") is True
        assert self.feature_flags.is_enabled("pandas_cleaning") is False
        assert self.feature_flags.is_enabled("base64_input") is False
    
    @patch.dict(os.environ, {"ENABLE_PANDAS_CLEANING": "true"})
    def test_environment_override_true(self):
        """Test environment variable override to true."""
        feature_flags = FeatureFlags()
        assert feature_flags.is_enabled("pandas_cleaning") is True
    
    @patch.dict(os.environ, {"ENABLE_CHUNKING": "false"})
    def test_environment_override_false(self):
        """Test environment variable override to false."""
        feature_flags = FeatureFlags()
        assert feature_flags.is_enabled("chunking") is False
    
    @patch.dict(os.environ, {"ENABLE_DEBUG_MODE": "1"})
    def test_environment_override_numeric_true(self):
        """Test environment variable override with numeric true."""
        feature_flags = FeatureFlags()
        assert feature_flags.is_enabled("debug_mode") is True
    
    @patch.dict(os.environ, {"ENABLE_DEBUG_MODE": "0"})
    def test_environment_override_numeric_false(self):
        """Test environment variable override with numeric false."""
        feature_flags = FeatureFlags()
        assert feature_flags.is_enabled("debug_mode") is False
    
    def test_invalid_flag_name(self):
        """Test invalid flag name raises error."""
        with pytest.raises(ConfigurationException) as exc_info:
            self.feature_flags.is_enabled("nonexistent_flag")
        
        assert "does not exist" in str(exc_info.value).lower()
        assert exc_info.value.config_key == "nonexistent_flag"
    
    def test_get_all_flags(self):
        """Test getting all feature flags."""
        all_flags = self.feature_flags.get_all_flags()
        
        assert isinstance(all_flags, dict)
        assert "chunking" in all_flags
        assert "llm_summarization" in all_flags
        assert "pdf_beta" in all_flags
    
    def test_get_enabled_flags(self):
        """Test getting only enabled flags."""
        enabled_flags = self.feature_flags.get_enabled_flags()
        
        assert isinstance(enabled_flags, dict)
        assert all(enabled_flags.values())  # All should be True
        assert "chunking" in enabled_flags
    
    def test_get_disabled_flags(self):
        """Test getting only disabled flags."""
        disabled_flags = self.feature_flags.get_disabled_flags()
        
        assert isinstance(disabled_flags, dict)
        assert all(not value for value in disabled_flags.values())  # All should be False
        assert "pandas_cleaning" in disabled_flags
    
    def test_validate_flag_dependencies(self):
        """Test flag dependency validation."""
        # This should not raise any errors with default configuration
        self.feature_flags.validate_flag_dependencies()
    
    def test_get_flag_summary(self):
        """Test flag summary."""
        summary = self.feature_flags.get_flag_summary()
        
        assert "total_flags" in summary
        assert "enabled_flags" in summary
        assert "disabled_flags" in summary
        assert "enable_percentage" in summary
        assert "flags" in summary
        assert summary["total_flags"] > 0


class TestApiLimits:
    """Test cases for ApiLimits."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear environment variables for clean testing
        for key in list(os.environ.keys()):
            if key.startswith("MAX_") or key.startswith("RATE_LIMIT_"):
                os.environ.pop(key, None)
        self.api_limits = ApiLimits()
    
    def test_default_api_limits(self):
        """Test default API limit values."""
        assert self.api_limits.get_limit("max_tokens") == 64000
        assert self.api_limits.get_limit("max_image_bytes") == 4_500_000
        assert self.api_limits.get_limit("max_file_size_mb") == 50
        assert self.api_limits.get_limit("max_concurrent_requests") == 10
    
    @patch.dict(os.environ, {"MAX_TOKENS": "100000"})
    def test_environment_override(self):
        """Test environment variable override."""
        api_limits = ApiLimits()
        assert api_limits.get_limit("max_tokens") == 100000
    
    @patch.dict(os.environ, {"MAX_TOKENS": "invalid"})
    def test_invalid_environment_value(self):
        """Test invalid environment value uses default."""
        api_limits = ApiLimits()
        assert api_limits.get_limit("max_tokens") == 64000  # Should use default
    
    @patch.dict(os.environ, {"MAX_TOKENS": "-100"})
    def test_negative_environment_value(self):
        """Test negative environment value uses default."""
        api_limits = ApiLimits()
        assert api_limits.get_limit("max_tokens") == 64000  # Should use default
    
    def test_invalid_limit_name(self):
        """Test invalid limit name raises error."""
        with pytest.raises(ConfigurationException) as exc_info:
            self.api_limits.get_limit("nonexistent_limit")
        
        assert "does not exist" in str(exc_info.value).lower()
        assert exc_info.value.config_key == "nonexistent_limit"
    
    def test_get_all_limits(self):
        """Test getting all API limits."""
        all_limits = self.api_limits.get_all_limits()
        
        assert isinstance(all_limits, dict)
        assert "max_tokens" in all_limits
        assert "max_image_bytes" in all_limits
        assert "max_file_size_mb" in all_limits
    
    def test_validate_limits(self):
        """Test limit validation."""
        # This should not raise any errors with default configuration
        self.api_limits.validate_limits()
    
    def test_get_file_size_limits(self):
        """Test getting file size limits."""
        file_limits = self.api_limits.get_file_size_limits()
        
        assert "max_file_size_mb" in file_limits
        assert "max_file_size_bytes" in file_limits
        assert "max_image_bytes" in file_limits
        assert file_limits["max_file_size_bytes"] == file_limits["max_file_size_mb"] * 1024 * 1024
    
    def test_get_rate_limits(self):
        """Test getting rate limits."""
        rate_limits = self.api_limits.get_rate_limits()
        
        assert "max_concurrent_requests" in rate_limits
        assert "rate_limit_per_minute" in rate_limits
        assert "rate_limit_per_hour" in rate_limits
    
    def test_get_processing_limits(self):
        """Test getting processing limits."""
        processing_limits = self.api_limits.get_processing_limits()
        
        assert "max_tokens" in processing_limits
        assert "max_text_length" in processing_limits
        assert "max_chunk_size" in processing_limits
    
    def test_get_limits_summary(self):
        """Test limits summary."""
        summary = self.api_limits.get_limits_summary()
        
        assert "total_limits" in summary
        assert "file_size_mb" in summary
        assert "max_tokens" in summary
        assert "categories" in summary


class TestFileProcessingConfig:
    """Test cases for FileProcessingConfig."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear environment variables for clean testing
        for key in list(os.environ.keys()):
            if key.startswith("SUPPORTED_") or key.startswith("ALLOWED_") or key.startswith("BLOCKED_"):
                os.environ.pop(key, None)
        self.file_config = FileProcessingConfig()
    
    def test_default_supported_extensions(self):
        """Test default supported extensions."""
        text_extensions = self.file_config.get_supported_extensions('text')
        image_extensions = self.file_config.get_supported_extensions('image')
        pdf_extensions = self.file_config.get_supported_extensions('pdf')
        
        assert ".txt" in text_extensions
        assert ".md" in text_extensions
        assert ".csv" in text_extensions
        assert ".jpg" in image_extensions
        assert ".png" in image_extensions
        assert ".pdf" in pdf_extensions
    
    @patch.dict(os.environ, {"SUPPORTED_TEXT_EXTENSIONS": ".txt,.md,.custom"})
    def test_custom_text_extensions(self):
        """Test custom text extensions."""
        file_config = FileProcessingConfig()
        text_extensions = file_config.get_supported_extensions('text')
        
        assert ".txt" in text_extensions
        assert ".md" in text_extensions
        assert ".custom" in text_extensions
        assert ".csv" not in text_extensions  # Should not include default ones
    
    def test_is_supported_extension(self):
        """Test extension support checking."""
        assert self.file_config.is_supported_extension(".txt", "text") is True
        assert self.file_config.is_supported_extension("txt", "text") is True
        assert self.file_config.is_supported_extension(".jpg", "image") is True
        assert self.file_config.is_supported_extension(".pdf", "pdf") is True
        assert self.file_config.is_supported_extension(".xyz", "text") is False
    
    def test_is_supported_extension_no_type(self):
        """Test extension support without type hint."""
        assert self.file_config.is_supported_extension(".txt") is True
        assert self.file_config.is_supported_extension(".jpg") is True
        assert self.file_config.is_supported_extension(".pdf") is True
        assert self.file_config.is_supported_extension(".xyz") is False
    
    def test_get_file_type_from_extension(self):
        """Test file type detection from extension."""
        assert self.file_config.get_file_type_from_extension(".txt") == "text"
        assert self.file_config.get_file_type_from_extension("txt") == "text"
        assert self.file_config.get_file_type_from_extension(".jpg") == "image"
        assert self.file_config.get_file_type_from_extension(".pdf") == "pdf"
        assert self.file_config.get_file_type_from_extension(".xyz") == "unknown"
    
    def test_is_allowed_mime_type(self):
        """Test MIME type validation."""
        assert self.file_config.is_allowed_mime_type("text/plain") is True
        assert self.file_config.is_allowed_mime_type("image/jpeg") is True
        assert self.file_config.is_allowed_mime_type("application/pdf") is True
        assert self.file_config.is_allowed_mime_type("application/unknown") is False
    
    def test_is_blocked_filename(self):
        """Test blocked filename checking."""
        assert self.file_config.is_blocked_filename("../../../etc/passwd") is True
        assert self.file_config.is_blocked_filename("file.exe") is True
        assert self.file_config.is_blocked_filename("normal.txt") is False
        assert self.file_config.is_blocked_filename(".hidden") is True
    
    def test_get_directory_config(self):
        """Test getting directory configuration."""
        dir_config = self.file_config.get_directory_config()
        
        assert "output_directory" in dir_config
        assert "temp_directory" in dir_config
        assert "upload_directory" in dir_config
        assert dir_config["output_directory"] == "output"
    
    def test_get_validation_config(self):
        """Test getting validation configuration."""
        validation_config = self.file_config.get_validation_config()
        
        assert "max_filename_length" in validation_config
        assert "allowed_mime_types" in validation_config
        assert "blocked_patterns" in validation_config
        assert "max_concurrent_uploads" in validation_config
    
    def test_get_config_summary(self):
        """Test configuration summary."""
        summary = self.file_config.get_config_summary()
        
        assert "supported_extensions" in summary
        assert "directories" in summary
        assert "compression" in summary
        assert "validation" in summary


class TestLLMConfig:
    """Test cases for LLMConfig."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear environment variables for clean testing
        for key in list(os.environ.keys()):
            if key.startswith("ANTHROPIC_") or key.startswith("LLM_"):
                os.environ.pop(key, None)
        self.llm_config = LLMConfig()
    
    def test_default_llm_config(self):
        """Test default LLM configuration."""
        assert self.llm_config.get_default_model() == "claude-3-5-sonnet-20241022"
        assert self.llm_config.get_default_temperature() == 0.0
        assert "pdfs-2024-09-25" in self.llm_config.get_beta_headers()
    
    @patch.dict(os.environ, {"ANTHROPIC_MODEL": "claude-3-haiku-20240307"})
    def test_custom_model(self):
        """Test custom model configuration."""
        llm_config = LLMConfig()
        assert llm_config.get_default_model() == "claude-3-haiku-20240307"
    
    @patch.dict(os.environ, {"LLM_TEMPERATURE": "1.5"})
    def test_custom_temperature(self):
        """Test custom temperature configuration."""
        llm_config = LLMConfig()
        assert llm_config.get_default_temperature() == 1.5
    
    @patch.dict(os.environ, {"LLM_TEMPERATURE": "3.0"})
    def test_invalid_temperature(self):
        """Test invalid temperature uses default."""
        llm_config = LLMConfig()
        assert llm_config.get_default_temperature() == 0.0  # Should use default
    
    def test_is_model_available(self):
        """Test model availability checking."""
        assert self.llm_config.is_model_available("claude-3-5-sonnet-20241022") is True
        assert self.llm_config.is_model_available("claude-3-haiku-20240307") is True
        assert self.llm_config.is_model_available("nonexistent-model") is False
    
    def test_supports_vision(self):
        """Test vision support checking."""
        assert self.llm_config.supports_vision("claude-3-5-sonnet-20241022") is True
        assert self.llm_config.supports_vision("claude-3-haiku-20240307") is True
    
    def test_supports_pdf(self):
        """Test PDF support checking."""
        assert self.llm_config.supports_pdf("claude-3-5-sonnet-20241022") is True
        assert self.llm_config.supports_pdf("claude-3-haiku-20240307") is False
    
    def test_get_max_tokens(self):
        """Test getting max tokens for model."""
        assert self.llm_config.get_max_tokens("claude-3-5-sonnet-20241022") == 200000
        assert self.llm_config.get_max_tokens("claude-3-haiku-20240307") == 40000
    
    def test_validate_temperature(self):
        """Test temperature validation."""
        # Valid temperatures
        assert self.llm_config.validate_temperature(0.5) == 0.5
        assert self.llm_config.validate_temperature(1.0) == 1.0
        
        # Out of range temperatures should be clamped
        assert self.llm_config.validate_temperature(-1.0) == 0.0
        assert self.llm_config.validate_temperature(3.0) == 2.0
    
    def test_get_config_summary(self):
        """Test configuration summary."""
        summary = self.llm_config.get_config_summary()
        
        assert "default_model" in summary
        assert "default_temperature" in summary
        assert "beta_headers" in summary
        assert "available_models" in summary
        assert "model_limits" in summary


class TestAppConfig:
    """Test cases for AppConfig."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear environment variables for clean testing
        for key in list(os.environ.keys()):
            if key in ["APP_NAME", "APP_VERSION", "ENVIRONMENT", "DEBUG", "HOST", "PORT", "LOG_LEVEL"]:
                os.environ.pop(key, None)
        self.app_config = AppConfig()
    
    def test_default_app_config(self):
        """Test default app configuration."""
        assert self.app_config.get_app_name() == "Tax AI Agent"
        assert self.app_config.get_app_version() == "0.0.0"
        assert self.app_config.get_environment() == "development"
        assert self.app_config.is_debug() is False
        assert self.app_config.get_host() == "0.0.0.0"
        assert self.app_config.get_port() == 8000
    
    @patch.dict(os.environ, {"APP_VERSION": "1.0.0"})
    def test_custom_version(self):
        """Test custom version configuration."""
        app_config = AppConfig()
        assert app_config.get_app_version() == "1.0.0"
    
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_production_environment(self):
        """Test production environment."""
        app_config = AppConfig()
        assert app_config.get_environment() == "production"
        assert app_config.is_production() is True
        assert app_config.is_development() is False
    
    @patch.dict(os.environ, {"DEBUG": "true"})
    def test_debug_mode(self):
        """Test debug mode."""
        app_config = AppConfig()
        assert app_config.is_debug() is True
    
    def test_get_cors_origins(self):
        """Test CORS origins."""
        origins = self.app_config.get_cors_origins()
        assert isinstance(origins, list)
        assert "*" in origins
    
    @patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,https://example.com"})
    def test_custom_cors_origins(self):
        """Test custom CORS origins."""
        app_config = AppConfig()
        origins = app_config.get_cors_origins()
        assert "http://localhost:3000" in origins
        assert "https://example.com" in origins
        assert "*" not in origins
    
    def test_get_config_summary(self):
        """Test configuration summary."""
        summary = self.app_config.get_config_summary()
        
        assert "app_name" in summary
        assert "version" in summary
        assert "environment" in summary
        assert "debug" in summary
        assert "host" in summary
        assert "port" in summary


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear environment variables for clean testing
        env_vars_to_clear = []
        for key in os.environ:
            if any(key.startswith(prefix) for prefix in [
                "ENABLE_", "MAX_", "RATE_LIMIT_", "SUPPORTED_", "ALLOWED_", 
                "BLOCKED_", "ANTHROPIC_", "LLM_", "APP_", "DEBUG", "HOST", "PORT", "LOG_LEVEL"
            ]):
                env_vars_to_clear.append(key)
        
        for key in env_vars_to_clear:
            os.environ.pop(key, None)
        
        self.config_manager = ConfigManager()
    
    def test_config_manager_initialization(self):
        """Test config manager initialization."""
        assert self.config_manager.feature_flags() is not None
        assert self.config_manager.api_limits() is not None
        assert self.config_manager.file_config() is not None
        assert self.config_manager.llm_config() is not None
        assert self.config_manager.app_config() is not None
    
    def test_feature_flag_access(self):
        """Test feature flag access through config manager."""
        assert self.config_manager.is_feature_enabled("chunking") is True
        assert self.config_manager.is_feature_disabled("pandas_cleaning") is True
    
    def test_api_limit_access(self):
        """Test API limit access through config manager."""
        assert self.config_manager.get_api_limit("max_tokens") == 64000
        assert self.config_manager.get_api_limit("max_image_bytes") == 4_500_000
    
    def test_file_config_access(self):
        """Test file config access through config manager."""
        assert self.config_manager.is_supported_file(".txt", "text") is True
        assert self.config_manager.is_supported_file(".jpg", "image") is True
        assert self.config_manager.is_supported_file(".pdf", "pdf") is True
    
    def test_llm_config_access(self):
        """Test LLM config access through config manager."""
        assert self.config_manager.get_llm_model() == "claude-3-5-sonnet-20241022"
        assert self.config_manager.get_app_version() == "0.0.0"
    
    def test_get_complete_config(self):
        """Test getting complete configuration."""
        complete_config = self.config_manager.get_complete_config()
        
        assert "app" in complete_config
        assert "feature_flags" in complete_config
        assert "api_limits" in complete_config
        assert "file_processing" in complete_config
        assert "llm" in complete_config
    
    def test_get_runtime_config(self):
        """Test getting runtime configuration."""
        runtime_config = self.config_manager.get_runtime_config()
        
        assert "app_version" in runtime_config
        assert "environment" in runtime_config
        assert "debug_mode" in runtime_config
        assert "feature_flags" in runtime_config
        assert "api_limits" in runtime_config
        assert "supported_file_extensions" in runtime_config
        assert "llm_model" in runtime_config
        assert "llm_beta_headers" in runtime_config
    
    def test_validate_request_config(self):
        """Test request configuration validation."""
        # Valid request
        self.config_manager.validate_request_config(5, 10 * 1024 * 1024)  # 5 files, 10MB
        
        # Too many files
        with pytest.raises(ConfigurationException):
            self.config_manager.validate_request_config(20, 10 * 1024 * 1024)  # 20 files
        
        # Too large
        with pytest.raises(ConfigurationException):
            self.config_manager.validate_request_config(5, 100 * 1024 * 1024)  # 100MB
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""})
    def test_missing_api_key(self):
        """Test missing API key raises error."""
        config_manager = ConfigManager()
        
        with pytest.raises(ConfigurationException) as exc_info:
            config_manager.get_llm_api_key()
        
        assert "not configured" in str(exc_info.value).lower()
        assert exc_info.value.config_key == "ANTHROPIC_API_KEY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

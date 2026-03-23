"""API limits and thresholds configuration."""

import os
from typing import Dict, Any
from utils.logger import get_logger
from exceptions.base_exceptions import ConfigurationException


class ApiLimits:
    """Centralized API limits and thresholds management."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._limits = self._load_api_limits()
    
    def _load_api_limits(self) -> Dict[str, int]:
        """Load API limits from environment variables."""
        limits = {
            "max_tokens": self._get_int_limit("MAX_TOKENS", 64000),
            "max_image_bytes": self._get_int_limit("MAX_IMAGE_BYTES", 4_500_000),
            "max_file_size_mb": self._get_int_limit("MAX_FILE_SIZE_MB", 50),
            "max_concurrent_requests": self._get_int_limit("MAX_CONCURRENT_REQUESTS", 10),
            "rate_limit_per_minute": self._get_int_limit("RATE_LIMIT_PER_MINUTE", 60),
            "rate_limit_per_hour": self._get_int_limit("RATE_LIMIT_PER_HOUR", 1000),
            "max_text_length": self._get_int_limit("MAX_TEXT_LENGTH", 1_000_000),
            "max_chunk_size": self._get_int_limit("MAX_CHUNK_SIZE", 2000),
            "chunk_overlap": self._get_int_limit("CHUNK_OVERLAP", 200),
            "max_files_per_request": self._get_int_limit("MAX_FILES_PER_REQUEST", 10),
            "request_timeout_seconds": self._get_int_limit("REQUEST_TIMEOUT_SECONDS", 300),
            "max_retry_attempts": self._get_int_limit("MAX_RETRY_ATTEMPTS", 3),
            "retry_delay_seconds": self._get_int_limit("RETRY_DELAY_SECONDS", 5),
            "api_overload_retry_seconds": self._get_int_limit("API_OVERLOAD_RETRY_SECONDS", 30),
            "rate_limit_retry_seconds": self._get_int_limit("RATE_LIMIT_RETRY_SECONDS", 60),
            "max_csv_rows": self._get_int_limit("MAX_CSV_ROWS", 10_000),
            "max_base64_size_mb": self._get_int_limit("MAX_BASE64_SIZE_MB", 5)
        }
        
        self.logger.info(
            "API limits loaded",
            extra={
                "limits_count": len(limits),
                "max_tokens": limits["max_tokens"],
                "max_image_bytes": limits["max_image_bytes"],
                "max_file_size_mb": limits["max_file_size_mb"]
            }
        )
        
        return limits
    
    def _get_int_limit(self, env_var: str, default: int) -> int:
        """Get integer value from environment variable."""
        value = os.getenv(env_var)
        if value is None:
            return default
        
        try:
            int_value = int(value)
            if int_value < 0:
                self.logger.warning(
                    "Negative limit value, using default",
                    extra={
                        "env_var": env_var,
                        "value": value,
                        "default": default
                    }
                )
                return default
            return int_value
        except ValueError:
            self.logger.warning(
                "Invalid integer limit value, using default",
                extra={
                    "env_var": env_var,
                    "value": value,
                    "default": default
                }
            )
            return default
    
    def get_limit(self, limit_name: str) -> int:
        """
        Get an API limit value.
        
        Args:
            limit_name: Name of the limit
            
        Returns:
            Limit value
            
        Raises:
            ConfigurationException: If limit doesn't exist
        """
        if limit_name not in self._limits:
            raise ConfigurationException(
                f"API limit '{limit_name}' does not exist",
                config_key=limit_name
            )
        
        return self._limits[limit_name]
    
    def get_all_limits(self) -> Dict[str, int]:
        """Get all API limits."""
        return self._limits.copy()
    
    def validate_limits(self) -> None:
        """Validate that API limits are reasonable."""
        # Validate chunk size vs max tokens
        if self._limits["max_chunk_size"] > self._limits["max_tokens"]:
            self.logger.warning(
                "Chunk size exceeds max tokens",
                extra={
                    "max_chunk_size": self._limits["max_chunk_size"],
                    "max_tokens": self._limits["max_tokens"]
                }
            )
        
        # Validate chunk overlap vs chunk size
        if self._limits["chunk_overlap"] >= self._limits["max_chunk_size"]:
            self.logger.warning(
                "Chunk overlap is too large compared to chunk size",
                extra={
                    "chunk_overlap": self._limits["chunk_overlap"],
                    "max_chunk_size": self._limits["max_chunk_size"]
                }
            )
        
        # Validate file size vs image size
        max_file_bytes = self._limits["max_file_size_mb"] * 1024 * 1024
        if max_file_bytes < self._limits["max_image_bytes"]:
            self.logger.warning(
                "Max file size is smaller than max image size",
                extra={
                    "max_file_size_mb": self._limits["max_file_size_mb"],
                    "max_image_bytes": self._limits["max_image_bytes"]
                }
            )
        
        # Validate rate limits
        if self._limits["rate_limit_per_hour"] < self._limits["rate_limit_per_minute"]:
            self.logger.warning(
                "Hourly rate limit is smaller than minute rate limit",
                extra={
                    "rate_limit_per_hour": self._limits["rate_limit_per_hour"],
                    "rate_limit_per_minute": self._limits["rate_limit_per_minute"]
                }
            )
    
    def get_file_size_limits(self) -> Dict[str, int]:
        """Get file size related limits."""
        return {
            "max_file_size_mb": self._limits["max_file_size_mb"],
            "max_file_size_bytes": self._limits["max_file_size_mb"] * 1024 * 1024,
            "max_image_bytes": self._limits["max_image_bytes"],
            "max_base64_size_mb": self._limits["max_base64_size_mb"],
            "max_base64_size_bytes": self._limits["max_base64_size_mb"] * 1024 * 1024
        }
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get rate limiting related limits."""
        return {
            "max_concurrent_requests": self._limits["max_concurrent_requests"],
            "rate_limit_per_minute": self._limits["rate_limit_per_minute"],
            "rate_limit_per_hour": self._limits["rate_limit_per_hour"],
            "request_timeout_seconds": self._limits["request_timeout_seconds"],
            "max_retry_attempts": self._limits["max_retry_attempts"],
            "retry_delay_seconds": self._limits["retry_delay_seconds"]
        }
    
    def get_processing_limits(self) -> Dict[str, int]:
        """Get processing related limits."""
        return {
            "max_tokens": self._limits["max_tokens"],
            "max_text_length": self._limits["max_text_length"],
            "max_chunk_size": self._limits["max_chunk_size"],
            "chunk_overlap": self._limits["chunk_overlap"],
            "max_files_per_request": self._limits["max_files_per_request"],
            "max_csv_rows": self._limits["max_csv_rows"]
        }
    
    def get_error_retry_limits(self) -> Dict[str, int]:
        """Get error retry related limits."""
        return {
            "max_retry_attempts": self._limits["max_retry_attempts"],
            "retry_delay_seconds": self._limits["retry_delay_seconds"],
            "api_overload_retry_seconds": self._limits["api_overload_retry_seconds"],
            "rate_limit_retry_seconds": self._limits["rate_limit_retry_seconds"]
        }
    
    def get_limits_summary(self) -> Dict[str, Any]:
        """Get a summary of API limits."""
        return {
            "total_limits": len(self._limits),
            "file_size_mb": self._limits["max_file_size_mb"],
            "max_tokens": self._limits["max_tokens"],
            "rate_limit_per_minute": self._limits["rate_limit_per_minute"],
            "max_files_per_request": self._limits["max_files_per_request"],
            "categories": {
                "file_processing": ["max_file_size_mb", "max_image_bytes", "max_base64_size_mb", "max_files_per_request"],
                "text_processing": ["max_tokens", "max_text_length", "max_chunk_size", "chunk_overlap"],
                "rate_limiting": ["max_concurrent_requests", "rate_limit_per_minute", "rate_limit_per_hour"],
                "error_handling": ["max_retry_attempts", "retry_delay_seconds", "api_overload_retry_seconds"]
            }
        }

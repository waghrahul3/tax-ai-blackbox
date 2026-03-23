"""LLM configuration and model settings."""

import os
from typing import Dict, List, Optional
from utils.logger import get_logger
from exceptions.base_exceptions import ConfigurationException


class LLMConfig:
    """Centralized LLM configuration management."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._config = self._load_llm_config()
    
    def _load_llm_config(self) -> Dict[str, any]:
        """Load LLM configuration from environment variables."""
        config = {
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "default_model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            "default_temperature": self._get_float_setting("LLM_TEMPERATURE", 0.0),
            "beta_headers": self._get_beta_headers(),
            "available_models": self._get_available_models(),
            "model_limits": self._get_model_limits(),
            "retry_config": self._get_retry_config(),
            "timeout_config": self._get_timeout_config()
        }
        
        self.logger.info(
            "LLM config loaded",
            extra={
                "default_model": config["default_model"],
                "default_temperature": config["default_temperature"],
                "beta_headers_enabled": len(config["beta_headers"]) > 0,
                "available_models": len(config["available_models"])
            }
        )
        
        return config
    
    def _get_float_setting(self, env_var: str, default: float) -> float:
        """Get float setting from environment variable."""
        value = os.getenv(env_var)
        if value is None:
            return default
        
        try:
            float_value = float(value)
            # Validate temperature range
            if "TEMPERATURE" in env_var and not 0.0 <= float_value <= 2.0:
                self.logger.warning(
                    "Temperature out of range, using default",
                    extra={
                        "env_var": env_var,
                        "value": float_value,
                        "default": default
                    }
                )
                return default
            return float_value
        except ValueError:
            return default
    
    def _get_beta_headers(self) -> List[str]:
        """Get beta headers configuration."""
        beta_env = os.getenv("ANTHROPIC_BETA_HEADERS", "pdfs-2024-09-25")
        if beta_env:
            return [header.strip() for header in beta_env.split(',') if header.strip()]
        return []
    
    def _get_available_models(self) -> Dict[str, Dict[str, any]]:
        """Get available LLM models and their configurations."""
        models_env = os.getenv("AVAILABLE_MODELS", "")
        if models_env:
            # Parse custom models from environment
            models = {}
            for model_spec in models_env.split(','):
                model_spec = model_spec.strip()
                if ':' in model_spec:
                    name, config = model_spec.split(':', 1)
                    models[name] = {"name": name, "custom": True, "config": config}
                else:
                    models[model_spec] = {"name": model_spec, "custom": False}
            return models
        
        # Default models
        return {
            "claude-3-5-sonnet-20241022": {
                "name": "claude-3-5-sonnet-20241022",
                "max_tokens": 200000,
                "supports_vision": True,
                "supports_pdf": True,
                "context_window": 200000
            },
            "claude-3-haiku-20240307": {
                "name": "claude-3-haiku-20240307",
                "max_tokens": 40000,
                "supports_vision": True,
                "supports_pdf": False,
                "context_window": 40000
            },
            "claude-3-opus-20240229": {
                "name": "claude-3-opus-20240229",
                "max_tokens": 4000,
                "supports_vision": True,
                "supports_pdf": False,
                "context_window": 4000
            }
        }
    
    def _get_model_limits(self) -> Dict[str, int]:
        """Get model-specific limits."""
        return {
            "default_max_tokens": int(os.getenv("MAX_TOKENS", "64000")),
            "min_temperature": 0.0,
            "max_temperature": 2.0,
            "max_prompt_length": int(os.getenv("MAX_PROMPT_LENGTH", "100000")),
            "max_response_length": int(os.getenv("MAX_RESPONSE_LENGTH", "4000"))
        }
    
    def _get_retry_config(self) -> Dict[str, int]:
        """Get retry configuration."""
        return {
            "max_retries": int(os.getenv("LLM_MAX_RETRIES", "3")),
            "retry_delay": int(os.getenv("LLM_RETRY_DELAY", "5")),
            "exponential_backoff": self._get_bool_setting("LLM_EXPONENTIAL_BACKOFF", True),
            "max_retry_delay": int(os.getenv("LLM_MAX_RETRY_DELAY", "60"))
        }
    
    def _get_timeout_config(self) -> Dict[str, int]:
        """Get timeout configuration."""
        return {
            "request_timeout": int(os.getenv("LLM_REQUEST_TIMEOUT", "300")),
            "read_timeout": int(os.getenv("LLM_READ_TIMEOUT", "120")),
            "connect_timeout": int(os.getenv("LLM_CONNECT_TIMEOUT", "30"))
        }
    
    def _get_bool_setting(self, env_var: str, default: bool) -> bool:
        """Get boolean setting from environment variable."""
        value = os.getenv(env_var)
        if value is None:
            return default
        
        value = value.strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        elif value in {"0", "false", "no", "off"}:
            return False
        else:
            return default
    
    def get_api_key(self) -> Optional[str]:
        """Get the API key."""
        return self._config["api_key"]
    
    def get_default_model(self) -> str:
        """Get the default model name."""
        return self._config["default_model"]
    
    def get_default_temperature(self) -> float:
        """Get the default temperature."""
        return self._config["default_temperature"]
    
    def get_beta_headers(self) -> List[str]:
        """Get beta headers."""
        return self._config["beta_headers"].copy()
    
    def is_model_available(self, model_name: str) -> bool:
        """
        Check if a model is available.
        
        Args:
            model_name: Model name to check
            
        Returns:
            True if model is available
        """
        return model_name in self._config["available_models"]
    
    def get_model_config(self, model_name: str) -> Optional[Dict[str, any]]:
        """
        Get configuration for a specific model.
        
        Args:
            model_name: Model name
            
        Returns:
            Model configuration or None if not found
        """
        return self._config["available_models"].get(model_name)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        return list(self._config["available_models"].keys())
    
    def supports_vision(self, model_name: str = None) -> bool:
        """
        Check if a model supports vision.
        
        Args:
            model_name: Model name (uses default if None)
            
        Returns:
            True if model supports vision
        """
        model_name = model_name or self._config["default_model"]
        model_config = self.get_model_config(model_name)
        return model_config.get("supports_vision", False) if model_config else False
    
    def supports_pdf(self, model_name: str = None) -> bool:
        """
        Check if a model supports PDF processing.
        
        Args:
            model_name: Model name (uses default if None)
            
        Returns:
            True if model supports PDF
        """
        model_name = model_name or self._config["default_model"]
        model_config = self.get_model_config(model_name)
        return model_config.get("supports_pdf", False) if model_config else False
    
    def get_max_tokens(self, model_name: str = None) -> int:
        """
        Get maximum tokens for a model.
        
        Args:
            model_name: Model name (uses default if None)
            
        Returns:
            Maximum tokens
        """
        model_name = model_name or self._config["default_model"]
        model_config = self.get_model_config(model_name)
        
        if model_config and "max_tokens" in model_config:
            return model_config["max_tokens"]
        
        return self._config["model_limits"]["default_max_tokens"]
    
    def validate_temperature(self, temperature: float) -> float:
        """
        Validate and clamp temperature to valid range.
        
        Args:
            temperature: Temperature to validate
            
        Returns:
            Validated temperature
        """
        min_temp = self._config["model_limits"]["min_temperature"]
        max_temp = self._config["model_limits"]["max_temperature"]
        
        if temperature < min_temp:
            self.logger.warning(
                "Temperature too low, clamping to minimum",
                extra={"temperature": temperature, "min": min_temp}
            )
            return min_temp
        elif temperature > max_temp:
            self.logger.warning(
                "Temperature too high, clamping to maximum",
                extra={"temperature": temperature, "max": max_temp}
            )
            return max_temp
        
        return temperature
    
    def get_retry_config(self) -> Dict[str, int]:
        """Get retry configuration."""
        return self._config["retry_config"].copy()
    
    def get_timeout_config(self) -> Dict[str, int]:
        """Get timeout configuration."""
        return self._config["timeout_config"].copy()
    
    def get_config_summary(self) -> Dict[str, any]:
        """Get LLM configuration summary."""
        return {
            "default_model": self._config["default_model"],
            "default_temperature": self._config["default_temperature"],
            "beta_headers": self._config["beta_headers"],
            "available_models": len(self._config["available_models"]),
            "model_limits": self._config["model_limits"],
            "retry_config": self._config["retry_config"],
            "timeout_config": self._config["timeout_config"],
            "api_key_configured": bool(self._config["api_key"])
        }

"""Base exception classes for the Tax AI Agent application."""


class TaxAIAgentException(Exception):
    """Base exception for all Tax AI Agent errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ValidationException(TaxAIAgentException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value


class ConfigurationException(TaxAIAgentException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key

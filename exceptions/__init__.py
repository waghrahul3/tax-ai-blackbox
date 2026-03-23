"""Custom exceptions for the Tax AI Agent application."""

from .base_exceptions import (
    TaxAIAgentException,
    ValidationException,
    ConfigurationException
)
from .document_exceptions import (
    DocumentProcessingException,
    FileValidationException,
    DocumentLoadException
)
from .llm_exceptions import (
    LLMServiceException,
    LLMRateLimitException,
    LLMAPIOverloadException
)
from .output_exceptions import (
    OutputGenerationException,
    OutputFormatException,
    FileCreationException
)

__all__ = [
    # Base exceptions
    "TaxAIAgentException",
    "ValidationException", 
    "ConfigurationException",
    
    # Document exceptions
    "DocumentProcessingException",
    "FileValidationException",
    "DocumentLoadException",
    
    # LLM exceptions
    "LLMServiceException",
    "LLMRateLimitException",
    "LLMAPIOverloadException",
    
    # Output exceptions
    "OutputGenerationException",
    "OutputFormatException",
    "FileCreationException"
]

"""LLM service related exceptions."""

from .base_exceptions import TaxAIAgentException


class LLMServiceException(TaxAIAgentException):
    """Base exception for LLM service errors."""
    
    def __init__(self, message: str, model: str = None, request_id: str = None):
        super().__init__(message, "LLM_SERVICE_ERROR")
        self.model = model
        self.request_id = request_id


class LLMRateLimitException(LLMServiceException):
    """Raised when LLM API rate limit is exceeded."""
    
    def __init__(self, message: str, model: str = None, request_id: str = None, 
                 retry_after: int = None):
        super().__init__(message, model, request_id)
        self.error_code = "LLM_RATE_LIMIT_ERROR"
        self.retry_after = retry_after


class LLMAPIOverloadException(LLMServiceException):
    """Raised when LLM API is overloaded."""
    
    def __init__(self, message: str, model: str = None, request_id: str = None, 
                 retry_after: int = None):
        super().__init__(message, model, request_id)
        self.error_code = "LLM_API_OVERLOAD_ERROR"
        self.retry_after = retry_after

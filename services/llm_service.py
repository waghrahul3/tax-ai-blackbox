"""Service for handling LLM interactions and API calls."""

from typing import List, Dict, Any
from core.llm_factory import get_llm
from utils.logger import get_logger
from exceptions.llm_exceptions import (
    LLMServiceException,
    LLMRateLimitException,
    LLMAPIOverloadException
)
from config.config_manager import get_config_manager


class LLMService:
    """Service for managing LLM interactions and API calls."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = get_config_manager()
        self.llm_config = self.config_manager.llm_config()
        self.api_limits = self.config_manager.api_limits()
        
        # Use new configuration system
        self.default_model = self.llm_config.get_default_model()
        self.default_max_tokens = self.api_limits.get_limit("max_tokens")
        self.pdf_beta_enabled = self.config_manager.is_feature_enabled("pdf_beta")
        self.beta_headers = self.llm_config.get_beta_headers()
    
    async def create_message(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = None,
        temperature: float = 0.0,
        include_beta_headers: bool = False,
        stream: bool = True
    ) -> str:
        """
        Create and execute an LLM message request.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use (defaults to configured model)
            max_tokens: Maximum tokens for response (defaults to configured)
            temperature: Temperature for response generation
            include_beta_headers: Whether to include beta headers
            stream: Whether to stream the response
            
        Returns:
            Generated text response
            
        Raises:
            LLMServiceException: If LLM call fails
            LLMRateLimitException: If rate limit is exceeded
            LLMAPIOverloadException: If API is overloaded
        """
        model = model or self.default_model
        max_tokens = max_tokens or self.default_max_tokens
        
        try:
            # Determine if beta headers should be used
            use_beta = include_beta_headers and self.pdf_beta_enabled
            
            # Get appropriate LLM client
            llm = get_llm(temperature=temperature, include_beta_headers=use_beta)
            
            self.logger.debug(
                "Invoking LLM",
                extra={
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "use_beta_headers": use_beta,
                    "message_count": len(messages)
                }
            )
            
            # Create the message
            response = await llm.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                stream=stream
            )
            
            # Collect streamed response
            if stream:
                text_response = ""
                async for chunk in response:
                    if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                        text_response += chunk.delta.text
                    elif chunk.type == "content_block_stop":
                        break
                return text_response
            else:
                return response.content[0].text if response.content else ""
                
        except Exception as e:
            error_message = str(e)
            
            # Handle specific API errors
            if "529" in error_message or "overloaded_error" in error_message:
                self.logger.error(
                    "Anthropic API overloaded",
                    extra={"error": error_message, "model": model}
                )
                raise LLMAPIOverloadException(
                    "AI service temporarily overloaded",
                    model=model,
                    retry_after=30
                ) from e
                
            elif "429" in error_message or "rate_limit" in error_message:
                self.logger.error(
                    "Anthropic API rate limit exceeded",
                    extra={"error": error_message, "model": model}
                )
                raise LLMRateLimitException(
                    "Rate limit exceeded",
                    model=model,
                    retry_after=60
                ) from e
                
            else:
                self.logger.error(
                    "LLM call failed",
                    extra={"error": error_message, "model": model}
                )
                raise LLMServiceException(
                    f"LLM call failed: {error_message}",
                    model=model
                ) from e
    
    async def create_text_summarization(
        self,
        text: str,
        instruction: str = "Summarize this text:",
        temperature: float = 0.0,
        model: str = None
    ) -> str:
        """
        Create a text summarization request.
        
        Args:
            text: Text to summarize
            instruction: Instruction for summarization
            temperature: Temperature for response generation
            model: Model name to use
            
        Returns:
            Summarized text
        """
        messages = [
            {
                "role": "user",
                "content": f"{instruction}\n\n{text}"
            }
        ]
        
        return await self.create_message(
            messages=messages,
            temperature=temperature,
            model=model
        )
    
    async def create_document_analysis(
        self,
        content: str,
        instruction: str = "Analyze this document:",
        temperature: float = 0.0,
        model: str = None
    ) -> str:
        """
        Create a document analysis request.
        
        Args:
            content: Document content to analyze
            instruction: Instruction for analysis
            temperature: Temperature for response generation
            model: Model name to use
            
        Returns:
            Analysis result
        """
        messages = [
            {
                "role": "user",
                "content": f"{instruction}\n\n{content}"
            }
        ]
        
        return await self.create_message(
            messages=messages,
            temperature=temperature,
            model=model
        )
    
    def get_client_info(self) -> Dict[str, Any]:
        """
        Get information about the LLM client configuration.
        
        Returns:
            Dictionary with client configuration details
        """
        return {
            "default_model": self.default_model,
            "default_max_tokens": self.default_max_tokens,
            "pdf_beta_enabled": self.pdf_beta_enabled,
            "beta_headers": self.beta_headers
        }
    
    def validate_messages(self, messages: List[Dict[str, str]]) -> None:
        """
        Validate message format before sending to LLM.
        
        Args:
            messages: List of message dictionaries
            
        Raises:
            LLMServiceException: If messages are invalid
        """
        if not messages:
            raise LLMServiceException("No messages provided")
        
        if not isinstance(messages, list):
            raise LLMServiceException("Messages must be a list")
        
        for i, message in enumerate(messages):
            if not isinstance(message, dict):
                raise LLMServiceException(f"Message {i} must be a dictionary")
            
            if "role" not in message:
                raise LLMServiceException(f"Message {i} missing 'role' field")
            
            if "content" not in message:
                raise LLMServiceException(f"Message {i} missing 'content' field")
            
            if message["role"] not in ["user", "assistant", "system"]:
                raise LLMServiceException(f"Message {i} has invalid role: {message['role']}")
            
            if not isinstance(message["content"], str):
                raise LLMServiceException(f"Message {i} content must be a string")

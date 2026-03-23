"""Unit tests for custom exception classes."""

import pytest
from exceptions.base_exceptions import TaxAIAgentException, ValidationException, ConfigurationException
from exceptions.document_exceptions import DocumentProcessingException, FileValidationException, DocumentLoadException
from exceptions.llm_exceptions import LLMServiceException, LLMRateLimitException, LLMAPIOverloadException
from exceptions.output_exceptions import OutputGenerationException, OutputFormatException, FileCreationException


class TestBaseExceptions:
    """Test cases for base exception classes."""
    
    def test_tax_ai_agent_exception_basic(self):
        """Test basic TaxAIAgentException."""
        exc = TaxAIAgentException("Test error")
        
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.error_code is None
        assert exc.details == {}
    
    def test_tax_ai_agent_exception_with_code(self):
        """Test TaxAIAgentException with error code."""
        exc = TaxAIAgentException("Test error", "TEST_ERROR")
        
        assert str(exc) == "[TEST_ERROR] Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {}
    
    def test_tax_ai_agent_exception_with_details(self):
        """Test TaxAIAgentException with details."""
        details = {"key": "value", "number": 42}
        exc = TaxAIAgentException("Test error", "TEST_ERROR", details)
        
        assert str(exc) == "[TEST_ERROR] Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == details
    
    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException("Invalid input", field="username", value="invalid")
        
        assert str(exc) == "[VALIDATION_ERROR] Invalid input"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.field == "username"
        assert exc.value == "invalid"
    
    def test_configuration_exception(self):
        """Test ConfigurationException."""
        exc = ConfigurationException("Missing config", config_key="API_KEY")
        
        assert str(exc) == "[CONFIG_ERROR] Missing config"
        assert exc.error_code == "CONFIG_ERROR"
        assert exc.config_key == "API_KEY"


class TestDocumentExceptions:
    """Test cases for document processing exceptions."""
    
    def test_document_processing_exception_basic(self):
        """Test basic DocumentProcessingException."""
        exc = DocumentProcessingException("Processing failed")
        
        assert str(exc) == "[DOCUMENT_PROCESSING_ERROR] Processing failed"
        assert exc.error_code == "DOCUMENT_PROCESSING_ERROR"
        assert exc.filename is None
        assert exc.document_type is None
    
    def test_document_processing_exception_with_details(self):
        """Test DocumentProcessingException with details."""
        exc = DocumentProcessingException("Processing failed", "test.txt", "text")
        
        assert str(exc) == "[DOCUMENT_PROCESSING_ERROR] Processing failed"
        assert exc.filename == "test.txt"
        assert exc.document_type == "text"
    
    def test_file_validation_exception(self):
        """Test FileValidationException."""
        exc = FileValidationException("File too large", "large.txt", 10 * 1024 * 1024, "text", "size_limit")
        
        assert str(exc) == "[FILE_VALIDATION_ERROR] File too large"
        assert exc.filename == "large.txt"
        assert exc.file_size == 10 * 1024 * 1024
        assert exc.file_type == "text"
        assert exc.validation_rule == "size_limit"
    
    def test_document_load_exception(self):
        """Test DocumentLoadException."""
        exc = DocumentLoadException("Load failed", "missing.txt", "/path/to/missing.txt", "file_reader")
        
        assert str(exc) == "[DOCUMENT_LOAD_ERROR] Load failed"
        assert exc.filename == "missing.txt"
        assert exc.source_path == "/path/to/missing.txt"
        assert exc.loader_type == "file_reader"


class TestLLMExceptions:
    """Test cases for LLM service exceptions."""
    
    def test_llm_service_exception_basic(self):
        """Test basic LLMServiceException."""
        exc = LLMServiceException("API call failed")
        
        assert str(exc) == "[LLM_SERVICE_ERROR] API call failed"
        assert exc.error_code == "LLM_SERVICE_ERROR"
        assert exc.model is None
        assert exc.request_id is None
    
    def test_llm_service_exception_with_details(self):
        """Test LLMServiceException with details."""
        exc = LLMServiceException("API call failed", "claude-3-sonnet", "req-123")
        
        assert str(exc) == "[LLM_SERVICE_ERROR] API call failed"
        assert exc.model == "claude-3-sonnet"
        assert exc.request_id == "req-123"
    
    def test_llm_rate_limit_exception(self):
        """Test LLMRateLimitException."""
        exc = LLMRateLimitException("Rate limit exceeded", "claude-3-sonnet", "req-123", 60)
        
        assert str(exc) == "[LLM_RATE_LIMIT_ERROR] Rate limit exceeded"
        assert exc.error_code == "LLM_RATE_LIMIT_ERROR"
        assert exc.model == "claude-3-sonnet"
        assert exc.request_id == "req-123"
        assert exc.retry_after == 60
    
    def test_llm_api_overload_exception(self):
        """Test LLMAPIOverloadException."""
        exc = LLMAPIOverloadException("API overloaded", "claude-3-sonnet", "req-123", 30)
        
        assert str(exc) == "[LLM_API_OVERLOAD_ERROR] API overloaded"
        assert exc.error_code == "LLM_API_OVERLOAD_ERROR"
        assert exc.model == "claude-3-sonnet"
        assert exc.request_id == "req-123"
        assert exc.retry_after == 30


class TestOutputExceptions:
    """Test cases for output generation exceptions."""
    
    def test_output_generation_exception_basic(self):
        """Test basic OutputGenerationException."""
        exc = OutputGenerationException("Generation failed")
        
        assert str(exc) == "[OUTPUT_GENERATION_ERROR] Generation failed"
        assert exc.error_code == "OUTPUT_GENERATION_ERROR"
        assert exc.output_format is None
        assert exc.output_path is None
    
    def test_output_generation_exception_with_details(self):
        """Test OutputGenerationException with details."""
        exc = OutputGenerationException("Generation failed", "markdown", "/path/to/output.md")
        
        assert str(exc) == "[OUTPUT_GENERATION_ERROR] Generation failed"
        assert exc.output_format == "markdown"
        assert exc.output_path == "/path/to/output.md"
    
    def test_output_format_exception(self):
        """Test OutputFormatException."""
        exc = OutputFormatException("Unsupported format", "xyz", ["markdown", "csv", "json"])
        
        assert str(exc) == "[OUTPUT_FORMAT_ERROR] Unsupported format"
        assert exc.error_code == "OUTPUT_FORMAT_ERROR"
        assert exc.output_format == "xyz"
        assert exc.supported_formats == ["markdown", "csv", "json"]
    
    def test_file_creation_exception(self):
        """Test FileCreationException."""
        exc = FileCreationException("Cannot create file", "/path/to/file.txt", "write")
        
        assert str(exc) == "[FILE_CREATION_ERROR] Cannot create file"
        assert exc.error_code == "FILE_CREATION_ERROR"
        assert exc.file_path == "/path/to/file.txt"
        assert exc.file_operation == "write"


class TestExceptionInheritance:
    """Test cases for exception inheritance hierarchy."""
    
    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from TaxAIAgentException."""
        base_exceptions = [
            ValidationException,
            ConfigurationException
        ]
        
        document_exceptions = [
            DocumentProcessingException,
            FileValidationException,
            DocumentLoadException
        ]
        
        llm_exceptions = [
            LLMServiceException,
            LLMRateLimitException,
            LLMAPIOverloadException
        ]
        
        output_exceptions = [
            OutputGenerationException,
            OutputFormatException,
            FileCreationException
        ]
        
        all_exceptions = base_exceptions + document_exceptions + llm_exceptions + output_exceptions
        
        for exc_class in all_exceptions:
            assert issubclass(exc_class, TaxAIAgentException), f"{exc_class.__name__} should inherit from TaxAIAgentException"
    
    def test_specific_exception_inheritance(self):
        """Test specific exception inheritance chains."""
        # Document exceptions
        assert issubclass(FileValidationException, DocumentProcessingException)
        assert issubclass(DocumentLoadException, DocumentProcessingException)
        
        # LLM exceptions
        assert issubclass(LLMRateLimitException, LLMServiceException)
        assert issubclass(LLMAPIOverloadException, LLMServiceException)
        
        # Output exceptions
        assert issubclass(OutputFormatException, OutputGenerationException)
        assert issubclass(FileCreationException, OutputGenerationException)


class TestExceptionUsage:
    """Test cases for practical exception usage."""
    
    def test_exception_chaining(self):
        """Test exception chaining with cause."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as original_exc:
                raise DocumentProcessingException("Processing failed") from original_exc
        except DocumentProcessingException as exc:
            assert exc.__cause__ is not None
            assert isinstance(exc.__cause__, ValueError)
            assert str(exc.__cause__) == "Original error"
    
    def test_exception_in_catch_blocks(self):
        """Test catching specific exception types."""
        try:
            raise FileValidationException("File too large", validation_rule="size_limit")
        except DocumentProcessingException:
            # Should catch the more specific exception
            caught = True
        else:
            caught = False
        
        assert caught is True
    
    def test_exception_serialization(self):
        """Test exception serialization for logging."""
        exc = FileValidationException(
            "File too large", 
            "large.txt", 
            10 * 1024 * 1024, 
            "text", 
            "size_limit"
        )
        
        # Test that exception can be converted to dict for logging
        exc_dict = {
            "type": type(exc).__name__,
            "message": str(exc),
            "error_code": exc.error_code,
            "filename": exc.filename,
            "file_size": exc.file_size,
            "file_type": exc.file_type,
            "validation_rule": exc.validation_rule
        }
        
        assert exc_dict["type"] == "FileValidationException"
        assert exc_dict["error_code"] == "FILE_VALIDATION_ERROR"
        assert exc_dict["filename"] == "large.txt"
        assert exc_dict["validation_rule"] == "size_limit"
    
    def test_exception_with_none_values(self):
        """Test exceptions with None optional values."""
        exc = DocumentProcessingException("Processing failed", None, None)
        
        assert exc.filename is None
        assert exc.document_type is None
        assert str(exc) == "[DOCUMENT_PROCESSING_ERROR] Processing failed"
    
    def test_exception_error_codes(self):
        """Test that all exceptions have proper error codes."""
        exceptions_and_codes = [
            (TaxAIAgentException, None),  # Base class doesn't have a fixed code
            (ValidationException, "VALIDATION_ERROR"),
            (ConfigurationException, "CONFIG_ERROR"),
            (DocumentProcessingException, "DOCUMENT_PROCESSING_ERROR"),
            (FileValidationException, "FILE_VALIDATION_ERROR"),
            (DocumentLoadException, "DOCUMENT_LOAD_ERROR"),
            (LLMServiceException, "LLM_SERVICE_ERROR"),
            (LLMRateLimitException, "LLM_RATE_LIMIT_ERROR"),
            (LLMAPIOverloadException, "LLM_API_OVERLOAD_ERROR"),
            (OutputGenerationException, "OUTPUT_GENERATION_ERROR"),
            (OutputFormatException, "OUTPUT_FORMAT_ERROR"),
            (FileCreationException, "FILE_CREATION_ERROR")
        ]
        
        for exc_class, expected_code in exceptions_and_codes:
            if expected_code is not None:
                exc = exc_class("Test message")
                assert exc.error_code == expected_code, f"{exc_class.__name__} should have error code {expected_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

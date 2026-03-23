"""Output generation related exceptions."""

from .base_exceptions import TaxAIAgentException


class OutputGenerationException(TaxAIAgentException):
    """Raised when output generation fails."""
    
    def __init__(self, message: str, output_format: str = None, 
                 output_path: str = None):
        super().__init__(message, "OUTPUT_GENERATION_ERROR")
        self.output_format = output_format
        self.output_path = output_path


class OutputFormatException(OutputGenerationException):
    """Raised when output format is invalid or unsupported."""
    
    def __init__(self, message: str, output_format: str = None, 
                 supported_formats: list = None):
        super().__init__(message, output_format)
        self.error_code = "OUTPUT_FORMAT_ERROR"
        self.supported_formats = supported_formats or []


class FileCreationException(OutputGenerationException):
    """Raised when file creation fails."""
    
    def __init__(self, message: str, file_path: str = None, 
                 file_operation: str = None):
        super().__init__(message, None, file_path)
        self.error_code = "FILE_CREATION_ERROR"
        self.file_operation = file_operation

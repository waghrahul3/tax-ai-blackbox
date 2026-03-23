"""Document processing related exceptions."""

from .base_exceptions import TaxAIAgentException


class DocumentProcessingException(TaxAIAgentException):
    """Raised when document processing fails."""
    
    def __init__(self, message: str, filename: str = None, document_type: str = None):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR")
        self.filename = filename
        self.document_type = document_type


class FileValidationException(DocumentProcessingException):
    """Raised when file validation fails."""
    
    def __init__(self, message: str, filename: str = None, file_size: int = None, 
                 file_type: str = None, validation_rule: str = None):
        super().__init__(message, filename, file_type)
        self.error_code = "FILE_VALIDATION_ERROR"
        self.file_size = file_size
        self.validation_rule = validation_rule


class PasswordProtectedPDFException(DocumentProcessingException):
    """Raised when password-protected PDF processing fails."""
    
    def __init__(self, message: str, filename: str = None, error_code: str = None):
        super().__init__(message, filename, "password_protected_pdf")
        self.error_code = error_code or "PASSWORD_PROTECTED_PDF_ERROR"


class DocumentLoadException(DocumentProcessingException):
    """Raised when document loading fails."""
    
    def __init__(self, message: str, filename: str = None, source_path: str = None, 
                 loader_type: str = None):
        super().__init__(message, filename, "load_error")
        self.error_code = "DOCUMENT_LOAD_ERROR"
        self.source_path = source_path
        self.loader_type = loader_type

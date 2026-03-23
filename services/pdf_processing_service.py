"""PDF processing service for handling password-protected PDFs."""

from typing import Optional, Tuple
from dataclasses import dataclass

from config.pdf_config import get_pdf_config
from utils.password_extractor import extract_password_from_filename
from utils.pdf_extractor import extract_text_from_pdf, create_decrypted_pdf_copy
from utils.temp_file_manager import get_temp_manager
from utils.logger import get_logger
from exceptions.document_exceptions import PasswordProtectedPDFException
from models.document import DocumentContent

logger = get_logger(__name__)


@dataclass
class PDFProcessingResult:
    """Result of PDF processing operations."""
    
    text_content: str
    source_path: str
    password_processed: bool
    has_decrypted_copy: bool
    original_size: int
    decrypted_size: Optional[int] = None


class PDFProcessingService:
    """Service for processing PDF files with password support."""
    
    def __init__(self):
        self.config = get_pdf_config()
        self.temp_manager = get_temp_manager()
    
    def process_pdf(self, filename: str, data: bytes, original_path: str) -> PDFProcessingResult:
        """
        Process a PDF file, handling password protection and creating decrypted copies.
        
        Args:
            filename: Original filename
            data: PDF file data as bytes
            original_path: Original file path
            
        Returns:
            PDFProcessingResult with processing details
            
        Raises:
            PasswordProtectedPDFException: If password processing fails
        """
        logger.info(
            "Starting PDF processing",
            extra={
                "filename": filename,
                "size": len(data),
                "password_extraction_enabled": self.config.enable_password_extraction
            }
        )
        
        # Validate file size
        if len(data) > self.config.get_max_pdf_size_bytes():
            raise PasswordProtectedPDFException(
                f"PDF file too large (max {self.config.max_pdf_size_mb}MB)",
                filename=filename,
                error_code="file_too_large"
            )
        
        # Extract password if enabled
        password = None
        password_processed = False
        
        if self.config.enable_password_extraction:
            password = extract_password_from_filename(filename)
            password_processed = password is not None
            
            if password_processed:
                logger.info(
                    "Password extracted from filename",
                    extra={
                        "filename": filename,
                        "password_length": len(password)
                    }
                )
        
        # Extract text content
        try:
            text_content = extract_text_from_pdf(data, password)
            
            if not text_content.strip():
                logger.warning(
                    "PDF text extraction returned empty content",
                    extra={"filename": filename, "password_provided": password_processed}
                )
                text_content = ""
            
        except PasswordProtectedPDFException:
            # Re-raise password-related exceptions
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during PDF text extraction",
                extra={"filename": filename, "error": str(e)}
            )
            raise PasswordProtectedPDFException(
                "PDF processing failed",
                filename=filename,
                error_code="processing_failed"
            )
        
        # Create decrypted copy if password was used
        decrypted_path = original_path
        has_decrypted_copy = False
        decrypted_size = None
        
        if password_processed and password:
            try:
                decrypted_path, decrypted_size = self._create_decrypted_copy(
                    data, password, filename
                )
                has_decrypted_copy = True
                
                logger.info(
                    "Successfully created decrypted PDF copy",
                    extra={
                        "filename": filename,
                        "original_size": len(data),
                        "decrypted_size": decrypted_size,
                        "decrypted_path": decrypted_path
                    }
                )
                
            except Exception as e:
                if self.config.enable_decryption_fallback:
                    logger.warning(
                        "Failed to create decrypted copy, using original path",
                        extra={
                            "filename": filename,
                            "error": str(e)
                        }
                    )
                    decrypted_path = original_path
                    has_decrypted_copy = False
                else:
                    logger.error(
                        "Decryption failed and fallback disabled",
                        extra={"filename": filename, "error": str(e)}
                    )
                    raise PasswordProtectedPDFException(
                        "PDF decryption failed",
                        filename=filename,
                        error_code="decryption_failed"
                    )
        
        result = PDFProcessingResult(
            text_content=text_content,
            source_path=decrypted_path,
            password_processed=password_processed,
            has_decrypted_copy=has_decrypted_copy,
            original_size=len(data),
            decrypted_size=decrypted_size
        )
        
        logger.info(
            "PDF processing completed",
            extra={
                "filename": filename,
                "text_length": len(text_content),
                "password_processed": password_processed,
                "has_decrypted_copy": has_decrypted_copy
            }
        )
        
        return result
    
    def _create_decrypted_copy(self, data: bytes, password: str, filename: str) -> Tuple[str, int]:
        """
        Create a decrypted copy of a password-protected PDF.
        
        Args:
            data: Original PDF data
            password: Password for decryption
            filename: Original filename
            
        Returns:
            Tuple of (decrypted_file_path, decrypted_file_size)
            
        Raises:
            PasswordProtectedPDFException: If decryption fails
        """
        try:
            # Create decrypted data
            decrypted_data = create_decrypted_pdf_copy(data, password)
            
            # Create temporary file for decrypted copy
            decrypted_path = self.temp_manager.create_decrypted_pdf(
                purpose=f"decrypted_{filename}"
            )
            
            # Write decrypted data to file
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)
            
            return decrypted_path, len(decrypted_data)
            
        except PasswordProtectedPDFException:
            raise
        except Exception as e:
            logger.error(
                "Failed to create decrypted PDF copy",
                extra={"filename": filename, "error": str(e)}
            )
            raise PasswordProtectedPDFException(
                "Failed to create decrypted copy",
                filename=filename,
                error_code="decryption_failed"
            )
    
    def create_document_content(
        self, 
        filename: str, 
        result: PDFProcessingResult, 
        original_path: str,
        media_type: str = "application/pdf"
    ) -> DocumentContent:
        """
        Create DocumentContent from processing result.
        
        Args:
            filename: Original filename
            result: PDF processing result
            original_path: Original file path
            media_type: Media type for the document
            
        Returns:
            DocumentContent instance
        """
        return DocumentContent(
            content_type="text",
            filename=filename,
            text_content=result.text_content,
            source_path=result.source_path,
            source_media_type=media_type,
            password_processed=result.password_processed
        )
    
    def is_decrypted_file(self, file_path: str) -> bool:
        """Check if a file path points to a decrypted copy."""
        return self.config.is_decrypted_file(file_path)


# Global service instance
_pdf_service: Optional[PDFProcessingService] = None


def get_pdf_service() -> PDFProcessingService:
    """Get the global PDF processing service instance."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFProcessingService()
    return _pdf_service


def reset_pdf_service() -> None:
    """Reset the PDF processing service (mainly for testing)."""
    global _pdf_service
    _pdf_service = None

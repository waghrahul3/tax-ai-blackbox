"""Test cases for PDF Processing Service."""

import os
import pytest
from unittest.mock import patch, MagicMock

from services.pdf_processing_service import (
    PDFProcessingService,
    PDFProcessingResult,
    get_pdf_service,
    reset_pdf_service
)
from config.pdf_config import reset_pdf_config
from exceptions.document_exceptions import PasswordProtectedPDFException


class TestPDFProcessingService:
    """Test PDF processing service functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Reset configurations
        reset_pdf_config()
        reset_pdf_service()
        
        # Set up test environment
        os.environ["PDF_PASSWORD_PATTERNS"] = "_password_,_pwd_,_secure_"
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "true"
        os.environ["PDF_PATTERN_CASE_SENSITIVE"] = "false"
        os.environ["MAX_PDF_SIZE_MB"] = "50"
        os.environ["ENABLE_DECRYPTION_FALLBACK"] = "true"

    def test_service_initialization(self):
        """Test service initialization."""
        service = PDFProcessingService()
        
        assert service.config is not None
        assert service.temp_manager is not None
        assert service.config.enable_password_extraction is True
        assert service.config.max_pdf_size_mb == 50

    def test_process_normal_pdf(self):
        """Test processing a normal PDF without password."""
        service = PDFProcessingService()
        filename = "normal_document.pdf"
        data = b"fake pdf data"
        original_path = "/tmp/normal_document.pdf"
        
        with patch('services.pdf_processing_service.extract_text_from_pdf', return_value="Extracted text content"):
            result = service.process_pdf(filename, data, original_path)
            
            assert isinstance(result, PDFProcessingResult)
            assert result.text_content == "Extracted text content"
            assert result.source_path == original_path
            assert result.password_processed is False
            assert result.has_decrypted_copy is False
            assert result.original_size == len(data)

    def test_process_password_protected_pdf(self):
        """Test processing a password-protected PDF."""
        service = PDFProcessingService()
        filename = "file_password_secret123.pdf"
        data = b"encrypted pdf data"
        original_path = "/tmp/file_password_secret123.pdf"
        
        with patch('services.pdf_processing_service.extract_text_from_pdf', return_value="Decrypted text content") as mock_extract:
            with patch('services.pdf_processing_service.create_decrypted_pdf_copy', return_value=b"decrypted data") as mock_decrypt:
                with patch.object(service.temp_manager, 'create_decrypted_pdf', return_value="/tmp/decrypted_copy.pdf"):
                    
                    result = service.process_pdf(filename, data, original_path)
                    
                    assert result.password_processed is True
                    assert result.has_decrypted_copy is True
                    assert result.text_content == "Decrypted text content"
                    assert result.decrypted_size == len(b"decrypted data")
                    
                    # Verify methods were called with password
                    mock_extract.assert_called_once_with(data, "secret123")
                    mock_decrypt.assert_called_once_with(data, "secret123")

    def test_process_pdf_too_large(self):
        """Test processing a PDF that's too large."""
        service = PDFProcessingService()
        filename = "large_document.pdf"
        # Create data larger than limit
        data = b"x" * (51 * 1024 * 1024)  # 51MB
        original_path = "/tmp/large_document.pdf"
        
        with pytest.raises(PasswordProtectedPDFException) as exc_info:
            service.process_pdf(filename, data, original_path)
        
        assert exc_info.value.error_code == "file_too_large"
        assert "too large" in str(exc_info.value).lower()

    def test_process_pdf_decryption_failure_with_fallback(self):
        """Test processing PDF when decryption fails but fallback is enabled."""
        service = PDFProcessingService()
        filename = "file_password_secret123.pdf"
        data = b"encrypted pdf data"
        original_path = "/tmp/file_password_secret123.pdf"
        
        with patch('services.pdf_processing_service.extract_text_from_pdf', return_value="Extracted text"):
            with patch('services.pdf_processing_service.create_decrypted_pdf_copy', side_effect=Exception("Decryption failed")):
                
                result = service.process_pdf(filename, data, original_path)
                
                # Should fallback to original path and no decrypted copy
                assert result.password_processed is True
                assert result.has_decrypted_copy is False
                assert result.source_path == original_path
                assert result.text_content == "Extracted text"

    def test_process_pdf_decryption_failure_no_fallback(self):
        """Test processing PDF when decryption fails and fallback is disabled."""
        os.environ["ENABLE_DECRYPTION_FALLBACK"] = "false"
        reset_pdf_config()
        
        service = PDFProcessingService()
        filename = "file_password_secret123.pdf"
        data = b"encrypted pdf data"
        original_path = "/tmp/file_password_secret123.pdf"
        
        with patch('services.pdf_processing_service.extract_text_from_pdf', return_value="Extracted text"):
            with patch('services.pdf_processing_service.create_decrypted_pdf_copy', side_effect=Exception("Decryption failed")):
                
                with pytest.raises(PasswordProtectedPDFException) as exc_info:
                    service.process_pdf(filename, data, original_path)
                
                assert exc_info.value.error_code == "decryption_failed"

    def test_create_document_content(self):
        """Test creating DocumentContent from processing result."""
        service = PDFProcessingService()
        
        result = PDFProcessingResult(
            text_content="Sample text",
            source_path="/tmp/document.pdf",
            password_processed=True,
            has_decrypted_copy=True,
            original_size=1024,
            decrypted_size=1000
        )
        
        doc_content = service.create_document_content(
            filename="test.pdf",
            result=result,
            original_path="/tmp/original.pdf",
            media_type="application/pdf"
        )
        
        assert doc_content.filename == "test.pdf"
        assert doc_content.text_content == "Sample text"
        assert doc_content.source_path == "/tmp/document.pdf"
        assert doc_content.source_media_type == "application/pdf"
        assert doc_content.password_processed is True

    def test_is_decrypted_file(self):
        """Test checking if file is a decrypted copy."""
        service = PDFProcessingService()
        
        assert service.is_decrypted_file("/tmp/document_decrypted.pdf") is True
        assert service.is_decrypted_file("/tmp/document.pdf") is False
        assert service.is_decrypted_file("/tmp/document_decrypted.pdf") is True
        assert service.is_decrypted_file("/tmp/other_file.txt") is False

    def test_get_pdf_service_singleton(self):
        """Test that get_pdf_service returns singleton instance."""
        service1 = get_pdf_service()
        service2 = get_pdf_service()
        
        assert service1 is service2
        assert isinstance(service1, PDFProcessingService)

    def test_reset_pdf_service(self):
        """Test resetting PDF service."""
        service1 = get_pdf_service()
        reset_pdf_service()
        service2 = get_pdf_service()
        
        assert service1 is not service2

    def test_process_pdf_with_empty_text(self):
        """Test processing PDF that returns empty text."""
        service = PDFProcessingService()
        filename = "empty_document.pdf"
        data = b"pdf with no text"
        original_path = "/tmp/empty_document.pdf"
        
        with patch('services.pdf_processing_service.extract_text_from_pdf', return_value=""):
            result = service.process_pdf(filename, data, original_path)
            
            assert result.text_content == ""
            assert result.password_processed is False

    def test_process_pdf_extraction_exception(self):
        """Test processing PDF when extraction raises PasswordProtectedPDFException."""
        service = PDFProcessingService()
        filename = "protected_document.pdf"
        data = b"protected pdf data"
        original_path = "/tmp/protected_document.pdf"
        
        with patch('services.pdf_processing_service.extract_text_from_pdf', 
                  side_effect=PasswordProtectedPDFException("Password required", error_code="password_required")):
            
            with pytest.raises(PasswordProtectedPDFException) as exc_info:
                service.process_pdf(filename, data, original_path)
            
            assert exc_info.value.error_code == "password_required"

    def test_process_pdf_general_exception(self):
        """Test processing PDF when extraction raises general exception."""
        service = PDFProcessingService()
        filename = "corrupt_document.pdf"
        data = b"corrupt pdf data"
        original_path = "/tmp/corrupt_document.pdf"
        
        with patch('services.pdf_processing_service.extract_text_from_pdf', side_effect=Exception("General error")):
            
            with pytest.raises(PasswordProtectedPDFException) as exc_info:
                service.process_pdf(filename, data, original_path)
            
            assert exc_info.value.error_code == "processing_failed"

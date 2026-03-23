"""Integration tests for password-protected PDF functionality."""

import os
import pytest
from unittest.mock import patch, MagicMock

from exceptions.document_exceptions import PasswordProtectedPDFException


class TestPasswordPDFIntegration:
    """Integration tests for password-protected PDF processing."""

    def setup_method(self):
        """Set up test environment."""
        # Set up password extraction environment
        os.environ["PDF_PASSWORD_PATTERNS"] = "_password_,_pwd_,_secure_"
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "true"
        os.environ["PDF_PATTERN_CASE_SENSITIVE"] = "false"

    def create_mock_file(self, filename, content_type="application/pdf", data=b"test"):
        """Create a mock file object."""
        mock_file = MagicMock()
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.file_path = f"/tmp/{filename}"
        mock_file.read.return_value = data
        return mock_file

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage._looks_like_pdf')
    def test_normal_pdf_processing(self, mock_looks_like_pdf, mock_extract_text):
        """Test processing of normal (non-protected) PDF."""
        mock_looks_like_pdf.return_value = True
        mock_extract_text.return_value = "Normal PDF content"
        
        mock_file = self.create_mock_file("normal.pdf")
        mock_file.read.return_value = b"pdf data"
        
        result = self.storage.read_file(mock_file)
        
        assert result.content_type == "text"
        assert result.text_content == "Normal PDF content"
        assert result.filename == "normal.pdf"

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_password_protected_pdf_success(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test successful processing of password-protected PDF."""
        mock_looks_like_pdf.return_value = True
        mock_extract_password.return_value = "secret123"
        mock_extract_text.return_value = "Protected PDF content"
        
        mock_file = self.create_mock_file("file_password_secret123.pdf")
        mock_file.read.return_value = b"encrypted pdf data"
        
        result = self.storage.read_file(mock_file)
        
        assert result.content_type == "text"
        assert result.text_content == "Protected PDF content"
        mock_extract_password.assert_called_once_with("file_password_secret123.pdf")
        mock_extract_text.assert_called_once_with(b"encrypted pdf data", "secret123")

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_password_protected_pdf_no_password_in_filename(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test password-protected PDF with no password in filename."""
        mock_looks_like_pdf.return_value = True
        mock_extract_password.return_value = None
        mock_extract_text.side_effect = PasswordProtectedPDFException("Password required", error_code="password_required")
        
        mock_file = self.create_mock_file("protected.pdf")
        mock_file.read.return_value = b"encrypted pdf data"
        
        with pytest.raises(PasswordProtectedPDFException) as exc_info:
            self.storage.read_file(mock_file)
        
        assert exc_info.value.error_code == "password_required"
        mock_extract_password.assert_called_once_with("protected.pdf")

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_password_protected_pdf_wrong_password(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test password-protected PDF with wrong password from filename."""
        mock_looks_like_pdf.return_value = True
        mock_extract_password.return_value = "wrongpass"
        mock_extract_text.side_effect = PasswordProtectedPDFException("Wrong password", error_code="wrong_password")
        
        mock_file = self.create_mock_file("file_password_wrongpass.pdf")
        mock_file.read.return_value = b"encrypted pdf data"
        
        with pytest.raises(PasswordProtectedPDFException) as exc_info:
            self.storage.read_file(mock_file)
        
        assert exc_info.value.error_code == "wrong_password"

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_password_protected_pdf_invalid_pdf(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test invalid/corrupted PDF."""
        mock_looks_like_pdf.return_value = True
        mock_extract_password.return_value = "anypass"
        mock_extract_text.side_effect = PasswordProtectedPDFException("Invalid PDF", error_code="invalid_pdf")
        
        mock_file = self.create_mock_file("corrupted_password_anypass.pdf")
        mock_file.read.return_value = b"corrupted data"
        
        with pytest.raises(PasswordProtectedPDFException) as exc_info:
            self.storage.read_file(mock_file)
        
        assert exc_info.value.error_code == "invalid_pdf"

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_password_extraction_disabled(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test behavior when password extraction is disabled."""
        # Disable password extraction
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "false"
        
        mock_looks_like_pdf.return_value = True
        mock_extract_password.return_value = None  # Should not be called
        mock_extract_text.return_value = "PDF content"
        
        mock_file = self.create_mock_file("file_password_secret123.pdf")
        mock_file.read.return_value = b"pdf data"
        
        result = self.storage.read_file(mock_file)
        
        assert result.content_type == "text"
        assert result.text_content == "PDF content"
        # Password extraction should not be called when disabled
        mock_extract_password.assert_not_called()

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_multiple_password_patterns(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test multiple password patterns."""
        mock_looks_like_pdf.return_value = True
        mock_extract_password.side_effect = lambda filename: {
            "file_password_secret123.pdf": "secret123",
            "document_pwd_abc456.pdf": "abc456",
            "tax_secure_myPass789.pdf": "myPass789"
        }.get(filename)
        mock_extract_text.return_value = "PDF content"
        
        test_files = [
            ("file_password_secret123.pdf", "secret123"),
            ("document_pwd_abc456.pdf", "abc456"),
            ("tax_secure_myPass789.pdf", "myPass789")
        ]
        
        for filename, expected_password in test_files:
            mock_file = self.create_mock_file(filename)
            mock_file.read.return_value = b"pdf data"
            
            result = self.storage.read_file(mock_file)
            
            assert result.content_type == "text"
            assert result.text_content == "PDF content"
            mock_extract_text.assert_called_with(b"pdf data", expected_password)

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_case_insensitive_patterns(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test case-insensitive password patterns."""
        mock_looks_like_pdf.return_value = True
        mock_extract_password.side_effect = lambda filename: {
            "file_PASSWORD_secret123.pdf": "secret123",
            "document_PWD_abc456.pdf": "abc456",
            "tax_SECURE_myPass789.pdf": "myPass789"
        }.get(filename)
        mock_extract_text.return_value = "PDF content"
        
        test_files = [
            "file_PASSWORD_secret123.pdf",
            "document_PWD_abc456.pdf", 
            "tax_SECURE_myPass789.pdf"
        ]
        
        for filename in test_files:
            mock_file = self.create_mock_file(filename)
            mock_file.read.return_value = b"pdf data"
            
            result = self.storage.read_file(mock_file)
            
            assert result.content_type == "text"
            assert result.text_content == "PDF content"

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_document_processing_service_integration(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test integration with document processing service."""
        mock_looks_like_pdf.return_value = True
        mock_extract_password.return_value = "secret123"
        mock_extract_text.return_value = "Protected PDF content"
        
        mock_file = self.create_mock_file("file_password_secret123.pdf")
        mock_file.read.return_value = b"encrypted pdf data"
        
        # Mock the storage read_file method
        with patch.object(self.storage, 'read_file') as mock_read_file:
            mock_doc = MagicMock()
            mock_doc.content_type = "text"
            mock_doc.text_content = "Protected PDF content"
            mock_doc.is_text.return_value = True
            mock_doc.is_image.return_value = False
            mock_doc.get_display_info.return_value = {"filename": "file_password_secret123.pdf"}
            mock_read_file.return_value = mock_doc
            
            documents = self.doc_service.load_documents([mock_file])
            
            assert len(documents) == 1
            assert documents[0].text_content == "Protected PDF content"

    @patch('storage.local_storage.extract_text_from_pdf')
    @patch('storage.local_storage.extract_password_from_filename')
    @patch('storage.local_storage._looks_like_pdf')
    def test_document_processing_service_password_error(self, mock_looks_like_pdf, mock_extract_password, mock_extract_text):
        """Test document processing service handling password errors."""
        mock_looks_like_pdf.return_value = True
        mock_extract_password.return_value = None
        mock_extract_text.side_effect = PasswordProtectedPDFException("Password required", error_code="password_required")
        
        mock_file = self.create_mock_file("protected.pdf")
        mock_file.read.return_value = b"encrypted pdf data"
        
        # Mock the storage read_file method to raise password exception
        with patch.object(self.storage, 'read_file', side_effect=PasswordProtectedPDFException("Password required", error_code="password_required")):
            with pytest.raises(PasswordProtectedPDFException) as exc_info:
                self.doc_service.load_documents([mock_file])
            
            assert exc_info.value.error_code == "password_required"

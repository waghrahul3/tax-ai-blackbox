"""Test cases for PDF extraction with password support."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from utils.pdf_extractor import extract_text_from_pdf
from exceptions.document_exceptions import PasswordProtectedPDFException


class TestPDFExtractor:
    """Test PDF extraction with password support."""

    def test_extract_text_normal_pdf(self):
        """Test extracting text from normal (non-protected) PDF."""
        # Create a mock PDF content
        mock_pdf_data = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"
        
        # Mock PyMuPDFLoader to return some text
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            mock_doc = MagicMock()
            mock_doc.page_content = "Sample PDF content"
            mock_loader.return_value.load.return_value = [mock_doc]
            
            result = extract_text_from_pdf(mock_pdf_data)
            assert result == "Sample PDF content"
            
            # Verify loader was called without password
            mock_loader.assert_called_once()
            call_args = mock_loader.call_args
            assert 'password' not in call_args.kwargs or call_args.kwargs.get('password') is None

    def test_extract_text_protected_pdf_with_password(self):
        """Test extracting text from password-protected PDF with correct password."""
        mock_pdf_data = b"%PDF-1.4\nencrypted content\n"
        password = "test123"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            mock_doc = MagicMock()
            mock_doc.page_content = "Protected PDF content"
            mock_loader.return_value.load.return_value = [mock_doc]
            
            result = extract_text_from_pdf(mock_pdf_data, password)
            assert result == "Protected PDF content"
            
            # Verify loader was called with password
            mock_loader.assert_called_once()
            call_args = mock_loader.call_args
            assert call_args.kwargs.get('password') == password

    def test_extract_text_protected_pdf_no_password(self):
        """Test extracting text from password-protected PDF without password."""
        mock_pdf_data = b"%PDF-1.4\nencrypted content\n"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            # Simulate password error
            mock_loader.side_effect = Exception("password required")
            
            with pytest.raises(PasswordProtectedPDFException) as exc_info:
                extract_text_from_pdf(mock_pdf_data)
            
            assert exc_info.value.error_code == "password_required"

    def test_extract_text_protected_pdf_wrong_password(self):
        """Test extracting text from password-protected PDF with wrong password."""
        mock_pdf_data = b"%PDF-1.4\nencrypted content\n"
        wrong_password = "wrongpass"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            # Simulate wrong password error
            mock_loader.side_effect = Exception("invalid password")
            
            with pytest.raises(PasswordProtectedPDFException) as exc_info:
                extract_text_from_pdf(mock_pdf_data, wrong_password)
            
            assert exc_info.value.error_code == "wrong_password"

    def test_extract_text_corrupted_pdf(self):
        """Test extracting text from corrupted PDF."""
        mock_pdf_data = b"corrupted pdf content"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            # Simulate corrupted PDF error
            mock_loader.side_effect = Exception("invalid pdf format")
            
            with pytest.raises(PasswordProtectedPDFException) as exc_info:
                extract_text_from_pdf(mock_pdf_data)
            
            assert exc_info.value.error_code == "invalid_pdf"

    def test_extract_text_various_password_errors(self):
        """Test various password-related error messages."""
        mock_pdf_data = b"%PDF-1.4\nencrypted content\n"
        
        error_messages = [
            "password required",
            "PDF is encrypted",
            "authentication failed",
            "Invalid password provided",
            "This PDF is password protected",
            "Encrypted document"
        ]
        
        for error_msg in error_messages:
            with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
                mock_loader.side_effect = Exception(error_msg)
                
                with pytest.raises(PasswordProtectedPDFException) as exc_info:
                    extract_text_from_pdf(mock_pdf_data)
                
                if "password" in error_msg.lower():
                    assert exc_info.value.error_code == "password_required"

    def test_extract_text_with_password_provided_error(self):
        """Test password errors when password is provided."""
        mock_pdf_data = b"%PDF-1.4\nencrypted content\n"
        password = "test123"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            mock_loader.side_effect = Exception("invalid password")
            
            with pytest.raises(PasswordProtectedPDFException) as exc_info:
                extract_text_from_pdf(mock_pdf_data, password)
            
            assert exc_info.value.error_code == "wrong_password"

    def test_extract_text_empty_pdf(self):
        """Test extracting text from empty PDF."""
        mock_pdf_data = b""
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            mock_doc = MagicMock()
            mock_doc.page_content = ""
            mock_loader.return_value.load.return_value = [mock_doc]
            
            result = extract_text_from_pdf(mock_pdf_data)
            assert result == ""

    def test_extract_text_multiple_pages(self):
        """Test extracting text from multi-page PDF."""
        mock_pdf_data = b"%PDF-1.4\nmulti-page content\n"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            # Create mock documents for multiple pages
            mock_docs = []
            for i in range(3):
                mock_doc = MagicMock()
                mock_doc.page_content = f"Page {i+1} content"
                mock_docs.append(mock_doc)
            
            mock_loader.return_value.load.return_value = mock_docs
            
            result = extract_text_from_pdf(mock_pdf_data)
            expected = "Page 1 content\n\nPage 2 content\n\nPage 3 content"
            assert result == expected

    def test_extract_text_with_empty_pages(self):
        """Test extracting text when some pages are empty."""
        mock_pdf_data = b"%PDF-1.4\nmixed content\n"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            # Create mock documents with some empty pages
            mock_docs = [
                MagicMock(page_content="Page 1 content"),
                MagicMock(page_content=""),  # Empty page
                MagicMock(page_content="   "),  # Whitespace only
                MagicMock(page_content="Page 4 content"),
            ]
            
            mock_loader.return_value.load.return_value = mock_docs
            
            result = extract_text_from_pdf(mock_pdf_data)
            expected = "Page 1 content\n\nPage 4 content"
            assert result == expected

    def test_extract_text_file_cleanup(self):
        """Test that temporary files are cleaned up."""
        mock_pdf_data = b"%PDF-1.4\ntest content\n"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            mock_doc = MagicMock()
            mock_doc.page_content = "Test content"
            mock_loader.return_value.load.return_value = [mock_doc]
            
            # Mock os.unlink to track if it's called
            with patch('utils.pdf_extractor.os.unlink') as mock_unlink:
                extract_text_from_pdf(mock_pdf_data)
                mock_unlink.assert_called_once()

    def test_extract_text_file_cleanup_error(self):
        """Test handling of file cleanup errors."""
        mock_pdf_data = b"%PDF-1.4\ntest content\n"
        
        with patch('utils.pdf_extractor.PyMuPDFLoader') as mock_loader:
            mock_doc = MagicMock()
            mock_doc.page_content = "Test content"
            mock_loader.return_value.load.return_value = [mock_doc]
            
            # Mock os.unlink to raise OSError
            with patch('utils.pdf_extractor.os.unlink', side_effect=OSError("Permission denied")):
                # Should not raise exception despite cleanup error
                result = extract_text_from_pdf(mock_pdf_data)
                assert result == "Test content"

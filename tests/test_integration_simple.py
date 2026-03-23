"""Simple integration tests for password-protected PDF functionality."""

import os
import pytest
from unittest.mock import patch, MagicMock

from config.pdf_config import reset_pdf_config

from exceptions.document_exceptions import PasswordProtectedPDFException


class TestPasswordPDFIntegration:
    """Integration tests for password-protected PDF processing."""

    def setup_method(self):
        """Set up test environment."""
        # Set up password extraction environment
        os.environ["PDF_PASSWORD_PATTERNS"] = "_password_,_pwd_,_secure_"
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "true"
        os.environ["PDF_PATTERN_CASE_SENSITIVE"] = "false"

    def test_password_extraction_flow(self):
        """Test the complete password extraction flow."""
        # Import here to avoid circular imports
        from utils.password_extractor import extract_password_from_filename
        
        # Test password extraction
        password = extract_password_from_filename("file_password_secret123.pdf")
        assert password == "secret123"
        
        # Test no password pattern
        password = extract_password_from_filename("normal.pdf")
        assert password is None

    @patch('utils.pdf_extractor.PyMuPDFLoader')
    def test_pdf_extractor_with_password(self, mock_loader):
        """Test PDF extractor with password."""
        from utils.pdf_extractor import extract_text_from_pdf
        
        # Mock successful extraction with password
        mock_doc = MagicMock()
        mock_doc.page_content = "Protected content"
        mock_loader.return_value.load.return_value = [mock_doc]
        
        result = extract_text_from_pdf(b"pdf data", "secret123")
        assert result == "Protected content"
        
        # Verify loader was called with password
        mock_loader.assert_called_once()
        call_args = mock_loader.call_args
        assert call_args.kwargs.get('password') == "secret123"

    @patch('utils.pdf_extractor.PyMuPDFLoader')
    def test_pdf_extractor_password_required(self, mock_loader):
        """Test PDF extractor when password is required."""
        from utils.pdf_extractor import extract_text_from_pdf
        
        # Mock password required error
        mock_loader.side_effect = Exception("password required")
        
        with pytest.raises(PasswordProtectedPDFException) as exc_info:
            extract_text_from_pdf(b"encrypted pdf data")
        
        assert exc_info.value.error_code == "password_required"

    @patch('utils.pdf_extractor.PyMuPDFLoader')
    def test_pdf_extractor_wrong_password(self, mock_loader):
        """Test PDF extractor with wrong password."""
        from utils.pdf_extractor import extract_text_from_pdf
        
        # Mock wrong password error
        mock_loader.side_effect = Exception("invalid password")
        
        with pytest.raises(PasswordProtectedPDFException) as exc_info:
            extract_text_from_pdf(b"encrypted pdf data", "wrongpass")
        
        assert exc_info.value.error_code == "wrong_password"

    def test_password_extractor_case_insensitive(self):
        """Test case-insensitive password extraction."""
        from utils.password_extractor import extract_password_from_filename
        
        test_cases = [
            ("file_PASSWORD_secret123.pdf", "secret123"),
            ("document_PWD_abc456.pdf", "abc456"),
            ("tax_SECURE_myPass789.pdf", "myPass789"),
        ]
        
        for filename, expected in test_cases:
            result = extract_password_from_filename(filename)
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"

    def test_password_extractor_custom_patterns(self):
        """Test custom password patterns."""
        from utils.password_extractor import extract_password_from_filename
        
        # Reset configuration to pick up new environment variable
        reset_pdf_config()
        
        # Set custom patterns
        os.environ["PDF_PASSWORD_PATTERNS"] = "_secret_,_key_,_code_"
        test_cases = [
            ("file_secret_mysecret.pdf", "mysecret"),
            ("document_key_123abc.pdf", "123abc"),
            ("tax_code_CODE456.pdf", "CODE456"),
        ]
        
        for filename, expected in test_cases:
            result = extract_password_from_filename(filename)
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"

    def test_password_extractor_disabled(self):
        """Test password extraction when disabled."""
        from utils.password_extractor import extract_password_from_filename
        
        # Reset configuration to pick up new environment variable
        reset_pdf_config()
        
        # Disable password extraction
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "false"
        
        result = extract_password_from_filename("file_password_secret123.pdf")
        assert result is None

    def test_error_codes_consistency(self):
        """Test that error codes are consistent across the system."""
        expected_error_codes = ["password_required", "wrong_password", "invalid_pdf"]
        
        # Test exception creation
        for error_code in expected_error_codes:
            exception = PasswordProtectedPDFException("Test error", error_code=error_code)
            assert exception.error_code == error_code
            assert exception.filename is None  # Default value

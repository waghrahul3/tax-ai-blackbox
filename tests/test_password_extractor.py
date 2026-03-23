"""Test cases for password extraction functionality."""

import os
import pytest
from unittest.mock import patch

from utils.password_extractor import (
    extract_password_from_filename,
    get_supported_patterns,
    is_password_extraction_enabled,
    _extract_with_pattern
)
from config.pdf_config import reset_pdf_config


class TestPasswordExtractor:
    """Test password extraction from filenames."""

    def setup_method(self):
        """Set up test environment."""
        # Set default test environment
        os.environ["PDF_PASSWORD_PATTERNS"] = "_password_,_pwd_,_secure_"
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "true"
        os.environ["PDF_PATTERN_CASE_SENSITIVE"] = "false"

    def test_extract_password_basic_patterns(self):
        """Test basic password extraction patterns."""
        test_cases = [
            ("ElizabethDelleman_T4_2025_password_del05151997.pdf", "del05151997"),
            ("document_pwd_abc456.pdf", "abc456"),
            ("tax_secure_myPass789.pdf", "myPass789"),
            ("file_password_secret123.pdf", "secret123"),
        ]
        
        for filename, expected in test_cases:
            result = extract_password_from_filename(filename)
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"

    def test_extract_password_case_insensitive(self):
        """Test case-insensitive pattern matching."""
        test_cases = [
            ("file_PASSWORD_secret123.pdf", "secret123"),
            ("document_PWD_abc456.pdf", "abc456"),
            ("tax_SECURE_myPass789.pdf", "myPass789"),
            ("FILE_PASSWORD_UPPER.pdf", "UPPER"),
        ]
        
        for filename, expected in test_cases:
            result = extract_password_from_filename(filename)
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"

    def test_extract_password_case_sensitive(self):
        """Test case-sensitive pattern matching."""
        # Reset configuration to pick up new environment variable
        reset_pdf_config()
        
        # Enable case-sensitive matching
        os.environ["PDF_PATTERN_CASE_SENSITIVE"] = "true"
        
        # Should work with exact case
        result = extract_password_from_filename("file_password_secret123.pdf")
        assert result == "secret123"
        
        # Should not work with different case
        result = extract_password_from_filename("file_PASSWORD_secret123.pdf")
        assert result is None

    def test_extract_password_no_pattern(self):
        """Test filenames without password patterns."""
        test_cases = [
            "normal_file.pdf",
            "document.pdf",
            "tax_return.pdf",
            "file_without_password.pdf",
        ]
        
        for filename in test_cases:
            result = extract_password_from_filename(filename)
            assert result is None, f"Expected None for {filename}, got {result}"

    def test_extract_password_empty_password(self):
        """Test filenames with empty password after pattern."""
        test_cases = [
            "file_password_.pdf",
            "document_pwd_.pdf",
            "tax_secure_.pdf",
        ]
        
        for filename in test_cases:
            result = extract_password_from_filename(filename)
            assert result is None, f"Expected None for {filename}, got {result}"

    def test_extract_password_edge_cases(self):
        """Test edge cases for password extraction."""
        test_cases = [
            ("", None),  # Empty filename
            (None, None),  # None filename
            ("file.pdf", None),  # No password pattern
            ("file_password", None),  # No underscore after password
            ("file_password_.pdf", None),  # Empty password after pattern
            ("file_password.pdf.txt", None),  # Multiple extensions - no pattern match
            ("file_password_secret.pdf", "secret"),  # Standard case with password
        ]
        
        for filename, expected in test_cases:
            result = extract_password_from_filename(filename)
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"

    def test_extract_password_disabled(self):
        """Test password extraction when disabled."""
        # Reset configuration to pick up new environment variable
        reset_pdf_config()
        
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "false"
        
        result = extract_password_from_filename("file_password_secret123.pdf")
        assert result is None

    def test_extract_password_custom_patterns(self):
        """Test custom password patterns."""
        # Reset configuration to pick up new environment variable
        reset_pdf_config()
        
        os.environ["PDF_PASSWORD_PATTERNS"] = "_secret_,_key_,_code_"
        
        test_cases = [
            ("file_secret_mysecret.pdf", "mysecret"),
            ("document_key_123abc.pdf", "123abc"),
            ("tax_code_CODE456.pdf", "CODE456"),
        ]
        
        for filename, expected in test_cases:
            result = extract_password_from_filename(filename)
            assert result == expected, f"Failed for {filename}: expected {expected}, got {result}"

    def test_get_supported_patterns(self):
        """Test getting supported patterns."""
        # Reset configuration to ensure clean state
        reset_pdf_config()
        
        patterns = get_supported_patterns()
        expected = ["_password_", "_pwd_", "_secure_"]
        assert patterns == expected

    def test_get_supported_patterns_custom(self):
        """Test getting supported custom patterns."""
        # Reset configuration to pick up new environment variable
        reset_pdf_config()
        
        os.environ["PDF_PASSWORD_PATTERNS"] = "_secret_,_key_"
        patterns = get_supported_patterns()
        expected = ["_secret_", "_key_"]
        assert patterns == expected

    def test_is_password_extraction_enabled(self):
        """Test checking if password extraction is enabled."""
        assert is_password_extraction_enabled() is True
        
        # Reset configuration to pick up new environment variable
        reset_pdf_config()
        
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "false"
        assert is_password_extraction_enabled() is False

    def test_extract_with_pattern(self):
        """Test individual pattern extraction."""
        # Test case-insensitive
        result = _extract_with_pattern("file_password_secret123", "_password_", False)
        assert result == "secret123"
        
        result = _extract_with_pattern("file_PASSWORD_secret123", "_password_", False)
        assert result == "secret123"
        
        # Test case-sensitive
        result = _extract_with_pattern("file_password_secret123", "_password_", True)
        assert result == "secret123"
        
        result = _extract_with_pattern("file_PASSWORD_secret123", "_password_", True)
        assert result is None

    def test_extract_with_pattern_no_match(self):
        """Test pattern extraction with no match."""
        result = _extract_with_pattern("file_secret123", "_password_", False)
        assert result is None

    def test_extract_with_pattern_empty_result(self):
        """Test pattern extraction with empty result."""
        result = _extract_with_pattern("file_password_", "_password_", False)
        assert result is None

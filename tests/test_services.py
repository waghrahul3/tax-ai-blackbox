"""Unit tests for service layer."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from models.document import DocumentContent
from services.content_cleaning_service import ContentCleaningService
from services.file_validation_service import FileValidationService
from services.template_service import TemplateService
from exceptions.base_exceptions import ValidationException
from exceptions.document_exceptions import FileValidationException


class TestContentCleaningService:
    """Test cases for ContentCleaningService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ContentCleaningService()
    
    def test_clean_unicode_box_characters(self):
        """Test Unicode box character cleaning."""
        # Test with box characters
        content_with_boxes = "══ Test ┌─Content ┐ with │boxes│ └──┘"
        cleaned = self.service.clean_unicode_box_characters(content_with_boxes)
        
        assert "══" not in cleaned
        assert "┌" not in cleaned
        assert "─" not in cleaned
        assert "│" not in cleaned
        assert "┐" not in cleaned
        assert "└" not in cleaned
        assert "┘" not in cleaned
        assert "== Test +-Content + with |boxes| +--+" in cleaned
    
    def test_clean_markdown_formatting(self):
        """Test markdown formatting cleaning."""
        # Test with HTML entities and Unicode
        content_with_formatting = "&quot;Hello&quot; &amp; world — with em dash"
        cleaned = self.service.clean_markdown_formatting(content_with_formatting)
        
        assert '"Hello"' in cleaned
        assert '& world' in cleaned
        assert '-- with em dash' in cleaned
        assert "&quot;" not in cleaned
        assert "&amp;" not in cleaned
        assert "—" not in cleaned
    
    def test_clean_prompt_content_complete_pipeline(self):
        """Test complete prompt cleaning pipeline."""
        content = "══ Test ┌─Content ┐ &quot;quoted&quot; — dash"
        cleaned = self.service.clean_prompt_content(content)
        
        # Should clean both Unicode boxes and markdown formatting
        assert "══" not in cleaned
        assert "┌" not in cleaned
        assert "&quot;" not in cleaned
        assert "—" not in cleaned
        assert "== Test +Content +" in cleaned
        assert '"quoted"' in cleaned
        assert "-- dash" in cleaned
    
    def test_validation_errors(self):
        """Test validation error handling."""
        # Test with non-string input
        with pytest.raises(ValidationException):
            self.service.clean_prompt_content(123)
        
        with pytest.raises(ValidationException):
            self.service.clean_unicode_box_characters(None)
        
        with pytest.raises(ValidationException):
            self.service.clean_markdown_formatting([])
    
    def test_empty_content_handling(self):
        """Test handling of empty content."""
        assert self.service.clean_prompt_content("") == ""
        assert self.service.clean_unicode_box_characters("") == ""
        assert self.service.clean_markdown_formatting("") == ""
        assert self.service.clean_prompt_content(None) is None


class TestFileValidationService:
    """Test cases for FileValidationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = FileValidationService()
    
    def create_mock_file(self, filename="test.txt", size=1024, content_type="text/plain"):
        """Create a mock file object."""
        mock_file = Mock()
        mock_file.filename = filename
        mock_file.size = size
        mock_file.content_type = content_type
        return mock_file
    
    def test_validate_supported_file(self):
        """Test validation of supported files."""
        mock_file = self.create_mock_file("test.txt", 1024, "text/plain")
        result = self.service._validate_single_file(mock_file)
        
        assert result["valid"] is True
        assert result["filename"] == "test.txt"
        assert result["file_type"] == "text"
        assert result["file_size"] == 1024
    
    def test_validate_image_file(self):
        """Test validation of image files."""
        mock_file = self.create_mock_file("test.jpg", 2048, "image/jpeg")
        result = self.service._validate_single_file(mock_file)
        
        assert result["valid"] is True
        assert result["file_type"] == "image"
        assert result["content_type"] == "image/jpeg"
    
    def test_validate_pdf_file(self):
        """Test validation of PDF files."""
        mock_file = self.create_mock_file("test.pdf", 4096, "application/pdf")
        result = self.service._validate_single_file(mock_file)
        
        assert result["valid"] is True
        assert result["file_type"] == "pdf"
    
    def test_invalid_filename(self):
        """Test validation of invalid filenames."""
        # Test dangerous filename
        mock_file = self.create_mock_file("../../../etc/passwd", 1024, "text/plain")
        
        with pytest.raises(FileValidationException) as exc_info:
            self.service._validate_single_file(mock_file)
        
        assert "invalid characters" in str(exc_info.value).lower()
        assert exc_info.value.validation_rule == "filename_safe_chars"
    
    def test_empty_filename(self):
        """Test validation of empty filename."""
        mock_file = self.create_mock_file("", 1024, "text/plain")
        
        with pytest.raises(FileValidationException) as exc_info:
            self.service._validate_single_file(mock_file)
        
        assert "empty" in str(exc_info.value).lower()
        assert exc_info.value.validation_rule == "filename_not_empty"
    
    def test_oversized_file(self):
        """Test validation of oversized files."""
        # Create a file larger than the limit
        mock_file = self.create_mock_file("huge.txt", 100 * 1024 * 1024, "text/plain")
        
        with pytest.raises(FileValidationException) as exc_info:
            self.service._validate_single_file(mock_file)
        
        assert "size" in str(exc_info.value).lower()
        assert exc_info.value.validation_rule == "file_size_limit"
    
    def test_multiple_files_validation(self):
        """Test validation of multiple files."""
        files = [
            self.create_mock_file("test1.txt", 1024, "text/plain"),
            self.create_mock_file("test2.jpg", 2048, "image/jpeg"),
            self.create_mock_file("test3.pdf", 4096, "application/pdf")
        ]
        
        result = self.service.validate_files(files)
        
        assert result["total_files"] == 3
        assert result["valid_files"] == 3
        assert result["invalid_files"] == 0
        assert len(result["file_details"]) == 3
    
    def test_supported_extensions(self):
        """Test supported extensions checking."""
        assert self.service.is_supported_extension(".txt", "text") is True
        assert self.service.is_supported_extension("txt", "text") is True
        assert self.service.is_supported_extension(".jpg", "image") is True
        assert self.service.is_supported_extension(".pdf", "pdf") is True
        assert self.service.is_supported_extension(".xyz", "unknown") is False
    
    def test_file_type_detection(self):
        """Test file type detection from extension."""
        assert self.service.get_file_type_from_extension(".txt") == "text"
        assert self.service.get_file_type_from_extension("txt") == "text"
        assert self.service.get_file_type_from_extension(".jpg") == "image"
        assert self.service.get_file_type_from_extension(".pdf") == "pdf"
        assert self.service.get_file_type_from_extension(".xyz") == "unknown"


class TestTemplateService:
    """Test cases for TemplateService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TemplateService()
    
    @patch('services.template_service.get_prompt_template')
    def test_get_template_success(self, mock_get_template):
        """Test successful template retrieval."""
        mock_template_config = Mock()
        mock_template_config.name = "test_template"
        mock_template_config.description = "Test template"
        mock_get_template.return_value = mock_template_config
        
        result = self.service.get_template("test_template")
        
        assert result == mock_template_config
        mock_get_template.assert_called_once_with("test_template")
    
    @patch('services.template_service.get_prompt_template')
    def test_get_template_not_found(self, mock_get_template):
        """Test template not found error."""
        mock_get_template.side_effect = ValueError("Template not found")
        
        with pytest.raises(ValidationException) as exc_info:
            self.service.get_template("nonexistent_template")
        
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.field == "template_name"
    
    @patch('services.template_service.list_prompt_templates')
    def test_list_templates(self, mock_list_templates):
        """Test template listing."""
        mock_templates = ["template1", "template2", "template3"]
        mock_list_templates.return_value = mock_templates
        
        result = self.service.list_templates()
        
        assert result["status"] == "success"
        assert result["template_count"] == 3
        assert result["templates"] == mock_templates
    
    def test_validate_template_name(self):
        """Test template name validation."""
        # Test with valid template
        with patch.object(self.service, 'get_template') as mock_get:
            mock_get.return_value = Mock()
            assert self.service.validate_template_name("valid_template") is True
        
        # Test with invalid template
        with patch.object(self.service, 'get_template') as mock_get:
            mock_get.side_effect = ValidationException("Not found")
            assert self.service.validate_template_name("invalid_template") is False
    
    def test_cache_operations(self):
        """Test template cache operations."""
        # Add a template to cache
        mock_template = Mock()
        mock_template.name = "cached_template"
        self.service._template_cache["cached_template"] = mock_template
        
        # Test cache hit
        result = self.service.get_template("cached_template")
        assert result == mock_template
        
        # Test cache clear
        self.service.clear_cache()
        assert len(self.service._template_cache) == 0
        
        # Test cache stats
        stats = self.service.get_cache_stats()
        assert "cached_templates" in stats
        assert "cache_limit" in stats


# Integration tests
class TestServiceIntegration:
    """Integration tests for service interactions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.content_cleaner = ContentCleaningService()
        self.file_validator = FileValidationService()
    
    def test_content_cleaning_with_validation(self):
        """Test content cleaning service integration."""
        # Create test content with various issues
        content = "══ Test ┌─Content ┐ &quot;quoted&quot; — dash"
        
        # Clean the content
        cleaned_content = self.content_cleaner.clean_prompt_content(content)
        
        # Validate cleaned content
        assert isinstance(cleaned_content, str)
        assert len(cleaned_content) > 0
        assert "══" not in cleaned_content
        assert "&quot;" not in cleaned_content
    
    @pytest.mark.asyncio
    async def test_document_processing_workflow(self):
        """Test document processing workflow simulation."""
        # Create mock document
        document = DocumentContent(
            content_type="text",
            filename="test.txt",
            text_content="══ Test content with ┌boxes┐"
        )
        
        # Process through content cleaner
        cleaned_content = self.content_cleaner.clean_prompt_content(document.text_content)
        document.text_content = cleaned_content
        
        # Validate the result
        assert document.text_content != "══ Test content with ┌boxes┐"
        assert "==" in document.text_content
        assert "+" in document.text_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

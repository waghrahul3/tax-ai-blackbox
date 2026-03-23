"""Unit tests for strategy pattern implementations."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from models.document import DocumentContent
from strategies.document_strategies import (
    TextDocumentStrategy,
    ImageDocumentStrategy,
    PDFDocumentStrategy,
    DocumentStrategyFactory
)
from strategies.output_format_strategies import (
    MarkdownOutputStrategy,
    CSVOutputStrategy,
    JSONOutputStrategy,
    TextOutputStrategy,
    OutputFormatStrategyFactory
)
from strategies.compression_strategies import (
    ImageCompressionStrategy,
    NoCompressionStrategy,
    CompressionStrategyFactory
)
from exceptions.document_exceptions import DocumentProcessingException
from exceptions.output_exceptions import OutputFormatException


class TestTextDocumentStrategy:
    """Test cases for TextDocumentStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = TextDocumentStrategy()
    
    def test_can_process_text_document(self):
        """Test strategy can process text documents."""
        text_doc = DocumentContent(
            content_type="text",
            filename="test.txt",
            text_content="This is text content"
        )
        
        assert self.strategy.can_process(text_doc) is True
    
    def test_cannot_process_image_document(self):
        """Test strategy cannot process image documents."""
        image_doc = DocumentContent(
            content_type="image",
            filename="test.jpg",
            image_data=b"fake_image_data"
        )
        
        assert self.strategy.can_process(image_doc) is False
    
    @pytest.mark.asyncio
    async def test_process_text_document(self):
        """Test text document processing."""
        text_doc = DocumentContent(
            content_type="text",
            filename="test.txt",
            text_content="This is text content"
        )
        
        result = await self.strategy.process(text_doc)
        
        assert result == text_doc
        assert result.text_content == "This is text content"
    
    @pytest.mark.asyncio
    async def test_process_non_text_document_raises_error(self):
        """Test processing non-text document raises error."""
        image_doc = DocumentContent(
            content_type="image",
            filename="test.jpg",
            image_data=b"fake_image_data"
        )
        
        with pytest.raises(DocumentProcessingException) as exc_info:
            await self.strategy.process(image_doc)
        
        assert "not a text document" in str(exc_info.value).lower()
    
    @patch('strategies.document_strategies.normalize_tabular_text')
    @pytest.mark.asyncio
    async def test_process_with_pandas_cleaning(self, mock_normalize):
        """Test processing with pandas cleaning enabled."""
        mock_normalize.return_value = "Cleaned content"
        
        # Mock feature flag
        self.strategy.config_manager.is_feature_enabled.return_value = True
        
        text_doc = DocumentContent(
            content_type="text",
            filename="test.csv",
            text_content="Original content"
        )
        
        result = await self.strategy.process(text_doc)
        
        mock_normalize.assert_called_once_with("Original content")
        assert result.text_content == "Cleaned content"
    
    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        extensions = self.strategy.get_supported_extensions()
        
        assert isinstance(extensions, list)
        assert ".txt" in extensions
        assert ".md" in extensions
        assert ".csv" in extensions
    
    def test_strategy_info(self):
        """Test strategy information."""
        info = self.strategy.get_strategy_info()
        
        assert "strategy_name" in info
        assert "supported_extensions" in info
        assert "can_process_text" in info
        assert "can_process_images" in info
        assert info["can_process_text"] is True
        assert info["can_process_images"] is False


class TestImageDocumentStrategy:
    """Test cases for ImageDocumentStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = ImageDocumentStrategy()
    
    def test_can_process_image_document(self):
        """Test strategy can process image documents."""
        image_doc = DocumentContent(
            content_type="image",
            filename="test.jpg",
            image_data=b"fake_image_data"
        )
        
        assert self.strategy.can_process(image_doc) is True
    
    def test_cannot_process_text_document(self):
        """Test strategy cannot process text documents."""
        text_doc = DocumentContent(
            content_type="text",
            filename="test.txt",
            text_content="This is text content"
        )
        
        assert self.strategy.can_process(text_doc) is False
    
    @pytest.mark.asyncio
    async def test_process_image_document(self):
        """Test image document processing."""
        image_doc = DocumentContent(
            content_type="image",
            filename="test.jpg",
            image_data=b"small_image_data"
        )
        
        result = await self.strategy.process(image_doc)
        
        assert result == image_doc
        assert result.image_data == b"small_image_data"
    
    @patch('strategies.document_strategies.compress_image_to_limit')
    @pytest.mark.asyncio
    async def test_process_with_compression(self, mock_compress):
        """Test processing with image compression."""
        mock_compress.return_value = (b"compressed_data", "image/jpeg")
        
        # Mock feature flag and config
        self.strategy.config_manager.is_feature_enabled.return_value = True
        self.strategy.config_manager.api_limits.return_value.get_limit.return_value = 1000
        
        image_doc = DocumentContent(
            content_type="image",
            filename="test.jpg",
            image_data=b"large_image_data"
        )
        
        result = await self.strategy.process(image_doc)
        
        assert result.image_data == b"compressed_data"
        assert result.image_media_type == "image/jpeg"


class TestPDFDocumentStrategy:
    """Test cases for PDFDocumentStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = PDFDocumentStrategy()
    
    def test_can_process_pdf_document(self):
        """Test strategy can process PDF documents."""
        pdf_doc = DocumentContent(
            content_type="text",  # PDFs often have text content type after processing
            filename="test.pdf",
            text_content="PDF content",
            source_media_type="application/pdf"
        )
        
        assert self.strategy.can_process(pdf_doc) is True
    
    def test_can_process_pdf_by_filename(self):
        """Test strategy can process PDF by filename extension."""
        pdf_doc = DocumentContent(
            content_type="text",
            filename="test.pdf",
            text_content="PDF content"
        )
        
        assert self.strategy.can_process(pdf_doc) is True
    
    def test_cannot_process_non_pdf_document(self):
        """Test strategy cannot process non-PDF documents."""
        text_doc = DocumentContent(
            content_type="text",
            filename="test.txt",
            text_content="Text content"
        )
        
        assert self.strategy.can_process(text_doc) is False


class TestDocumentStrategyFactory:
    """Test cases for DocumentStrategyFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = DocumentStrategyFactory()
    
    def test_get_strategy_for_text_document(self):
        """Test getting strategy for text document."""
        text_doc = DocumentContent(
            content_type="text",
            filename="test.txt",
            text_content="Text content"
        )
        
        strategy = self.factory.get_strategy(text_doc)
        
        assert isinstance(strategy, TextDocumentStrategy)
    
    def test_get_strategy_for_image_document(self):
        """Test getting strategy for image document."""
        image_doc = DocumentContent(
            content_type="image",
            filename="test.jpg",
            image_data=b"image_data"
        )
        
        strategy = self.factory.get_strategy(image_doc)
        
        assert isinstance(strategy, ImageDocumentStrategy)
    
    def test_get_strategy_for_pdf_document(self):
        """Test getting strategy for PDF document."""
        pdf_doc = DocumentContent(
            content_type="text",
            filename="test.pdf",
            text_content="PDF content",
            source_media_type="application/pdf"
        )
        
        strategy = self.factory.get_strategy(pdf_doc)
        
        assert isinstance(strategy, PDFDocumentStrategy)
    
    def test_get_strategy_unsupported_document(self):
        """Test getting strategy for unsupported document type."""
        unsupported_doc = DocumentContent(
            content_type="unknown",
            filename="test.xyz",
            text_content="Unknown content"
        )
        
        with pytest.raises(DocumentProcessingException) as exc_info:
            self.factory.get_strategy(unsupported_doc)
        
        assert "no strategy available" in str(exc_info.value).lower()
    
    def test_get_all_strategies(self):
        """Test getting all strategies."""
        strategies = self.factory.get_all_strategies()
        
        assert len(strategies) == 3
        assert any(isinstance(s, TextDocumentStrategy) for s in strategies)
        assert any(isinstance(s, ImageDocumentStrategy) for s in strategies)
        assert any(isinstance(s, PDFDocumentStrategy) for s in strategies)
    
    def test_get_supported_extensions(self):
        """Test getting all supported extensions."""
        extensions = self.factory.get_supported_extensions()
        
        assert isinstance(extensions, list)
        assert ".txt" in extensions
        assert ".jpg" in extensions
        assert ".pdf" in extensions
    
    def test_get_strategy_info(self):
        """Test getting strategy factory information."""
        info = self.factory.get_strategy_info()
        
        assert "total_strategies" in info
        assert "strategies" in info
        assert "supported_extensions" in info
        assert info["total_strategies"] == 3


class TestOutputFormatStrategies:
    """Test cases for output format strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.markdown_strategy = MarkdownOutputStrategy()
        self.csv_strategy = CSVOutputStrategy()
        self.json_strategy = JSONOutputStrategy()
        self.text_strategy = TextOutputStrategy()
    
    def test_markdown_strategy_can_handle(self):
        """Test markdown strategy format handling."""
        assert self.markdown_strategy.can_handle("markdown") is True
        assert self.markdown_strategy.can_handle("md") is True
        assert self.markdown_strategy.can_handle("csv") is False
    
    def test_csv_strategy_can_handle(self):
        """Test CSV strategy format handling."""
        assert self.csv_strategy.can_handle("csv") is True
        assert self.csv_strategy.can_handle("CSV") is True
        assert self.csv_strategy.can_handle("markdown") is False
    
    def test_json_strategy_can_handle(self):
        """Test JSON strategy format handling."""
        assert self.json_strategy.can_handle("json") is True
        assert self.json_strategy.can_handle("JSON") is True
        assert self.json_strategy.can_handle("csv") is False
    
    def test_text_strategy_can_handle(self):
        """Test text strategy format handling."""
        assert self.text_strategy.can_handle("text") is True
        assert self.text_strategy.can_handle("txt") is True
        assert self.text_strategy.can_handle("plain") is True
        assert self.text_strategy.can_handle("csv") is False
    
    def test_markdown_strategy_prepare_content(self):
        """Test markdown content preparation."""
        content = "# Header\n\nSome content with ```csv\ncol1,col2\nval1,val2\n```"
        prepared = self.markdown_strategy.prepare_content(content)
        
        assert "# Header" in prepared
        assert "col1,col2" not in prepared  # CSV blocks should be removed
        assert "Generated CSV Files" in prepared  # References should be added
    
    def test_csv_strategy_prepare_content(self):
        """Test CSV content preparation."""
        content = "```csv\ncol1,col2\nval1,val2\n```"
        prepared = self.csv_strategy.prepare_content(content)
        
        assert "col1,col2" in prepared
        assert "val1,val2" in prepared
        assert "```" not in prepared
    
    def test_json_strategy_prepare_content(self):
        """Test JSON content preparation."""
        content = '{"key": "value"}'
        prepared = self.json_strategy.prepare_content(content)
        
        assert '"key"' in prepared
        assert '"value"' in prepared
        assert prepared.startswith("{")
        assert prepared.endswith("}")
    
    def test_text_strategy_prepare_content(self):
        """Test text content preparation."""
        content = "# Header\n\n**Bold** text and *italic* text"
        prepared = self.text_strategy.prepare_content(content)
        
        assert "Header" in prepared
        assert "#" not in prepared  # Headers should be removed
        assert "**Bold**" not in prepared  # Bold should be removed
        assert "*italic*" not in prepared  # Italic should be removed
        assert "Bold" in prepared
        assert "italic" in prepared
    
    def test_strategy_file_extensions(self):
        """Test strategy file extensions."""
        assert self.markdown_strategy.get_file_extension() == ".md"
        assert self.csv_strategy.get_file_extension() == ".csv"
        assert self.json_strategy.get_file_extension() == ".json"
        assert self.text_strategy.get_file_extension() == ".txt"
    
    def test_strategy_mime_types(self):
        """Test strategy MIME types."""
        assert self.markdown_strategy.get_mime_type() == "text/markdown"
        assert self.csv_strategy.get_mime_type() == "text/csv"
        assert self.json_strategy.get_mime_type() == "application/json"
        assert self.text_strategy.get_mime_type() == "text/plain"


class TestOutputFormatStrategyFactory:
    """Test cases for OutputFormatStrategyFactory."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = OutputFormatStrategyFactory()
    
    def test_get_strategy_for_markdown(self):
        """Test getting strategy for markdown format."""
        strategy = self.factory.get_strategy("markdown")
        
        assert isinstance(strategy, MarkdownOutputStrategy)
    
    def test_get_strategy_for_csv(self):
        """Test getting strategy for CSV format."""
        strategy = self.factory.get_strategy("csv")
        
        assert isinstance(strategy, CSVOutputStrategy)
    
    def test_get_strategy_for_json(self):
        """Test getting strategy for JSON format."""
        strategy = self.factory.get_strategy("json")
        
        assert isinstance(strategy, JSONOutputStrategy)
    
    def test_get_strategy_for_text(self):
        """Test getting strategy for text format."""
        strategy = self.factory.get_strategy("text")
        
        assert isinstance(strategy, TextOutputStrategy)
    
    def test_get_strategy_unsupported_format(self):
        """Test getting strategy for unsupported format."""
        with pytest.raises(OutputFormatException) as exc_info:
            self.factory.get_strategy("unsupported")
        
        assert "no strategy available" in str(exc_info.value).lower()
    
    def test_get_all_strategies(self):
        """Test getting all strategies."""
        strategies = self.factory.get_all_strategies()
        
        assert len(strategies) == 4
        assert any(isinstance(s, MarkdownOutputStrategy) for s in strategies)
        assert any(isinstance(s, CSVOutputStrategy) for s in strategies)
        assert any(isinstance(s, JSONOutputStrategy) for s in strategies)
        assert any(isinstance(s, TextOutputStrategy) for s in strategies)
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.factory.get_supported_formats()
        
        assert isinstance(formats, list)
        assert "markdown" in formats
        assert "csv" in formats
        assert "json" in formats
        assert "text" in formats


class TestCompressionStrategies:
    """Test cases for compression strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.image_strategy = ImageCompressionStrategy()
        self.no_compression_strategy = NoCompressionStrategy()
        self.factory = CompressionStrategyFactory()
    
    def test_image_strategy_can_compress(self):
        """Test image strategy compression capability."""
        assert self.image_strategy.can_compress(b"data", "image/jpeg") is True
        assert self.image_strategy.can_compress(b"data", "text/plain") is False
    
    def test_no_compression_strategy_can_compress(self):
        """Test no compression strategy capability."""
        assert self.no_compression_strategy.can_compress(b"data", "image/jpeg") is True
        assert self.no_compression_strategy.can_compress(b"data", "text/plain") is True
        assert self.no_compression_strategy.can_compress(b"data", "application/pdf") is True
    
    @pytest.mark.asyncio
    async def test_no_compression_strategy_compress(self):
        """Test no compression strategy compression."""
        data = b"test data"
        result_data, result_type = await self.no_compression_strategy.compress(data, "text/plain")
        
        assert result_data == data
        assert result_type == "text/plain"
    
    def test_get_strategy_by_data_type(self):
        """Test getting strategy by data type."""
        # Image data
        strategy = self.factory.get_strategy(b"data", "image/jpeg")
        assert isinstance(strategy, ImageCompressionStrategy)
        
        # Text data (should fall back to NoCompressionStrategy)
        strategy = self.factory.get_strategy(b"data", "text/plain")
        assert isinstance(strategy, NoCompressionStrategy)
    
    def test_get_strategy_by_type_name(self):
        """Test getting strategy by type name."""
        strategy = self.factory.get_strategy_by_type("image")
        assert isinstance(strategy, ImageCompressionStrategy)
        
        strategy = self.factory.get_strategy_by_type("none")
        assert isinstance(strategy, NoCompressionStrategy)
        
        with pytest.raises(Exception):  # Should raise some exception for unknown type
            self.factory.get_strategy_by_type("unknown")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

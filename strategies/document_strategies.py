"""Document processing strategies for different file types."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from models.document import DocumentContent
from utils.logger import get_logger
from exceptions.document_exceptions import DocumentProcessingException
from config.config_manager import get_config_manager


class DocumentStrategy(ABC):
    """Abstract base class for document processing strategies."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = get_config_manager()
    
    @abstractmethod
    def can_process(self, document: DocumentContent) -> bool:
        """
        Check if this strategy can process the given document.
        
        Args:
            document: Document to check
            
        Returns:
            True if strategy can process the document
        """
        pass
    
    @abstractmethod
    async def process(self, document: DocumentContent) -> DocumentContent:
        """
        Process the document according to the strategy.
        
        Args:
            document: Document to process
            
        Returns:
            Processed document
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.
        
        Returns:
            List of supported extensions
        """
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about this strategy.
        
        Returns:
            Strategy information dictionary
        """
        return {
            "strategy_name": self.__class__.__name__,
            "supported_extensions": self.get_supported_extensions(),
            "can_process_text": self.can_process_text(),
            "can_process_images": self.can_process_images()
        }
    
    def can_process_text(self) -> bool:
        """Check if strategy can process text content."""
        return False
    
    def can_process_images(self) -> bool:
        """Check if strategy can process image content."""
        return False


class TextDocumentStrategy(DocumentStrategy):
    """Strategy for processing text documents."""
    
    def can_process(self, document: DocumentContent) -> bool:
        """Check if document is a text document."""
        return document.is_text()
    
    async def process(self, document: DocumentContent) -> DocumentContent:
        """Process text document (validation and normalization)."""
        if not document.is_text():
            raise DocumentProcessingException(
                "Document is not a text document",
                filename=document.filename,
                document_type="text"
            )
        
        # Validate text content
        if not document.text_content or not document.text_content.strip():
            self.logger.warning(
                "Text document has no content",
                extra={"filename": document.filename}
            )
        
        # Apply text cleaning if enabled
        if self.config_manager.is_feature_enabled("pandas_cleaning"):
            document = await self._apply_pandas_cleaning(document)
        
        self.logger.debug(
            "Text document processed",
            extra={
                "filename": document.filename,
                "content_length": len(document.text_content) if document.text_content else 0
            }
        )
        
        return document
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported text file extensions."""
        return self.config_manager.file_config().get_supported_extensions('text')
    
    def can_process_text(self) -> bool:
        """Strategy can process text content."""
        return True
    
    async def _apply_pandas_cleaning(self, document: DocumentContent) -> DocumentContent:
        """Apply pandas cleaning to normalize tabular text."""
        try:
            from utils.pandas_cleaner import normalize_tabular_text
            
            original_text = document.text_content
            cleaned_text = normalize_tabular_text(original_text)
            
            if cleaned_text != original_text:
                document.text_content = cleaned_text
                self.logger.info(
                    "Pandas cleaning applied to text document",
                    extra={
                        "filename": document.filename,
                        "original_length": len(original_text),
                        "cleaned_length": len(cleaned_text)
                    }
                )
            
            return document
            
        except Exception as e:
            self.logger.warning(
                "Pandas cleaning failed, using original text",
                extra={
                    "filename": document.filename,
                    "error": str(e)
                }
            )
            return document


class ImageDocumentStrategy(DocumentStrategy):
    """Strategy for processing image documents."""
    
    def can_process(self, document: DocumentContent) -> bool:
        """Check if document is an image document."""
        return document.is_image()
    
    async def process(self, document: DocumentContent) -> DocumentContent:
        """Process image document (compression and validation)."""
        if not document.is_image():
            raise DocumentProcessingException(
                "Document is not an image document",
                filename=document.filename,
                document_type="image"
            )
        
        # Apply compression if enabled and needed
        if self.config_manager.is_feature_enabled("file_compression"):
            document = await self._apply_compression(document)
        
        # Extract text from image if possible
        if self.config_manager.is_feature_enabled("image_text_extraction"):
            document = await self._extract_text_from_image(document)
        
        self.logger.debug(
            "Image document processed",
            extra={
                "filename": document.filename,
                "image_size": len(document.image_data) if document.image_data else 0,
                "has_text": bool(document.text_content)
            }
        )
        
        return document
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported image file extensions."""
        return self.config_manager.file_config().get_supported_extensions('image')
    
    def can_process_images(self) -> bool:
        """Strategy can process image content."""
        return True
    
    async def _apply_compression(self, document: DocumentContent) -> DocumentContent:
        """Apply image compression if needed."""
        if not document.image_data:
            return document
        
        max_image_bytes = self.config_manager.api_limits().get_limit("max_image_bytes")
        
        if len(document.image_data) <= max_image_bytes:
            return document
        
        try:
            from utils.image_handler import compress_image_to_limit
            
            compressed_data, media_type = compress_image_to_limit(document.image_data)
            document.image_data = compressed_data
            document.image_media_type = media_type
            
            self.logger.info(
                "Image compressed",
                extra={
                    "filename": document.filename,
                    "original_size": len(document.image_data),
                    "compressed_size": len(compressed_data)
                }
            )
            
            return document
            
        except Exception as e:
            self.logger.warning(
                "Image compression failed, using original",
                extra={
                    "filename": document.filename,
                    "error": str(e)
                }
            )
            return document
    
    async def _extract_text_from_image(self, document: DocumentContent) -> DocumentContent:
        """Extract text from image using OCR."""
        try:
            from storage.local_storage import LocalStorage
            
            storage = LocalStorage()
            extracted_text = storage._extract_text_from_image(
                document.image_data, 
                document.image_media_type or "image/jpeg"
            )
            
            if extracted_text.strip():
                document.text_content = extracted_text
                self.logger.info(
                    "Text extracted from image",
                    extra={
                        "filename": document.filename,
                        "extracted_length": len(extracted_text)
                    }
                )
            
            return document
            
        except Exception as e:
            self.logger.warning(
                "Text extraction from image failed",
                extra={
                    "filename": document.filename,
                    "error": str(e)
                }
            )
            return document


class PDFDocumentStrategy(DocumentStrategy):
    """Strategy for processing PDF documents."""
    
    def can_process(self, document: DocumentContent) -> bool:
        """Check if document is a PDF document."""
        return (document.source_media_type == "application/pdf" or 
                (document.filename and document.filename.lower().endswith('.pdf')))
    
    async def process(self, document: DocumentContent) -> DocumentContent:
        """Process PDF document (text extraction and structured data)."""
        if not self.can_process(document):
            raise DocumentProcessingException(
                "Document is not a PDF document",
                filename=document.filename,
                document_type="pdf"
            )
        
        # Extract text from PDF if available
        if document.source_path:
            document = await self._extract_pdf_text(document)
        
        # Apply structured data extraction if enabled
        if self.config_manager.is_feature_enabled("structured_data_extraction"):
            document = await self._extract_structured_data(document)
        
        self.logger.debug(
            "PDF document processed",
            extra={
                "filename": document.filename,
                "has_text": bool(document.text_content),
                "text_length": len(document.text_content) if document.text_content else 0
            }
        )
        
        return document
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported PDF file extensions."""
        return ['.pdf']
    
    def can_process_text(self) -> bool:
        """Strategy can process text content."""
        return True
    
    async def _extract_pdf_text(self, document: DocumentContent) -> DocumentContent:
        """Extract text from PDF file."""
        try:
            from utils.pdf_extractor import extract_text_from_pdf
            
            if document.source_path:
                pdf_text = extract_text_from_pdf(document.source_path)
                if pdf_text.strip():
                    document.text_content = pdf_text
                    self.logger.info(
                        "PDF text extracted",
                        extra={
                            "filename": document.filename,
                            "extracted_length": len(pdf_text)
                        }
                    )
            
            return document
            
        except Exception as e:
            self.logger.warning(
                "PDF text extraction failed",
                extra={
                    "filename": document.filename,
                    "error": str(e)
                }
            )
            return document
    
    async def _extract_structured_data(self, document: DocumentContent) -> DocumentContent:
        """Extract structured data from PDF."""
        try:
            from utils.t4_extractor import extract_structured_slip, format_structured_text
            
            if document.source_path:
                doc_type, extraction = extract_structured_slip(document.source_path)
                if doc_type and extraction:
                    formatted_text = format_structured_text(doc_type, extraction)
                    enrichment = (
                        f"\n\n[{doc_type} Structured Extraction]\n"
                        f"{formatted_text}\n"
                    )
                    
                    base_text = document.text_content or ""
                    document.text_content = f"{base_text}{enrichment}" if base_text else enrichment
                    
                    self.logger.info(
                        "Structured data extracted from PDF",
                        extra={
                            "filename": document.filename,
                            "doc_type": doc_type,
                            "enrichment_length": len(enrichment)
                        }
                    )
            
            return document
            
        except Exception as e:
            self.logger.warning(
                "Structured data extraction failed",
                extra={
                    "filename": document.filename,
                    "error": str(e)
                }
            )
            return document


class DocumentStrategyFactory:
    """Factory for creating document processing strategies."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._strategies = [
            TextDocumentStrategy(),
            ImageDocumentStrategy(),
            PDFDocumentStrategy()
        ]
    
    def get_strategy(self, document: DocumentContent) -> DocumentStrategy:
        """
        Get the appropriate strategy for processing a document.
        
        Args:
            document: Document to process
            
        Returns:
            Appropriate document strategy
            
        Raises:
            DocumentProcessingException: If no strategy can process the document
        """
        for strategy in self._strategies:
            if strategy.can_process(document):
                self.logger.debug(
                    "Strategy selected for document",
                    extra={
                        "strategy": strategy.__class__.__name__,
                        "filename": document.filename,
                        "content_type": document.content_type
                    }
                )
                return strategy
        
        raise DocumentProcessingException(
            f"No strategy available to process document: {document.filename}",
            filename=document.filename,
            document_type=document.content_type
        )
    
    def get_all_strategies(self) -> List[DocumentStrategy]:
        """Get all available strategies."""
        return self._strategies.copy()
    
    def get_supported_extensions(self) -> List[str]:
        """Get all supported extensions from all strategies."""
        extensions = set()
        for strategy in self._strategies:
            extensions.update(strategy.get_supported_extensions())
        return list(extensions)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about all strategies."""
        return {
            "total_strategies": len(self._strategies),
            "strategies": [strategy.get_strategy_info() for strategy in self._strategies],
            "supported_extensions": self.get_supported_extensions()
        }

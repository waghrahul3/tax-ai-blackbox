"""Service for processing and loading documents."""

from typing import List
from models.document import DocumentContent
from storage.storage_factory import get_storage
from utils.logger import get_logger
from exceptions.document_exceptions import (
    DocumentProcessingException,
    FileValidationException,
    DocumentLoadException
)
from config.config_manager import get_config_manager
from strategies.document_strategies import DocumentStrategyFactory


class DocumentProcessingService:
    """Service for handling document loading and preprocessing."""
    
    def __init__(self, storage=None):
        self.logger = get_logger(__name__)
        self.storage = storage or get_storage()
        self.config_manager = get_config_manager()
        self.api_limits = self.config_manager.api_limits()
        self.max_image_bytes = self.api_limits.get_limit("max_image_bytes")
        self.strategy_factory = DocumentStrategyFactory()
    
    async def load_documents(self, files: List) -> List[DocumentContent]:
        """
        Load and validate documents from uploaded files.
        
        Args:
            files: List of uploaded files to process
            
        Returns:
            List of processed DocumentContent objects
            
        Raises:
            DocumentProcessingException: If document loading fails
            FileValidationException: If file validation fails
        """
        if not files:
            raise DocumentProcessingException("No files provided for processing")
        
        documents = []
        
        try:
            self.logger.info(
                "Loading documents", 
                extra={"file_count": len(files)}
            )
            
            for file in files:
                try:
                    # Validate file before processing
                    self._validate_file(file)
                    
                    # Load document
                    doc = await self.storage.read_file(file)
                    
                    # Apply strategy-based processing
                    doc = await self.process_document_with_strategy(doc)
                    
                    # Check for oversized images
                    self._validate_image_size(doc)
                    
                    documents.append(doc)
                    
                    self.logger.debug(
                        "Loaded document",
                        extra=doc.get_display_info()
                    )
                    
                except FileValidationException:
                    raise  # Re-raise validation exceptions
                except Exception as e:
                    filename = getattr(file, 'filename', 'unknown')
                    raise DocumentLoadException(
                        f"Failed to load document: {str(e)}",
                        filename=filename,
                        source_path=getattr(file, 'file_path', None),
                        loader_type="storage"
                    ) from e
            
            # Log summary
            text_count = sum(1 for d in documents if d.is_text())
            image_count = sum(1 for d in documents if d.is_image())
            
            self.logger.info(
                "Documents loaded successfully",
                extra={
                    "total": len(documents), 
                    "text": text_count, 
                    "images": image_count,
                    "file_paths": [getattr(f, 'file_path', 'unknown') for f in files]
                }
            )
            
            return documents
            
        except Exception as e:
            if isinstance(e, (DocumentProcessingException, FileValidationException)):
                raise
            raise DocumentProcessingException(
                f"Unexpected error during document loading: {str(e)}"
            ) from e
    
    def _validate_file(self, file) -> None:
        """
        Validate uploaded file before processing.
        
        Args:
            file: Uploaded file to validate
            
        Raises:
            FileValidationException: If file validation fails
        """
        if not file:
            raise FileValidationException("File object is None")
        
        filename = getattr(file, 'filename', None)
        if not filename:
            raise FileValidationException("File has no filename", validation_rule="filename_required")
        
        if not isinstance(filename, str):
            raise FileValidationException(
                "Filename must be a string", 
                filename=str(filename),
                validation_rule="filename_type"
            )
        
        # Check for empty filename
        if filename.strip() == "":
            raise FileValidationException("Filename cannot be empty", validation_rule="filename_not_empty")
        
        # Check for potentially dangerous filenames
        dangerous_patterns = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(pattern in filename for pattern in dangerous_patterns):
            raise FileValidationException(
                "Filename contains invalid characters",
                filename=filename,
                validation_rule="filename_safe_chars"
            )
    
    def _validate_image_size(self, doc: DocumentContent) -> None:
        """
        Validate image size and log warnings for oversized images.
        
        Args:
            doc: Document content to validate
            
        Raises:
            FileValidationException: If image is too large
        """
        if not doc.is_image():
            return
        
        if not hasattr(doc, 'image_data') or not doc.image_data:
            return
        
        image_size = len(doc.image_data)
        
        if image_size > self.max_image_bytes:
            self.logger.warning(
                "Image file exceeds safe API limit and will be compressed",
                extra={
                    "file_name": doc.filename, 
                    "size": image_size, 
                    "limit": self.max_image_bytes
                }
            )
        
        # Check for extremely large images that might cause issues
        if image_size > self.max_image_bytes * 2:
            raise FileValidationException(
                "Image file is too large for processing",
                filename=doc.filename,
                file_size=image_size,
                validation_rule="image_size_limit"
            )
    
    def get_document_summary(self, documents: List[DocumentContent]) -> dict:
        """
        Get summary statistics for loaded documents.
        
        Args:
            documents: List of DocumentContent objects
            
        Returns:
            Dictionary with document statistics
        """
        if not documents:
            return {
                "total_documents": 0,
                "text_documents": 0,
                "image_documents": 0,
                "total_text_characters": 0,
                "total_image_bytes": 0
            }
        
        text_docs = [d for d in documents if d.is_text()]
        image_docs = [d for d in documents if d.is_image()]
        
        total_text_chars = sum(
            len(d.text_content) for d in text_docs 
            if d.text_content
        )
        
        total_image_bytes = sum(
            len(d.image_data) for d in image_docs 
            if hasattr(d, 'image_data') and d.image_data
        )
        
        return {
            "total_documents": len(documents),
            "text_documents": len(text_docs),
            "image_documents": len(image_docs),
            "total_text_characters": total_text_chars,
            "total_image_bytes": total_image_bytes,
            "file_types": list(set(d.content_type for d in documents))
        }
    
    async def process_document_with_strategy(self, document: DocumentContent) -> DocumentContent:
        """
        Process a document using the appropriate strategy.
        
        Args:
            document: Document to process
            
        Returns:
            Processed document
        """
        try:
            strategy = self.strategy_factory.get_strategy(document)
            processed_doc = await strategy.process(document)
            
            self.logger.debug(
                "Document processed with strategy",
                extra={
                    "strategy": strategy.__class__.__name__,
                    "filename": document.filename,
                    "content_type": document.content_type
                }
            )
            
            return processed_doc
            
        except Exception as e:
            self.logger.error(
                "Strategy-based document processing failed",
                extra={
                    "filename": document.filename,
                    "content_type": document.content_type,
                    "error": str(e)
                }
            )
            # Fall back to original document if strategy fails
            return document
    
    def get_strategy_info(self) -> dict:
        """Get information about available document strategies."""
        return self.strategy_factory.get_strategy_info()

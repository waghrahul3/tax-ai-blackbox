"""Compression strategies for different file types."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger
from exceptions.output_exceptions import FileCreationException
from config.config_manager import get_config_manager


class CompressionStrategy(ABC):
    """Abstract base class for compression strategies."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = get_config_manager()
    
    @abstractmethod
    def can_compress(self, data: bytes, file_type: str) -> bool:
        """
        Check if this strategy can compress the given data.
        
        Args:
            data: Data to compress
            file_type: Type of file
            
        Returns:
            True if strategy can compress the data
        """
        pass
    
    @abstractmethod
    async def compress(self, data: bytes, file_type: str, **kwargs) -> Tuple[bytes, str]:
        """
        Compress the data according to the strategy.
        
        Args:
            data: Data to compress
            file_type: Type of file
            **kwargs: Additional compression parameters
            
        Returns:
            Tuple of (compressed_data, media_type)
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
            "supported_types": self.get_supported_types()
        }
    
    @abstractmethod
    def get_supported_types(self) -> list:
        """Get list of supported file types."""
        pass


class ImageCompressionStrategy(CompressionStrategy):
    """Strategy for compressing image files."""
    
    def can_compress(self, data: bytes, file_type: str) -> bool:
        """Check if data is an image that can be compressed."""
        return file_type.lower().startswith('image/')
    
    async def compress(self, data: bytes, file_type: str, **kwargs) -> Tuple[bytes, str]:
        """Compress image data."""
        if not self.can_compress(data, file_type):
            raise FileCreationException(
                f"Cannot compress file type: {file_type}",
                file_operation="image_compression"
            )
        
        max_size = kwargs.get('max_size') or self.config_manager.api_limits().get_limit("max_image_bytes")
        quality = kwargs.get('quality') or self.config_manager.file_config().get_compression_config()["compression_quality"]
        
        try:
            from utils.image_handler import compress_image_to_limit
            
            compressed_data, media_type = compress_image_to_limit(data, max_size)
            
            self.logger.info(
                "Image compressed successfully",
                extra={
                    "original_size": len(data),
                    "compressed_size": len(compressed_data),
                    "compression_ratio": len(compressed_data) / len(data) if data else 0,
                    "media_type": media_type
                }
            )
            
            return compressed_data, media_type
            
        except Exception as e:
            self.logger.error(
                "Image compression failed",
                extra={
                    "file_type": file_type,
                    "error": str(e)
                }
            )
            raise FileCreationException(
                f"Image compression failed: {str(e)}",
                file_operation="image_compression"
            ) from e
    
    def get_supported_types(self) -> list:
        """Get supported image types."""
        return ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']


class NoCompressionStrategy(CompressionStrategy):
    """Strategy that doesn't compress data (pass-through)."""
    
    def can_compress(self, data: bytes, file_type: str) -> bool:
        """This strategy can handle any data type."""
        return True
    
    async def compress(self, data: bytes, file_type: str, **kwargs) -> Tuple[bytes, str]:
        """Return data without compression."""
        self.logger.debug(
            "No compression applied",
            extra={
                "data_size": len(data),
                "file_type": file_type
            }
        )
        
        # Determine media type if not provided
        media_type = kwargs.get('media_type') or file_type
        if not media_type:
            media_type = 'application/octet-stream'
        
        return data, media_type
    
    def get_supported_types(self) -> list:
        """Get supported types (all types)."""
        return ['*']


class PDFCompressionStrategy(CompressionStrategy):
    """Strategy for compressing PDF files."""
    
    def can_compress(self, data: bytes, file_type: str) -> bool:
        """Check if data is a PDF file."""
        return file_type.lower() == 'application/pdf'
    
    async def compress(self, data: bytes, file_type: str, **kwargs) -> Tuple[bytes, str]:
        """Compress PDF data."""
        if not self.can_compress(data, file_type):
            raise FileCreationException(
                f"Cannot compress file type: {file_type}",
                file_operation="pdf_compression"
            )
        
        # For PDF compression, we'll use a simple approach
        # In a real implementation, you might use libraries like PyPDF2 or reportlab
        try:
            # Simple size check - if PDF is too large, warn but don't compress
            max_pdf_size = kwargs.get('max_size') or (10 * 1024 * 1024)  # 10MB default
            
            if len(data) > max_pdf_size:
                self.logger.warning(
                    "PDF file is large but compression not implemented",
                    extra={
                        "pdf_size": len(data),
                        "max_size": max_pdf_size
                    }
                )
            
            self.logger.debug(
                "PDF compression (pass-through)",
                extra={
                    "pdf_size": len(data)
                }
            )
            
            return data, 'application/pdf'
            
        except Exception as e:
            self.logger.error(
                "PDF compression failed",
                extra={
                    "error": str(e)
                }
            )
            raise FileCreationException(
                f"PDF compression failed: {str(e)}",
                file_operation="pdf_compression"
            ) from e
    
    def get_supported_types(self) -> list:
        """Get supported PDF types."""
        return ['application/pdf']


class CompressionStrategyFactory:
    """Factory for creating compression strategies."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._strategies = [
            ImageCompressionStrategy(),
            PDFCompressionStrategy(),
            NoCompressionStrategy()  # Fallback strategy
        ]
    
    def get_strategy(self, data: bytes, file_type: str) -> CompressionStrategy:
        """
        Get the appropriate compression strategy.
        
        Args:
            data: Data to compress
            file_type: Type of file
            
        Returns:
            Appropriate compression strategy
        """
        for strategy in self._strategies:
            if strategy.can_compress(data, file_type):
                self.logger.debug(
                    "Compression strategy selected",
                    extra={
                        "strategy": strategy.__class__.__name__,
                        "file_type": file_type,
                        "data_size": len(data)
                    }
                )
                return strategy
        
        # This should never happen due to NoCompressionStrategy
        raise FileCreationException(
            f"No compression strategy available for: {file_type}",
            file_operation="compression_selection"
        )
    
    def get_strategy_by_type(self, strategy_type: str) -> CompressionStrategy:
        """
        Get strategy by type name.
        
        Args:
            strategy_type: Type of strategy ('image', 'pdf', 'none')
            
        Returns:
            Requested strategy
        """
        strategy_map = {
            'image': ImageCompressionStrategy,
            'pdf': PDFCompressionStrategy,
            'none': NoCompressionStrategy
        }
        
        strategy_class = strategy_map.get(strategy_type.lower())
        if not strategy_class:
            raise FileCreationException(
                f"Unknown compression strategy: {strategy_type}",
                file_operation="compression_selection"
            )
        
        return strategy_class()
    
    def get_all_strategies(self) -> list:
        """Get all available strategies."""
        return self._strategies.copy()
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about all strategies."""
        return {
            "total_strategies": len(self._strategies),
            "strategies": [strategy.get_strategy_info() for strategy in self._strategies]
        }

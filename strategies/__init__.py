"""Strategy pattern implementations for document processing."""

from .document_strategies import (
    DocumentStrategy,
    TextDocumentStrategy,
    ImageDocumentStrategy,
    PDFDocumentStrategy,
    DocumentStrategyFactory
)
from .output_format_strategies import (
    OutputFormatStrategy,
    MarkdownOutputStrategy,
    CSVOutputStrategy,
    JSONOutputStrategy,
    TextOutputStrategy,
    OutputFormatStrategyFactory
)
from .compression_strategies import (
    CompressionStrategy,
    ImageCompressionStrategy,
    NoCompressionStrategy,
    CompressionStrategyFactory
)

__all__ = [
    # Document strategies
    "DocumentStrategy",
    "TextDocumentStrategy", 
    "ImageDocumentStrategy",
    "PDFDocumentStrategy",
    "DocumentStrategyFactory",
    
    # Output format strategies
    "OutputFormatStrategy",
    "MarkdownOutputStrategy",
    "CSVOutputStrategy", 
    "JSONOutputStrategy",
    "TextOutputStrategy",
    "OutputFormatStrategyFactory",
    
    # Compression strategies
    "CompressionStrategy",
    "ImageCompressionStrategy",
    "NoCompressionStrategy", 
    "CompressionStrategyFactory"
]

"""Output format strategies for different file formats."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from exceptions.output_exceptions import OutputFormatException
from config.config_manager import get_config_manager


class OutputFormatStrategy(ABC):
    """Abstract base class for output format strategies."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = get_config_manager()
    
    @abstractmethod
    def can_handle(self, format_type: str) -> bool:
        """
        Check if this strategy can handle the given format.
        
        Args:
            format_type: Format type to check
            
        Returns:
            True if strategy can handle the format
        """
        pass
    
    @abstractmethod
    def prepare_content(self, content: str) -> str:
        """
        Prepare content for the specific format.
        
        Args:
            content: Raw content to prepare
            
        Returns:
            Formatted content
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Get the file extension for this format.
        
        Returns:
            File extension (including dot)
        """
        pass
    
    @abstractmethod
    def get_mime_type(self) -> str:
        """
        Get the MIME type for this format.
        
        Returns:
            MIME type string
        """
        pass
    
    def validate_content(self, content: str) -> str:
        """
        Validate content for the format.
        
        Args:
            content: Content to validate
            
        Returns:
            Validated content
            
        Raises:
            OutputFormatException: If content is invalid
        """
        if not content:
            raise OutputFormatException(
                "Content cannot be empty",
                output_format=self.__class__.__name__.replace("Strategy", "").lower()
            )
        
        return content
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about this strategy.
        
        Returns:
            Strategy information dictionary
        """
        return {
            "strategy_name": self.__class__.__name__,
            "file_extension": self.get_file_extension(),
            "mime_type": self.get_mime_type()
        }


class MarkdownOutputStrategy(OutputFormatStrategy):
    """Strategy for handling markdown output format."""
    
    def can_handle(self, format_type: str) -> bool:
        """Check if format is markdown."""
        return format_type.lower() in ["markdown", "md"]
    
    def prepare_content(self, content: str) -> str:
        """Prepare content for markdown output."""
        content = self.validate_content(content)
        
        # Extract CSV blocks and remove them from main content
        csv_blocks = self._extract_csv_blocks(content)
        if csv_blocks:
            content = self._remove_all_csv_blocks(content)
            # Add references to generated CSV files
            content = self._add_csv_references(content, csv_blocks)
        
        # Clean up excessive whitespace
        content = self._clean_whitespace(content)
        
        return content
    
    def get_file_extension(self) -> str:
        """Get markdown file extension."""
        return ".md"
    
    def get_mime_type(self) -> str:
        """Get markdown MIME type."""
        return "text/markdown"
    
    def _extract_csv_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract CSV blocks from content."""
        from services.output_service import _extract_csv_blocks
        return _extract_csv_blocks(content)
    
    def _remove_all_csv_blocks(self, content: str) -> str:
        """Remove all CSV blocks from content."""
        from services.output_service import _remove_all_csv_blocks
        return _remove_all_csv_blocks(content)
    
    def _add_csv_references(self, content: str, csv_blocks: List[Dict[str, str]]) -> str:
        """Add references to generated CSV files."""
        if not csv_blocks:
            return content
        
        references = "\n\n**Generated CSV Files:**\n"
        for csv_block in csv_blocks:
            references += f"- {csv_block['original_section']}: `{csv_block['name']}.csv`\n"
        
        return content + references
    
    def _clean_whitespace(self, content: str) -> str:
        """Clean up excessive whitespace."""
        import re
        content = re.sub(r'\n\s*\n', '\n\n', content)
        return content.strip()


class CSVOutputStrategy(OutputFormatStrategy):
    """Strategy for handling CSV output format."""
    
    def can_handle(self, format_type: str) -> bool:
        """Check if format is CSV."""
        return format_type.lower() == "csv"
    
    def prepare_content(self, content: str) -> str:
        """Prepare content for CSV output."""
        content = self.validate_content(content)
        
        # Extract CSV content from markdown blocks
        content = self._sanitize_csv_content(content)
        
        # Validate CSV format
        self._validate_csv_format(content)
        
        return content
    
    def get_file_extension(self) -> str:
        """Get CSV file extension."""
        return ".csv"
    
    def get_mime_type(self) -> str:
        """Get CSV MIME type."""
        return "text/csv"
    
    def _sanitize_csv_content(self, content: str) -> str:
        """Sanitize content for CSV output."""
        from services.output_service import _sanitize_csv_content
        return _sanitize_csv_content(content)
    
    def _validate_csv_format(self, content: str) -> None:
        """Validate that content is valid CSV format."""
        lines = content.strip().split('\n')
        if not lines:
            raise OutputFormatException(
                "CSV content has no data",
                output_format="csv"
            )
        
        # Check for consistent column count
        first_line_cols = len(lines[0].split(','))
        for i, line in enumerate(lines[1:], 1):
            cols = len(line.split(','))
            if cols != first_line_cols:
                self.logger.warning(
                    "CSV row has different column count",
                    extra={
                        "row": i + 1,
                        "expected_cols": first_line_cols,
                        "actual_cols": cols
                    }
                )


class JSONOutputStrategy(OutputFormatStrategy):
    """Strategy for handling JSON output format."""
    
    def can_handle(self, format_type: str) -> bool:
        """Check if format is JSON."""
        return format_type.lower() == "json"
    
    def prepare_content(self, content: str) -> str:
        """Prepare content for JSON output."""
        content = self.validate_content(content)
        
        # Try to parse and reformat JSON
        try:
            import json
            parsed = json.loads(content)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            return formatted
        except json.JSONDecodeError as e:
            # If content is not valid JSON, wrap it in a JSON structure
            wrapped = {
                "content": content,
                "format": "wrapped_text",
                "original_error": str(e)
            }
            return json.dumps(wrapped, indent=2, ensure_ascii=False)
    
    def get_file_extension(self) -> str:
        """Get JSON file extension."""
        return ".json"
    
    def get_mime_type(self) -> str:
        """Get JSON MIME type."""
        return "application/json"


class TextOutputStrategy(OutputFormatStrategy):
    """Strategy for handling plain text output format."""
    
    def can_handle(self, format_type: str) -> bool:
        """Check if format is text."""
        return format_type.lower() in ["text", "txt", "plain"]
    
    def prepare_content(self, content: str) -> str:
        """Prepare content for text output."""
        content = self.validate_content(content)
        
        # Clean up formatting for plain text
        content = self._clean_for_text(content)
        
        return content
    
    def get_file_extension(self) -> str:
        """Get text file extension."""
        return ".txt"
    
    def get_mime_type(self) -> str:
        """Get text MIME type."""
        return "text/plain"
    
    def _clean_for_text(self, content: str) -> str:
        """Clean content for plain text output."""
        import re
        
        # Remove markdown formatting
        content = re.sub(r'#{1,6}\s*', '', content)  # Remove headers
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)  # Remove italic
        content = re.sub(r'`(.*?)`', r'\1', content)  # Remove inline code
        
        # Clean up whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()


class OutputFormatStrategyFactory:
    """Factory for creating output format strategies."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._strategies = [
            MarkdownOutputStrategy(),
            CSVOutputStrategy(),
            JSONOutputStrategy(),
            TextOutputStrategy()
        ]
    
    def get_strategy(self, format_type: str) -> OutputFormatStrategy:
        """
        Get the appropriate strategy for the output format.
        
        Args:
            format_type: Format type to handle
            
        Returns:
            Appropriate output format strategy
            
        Raises:
            OutputFormatException: If no strategy can handle the format
        """
        for strategy in self._strategies:
            if strategy.can_handle(format_type):
                self.logger.debug(
                    "Output format strategy selected",
                    extra={
                        "strategy": strategy.__class__.__name__,
                        "format_type": format_type
                    }
                )
                return strategy
        
        # List supported formats in error
        supported_formats = []
        for strategy in self._strategies:
            if hasattr(strategy, 'can_handle'):
                # This is a simplified approach - in reality, we'd need to know which formats each strategy handles
                supported_formats.extend(strategy.__class__.__name__.lower().replace('strategy', '').split('_'))
        
        raise OutputFormatException(
            f"No strategy available for output format: {format_type}",
            output_format=format_type,
            supported_formats=supported_formats
        )
    
    def get_all_strategies(self) -> List[OutputFormatStrategy]:
        """Get all available strategies."""
        return self._strategies.copy()
    
    def get_supported_formats(self) -> List[str]:
        """Get all supported output formats."""
        return ["markdown", "csv", "json", "text"]
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about all strategies."""
        return {
            "total_strategies": len(self._strategies),
            "strategies": [strategy.get_strategy_info() for strategy in self._strategies],
            "supported_formats": self.get_supported_formats()
        }

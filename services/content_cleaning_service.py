"""Service for cleaning and normalizing text content."""

import re
import html
from typing import Dict
from utils.logger import get_logger
from exceptions.base_exceptions import ValidationException


class ContentCleaningService:
    """Service for cleaning Unicode characters and normalizing text content."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._unicode_box_mappings = self._get_unicode_box_mappings()
        self._unicode_to_ascii_mappings = self._get_unicode_to_ascii_mappings()
        self._escape_mappings = self._get_escape_mappings()
    
    def clean_unicode_box_characters(self, content: str) -> str:
        """
        Replace Unicode box-drawing characters with ASCII equivalents.
        This prevents special characters like ══ from appearing in prompts.
        
        Args:
            content: Text content to clean
            
        Returns:
            Cleaned content with ASCII equivalents
            
        Raises:
            ValidationException: If content is not a string
        """
        if not isinstance(content, str):
            raise ValidationException("Content must be a string", field="content", value=type(content))
        
        if not content:
            return content
            
        # Create regex pattern for all box characters
        box_pattern = re.compile(f"[{''.join(self._unicode_box_mappings.keys())}]")
        
        # Replace each box character with its ASCII equivalent
        cleaned_content = box_pattern.sub(
            lambda match: self._unicode_box_mappings[match.group()], 
            content
        )
        
        self.logger.debug(
            "Cleaned Unicode box characters from prompt",
            extra={
                "original_length": len(content),
                "cleaned_length": len(cleaned_content)
            }
        )
        
        return cleaned_content
    
    def clean_markdown_formatting(self, content: str) -> str:
        """
        Clean problematic Unicode characters that appear during internet transfer
        while preserving markdown structure for LLM comprehension.
        
        Args:
            content: Text content to clean
            
        Returns:
            Cleaned content with ASCII equivalents and preserved markdown
            
        Raises:
            ValidationException: If content is not a string
        """
        if not isinstance(content, str):
            raise ValidationException("Content must be a string", field="content", value=type(content))
        
        if not content:
            return content
        
        # Apply escape mappings first
        cleaned_content = self._apply_escape_mappings(content)
        
        # Handle HTML entities
        cleaned_content = self._decode_html_entities(cleaned_content)
        
        # Handle remaining numeric entities
        cleaned_content = self._clean_numeric_entities(cleaned_content)
        
        # Replace Unicode characters with ASCII equivalents
        cleaned_content = self._replace_unicode_characters(cleaned_content)
        
        # Clean up excessive whitespace while preserving structure
        cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content)
        cleaned_content = cleaned_content.strip()
        
        self.logger.debug(
            "Cleaned Unicode characters while preserving markdown",
            extra={
                "original_length": len(content),
                "cleaned_length": len(cleaned_content)
            }
        )
        
        return cleaned_content
    
    def clean_prompt_content(self, content: str) -> str:
        """
        Complete cleaning pipeline for prompt content.
        
        Args:
            content: Raw prompt content
            
        Returns:
            Fully cleaned prompt content
        """
        if not isinstance(content, str):
            raise ValidationException("Content must be a string", field="content", value=type(content))
        
        # Apply both cleaning steps
        unicode_cleaned = self.clean_unicode_box_characters(content)
        final_cleaned = self.clean_markdown_formatting(unicode_cleaned)
        
        return final_cleaned
    
    def _get_unicode_box_mappings(self) -> Dict[str, str]:
        """Get mappings for Unicode box characters to ASCII equivalents."""
        return {
            '═': '=', '─': '-', '│': '|', '┌': '+', '┐': '+', '└': '+', '┘': '+',
            '├': '+', '┤': '+', '┬': '+', '┴': '+', '┼': '+', '╔': '+', '╗': '+',
            '╚': '+', '╝': '+', '╠': '+', '╣': '+', '╦': '+', '╩': '+', '╬': '+',
            '║': '|', '╞': '+', '╡': '+', '╤': '+', '╥': '+', '╙': '+', '╘': '+',
            '╒': '+', '╓': '+', '╫': '+', '╪': '+', '┝': '+', '┠': '+', '┣': '+',
            '┥': '+', '┨': '+', '┫': '+', '┭': '+', '┮': '+', '┯': '+', '┰': '+',
            '┱': '+', '┲': '+', '┳': '+', '┵': '+', '┶': '+', '┷': '+', '┸': '+',
            '┹': '+', '┺': '+', '┻': '+', '┽': '+', '┾': '+', '┿': '+', '╀': '+',
            '╁': '+', '╂': '+', '╃': '+', '╄': '+', '╅': '+', '╆': '+', '╇': '+',
            '╈': '+', '╉': '+', '╊': '+'
        }
    
    def _get_unicode_to_ascii_mappings(self) -> Dict[str, str]:
        """Get mappings for Unicode characters to ASCII equivalents."""
        return {
            '═': '=', '─': '-', '│': '|', '┌': '+', '┐': '+', '└': '+', '┘': '+',
            '├': '+', '┤': '+', '┬': '+', '┴': '+', '┼': '+', '╔': '+', '╗': '+',
            '╚': '+', '╝': '+', '╠': '+', '╣': '+', '╦': '+', '╩': '+', '╬': '+',
            '║': '|', '•': '-',     # bullet points
            '→': '->',    # arrows
            '—': '--',    # em dash
            '–': '-',     # en dash
            '\u201c': '"',  # left double quotation mark (U+201C)
            '\u201d': '"',  # right double quotation mark (U+201D)
            '\u2018': "'",  # left single quotation mark (U+2018)
            '\u2019': "'",  # right single quotation mark (U+2019)
        }
    
    def _get_escape_mappings(self) -> Dict[str, str]:
        """Get mappings for HTML/JSON escaped characters."""
        return {
            '\\r\\n': '\n', '\\r': '\n', '\\n': '\n',
            '&amp;amp;': '&', '&amp;': '&', '&lt;': '<', '&gt;': '>',
            '&quot;': '"', '&#39;': "'", '&apos;': "'",
            '&amp;#40;': '(', '&amp;#41;': ')', '&#40;': '(', '&#41;': ')',
            '&amp;#x27;': "'", '&amp;#x2F;': '/', '&#x27;': "'", '&#x2F;': '/',
        }
    
    def _apply_escape_mappings(self, content: str) -> str:
        """Apply escape mappings to content."""
        for escaped, replacement in self._escape_mappings.items():
            content = content.replace(escaped, replacement)
        return content
    
    def _decode_html_entities(self, content: str) -> str:
        """Decode HTML entities in content."""
        try:
            return html.unescape(content)
        except Exception as e:
            self.logger.warning(f"HTML unescape failed: {e}")
            return content
    
    def _clean_numeric_entities(self, content: str) -> str:
        """Clean remaining HTML numeric entities."""
        # Manual cleanup for any remaining escaped sequences
        content = re.sub(r'&amp;#(\d+);', lambda m: chr(int(m.group(1))), content)
        content = re.sub(r'&amp;#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), content)
        content = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), content)
        content = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), content)
        return content
    
    def _replace_unicode_characters(self, content: str) -> str:
        """Replace Unicode characters with ASCII equivalents."""
        unicode_pattern = re.compile(f"[{''.join(self._unicode_to_ascii_mappings.keys())}]")
        return unicode_pattern.sub(
            lambda match: self._unicode_to_ascii_mappings[match.group()], 
            content
        )

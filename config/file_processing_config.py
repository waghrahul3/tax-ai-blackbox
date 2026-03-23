"""File processing configuration and supported formats."""

import os
from typing import Dict, Set, List
from utils.logger import get_logger
from exceptions.base_exceptions import ConfigurationException


class FileProcessingConfig:
    """Centralized file processing configuration."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._config = self._load_file_config()
    
    def _load_file_config(self) -> Dict[str, any]:
        """Load file processing configuration."""
        config = {
            "supported_text_extensions": self._get_text_extensions(),
            "supported_image_extensions": self._get_image_extensions(),
            "supported_pdf_extensions": {'.pdf'},
            "output_directory": os.getenv("OUTPUT_DIRECTORY", "output"),
            "temp_directory": os.getenv("TEMP_DIRECTORY", "/tmp"),
            "upload_directory": os.getenv("UPLOAD_DIRECTORY", "uploads"),
            "enable_file_compression": self._get_bool_setting("ENABLE_FILE_COMPRESSION", True),
            "compression_quality": self._get_int_setting("COMPRESSION_QUALITY", 85),
            "max_filename_length": self._get_int_setting("MAX_FILENAME_LENGTH", 255),
            "allowed_mime_types": self._get_allowed_mime_types(),
            "blocked_file_patterns": self._get_blocked_patterns(),
            "max_concurrent_uploads": self._get_int_setting("MAX_CONCURRENT_UPLOADS", 5)
        }
        
        self.logger.info(
            "File processing config loaded",
            extra={
                "text_extensions": len(config["supported_text_extensions"]),
                "image_extensions": len(config["supported_image_extensions"]),
                "output_directory": config["output_directory"],
                "enable_compression": config["enable_file_compression"]
            }
        )
        
        return config
    
    def _get_text_extensions(self) -> Set[str]:
        """Get supported text file extensions."""
        extensions_env = os.getenv("SUPPORTED_TEXT_EXTENSIONS", "")
        if extensions_env:
            extensions = {ext.strip().lower() for ext in extensions_env.split(',')}
            return {ext if ext.startswith('.') else f'.{ext}' for ext in extensions}
        
        # Default extensions
        return {
            '.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm',
            '.rtf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
        }
    
    def _get_image_extensions(self) -> Set[str]:
        """Get supported image file extensions."""
        extensions_env = os.getenv("SUPPORTED_IMAGE_EXTENSIONS", "")
        if extensions_env:
            extensions = {ext.strip().lower() for ext in extensions_env.split(',')}
            return {ext if ext.startswith('.') else f'.{ext}' for ext in extensions}
        
        # Default extensions
        return {
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'
        }
    
    def _get_bool_setting(self, env_var: str, default: bool) -> bool:
        """Get boolean setting from environment variable."""
        value = os.getenv(env_var)
        if value is None:
            return default
        
        value = value.strip().lower()
        if value in {"1", "true", "yes", "on"}:
            return True
        elif value in {"0", "false", "no", "off"}:
            return False
        else:
            return default
    
    def _get_int_setting(self, env_var: str, default: int) -> int:
        """Get integer setting from environment variable."""
        value = os.getenv(env_var)
        if value is None:
            return default
        
        try:
            return int(value)
        except ValueError:
            return default
    
    def _get_allowed_mime_types(self) -> Set[str]:
        """Get allowed MIME types."""
        mime_env = os.getenv("ALLOWED_MIME_TYPES", "")
        if mime_env:
            return {mime.strip().lower() for mime in mime_env.split(',')}
        
        # Default MIME types
        return {
            # Text types
            'text/plain', 'text/html', 'text/css', 'text/javascript', 'text/csv',
            'text/markdown', 'application/json', 'application/xml', 'text/xml',
            
            # Document types
            'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            
            # Image types
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
            'image/tiff', 'image/svg+xml'
        }
    
    def _get_blocked_patterns(self) -> List[str]:
        """Get blocked file patterns."""
        patterns_env = os.getenv("BLOCKED_FILE_PATTERNS", "")
        if patterns_env:
            return [pattern.strip() for pattern in patterns_env.split(',')]
        
        # Default blocked patterns
        return [
            '*.exe', '*.bat', '*.cmd', '*.com', '*.pif', '*.scr', '*.vbs', '*.js',
            '*.jar', '*.app', '*.deb', '*.rpm', '*.dmg', '*.pkg', '*.msi',
            '.*', '*~', '*.tmp', '*.temp', '*.swp', '*.swo'
        ]
    
    def is_supported_extension(self, extension: str, file_type: str = None) -> bool:
        """
        Check if a file extension is supported.
        
        Args:
            extension: File extension (with or without dot)
            file_type: Optional file type hint ('text', 'image', 'pdf')
            
        Returns:
            True if extension is supported
        """
        # Normalize extension
        if not extension.startswith('.'):
            extension = f'.{extension}'
        extension = extension.lower()
        
        if file_type:
            if file_type == 'text':
                return extension in self._config["supported_text_extensions"]
            elif file_type == 'image':
                return extension in self._config["supported_image_extensions"]
            elif file_type == 'pdf':
                return extension in self._config["supported_pdf_extensions"]
        
        # Check all supported extensions
        all_extensions = (
            self._config["supported_text_extensions"] |
            self._config["supported_image_extensions"] |
            self._config["supported_pdf_extensions"]
        )
        
        return extension in all_extensions
    
    def is_allowed_mime_type(self, mime_type: str) -> bool:
        """
        Check if a MIME type is allowed.
        
        Args:
            mime_type: MIME type to check
            
        Returns:
            True if MIME type is allowed
        """
        return mime_type.lower() in self._config["allowed_mime_types"]
    
    def is_blocked_filename(self, filename: str) -> bool:
        """
        Check if a filename matches blocked patterns.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if filename is blocked
        """
        import fnmatch
        
        filename_lower = filename.lower()
        for pattern in self._config["blocked_file_patterns"]:
            if fnmatch.fnmatch(filename_lower, pattern.lower()):
                return True
        
        return False
    
    def get_supported_extensions(self, file_type: str = None) -> Set[str]:
        """
        Get supported extensions for a file type.
        
        Args:
            file_type: Optional file type filter
            
        Returns:
            Set of supported extensions
        """
        if file_type == 'text':
            return self._config["supported_text_extensions"].copy()
        elif file_type == 'image':
            return self._config["supported_image_extensions"].copy()
        elif file_type == 'pdf':
            return self._config["supported_pdf_extensions"].copy()
        
        # Return all extensions
        return (
            self._config["supported_text_extensions"] |
            self._config["supported_image_extensions"] |
            self._config["supported_pdf_extensions"]
        )
    
    def get_file_type_from_extension(self, extension: str) -> str:
        """
        Determine file type from extension.
        
        Args:
            extension: File extension
            
        Returns:
            File type ('text', 'image', 'pdf', 'unknown')
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        extension = extension.lower()
        
        if extension in self._config["supported_text_extensions"]:
            return 'text'
        elif extension in self._config["supported_image_extensions"]:
            return 'image'
        elif extension in self._config["supported_pdf_extensions"]:
            return 'pdf'
        else:
            return 'unknown'
    
    def get_directory_config(self) -> Dict[str, str]:
        """Get directory configuration."""
        return {
            "output_directory": self._config["output_directory"],
            "temp_directory": self._config["temp_directory"],
            "upload_directory": self._config["upload_directory"]
        }
    
    def get_compression_config(self) -> Dict[str, any]:
        """Get compression configuration."""
        return {
            "enable_compression": self._config["enable_file_compression"],
            "compression_quality": self._config["compression_quality"]
        }
    
    def get_validation_config(self) -> Dict[str, any]:
        """Get validation configuration."""
        return {
            "max_filename_length": self._config["max_filename_length"],
            "allowed_mime_types": self._config["allowed_mime_types"].copy(),
            "blocked_patterns": self._config["blocked_file_patterns"].copy(),
            "max_concurrent_uploads": self._config["max_concurrent_uploads"]
        }
    
    def get_config_summary(self) -> Dict[str, any]:
        """Get configuration summary."""
        return {
            "supported_extensions": {
                "text": len(self._config["supported_text_extensions"]),
                "image": len(self._config["supported_image_extensions"]),
                "pdf": len(self._config["supported_pdf_extensions"]),
                "total": len(self.get_supported_extensions())
            },
            "directories": self.get_directory_config(),
            "compression": self.get_compression_config(),
            "validation": {
                "max_filename_length": self._config["max_filename_length"],
                "allowed_mime_types": len(self._config["allowed_mime_types"]),
                "blocked_patterns": len(self._config["blocked_file_patterns"])
            }
        }

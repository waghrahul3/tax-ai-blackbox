"""PDF processing configuration management."""

import os
from typing import List, Optional
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PDFProcessingConfig:
    """Configuration for PDF processing operations."""
    
    # Password extraction settings
    password_patterns: List[str]
    enable_password_extraction: bool
    case_sensitive_patterns: bool
    
    # File handling settings
    decrypted_file_suffix: str
    temp_file_cleanup: bool
    
    # Processing settings
    max_pdf_size_mb: int
    enable_decryption_fallback: bool
    
    @classmethod
    def from_environment(cls) -> 'PDFProcessingConfig':
        """Create configuration from environment variables."""
        try:
            # Password extraction patterns
            patterns_str = os.getenv("PDF_PASSWORD_PATTERNS", "_password_,_pwd_,_secure_")
            password_patterns = [p.strip() for p in patterns_str.split(",") if p.strip()]
            
            # Feature flags
            enable_password_extraction = os.getenv("ENABLE_PASSWORD_EXTRACTION", "true").lower() == "true"
            case_sensitive_patterns = os.getenv("PDF_PATTERN_CASE_SENSITIVE", "false").lower() == "true"
            
            # File handling
            decrypted_file_suffix = os.getenv("DECRYPTED_FILE_SUFFIX", "_decrypted")
            temp_file_cleanup = os.getenv("TEMP_FILE_CLEANUP", "true").lower() == "true"
            
            # Processing limits
            max_pdf_size_mb = int(os.getenv("MAX_PDF_SIZE_MB", "50"))
            enable_decryption_fallback = os.getenv("ENABLE_DECRYPTION_FALLBACK", "true").lower() == "true"
            
            config = cls(
                password_patterns=password_patterns,
                enable_password_extraction=enable_password_extraction,
                case_sensitive_patterns=case_sensitive_patterns,
                decrypted_file_suffix=decrypted_file_suffix,
                temp_file_cleanup=temp_file_cleanup,
                max_pdf_size_mb=max_pdf_size_mb,
                enable_decryption_fallback=enable_decryption_fallback
            )
            
            logger.info(
                "PDF configuration loaded",
                extra={
                    "password_patterns": password_patterns,
                    "enable_password_extraction": enable_password_extraction,
                    "case_sensitive": case_sensitive_patterns,
                    "max_pdf_size_mb": max_pdf_size_mb
                }
            )
            
            return config
            
        except Exception as e:
            logger.error(
                "Failed to load PDF configuration, using defaults",
                extra={"error": str(e)}
            )
            # Return safe defaults
            return cls(
                password_patterns=["_password_"],
                enable_password_extraction=True,
                case_sensitive_patterns=False,
                decrypted_file_suffix="_decrypted",
                temp_file_cleanup=True,
                max_pdf_size_mb=50,
                enable_decryption_fallback=True
            )
    
    def validate_password_patterns(self) -> bool:
        """Validate password patterns are properly formatted."""
        if not self.password_patterns:
            return False
        
        for pattern in self.password_patterns:
            if not pattern or not pattern.strip():
                logger.warning("Empty password pattern found", extra={"pattern": pattern})
                return False
        
        return True
    
    def is_decrypted_file(self, file_path: str) -> bool:
        """Check if a file path points to a decrypted copy."""
        return self.decrypted_file_suffix in file_path
    
    def get_max_pdf_size_bytes(self) -> int:
        """Get maximum PDF size in bytes."""
        return self.max_pdf_size_mb * 1024 * 1024


# Global configuration instance
_pdf_config: Optional[PDFProcessingConfig] = None


def get_pdf_config() -> PDFProcessingConfig:
    """Get the global PDF configuration instance."""
    global _pdf_config
    if _pdf_config is None:
        _pdf_config = PDFProcessingConfig.from_environment()
    return _pdf_config


def reset_pdf_config() -> None:
    """Reset the PDF configuration (mainly for testing)."""
    global _pdf_config
    _pdf_config = None

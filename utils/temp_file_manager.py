"""Temporary file management utilities."""

import os
import tempfile
import threading
from typing import Optional, List
from contextlib import contextmanager
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TempFileInfo:
    """Information about a temporary file."""
    path: str
    purpose: str
    created_at: float
    thread_id: int


class TemporaryFileManager:
    """Manages temporary file creation and cleanup."""
    
    def __init__(self, enable_cleanup: bool = True):
        self.enable_cleanup = enable_cleanup
        self._temp_files: List[TempFileInfo] = []
        self._lock = threading.Lock()
    
    def create_temp_file(self, suffix: str = "", purpose: str = "general") -> str:
        """Create a temporary file and track it for cleanup."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                temp_path = tmp_file.name
            
            file_info = TempFileInfo(
                path=temp_path,
                purpose=purpose,
                created_at=threading.get_ident(),
                thread_id=threading.get_ident()
            )
            
            with self._lock:
                self._temp_files.append(file_info)
            
            logger.debug(
                "Created temporary file",
                extra={
                    "path": temp_path,
                    "purpose": purpose,
                    "suffix": suffix
                }
            )
            
            return temp_path
            
        except Exception as e:
            logger.error(
                "Failed to create temporary file",
                extra={"suffix": suffix, "purpose": purpose, "error": str(e)}
            )
            raise
    
    def create_temp_pdf(self, purpose: str = "pdf_processing") -> str:
        """Create a temporary PDF file."""
        return self.create_temp_file(suffix=".pdf", purpose=purpose)
    
    def create_decrypted_pdf(self, purpose: str = "pdf_decryption") -> str:
        """Create a temporary file for decrypted PDF."""
        from config.pdf_config import get_pdf_config
        config = get_pdf_config()
        return self.create_temp_file(suffix=config.decrypted_file_suffix + ".pdf", purpose=purpose)
    
    def cleanup_file(self, file_path: str) -> bool:
        """Clean up a specific temporary file."""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                
                # Remove from tracking
                with self._lock:
                    self._temp_files = [
                        f for f in self._temp_files 
                        if f.path != file_path
                    ]
                
                logger.debug(
                    "Cleaned up temporary file",
                    extra={"path": file_path}
                )
                return True
            else:
                logger.warning(
                    "Temporary file not found for cleanup",
                    extra={"path": file_path}
                )
                return False
                
        except Exception as e:
            logger.error(
                "Failed to cleanup temporary file",
                extra={"path": file_path, "error": str(e)}
            )
            return False
    
    def cleanup_all(self) -> int:
        """Clean up all tracked temporary files."""
        if not self.enable_cleanup:
            logger.info("Temporary file cleanup is disabled")
            return 0
        
        cleaned_count = 0
        with self._lock:
            files_to_cleanup = self._temp_files.copy()
            self._temp_files.clear()
        
        for file_info in files_to_cleanup:
            if self.cleanup_file(file_info.path):
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(
                "Cleaned up temporary files",
                extra={"count": cleaned_count}
            )
        
        return cleaned_count
    
    def get_tracked_files(self) -> List[TempFileInfo]:
        """Get list of tracked temporary files."""
        with self._lock:
            return self._temp_files.copy()
    
    def get_file_count(self) -> int:
        """Get number of tracked temporary files."""
        with self._lock:
            return len(self._temp_files)
    
    @contextmanager
    def managed_temp_file(self, suffix: str = "", purpose: str = "general"):
        """Context manager for temporary file with automatic cleanup."""
        temp_path = None
        try:
            temp_path = self.create_temp_file(suffix=suffix, purpose=purpose)
            yield temp_path
        finally:
            if temp_path:
                self.cleanup_file(temp_path)
    
    @contextmanager
    def managed_temp_pdf(self, purpose: str = "pdf_processing"):
        """Context manager for temporary PDF with automatic cleanup."""
        temp_path = None
        try:
            temp_path = self.create_temp_pdf(purpose=purpose)
            yield temp_path
        finally:
            if temp_path:
                self.cleanup_file(temp_path)


# Global instance
_temp_manager: Optional[TemporaryFileManager] = None


def get_temp_manager() -> TemporaryFileManager:
    """Get the global temporary file manager instance."""
    global _temp_manager
    if _temp_manager is None:
        from config.pdf_config import get_pdf_config
        config = get_pdf_config()
        _temp_manager = TemporaryFileManager(enable_cleanup=config.temp_file_cleanup)
    return _temp_manager


def reset_temp_manager() -> None:
    """Reset the temporary file manager (mainly for testing)."""
    global _temp_manager
    if _temp_manager:
        _temp_manager.cleanup_all()
    _temp_manager = None

"""Service for validating files and ensuring they meet requirements."""

from typing import List, Dict, Set
from utils.logger import get_logger
from utils.image_handler import is_image_file
from exceptions.document_exceptions import FileValidationException


class FileValidationService:
    """Service for validating uploaded files and ensuring they meet requirements."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._supported_text_extensions = {
            '.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm'
        }
        self._supported_image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'
        }
        self._supported_pdf_extensions = {'.pdf'}
        self._max_file_size = 50 * 1024 * 1024  # 50MB
        self._max_image_size = 4_500_000  # 4.5MB for API safety
    
    def validate_files(self, files: List) -> Dict[str, any]:
        """
        Validate a list of uploaded files.
        
        Args:
            files: List of uploaded files to validate
            
        Returns:
            Dictionary with validation results
            
        Raises:
            FileValidationException: If any file validation fails
        """
        if not files:
            raise FileValidationException("No files provided", validation_rule="files_required")
        
        validation_results = {
            "total_files": len(files),
            "valid_files": 0,
            "invalid_files": 0,
            "file_details": [],
            "warnings": []
        }
        
        for file in files:
            try:
                file_info = self._validate_single_file(file)
                validation_results["file_details"].append(file_info)
                validation_results["valid_files"] += 1
                
            except FileValidationException as e:
                validation_results["invalid_files"] += 1
                validation_results["file_details"].append({
                    "filename": getattr(file, 'filename', 'unknown'),
                    "valid": False,
                    "error": str(e),
                    "validation_rule": e.validation_rule
                })
                raise  # Re-raise the first validation error
        
        return validation_results
    
    def _validate_single_file(self, file) -> Dict[str, any]:
        """
        Validate a single uploaded file.
        
        Args:
            file: Uploaded file to validate
            
        Returns:
            Dictionary with file validation information
            
        Raises:
            FileValidationException: If file validation fails
        """
        # Basic file object validation
        self._validate_file_object(file)
        
        filename = getattr(file, 'filename', 'unknown')
        file_size = getattr(file, 'size', 0)
        content_type = getattr(file, 'content_type', '')
        
        # Filename validation
        self._validate_filename(filename)
        
        # File size validation
        self._validate_file_size(file_size, filename)
        
        # File type validation
        file_type = self._determine_file_type(filename, content_type)
        self._validate_file_type(file_type, filename)
        
        # Content-type validation
        self._validate_content_type(content_type, file_type, filename)
        
        # Image-specific validation
        if file_type == "image":
            self._validate_image_file(file, filename)
        
        return {
            "filename": filename,
            "file_size": file_size,
            "content_type": content_type,
            "file_type": file_type,
            "valid": True,
            "warnings": self._get_file_warnings(file_size, file_type)
        }
    
    def _validate_file_object(self, file) -> None:
        """Validate the file object itself."""
        if file is None:
            raise FileValidationException("File object is None", validation_rule="file_object_required")
    
    def _validate_filename(self, filename: str) -> None:
        """Validate filename format and safety."""
        if not filename:
            raise FileValidationException("Filename is required", validation_rule="filename_required")
        
        if not isinstance(filename, str):
            raise FileValidationException("Filename must be a string", validation_rule="filename_type")
        
        if filename.strip() == "":
            raise FileValidationException("Filename cannot be empty", validation_rule="filename_not_empty")
        
        # Check for dangerous characters
        dangerous_patterns = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(pattern in filename for pattern in dangerous_patterns):
            raise FileValidationException(
                "Filename contains invalid characters",
                filename=filename,
                validation_rule="filename_safe_chars"
            )
        
        # Check filename length
        if len(filename) > 255:
            raise FileValidationException(
                "Filename is too long (max 255 characters)",
                filename=filename,
                validation_rule="filename_length"
            )
    
    def _validate_file_size(self, file_size: int, filename: str) -> None:
        """Validate file size."""
        if file_size < 0:
            raise FileValidationException(
                "File size cannot be negative",
                filename=filename,
                file_size=file_size,
                validation_rule="file_size_positive"
            )
        
        if file_size > self._max_file_size:
            raise FileValidationException(
                f"File size exceeds maximum allowed size ({self._max_file_size / 1024 / 1024:.1f}MB)",
                filename=filename,
                file_size=file_size,
                validation_rule="file_size_limit"
            )
    
    def _determine_file_type(self, filename: str, content_type: str) -> str:
        """Determine the type of file based on filename and content type."""
        filename_lower = filename.lower()
        content_type_lower = content_type.lower()
        
        # Check for PDF
        if (filename_lower.endswith('.pdf') or 
            content_type_lower == 'application/pdf'):
            return "pdf"
        
        # Check for image
        if is_image_file(filename, content_type):
            return "image"
        
        # Check for text
        if any(filename_lower.endswith(ext) for ext in self._supported_text_extensions):
            return "text"
        
        # Default to text for unknown types
        return "text"
    
    def _validate_file_type(self, file_type: str, filename: str) -> None:
        """Validate that the file type is supported."""
        supported_types = {"text", "image", "pdf"}
        if file_type not in supported_types:
            raise FileValidationException(
                f"Unsupported file type: {file_type}",
                filename=filename,
                file_type=file_type,
                validation_rule="file_type_supported"
            )
    
    def _validate_content_type(self, content_type: str, file_type: str, filename: str) -> None:
        """Validate content type matches file type."""
        if not content_type:
            return  # Content type is optional
        
        content_type_lower = content_type.lower()
        
        # Basic validation for common mismatches
        if file_type == "image" and not content_type_lower.startswith("image/"):
            self.logger.warning(
                "Content type doesn't match file type",
                extra={
                    "filename": filename,
                    "file_type": file_type,
                    "content_type": content_type
                }
            )
        
        elif file_type == "pdf" and content_type_lower != "application/pdf":
            self.logger.warning(
                "Content type doesn't match file type",
                extra={
                    "filename": filename,
                    "file_type": file_type,
                    "content_type": content_type
                }
            )
    
    def _validate_image_file(self, file, filename: str) -> None:
        """Validate image-specific requirements."""
        # Additional image validation could be added here
        # For now, we rely on the image handler for processing
        pass
    
    def _get_file_warnings(self, file_size: int, file_type: str) -> List[str]:
        """Get warnings for the file."""
        warnings = []
        
        # Large file warning
        if file_size > self._max_file_size * 0.8:  # 80% of max size
            warnings.append(f"Large file ({file_size / 1024 / 1024:.1f}MB)")
        
        # Image size warning
        if file_type == "image" and file_size > self._max_image_size:
            warnings.append(f"Image will be compressed ({file_size / 1024 / 1024:.1f}MB > {self._max_image_size / 1024 / 1024:.1f}MB)")
        
        return warnings
    
    def get_supported_extensions(self) -> Dict[str, Set[str]]:
        """Get all supported file extensions by type."""
        return {
            "text": self._supported_text_extensions.copy(),
            "image": self._supported_image_extensions.copy(),
            "pdf": self._supported_pdf_extensions.copy()
        }
    
    def get_validation_limits(self) -> Dict[str, int]:
        """Get validation limits."""
        return {
            "max_file_size": self._max_file_size,
            "max_image_size": self._max_image_size,
            "max_filename_length": 255
        }

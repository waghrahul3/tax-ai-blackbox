import base64
from typing import Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


def is_image_file(filename: str, content_type: str = "") -> bool:
    """Check if a file is an image based on filename or content type."""
    
    filename_lower = filename.lower()
    content_type_lower = content_type.lower()
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
    image_content_types = ('image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp')
    
    return (
        filename_lower.endswith(image_extensions) or
        content_type_lower in image_content_types
    )


def get_image_media_type(filename: str, content_type: str = "") -> str:
    """Determine the media type for an image file."""
    
    filename_lower = filename.lower()
    content_type_lower = content_type.lower()
    
    if content_type_lower in ('image/jpeg', 'image/jpg'):
        return "image/jpeg"
    elif content_type_lower == 'image/png':
        return "image/png"
    elif content_type_lower == 'image/gif':
        return "image/gif"
    elif content_type_lower == 'image/webp':
        return "image/webp"
    
    if filename_lower.endswith(('.jpg', '.jpeg')):
        return "image/jpeg"
    elif filename_lower.endswith('.png'):
        return "image/png"
    elif filename_lower.endswith('.gif'):
        return "image/gif"
    elif filename_lower.endswith('.webp'):
        return "image/webp"
    
    return "image/jpeg"


def encode_image_for_claude(image_data: bytes, filename: str, content_type: str = "") -> Tuple[str, str]:
    """
    Encode image data to base64 for Claude API.
    
    Returns:
        Tuple of (base64_encoded_data, media_type)
    """
    
    media_type = get_image_media_type(filename, content_type)
    
    encoded = base64.standard_b64encode(image_data).decode('utf-8')
    
    logger.debug(
        "Encoded image for Claude",
        extra={
            "file_name": filename,
            "media_type": media_type,
            "original_size": len(image_data),
            "encoded_size": len(encoded)
        }
    )
    
    return encoded, media_type

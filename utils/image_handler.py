import base64
import io
from typing import Tuple
from PIL import Image
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


def compress_image_to_limit(image_data: bytes, max_bytes: int = 4_500_000) -> tuple[bytes, str]:
    """Compress image to stay under API size limit. Returns (compressed_bytes, media_type)."""
    if len(image_data) <= max_bytes:
        return image_data, "image/jpeg"
    
    logger.debug(
        "Compressing image",
        extra={"original_size": len(image_data), "target_size": max_bytes}
    )
    
    try:
        img = Image.open(io.BytesIO(image_data))
        img = img.convert("RGB")  # ensure no alpha channel
    except Exception as e:
        logger.warning(
            "Failed to open image for compression, returning original data",
            extra={"original_size": len(image_data), "error": str(e)}
        )
        return image_data, "image/jpeg"
    
    quality = 85
    while quality >= 20:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        compressed = buffer.getvalue()
        if len(compressed) <= max_bytes:
            logger.info(
                "Image compressed successfully",
                extra={
                    "original_size": len(image_data),
                    "compressed_size": len(compressed),
                    "quality": quality
                }
            )
            return compressed, "image/jpeg"
        quality -= 10
    
    # If still too large, resize by 50%
    logger.warning(
        "Quality reduction insufficient, resizing image",
        extra={"size_after_quality_reduction": len(compressed)}
    )
    
    img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=75)
    final_compressed = buffer.getvalue()
    
    logger.info(
        "Image resized and compressed",
        extra={
            "original_size": len(image_data),
            "final_size": len(final_compressed),
            "dimensions": (img.width, img.height)
        }
    )
    
    return final_compressed, "image/jpeg"

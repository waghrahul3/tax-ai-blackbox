from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class DocumentContent:
    """Represents a document that can be either text or an image."""
    
    content_type: Literal["text", "image"]
    filename: str
    
    text_content: Optional[str] = None
    
    image_data: Optional[bytes] = None
    image_media_type: Optional[str] = None
    
    def is_text(self) -> bool:
        return self.content_type == "text"
    
    def is_image(self) -> bool:
        return self.content_type == "image"
    
    def get_display_info(self) -> dict:
        """Get display information for logging."""
        if self.is_text():
            return {
                "type": "text",
                "file_name": self.filename,
                "length": len(self.text_content) if self.text_content else 0
            }
        else:
            return {
                "type": "image",
                "file_name": self.filename,
                "media_type": self.image_media_type,
                "size": len(self.image_data) if self.image_data else 0
            }

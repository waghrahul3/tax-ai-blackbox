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

    source_path: Optional[str] = None
    source_media_type: Optional[str] = None
    
    # Track if this document was processed with a password
    password_processed: Optional[bool] = None

    def is_text(self) -> bool:
        return self.content_type == "text"

    def is_image(self) -> bool:
        return self.content_type == "image"

    def get_display_info(self) -> dict:
        """Get display information for logging."""
        base = {
            "type": self.content_type,
            "file_name": self.filename,
        }

        if self.source_path:
            base["source_path"] = self.source_path

        if self.is_text():
            base["length"] = len(self.text_content) if self.text_content else 0
        else:
            base["media_type"] = self.image_media_type
            base["size"] = len(self.image_data) if self.image_data else 0

        return base

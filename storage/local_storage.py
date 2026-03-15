from utils.logger import get_logger
from utils.pdf_extractor import extract_text_from_pdf
from utils.image_handler import is_image_file, get_image_media_type
from models.document import DocumentContent


def _looks_like_pdf(file, data: bytes) -> bool:

    filename = (getattr(file, "filename", "") or "").lower()
    content_type = (getattr(file, "content_type", "") or "").lower()

    if filename.endswith(".pdf") or content_type == "application/pdf":
        return True

    return data.startswith(b"%PDF")


class LocalStorage:

    def __init__(self):

        self.logger = get_logger(__name__)

    async def read_file(self, file):

        data = await file.read()
        filename = getattr(file, "filename", "unknown")
        content_type = getattr(file, "content_type", "")

        if is_image_file(filename, content_type):
            media_type = get_image_media_type(filename, content_type)
            self.logger.info(
                "Detected image file",
                extra={"file_name": filename, "media_type": media_type, "size": len(data)}
            )
            return DocumentContent(
                content_type="image",
                filename=filename,
                image_data=data,
                image_media_type=media_type
            )

        if _looks_like_pdf(file, data):

            try:
                pdf_text = extract_text_from_pdf(data)

                if pdf_text.strip():
                    self.logger.info(
                        "Extracted PDF text",
                        extra={"file_name": filename, "length": len(pdf_text)}
                    )
                    return DocumentContent(
                        content_type="text",
                        filename=filename,
                        text_content=pdf_text
                    )

            except Exception:
                self.logger.exception(
                    "Failed to extract PDF text",
                    extra={"file_name": filename}
                )

        self.logger.debug(
            "Decoding file as text",
            extra={"file_name": filename, "length": len(data)}
        )

        text_content = data.decode("utf-8", errors="ignore")
        return DocumentContent(
            content_type="text",
            filename=filename,
            text_content=text_content
        )
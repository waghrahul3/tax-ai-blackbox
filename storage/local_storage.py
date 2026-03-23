import os
import tempfile

from langchain_community.document_loaders.image import UnstructuredImageLoader

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
        source_path = getattr(file, "file_path", None)

        if is_image_file(filename, content_type):
            media_type = get_image_media_type(filename, content_type)
            self.logger.info(
                "Detected image file",
                extra={"file_name": filename, "media_type": media_type, "size": len(data)}
            )

            extracted_text = self._extract_text_from_image(data, media_type)
            if extracted_text.strip():
                self.logger.info(
                    "Extracted image text via Unstructured",
                    extra={"file_name": filename, "length": len(extracted_text)}
                )
                return DocumentContent(
                    content_type="text",
                    filename=filename,
                    text_content=extracted_text
                )

            self.logger.warning(
                "Falling back to binary image ingestion; no text extracted",
                extra={"file_name": filename}
            )
            return DocumentContent(
                content_type="image",
                filename=filename,
                image_data=data,
                image_media_type=media_type,
                source_path=source_path,
                source_media_type=media_type or content_type
            )

        if _looks_like_pdf(file, data):
            # Always preserve PDF media type regardless of text extraction success
            pdf_media_type = "application/pdf"
            
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
                        text_content=pdf_text,
                        source_path=source_path,
                        source_media_type=pdf_media_type
                    )

            except Exception:
                self.logger.exception(
                    "Failed to extract PDF text",
                    extra={"file_name": filename}
                )

            # If text extraction failed or returned empty, still treat as PDF document
            self.logger.warning(
                "PDF text extraction failed or returned empty, treating as binary PDF",
                extra={"file_name": filename}
            )
            return DocumentContent(
                content_type="text",
                filename=filename,
                text_content="",  # Empty text content for failed extraction
                source_path=source_path,
                source_media_type=pdf_media_type
            )

        self.logger.debug(
            "Decoding file as text",
            extra={"file_name": filename, "length": len(data)}
        )

        text_content = data.decode("utf-8", errors="ignore")
        return DocumentContent(
            content_type="text",
            filename=filename,
            text_content=text_content,
            source_path=source_path,
            source_media_type=content_type or "text/plain"
        )

    def _extract_text_from_image(self, data: bytes, media_type: str) -> str:

        suffix = ".png"
        if media_type == "image/jpeg":
            suffix = ".jpg"
        elif media_type == "image/gif":
            suffix = ".gif"
        elif media_type == "image/webp":
            suffix = ".webp"

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(data)
                tmp_path = tmp_file.name

            loader = UnstructuredImageLoader(tmp_path)
            documents = loader.load()
            pieces = [
                doc.page_content.strip()
                for doc in documents
                if getattr(doc, "page_content", "").strip()
            ]
            return "\n\n".join(pieces)
        except Exception:
            self.logger.exception("Failed to extract text from image via Unstructured")
            return ""
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

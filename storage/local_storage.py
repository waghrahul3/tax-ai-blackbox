import os
import tempfile

from langchain_community.document_loaders.image import UnstructuredImageLoader

from utils.logger import get_logger
from utils.image_handler import is_image_file, get_image_media_type
from models.document import DocumentContent
from services.document_loader import MAX_IMAGE_BYTES
from services.pdf_processing_service import get_pdf_service


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
            # Check if image needs compression before storing
            compressed_image_data = data
            image_media_type = media_type or "image/jpeg"
            
            if len(data) > MAX_IMAGE_BYTES:
                self.logger.info(
                    "Compressing image in document loader",
                    extra={"file_name": filename, "original_size": len(data)}
                )
                try:
                    from utils.image_handler import compress_image_to_limit
                    compressed_image_data, _ = compress_image_to_limit(data)
                    self.logger.info(
                        "Image compressed in document loader",
                        extra={"file_name": filename, "compressed_size": len(compressed_image_data)}
                    )
                    compressed_image_data = compressed_image_data
                except Exception as e:
                    self.logger.error(
                        "Failed to compress image in document loader",
                        extra={"file_name": filename, "error": str(e)}
                    )
            
            return DocumentContent(
                content_type="image",
                filename=filename,
                image_data=compressed_image_data,  # ✅ Use compressed data
                image_media_type=image_media_type,
                source_path=source_path,
                source_media_type=media_type or content_type
            )

        if _looks_like_pdf(file, data):
            # Always preserve PDF media type regardless of text extraction success
            pdf_media_type = "application/pdf"
            
            # Use PDF processing service for all PDF operations
            try:
                pdf_service = get_pdf_service()
                processing_result = pdf_service.process_pdf(filename, data, source_path)
                
                # Create document content from processing result
                return pdf_service.create_document_content(
                    filename=filename,
                    result=processing_result,
                    original_path=source_path,
                    media_type=pdf_media_type
                )
                
            except Exception as e:
                # Handle password-protected PDF exceptions
                from exceptions.document_exceptions import PasswordProtectedPDFException
                if isinstance(e, PasswordProtectedPDFException):
                    self.logger.error(
                        "Password-protected PDF error",
                        extra={
                            "file_name": filename,
                            "error_code": e.error_code
                        }
                    )
                    raise  # Re-raise to be handled by upper layers
                else:
                    self.logger.exception(
                        "Failed to process PDF",
                        extra={"file_name": filename}
                    )

            # If we get here, processing failed but didn't raise an exception
            # Treat as binary PDF document
            self.logger.warning(
                "PDF processing failed, treating as binary PDF",
                extra={"file_name": filename}
            )
            return DocumentContent(
                content_type="text",
                filename=filename,
                text_content="",  # Empty text content for failed processing
                source_path=source_path,
                source_media_type=pdf_media_type,
                password_processed=False
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

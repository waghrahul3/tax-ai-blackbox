import os
import tempfile

from langchain_community.document_loaders import PyMuPDFLoader
from utils.logger import get_logger
from exceptions.document_exceptions import PasswordProtectedPDFException

logger = get_logger(__name__)


def extract_text_from_pdf(data: bytes, password: str = None) -> str:
    """
    Extract text from PDF data with optional password support.
    
    Args:
        data: PDF file data as bytes
        password: Optional password for encrypted PDFs
        
    Returns:
        Extracted text content
        
    Raises:
        PasswordProtectedPDFException: If PDF is password-protected and password is missing/incorrect
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name

    try:
        # Try to load PDF with or without password
        try:
            loader = PyMuPDFLoader(tmp_path, password=password)
            documents = loader.load()
            
            texts = [
                doc.page_content.strip()
                for doc in documents
                if getattr(doc, "page_content", "").strip()
            ]
            return "\n\n".join(texts)
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for password-related errors
            if any(keyword in error_msg for keyword in ["password", "encrypted", "auth", "invalid password"]):
                if password:
                    # Password was provided but is wrong
                    logger.warning(
                        "Wrong password provided for PDF",
                        extra={"error": str(e)}
                    )
                    raise PasswordProtectedPDFException(
                        "Wrong password provided",
                        error_code="wrong_password"
                    )
                else:
                    # No password provided but PDF is protected
                    logger.warning(
                        "PDF is password-protected but no password provided",
                        extra={"error": str(e)}
                    )
                    raise PasswordProtectedPDFException(
                        "PDF is password-protected",
                        error_code="password_required"
                    )
            else:
                # Other PDF errors (corrupted, invalid, etc.)
                logger.error(
                    "PDF processing failed",
                    extra={"error": str(e)}
                )
                raise PasswordProtectedPDFException(
                    "Invalid or corrupted PDF",
                    error_code="invalid_pdf"
                )
                
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def create_decrypted_pdf_copy(data: bytes, password: str) -> bytes:
    """
    Create a decrypted copy of a password-protected PDF.
    
    Args:
        data: Original encrypted PDF data as bytes
        password: Password to decrypt the PDF
        
    Returns:
        Decrypted PDF data as bytes (without password protection)
        
    Raises:
        PasswordProtectedPDFException: If decryption fails
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name

    try:
        # Open the PDF with password
        import fitz  # PyMuPDF
        doc = fitz.open(tmp_path)
        
        # Check if password is required and provided
        if doc.needs_pass:
            if not password:
                raise PasswordProtectedPDFException(
                    "PDF is password-protected",
                    error_code="password_required"
                )
            
            # Authenticate with password
            if not doc.authenticate(password):
                raise PasswordProtectedPDFException(
                    "Wrong password provided",
                    error_code="wrong_password"
                )
        
        # Create a new PDF without password protection
        decrypted_data = doc.tobytes()
        doc.close()
        
        logger.info(
            "Successfully created decrypted PDF copy",
            extra={"original_size": len(data), "decrypted_size": len(decrypted_data)}
        )
        
        return decrypted_data
        
    except PasswordProtectedPDFException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for password-related errors
        if any(keyword in error_msg for keyword in ["password", "encrypted", "auth", "invalid password"]):
            if password:
                logger.error(
                    "Failed to decrypt PDF with provided password",
                    extra={"error": str(e)}
                )
                raise PasswordProtectedPDFException(
                    "Wrong password provided",
                    error_code="wrong_password"
                )
            else:
                logger.error(
                    "PDF is password-protected but no password provided",
                    extra={"error": str(e)}
                )
                raise PasswordProtectedPDFException(
                    "PDF is password-protected",
                    error_code="password_required"
                )
        else:
            logger.error(
                "Failed to create decrypted PDF copy",
                extra={"error": str(e)}
            )
            raise PasswordProtectedPDFException(
                "Failed to decrypt PDF",
                error_code="invalid_pdf"
            )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

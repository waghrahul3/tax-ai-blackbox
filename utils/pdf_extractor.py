import os
import tempfile

from langchain_community.document_loaders import PyMuPDFLoader


def extract_text_from_pdf(data: bytes) -> str:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name

    try:
        loader = PyMuPDFLoader(tmp_path)
        documents = loader.load()
        texts = [
            doc.page_content.strip()
            for doc in documents
            if getattr(doc, "page_content", "").strip()
        ]
        return "\n\n".join(texts)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

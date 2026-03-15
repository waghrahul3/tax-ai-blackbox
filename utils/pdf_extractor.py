from io import BytesIO

from PyPDF2 import PdfReader


def extract_text_from_pdf(data: bytes) -> str:

    reader = PdfReader(BytesIO(data))

    texts = []

    for page in reader.pages:

        text = page.extract_text() or ""

        if text.strip():
            texts.append(text.strip())

    return "\n\n".join(texts)

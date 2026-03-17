import asyncio
import os
from datetime import datetime
from typing import List, Tuple
from uuid import uuid4

from fastapi import UploadFile

from utils.logger import get_logger

logger = get_logger(__name__)


class SavedUploadFile:

    def __init__(self, file_path: str, filename: str, content_type: str | None):

        self.file_path = file_path
        self.filename = filename
        self.content_type = content_type or "application/octet-stream"

    async def read(self) -> bytes:

        return await asyncio.to_thread(self._read_sync)

    def _read_sync(self) -> bytes:

        with open(self.file_path, "rb") as source:
            return source.read()


def generate_request_id() -> str:

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = uuid4().hex[:6]
    return f"{timestamp}_{suffix}"


async def persist_uploads(files: List[UploadFile], request_id: str) -> Tuple[List[SavedUploadFile], str]:

    upload_root = os.path.join("output", "uploads", request_id)
    os.makedirs(upload_root, exist_ok=True)

    saved_files: List[SavedUploadFile] = []

    for index, file in enumerate(files):

        original_name = getattr(file, "filename", None) or f"upload_{index + 1}"
        safe_name = os.path.basename(original_name)
        destination_path = os.path.join(upload_root, safe_name)

        contents = await file.read()
        with open(destination_path, "wb") as destination:
            destination.write(contents)

        await file.close()

        saved_file = SavedUploadFile(destination_path, safe_name, getattr(file, "content_type", None))
        saved_files.append(saved_file)

        logger.info(
            "Saved uploaded file",
            extra={
                "file_name": safe_name,
                "destination": destination_path,
                "size": len(contents),
                "request_id": request_id
            }
        )

    return saved_files, upload_root

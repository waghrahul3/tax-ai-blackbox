from utils.logger import get_logger

logger = get_logger(__name__)

MAX_IMAGE_BYTES = 4_500_000  # ~4.5MB pre-encoding, stays under 5MB after base64

async def load_documents(files, storage):

    documents = []

    logger.info("Loading documents", extra={"file_count": len(files)})

    for file in files:

        doc = await storage.read_file(file)

        # Add early warning for oversized images
        if doc.is_image() and hasattr(doc, 'image_data') and len(doc.image_data) > MAX_IMAGE_BYTES:
            logger.warning(
                "Image file exceeds safe API limit and will be compressed",
                extra={"file_name": doc.filename, "size": len(doc.image_data), "limit": MAX_IMAGE_BYTES}
            )

        documents.append(doc)

        logger.debug(
            "Loaded document",
            extra=doc.get_display_info()
        )

    text_count = sum(1 for d in documents if d.is_text())
    image_count = sum(1 for d in documents if d.is_image())

    logger.info(
        "Documents loaded",
        extra={"total": len(documents), "text": text_count, "images": image_count, "file_paths": [f.file_path for f in files]}
    )

    return documents
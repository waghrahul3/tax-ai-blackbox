from utils.logger import get_logger

logger = get_logger(__name__)

async def load_documents(files, storage):

    documents = []

    logger.info("Loading documents", extra={"file_count": len(files)})

    for file in files:

        doc = await storage.read_file(file)

        documents.append(doc)

        logger.debug(
            "Loaded document",
            extra=doc.get_display_info()
        )

    text_count = sum(1 for d in documents if d.is_text())
    image_count = sum(1 for d in documents if d.is_image())

    logger.info(
        "Documents loaded",
        extra={"total": len(documents), "text": text_count, "images": image_count}
    )

    return documents
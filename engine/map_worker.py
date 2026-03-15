import asyncio
from utils.logger import get_logger
from utils.image_handler import encode_image_for_claude

logger = get_logger(__name__)


async def summarize_chunks(chunks, llm, image_docs=None):

    if image_docs is None:
        image_docs = []

    logger.info(
        "Starting content summarization",
        extra={"text_chunks": len(chunks), "images": len(image_docs)}
    )

    tasks = []

    for idx, chunk in enumerate(chunks):

        logger.debug(
            "Preparing text chunk for summarization",
            extra={"chunk_index": idx, "chunk_length": len(chunk)}
        )

        prompt = f"""
        Summarize this document chunk:

        {chunk}
        """

        tasks.append(llm.ainvoke(prompt))

    for idx, image_doc in enumerate(image_docs):

        logger.debug(
            "Preparing image for vision analysis",
            extra={"image_index": idx, "file_name": image_doc.filename}
        )

        encoded_image, media_type = encode_image_for_claude(
            image_doc.image_data,
            image_doc.filename,
            image_doc.image_media_type
        )

        vision_message = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract all text and data from this image. If it's a tax document, extract all box numbers, labels, and values exactly as shown."
                    }
                ]
            }
        ]

        tasks.append(llm.ainvoke(vision_message))

    logger.debug(
        "Invoking LLM for all content in parallel",
        extra={"task_count": len(tasks)}
    )

    responses = await asyncio.gather(*tasks)

    logger.info(
        "Content summarization completed",
        extra={
            "response_count": len(responses),
            "total_summary_length": sum(len(r.content) for r in responses)
        }
    )

    summaries = [r.content for r in responses]

    for idx, summary in enumerate(summaries):
        source_type = "text" if idx < len(chunks) else "image"
        logger.debug(
            "Summary generated",
            extra={"index": idx, "source_type": source_type, "summary_length": len(summary)}
        )

    return summaries
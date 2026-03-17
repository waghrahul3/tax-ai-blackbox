from core.config import DEFAULT_TEMPERATURE
from core.llm_factory import get_llm
from engine.chunk_engine import create_chunks
from engine.map_worker import summarize_chunks
from engine.reduce_worker import reduce_summaries
from utils.logger import get_logger


class DocumentPipeline:

    def __init__(self):

        self.logger = get_logger(__name__)

    async def run(self, documents, user_instruction="", template_name=None, template_config=None):

        temperature = DEFAULT_TEMPERATURE
        if template_config and template_config.primary_step.temperature is not None:
            temperature = template_config.primary_step.temperature
            self.logger.info(
                "Using template-defined temperature",
                extra={"temperature": temperature, "template": template_config.name}
            )
        else:
            self.logger.info(
                "Using configured default temperature",
                extra={"temperature": temperature}
            )

        llm = get_llm(temperature=temperature)

        text_docs = [d for d in documents if d.is_text()]
        image_docs = [d for d in documents if d.is_image()]

        self.logger.info(
            "Processing documents",
            extra={"text_docs": len(text_docs), "image_docs": len(image_docs)}
        )

        combined_text = "\n\n".join(d.text_content for d in text_docs if d.text_content)

        self.logger.debug("Creating chunks", extra={"text_length": len(combined_text)})

        chunks = create_chunks(combined_text) if combined_text else []

        self.logger.info(
            "Summarizing content",
            extra={"text_chunks": len(chunks), "images": len(image_docs)}
        )

        chunk_summaries = await summarize_chunks(chunks, llm, image_docs)

        self.logger.info("Reducing summaries", extra={"summary_count": len(chunk_summaries)})

        final_summary = await reduce_summaries(
            chunk_summaries,
            llm,
            user_instruction,
            template_name=template_name
        )

        self.logger.info("Reduce step completed", extra={"summary_length": len(final_summary)})

        return final_summary
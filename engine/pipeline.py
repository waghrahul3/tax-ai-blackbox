from core.config import (
    DEFAULT_TEMPERATURE,
    ENABLE_PANDAS_CLEANING,
    ENABLE_CHUNKING,
    ENABLE_BASE64_INPUT
)
from core.llm_factory import get_llm
from engine.chunk_engine import create_chunks
from engine.map_worker import summarize_chunks
from engine.reduce_worker import reduce_summaries
from utils.logger import get_logger
from utils.pandas_cleaner import normalize_tabular_text
from utils.t4_extractor import extract_structured_slip, format_structured_text


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
        file_docs = [d for d in documents if getattr(d, "source_path", None)]

        if ENABLE_PANDAS_CLEANING and text_docs:
            self._normalize_text_documents(text_docs)

        if not ENABLE_BASE64_INPUT and text_docs:
            self._augment_pdf_documents(text_docs)

        self.logger.info(
            "Processing documents",
            extra={
                "text_docs": len(text_docs),
                "image_docs": len(image_docs),
                "chunking_enabled": ENABLE_CHUNKING,
                "base64_enabled": ENABLE_BASE64_INPUT
            }
        )

        combined_text = "\n\n".join(d.text_content for d in text_docs if d.text_content)

        if ENABLE_CHUNKING:
            self.logger.debug(
                "Creating chunks",
                extra={"text_length": len(combined_text)}
            )
            chunks = create_chunks(combined_text) if combined_text else []
        else:
            chunks = [d.text_content for d in text_docs if d.text_content]
            self.logger.info(
                "Chunking disabled; feeding raw documents",
                extra={"raw_chunk_count": len(chunks)}
            )

        self.logger.info(
            "Summarizing content",
            extra={"text_chunks": len(chunks), "images": len(image_docs)}
        )

        base64_collector = [] if ENABLE_BASE64_INPUT else None

        chunk_summaries = await summarize_chunks(
            chunks,
            llm,
            image_docs,
            use_base64=ENABLE_BASE64_INPUT,
            base64_collector=base64_collector,
            file_docs=file_docs
        )

        self.logger.info("Reducing summaries", extra={"summary_count": len(chunk_summaries)})

        final_summary = await reduce_summaries(
            chunk_summaries,
            llm,
            user_instruction,
            template_name=template_name
        )

        self.logger.info("Reduce step completed", extra={"summary_length": len(final_summary)})

        return {
            "summary": final_summary,
            "base64_chunks": base64_collector if base64_collector else None
        }

    def _normalize_text_documents(self, documents):

        for doc in documents:
            if not doc.text_content:
                continue

            original_text = doc.text_content
            cleaned_text = normalize_tabular_text(original_text)

            if cleaned_text == original_text:
                self.logger.debug(
                    "Pandas cleaner skipped (no change)",
                    extra={
                        "file_name": doc.filename,
                        "input_preview": original_text[:200]
                    }
                )
                continue

            self.logger.info(
                "Pandas cleaner applied",
                extra={
                    "file_name": doc.filename,
                    "original_length": len(original_text),
                    "cleaned_length": len(cleaned_text)
                }
            )
            self.logger.debug(
                "Pandas cleaner output",
                extra={
                    "file_name": doc.filename,
                    "input_preview": original_text[:200],
                    "output_preview": cleaned_text[:200]
                }
            )

            doc.text_content = cleaned_text

    def _augment_pdf_documents(self, documents):

        for doc in documents:
            media_type = (doc.source_media_type or "").lower()
            if media_type != "application/pdf" or not doc.source_path:
                continue

            doc_type, extraction = extract_structured_slip(doc.source_path)
            if not doc_type or not extraction:
                continue

            formatted = format_structured_text(doc_type, extraction)
            enrichment = (
                f"\n\n[{doc_type} Structured Extraction]\n"
                f"{formatted}\n"
            )
            base_text = doc.text_content or ""
            doc.text_content = f"{base_text}{enrichment}" if base_text else enrichment

            self.logger.info(
                "Structured slip extractor enriched PDF document",
                extra={
                    "file_name": doc.filename,
                    "source_path": doc.source_path,
                    "enrichment_length": len(enrichment),
                    "doc_type": doc_type
                }
            )

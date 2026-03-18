import os
from urllib.parse import quote, unquote_plus

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from structlog.contextvars import bind_contextvars, unbind_contextvars
from typing import List, Optional

from engine.pipeline import DocumentPipeline
from services.document_loader import load_documents
from services.output_service import generate_output_file
from services.upload_service import generate_request_id, persist_uploads
from storage.storage_factory import get_storage
from core.prompt_templates import get_prompt_template, list_prompt_templates
from utils.logger import get_logger, build_log_extra
import re

logger = get_logger(__name__)


def _clean_unicode_box_characters(content: str) -> str:
    """
    Replace Unicode box-drawing characters with ASCII equivalents.
    This prevents special characters like ══ from appearing in prompts.
    """
    # Define mappings of Unicode box characters to ASCII equivalents
    box_char_mappings = {
        '═': '=',
        '─': '-',
        '│': '|',
        '┌': '+',
        '┐': '+', 
        '└': '+',
        '┘': '+',
        '├': '+',
        '┤': '+',
        '┬': '+',
        '┴': '+',
        '┼': '+',
        '╔': '+',
        '╗': '+',
        '╚': '+',
        '╝': '+',
        '╠': '+',
        '╣': '+',
        '╦': '+',
        '╩': '+',
        '╬': '+',
        '║': '|',
        '╞': '+',
        '╡': '+',
        '╤': '+',
        '╥': '+',
        '╙': '+',
        '╘': '+',
        '╒': '+',
        '╓': '+',
        '╫': '+',
        '╪': '+',
        '┝': '+',
        '┠': '+',
        '┣': '+',
        '┥': '+',
        '┨': '+',
        '┫': '+',
        '┭': '+',
        '┮': '+',
        '┯': '+',
        '┰': '+',
        '┱': '+',
        '┲': '+',
        '┳': '+',
        '┵': '+',
        '┶': '+',
        '┷': '+',
        '┸': '+',
        '┹': '+',
        '┺': '+',
        '┻': '+',
        '┽': '+',
        '┾': '+',
        '┿': '+',
        '╀': '+',
        '╁': '+',
        '╂': '+',
        '╃': '+',
        '╄': '+',
        '╅': '+',
        '╆': '+',
        '╇': '+',
        '╈': '+',
        '╉': '+',
        '╊': '+',
    }
    
    # Create regex pattern for all box characters
    box_pattern = re.compile(f"[{''.join(box_char_mappings.keys())}]")
    
    # Replace each box character with its ASCII equivalent
    cleaned_content = box_pattern.sub(lambda match: box_char_mappings[match.group()], content)
    
    logger.debug(
        "Cleaned Unicode box characters from prompt",
        extra={
            "original_length": len(content),
            "cleaned_length": len(cleaned_content)
        }
    )
    
    return cleaned_content


def _clean_markdown_formatting(content: str) -> str:
    """
    Clean problematic Unicode characters that appear during internet transfer
    while preserving markdown structure for LLM comprehension.
    """
    import re
    
    # Replace problematic Unicode characters with ASCII equivalents
    # but preserve markdown structure
    
    # Replace Unicode box drawing characters with ASCII equivalents
    unicode_to_ascii = {
        '═': '=',
        '─': '-',
        '│': '|',
        '┌': '+',
        '┐': '+', 
        '└': '+',
        '┘': '+',
        '├': '+',
        '┤': '+',
        '┬': '+',
        '┴': '+',
        '┼': '+',
        '╔': '+',
        '╗': '+',
        '╚': '+',
        '╝': '+',
        '╠': '+',
        '╣': '+',
        '╦': '+',
        '╩': '+',
        '╬': '+',
        '║': '|',
        '•': '-',     # bullet points
        '→': '->',    # arrows
        '—': '--',    # em dash
        '–': '-',     # en dash
        '\u201c': '"',  # left double quotation mark (U+201C)
        '\u201d': '"',  # right double quotation mark (U+201D)
        '\u2018': "'",  # left single quotation mark (U+2018)
        '\u2019': "'",  # right single quotation mark (U+2019)
    }
    
    # Create regex pattern for all Unicode characters
    unicode_pattern = re.compile(f"[{''.join(unicode_to_ascii.keys())}]")
    
    # Replace each Unicode character with its ASCII equivalent
    cleaned_content = unicode_pattern.sub(lambda match: unicode_to_ascii[match.group()], content)
    
    # Clean up excessive whitespace but preserve structure
    cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content)
    cleaned_content = cleaned_content.strip()
    
    logger.debug(
        "Cleaned Unicode characters while preserving markdown",
        extra={
            "original_length": len(content),
            "cleaned_length": len(cleaned_content)
        }
    )
    
    return cleaned_content


class ProcessResponse(BaseModel):

    status: str = Field(description="Processing status message")
    format: str = Field(description="Detected output format e.g. markdown, csv")
    file: str = Field(description="Path to the primary generated file")
    folder: str = Field(description="Run folder path containing all artifacts")
    download_url: str = Field(description="Relative URL to download the main output")
    ctid: Optional[str] = Field(default=None, description="Correlation tracking ID echoed back to caller")
    markdown_file: Optional[str] = Field(default=None, description="Markdown file path when available")
    markdown_download_url: Optional[str] = Field(default=None, description="Download URL for markdown output")
    csv_file: Optional[str] = Field(default=None, description="CSV file path when available")
    csv_download_url: Optional[str] = Field(default=None, description="Download URL for CSV output")
    zip_file: Optional[str] = Field(default=None, description="ZIP archive path containing the run outputs")
    zip_download_url: Optional[str] = Field(default=None, description="Download URL for the ZIP archive")
    base64_file: Optional[str] = Field(default=None, description="JSON file capturing base64-encoded chunks when enabled")
    base64_download_url: Optional[str] = Field(default=None, description="Download URL for the base64 JSON artifact")


router = APIRouter()

pipeline = DocumentPipeline()
storage = get_storage()
logger = get_logger(__name__)


@router.post(
    "/ai/process",
    summary="Process documents with AI",
    description=(
        "Upload one or more supported files (PDF, JPG, JPEG, PNG, CSV) and process them with a required prompt. "
        "The 'prompt' parameter is treated as user instruction, while 'system_prompt' defines the AI's behavior. "
        "Optionally select a prompt template for opinionated workflows and pass an optional CTID for log correlation. "
        "The response includes download URLs for the primary output plus any markdown, CSV, or ZIP bundles that were generated, "
        "and echoes the CTID when provided."
    ),
    response_description="JSON payload describing the aggregate output and download links",
    response_model=ProcessResponse
)
async def process_documents(
    request: Request,
    files: List[UploadFile] = File(..., description="Upload one or more files to process"),
    template_name: Optional[str] = Form(
        None,
        description="Optional template name (e.g., 't_slip_data_extraction', 'medical_tax_credit')"
    ),
    prompt: str = Form(..., min_length=1, description="Required instruction for processing"),
    system_prompt: Optional[str] = Form(
        None,
        description="Optional system prompt to override default behavior"
    ),
    ctid: Optional[str] = Form(
        None,
        description="Optional correlation tracking ID passed through to server logs"
    )
):

    unbind_fields = []
    if ctid:
        bind_contextvars(ctid=ctid)
        unbind_fields.append("ctid")

    request_id = generate_request_id()

    try:
        template_config = None
        if template_name:
            try:
                template_config = get_prompt_template(template_name)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        logger.info(
            "Processing request",
            extra=build_log_extra(
                request,
                template=template_name,
                file_count=len(files),
                ctid=ctid,
                request_id=request_id
            )
        )

        saved_files, upload_dir = await persist_uploads(files, request_id)

        logger.info(
            "Uploads persisted",
            extra=build_log_extra(
                request,
                upload_dir=upload_dir,
                request_id=request_id,
                ctid=ctid
            )
        )

        documents = await load_documents(saved_files, storage)

        decoded_prompt = unquote_plus(prompt)
        unicode_cleaned_prompt = _clean_unicode_box_characters(decoded_prompt)
        final_prompt = _clean_markdown_formatting(unicode_cleaned_prompt)

        # Process system_prompt if provided
        final_system_prompt = None
        if system_prompt:
            decoded_system_prompt = unquote_plus(system_prompt)
            unicode_cleaned_system_prompt = _clean_unicode_box_characters(decoded_system_prompt)
            final_system_prompt = _clean_markdown_formatting(unicode_cleaned_system_prompt)

        logger.info(
            "Processed prompt",
            extra={
                "original_length": len(prompt),
                "decoded_length": len(decoded_prompt),
                "unicode_cleaned_length": len(unicode_cleaned_prompt),
                "final_length": len(final_prompt),
                "system_prompt_provided": system_prompt is not None,
                "system_prompt_length": len(final_system_prompt) if final_system_prompt else 0
            }
        )

        try:
            pipeline_result = await pipeline.run(
                documents,
                user_instruction=final_prompt,
                template_name=template_name,
                template_config=template_config,
                system_prompt=final_system_prompt
            )
        except Exception as e:
            # Handle Anthropic API errors gracefully
            error_message = str(e)
            if "529" in error_message or "overloaded_error" in error_message:
                logger.error(
                    "Anthropic API overloaded - retry later",
                    extra={"error": error_message, "request_id": request_id}
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "AI service temporarily unavailable",
                        "message": "The AI service is currently overloaded. Please try again in a few moments.",
                        "request_id": request_id,
                        "retry_after": 30
                    }
                )
            elif "429" in error_message or "rate_limit" in error_message:
                logger.error(
                    "Anthropic API rate limit exceeded",
                    extra={"error": error_message, "request_id": request_id}
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please wait before trying again.",
                        "request_id": request_id,
                        "retry_after": 60
                    }
                )
            else:
                logger.error(
                    "Pipeline execution failed",
                    extra={"error": error_message, "request_id": request_id}
                )
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Processing failed",
                        "message": "An error occurred during document processing.",
                        "request_id": request_id
                    }
                )

        base64_chunks = pipeline_result.get("base64_chunks") if isinstance(pipeline_result, dict) else None
        summary_text = pipeline_result.get("summary") if isinstance(pipeline_result, dict) else pipeline_result

        output = generate_output_file(
            summary_text,
            template_config=template_config,
            base64_chunks=base64_chunks
        )
    finally:
        if unbind_fields:
            unbind_contextvars(*unbind_fields)

    logger.info(
        "Output generated",
        extra=build_log_extra(
            request,
            format=output["format"],
            path=output["file_path"],
            folder=output["folder_path"],
            ctid=ctid
        )
    )

    download_path = request.url_for("download_file").path
    download_url = f"{download_path}?file_path={quote(output['file_path'])}"
    csv_file_path = output.get("csv_file_path")
    csv_download_url = None
    zip_file_path = output.get("zip_file_path")
    zip_download_url = None
    base64_file_path = output.get("base64_file_path")
    base64_download_url = None
    if csv_file_path:
        csv_download_url = f"{download_path}?file_path={quote(csv_file_path)}"
    if zip_file_path:
        zip_download_url = f"{download_path}?file_path={quote(zip_file_path)}"
    if base64_file_path:
        base64_download_url = f"{download_path}?file_path={quote(base64_file_path)}"

    return {
        "status": "success",
        "format": output["format"],
        "file": output["file_path"],
        "folder": output["folder_path"],
        "download_url": download_url,
        "markdown_file": output["file_path"] if output["format"] == "markdown" else None,
        "markdown_download_url": download_url if output["format"] == "markdown" else None,
        "csv_file": csv_file_path if csv_file_path else (output["file_path"] if output["format"] == "csv" else None),
        "csv_download_url": csv_download_url if csv_download_url else (download_url if output["format"] == "csv" else None),
        "zip_file": zip_file_path,
        "zip_download_url": zip_download_url,
        "base64_file": base64_file_path,
        "base64_download_url": base64_download_url,
        "ctid": ctid,
        "request_id": request_id
    }


@router.get("/ai/templates")
async def list_templates():

    templates = list_prompt_templates()

    logger.debug("Listing templates", extra={"count": len(templates)})

    return {
        "status": "success",
        "templates": templates
    }


@router.get("/ai/download", name="download_file")
async def download_file(
    request: Request,
    file_path: str = Query(..., description="File path returned from /ai/process response"),
    ctid: Optional[str] = Query(None, description="Optional correlation tracking ID passed through to server logs")
):

    unbind_fields = []
    if ctid:
        bind_contextvars(ctid=ctid)
        unbind_fields.append("ctid")

    try:
        requested_path = os.path.normpath(file_path)
        absolute_path = os.path.abspath(requested_path)
        output_root = os.path.abspath("output")

        if not absolute_path.startswith(f"{output_root}{os.sep}"):
            raise HTTPException(status_code=400, detail="Invalid file path. Only output files can be downloaded.")

        if not os.path.isfile(absolute_path):
            raise HTTPException(status_code=404, detail="Requested file not found.")

        logger.info(
            "Downloading output file",
            extra=build_log_extra(request, path=absolute_path, ctid=ctid)
        )

        return FileResponse(
            path=absolute_path,
            filename=os.path.basename(absolute_path),
            media_type="application/octet-stream"
        )
    finally:
        if unbind_fields:
            unbind_contextvars(*unbind_fields)
import os
from urllib.parse import quote, unquote_plus

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from structlog.contextvars import bind_contextvars, unbind_contextvars
from typing import List, Optional

from engine.pipeline import DocumentPipeline
from services.upload_service import generate_request_id, persist_uploads
from services.service_container import get_service, configure_services
from utils.logger import get_logger, build_log_extra
from exceptions.document_exceptions import PasswordProtectedPDFException

# Configure services on import
configure_services()

logger = get_logger(__name__)


class ProcessResponse(BaseModel):
    """Response model for document processing."""

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

# Initialize services
document_processing_service = get_service("document_processing")
content_cleaning_service = get_service("content_cleaning")
llm_service = get_service("llm")
output_generation_service = get_service("output_generation")
file_validation_service = get_service("file_validation")
template_service = get_service("template")

# Keep pipeline for now (will be refactored later)
pipeline = DocumentPipeline()
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
    """Process uploaded documents with AI using refactored services."""
    
    unbind_fields = []
    if ctid:
        bind_contextvars(ctid=ctid)
        unbind_fields.append("ctid")

    request_id = generate_request_id()

    try:
        # Validate files first
        file_validation_service.validate_files(files)

        # Get template configuration if specified
        template_config = None
        if template_name:
            template_config = template_service.get_template(template_name)

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

        # Persist uploads
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

        # Load documents using new service
        try:
            documents = await document_processing_service.load_documents(saved_files)
        except PasswordProtectedPDFException as e:
            # Handle password-protected PDF errors with specific HTTP responses
            filename = getattr(e, 'filename', 'unknown')
            
            if e.error_code == "password_required":
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "password_required",
                        "filename": filename
                    }
                )
            elif e.error_code == "wrong_password":
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "wrong_password",
                        "filename": filename
                    }
                )
            elif e.error_code == "invalid_pdf":
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "invalid_pdf",
                        "filename": filename
                    }
                )
            else:
                # Generic password-protected PDF error
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "pdf_processing_error",
                        "filename": filename,
                        "message": str(e)
                    }
                )

        # Clean prompts using new service
        decoded_prompt = unquote_plus(prompt)
        final_prompt = content_cleaning_service.clean_prompt_content(decoded_prompt)

        final_system_prompt = None
        if system_prompt:
            decoded_system_prompt = unquote_plus(system_prompt)
            final_system_prompt = content_cleaning_service.clean_prompt_content(decoded_system_prompt)

        logger.info(
            "Processed prompt",
            extra={
                "original_length": len(prompt),
                "decoded_length": len(decoded_prompt),
                "final_length": len(final_prompt),
                "system_prompt_provided": system_prompt is not None,
                "system_prompt_length": len(final_system_prompt) if final_system_prompt else 0
            }
        )

        # Log detailed input data for debugging
        logger.info(
            "Request input data details",
            extra={
                "request_id": request_id,
                "ctid": ctid,
                "template_name": template_name,
                "file_count": len(files),
                "upload_dir": upload_dir,
                "prompt_raw": prompt,
                "prompt_decoded": decoded_prompt,
                "prompt_final": final_prompt,
                "system_prompt_raw": system_prompt,
                "system_prompt_decoded": decoded_system_prompt if system_prompt else None,
                "system_prompt_final": final_system_prompt,
                "encoding_info": {
                    "prompt_encoded_chars": sum(1 for c in prompt if ord(c) > 127),
                    "system_prompt_encoded_chars": sum(1 for c in system_prompt if ord(c) > 127) if system_prompt else 0,
                    "prompt_has_unicode_quotes": '"' in prompt or "'" in prompt,
                    "prompt_has_html_entities": '&' in prompt,
                    "prompt_has_escaped_newlines": '\\r' in prompt or '\\n' in prompt,
                    "prompt_has_percent_encoding": '%' in prompt
                },
                "file_details": [
                    {
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size": file.size if hasattr(file, 'size') else "unknown"
                    }
                    for file in files
                ]
            }
        )

        # Process documents through pipeline (keep existing for now)
        try:
            pipeline_result = await pipeline.run(
                documents,
                user_instruction=final_prompt,
                template_name=template_name,
                template_config=template_config,
                system_prompt=final_system_prompt
            )
        except Exception as e:
            # Handle errors with new exception types
            error_message = str(e)
            if "529" in error_message or "overloaded_error" in error_message:
                from exceptions.llm_exceptions import LLMAPIOverloadException
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
                from exceptions.llm_exceptions import LLMRateLimitException
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
                from exceptions.document_exceptions import DocumentProcessingException
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

        # Generate output using new service
        output = output_generation_service.generate_output_file(
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

    # Generate download URLs
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
    """List available prompt templates using new service."""
    
    templates_result = template_service.list_templates()
    
    logger.debug("Listing templates", extra={"count": templates_result["template_count"]})

    return templates_result


@router.get("/ai/download", name="download_file")
async def download_file(
    request: Request,
    file_path: str = Query(..., description="File path returned from /ai/process response"),
    ctid: Optional[str] = Query(None, description="Optional correlation tracking ID passed through to server logs")
):
    """Download output file with security validation."""
    
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

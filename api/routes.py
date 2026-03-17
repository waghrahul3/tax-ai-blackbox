import os
from urllib.parse import quote

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from structlog.contextvars import bind_contextvars, unbind_contextvars
from typing import List, Optional

from engine.pipeline import DocumentPipeline
from services.document_loader import load_documents
from services.output_service import generate_output_file
from storage.storage_factory import get_storage
from core.prompt_templates import get_prompt_template, list_prompt_templates
from utils.logger import get_logger, build_log_extra

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


router = APIRouter()

pipeline = DocumentPipeline()
storage = get_storage()
logger = get_logger(__name__)


@router.post(
    "/ai/process",
    summary="Process documents with AI",
    description=(
        "Upload one or more supported files (PDF, JPG, JPEG, PNG, CSV) and process them with a required prompt. "
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
    ctid: Optional[str] = Form(
        None,
        description="Optional correlation tracking ID passed through to server logs"
    )
):

    unbind_fields = []
    if ctid:
        bind_contextvars(ctid=ctid)
        unbind_fields.append("ctid")

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
                ctid=ctid
            )
        )

        documents = await load_documents(files, storage)

        summary = await pipeline.run(
            documents,
            user_instruction=prompt,
            template_name=template_name,
            template_config=template_config
        )

        output = generate_output_file(summary, template_config=template_config)
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
    if csv_file_path:
        csv_download_url = f"{download_path}?file_path={quote(csv_file_path)}"
    if zip_file_path:
        zip_download_url = f"{download_path}?file_path={quote(zip_file_path)}"

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
        "ctid": ctid
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
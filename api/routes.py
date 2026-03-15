import os
from urllib.parse import quote

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Query
from fastapi.responses import FileResponse
from typing import List

from engine.pipeline import DocumentPipeline
from services.document_loader import load_documents
from services.output_service import generate_output_file
from storage.storage_factory import get_storage
from core.prompt_templates import get_prompt_template, list_prompt_templates
from utils.logger import get_logger

router = APIRouter()

pipeline = DocumentPipeline()
storage = get_storage()
logger = get_logger(__name__)


@router.post(
    "/ai/process",
    summary="Process documents with AI",
    description="Upload multiple files (PDF, JPG, JPEG, PNG, CSV) and process them using a selected template"
)
async def process_documents(
    request: Request,
    files: List[UploadFile] = File(..., description="Upload one or more files to process"),
    template_name: str = Form(..., description="Template name (e.g., 't_slip_data_extraction', 'medical_tax_credit')"),
    prompt: str = Form("", description="Optional custom instructions for processing")
):

    try:
        template_config = get_prompt_template(template_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("Processing request", extra={"template": template_name, "file_count": len(files)})

    documents = await load_documents(files, storage)

    summary = await pipeline.run(
        documents,
        user_instruction=prompt,
        template_name=template_name,
        template_config=template_config
    )

    output = generate_output_file(summary, template_config=template_config)

    logger.info(
        "Output generated",
        extra={"format": output["format"], "path": output["file_path"]}
    )

    download_url = f"{request.url_for('download_file')}?file_path={quote(output['file_path'])}"
    csv_file_path = output.get("csv_file_path")
    csv_download_url = None
    if csv_file_path:
        csv_download_url = f"{request.url_for('download_file')}?file_path={quote(csv_file_path)}"

    return {
        "status": "success",
        "format": output["format"],
        "file": output["file_path"],
        "folder": output["folder_path"],
        "download_url": download_url,
        "markdown_file": output["file_path"] if output["format"] == "markdown" else None,
        "markdown_download_url": download_url if output["format"] == "markdown" else None,
        "csv_file": csv_file_path if csv_file_path else (output["file_path"] if output["format"] == "csv" else None),
        "csv_download_url": csv_download_url if csv_download_url else (download_url if output["format"] == "csv" else None)
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
async def download_file(file_path: str = Query(..., description="File path returned from /ai/process response")):

    requested_path = os.path.normpath(file_path)
    absolute_path = os.path.abspath(requested_path)
    output_root = os.path.abspath("output")

    if not absolute_path.startswith(f"{output_root}{os.sep}"):
        raise HTTPException(status_code=400, detail="Invalid file path. Only output files can be downloaded.")

    if not os.path.isfile(absolute_path):
        raise HTTPException(status_code=404, detail="Requested file not found.")

    logger.info("Downloading output file", extra={"path": absolute_path})

    return FileResponse(
        path=absolute_path,
        filename=os.path.basename(absolute_path),
        media_type="application/octet-stream"
    )
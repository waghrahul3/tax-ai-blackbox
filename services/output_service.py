import os
import re
import zipfile
from datetime import datetime
from uuid import uuid4

from utils.output_detector import OutputDetector
from utils.file_mapper import get_extension
from utils.logger import get_logger

logger = get_logger(__name__)

OUTPUT_ROOT = "output"

os.makedirs(OUTPUT_ROOT, exist_ok=True)


def _create_run_folder():

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    folder_name = f"run_{timestamp}_{uuid4().hex[:6]}"
    folder_path = os.path.join(OUTPUT_ROOT, folder_name)

    logger.debug("Creating run folder", extra={"folder_name": folder_name, "path": folder_path})

    os.makedirs(folder_path, exist_ok=True)

    logger.info("Run folder created", extra={"path": folder_path})

    return folder_path


def _sanitize_csv_content(content: str) -> str:

    text = content.strip()

    fenced_csv = re.search(r"```csv\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if fenced_csv:
        text = fenced_csv.group(1).strip()
    else:
        generic_fence = re.search(r"```\s*\n(.*?)\n```", text, re.DOTALL)
        if generic_fence:
            text = generic_fence.group(1).strip()

    return text


def _extract_csv_block(content: str) -> str:

    match = re.search(r"```csv\s*\n(.*?)\n```", content, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""

    return match.group(1).strip()


def _remove_csv_block(content: str) -> str:

    cleaned = re.sub(r"```csv\s*\n.*?\n```", "", content, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def _create_output_zip(output_folder: str) -> str:

    folder_name = os.path.basename(output_folder)
    zip_path = os.path.join(OUTPUT_ROOT, f"{folder_name}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_folder):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                arcname = os.path.relpath(file_path, output_folder)
                zipf.write(file_path, arcname=arcname)

    logger.info("Generated zip archive for output folder", extra={"zip_path": zip_path, "folder": output_folder})
    return zip_path


def generate_output_file(content, template_config=None):

    logger.debug(
        "Starting output file generation",
        extra={
            "content_length": len(content),
            "has_template_config": template_config is not None
        }
    )

    if template_config and template_config.primary_step.output_format:
        format_type = template_config.primary_step.output_format
        logger.info(
            "Using template-defined output format",
            extra={"format": format_type, "template": template_config.name}
        )
    else:
        format_type = OutputDetector.detect_format(content)
        logger.info(
            "Auto-detected output format",
            extra={"format": format_type}
        )

    extension = get_extension(format_type)
    logger.debug("File extension determined", extra={"extension": extension})

    if template_config and template_config.primary_step.output_filename_template:
        filename_template = template_config.primary_step.output_filename_template
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = filename_template.replace("{date}", timestamp)
        logger.info(
            "Using template-defined filename",
            extra={"template_pattern": filename_template, "file_name": filename}
        )
    else:
        filename = f"summary_report{extension}"
        logger.info("Using default filename", extra={"file_name": filename})

    output_folder = _create_run_folder()

    path = os.path.join(output_folder, filename)

    logger.debug("Writing output file", extra={"path": path, "size": len(content)})

    content_to_write = content
    csv_file_path = None
    if format_type == "csv":
        content_to_write = _sanitize_csv_content(content)
        logger.debug(
            "Sanitized CSV content",
            extra={
                "original_size": len(content),
                "sanitized_size": len(content_to_write)
            }
        )
    elif format_type == "markdown":
        csv_block = _extract_csv_block(content)
        if csv_block:
            content_to_write = _remove_csv_block(content)

            base_name, _ = os.path.splitext(filename)
            csv_filename = f"{base_name}.csv"
            csv_file_path = os.path.join(output_folder, csv_filename)

            with open(csv_file_path, "w", encoding="utf-8") as csv_file:
                csv_file.write(_sanitize_csv_content(csv_block))

            logger.info(
                "Generated separated CSV output",
                extra={"csv_path": csv_file_path}
            )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content_to_write)

    logger.info(
        "Output file generated successfully",
        extra={
            "path": path,
            "format": format_type,
            "folder": output_folder,
            "file_name": filename
        }
    )

    zip_file_path = _create_output_zip(output_folder)

    return {
        "format": format_type,
        "file_path": path,
        "folder_path": output_folder,
        "csv_file_path": csv_file_path,
        "zip_file_path": zip_file_path
    }
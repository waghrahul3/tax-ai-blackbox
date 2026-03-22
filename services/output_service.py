import json
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


def _convert_markdown_to_csv(markdown_content: str) -> str:
    """
    Convert markdown content to CSV format
    """
    # Remove markdown code blocks
    lines = []
    for line in markdown_content.split('\n'):
        if line.strip().startswith('```'):
            continue
        # Escape commas and quotes for CSV
        clean_line = line.replace('"', '""').replace(',', '","')
        lines.append(clean_line)
    
    return '\n'.join(lines)

def _convert_csv_to_markdown(csv_content: str) -> str:
    """
    Convert CSV content to markdown format
    """
    lines = csv_content.split('\n')
    markdown_lines = []
    
    for line in lines:
        if line.strip():
            # Escape pipe characters and format as markdown table row
            clean_line = line.replace('"', '""').replace(',', '\\,')
            markdown_lines.append(f"| {clean_line} |")
    
    if markdown_lines:
        markdown_lines.insert(0, "| Field 1 | Field 2 | Field 3 |")
        markdown_lines.append("|---|---|---|")
    
    return '\n'.join(markdown_lines)

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


def _extract_csv_blocks(content: str) -> list:
    """Extract multiple CSV blocks with their section names."""
    csv_blocks = []
    
    # Pattern to match CSV blocks with CSV Output X: filename.csv format
    section_pattern = r"##\s*CSV\s+Output\s+\d+:\s*([^\n\.]+\.csv).*?```csv\s*\n(.*?)\n```"
    matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        filename = match.group(1).strip()
        csv_content = match.group(2).strip()
        
        # Clean filename for use in output filename
        clean_name = filename.replace('.csv', '')
        clean_name = re.sub(r"[^\w\s-]", "", clean_name)
        clean_name = re.sub(r"\s+", "_", clean_name)
        
        csv_blocks.append({
            "name": clean_name,
            "content": csv_content,
            "original_section": filename
        })
    
    # If no CSV Output pattern found, try pattern where filename is in code block
    if not csv_blocks:
        # Pattern: ## CSV Output 1 followed by ```filename.csv``` then actual CSV content
        section_pattern = r"##\s*CSV\s+Output\s+\d+:\s*([^\n]*)\n```\s*([^\n\.]+\.csv)\s*```\s*```csv\s*\n(.*?)\n```"
        matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            filename = match.group(2).strip()
            csv_content = match.group(3).strip()
            
            # Clean filename for use in output filename
            clean_name = filename.replace('.csv', '')
            clean_name = re.sub(r"[^\w\s-]", "", clean_name)
            clean_name = re.sub(r"\s+", "_", clean_name)
            
            csv_blocks.append({
                "name": clean_name,
                "content": csv_content,
                "original_section": filename
            })
    
    # If no CSV Output pattern found, try simple filename block followed by CSV content
    if not csv_blocks:
        # Pattern: ```filename.csv``` followed by ```csv content```
        section_pattern = r"```\s*([^\n\.]+\.csv)\s*```\s*```csv\s*\n(.*?)\n```"
        matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            filename = match.group(1).strip()
            csv_content = match.group(2).strip()
            
            # Clean filename for use in output filename
            clean_name = filename.replace('.csv', '')
            clean_name = re.sub(r"[^\w\s-]", "", clean_name)
            clean_name = re.sub(r"\s+", "_", clean_name)
            
            csv_blocks.append({
                "name": clean_name,
                "content": csv_content,
                "original_section": filename
            })
    
    # If no patterns found, try simple ## filename.csv format (new LLM format)
    if not csv_blocks:
        # Pattern: ## filename.csv followed by CSV content somewhere later
        section_pattern = r"##\s*([^\n\.]+\.csv)\s*\n.*?```csv\s*\n(.*?)\n```"
        matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            filename = match.group(1).strip()
            csv_content = match.group(2).strip()
            
            # Clean filename for use in output filename
            clean_name = filename.replace('.csv', '')
            clean_name = re.sub(r"[^\w\s-]", "", clean_name)
            clean_name = re.sub(r"\s+", "_", clean_name)
            
            csv_blocks.append({
                "name": clean_name,
                "content": csv_content,
                "original_section": filename
            })
    
    # If no CSV Output pattern found, try FILE X pattern
    if not csv_blocks:
        section_pattern = r"##\s*FILE\s+\d+:\s*([^\n\.]+\.csv).*?```csv\s*\n(.*?)\n```"
        matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            filename = match.group(1).strip()
            csv_content = match.group(2).strip()
            
            # Clean filename for use in output filename
            clean_name = filename.replace('.csv', '')
            clean_name = re.sub(r"[^\w\s-]", "", clean_name)
            clean_name = re.sub(r"\s+", "_", clean_name)
            
            csv_blocks.append({
                "name": clean_name,
                "content": csv_content,
                "original_section": filename
            })
    
    # If no FILE X pattern found, try SECTION X pattern
    if not csv_blocks:
        section_pattern = r"SECTION\s+\d+\s*[—-]\s*([^\n]+).*?```csv\s*\n(.*?)\n```"
        matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            section_name = match.group(1).strip()
            csv_content = match.group(2).strip()
            
            # Clean section name for filename
            clean_name = re.sub(r"[^\w\s-]", "", section_name)
            clean_name = re.sub(r"\s+", "_", clean_name)
            
            csv_blocks.append({
                "name": clean_name,
                "content": csv_content,
                "original_section": section_name
            })
    
    # If no named sections found, fall back to simple CSV blocks
    if not csv_blocks:
        simple_pattern = r"```csv\s*\n(.*?)\n```"
        matches = re.finditer(simple_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for i, match in enumerate(matches):
            csv_blocks.append({
                "name": f"csv_output_{i+1}",
                "content": match.group(1).strip(),
                "original_section": f"CSV Output {i+1}"
            })
    
    return csv_blocks


def _extract_csv_block(content: str) -> str:

    match = re.search(r"```csv\s*\n(.*?)\n```", content, re.DOTALL | re.IGNORECASE)
    if not match:
        return ""

    return match.group(1).strip()


def _remove_all_csv_blocks(content: str) -> str:
    """Remove all CSV blocks from content."""
    # Remove CSV Output X patterns with CSV blocks
    cleaned = re.sub(r"##\s*CSV\s+Output\s+\d+:\s*[^\n\.]+\.csv.*?```csv\s*\n.*?\n```", "", content, flags=re.DOTALL | re.IGNORECASE)
    # Remove CSV Output X patterns with filename in code block
    cleaned = re.sub(r"##\s*CSV\s+Output\s+\d+:[^\n]*\n```\s*[^\n\.]+\.csv\s*```\s*```csv\s*\n.*?\n```", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove simple filename block patterns
    cleaned = re.sub(r"```\s*[^\n\.]+\.csv\s*```\s*```csv\s*\n.*?\n```", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove simple ## filename.csv patterns (new LLM format)
    cleaned = re.sub(r"##\s*[^\n\.]+\.csv\s*\n.*?```csv\s*\n.*?\n```", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove FILE X patterns with CSV blocks
    cleaned = re.sub(r"##\s*FILE\s+\d+:\s*[^\n\.]+\.csv.*?```csv\s*\n.*?\n```", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove SECTION X patterns with CSV blocks
    cleaned = re.sub(r"SECTION\s+\d+\s*[—-][^\n]*.*?```csv\s*\n.*?\n```", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove simple CSV blocks
    cleaned = re.sub(r"```csv\s*\n.*?\n```", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


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


def generate_output_file(content: str, template_config=None, base64_chunks=None):

    logger.debug(
        "Starting output file generation",
        extra={
            "content_length": len(content),
            "has_template_config": template_config is not None
        }
    )

    # Extract status information if present
    from utils.output_detector import _extract_status_info
    cleaned_content, status_info = _extract_status_info(content)
    
    if status_info:
        logger.info(
            "Status information extracted",
            extra={"status": status_info, "original_length": len(content), "cleaned_length": len(cleaned_content)}
        )
    
    # Use cleaned content for format detection and processing
    content_to_process = cleaned_content

    if template_config and template_config.primary_step.output_format:
        format_type = template_config.primary_step.output_format
        logger.info(
            "Using template-defined output format",
            extra={"format": format_type, "template": template_config.name}
        )
    else:
        format_type = OutputDetector.detect_format(content_to_process)
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

    # Generate primary output file
    path = os.path.join(output_folder, filename)
    logger.debug("Writing output file", extra={"path": path, "size": len(content_to_process)})

    content_to_write = content_to_process
    csv_file_path = None
    base64_file_path = None
    if format_type == "csv":
        content_to_write = _sanitize_csv_content(content_to_process)
        logger.debug(
            "Sanitized CSV content",
            extra={
                "original_size": len(content_to_process),
                "sanitized_size": len(content_to_write)
            }
        )
    elif format_type == "markdown":
        content_to_write = content_to_process  # Initialize with cleaned content
        csv_blocks = _extract_csv_blocks(content_to_process)
        if csv_blocks:
            # Remove all CSV blocks from main content
            content_to_write = _remove_all_csv_blocks(content_to_process)
            base_name, _ = os.path.splitext(filename)
            generated_csv_files = []
            
            for i, csv_block in enumerate(csv_blocks):
                csv_filename = f"{base_name}_{csv_block['name']}.csv"
                csv_file_path = os.path.join(output_folder, csv_filename)
                
                with open(csv_file_path, "w", encoding="utf-8") as csv_file:
                    csv_file.write(_sanitize_csv_content(csv_block['content']))
                
                generated_csv_files.append(csv_file_path)
                
                logger.info(
                    "Generated named CSV output",
                    extra={
                        "csv_path": csv_file_path,
                        "section_name": csv_block['original_section'],
                        "csv_name": csv_block['name']
                    }
                )
            
            # Update the main content to reference the generated CSV files
            if generated_csv_files:
                csv_references = "\n\n**Generated CSV Files:**\n"
                for i, csv_path in enumerate(generated_csv_files):
                    csv_filename = os.path.basename(csv_path)
                    csv_references += f"- {csv_blocks[i]['original_section']}: `{csv_filename}`\n"
                content_to_write += csv_references

    if base64_chunks:
        base64_filename = "base64_chunks.json"
        base64_file_path = os.path.join(output_folder, base64_filename)
        with open(base64_file_path, "w", encoding="utf-8") as base64_file:
            payload = {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "chunk_count": len(base64_chunks),
                "chunks": base64_chunks
            }
            json.dump(payload, base64_file, indent=2)

        logger.info(
            "Captured base64 chunk payload",
            extra={"base64_path": base64_file_path, "chunk_count": len(base64_chunks)}
        )

        base64_zip_path = os.path.join(output_folder, "base64_chunks.zip")
        with zipfile.ZipFile(base64_zip_path, "w", zipfile.ZIP_DEFLATED) as base64_zip:
            base64_zip.write(base64_file_path, arcname=base64_filename)

        logger.info(
            "Created base64 zip artifact",
            extra={"base64_zip_path": base64_zip_path}
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content_to_write)

    # Save status information if present
    status_file_path = None
    if status_info:
        status_file_path = os.path.join(output_folder, "status.txt")
        with open(status_file_path, "w", encoding="utf-8") as f:
            f.write(f"Status: {status_info}\n")
            f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
        logger.info(
            "Status file created",
            extra={"status_file_path": status_file_path, "status": status_info}
        )

    logger.info(
        "Output file generated successfully",
        extra={
            "path": path,
            "format": format_type,
            "folder": output_folder,
            "file_name": filename,
            "status_saved": status_info is not None
        }
    )

    zip_file_path = _create_output_zip(output_folder)

    return {
        "format": format_type,
        "file_path": path,
        "folder_path": output_folder,
        "csv_file_path": csv_file_path,
        "zip_file_path": zip_file_path,
        "base64_file_path": base64_file_path,
        "status_file_path": status_file_path,
        "status_info": status_info
    }
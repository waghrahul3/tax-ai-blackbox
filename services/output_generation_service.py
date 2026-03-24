"""Service for generating output files and formatting results."""

import json
import os
import zipfile
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Optional

from utils.output_detector import OutputDetector
from utils.file_mapper import get_extension
from utils.logger import get_logger
from core.prompt_templates.base import PromptTemplateConfig
from exceptions.output_exceptions import (
    OutputGenerationException,
    OutputFormatException,
    FileCreationException
)
from config.config_manager import get_config_manager
from strategies.output_format_strategies import OutputFormatStrategyFactory


class OutputGenerationService:
    """Service for handling output file generation and formatting."""
    
    def __init__(self, output_root: str = "output"):
        self.logger = get_logger(__name__)
        self.output_root = output_root
        self.config_manager = get_config_manager()
        self.output_strategy_factory = OutputFormatStrategyFactory()
        self._ensure_output_directory()
    
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        try:
            os.makedirs(self.output_root, exist_ok=True)
        except OSError as e:
            raise OutputGenerationException(
                f"Failed to create output directory: {str(e)}",
                output_path=self.output_root
            ) from e
    
    def generate_output_file(
        self,
        content: str,
        template_config: Optional[PromptTemplateConfig] = None,
        base64_chunks: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """
        Generate output file from processed content.
        
        Args:
            content: Processed content to output
            template_config: Optional template configuration
            base64_chunks: Optional base64 chunk data
            
        Returns:
            Dictionary with file paths and metadata
            
        Raises:
            OutputGenerationException: If output generation fails
            OutputFormatException: If format is invalid
            FileCreationException: If file creation fails
        """
        try:
            self.logger.debug(
                "Starting output file generation",
                extra={
                    "content_length": len(content),
                    "has_template_config": template_config is not None
                }
            )
            
            # Extract status information if present
            cleaned_content, status_info = self._extract_status_info(content)
            
            if status_info:
                self.logger.info(
                    "Status information extracted",
                    extra={
                        "status": status_info,
                        "original_length": len(content),
                        "cleaned_length": len(cleaned_content)
                    }
                )
            
            # Use cleaned content for format detection and processing
            content_to_process = cleaned_content
            
            # Determine output format
            format_type = self._determine_output_format(content_to_process, template_config)
            
            # Generate filename
            filename = self._generate_filename(format_type, template_config)
            
            # Create output folder
            output_folder = self._create_run_folder()
            
            # Generate primary output file
            file_path = self._write_primary_output(
                output_folder, filename, content_to_process, format_type
            )
            
            # Generate additional files (CSV, base64, etc.)
            additional_files = self._generate_additional_files(
                output_folder, filename, content_to_process, format_type, base64_chunks
            )
            
            # Create zip archive
            zip_file_path = self._create_output_zip(output_folder)
            
            # Save status information if present
            status_file_path = self._save_status_file(output_folder, status_info)
            
            result = {
                "format": format_type,
                "file_path": file_path,
                "folder_path": output_folder,
                "zip_file_path": zip_file_path,
                "status_file_path": status_file_path,
                "status_info": status_info,
                **additional_files
            }
            
            self.logger.info(
                "Output file generated successfully",
                extra={
                    "path": file_path,
                    "format": format_type,
                    "folder": output_folder,
                    "file_name": filename,
                    "status_saved": status_info is not None
                }
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, (OutputGenerationException, OutputFormatException, FileCreationException)):
                raise
            raise OutputGenerationException(
                f"Unexpected error during output generation: {str(e)}"
            ) from e
    
    def _extract_status_info(self, content: str) -> tuple[str, Optional[str]]:
        """Extract status information from content."""
        from utils.output_detector import _extract_status_info
        return _extract_status_info(content)
    
    def _determine_output_format(
        self, 
        content: str, 
        template_config: Optional[PromptTemplateConfig]
    ) -> str:
        """Determine the output format for the content."""
        if template_config and template_config.primary_step.output_format:
            format_type = template_config.primary_step.output_format
            self.logger.info(
                "Using template-defined output format",
                extra={"format": format_type, "template": template_config.name}
            )
        else:
            format_type = OutputDetector.detect_format(content)
            self.logger.info(
                "Auto-detected output format",
                extra={"format": format_type}
            )
        
        # Validate format and map unsupported formats to supported ones
        format_mapping = {
            "table": "markdown",  # Map table format to markdown
            "code": "text"       # Map code format to text
        }
        
        # Apply mapping if needed
        original_format = format_type
        format_type = format_mapping.get(format_type, format_type)
        
        if format_type != original_format:
            self.logger.info(
                "Mapped output format",
                extra={"original": original_format, "mapped": format_type}
            )
        
        supported_formats = ["markdown", "csv", "json", "txt", "text"]
        if format_type not in supported_formats:
            raise OutputFormatException(
                f"Unsupported output format: {original_format}",
                output_format=original_format,
                supported_formats=supported_formats
            )
        
        return format_type
    
    def _generate_filename(
        self, 
        format_type: str, 
        template_config: Optional[PromptTemplateConfig]
    ) -> str:
        """Generate filename for output file."""
        if template_config and template_config.primary_step.output_filename_template:
            filename_template = template_config.primary_step.output_filename_template
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = filename_template.replace("{date}", timestamp)
            self.logger.info(
                "Using template-defined filename",
                extra={"template_pattern": filename_template, "file_name": filename}
            )
        else:
            extension = get_extension(format_type)
            filename = f"summary_report{extension}"
            self.logger.info("Using default filename", extra={"file_name": filename})
        
        return filename
    
    def _create_run_folder(self) -> str:
        """Create a unique output folder for this run."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        folder_name = f"run_{timestamp}_{uuid4().hex[:6]}"
        folder_path = os.path.join(self.output_root, folder_name)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            self.logger.info("Run folder created", extra={"path": folder_path})
            return folder_path
        except OSError as e:
            raise FileCreationException(
                f"Failed to create run folder: {str(e)}",
                file_path=folder_path,
                file_operation="create_directory"
            ) from e
    
    def _write_primary_output(
        self, 
        output_folder: str, 
        filename: str, 
        content: str, 
        format_type: str
    ) -> str:
        """Write the primary output file."""
        file_path = os.path.join(output_folder, filename)
        
        try:
            # Prepare content based on format
            content_to_write = self._prepare_content_for_format(content, format_type)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_to_write)
            
            self.logger.debug(
                "Primary output file written",
                extra={"path": file_path, "size": len(content_to_write)}
            )
            
            return file_path
            
        except OSError as e:
            raise FileCreationException(
                f"Failed to write output file: {str(e)}",
                file_path=file_path,
                file_operation="write_file"
            ) from e
    
    def _prepare_content_for_format(self, content: str, format_type: str) -> str:
        """Prepare content based on output format using strategy pattern."""
        # Handle empty content gracefully
        if not content.strip():
            self.logger.warning(
                "Empty content received, providing default message",
                extra={"format_type": format_type}
            )
            content = "No content generated. The LLM processed the input but returned an empty response."
        
        try:
            strategy = self.output_strategy_factory.get_strategy(format_type)
            prepared_content = strategy.prepare_content(content)
            
            self.logger.debug(
                "Content prepared with strategy",
                extra={
                    "strategy": strategy.__class__.__name__,
                    "format_type": format_type,
                    "original_length": len(content),
                    "prepared_length": len(prepared_content)
                }
            )
            
            return prepared_content
            
        except Exception as e:
            self.logger.warning(
                "Strategy-based content preparation failed, using fallback",
                extra={
                    "format_type": format_type,
                    "error": str(e)
                }
            )
            # Fallback to original method
            return self._fallback_content_preparation(content, format_type)
    
    def _sanitize_csv_content(self, content: str) -> str:
        """Sanitize content for CSV output."""
        # Remove markdown code blocks
        text = content.strip()
        
        fenced_csv = None
        import re
        fenced_csv = re.search(r"```csv\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
        if fenced_csv:
            text = fenced_csv.group(1).strip()
        else:
            generic_fence = re.search(r"```\s*\n(.*?)\n```", text, re.DOTALL)
            if generic_fence:
                text = generic_fence.group(1).strip()
        
        return text
    
    def _prepare_markdown_content(self, content: str) -> str:
        """Prepare content for markdown output."""
        # Extract CSV blocks and remove them from main content
        from services.output_service import _extract_csv_blocks, _remove_all_csv_blocks
        
        csv_blocks = _extract_csv_blocks(content)
        if csv_blocks:
            # Remove all CSV blocks from main content
            return _remove_all_csv_blocks(content)
        
        return content
    
    def _generate_additional_files(
        self,
        output_folder: str,
        filename: str,
        content: str,
        format_type: str,
        base64_chunks: Optional[List[Dict]]
    ) -> Dict[str, Optional[str]]:
        """Generate additional output files (CSV, base64, text, markdown, etc.)."""
        additional_files = {}
        base_name, _ = os.path.splitext(filename)
        
        # Always generate raw text output with original content
        text_file_path = self._generate_text_file(output_folder, base_name, content)
        additional_files["text_file_path"] = text_file_path
        
        # Always generate markdown output for formatted content
        markdown_file_path = self._generate_markdown_file(output_folder, base_name, content)
        additional_files["markdown_file_path"] = markdown_file_path
        
        # Generate CSV files if CSV blocks are present (regardless of format type)
        csv_file_path = self._generate_csv_files(output_folder, filename, content)
        if csv_file_path:
            additional_files["csv_file_path"] = csv_file_path
        
        # Generate base64 chunk file
        if base64_chunks:
            base64_file_path = self._generate_base64_file(output_folder, base64_chunks)
            additional_files["base64_file_path"] = base64_file_path
        
        return additional_files
    
    def _generate_csv_files(self, output_folder: str, filename: str, content: str) -> Optional[str]:
        """Generate CSV files from content (works for any format type)."""
        from services.output_service import _extract_csv_blocks
        
        csv_blocks = _extract_csv_blocks(content)
        if not csv_blocks:
            self.logger.debug("No CSV blocks found in content")
            return None
        
        base_name, _ = os.path.splitext(filename)
        generated_csv_files = []
        
        for csv_block in csv_blocks:
            csv_filename = f"{base_name}_{csv_block['name']}.csv"
            csv_file_path = os.path.join(output_folder, csv_filename)
            
            try:
                with open(csv_file_path, "w", encoding="utf-8") as csv_file:
                    csv_file.write(self._sanitize_csv_content(csv_block['content']))
                
                generated_csv_files.append(csv_file_path)
                
                self.logger.info(
                    "Generated named CSV output",
                    extra={
                        "csv_path": csv_file_path,
                        "section_name": csv_block['original_section'],
                        "csv_name": csv_block['name']
                    }
                )
                
            except OSError as e:
                self.logger.error(
                    "Failed to generate CSV file",
                    extra={
                        "csv_path": csv_file_path,
                        "error": str(e)
                    }
                )
        
        return generated_csv_files[0] if generated_csv_files else None
    
    def _generate_text_file(self, output_folder: str, base_name: str, content: str) -> str:
        """Generate raw text file with original content."""
        text_filename = f"{base_name}_raw.txt"
        text_file_path = os.path.join(output_folder, text_filename)
        
        try:
            with open(text_file_path, "w", encoding="utf-8") as text_file:
                text_file.write(content)
            
            self.logger.info(
                "Generated raw text output",
                extra={
                    "text_path": text_file_path,
                    "content_length": len(content)
                }
            )
            
            return text_file_path
            
        except OSError as e:
            raise FileCreationException(
                f"Failed to create text file: {str(e)}",
                file_path=text_file_path,
                file_operation="create_text_file"
            ) from e
    
    def _generate_markdown_file(self, output_folder: str, base_name: str, content: str) -> str:
        """Generate markdown file with formatted content."""
        markdown_filename = f"{base_name}_content.md"
        markdown_file_path = os.path.join(output_folder, markdown_filename)
        
        try:
            # Prepare content for markdown format
            markdown_content = self._prepare_markdown_content(content)
            
            # Extract CSV blocks to add references
            from services.output_service import _extract_csv_blocks
            csv_blocks = _extract_csv_blocks(content)
            
            # Add references to generated CSV files
            if csv_blocks:
                csv_references = "\n\n**Generated CSV Files:**\n"
                for csv_block in csv_blocks:
                    csv_filename = f"{base_name}_{csv_block['name']}.csv"
                    csv_references += f"- {csv_block['original_section']}: `{csv_filename}`\n"
                markdown_content += csv_references
            
            with open(markdown_file_path, "w", encoding="utf-8") as markdown_file:
                markdown_file.write(markdown_content)
            
            self.logger.info(
                "Generated markdown output",
                extra={
                    "markdown_path": markdown_file_path,
                    "original_length": len(content),
                    "markdown_length": len(markdown_content),
                    "csv_references_added": len(csv_blocks) > 0
                }
            )
            
            return markdown_file_path
            
        except OSError as e:
            raise FileCreationException(
                f"Failed to create markdown file: {str(e)}",
                file_path=markdown_file_path,
                file_operation="create_markdown_file"
            ) from e
    
    def _generate_base64_file(self, output_folder: str, base64_chunks: List[Dict]) -> str:
        """Generate base64 chunk JSON file."""
        base64_filename = "base64_chunks.json"
        base64_file_path = os.path.join(output_folder, base64_filename)
        
        try:
            payload = {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "chunk_count": len(base64_chunks),
                "chunks": base64_chunks
            }
            
            with open(base64_file_path, "w", encoding="utf-8") as base64_file:
                json.dump(payload, base64_file, indent=2)
            
            self.logger.info(
                "Captured base64 chunk payload",
                extra={"base64_path": base64_file_path, "chunk_count": len(base64_chunks)}
            )
            
            return base64_file_path
            
        except (OSError, json.JSONEncodeError) as e:
            raise FileCreationException(
                f"Failed to create base64 file: {str(e)}",
                file_path=base64_file_path,
                file_operation="create_base64_file"
            ) from e
    
    def _create_output_zip(self, output_folder: str) -> str:
        """Create zip archive of output folder."""
        folder_name = os.path.basename(output_folder)
        zip_path = os.path.join(self.output_root, f"{folder_name}.zip")
        
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(output_folder):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        arcname = os.path.relpath(file_path, output_folder)
                        zipf.write(file_path, arcname=arcname)
            
            self.logger.info("Generated zip archive", extra={"zip_path": zip_path})
            return zip_path
            
        except (OSError, zipfile.BadZipFile) as e:
            raise FileCreationException(
                f"Failed to create zip archive: {str(e)}",
                file_path=zip_path,
                file_operation="create_zip"
            ) from e
    
    def _save_status_file(self, output_folder: str, status_info: Optional[str]) -> Optional[str]:
        """Save status information to file."""
        if not status_info:
            return None
        
        status_file_path = os.path.join(output_folder, "status.txt")
        
        try:
            with open(status_file_path, "w", encoding="utf-8") as f:
                f.write(f"Status: {status_info}\n")
                f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
            
            self.logger.info(
                "Status file created",
                extra={"status_file_path": status_file_path, "status": status_info}
            )
            
            return status_file_path
            
        except OSError as e:
            self.logger.error(
                "Failed to create status file",
                extra={"status_file_path": status_file_path, "error": str(e)}
            )
            return None
    
    def _fallback_content_preparation(self, content: str, format_type: str) -> str:
        """Fallback method for content preparation."""
        if format_type == "csv":
            return self._sanitize_csv_content(content)
        elif format_type == "markdown":
            return self._prepare_markdown_content(content)
        else:
            return content
    
    def get_output_strategy_info(self) -> dict:
        """Get information about available output strategies."""
        return self.output_strategy_factory.get_strategy_info()

"""
file_manifest.py — Builds a human + LLM readable file manifest
for any collection of uploaded files.
"""

from utils.file_registry import detect_file_info, FileRole, FileInfo
from utils.logger import get_logger

logger = get_logger(__name__)


def build_file_manifest(base64_collector: list[dict]) -> str:
    """
    Build a structured manifest of all attached files.
    Works for any file type — tax docs, invoices, bank statements, etc.
    Returns a plain text block to prepend to the LLM user message.
    """
    if not base64_collector:
        return ""

    file_infos = _classify_files(base64_collector)

    if not file_infos:
        return ""

    lines = [
        "ATTACHED FILES MANIFEST",
        "=" * 50,
        f"Total files: {len(file_infos)}",
        "",
    ]

    # Group by role for clarity
    references = [f for f in file_infos if f.role == FileRole.REFERENCE]
    sources = [f for f in file_infos if f.role == FileRole.SOURCE]
    supporting = [f for f in file_infos if f.role == FileRole.SUPPORTING]
    unknowns = [f for f in file_infos if f.role == FileRole.UNKNOWN]

    if references:
        lines.append("REFERENCE DOCUMENTS (compare against these):")
        for fi in references:
            lines.extend(_format_file_entry(fi))

    if sources:
        lines.append("SOURCE DOCUMENTS (verify these):")
        for fi in sources:
            lines.extend(_format_file_entry(fi))

    if supporting:
        lines.append("SUPPORTING DOCUMENTS:")
        for fi in supporting:
            lines.extend(_format_file_entry(fi))

    if unknowns:
        lines.append("UNCLASSIFIED DOCUMENTS (role unclear — use context):")
        for fi in unknowns:
            lines.extend(_format_file_entry(fi))

    lines.extend(
        [
            "=" * 50,
            _build_processing_instruction(references, sources, unknowns),
        ]
    )

    manifest = "\n".join(lines)

    logger.debug(
        "File manifest built",
        extra={
            "total_files": len(file_infos),
            "references": len(references),
            "sources": len(sources),
            "supporting": len(supporting),
            "unknowns": len(unknowns),
        },
    )

    return manifest


def _classify_files(base64_collector: list[dict]) -> list[FileInfo]:
    """Classify all files in the collector."""
    file_infos = []
    for idx, file_data in enumerate(base64_collector, start=1):
        filename = file_data.get("filename") or file_data.get(
            "file_name", f"file_{idx}"
        )
        media_type = file_data.get("media_type", "application/octet-stream")
        info = detect_file_info(filename, media_type, idx)
        file_infos.append(info)
        logger.debug(
            "File classified",
            extra={
                "filename": filename,
                "media_type": media_type,
                "role": info.role.value,
                "category": info.category,
            },
        )
    return file_infos


def _format_file_entry(fi: FileInfo) -> list[str]:
    """Format a single file entry for the manifest."""
    type_label = _media_type_label(fi.media_type)
    return [
        f"  [{fi.index}] {fi.filename}",
        f"       Role : {fi.role_label}",
        f"       Type : {type_label}",
        "",
    ]


def _media_type_label(media_type: str) -> str:
    labels = {
        "application/pdf": "PDF",
        "image/jpeg": "JPEG Image",
        "image/png": "PNG Image",
        "image/tiff": "TIFF Image",
        "image/webp": "WebP Image",
    }
    return labels.get(media_type, media_type)


def _build_processing_instruction(
    references: list[FileInfo],
    sources: list[FileInfo],
    unknowns: list[FileInfo],
) -> str:
    """Build a tailored instruction based on what files are present."""

    parts = []

    if references and sources:
        ref_names = ", ".join(f.filename for f in references)
        parts.append(f"Compare all SOURCE documents against: {ref_names}.")

    if unknowns:
        parts.append(
            "Some files could not be classified automatically. "
            "Use document content and context to determine their role."
        )

    if not references and sources:
        parts.append(
            "No reference document was detected. "
            "Process source documents independently and flag any anomalies."
        )

    if not parts:
        parts.append("Process all attached documents as instructed.")

    return " ".join(parts)

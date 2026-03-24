"""
file_registry.py — Generic file role detection for any document type.
Add new patterns here without touching pipeline code.
"""

from dataclasses import dataclass
from enum import Enum


class FileRole(Enum):
    REFERENCE = "REFERENCE"  # source of truth to compare against
    SOURCE = "SOURCE"  # original document to verify
    SUPPORTING = "SUPPORTING"  # supplementary context
    UNKNOWN = "UNKNOWN"  # could not determine


@dataclass
class FileInfo:
    filename: str
    media_type: str
    role: FileRole
    role_label: str
    category: str  # e.g. "Tax Summary", "T-slip", "Invoice", "Bank Statement"
    index: int  # position in attachment list (1-based)


# ── Role detection rules ─────────────────────────────────────────────────────
# Each rule: (keywords_in_filename, role, category_label)
# Rules are evaluated top-to-bottom; first match wins.

_ROLE_RULES: list[tuple[list[str], FileRole, str]] = [
    # T-slips (source documents) - moved before federal slip summary for priority
    (["t4a"], FileRole.SOURCE, "T4A Slip"),
    (["t4e"], FileRole.SOURCE, "T4E Slip"),
    (["t4"], FileRole.SOURCE, "T4 Slip"),
    (["t5008"], FileRole.SOURCE, "T5008 Slip"),
    (["t5"], FileRole.SOURCE, "T5 Slip"),
    (["t3"], FileRole.SOURCE, "T3 Slip"),
    (["rl1"], FileRole.SOURCE, "RL-1 Slip"),
    (["rl3"], FileRole.SOURCE, "RL-3 Slip"),
    # Tax summary / reference documents
    (
        ["federal_slip", "federal slips", "slip_summary", "slips_summary"],
        FileRole.REFERENCE,
        "Federal Slip Summary",
    ),
    (
        ["taxprep", "ifirm", "tax_summary", "tax summary"],
        FileRole.REFERENCE,
        "Tax Software Summary",
    ),
    (["notice_of_assessment", "noa"], FileRole.REFERENCE, "Notice of Assessment"),
    # Financial documents
    (["bank_statement", "bank statement"], FileRole.SOURCE, "Bank Statement"),
    (["invoice", "receipt"], FileRole.SOURCE, "Invoice / Receipt"),
    (["payslip", "pay_slip", "paystub"], FileRole.SOURCE, "Pay Stub"),
    (["contract", "agreement"], FileRole.SUPPORTING, "Contract"),
    (["letter", "correspondence"], FileRole.SUPPORTING, "Correspondence"),
]


def detect_file_info(filename: str, media_type: str, index: int) -> FileInfo:
    """
    Detect role and category for any uploaded file based on filename patterns.
    Falls back to UNKNOWN if no rule matches.
    """
    name_lower = filename.lower().replace(" ", "_").replace("-", "_")

    for keywords, role, category in _ROLE_RULES:
        if any(kw.replace(" ", "_") in name_lower for kw in keywords):
            role_label = _role_label(role, category)
            return FileInfo(
                filename=filename,
                media_type=media_type,
                role=role,
                role_label=role_label,
                category=category,
                index=index,
            )

    # No rule matched
    category = _infer_category_from_media_type(media_type)
    role_label = _role_label(FileRole.UNKNOWN, category)
    return FileInfo(
        filename=filename,
        media_type=media_type,
        role=FileRole.UNKNOWN,
        role_label=role_label,
        category=category,
        index=index,
    )


def _role_label(role: FileRole, category: str) -> str:
    labels = {
        FileRole.REFERENCE: f"{category} (REFERENCE — compare against this)",
        FileRole.SOURCE: f"{category} (SOURCE — verify this document)",
        FileRole.SUPPORTING: f"{category} (SUPPORTING — supplementary context)",
        FileRole.UNKNOWN: f"{category} (UNKNOWN — role unclear)",
    }
    return labels[role]


def _infer_category_from_media_type(media_type: str) -> str:
    if media_type == "application/pdf":
        return "PDF Document"
    if media_type.startswith("image/"):
        return "Scanned Image"
    if media_type in (
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ):
        return "Spreadsheet"
    if media_type in (
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        return "Word Document"
    return "Document"

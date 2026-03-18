import re
from typing import Any, Dict, Optional, Tuple

import fitz  # PyMuPDF

from utils.logger import get_logger

logger = get_logger(__name__)

T4_MARKERS = [
    r"T4\s*\(\d{2}\)",
    r"Statement of Remuneration Paid",
    r"Canada Revenue Agency",
    r"Revenus d'emploi",
]
T4_STANDARD_BOXES = {
    "10": "Canada Pension Plan contributions",
    "12": "EI premiums",
    "14": "Employment Income",
    "16": "Employee CPP",
    "18": "Employee EI",
    "20": "RPP Contributions",
    "22": "Income Tax Deducted",
    "24": "EI Insurable Earnings",
    "26": "CPP Pensionable Earnings",
    "28": "Exempt (CPP/QPP, EI, PPIP)",
    "32": "Pensionable earnings for QPP",
    "44": "Union dues",
    "46": "RPP contributions",
    "50": "PPIP premiums",
    "52": "Pension Adjustment",
    "56": "PPIP insurable earnings",
}
T4_OTHER_INFO_PATTERN = r"\b(3[0-9]|4[0-5]|5[0-9]|6[0-9]|7[0-9]|8[0-9]|9[0-5])\s+([\d,]+(?:\.\d{2})?)"
T4_SIMPLE_AMOUNT_PATTERN = r"\b{box}\s+([\d,]+(?:\.\d{{2}})?)"

T4A_MARKERS = [
    r"T4A\s*\(",
    r"Statement of Pension, Retirement, Annuity",
    r"Annuity",
    r"Pension or Superannuation",
]
T4A_MAIN_BOXES = {
    "016": "Pension or Superannuation",
    "018": "Lump-sum payments",
    "020": "Self-employed commissions",
    "022": "Income tax deducted",
    "024": "Annuities",
    "048": "Fees for services",
    "105": "Scholarships, bursaries",
    "107": "Research grants",
    "109": "Other income",
    "117": "Loan forgiveness",
    "119": "Premiums for group term life",
    "135": "Foreign workdays",
    "136": "Foreign workdays (social security)",
    "154": "Registered pension income",
    "197": "COVID-19 relief (CERB/CESB)",
    "200": "Pension adjustment",
    "205": "RCAs",
    "210": "Other taxable income",
    "211": "Employee benefits",
}
T4A_OTHER_INFO_PATTERN = r"\b(1\d{2}|2[0-1]\d)\s+([\d,]+(?:\.\d{2})?)"


def _normalize_amount(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", "", value)


def _resolve_label(code: str, label_map: Dict[str, str], default_prefix: str) -> str:
    normalized = code.lstrip("0") or code
    return label_map.get(code) or label_map.get(normalized) or f"{default_prefix} {code}"


def _extract_all_boxes(full_text: str, code_ranges, label_map, default_prefix) -> list[Dict[str, str]]:
    patterns = [
        re.compile(r"(?:Box\s+)?(\d{2,3}[A-Z]?)\s+([\d,]+(?:\.\d{2})?)", re.IGNORECASE),
        re.compile(r"(?:Box\s+)?(\d{2,3}[A-Z]?)\s*(?:\n|\r\n)+\s*([\d,]+(?:\.\d{2})?)", re.IGNORECASE)
    ]

    boxes = []
    seen = set()

    for pattern in patterns:
        for code, amount in pattern.findall(full_text):
            numeric_match = re.match(r"\d+", code)
            if not numeric_match:
                continue
            numeric_value = int(numeric_match.group())
            if not any(low <= numeric_value <= high for (low, high) in code_ranges):
                continue

            normalized = _normalize_amount(amount)
            dedupe_key = (code, normalized)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            boxes.append({
                "Code": code,
                "Amount": normalized,
                "Label": _resolve_label(code, label_map, default_prefix)
            })

    return boxes


def _looks_like_t4(text: str) -> bool:
    matches = [1 for marker in T4_MARKERS if re.search(marker, text, re.IGNORECASE)]
    return len(matches) >= 2


def _looks_like_t4a(text: str) -> bool:
    matches = [1 for marker in T4A_MARKERS if re.search(marker, text, re.IGNORECASE)]
    return len(matches) >= 1


def _read_pdf_text(pdf_path: str) -> Optional[str]:
    try:
        with fitz.open(pdf_path) as doc:
            page_text = [page.get_text("text") or "" for page in doc]
    except FileNotFoundError:
        logger.error("Structured slip extractor missing file", extra={"path": pdf_path})
        return None
    except Exception:
        logger.exception("Failed to open PDF for structured slip extraction", extra={"path": pdf_path})
        return None

    full_text = "\n".join(page_text)
    if not full_text.strip():
        logger.debug("Structured slip extractor found empty text", extra={"path": pdf_path})
        return None
    return full_text


def extract_structured_slip(pdf_path: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    full_text = _read_pdf_text(pdf_path)
    if not full_text:
        return None, None

    if _looks_like_t4(full_text):
        data = _extract_t4_data(full_text)
        if data:
            return "T4", data

    if _looks_like_t4a(full_text):
        data = _extract_t4a_data(full_text)
        if data:
            return "T4A", data

    return None, None


def _extract_t4_data(full_text: str) -> Optional[Dict[str, Any]]:
    extraction: Dict[str, Any] = {"Box_Values": {}, "Other_Information": [], "Metadata": {}}

    for box, label in T4_STANDARD_BOXES.items():
        pattern = T4_SIMPLE_AMOUNT_PATTERN.format(box=box)
        match = re.search(pattern, full_text)
        if match:
            extraction["Box_Values"][f"Box {box} ({label})"] = _normalize_amount(match.group(1))

    seen_codes = set()
    for code, amount in re.findall(T4_OTHER_INFO_PATTERN, full_text):
        if code in T4_STANDARD_BOXES:
            continue
        key = (code, amount)
        if key in seen_codes:
            continue
        seen_codes.add(key)
        extraction["Other_Information"].append({"Code": code, "Amount": _normalize_amount(amount)})

    year_match = re.search(r"Year\s*\n?\s*(\d{4})", full_text)
    sin_match = re.search(r"(\d{3}\s\d{3}\s\d{3})", full_text)
    extraction["Metadata"] = {
        "Tax_Year": year_match.group(1) if year_match else "Not Found",
        "SIN": sin_match.group(1) if sin_match else "Not Found",
    }

    extraction["All_Boxes"] = _extract_all_boxes(full_text, [(10, 99)], T4_STANDARD_BOXES, "Box")

    if not extraction["Box_Values"] and not extraction["Other_Information"] and not extraction["All_Boxes"]:
        logger.debug("T4 markers found but no data extracted")
        return None

    return extraction


def _extract_t4a_data(full_text: str) -> Optional[Dict[str, Any]]:
    extraction: Dict[str, Any] = {"Standard_Boxes": {}, "Other_Information": [], "Metadata": {}}

    for code, label in T4A_MAIN_BOXES.items():
        pattern = rf"\b{code}\s+([\d,]+(?:\.\d{{2}})?)"
        match = re.search(pattern, full_text)
        if match:
            extraction["Standard_Boxes"][f"Box {code} ({label})"] = _normalize_amount(match.group(1))

    seen_codes = set()
    for code, amount in re.findall(T4A_OTHER_INFO_PATTERN, full_text):
        key = (code, amount)
        if key in seen_codes:
            continue
        seen_codes.add(key)
        extraction["Other_Information"].append({"Code": code, "Amount": _normalize_amount(amount)})

    year_match = re.search(r"Year\s*\n?\s*(\d{4})", full_text)
    extraction["Metadata"] = {
        "Tax_Year": year_match.group(1) if year_match else "Not Found",
    }

    extraction["All_Boxes"] = _extract_all_boxes(full_text, [(10, 299)], T4A_MAIN_BOXES, "Box")

    if not extraction["Standard_Boxes"] and not extraction["Other_Information"] and not extraction["All_Boxes"]:
        logger.debug("T4A markers found but no data extracted")
        return None

    return extraction


def format_structured_text(doc_type: str, extracted: Dict[str, Any]) -> str:

    lines: list[str] = []

    lines.append(f"Document Type: {doc_type}")

    def _append_dict(title: str, data: Dict[str, Any]):
        if not data:
            return
        lines.append(f"{title}:")
        for key, value in data.items():
            lines.append(f"  - {key}: {value}")

    def _append_list(title: str, rows, label_key="Label"):
        if not rows:
            return
        lines.append(f"{title}:")
        for row in rows:
            code = row.get("Code", "")
            amount = row.get("Amount", "")
            label = row.get(label_key) or (f"Box {code}" if code else "Box")
            code_note = f" ({code})" if code else ""
            lines.append(f"  - {label}{code_note}: {amount}")

    _append_dict("Box Values", extracted.get("Box_Values", {}))
    _append_dict("Standard Boxes", extracted.get("Standard_Boxes", {}))
    _append_list("Other Information", extracted.get("Other_Information", []), label_key=None)
    _append_dict("Metadata", extracted.get("Metadata", {}))
    _append_list("All Boxes", extracted.get("All_Boxes", []))

    return "\n".join(lines) + "\n"

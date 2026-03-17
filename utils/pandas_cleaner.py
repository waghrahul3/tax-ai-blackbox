from __future__ import annotations

import re
from io import StringIO
from typing import List

from utils.logger import get_logger

try:
    import pandas as pd
except ImportError:
    pd = None


logger = get_logger(__name__)

TABLE_PATTERN = re.compile(r"(?:^\|.*\|\s*$\n?){3,}", re.MULTILINE)
CSV_PATTERN = re.compile(r"```csv\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def _pandas_available() -> bool:
    if pd is None:
        logger.warning("ENABLE_PANDAS_CLEANING is true but pandas is not installed")
        return False
    return True


def _strip_cell(value):
    return value.strip() if isinstance(value, str) else value


def _clean_dataframe(df):
    cleaned = df.applymap(_strip_cell)
    cleaned = cleaned.dropna(how="all")
    cleaned = cleaned.fillna("")
    cleaned = cleaned.drop_duplicates()
    return cleaned


def _stringify(value) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return ("{:.4f}".format(value)).rstrip("0").rstrip(".")
    return str(value)


def clean_csv_text(csv_text: str) -> str:
    if not csv_text.strip():
        return csv_text
    if not _pandas_available():
        return csv_text
    try:
        df = pd.read_csv(StringIO(csv_text))
    except Exception:
        logger.exception("Failed to parse CSV content for cleaning")
        return csv_text

    df = _clean_dataframe(df)

    try:
        return df.to_csv(index=False)
    except Exception:
        logger.exception("Failed to serialize cleaned CSV content")
        return csv_text


def _split_markdown_row(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells: List[str]) -> bool:
    if not cells:
        return False
    for cell in cells:
        stripped = cell.replace(":", "").replace("-", "").strip()
        if stripped:
            return False
    return True


def _format_markdown_table(columns: List[str], rows: List[List[str]]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_stringify(value) for value in row) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def _clean_markdown_table(table_text: str) -> str:
    if not _pandas_available():
        return table_text

    lines = [line.strip() for line in table_text.strip().splitlines() if line.strip()]
    if len(lines) < 3:
        return table_text

    header_cells = _split_markdown_row(lines[0])
    data_lines = lines[1:]

    if data_lines and _is_separator_row(_split_markdown_row(data_lines[0])):
        data_lines = data_lines[1:]

    if not data_lines:
        return table_text

    rows = []
    for line in data_lines:
        row = _split_markdown_row(line)
        if not row:
            continue
        if len(row) < len(header_cells):
            row += [""] * (len(header_cells) - len(row))
        elif len(row) > len(header_cells):
            row = row[: len(header_cells)]
        rows.append(row)

    if not rows:
        return table_text

    try:
        df = pd.DataFrame(rows, columns=header_cells)
    except Exception:
        logger.exception("Failed to build DataFrame from markdown table")
        return table_text

    df = _clean_dataframe(df)
    cleaned_rows = [list(row) for row in df.to_numpy().tolist()]
    return _format_markdown_table(list(df.columns), cleaned_rows)


def clean_markdown_tables(markdown_text: str) -> str:
    if not markdown_text.strip():
        return markdown_text
    if not _pandas_available():
        return markdown_text

    def _replacement(match: re.Match) -> str:
        original = match.group(0)
        cleaned = _clean_markdown_table(original)
        if cleaned != original:
            logger.debug("Markdown table cleaned via pandas")
        return cleaned

    return TABLE_PATTERN.sub(_replacement, markdown_text)


def _replace_csv_blocks(text: str) -> str:
    if not text.strip():
        return text

    def _replacement(match: re.Match) -> str:
        body = match.group(1)
        cleaned = clean_csv_text(body)
        if cleaned != body:
            logger.debug("CSV fenced block cleaned via pandas")
        return f"```csv\n{cleaned}\n```"

    return CSV_PATTERN.sub(_replacement, text)


def normalize_tabular_text(text: str) -> str:
    if not text.strip():
        return text
    if not _pandas_available():
        return text

    cleaned = clean_markdown_tables(text)
    cleaned = _replace_csv_blocks(cleaned)
    return cleaned

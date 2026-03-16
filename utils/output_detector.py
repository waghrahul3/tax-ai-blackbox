import json
import re


def _is_json(text):

    try:
        json.loads(text)
        return True
    except Exception:
        return False


def _is_pure_csv(text):

    stripped = text.strip()

    # Try to unwrap fenced CSV blocks. If the entire text isn't just a block, it's not pure CSV.
    fenced_match = re.fullmatch(r"```(?:csv)?\s*\n?(.*?)\n?```", stripped, re.DOTALL)

    if fenced_match:
        stripped = fenced_match.group(1).strip()
    elif "```" in stripped:
        return False

    lines = [line for line in stripped.splitlines() if line.strip()]

    if len(lines) < 2:
        return False

    column_count = None

    for line in lines:

        if "," not in line:
            return False

        cells = [cell.strip() for cell in line.split(",")]

        if column_count is None:
            column_count = len(cells)

            if column_count < 2:
                return False
        elif len(cells) != column_count:
            return False

    return True


def _contains_csv_block(text: str) -> bool:

    return bool(re.search(r"```csv\s*\n.*?\n```", text, re.DOTALL | re.IGNORECASE))


def _remove_csv_blocks(text: str) -> str:

    return re.sub(r"```csv\s*\n.*?\n```", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


class OutputDetector:

    @staticmethod
    def detect_format(content):

        text = content.strip()

        if _is_json(text):
            return "json"

        if _is_pure_csv(text):
            return "csv"

        if _contains_csv_block(text):
            remaining_text = _remove_csv_blocks(text)
            if remaining_text:
                return "markdown"
            return "csv"

        if re.search(r"^#", text, re.MULTILINE):
            return "markdown"

        if "|" in text:
            return "table"

        if "```" in text:
            return "code"

        return "text"
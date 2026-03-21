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

    # Check for and remove status lines at the end
    status_patterns = [
        r'^FILE STATUS:',
        r'^STATUS:',
        r'^STATUS\s*=',
        r'^RESULT:',
        r'^OUTCOME:'
    ]
    
    # Remove trailing status lines
    csv_lines = lines[:]
    for i in range(len(csv_lines) - 1, -1, -1):
        if any(re.match(pattern, csv_lines[i], re.IGNORECASE) for pattern in status_patterns):
            csv_lines.pop()
        else:
            break
    
    # If we removed all lines, it's not CSV
    if len(csv_lines) < 2:
        return False

    column_count = None

    for line in csv_lines:

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


def _looks_like_csv(text):
    """
    Fallback CSV detection using heuristics
    """
    lines = [line for line in text.strip().splitlines() if line.strip()]
    
    if len(lines) < 2:
        return False
    
    # Check first few lines for CSV patterns
    csv_line_count = 0
    column_count = None
    
    for line in lines[:10]:  # Check first 10 lines
        # Skip obvious non-CSV lines
        if any(pattern in line.upper() for pattern in ['FILE STATUS:', 'STATUS:', 'RESULT:']):
            continue
        
        # Count commas
        comma_count = line.count(',')
        
        # If line has commas and looks like CSV
        if comma_count >= 1:
            # Check if it's quoted CSV
            if line.startswith('"') and line.endswith('"'):
                csv_line_count += 1
            # Or has multiple comma-separated values
            elif comma_count >= 2:
                csv_line_count += 1
            
            # Track column count
            cells = line.split(',')
            if column_count is None:
                column_count = len(cells)
    
    # If majority of checked lines look like CSV
    return csv_line_count >= min(3, len(lines) // 2)


def _extract_status_info(text):
    """
    Extract status information from content
    Returns tuple: (cleaned_content, status_info)
    """
    lines = text.strip().split('\n')
    status_info = None
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            cleaned_lines.append(line)
            continue
            
        # Check for status patterns
        status_patterns = [
            r'^FILE STATUS:\s*(.+)$',
            r'^STATUS:\s*(.+)$',
            r'^STATUS\s*=\s*(.+)$',
            r'^RESULT:\s*(.+)$',
            r'^OUTCOME:\s*(.+)$'
        ]
        
        status_found = False
        for pattern in status_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                status_info = match.group(1).strip()
                status_found = True
                break
        
        if not status_found:
            cleaned_lines.append(line)
    
    # Return cleaned content and status
    cleaned_content = '\n'.join(cleaned_lines)
    return cleaned_content, status_info


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

        # Fallback: check if it looks like CSV even with status lines
        if _looks_like_csv(text):
            return "csv"

        if re.search(r"^#", text, re.MULTILINE):
            return "markdown"

        if "|" in text:
            return "table"

        if "```" in text:
            return "code"

        return "text"
# Password-Protected PDF Support

This document describes the implementation of password-protected PDF support in the Tax AI Agent.

## Overview

The system now supports password-protected PDFs by extracting passwords from filenames using configurable patterns. The implementation follows these principles:

- **Detection by attempt**: Password-protected PDFs are detected by attempting to open them, not by filename patterns
- **Configurable patterns**: Password extraction patterns are configurable via environment variables
- **Case-insensitive matching**: Pattern matching is case-insensitive by default
- **Fail loudly**: All password-related errors return specific HTTP 422 error codes
- **No password storage**: Passwords are only held in memory during request processing

## Configuration

Add these variables to your `.env` file:

```bash
# Password extraction patterns (comma-separated, case-insensitive)
PDF_PASSWORD_PATTERNS=_password_,_pwd_,_secure_

# Enable/disable password extraction from filenames
ENABLE_PASSWORD_EXTRACTION=true

# Case-sensitive pattern matching (true/false, default: false)
PDF_PATTERN_CASE_SENSITIVE=false

# Prevent password-protected PDFs from being sent to external APIs
# This avoids API errors when password-protected PDFs are sent to Anthropic
BLOCK_PASSWORD_PROTECTED_PDF_API_CALLS=true
```

### Configuration Details

- **`PDF_PASSWORD_PATTERNS`**: Comma-separated list of patterns to match in filenames
- **`ENABLE_PASSWORD_EXTRACTION`**: Turn the entire feature on/off
- **`PDF_PATTERN_CASE_SENSITIVE`**: Control case sensitivity (default: false)
- **`BLOCK_PASSWORD_PROTECTED_PDF_API_CALLS`**: Prevent API errors by blocking password-protected PDFs from external API calls

## Supported Patterns

The default patterns support these filename formats:

- `_password_` → `file_password_secret123.pdf` extracts `secret123`
- `_pwd_` → `document_pwd_abc456.pdf` extracts `abc456`
- `_secure_` → `tax_secure_myPass789.pdf` extracts `myPass789`

## Error Handling

The API returns specific HTTP 422 error codes for password-related issues:

### Password Required
```json
{
  "error": "password_required",
  "filename": "protected.pdf"
}
```
**When**: PDF is password-protected but no password found in filename

### Wrong Password
```json
{
  "error": "wrong_password",
  "filename": "file_password_wrongpass.pdf"
}
```
**When**: Password extracted from filename is incorrect

### Invalid PDF
```json
{
  "error": "invalid_pdf",
  "filename": "corrupted.pdf"
}
```
**When**: PDF is corrupted or invalid (not password-related)

## Implementation Details

### Files Modified

1. **`utils/password_extractor.py`** - New utility for extracting passwords from filenames
2. **`utils/pdf_extractor.py`** - Enhanced PDF extraction with password support
3. **`storage/local_storage.py`** - Integration point and password tracking
4. **`services/document_processing_service.py`** - Exception handling for password errors
5. **`exceptions/document_exceptions.py`** - New exception type for password errors
6. **`api/routes.py`** - HTTP error response handling
7. **`models/document.py`** - Added password_processed tracking field
8. **`engine/map_worker.py`** - Modified to send text instead of file for password-protected PDFs
9. **`.env.example`** - Configuration variables

### Key Fix: Password-Protected PDF Handling

**Problem**: Password-protected PDFs were being sent to the Anthropic API as base64-encoded files, causing errors:
```
"The PDF specified is password protected."
```

**Solution**: Modified the document processing pipeline to create decrypted copies:

1. **Extract password** from filename using configurable patterns
2. **Process PDF locally** with password to extract text
3. **Create decrypted copy** of the PDF without password protection
4. **Send decrypted copy** to LLM as base64 (preserves formatting, layout, structure)
5. **Fallback to text** if decryption fails

**Behavior Change**:
- **Normal PDFs**: Send file as document to LLM ✅
- **Password-protected PDFs**: Create decrypted copy, send decrypted file to LLM ✅
- **Failed decryption**: Send extracted text only as fallback ✅
- **Empty password-protected PDFs**: Skip entirely ✅

**Technical Implementation**:
- Added `create_decrypted_pdf_copy()` function using PyMuPDF
- Modified `LocalStorage` to create decrypted copies when passwords are used
- Updated `map_worker` to detect and send decrypted copies
- Maintains original file security (decrypted copies are temporary)

### Security Considerations

- Passwords are never stored or logged
- Only extracted during request processing
- Pattern matching is case-insensitive to improve usability
- Empty passwords are rejected for security

### Example Usage

With the file `ElizabethDelleman_T4_2025_password_del05151997.pdf`:

1. System detects it's a PDF
2. Extracts password `del05151997` from filename
3. Processes PDF locally with password
4. Creates decrypted copy without password protection
5. Sends decrypted copy to LLM as base64 (preserves full PDF structure)
6. LLM receives complete PDF with formatting, tables, and layout

### Advantages of Decrypted PDF Approach

**vs. Extracted Text Only:**
- ✅ Preserves original PDF formatting and layout
- ✅ Maintains table structures and visual elements
- ✅ Better LLM understanding of document structure
- ✅ No loss of spatial information

**vs. Encrypted PDF:**
- ✅ No API errors from password protection
- ✅ LLM can process the document fully
- ✅ Maintains security (decrypted copies are temporary)
- ✅ Fallback to text if decryption fails

## Testing

The implementation has been tested with:
- Correct password scenarios
- Wrong password scenarios  
- Missing password scenarios
- Case-insensitive pattern matching
- Multiple pattern support

All tests pass successfully.

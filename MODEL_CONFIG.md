# Model Configuration

This application supports configuring the Anthropic model through environment variables.

## Environment Variables

### MAX_TOKENS
- **Description**: Maximum number of tokens the model can generate in responses
- **Default**: `64000`
- **Current setting**: `64000` (from .env file)

### ANTHROPIC_MODEL
- **Description**: Specifies which Anthropic model to use for processing
- **Default**: `claude-3-5-sonnet-20241022`
- **Current setting**: `claude-opus-4-5-20251101` (from .env file)

### ENABLE_PDF_BETA
- **Description**: Enables PDF document support using the `anthropic-beta: pdfs-2024-09-25` header
- **Default**: `true`
- **Required for**: PDF document processing with Anthropic SDK 0.84.0+

### ANTHROPIC_BETA_HEADERS
- **Description**: Comma-separated list of Anthropic beta features to enable
- **Default**: `pdfs-2024-09-25`
- **Format**: `"pdfs-2024-09-25,prompt-caching-2024-07-31,computer-use-2024-10-22"`
- **Examples**: 
  - Single: `ANTHROPIC_BETA_HEADERS=pdfs-2024-09-25`
  - Multiple: `ANTHROPIC_BETA_HEADERS=pdfs-2024-09-25,prompt-caching-2024-07-31`

### Available Models
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet (recommended for most use cases)
- `claude-opus-4-5-20251101` - Claude Opus 4.5 (high performance)
- `claude-3-haiku-20240307` - Claude 3 Haiku (fast, lower cost)

## Configuration Methods

### 1. Environment Variable (Recommended)
```bash
export ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
export ENABLE_PDF_BETA=true
export ANTHROPIC_BETA_HEADERS=pdfs-2024-09-25
```

### 2. .env File
Add or modify the lines in your `.env` file:
```
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ENABLE_PDF_BETA=true
ANTHROPIC_BETA_HEADERS=pdfs-2024-09-25
```

### 3. Runtime
The application will automatically load the model from the environment at startup.

## Usage in Code

The model is imported from config and used consistently across all components:

```python
from core.config import ANTHROPIC_MODEL, MAX_TOKENS, ENABLE_PDF_BETA, ANTHROPIC_BETA_HEADERS

# Used in map_worker.py and reduce_worker.py
response = await llm.messages.create(
    model=ANTHROPIC_MODEL,
    max_tokens=MAX_TOKENS,
    messages=[{"role": "user", "content": content}],
    betas=ANTHROPIC_BETA_HEADERS if ENABLE_PDF_BETA and has_pdf else None
)
```

## PDF Support

### Beta Header Requirement
- **SDK Version**: Anthropic SDK 0.84.0+ requires `anthropic-beta: pdfs-2024-09-25` header for PDF processing
- **Environment Controlled**: Beta headers are configured via `ANTHROPIC_BETA_HEADERS` environment variable
- **Automatic Detection**: The application automatically detects PDF documents and adds beta headers when needed
- **Conditional Usage**: Beta headers are only added when PDF documents are present to minimize overhead
- **Multiple Features**: Supports comma-separated list for multiple beta features (PDF, prompt caching, computer use, etc.)

### PDF Processing Features
- **Native PDF Understanding**: Claude 3.5 Sonnet can directly process PDF content
- **Document Extraction**: Automatic extraction of text, tables, and structured data
- **Tax Document Support**: Optimized for tax forms and financial documents

## Notes

- The environment variable takes precedence over the default value
- All components (map_worker, reduce_worker) use the same model configuration
- Model and token limit changes require application restart to take effect
- MAX_TOKENS controls the maximum response length for all LLM calls
- PDF beta support can be disabled by setting `ENABLE_PDF_BETA=false` if needed
- Beta headers are conditionally added only when PDF documents are detected
- `ANTHROPIC_BETA_HEADERS` supports multiple beta features using comma separation
- Available beta features include: `pdfs-2024-09-25`, `prompt-caching-2024-07-31`, `computer-use-2024-10-22`, etc.

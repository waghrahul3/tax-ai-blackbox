# Model Configuration

This application supports configuring the Anthropic model through environment variables.

## Environment Variables

### ANTHROPIC_MODEL
- **Description**: Specifies which Anthropic model to use for processing
- **Default**: `claude-3-5-sonnet-20241022`
- **Current setting**: `claude-opus-4-5-20251101` (from .env file)

### Available Models
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet (recommended for most use cases)
- `claude-opus-4-5-20251101` - Claude Opus 4.5 (high performance)
- `claude-3-haiku-20240307` - Claude 3 Haiku (fast, lower cost)

## Configuration Methods

### 1. Environment Variable (Recommended)
```bash
export ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### 2. .env File
Add or modify the line in your `.env` file:
```
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### 3. Runtime
The application will automatically load the model from the environment at startup.

## Usage in Code

The model is imported from config and used consistently across all components:

```python
from core.config import ANTHROPIC_MODEL

# Used in map_worker.py and reduce_worker.py
response = await llm.messages.create(
    model=ANTHROPIC_MODEL,
    max_tokens=64000,
    messages=[{"role": "user", "content": content}]
)
```

## Notes

- The environment variable takes precedence over the default value
- All components (map_worker, reduce_worker) use the same model configuration
- Model changes require application restart to take effect

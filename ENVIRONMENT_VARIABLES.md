# Environment Variables Reference

This document describes all environment variables used by the Tax AI Agent application after the maintainability optimization.

## Quick Setup

1. Copy `.env.example` to `.env`
2. Set your `ANTHROPIC_API_KEY`
3. Adjust other variables as needed

## Environment Variables by Category

### Core Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Tax AI Agent` | Application name |
| `APP_VERSION` | `0.0.0` | Application version |
| `ENVIRONMENT` | `development` | Environment (development/staging/production) |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `DEBUG` | Logging level |

### LLM / Anthropic Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *Required* | Anthropic API key |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Default LLM model |
| `LLM_TEMPERATURE` | `0.0` | Default temperature (0.0-2.0) |
| `MAX_TOKENS` | `64000` | Maximum tokens per request |
| `ANTHROPIC_BETA_HEADERS` | `pdfs-2024-09-25` | Beta features (comma-separated) |

#### Advanced LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_PROMPT_LENGTH` | `100000` | Maximum prompt length |
| `MAX_RESPONSE_LENGTH` | `4000` | Maximum response length |
| `LLM_MAX_RETRIES` | `3` | Maximum retry attempts |
| `LLM_RETRY_DELAY` | `5` | Retry delay in seconds |
| `LLM_EXPONENTIAL_BACKOFF` | `true` | Use exponential backoff |
| `LLM_MAX_RETRY_DELAY` | `60` | Maximum retry delay |
| `LLM_REQUEST_TIMEOUT` | `300` | Request timeout (seconds) |
| `LLM_READ_TIMEOUT` | `120` | Read timeout (seconds) |
| `LLM_CONNECT_TIMEOUT` | `30` | Connect timeout (seconds) |
| `AVAILABLE_MODELS` | *auto* | Available models (comma-separated) |

### Feature Flags

#### Data Processing Features

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PANDAS_CLEANING` | `false` | Enable pandas data cleaning |
| `ENABLE_CHUNKING` | `true` | Enable text chunking |
| `ENABLE_BASE64_INPUT` | `false` | Enable base64 input processing |
| `ENABLE_LLM_SUMMARIZATION` | `true` | Enable LLM summarization |
| `ENABLE_LLM_MAP_SUMMARIZATION` | `true` | Enable map-reduce summarization |
| `ENABLE_PDF_BETA` | `true` | Enable PDF beta features |

#### System Features

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DEBUG_MODE` | `false` | Enable debug mode |
| `ENABLE_RATE_LIMITING` | `false` | Enable rate limiting |
| `ENABLE_REQUEST_LOGGING` | `true` | Enable request logging |
| `ENABLE_FILE_COMPRESSION` | `true` | Enable file compression |
| `ENABLE_TEMPLATE_CACHING` | `true` | Enable template caching |
| `ENABLE_OUTPUT_VALIDATION` | `true` | Enable output validation |
| `ENABLE_IMAGE_TEXT_EXTRACTION` | `true` | Enable OCR text extraction |
| `ENABLE_STRUCTURED_DATA_EXTRACTION` | `true` | Enable structured data extraction |

### API Limits and Thresholds

#### Token and Size Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_IMAGE_BYTES` | `4500000` | Maximum image size in bytes |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file size in MB |
| `MAX_TEXT_LENGTH` | `1000000` | Maximum text length |
| `MAX_CHUNK_SIZE` | `2000` | Maximum chunk size |
| `CHUNK_OVERLAP` | `200` | Chunk overlap size |
| `MAX_FILES_PER_REQUEST` | `10` | Maximum files per request |

#### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_REQUESTS` | `10` | Maximum concurrent requests |
| `RATE_LIMIT_PER_MINUTE` | `60` | Rate limit per minute |
| `RATE_LIMIT_PER_HOUR` | `1000` | Rate limit per hour |

#### Retry and Error Handling

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUEST_TIMEOUT_SECONDS` | `300` | Request timeout |
| `MAX_RETRY_ATTEMPTS` | `3` | Maximum retry attempts |
| `RETRY_DELAY_SECONDS` | `5` | Retry delay |
| `API_OVERLOAD_RETRY_SECONDS` | `30` | API overload retry delay |
| `RATE_LIMIT_RETRY_SECONDS` | `60` | Rate limit retry delay |

#### File Processing Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CSV_ROWS` | `10000` | Maximum CSV rows |
| `MAX_BASE64_SIZE_MB` | `5` | Maximum base64 size in MB |

### File Processing Configuration

#### Directory Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT_DIRECTORY` | `output` | Output directory |
| `TEMP_DIRECTORY` | `/tmp` | Temporary directory |
| `UPLOAD_DIRECTORY` | `uploads` | Upload directory |

#### File Validation

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILENAME_LENGTH` | `255` | Maximum filename length |
| `COMPRESSION_QUALITY` | `85` | Image compression quality |
| `MAX_CONCURRENT_UPLOADS` | `5` | Maximum concurrent uploads |

#### File Extensions (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPPORTED_TEXT_EXTENSIONS` | *auto* | Supported text extensions |
| `SUPPORTED_IMAGE_EXTENSIONS` | *auto* | Supported image extensions |
| `ALLOWED_MIME_TYPES` | *auto* | Allowed MIME types |
| `BLOCKED_FILE_PATTERNS` | *auto* | Blocked file patterns |

### Security Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_HTTPS` | `false` | Enable HTTPS |
| `SSL_CERT_PATH` | *empty* | SSL certificate path |
| `SSL_KEY_PATH` | *empty* | SSL key path |
| `MAX_REQUEST_SIZE` | `100` | Maximum request size |
| `ENABLE_RATE_LIMITING` | `false` | Enable rate limiting |
| `API_KEY_REQUIRED` | `false` | Require API key |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |

### CORS Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `*` | CORS origins (comma-separated) |

### Database Configuration (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *empty* | Database connection URL |
| `DATABASE_POOL_SIZE` | `10` | Database pool size |
| `DATABASE_MAX_OVERFLOW` | `20` | Database max overflow |

### Storage Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_TYPE` | `local` | Storage type (local/zoho) |

### Template Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_PROMPT_TEMPLATE` | `t_slip_data_extraction` | Default template |

### Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG_LOG_DIR` | `logs` | Debug log directory |

### Legacy Compatibility

These variables are mapped to the new configuration system for backward compatibility:

| Variable | New Mapping |
|----------|-------------|
| `ENABLE_PDF_BETA` | Feature flags → pdf_beta |
| `ENABLE_LLM_SUMMARIZATION` | Feature flags → llm_summarization |
| `ENABLE_CHUNKING` | Feature flags → chunking |
| `ENABLE_BASE64_INPUT` | Feature flags → base64_input |
| `ENABLE_PANDAS_CLEANING` | Feature flags → pandas_cleaning |

## Environment-Specific Recommendations

### Development
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_DEBUG_MODE=true
ENABLE_REQUEST_LOGGING=true
```

### Staging
```env
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
ENABLE_RATE_LIMITING=true
```

### Production
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ENABLE_RATE_LIMITING=true
ENABLE_HTTPS=true
API_KEY_REQUIRED=true
```

## Migration Notes

The new configuration system maintains backward compatibility with existing environment variables. However, it's recommended to:

1. Use the new structured variable names
2. Update your `.env` file with the new format
3. Remove deprecated variables when convenient

## Validation

The configuration system automatically validates:
- Required API keys
- Numeric ranges (temperature, timeouts, etc.)
- Boolean values
- File paths and directories
- Feature flag dependencies

Invalid configurations will log warnings and use default values.

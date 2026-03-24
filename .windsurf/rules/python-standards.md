---
description: Python coding standards enforcement for Tax AI Agent including PEP 8, type hints, docstrings, and best practices
trigger: always_on
---

# Python Standards Rules

Enforcement rules for Python coding standards in the Tax AI Agent project, ensuring consistency, readability, and maintainability across all code.

## Standards Overview

This rule set enforces:
- **PEP 8** compliance for code formatting
- **Type hints** for better code documentation and IDE support
- **Docstring standards** for consistent API documentation
- **Import organization** for clean dependency management
- **Exception handling** patterns for robust error management
- **Async/await** best practices for concurrent operations

## PEP 8 Compliance Rules

### Line Length and Formatting
- **Maximum line length**: 88 characters (Black formatter standard)
- **Indentation**: 4 spaces, no tabs
- **Blank lines**: 2 between top-level functions, 1 between methods
- **Trailing whitespace**: Not allowed
- **Line endings**: LF (Unix style)

### Naming Conventions
```python
# ✅ Correct
class DocumentProcessor:  # PascalCase for classes
    def process_document(self):  # snake_case for methods/functions
        self.max_file_size = 50  # snake_case for variables
        self.api_client = None  # snake_case for instance attributes
    
    MAX_RETRIES = 3  # UPPER_CASE for constants
    DEFAULT_TIMEOUT = 30  # UPPER_CASE for constants

# ❌ Incorrect
class documentProcessor:  # Should be PascalCase
    def ProcessDocument(self):  # Should be snake_case
        self.MaxFileSize = 50  # Should be snake_case
```

### Import Organization
```python
# ✅ Correct order and formatting
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from anthropic import Anthropic

from core.config import ANTHROPIC_API_KEY
from services.llm_service import LLMService
from utils.logger import get_logger

# ❌ Incorrect - wrong order, unused imports
from anthropic import Anthropic
import os, sys
from services.llm_service import LLMService, DocumentProcessor  # Unused import
```

## Type Hints Requirements

### Function Signatures
```python
# ✅ Complete type hints
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

@dataclass
class DocumentResult:
    content: str
    metadata: Dict[str, str]
    success: bool

def process_documents(
    files: List[str], 
    prompt: str,
    template_name: Optional[str] = None
) -> List[DocumentResult]:
    """Process multiple documents with the given prompt."""
    pass

# ❌ Missing type hints
def process_documents(files, prompt, template_name=None):
    """Process multiple documents with the given prompt."""
    pass
```

### Complex Type Annotations
```python
# ✅ Proper complex types
from typing import Dict, List, Optional, Union, Callable, Any
from collections.abc import AsyncGenerator

async def stream_llm_response(
    prompt: str,
    temperature: float = 0.0,
    callback: Optional[Callable[[str], None]] = None
) -> AsyncGenerator[str, None]:
    """Stream LLM response with optional callback."""
    pass

# ❌ Vague or missing types
async def stream_llm_response(prompt, temperature=0.0, callback=None):
    """Stream LLM response with optional callback."""
    pass
```

## Docstring Standards

### Google Style Docstrings
```python
# ✅ Google style with complete sections
def extract_text_from_pdf(
    file_path: str, 
    password: Optional[str] = None
) -> Dict[str, Any]:
    """Extract text content from PDF file.
    
    Args:
        file_path: Path to the PDF file to process.
        password: Optional password for encrypted PDFs.
        
    Returns:
        Dictionary containing extracted text and metadata.
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
        PasswordProtectedPDFException: If password is required but not provided.
        
    Example:
        >>> result = extract_text_from_pdf("document.pdf")
        >>> print(result["text"])
        "Extracted content..."
    """
    pass

# ❌ Incomplete or missing docstring
def extract_text_from_pdf(file_path, password=None):
    """Extract text from PDF."""
    pass
```

### Class Docstrings
```python
# ✅ Complete class documentation
class LLMService:
    """Service for interacting with Large Language Models.
    
    This service provides a unified interface for various LLM providers,
    handling authentication, rate limiting, and response parsing.
    
    Attributes:
        client: The underlying LLM client instance.
        model_name: The name of the model being used.
        temperature: Sampling temperature for generation.
        
    Example:
        >>> service = LLMService("claude-3-5-sonnet-20241022")
        >>> response = await service.generate("Hello, world!")
    """
    
    def __init__(self, model_name: str, temperature: float = 0.0):
        """Initialize the LLM service.
        
        Args:
            model_name: Name of the LLM model to use.
            temperature: Sampling temperature for responses.
        """
        pass
```

## Exception Handling Patterns

### Specific Exception Types
```python
# ✅ Specific exception handling
from exceptions.document_exceptions import (
    PasswordProtectedPDFException,
    UnsupportedFileFormatException
)
from exceptions.base_exceptions import ConfigurationException

async def process_document(file_path: str) -> Dict[str, Any]:
    """Process document with proper exception handling."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Process document logic here
        result = await _extract_content(file_path)
        return result
        
    except PasswordProtectedPDFException as e:
        logger.error(f"Password protected PDF: {e}")
        raise
    except UnsupportedFileFormatException as e:
        logger.warning(f"Unsupported format: {e}")
        return {"error": str(e), "success": False}
    except Exception as e:
        logger.error(f"Unexpected error processing {file_path}: {e}")
        raise DocumentProcessingError(f"Failed to process {file_path}") from e

# ❌ Generic exception handling
async def process_document(file_path):
    try:
        # Process document
        pass
    except Exception as e:
        print(f"Error: {e}")  # Too generic, no logging
        return None
```

### Context Manager Usage
```python
# ✅ Proper resource management
async def process_uploaded_file(file_data: bytes, output_path: str) -> None:
    """Process uploaded file with proper resource cleanup."""
    async with aiofiles.open(output_path, 'wb') as f:
        await f.write(file_data)
    
    # Use context managers for temporary resources
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_data)
        temp_path = temp_file.name
    
    try:
        await process_file(temp_path)
    finally:
        os.unlink(temp_path)  # Always cleanup

# ❌ Resource leaks
async def process_uploaded_file(file_data: bytes, output_path: str) -> None:
    f = open(output_path, 'wb')  # File not properly closed
    f.write(file_data)
    # Missing f.close()
```

## Async/Await Best Practices

### Proper Async Patterns
```python
# ✅ Correct async usage
import asyncio
from typing import List

async def process_multiple_documents(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Process multiple documents concurrently."""
    # Create tasks for concurrent processing
    tasks = [process_single_document(path) for path in file_paths]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions in results
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Failed to process {file_paths[i]}: {result}")
            processed_results.append({"error": str(result), "success": False})
        else:
            processed_results.append(result)
    
    return processed_results

# ❌ Blocking calls in async functions
async def process_multiple_documents(file_paths: List[str]) -> List[Dict[str, Any]]:
    results = []
    for path in file_paths:
        result = process_single_document(path)  # Blocking call!
        results.append(result)
    return results
```

### Async Context Managers
```python
# ✅ Proper async context managers
async def process_with_timeout(operation: Callable, timeout: float) -> Any:
    """Execute operation with timeout."""
    try:
        async with asyncio.timeout(timeout):
            result = await operation()
            return result
    except TimeoutError:
        logger.warning(f"Operation timed out after {timeout}s")
        raise

# ❌ Missing async context management
async def process_with_timeout(operation: Callable, timeout: float) -> Any:
    # No timeout handling
    result = await operation()
    return result
```

## Code Quality Rules

### Magic Numbers and Constants
```python
# ✅ Use named constants
MAX_FILE_SIZE_MB = 50
DEFAULT_TEMPERATURE = 0.0
REQUEST_TIMEOUT_SECONDS = 300

def validate_file_size(file_size: int) -> bool:
    return file_size <= MAX_FILE_SIZE_MB * 1024 * 1024

# ❌ Magic numbers
def validate_file_size(file_size: int) -> bool:
    return file_size <= 50 * 1024 * 1024  # What is 50?
```

### Function Complexity
```python
# ✅ Single responsibility, simple functions
def extract_text(content: str) -> str:
    """Extract plain text from content."""
    # Simple extraction logic
    return content.strip()

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Cleaning logic
    return text.replace('\n', ' ').strip()

def process_content(content: str) -> str:
    """Process content through extraction and cleaning."""
    text = extract_text(content)
    return clean_text(text)

# ❌ Complex function doing too much
def process_content(content: str) -> str:
    """Extract, clean, validate, format, and return content."""
    # 50+ lines of complex logic
    # Multiple responsibilities
    # Hard to test and maintain
    pass
```

## Validation Rules

### Required Tools
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **flake8**: Linting
- **pydocstyle**: Docstring checking

### Validation Commands
```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy core/ services/ api/ --strict

# Linting
flake8 core/ services/ api/ --max-line-length=88

# Docstring checking
pydocstyle core/ services/ api/
```

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-line-length=88]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Enforcement

### Automated Checks
1. **Pre-commit hooks** - Run on every commit
2. **CI pipeline** - Run on every pull request
3. **Code reviews** - Manual verification
4. **Regular audits** - Weekly compliance checks

### Failure Handling
- **Block commits** for critical violations
- **Create issues** for non-critical improvements
- **Provide feedback** with specific fix suggestions
- **Track metrics** for compliance over time

## Best Practices Summary

1. **Always use type hints** for function signatures and complex types
2. **Write comprehensive docstrings** following Google style
3. **Handle exceptions specifically** with proper logging
4. **Use async/await correctly** for concurrent operations
5. **Keep functions simple** with single responsibilities
6. **Use named constants** instead of magic numbers
7. **Format code consistently** using automated tools
8. **Validate imports** and remove unused dependencies

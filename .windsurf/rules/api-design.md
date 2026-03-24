---
description: API design standards and RESTful principles enforcement for Tax AI Agent FastAPI endpoints
---

# API Design Rules

Enforcement rules for API design in Tax AI Agent project, ensuring RESTful principles, consistent patterns, and comprehensive OpenAPI documentation.

## API Design Standards

This rule set enforces:
- **RESTful API principles** for resource-oriented design
- **Consistent response formats** across all endpoints
- **Proper HTTP status codes** for different scenarios
- **OpenAPI specification** completeness and accuracy
- **Error handling patterns** for robust client experience
- **Rate limiting and security** best practices

## RESTful API Principles

### Resource-Oriented Design

#### ✅ Correct RESTful Patterns
```python
# api/routes.py
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional

router = APIRouter()

# Resource naming conventions
@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum documents to return"),
    status: Optional[str] = Query(None, description="Filter by document status")
) -> List[DocumentResponse]:
    """List all documents with pagination and filtering."""
    pass

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str = Path(..., description="Document identifier")
) -> DocumentResponse:
    """Get a specific document by ID."""
    pass

@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def create_document(
    document: DocumentCreate = Body(..., description="Document to create")
) -> DocumentResponse:
    """Create a new document."""
    pass

@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str = Path(..., description="Document identifier"),
    document: DocumentUpdate = Body(..., description="Document updates")
) -> DocumentResponse:
    """Update an existing document."""
    pass

@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str = Path(..., description="Document identifier")
) -> None:
    """Delete a document."""
    pass

# Nested resources
@router.get("/documents/{document_id}/processing", response_model=ProcessingStatusResponse)
async def get_document_processing_status(
    document_id: str = Path(..., description="Document identifier")
) -> ProcessingStatusResponse:
    """Get processing status for a specific document."""
    pass

@router.post("/documents/{document_id}/process", response_model=ProcessingResponse)
async def process_document(
    document_id: str = Path(..., description="Document identifier"),
    processing_request: ProcessingRequest = Body(..., description="Processing configuration")
) -> ProcessingResponse:
    """Start processing a document."""
    pass
```

#### ❌ Non-RESTful Patterns
```python
# Bad: Action-based instead of resource-based
@router.post("/processDocument")
async def process_document(document_data: dict):
    """Not RESTful - should be POST to /documents/{id}/process"""
    pass

@router.get("/getAllDocuments")
async def get_all_documents():
    """Not RESTful - should be GET /documents"""
    pass

@router.post("/documents/delete/{document_id}")
async def delete_document(document_id: str):
    """Not RESTful - should be DELETE /documents/{document_id}"""
    pass

# Bad: Inconsistent naming
@router.get("/docs")
async def list_documents():
    """Should be /documents, not /docs"""
    pass

@router.get("/doc/{doc_id}")
async def get_document(doc_id: str):
    """Should be /documents/{document_id}"""
    pass
```

### HTTP Method Usage

#### Proper HTTP Method Mapping
```python
# ✅ Correct HTTP method usage
@router.get("/templates")                    # List resources
async def list_templates() -> List[Template]:
    pass

@router.post("/templates", status_code=201)    # Create resource
async def create_template(template: TemplateCreate) -> Template:
    pass

@router.get("/templates/{template_id}")        # Get specific resource
async def get_template(template_id: str) -> Template:
    pass

@router.put("/templates/{template_id}")        # Update entire resource
async def update_template(template_id: str, template: TemplateUpdate) -> Template:
    pass

@router.patch("/templates/{template_id}")       # Partial update
async def patch_template(template_id: str, template: TemplatePatch) -> Template:
    pass

@router.delete("/templates/{template_id}")    # Delete resource
async def delete_template(template_id: str) -> None:
    pass

# ✅ Action endpoints (when necessary)
@router.post("/templates/{template_id}/validate")  # Action on resource
async def validate_template(template_id: str) -> ValidationResult:
    pass

@router.post("/documents/batch")                   # Batch operations
async def batch_process_documents(request: BatchRequest) -> BatchResponse:
    pass
```

## Response Format Standards

### Consistent Response Structure

#### ✅ Standard Response Models
```python
# models/responses.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = Field(description="Request success status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = Field(default=False, description="Request failed")
    error_code: str = Field(description="Machine-readable error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class PaginatedResponse(BaseResponse):
    """Paginated response model."""
    items: List[Any] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum items per page")
    has_more: bool = Field(description="Whether more items are available")

# Specific response models
class DocumentResponse(BaseModel):
    """Document response model."""
    id: str = Field(description="Document identifier")
    filename: str = Field(description="Original filename")
    status: str = Field(description="Processing status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")

class ProcessingResponse(BaseResponse):
    """Processing response model."""
    processing_id: str = Field(description="Processing job identifier")
    status: str = Field(description="Processing status")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    result_url: Optional[str] = Field(None, description="URL to download results")
```

#### ❌ Inconsistent Response Formats
```python
# Bad: Inconsistent response structures
@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Returns document object directly - inconsistent with other endpoints."""
    return {"id": document_id, "data": "..."}

@router.get("/templates")
async def list_templates():
    """Returns list directly - no wrapper object."""
    return [{"id": "1", "name": "template1"}]

@router.post("/documents")
async def create_document(document: dict):
    """Returns success message only - no data."""
    return {"message": "Document created"}

@router.get("/health")
async def health_check():
    """Returns different format than other endpoints."""
    return {"status": "ok", "version": "1.0.0"}
```

### Error Handling Patterns

#### Standardized Error Responses
```python
# exceptions/handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

class APIException(Exception):
    """Base API exception."""
    def __init__(self, status_code: int, error_code: str, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details

class ValidationException(APIException):
    """Validation error exception."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(400, "VALIDATION_ERROR", message, details)

class ResourceNotFoundException(APIException):
    """Resource not found exception."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(404, "RESOURCE_NOT_FOUND", 
                       f"{resource} with identifier '{identifier}' not found")

class ConflictException(APIException):
    """Resource conflict exception."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(409, "CONFLICT", message, details)

# Exception handlers
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=exc.message,
            error_code=exc.error_code,
            error_details=exc.details
        ).dict()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors."""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            error_details={"validation_errors": exc.errors()}
        ).dict()
    )

# Usage in endpoints
@router.get("/documents/{document_id}")
async def get_document(document_id: str) -> DocumentResponse:
    """Get document with proper error handling."""
    try:
        document = await document_service.get_by_id(document_id)
        if not document:
            raise ResourceNotFoundException("Document", document_id)
        return DocumentResponse.from_orm(document)
    except DocumentServiceException as e:
        raise APIException(500, "SERVICE_ERROR", str(e))
```

## OpenAPI Documentation Standards

### Comprehensive Endpoint Documentation

#### ✅ Complete OpenAPI Documentation
```python
# api/routes.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()

class DocumentProcessingRequest(BaseModel):
    """Request model for document processing."""
    prompt: str = Field(
        ...,
        description="Natural language instruction for document processing",
        example="Extract all financial information and format as CSV",
        min_length=10,
        max_length=2000
    )
    template_name: Optional[str] = Field(
        None,
        description="Name of predefined template to use",
        example="t_slip_data_extraction"
    )
    temperature: Optional[float] = Field(
        0.0,
        description="LLM sampling temperature (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
        example=0.1
    )
    ctid: Optional[str] = Field(
        None,
        description="Correlation tracking ID for request tracing",
        example="req_123456789"
    )

class DocumentProcessingResponse(BaseModel):
    """Response model for document processing."""
    status: str = Field(
        description="Processing status",
        example="completed"
    )
    format: str = Field(
        description="Detected output format",
        example="markdown"
    )
    file: str = Field(
        description="Path to primary generated file",
        example="output/run_20240323_125958_9e717e/summary_report.md"
    )
    folder: str = Field(
        description="Run folder path containing all artifacts",
        example="output/run_20240323_125958_9e717e"
    )
    download_url: str = Field(
        description="Relative URL to download main output",
        example="/ai/download?file=summary_report.md&folder=run_20240323_125958_9e717e"
    )
    ctid: Optional[str] = Field(
        None,
        description="Echoed correlation tracking ID"
    )

@router.post(
    "/ai/process",
    response_model=DocumentProcessingResponse,
    summary="Process uploaded documents with AI",
    description="""
    Process one or more uploaded documents using AI with a natural language prompt.
    
    This endpoint accepts multiple file formats (PDF, images, CSV) and processes them
    using the configured LLM. The processing can use predefined templates or custom prompts.
    
    **File Processing:**
    - PDFs: Extract text content, handle password-protected files
    - Images: OCR text extraction using vision models
    - CSV: Direct data processing
    
    **Output Formats:**
    - Markdown: Structured reports with narrative
    - CSV: Tabular data extraction
    - Mixed: Both markdown and CSV when appropriate
    
    **Error Handling:**
    - Returns detailed error messages for validation failures
    - Supports correlation tracking with ctid parameter
    - Provides download URLs for all generated artifacts
    """,
    responses={
        200: {
            "description": "Document processing completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "completed",
                        "format": "markdown",
                        "file": "summary_report.md",
                        "folder": "run_20240323_125958_9e717e",
                        "download_url": "/ai/download?file=summary_report.md&folder=run_20240323_125958_9e717e",
                        "ctid": "req_123456789"
                    }
                }
            }
        },
        400: {
            "description": "Validation error - invalid request parameters",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "VALIDATION_ERROR",
                        "message": "Invalid prompt: must be between 10 and 2000 characters",
                        "error_details": {
                            "validation_errors": [
                                {
                                    "loc": ["body", "prompt"],
                                    "msg": "ensure this value has at least 10 characters",
                                    "type": "value_error.any_str.min_length",
                                    "ctx": {"limit_value": 10}
                                }
                            ]
                        }
                    }
                }
            }
        },
        413: {
            "description": "Request entity too large - files exceed size limit",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "FILE_TOO_LARGE",
                        "message": "File size exceeds maximum allowed limit of 50MB",
                        "error_details": {
                            "max_size_mb": 50,
                            "actual_size_mb": 75.5
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error - processing failed",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error_code": "PROCESSING_ERROR",
                        "message": "Document processing failed due to LLM service error",
                        "error_details": {
                            "processing_id": "proc_123456789",
                            "error_type": "LLM_SERVICE_ERROR"
                        }
                    }
                }
            }
        }
    },
    tags=["Document Processing"]
)
async def process_documents(
    files: List[UploadFile] = File(
        ...,
        description="Files to process (PDF, JPG, PNG, CSV supported)",
        example=[
            {
                "filename": "tax_document.pdf",
                "content_type": "application/pdf",
                "size": 1048576
            }
        ]
    ),
    request: DocumentProcessingRequest = Body(..., description="Processing configuration")
) -> DocumentProcessingResponse:
    """Process uploaded documents with AI using specified prompt and optional template."""
    pass
```

#### ❌ Incomplete Documentation
```python
# Bad: Missing comprehensive documentation
@router.post("/ai/process")
async def process_documents(files: List[UploadFile], prompt: str):
    """Process documents."""
    # No description, examples, or response models
    pass

@router.get("/templates")
async def get_templates():
    """Get templates."""
    # No response model or documentation
    pass
```

## Input Validation and Security

### Request Validation Patterns

#### ✅ Comprehensive Input Validation
```python
# models/requests.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class DocumentUploadRequest(BaseModel):
    """Request model for document upload with validation."""
    
    filename: str = Field(
        ...,
        description="Original filename",
        min_length=1,
        max_length=255,
        regex=r"^[a-zA-Z0-9._-]+$"  # Allowed characters only
    )
    
    file_size: int = Field(
        ...,
        description="File size in bytes",
        ge=1,
        le=50 * 1024 * 1024  # 50MB max
    )
    
    content_type: str = Field(
        ...,
        description="MIME type of the file",
        regex=r"^(application/pdf|image/(jpeg|png)|text/csv)$"
    )
    
    description: Optional[str] = Field(
        None,
        description="Optional file description",
        max_length=500
    )
    
    tags: Optional[List[str]] = Field(
        None,
        description="File tags for organization",
        max_items=10
    )
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("Tag length cannot exceed 50 characters")
                if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                    raise ValueError("Tags can only contain alphanumeric characters, hyphens, and underscores")
        return v

class ProcessingRequest(BaseModel):
    """Request model for document processing."""
    
    prompt: str = Field(
        ...,
        description="Natural language instruction for processing",
        min_length=10,
        max_length=2000,
        example="Extract all financial information and format as CSV"
    )
    
    template_name: Optional[str] = Field(
        None,
        description="Predefined template name",
        regex=r"^[a-z_][a-z0-9_]*$"  # Template naming convention
    )
    
    temperature: float = Field(
        0.0,
        description="LLM sampling temperature",
        ge=0.0,
        le=1.0
    )
    
    max_tokens: Optional[int] = Field(
        None,
        description="Maximum tokens in response",
        ge=100,
        le=64000
    )
    
    @validator('template_name')
    def validate_template_name(cls, v, values):
        if v:
            # Check if template exists
            from services.template_service import template_service
            if not template_service.template_exists(v):
                raise ValueError(f"Template '{v}' does not exist")
        return v
```

### Security Headers and Rate Limiting

#### ✅ Security Best Practices
```python
# middleware/security.py
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Add security headers and handle security concerns."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

# Apply rate limiting to endpoints
@router.post(
    "/ai/process",
    dependencies=[Depends(limiter.limit("10/minute"))]
)
async def process_documents(request: ProcessingRequest):
    """Rate limited to 10 requests per minute."""
    pass

@router.get(
    "/templates",
    dependencies=[Depends(limiter.limit("100/minute"))]
)
async def get_templates():
    """Rate limited to 100 requests per minute."""
    pass
```

## API Versioning and Evolution

### Versioning Strategy

#### ✅ Proper API Versioning
```python
# api/v1/routes.py
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1", tags=["API v1"])

@v1_router.post("/documents/process")
async def process_documents_v1():
    """Version 1 of document processing endpoint."""
    pass

# api/v2/routes.py  
from fastapi import APIRouter

v2_router = APIRouter(prefix="/api/v2", tags=["API v2"])

@v2_router.post("/documents/process")
async def process_documents_v2():
    """Version 2 with enhanced features."""
    pass

# main.py
from api.v1 import routes as v1_routes
from api.v2 import routes as v2_routes

app.include_router(v1_routes.v1_router)
app.include_router(v2_routes.v2_router)

# Default to latest version
@app.post("/documents/process")
async def process_documents_latest():
    """Redirects to latest version."""
    return await v2_routes.process_documents_v2()
```

## Validation Rules

### Automated API Quality Checks

#### OpenAPI Specification Validation
```bash
# Validate OpenAPI specification completeness
python - << 'EOF'
import json
import requests
from typing import Dict, List

def validate_openapi_spec(spec_url: str = "http://127.0.0.1:8000/openapi.json"):
    """Validate OpenAPI specification for completeness."""
    
    try:
        spec = requests.get(spec_url).json()
        issues = []
        
        # Check basic structure
        required_keys = ['openapi', 'info', 'paths']
        for key in required_keys:
            if key not in spec:
                issues.append(f"Missing required key: {key}")
        
        # Check endpoint documentation
        for path, methods in spec.get('paths', {}).items():
            for method, details in methods.items():
                if 'summary' not in details:
                    issues.append(f"{method.upper()} {path}: Missing summary")
                
                if 'description' not in details:
                    issues.append(f"{method.upper()} {path}: Missing description")
                
                if 'responses' not in details:
                    issues.append(f"{method.upper()} {path}: Missing responses")
                
                # Check response documentation
                responses = details.get('responses', {})
                if '200' not in responses and '201' not in responses:
                    issues.append(f"{method.upper()} {path}: Missing success response")
        
        # Check schema documentation
        components = spec.get('components', {}).get('schemas', {})
        for schema_name, schema in components.items():
            if 'description' not in schema:
                issues.append(f"Schema {schema_name}: Missing description")
        
        return issues
    
    except Exception as e:
        return [f"Failed to validate OpenAPI spec: {e}"]

# Run validation
issues = validate_openapi_spec()
if issues:
    print("OpenAPI Validation Issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ OpenAPI specification validation passed")
EOF
```

### Response Format Validation
```bash
# Validate response format consistency
python - << 'EOF'
import ast
import inspect
from pathlib import Path
from typing import Dict, List, Set

def validate_response_models() -> List[str]:
    """Validate response model consistency."""
    issues = []
    
    # Find all response models
    response_models = set()
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or '.pytest_cache' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if 'Response' in node.name:
                        response_models.add(node.name)
        except:
            pass
    
    # Check endpoints use response models
    for py_file in Path('api').rglob('*.py'):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    # Check for response_model parameter
                    for decorator in node.decorator_list:
                        if (isinstance(decorator, ast.Call) and
                            isinstance(decorator.func, ast.Name) and
                            decorator.func.id in ['get', 'post', 'put', 'delete', 'patch']):
                            
                            for keyword in decorator.keywords:
                                if keyword.arg == 'response_model':
                                    # Check if using proper response model
                                    if isinstance(keyword.value, ast.Name):
                                        model_name = keyword.value.id
                                        if model_name not in response_models:
                                            issues.append(
                                                f"Endpoint {node.name} uses undefined response model {model_name}"
                                            )
        except:
            pass
    
    return issues

# Run validation
issues = validate_response_models()
if issues:
    print("Response Model Validation Issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ Response model validation passed")
EOF
```

## Best Practices Summary

1. **Use resource-oriented URLs** - `/documents/{id}` instead of `/getDocument`
2. **Use proper HTTP methods** - GET for read, POST for create, PUT/PATCH for update, DELETE for remove
3. **Provide consistent response formats** - Use standardized response models
4. **Document all endpoints thoroughly** - Include examples, error responses, and detailed descriptions
5. **Validate all inputs** - Use Pydantic models with comprehensive validation
6. **Handle errors consistently** - Use standard error response format
7. **Implement rate limiting** - Protect against abuse
8. **Use API versioning** - Plan for future evolution
9. **Include security headers** - Implement security best practices
10. **Test API contracts** - Validate OpenAPI specification completeness

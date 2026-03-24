---
description: SOLID principles enforcement for Tax AI Agent service architecture and design patterns
trigger: always_on
---

# SOLID Principles Rules

Enforcement rules for SOLID principles in the Tax AI Agent project, ensuring maintainable, scalable, and robust service-oriented architecture.

## SOLID Overview

This rule set enforces the five SOLID principles:
- **S**ingle Responsibility Principle (SRP)
- **O**pen/Closed Principle (OCP)  
- **L**iskov Substitution Principle (LSP)
- **I**nterface Segregation Principle (ISP)
- **D**ependency Inversion Principle (DIP)

## Single Responsibility Principle (SRP)

### Rule: Each class should have only one reason to change

#### ✅ Correct Implementation
```python
# services/document_processing_service.py
class DocumentProcessingService:
    """Handles document processing operations only."""
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a single document."""
        pass

# services/file_validation_service.py  
class FileValidationService:
    """Handles file validation operations only."""
    
    def validate_file(self, file_path: str) -> bool:
        """Validate file format and size."""
        pass

# services/storage_service.py
class StorageService:
    """Handles file storage operations only."""
    
    async def save_file(self, content: bytes, path: str) -> str:
        """Save file to storage."""
        pass
```

#### ❌ Violation - Multiple Responsibilities
```python
# Bad: Class doing too many things
class DocumentService:
    """Handles processing, validation, storage, and logging."""
    
    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process document."""
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """Validate file format."""
        pass
    
    async def save_file(self, content: bytes, path: str) -> str:
        """Save to storage."""
        pass
    
    def log_operation(self, operation: str, details: Dict) -> None:
        """Log operations."""
        pass
```

### Validation Rules

#### Class Size and Complexity
- **Maximum methods per class**: 15 (excluding private helpers)
- **Maximum lines per class**: 300 (excluding docstrings and comments)
- **Cyclomatic complexity**: < 10 per method
- **Single purpose**: Clear, focused responsibility

#### Method Responsibility
```python
# ✅ Single responsibility per method
class OutputGenerationService:
    def _determine_output_format(self, content: str) -> str:
        """Determine if content is markdown, CSV, or mixed."""
        # Only format detection logic
        pass
    
    def _extract_csv_from_markdown(self, content: str) -> Optional[str]:
        """Extract CSV blocks from markdown content."""
        # Only CSV extraction logic
        pass
    
    def _create_summary_report(self, data: Dict) -> str:
        """Create markdown summary report."""
        # Only report generation logic
        pass

# ❌ Multiple responsibilities in single method
class OutputGenerationService:
    def process_content(self, content: str) -> Dict[str, str]:
        """Process content - doing too many things."""
        # Format detection
        if "```csv" in content:
            format_type = "csv"
        
        # CSV extraction
        csv_content = self._extract_csv(content)
        
        # Report generation
        report = self._generate_report(content)
        
        # File saving
        self._save_files(csv_content, report)
        
        # Logging
        self._log_processing(format_type)
        
        return {"format": format_type, "csv": csv_content, "report": report}
```

## Open/Closed Principle (OCP)

### Rule: Software entities should be open for extension, closed for modification

#### ✅ Correct Implementation - Strategy Pattern
```python
# strategies/text_extraction_strategy.py
from abc import ABC, abstractmethod

class TextExtractionStrategy(ABC):
    """Abstract base for text extraction strategies."""
    
    @abstractmethod
    async def extract(self, file_path: str) -> str:
        """Extract text from file."""
        pass

class PDFExtractionStrategy(TextExtractionStrategy):
    """PDF text extraction implementation."""
    
    async def extract(self, file_path: str) -> str:
        """Extract text from PDF."""
        pass

class ImageExtractionStrategy(TextExtractionStrategy):
    """Image OCR text extraction implementation."""
    
    async def extract(self, file_path: str) -> str:
        """Extract text from image using OCR."""
        pass

class CSVExtractionStrategy(TextExtractionStrategy):
    """CSV text extraction implementation."""
    
    async def extract(self, file_path: str) -> str:
        """Extract text from CSV."""
        pass

# services/document_processor.py
class DocumentProcessor:
    """Processor that can work with any extraction strategy."""
    
    def __init__(self, strategy: TextExtractionStrategy):
        self.strategy = strategy
    
    async def process(self, file_path: str) -> str:
        """Process document using configured strategy."""
        return await self.strategy.extract(file_path)

# Easy to extend without modifying existing code
class WordExtractionStrategy(TextExtractionStrategy):
    """Word document extraction - new feature."""
    
    async def extract(self, file_path: str) -> str:
        """Extract text from Word document."""
        pass
```

#### ❌ Violation - Modification Required
```python
# Bad: Need to modify this class for new file types
class DocumentProcessor:
    """Processor that needs modification for new types."""
    
    async def process(self, file_path: str) -> str:
        """Process document - needs modification for new types."""
        if file_path.endswith('.pdf'):
            return await self._extract_pdf(file_path)
        elif file_path.endswith('.jpg'):
            return await self._extract_image(file_path)
        elif file_path.endswith('.csv'):
            return await self._extract_csv(file_path)
        # Need to add more elif for new file types!
        else:
            raise UnsupportedFileException(f"Unsupported type: {file_path}")
```

### Validation Rules

#### Extensibility Patterns
- **Use abstract base classes** for common interfaces
- **Implement strategy pattern** for algorithms
- **Use factory pattern** for object creation
- **Avoid hardcoded type checks** in business logic

#### Configuration-Based Extension
```python
# ✅ Configuration-driven extension
class TemplateService:
    """Service that loads templates from configuration."""
    
    def __init__(self, template_config: Dict[str, Any]):
        self.templates = template_config
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get template by name."""
        return self.templates.get(name)

# New templates can be added without code changes
TEMPLATE_CONFIG = {
    "t_slip_extraction": {...},
    "medical_tax_credit": {...},
    "new_template_type": {...}  # Can be added in config only
}
```

## Liskov Substitution Principle (LSP)

### Rule: Subtypes must be substitutable for their base types

#### ✅ Correct Implementation
```python
# services/llm_service.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstract base for LLM providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate text response."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Get model information."""
        pass

class AnthropicProvider(LLMProvider):
    """Anthropic Claude implementation."""
    
    async def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate using Anthropic API."""
        # Implementation that respects the contract
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.content[0].text
    
    def get_model_info(self) -> Dict[str, str]:
        """Get Anthropic model info."""
        return {"provider": "anthropic", "model": self.model}

class OpenAIProvider(LLMProvider):
    """OpenAI GPT implementation."""
    
    async def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate using OpenAI API."""
        # Implementation that respects the contract
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def get_model_info(self) -> Dict[str, str]:
        """Get OpenAI model info."""
        return {"provider": "openai", "model": self.model}

# Both can be substituted without breaking the client
async def process_with_llm(provider: LLMProvider, prompt: str) -> str:
    """Process prompt with any LLM provider."""
    return await provider.generate(prompt, temperature=0.0)
```

#### ❌ Violation - Breaking Substitution
```python
# Bad: Subclass changes behavior contract
class FastLLMProvider(LLMProvider):
    """Provider that breaks the contract."""
    
    async def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """Returns cached results - different behavior!"""
        # This changes the expected behavior
        cached_result = self.cache.get(prompt)
        if cached_result:
            return cached_result  # Different from base behavior
        
        # Sometimes returns None - breaks contract
        if len(prompt) > 1000:
            return None  # Base class never returns None
        
        return await super().generate(prompt, temperature)
```

### Validation Rules

#### Contract Compliance
- **Method signatures** must match base class exactly
- **Return types** must be compatible
- **Exceptions** must not be more specific than base
- **Behavior** must maintain base class invariants

#### Preconditions and Postconditions
```python
# ✅ Maintains contract
class SecureLLMProvider(LLMProvider):
    """Provider that adds security while maintaining contract."""
    
    async def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate with security checks."""
        # Precondition: validate input
        self._validate_prompt(prompt)
        
        # Core functionality (same as base)
        result = await self._secure_generate(prompt, temperature)
        
        # Postcondition: ensure valid response
        return self._ensure_valid_response(result)
```

## Interface Segregation Principle (ISP)

### Rule: Clients should not be forced to depend on interfaces they don't use

#### ✅ Correct Implementation - Segregated Interfaces
```python
# interfaces/storage_interfaces.py
from abc import ABC, abstractmethod

class FileReader(ABC):
    """Interface for reading files."""
    
    @abstractmethod
    async def read(self, path: str) -> bytes:
        """Read file content."""
        pass

class FileWriter(ABC):
    """Interface for writing files."""
    
    @abstractmethod
    async def write(self, path: str, content: bytes) -> None:
        """Write file content."""
        pass

class FileDeleter(ABC):
    """Interface for deleting files."""
    
    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file."""
        pass

# Implementations can implement only needed interfaces
class ReadOnlyStorageService(FileReader):
    """Service that only reads files."""
    
    async def read(self, path: str) -> bytes:
        """Read file content."""
        pass
    # No need to implement write/delete

class ReadWriteStorageService(FileReader, FileWriter):
    """Service that reads and writes files."""
    
    async def read(self, path: str) -> bytes:
        """Read file content."""
        pass
    
    async def write(self, path: str, content: bytes) -> None:
        """Write file content."""
        pass
    # No need to implement delete
```

#### ❌ Violation - Fat Interface
```python
# Bad: Forces implementation of unused methods
class FileService(ABC):
    """Fat interface with too many responsibilities."""
    
    @abstractmethod
    async def read(self, path: str) -> bytes:
        """Read file."""
        pass
    
    @abstractmethod
    async def write(self, path: str, content: bytes) -> None:
        """Write file."""
        pass
    
    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file."""
        pass
    
    @abstractmethod
    async def copy(self, source: str, destination: str) -> None:
        """Copy file."""
        pass
    
    @abstractmethod
    async def move(self, source: str, destination: str) -> None:
        """Move file."""
        pass

# Client forced to implement methods it doesn't need
class ReadOnlyFileService(FileService):
    """Only needs to read files but must implement all methods."""
    
    async def read(self, path: str) -> bytes:
        return b"content"
    
    async def write(self, path: str, content: bytes) -> None:
        raise NotImplementedError("Write not supported")
    
    async def delete(self, path: str) -> None:
        raise NotImplementedError("Delete not supported")
    
    async def copy(self, source: str, destination: str) -> None:
        raise NotImplementedError("Copy not supported")
    
    async def move(self, source: str, destination: str) -> None:
        raise NotImplementedError("Move not supported")
```

### Validation Rules

#### Interface Design
- **Small, focused interfaces** with 1-3 methods
- **Role-based interfaces** for different client needs
- **Composition over inheritance** for multiple behaviors
- **Optional interfaces** for extended functionality

#### Client-Specific Interfaces
```python
# ✅ Role-based interface design
class DocumentValidator(ABC):
    """Interface for document validation."""
    
    @abstractmethod
    def validate(self, document: Dict[str, Any]) -> bool:
        """Validate document."""
        pass

class DocumentProcessor(ABC):
    """Interface for document processing."""
    
    @abstractmethod
    async def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process document."""
        pass

class DocumentFormatter(ABC):
    """Interface for document formatting."""
    
    @abstractmethod
    def format(self, document: Dict[str, Any]) -> str:
        """Format document."""
        pass
```

## Dependency Inversion Principle (DIP)

### Rule: High-level modules should not depend on low-level modules; both should depend on abstractions

#### ✅ Correct Implementation - Dependency Injection
```python
# abstractions/notification_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class NotificationService(ABC):
    """Abstract notification service."""
    
    @abstractmethod
    async def send_notification(self, message: str, recipient: str) -> bool:
        """Send notification."""
        pass

# implementations/email_notification.py
class EmailNotificationService(NotificationService):
    """Email notification implementation."""
    
    async def send_notification(self, message: str, recipient: str) -> bool:
        """Send email notification."""
        # Email implementation
        pass

# implementations/slack_notification.py
class SlackNotificationService(NotificationService):
    """Slack notification implementation."""
    
    async def send_notification(self, message: str, recipient: str) -> bool:
        """Send Slack notification."""
        # Slack implementation
        pass

# high_level/document_processor.py
class DocumentProcessor:
    """High-level module depending on abstraction."""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
    
    async def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process document with notifications."""
        # Business logic
        result = await self._do_processing(document)
        
        # Notify via injected dependency
        await self.notification_service.send_notification(
            f"Document processed: {result['id']}",
            "user@example.com"
        )
        
        return result
```

#### ❌ Violation - Direct Dependency
```python
# Bad: High-level module depends on low-level implementation
class DocumentProcessor:
    """High-level module directly depending on low-level."""
    
    def __init__(self):
        self.email_service = EmailNotificationService()  # Direct dependency
        self.file_service = LocalFileService()  # Direct dependency
    
    async def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process document - tightly coupled to implementations."""
        result = await self._do_processing(document)
        
        # Hard to test, hard to change
        await self.email_service.send_email(
            f"Document processed: {result['id']}",
            "user@example.com"
        )
        
        return result
```

### Validation Rules

#### Dependency Injection Patterns
- **Constructor injection** for required dependencies
- **Property injection** for optional dependencies
- **Interface injection** for multiple implementations
- **Factory injection** for complex object creation

#### Service Container Usage
```python
# ✅ Proper dependency injection
class ServiceContainer:
    """DI container for managing dependencies."""
    
    def __init__(self):
        self._services = {}
        self._factories = {}
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register singleton service."""
        self._services[name] = instance
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Register factory for service creation."""
        self._factories[name] = factory
    
    def get(self, name: str) -> Any:
        """Get service instance."""
        if name in self._services:
            return self._services[name]
        if name in self._factories:
            return self._factories[name]()
        raise KeyError(f"Service {name} not registered")

# Usage in high-level modules
class DocumentProcessingPipeline:
    """Pipeline using injected dependencies."""
    
    def __init__(self, container: ServiceContainer):
        self.llm_service = container.get("llm_service")
        self.storage_service = container.get("storage_service")
        self.notification_service = container.get("notification_service")
```

## Enforcement and Validation

### Automated Analysis
```python
# tools/solid_analyzer.py
class SOLIDAnalyzer:
    """Automated SOLID principle validation."""
    
    def analyze_single_responsibility(self, cls: type) -> List[str]:
        """Check SRP violations."""
        violations = []
        
        # Check method count
        if len([m for m in dir(cls) if not m.startswith('_')]) > 15:
            violations.append("Too many public methods")
        
        # Check class size
        if len(inspect.getsource(cls).split('\n')) > 300:
            violations.append("Class too large")
        
        return violations
    
    def analyze_interface_segregation(self, interface: type) -> List[str]:
        """Check ISP violations."""
        violations = []
        
        # Check interface size
        methods = [m for m in dir(interface) if not m.startswith('_')]
        if len(methods) > 5:
            violations.append("Interface has too many methods")
        
        return violations
```

### Code Review Checklist

#### SRP Checklist
- [ ] Class has single, clear responsibility
- [ ] Methods are cohesive and related
- [ ] Class size is manageable (< 300 lines)
- [ ] Changes occur for single reason

#### OCP Checklist  
- [ ] Uses interfaces/abstract classes
- [ ] Implements strategy pattern when needed
- [ ] Configuration-driven behavior
- [ ] No hardcoded type checks in business logic

#### LSP Checklist
- [ ] Subtypes maintain base class contracts
- [ ] Method signatures match exactly
- [ ] Return types are compatible
- [ ] Exceptions are not more specific

#### ISP Checklist
- [ ] Interfaces are small and focused
- [ ] Clients depend only on needed methods
- [ ] No fat interfaces with unused methods
- [ ] Role-based interface design

#### DIP Checklist
- [ ] High-level modules depend on abstractions
- [ ] Dependencies are injected, not created
- [ ] Uses DI container or factory pattern
- [ ] Easy to test with mock dependencies

## Best Practices Summary

1. **Design small, focused classes** with single responsibilities
2. **Use interfaces and abstractions** for extensibility
3. **Implement dependency injection** for loose coupling
4. **Create role-based interfaces** for different client needs
5. **Maintain substitution compatibility** in inheritance
6. **Prefer composition over inheritance** for flexibility
7. **Use strategy pattern** for algorithm variations
8. **Apply SOLID principles consistently** across the codebase

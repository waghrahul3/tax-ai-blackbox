---
description: Documentation generation workflow for Tax AI Agent including API docs, environment guides, and test coverage reports
---

# Generate Documentation Workflow

Comprehensive documentation generation workflow for Tax AI Agent project that creates and updates all project documentation from source code analysis.

## Usage

Run this workflow when you need to:
- Generate API documentation from FastAPI endpoints
- Update environment variable documentation
- Create test coverage reports
- Update README with latest project metrics
- Generate service architecture documentation
- Create developer onboarding guides

## Steps

### 1. Generate API Documentation

#### FastAPI OpenAPI Documentation
```bash
# Generate OpenAPI specification
curl -s http://127.0.0.1:8000/openapi.json > docs/api/openapi.json

# Generate HTML documentation
python -c "
import json
from fastapi.openapi.utils import get_openapi
from main import app

spec = get_openapi(
    title=app.title,
    version=app.version,
    description=app.description,
    routes=app.routes,
)

with open('docs/api/openapi.json', 'w') as f:
    json.dump(spec, f, indent=2)
"

# Generate ReDoc documentation
npx @redocly/cli build-docs docs/api/openapi.json --output docs/api/index.html
```

#### Endpoint Documentation
```bash
# Extract endpoint information
python - << 'EOF'
import json
import requests
from pathlib import Path

# Get OpenAPI spec
response = requests.get('http://127.0.0.1:8000/openapi.json')
spec = response.json()

# Generate endpoint documentation
docs = []
for path, methods in spec['paths'].items():
    for method, details in methods.items():
        docs.append({
            'path': path,
            'method': method.upper(),
            'summary': details.get('summary', ''),
            'description': details.get('description', ''),
            'parameters': details.get('parameters', []),
            'responses': details.get('responses', {})
        })

# Save documentation
Path('docs/api/endpoints.md').write_text('# API Endpoints\n\n')
for doc in docs:
    Path('docs/api/endpoints.md').write_text(
        f"## {doc['method']} {doc['path']}\n\n"
        f"**Summary:** {doc['summary']}\n\n"
        f"**Description:** {doc['description']}\n\n"
        f"**Parameters:**\n"
    )
EOF
```

### 2. Update Environment Variable Documentation

#### Extract Environment Variables
```bash
# Generate environment documentation from .env.example
python - << 'EOF'
import re
from pathlib import Path

env_content = Path('.env.example').read_text()

# Parse environment variables
variables = []
current_section = None

for line in env_content.split('\n'):
    if line.startswith('# ==='):
        current_section = line.strip('# ').strip()
        continue
    
    if '=' in line and not line.startswith('#'):
        var_name = line.split('=')[0].strip()
        var_comment = ''
        
        # Look for comments above the variable
        lines = env_content.split('\n')
        var_index = lines.index(line)
        for i in range(var_index - 1, -1, -1):
            if lines[i].strip().startswith('#'):
                var_comment = lines[i].strip('# ').strip() + ' ' + var_comment
            else:
                break
        
        variables.append({
            'name': var_name,
            'section': current_section,
            'description': var_comment.strip(),
            'default': line.split('=')[1].strip() if '=' in line else ''
        })

# Generate markdown documentation
doc_content = ['# Environment Variables\n\n']
sections = {}
for var in variables:
    if var['section'] not in sections:
        sections[var['section']] = []
    sections[var['section']].append(var)

for section, vars in sections.items():
    doc_content.append(f'## {section}\n\n')
    for var in vars:
        doc_content.append(f'### `{var["name"]}`\n\n')
        doc_content.append(f'{var["description"]}\n\n')
        if var['default']:
            doc_content.append(f'**Default:** `{var["default"]}`\n\n')
        doc_content.append('---\n\n')

Path('docs/environment/variables.md').write_text(''.join(doc_content))
EOF
```

#### Validate Configuration
```bash
# Check for missing environment variables in code
python - << 'EOF'
import os
import re
from pathlib import Path

# Find all environment variable usage in code
env_vars = set()
for py_file in Path('.').rglob('*.py'):
    if 'venv' in str(py_file) or '.pytest_cache' in str(py_file):
        continue
    
    content = py_file.read_text()
    matches = re.findall(r'os\.getenv\(["\']([^"\']+)["\']', content)
    env_vars.update(matches)

# Compare with .env.example
env_example = Path('.env.example').read_text()
defined_vars = set(re.findall(r'^([A-Z_]+)=', env_example, re.MULTILINE))

missing_vars = env_vars - defined_vars
extra_vars = defined_vars - env_vars

print("Environment Variable Analysis:")
print(f"Variables used in code: {len(env_vars)}")
print(f"Variables defined in .env.example: {len(defined_vars)}")

if missing_vars:
    print(f"\nMissing in .env.example: {missing_vars}")
if extra_vars:
    print(f"Extra in .env.example: {extra_vars}")
EOF
```

### 3. Generate Test Coverage Reports

#### Coverage Analysis
```bash
# Run tests with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=xml --cov-report=term

# Generate coverage summary
python - << 'EOF'
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Parse coverage XML
coverage_xml = Path('coverage.xml')
if coverage_xml.exists():
    tree = ET.parse(coverage_xml)
    root = tree.getroot()
    
    # Extract coverage data
    coverage_data = {}
    for package in root.findall('.//package'):
        package_name = package.get('name')
        total_lines = 0
        covered_lines = 0
        
        for class_elem in package.findall('.//class'):
            lines = class_elem.find('lines')
            if lines is not None:
                for line in lines.findall('line'):
                    total_lines += 1
                    if line.get('hits') != '0':
                        covered_lines += 1
        
        if total_lines > 0:
            coverage_percent = (covered_lines / total_lines) * 100
            coverage_data[package_name] = {
                'coverage': round(coverage_percent, 2),
                'lines': total_lines,
                'covered': covered_lines
            }
    
    # Generate coverage report
    report = ['# Test Coverage Report\n\n']
    report.append(f"**Overall Coverage:** {coverage_data.get('.', {}).get('coverage', 0):.1f}%\n\n")
    report.append('## Module Coverage\n\n')
    
    for module, data in sorted(coverage_data.items()):
        if module != '.':
            report.append(f"### {module}\n\n")
            report.append(f"- **Coverage:** {data['coverage']:.1f}%\n")
            report.append(f"- **Lines:** {data['covered']}/{data['lines']}\n\n")
    
    Path('docs/testing/coverage.md').write_text(''.join(report))
    print("Coverage report generated: docs/testing/coverage.md")
else:
    print("No coverage.xml found. Run tests with coverage first.")
EOF
```

#### Test Documentation
```bash
# Generate test documentation
python - << 'EOF'
import ast
import inspect
from pathlib import Path
from typing import Dict, List

def extract_test_info(test_file: Path) -> Dict[str, List[str]]:
    """Extract test information from a test file."""
    test_info = {
        'unit_tests': [],
        'integration_tests': [],
        'async_tests': []
    }
    
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                # Check for markers in docstring
                docstring = ast.get_docstring(node) or ''
                
                if 'unit' in docstring.lower() or 'unit' in node.name.lower():
                    test_info['unit_tests'].append(node.name)
                elif 'integration' in docstring.lower() or 'integration' in node.name.lower():
                    test_info['integration_tests'].append(node.name)
                
                # Check for async
                if any(isinstance(n, ast.Await) for n in ast.walk(node)):
                    test_info['async_tests'].append(node.name)
    
    except Exception as e:
        print(f"Error parsing {test_file}: {e}")
    
    return test_info

# Generate test documentation
test_files = list(Path('tests').glob('test_*.py'))
all_test_info = {'unit_tests': [], 'integration_tests': [], 'async_tests': []}

for test_file in test_files:
    test_info = extract_test_info(test_file)
    for category, tests in test_info.items():
        all_test_info[category].extend(tests)

# Generate documentation
doc_content = ['# Test Documentation\n\n']
doc_content.append(f"Total Test Files: {len(test_files)}\n\n")

for category, tests in all_test_info.items():
    doc_content.append(f"## {category.replace('_', ' ').title()}\n\n")
    doc_content.append(f"Total: {len(tests)} tests\n\n")
    
    for test in sorted(tests):
        doc_content.append(f"- `{test}`\n")
    
    doc_content.append('\n')

Path('docs/testing/tests.md').write_text(''.join(doc_content))
print("Test documentation generated: docs/testing/tests.md")
EOF
```

### 4. Generate Service Architecture Documentation

#### Service Dependency Analysis
```bash
# Generate service architecture documentation
python - << 'EOF'
import ast
import importlib.util
from pathlib import Path
from typing import Dict, Set

def analyze_service_dependencies(service_file: Path) -> Dict[str, Set[str]]:
    """Analyze dependencies of a service."""
    dependencies = set()
    service_name = service_file.stem.replace('_service', '')
    
    try:
        with open(service_file, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and ('services' in node.module or 'core' in node.module):
                    for alias in node.names:
                        dependencies.add(alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if 'services' in alias.name or 'core' in alias.name:
                        dependencies.add(alias.name)
    
    except Exception as e:
        print(f"Error analyzing {service_file}: {e}")
    
    return {service_name: dependencies}

# Analyze all services
services_dir = Path('services')
service_files = list(services_dir.glob('*_service.py'))

all_dependencies = {}
for service_file in service_files:
    deps = analyze_service_dependencies(service_file)
    all_dependencies.update(deps)

# Generate architecture documentation
doc_content = ['# Service Architecture\n\n']
doc_content.append('## Service Dependencies\n\n')

for service, deps in sorted(all_dependencies.items()):
    doc_content.append(f"### {service.title()} Service\n\n")
    if deps:
        doc_content.append("**Dependencies:**\n\n")
        for dep in sorted(deps):
            doc_content.append(f"- `{dep}`\n")
    else:
        doc_content.append("**Dependencies:** None\n")
    doc_content.append('\n')

# Generate dependency graph in Mermaid
doc_content.append('## Dependency Graph\n\n')
doc_content.append('```mermaid\n')
doc_content.append('graph TD\n')

for service, deps in sorted(all_dependencies.items()):
    for dep in deps:
        dep_service = dep.replace('Service', '').lower()
        doc_content.append(f'    {service.lower()} --> {dep_service}\n')

doc_content.append('```\n\n')

Path('docs/architecture/services.md').write_text(''.join(doc_content))
print("Service architecture documentation generated: docs/architecture/services.md")
EOF
```

### 5. Update README with Project Metrics

#### Generate Project Statistics
```bash
# Generate project metrics and update README
python - << 'EOF'
import os
import subprocess
from pathlib import Path

def count_lines_of_code(directory: Path) -> Dict[str, int]:
    """Count lines of code in directory."""
    stats = {'total': 0, 'python': 0, 'tests': 0}
    
    for py_file in directory.rglob('*.py'):
        if 'venv' in str(py_file) or '.pytest_cache' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r') as f:
                lines = len([l for l in f.readlines() if l.strip() and not l.strip().startswith('#')])
                stats['total'] += lines
                
                if 'tests' in str(py_file):
                    stats['tests'] += lines
                else:
                    stats['python'] += lines
        except:
            pass
    
    return stats

def get_git_stats():
    """Get git repository statistics."""
    try:
        total_commits = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD'], 
                                            stderr=subprocess.DEVNULL).decode().strip()
        contributors = subprocess.check_output(['git', 'shortlog', '-sn'], 
                                           stderr=subprocess.DEVNULL).decode().strip()
        return {'commits': total_commits, 'contributors': len(contributors.split('\n'))}
    except:
        return {'commits': 'Unknown', 'contributors': 'Unknown'}

# Calculate metrics
loc_stats = count_lines_of_code(Path('.'))
git_stats = get_git_stats()

# Generate metrics section
metrics = f"""
## Project Metrics

- **Lines of Code:** {loc_stats['total']:,}
  - Application Code: {loc_stats['python']:,}
  - Test Code: {loc_stats['tests']:,}
- **Test Coverage:** {loc_stats['tests'] / max(loc_stats['python'], 1) * 100:.1f}%
- **Git Commits:** {git_stats['commits']}
- **Contributors:** {git_stats['contributors']}
- **Python Version:** 3.11+
- **Framework:** FastAPI + LangChain
- **LLM Provider:** Anthropic Claude

"""

# Update README
readme_path = Path('README.md')
if readme_path.exists():
    readme_content = readme_path.read_text()
    
    # Replace or add metrics section
    if '## Project Metrics' in readme_content:
        # Replace existing metrics
        start = readme_content.find('## Project Metrics')
        end = readme_content.find('\n## ', start + 1)
        if end == -1:
            end = len(readme_content)
        readme_content = readme_content[:start] + metrics + readme_content[end:]
    else:
        # Add metrics before License section
        license_pos = readme_content.find('## License')
        if license_pos != -1:
            readme_content = readme_content[:license_pos] + metrics + '\n' + readme_content[license_pos:]
        else:
            readme_content += metrics
    
    readme_path.write_text(readme_content)
    print("README.md updated with project metrics")
else:
    print("README.md not found")
EOF
```

### 6. Generate Developer Onboarding Guide

#### Create Setup Documentation
```bash
# Generate developer setup guide
python - << 'EOF'
from pathlib import Path

setup_guide = '''# Developer Setup Guide

## Quick Start

### Prerequisites
- Python 3.11+
- Git
- Anthropic API key

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TaxAIAgent
   ```

2. **Create virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your ANTHROPIC_API_KEY
   ```

5. **Run the application**
   ```bash
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

### Development Workflow

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

#### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy core/ services/ api/

# Linting
flake8 core/ services/ api/
```

#### Documentation
```bash
# Generate API documentation
# Start server first, then:
curl http://127.0.0.1:8000/docs

# Generate full documentation
# Use Windsurf workflow: /generate-docs
```

## Project Structure

```
TaxAIAgent/
├── api/                    # FastAPI routes and endpoints
├── core/                   # Core configuration and utilities
├── services/               # Business logic services
├── engine/                 # Document processing pipeline
├── strategies/             # Processing strategies
├── utils/                  # Utility functions
├── exceptions/             # Custom exceptions
├── storage/                # Storage implementations
├── models/                 # Data models
├── tests/                  # Test suite
├── frontend/               # Static UI files
├── docs/                   # Generated documentation
├── output/                 # Generated output files
└── logs/                   # Application logs
```

## Key Services

### Document Processing
- `DocumentProcessingService`: Main document processing logic
- `LLMService`: LLM integration and communication
- `OutputGenerationService`: Output format handling

### File Handling
- `FileValidationService`: File format and size validation
- `PDFProcessingService`: PDF-specific processing
- `UploadService`: File upload handling

### Configuration
- `TemplateService`: Prompt template management
- `ServiceContainer`: Dependency injection container

## Development Tips

### Adding New Features
1. Create service in `services/` directory
2. Add tests in `tests/` directory
3. Register service in `service_container.py`
4. Add API endpoint if needed in `api/routes.py`

### Testing
- Write unit tests for all new services
- Write integration tests for API endpoints
- Use appropriate pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`)

### Code Standards
- Follow PEP 8 (use Black formatter)
- Add type hints to all functions
- Write comprehensive docstrings
- Handle exceptions properly

## Common Issues

### Environment Setup
- Ensure Python 3.11+ is used
- Virtual environment must be activated
- ANTHROPIC_API_KEY must be set in .env

### Running Tests
- Some tests require actual API keys
- Integration tests may need test files
- Use `-m "not slow"` to skip time-consuming tests

### LLM Integration
- Check API key configuration
- Monitor rate limits
- Handle API errors gracefully

## Getting Help

- Check existing documentation in `docs/`
- Review test files for usage examples
- Look at service implementations for patterns
- Use Windsurf workflows for common tasks
'''

Path('docs/development/setup.md').write_text(setup_guide)
print("Developer setup guide generated: docs/development/setup.md")
EOF
```

### 7. Create Documentation Index

#### Generate Documentation Navigation
```bash
# Create comprehensive documentation index
python - << 'EOF'
from pathlib import Path

def generate_doc_index():
    """Generate main documentation index."""
    
    index_content = '''# Tax AI Agent Documentation

## Overview

This documentation provides comprehensive information about the Tax AI Agent project, including API documentation, development guides, and operational procedures.

## Documentation Sections

### 📚 API Documentation
- [API Endpoints](api/endpoints.md) - Complete API reference
- [OpenAPI Specification](api/openapi.json) - Raw OpenAPI spec
- [Interactive API Docs](http://127.0.0.1:8000/docs) - Swagger UI

### ⚙️ Configuration
- [Environment Variables](environment/variables.md) - Complete configuration reference
- [Model Configuration](MODEL_CONFIG.md) - LLM model settings
- [Password PDF Support](PASSWORD_PDF_SUPPORT.md) - PDF handling

### 🏗️ Architecture
- [Service Architecture](architecture/services.md) - Service dependencies and design
- [Project Structure](README.md#project-structure) - Directory layout
- [Data Flow](architecture/data_flow.md) - Processing pipeline

### 🧪 Testing
- [Test Coverage](testing/coverage.md) - Coverage reports and analysis
- [Test Documentation](testing/tests.md) - Test suite documentation
- [Test Summary](TEST_SUMMARY_PASSWORD_PDF.md) - Feature testing summaries

### 👨‍💻 Development
- [Developer Setup](development/setup.md) - Getting started guide
- [Code Standards](../.windsurf/rules/python-standards.md) - Python coding standards
- [SOLID Principles](../.windsurf/rules/solid-principles.md) - Design principles

### 🔧 Operations
- [Environment Variables](ENVIRONMENT_VARIABLES.md) - Configuration guide
- [Deployment Guide](development/deployment.md) - Production deployment
- [Troubleshooting](README.md#troubleshooting) - Common issues and solutions

## Quick Links

### For Developers
- [Setup Guide](development/setup.md) - Get started in 5 minutes
- [Run Tests](../.windsurf/workflows/run-tests.md) - Testing workflow
- [Code Analysis](../.windsurf/workflows/code-analysis.md) - Quality checks

### For API Users
- [API Endpoints](api/endpoints.md) - Complete API reference
- [Interactive Documentation](http://127.0.0.1:8000/docs) - Try the API
- [Environment Setup](environment/variables.md) - Configuration

### For Operations
- [Environment Configuration](ENVIRONMENT_VARIABLES.md) - Production setup
- [Troubleshooting](README.md#troubleshooting) - Common issues
- [Test Coverage](testing/coverage.md) - Quality metrics

## Documentation Maintenance

This documentation is automatically generated using the [Generate Documentation workflow](../.windsurf/workflows/generate-docs.md).

To update documentation:
1. Run the workflow: `/generate-docs`
2. Review generated files in `docs/` directory
3. Commit changes to repository

## Last Updated

*Automatically updated when documentation generation workflow is run.*
'''

    Path('docs/README.md').write_text(index_content)
    print("Documentation index generated: docs/README.md")

generate_doc_index()
EOF
```

## Expected Outputs

### Generated Documentation Structure
```
docs/
├── README.md                    # Main documentation index
├── api/
│   ├── openapi.json            # OpenAPI specification
│   ├── endpoints.md           # Endpoint documentation
│   └── index.html             # ReDoc HTML documentation
├── environment/
│   └── variables.md           # Environment variables reference
├── architecture/
│   └── services.md            # Service architecture documentation
├── testing/
│   ├── coverage.md            # Test coverage reports
│   └── tests.md              # Test documentation
└── development/
    ├── setup.md               # Developer setup guide
    └── deployment.md          # Deployment instructions
```

### Updated Files
- `README.md` - Updated with project metrics
- `ENVIRONMENT_VARIABLES.md` - Synchronized with .env.example
- `MODEL_CONFIG.md` - Updated with latest model configurations

## Integration with Development Workflow

### Automated Updates
```bash
# Pre-commit hook for documentation updates
#!/bin/sh
# .git/hooks/pre-commit
python -m pytest tests/ --cov=. --cov-report=xml
python -c "import docs.generate_docs; docs.generate_docs.update_metrics()"
```

### CI/CD Integration
```yaml
# .github/workflows/docs.yml
name: Generate Documentation
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Generate documentation
        run: python -m docs.generate_docs
      - name: Deploy documentation
        run: # Deploy to GitHub Pages or similar
```

## Best Practices

1. **Run documentation generation** before releases
2. **Keep API documentation current** with code changes
3. **Update environment docs** when adding new configuration
4. **Maintain test coverage** above 80%
5. **Review generated docs** for accuracy
6. **Commit documentation changes** with code changes
7. **Use interactive API docs** for testing endpoints

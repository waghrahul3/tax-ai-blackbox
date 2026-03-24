---
description: Comprehensive test automation for Tax AI Agent with pytest, coverage, and performance analysis
---

# Run Tests Workflow

Comprehensive test execution workflow for the Tax AI Agent project that runs all test suites, generates coverage reports, and analyzes performance.

## Usage

Run this workflow when you need to:
- Execute all tests before committing changes
- Generate coverage reports for code quality analysis
- Run specific test categories (unit, integration, slow)
- Validate test performance and identify bottlenecks
- Ensure all test markers are properly configured

## Steps

### 1. Run All Tests with Coverage
```bash
# Run complete test suite with coverage
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Run with specific markers
pytest tests/ -m "unit" -v --cov=core --cov=services --cov-report=html
pytest tests/ -m "integration" -v --cov=api --cov=engine
pytest tests/ -m "not slow" -v  # Skip slow tests for quick feedback
```

### 2. Parallel Test Execution
```bash
# Run tests in parallel for faster execution
pytest tests/ -n auto -v --cov=. --cov-report=html

# Run specific test files in parallel
pytest tests/test_services.py tests/test_config.py -n auto -v
```

### 3. Performance Analysis
```bash
# Run tests with performance profiling
pytest tests/ --profile --profile-svg

# Identify slowest tests
pytest tests/ --durations=10

# Run with memory profiling
pytest tests/ --memprof-top
```

### 4. Test Categories Execution

#### Unit Tests
```bash
# Run only unit tests
pytest tests/ -m "unit" -v --cov=core --cov=services --cov=utils

# Specific unit test classes
pytest tests/test_services.py::TestLLMService -v
pytest tests/test_config.py::TestConfiguration -v
```

#### Integration Tests
```bash
# Run only integration tests
pytest tests/ -m "integration" -v --cov=api --cov=engine

# Specific integration test scenarios
pytest tests/test_integration_simple.py -v
pytest tests/test_integration_password_pdf.py -v
```

#### Async Tests
```bash
# Run async-specific tests
pytest tests/ -m "asyncio" -v

# Test async service methods specifically
pytest tests/test_services.py::TestLLMService::test_async_llm_call -v
```

### 5. Coverage Analysis
```bash
# Generate detailed HTML coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=xml

# Coverage for specific modules
pytest tests/ --cov=services.llm_service --cov=core.config --cov-report=term-missing

# Minimum coverage enforcement
pytest tests/ --cov=. --cov-fail-under=80 --cov-report=term-missing
```

### 6. Test Environment Validation
```bash
# Validate test configuration
pytest --collect-only  # Check if all tests can be collected

# Verify test markers
pytest --markers

# Check test discovery
pytest tests/ --collect-only -q
```

### 7. Continuous Integration Mode
```bash
# CI-friendly test execution (minimal output, exit on first failure)
pytest tests/ -x --tb=short --cov=. --cov-report=xml

# JUnit XML output for CI systems
pytest tests/ --junit-xml=test-results.xml --cov=. --cov-report=xml
```

## Test Categories

### Unit Tests (`-m "unit"`)
- Test individual service methods in isolation
- Mock external dependencies (LLM calls, file I/O)
- Fast execution, suitable for every commit
- Coverage: Core business logic, utilities, configurations

### Integration Tests (`-m "integration"`)
- Test service interactions and API endpoints
- Use real file systems and test databases
- Medium execution time
- Coverage: API routes, document processing pipeline

### Slow Tests (`-m "slow"`)
- Comprehensive end-to-end scenarios
- Real LLM API calls (when configured)
- Long execution time, run before releases
- Coverage: Full document processing workflows

### Async Tests (`-m "asyncio"`)
- Test async/await patterns
- Validate concurrent processing
- Medium execution time
- Coverage: Async service methods, parallel processing

## Configuration Files

### pytest.ini (Already Configured)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    asyncio: marks tests as async
```

## Expected Outputs

### Success Indicators
- All tests pass with appropriate coverage
- Coverage report shows >80% for critical modules
- Performance metrics within acceptable ranges
- No test discovery or collection errors

### Artifacts Generated
- `htmlcov/index.html` - Detailed coverage report
- `coverage.xml` - CI-compatible coverage data
- `test-results.xml` - JUnit test results
- `profile.svg` - Performance profiling data

## Troubleshooting

### Common Issues
- **Import Errors**: Ensure virtual environment is activated
- **Coverage Failures**: Check `.gitignore` doesn't exclude source files
- **Async Test Failures**: Verify `pytest-asyncio` is installed
- **Marker Warnings**: Use `--strict-markers` to catch undefined markers

### Performance Issues
- Use `-n auto` for parallel execution
- Exclude slow tests during development: `-m "not slow"`
- Run specific test files instead of entire suite
- Consider test database cleanup strategies

## Integration with Development Workflow

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
pytest tests/ -m "unit" -x --cov=core --cov=services --cov-fail-under=70
```

### Development Commands
```bash
# Quick feedback during development
pytest tests/ -m "unit" -x

# Full test suite before pushing
pytest tests/ -v --cov=. --cov-report=html

# Specific feature testing
pytest tests/test_services.py::TestOutputGenerationService -v
```

## Best Practices

1. **Run unit tests frequently** - Every commit
2. **Run integration tests** - Before pull requests
3. **Run full suite with coverage** - Before releases
4. **Use markers appropriately** - Categorize tests correctly
5. **Maintain coverage thresholds** - Keep critical modules well-covered
6. **Monitor test performance** - Identify and optimize slow tests

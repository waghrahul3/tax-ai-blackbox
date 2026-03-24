---
description: Deployment readiness validation workflow for Tax AI Agent including environment checks, service health, and performance testing
---

# Deployment Check Workflow

Comprehensive deployment readiness validation workflow for Tax AI Agent project that ensures environment configuration, service health, performance benchmarks, and operational readiness before production deployment.

## Usage

Run this workflow when you need to:
- Validate environment configuration before deployment
- Check service health endpoints and dependencies
- Verify file upload/download functionality
- Test performance benchmarks
- Ensure production readiness
- Validate monitoring and logging setup

## Steps

### 1. Environment Configuration Validation

#### Environment Variables Check
```bash
# Validate all required environment variables
python - << 'EOF'
import os
from pathlib import Path
from typing import Dict, List, Set

def validate_environment():
    """Validate environment configuration for deployment."""
    
    # Required environment variables
    required_vars = {
        'ANTHROPIC_API_KEY': {
            'description': 'Anthropic Claude API key',
            'validation': lambda x: x and x.startswith('sk-ant-'),
            'critical': True
        },
        'ANTHROPIC_MODEL': {
            'description': 'Anthropic model to use',
            'validation': lambda x: x and x.startswith('claude-'),
            'critical': False,
            'default': 'claude-3-5-sonnet-20241022'
        },
        'APP_VERSION': {
            'description': 'Application version',
            'validation': lambda x: x and len(x) > 0,
            'critical': False,
            'default': '0.0.0'
        },
        'LOG_LEVEL': {
            'description': 'Logging level',
            'validation': lambda x: x in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'critical': False,
            'default': 'INFO'
        },
        'ENVIRONMENT': {
            'description': 'Deployment environment',
            'validation': lambda x: x in ['development', 'staging', 'production'],
            'critical': False,
            'default': 'development'
        }
    }
    
    # Optional but recommended variables
    optional_vars = {
        'MAX_FILE_SIZE_MB': {
            'description': 'Maximum file upload size',
            'validation': lambda x: x and x.isdigit() and int(x) > 0,
            'default': '50'
        },
        'ENABLE_CHUNKING': {
            'description': 'Enable text chunking',
            'validation': lambda x: x in ['true', 'false'],
            'default': 'true'
        },
        'ENABLE_LLM_SUMMARIZATION': {
            'description': 'Enable LLM summarization',
            'validation': lambda x: x in ['true', 'false'],
            'default': 'true'
        },
        'OUTPUT_DIRECTORY': {
            'description': 'Output directory path',
            'validation': lambda x: x and len(x) > 0,
            'default': 'output'
        }
    }
    
    validation_results = {
        'critical_errors': [],
        'warnings': [],
        'missing_vars': [],
        'invalid_vars': [],
        'using_defaults': []
    }
    
    print("🔍 Validating environment configuration...")
    
    # Check required variables
    for var_name, config in required_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            if config['critical']:
                validation_results['critical_errors'].append(
                    f"Critical variable {var_name} is missing: {config['description']}"
                )
            else:
                validation_results['missing_vars'].append(var_name)
                if 'default' in config:
                    os.environ[var_name] = config['default']
                    validation_results['using_defaults'].append(f"{var_name}={config['default']}")
        else:
            if not config['validation'](value):
                validation_results['invalid_vars'].append(
                    f"Invalid value for {var_name}: '{value}' ({config['description']})"
                )
    
    # Check optional variables
    for var_name, config in optional_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            if 'default' in config:
                os.environ[var_name] = config['default']
                validation_results['using_defaults'].append(f"{var_name}={config['default']}")
        else:
            if not config['validation'](value):
                validation_results['warnings'].append(
                    f"Invalid optional variable {var_name}: '{value}' ({config['description']})"
                )
    
    # Generate report
    report = "# Environment Validation Report\n\n"
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if validation_results['critical_errors']:
        report += "## 🚨 Critical Errors\n\n"
        for error in validation_results['critical_errors']:
            report += f"- {error}\n"
        report += "\n"
    
    if validation_results['invalid_vars']:
        report += "## ❌ Invalid Variables\n\n"
        for invalid in validation_results['invalid_vars']:
            report += f"- {invalid}\n"
        report += "\n"
    
    if validation_results['warnings']:
        report += "## ⚠️ Warnings\n\n"
        for warning in validation_results['warnings']:
            report += f"- {warning}\n"
        report += "\n"
    
    if validation_results['missing_vars']:
        report += "## 📝 Missing Variables\n\n"
        for missing in validation_results['missing_vars']:
            report += f"- {missing}\n"
        report += "\n"
    
    if validation_results['using_defaults']:
        report += "## 🔧 Using Default Values\n\n"
        for default in validation_results['using_defaults']:
            report += f"- {default}\n"
        report += "\n"
    
    if not any(validation_results.values()):
        report += "✅ **All environment variables are properly configured**\n\n"
    
    # Environment-specific checks
    env = os.getenv('ENVIRONMENT', 'development')
    report += f"## Environment: {env.upper()}\n\n"
    
    if env == 'production':
        # Production-specific validations
        production_checks = []
        
        if os.getenv('LOG_LEVEL') == 'DEBUG':
            production_checks.append("DEBUG logging enabled in production")
        
        if not os.getenv('ENABLE_RATE_LIMITING') == 'true':
            production_checks.append("Rate limiting not enabled")
        
        if production_checks:
            report += "### Production Security Warnings\n\n"
            for check in production_checks:
                report += f"- ⚠️ {check}\n"
            report += "\n"
    
    report += "## Configuration Summary\n\n"
    report += f"- **Total Variables Checked:** {len(required_vars) + len(optional_vars)}\n"
    report += f"- **Critical Errors:** {len(validation_results['critical_errors'])}\n"
    report += f"- **Warnings:** {len(validation_results['warnings'])}\n"
    report += f"- **Missing Variables:** {len(validation_results['missing_vars'])}\n"
    report += f"- **Using Defaults:** {len(validation_results['using_defaults'])}\n\n"
    
    Path('reports/environment-validation.md').write_text(report)
    print("Environment validation report generated")
    
    return len(validation_results['critical_errors']) == 0

# Run environment validation
is_valid = validate_environment()
if not is_valid:
    print("❌ Environment validation failed - critical errors found")
    exit(1)
else:
    print("✅ Environment validation passed")
EOF
```

#### Directory and Permissions Check
```bash
# Validate directory structure and permissions
python - << 'EOF'
import os
import stat
from pathlib import Path

def validate_directories():
    """Validate directory structure and permissions."""
    
    required_dirs = [
        'output',      # Generated output files
        'logs',        # Application logs
        'uploads',     # Temporary upload directory
        'temp'         # Temporary files
    ]
    
    required_files = [
        '.env',        # Environment configuration
        'main.py',     # Application entry point
        'requirements.txt'  # Dependencies
    ]
    
    validation_results = {
        'missing_dirs': [],
        'permission_issues': [],
        'missing_files': [],
        'created_dirs': []
    }
    
    print("📁 Validating directory structure...")
    
    # Check and create required directories
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                validation_results['created_dirs'].append(str(dir_path))
                print(f"✅ Created directory: {dir_path}")
            except Exception as e:
                validation_results['missing_dirs'].append(f"{dir_name} (failed to create: {e})")
        else:
            # Check permissions
            try:
                # Test write permissions
                test_file = dir_path / '.write_test'
                test_file.touch()
                test_file.unlink()
                print(f"✅ Directory {dir_path} is writable")
            except Exception as e:
                validation_results['permission_issues'].append(f"{dir_name}: {e}")
    
    # Check required files
    for file_name in required_files:
        file_path = Path(file_name)
        
        if not file_path.exists():
            validation_results['missing_files'].append(file_name)
        else:
            # Check file permissions
            st = file_path.stat()
            mode = oct(st.st_mode)[-3:]
            if file_name == '.env' and mode != '600':
                validation_results['permission_issues'].append(f"{file_name}: insecure permissions ({mode})")
    
    # Generate report
    report = "# Directory Validation Report\n\n"
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if validation_results['missing_dirs']:
        report += "## 🚨 Missing Directories\n\n"
        for missing in validation_results['missing_dirs']:
            report += f"- {missing}\n"
        report += "\n"
    
    if validation_results['permission_issues']:
        report += "## ⚠️ Permission Issues\n\n"
        for issue in validation_results['permission_issues']:
            report += f"- {issue}\n"
        report += "\n"
    
    if validation_results['missing_files']:
        report += "## 📝 Missing Files\n\n"
        for missing in validation_results['missing_files']:
            report += f"- {missing}\n"
        report += "\n"
    
    if validation_results['created_dirs']:
        report += "## 🔧 Created Directories\n\n"
        for created in validation_results['created_dirs']:
            report += f"- {created}\n"
        report += "\n"
    
    if not any([validation_results['missing_dirs'], validation_results['permission_issues'], validation_results['missing_files']]):
        report += "✅ **Directory structure is properly configured**\n\n"
    
    # Disk space check
    import shutil
    total, used, free = shutil.disk_usage('.')
    
    report += "## Disk Space Analysis\n\n"
    report += f"- **Total Space:** {total // (1024**3):,} GB\n"
    report += f"- **Used Space:** {used // (1024**3):,} GB\n"
    report += f"- **Free Space:** {free // (1024**3):,} GB\n"
    report += f"- **Usage:** {(used/total)*100:.1f}%\n\n"
    
    if free < 1024**3:  # Less than 1GB free
        report += "⚠️ **Warning:** Low disk space detected\n\n"
    
    Path('reports/directory-validation.md').write_text(report)
    print("Directory validation report generated")
    
    return len(validation_results['missing_dirs']) == 0 and len(validation_results['missing_files']) == 0

# Run directory validation
is_valid = validate_directories()
if not is_valid:
    print("❌ Directory validation failed")
    exit(1)
else:
    print("✅ Directory validation passed")
EOF
```

### 2. Service Health Checks

#### Application Health Validation
```bash
# Start the application and run health checks
echo "🚀 Starting application for health checks..."

# Start the server in background
python -m uvicorn main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    
    echo "🔍 Checking endpoint: $endpoint"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000$endpoint")
    
    if [ "$response" -eq "$expected_status" ]; then
        echo "✅ $endpoint - $response"
        return 0
    else
        echo "❌ $endpoint - $response (expected $expected_status)"
        return 1
    fi
}

# Health check results
health_results=()

# Check basic health endpoint
if check_endpoint "/"; then
    health_results+=("basic_health:pass")
else
    health_results+=("basic_health:fail")
fi

# Check API documentation endpoint
if check_endpoint "/docs"; then
    health_results+=("docs:pass")
else
    health_results+=("docs:fail")
fi

# Check OpenAPI specification
if check_endpoint "/openapi.json"; then
    health_results+=("openapi:pass")
else
    health_results+=("openapi:fail")
fi

# Check templates endpoint
if check_endpoint "/ai/templates"; then
    health_results+=("templates:pass")
else
    health_results+=("templates:fail")
fi

# Check UI endpoint
if check_endpoint "/ui"; then
    health_results+=("ui:pass")
else
    health_results+=("ui:fail")
fi

# Generate health report
cat > reports/health-check.md << EOF
# Service Health Check Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**Server PID:** $SERVER_PID

## Endpoint Health Status

EOF

for result in "${health_results[@]}"; do
    endpoint=$(echo $result | cut -d: -f1)
    status=$(echo $result | cut -d: -f2)
    
    if [ "$status" = "pass" ]; then
        echo "✅ $endpoint: Healthy" >> reports/health-check.md
    else
        echo "❌ $endpoint: Unhealthy" >> reports/health-check.md
    fi
done

# Add detailed endpoint information
cat >> reports/health-check.md << EOF

## Detailed Endpoint Tests

### Basic Health Check
- **URL:** http://127.0.0.1:8000/
- **Purpose:** Basic application health
- **Status:** $(check_endpoint "/" && echo "✅ PASS" || echo "❌ FAIL")

### API Documentation
- **URL:** http://127.0.0.1:8000/docs
- **Purpose:** Swagger UI documentation
- **Status:** $(check_endpoint "/docs" && echo "✅ PASS" || echo "❌ FAIL")

### OpenAPI Specification
- **URL:** http://127.0.0.1:8000/openapi.json
- **Purpose:** API specification
- **Status:** $(check_endpoint "/openapi.json" && echo "✅ PASS" || echo "❌ FAIL")

### Templates Endpoint
- **URL:** http://127.0.0.1:8000/ai/templates
- **Purpose:** Available prompt templates
- **Status:** $(check_endpoint "/ai/templates" && echo "✅ PASS" || echo "❌ FAIL")

### Chat UI
- **URL:** http://127.0.0.1:8000/ui
- **Purpose:** Web interface
- **Status:** $(check_endpoint "/ui" && echo "✅ PASS" || echo "❌ FAIL")

## Service Dependencies

### LLM Service Test
EOF

# Test LLM service connectivity
python - << 'EOF' >> reports/health-check.md
import os
import asyncio
from services.llm_service import LLMService

async def test_llm_service():
    """Test LLM service connectivity."""
    try:
        llm_service = LLMService()
        result = await llm_service.generate("Test message", temperature=0.0)
        print("✅ LLM Service: Connected and responsive")
        return True
    except Exception as e:
        print(f"❌ LLM Service: {e}")
        return False

# Run test
success = asyncio.run(test_llm_service())
EOF

cat >> reports/health-check.md << EOF

### File System Test
EOF

# Test file system operations
python - << 'EOF' >> reports/health-check.md
import os
import tempfile
from pathlib import Path

def test_file_operations():
    """Test file system operations."""
    try:
        # Test write operation
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name
        
        # Test read operation
        with open(temp_path, 'r') as f:
            content = f.read()
        
        # Cleanup
        os.unlink(temp_path)
        
        if content == "test content":
            print("✅ File System: Read/write operations working")
            return True
        else:
            print("❌ File System: Content mismatch")
            return False
    except Exception as e:
        print(f"❌ File System: {e}")
        return False

# Run test
success = test_file_operations()
EOF

# Cleanup
kill $SERVER_PID 2>/dev/null

echo "Health check completed: reports/health-check.md"
```

#### Database and Storage Validation
```bash
# Validate storage and database connectivity
python - << 'EOF'
import os
import tempfile
import asyncio
from pathlib import Path
from services.storage_service import StorageService
from services.upload_service import persist_uploads

def validate_storage():
    """Validate storage service functionality."""
    
    storage_results = {
        'file_write': False,
        'file_read': False,
        'file_delete': False,
        'directory_ops': False,
        'upload_service': False
    }
    
    print("💾 Validating storage functionality...")
    
    # Test file operations
    try:
        # Test write
        test_content = b"Storage test content"
        test_file = Path("output") / "storage_test.txt"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        storage_results['file_write'] = True
        print("✅ File write: Success")
        
        # Test read
        with open(test_file, 'rb') as f:
            read_content = f.read()
        
        if read_content == test_content:
            storage_results['file_read'] = True
            print("✅ File read: Success")
        
        # Test delete
        test_file.unlink()
        storage_results['file_delete'] = True
        print("✅ File delete: Success")
        
    except Exception as e:
        print(f"❌ File operations failed: {e}")
    
    # Test directory operations
    try:
        test_dir = Path("output") / "test_dir"
        test_dir.mkdir(exist_ok=True)
        
        if test_dir.exists() and test_dir.is_dir():
            storage_results['directory_ops'] = True
            print("✅ Directory operations: Success")
        
        # Cleanup
        test_dir.rmdir()
        
    except Exception as e:
        print(f"❌ Directory operations failed: {e}")
    
    # Test upload service
    try:
        from services.upload_service import generate_request_id, persist_uploads
        
        # Test request ID generation
        request_id = generate_request_id()
        if request_id and len(request_id) > 0:
            print("✅ Request ID generation: Success")
        
        storage_results['upload_service'] = True
        
    except Exception as e:
        print(f"❌ Upload service test failed: {e}")
    
    # Generate report
    report = "# Storage Validation Report\n\n"
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    report += "## Storage Tests\n\n"
    
    test_names = {
        'file_write': 'File Write Operations',
        'file_read': 'File Read Operations',
        'file_delete': 'File Delete Operations',
        'directory_ops': 'Directory Operations',
        'upload_service': 'Upload Service'
    }
    
    for test_key, test_name in test_names.items():
        status = "✅ PASS" if storage_results[test_key] else "❌ FAIL"
        report += f"- **{test_name}:** {status}\n"
    
    report += "\n## Storage Configuration\n\n"
    
    # Check storage configuration
    output_dir = Path("output")
    if output_dir.exists():
        report += f"- **Output Directory:** {output_dir.absolute()}\n"
        report += f"- **Writable:** {os.access(output_dir, os.W_OK)}\n"
        report += f"- **Readable:** {os.access(output_dir, os.R_OK)}\n"
        
        # Count existing files
        try:
            file_count = len(list(output_dir.rglob("*")))
            report += f"- **Existing Files:** {file_count}\n"
        except:
            report += f"- **Existing Files:** Unable to count\n"
    else:
        report += "- **Output Directory:** Not found\n"
    
    # Disk space analysis
    import shutil
    total, used, free = shutil.disk_usage(str(output_dir))
    
    report += "\n## Disk Space\n\n"
    report += f"- **Total:** {total // (1024**3):,} GB\n"
    report += f"- **Used:** {used // (1024**3):,} GB\n"
    report += f"- **Free:** {free // (1024**3):,} GB\n"
    report += f"- **Available for Output:** {free // (1024**2):,} MB\n"
    
    Path('reports/storage-validation.md').write_text(report)
    print("Storage validation report generated")
    
    return all(storage_results.values())

# Run storage validation
is_valid = validate_storage()
if not is_valid:
    print("❌ Storage validation failed")
    exit(1)
else:
    print("✅ Storage validation passed")
EOF
```

### 3. Functionality Testing

#### File Upload/Download Testing
```bash
# Test file upload and download functionality
python - << 'EOF'
import os
import tempfile
import requests
import json
from pathlib import Path

def create_test_files():
    """Create test files for upload testing."""
    
    test_files = []
    
    # Create test PDF content (simplified)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    
    # Create test image content (simplified PNG)
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82"
    
    # Create test CSV content
    csv_content = b"Name,Amount,Date\nTest User,1000,2024-01-01\nAnother User,2000,2024-01-02\n"
    
    test_files = [
        ('test.pdf', pdf_content, 'application/pdf'),
        ('test.png', png_content, 'image/png'),
        ('test.csv', csv_content, 'text/csv')
    ]
    
    return test_files

def test_file_upload():
    """Test file upload functionality."""
    
    print("📤 Testing file upload functionality...")
    
    # Start server in background
    import subprocess
    import time
    
    server_process = subprocess.Popen(
        ['python', '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        test_files = create_test_files()
        upload_results = []
        
        for filename, content, content_type in test_files:
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                # Test upload
                with open(temp_file_path, 'rb') as f:
                    files = {'files': (filename, f, content_type)}
                    data = {
                        'prompt': 'Extract all information from this test file',
                        'template_name': None,
                        'ctid': f'test_{filename}'
                    }
                    
                    response = requests.post(
                        'http://127.0.0.1:8000/ai/process',
                        files=files,
                        data=data,
                        timeout=30
                    )
                
                # Cleanup
                os.unlink(temp_file_path)
                
                if response.status_code == 200:
                    result = response.json()
                    upload_results.append({
                        'file': filename,
                        'status': 'success',
                        'response': result
                    })
                    print(f"✅ {filename}: Upload successful")
                else:
                    upload_results.append({
                        'file': filename,
                        'status': 'failed',
                        'error': response.text,
                        'status_code': response.status_code
                    })
                    print(f"❌ {filename}: Upload failed ({response.status_code})")
            
            except Exception as e:
                upload_results.append({
                    'file': filename,
                    'status': 'error',
                    'error': str(e)
                })
                print(f"❌ {filename}: Error - {e}")
        
        # Test download functionality
        print("📥 Testing file download functionality...")
        download_results = []
        
        for result in upload_results:
            if result['status'] == 'success':
                try:
                    response_data = result['response']
                    if 'download_url' in response_data:
                        download_url = response_data['download_url']
                        
                        # Test download
                        download_response = requests.get(
                            f'http://127.0.0.1:8000{download_url}',
                            timeout=10
                        )
                        
                        if download_response.status_code == 200:
                            download_results.append({
                                'file': result['file'],
                                'status': 'success',
                                'size': len(download_response.content)
                            })
                            print(f"✅ {result['file']}: Download successful")
                        else:
                            download_results.append({
                                'file': result['file'],
                                'status': 'failed',
                                'error': download_response.text
                            })
                            print(f"❌ {result['file']}: Download failed")
                    else:
                        download_results.append({
                            'file': result['file'],
                            'status': 'no_url',
                            'error': 'No download URL in response'
                        })
                
                except Exception as e:
                    download_results.append({
                        'file': result['file'],
                        'status': 'error',
                        'error': str(e)
                    })
                    print(f"❌ {result['file']}: Download error - {e}")
        
        # Generate report
        report = "# File Upload/Download Test Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "## Upload Tests\n\n"
        for result in upload_results:
            status_icon = "✅" if result['status'] == 'success' else "❌"
            report += f"{status_icon} **{result['file']}:** {result['status'].upper()}\n"
            if result['status'] != 'success':
                report += f"   Error: {result.get('error', 'Unknown')}\n"
        report += "\n"
        
        report += "## Download Tests\n\n"
        for result in download_results:
            status_icon = "✅" if result['status'] == 'success' else "❌"
            report += f"{status_icon} **{result['file']}:** {result['status'].upper()}\n"
            if result['status'] == 'success':
                report += f"   Size: {result['size']} bytes\n"
            else:
                report += f"   Error: {result.get('error', 'Unknown')}\n"
        report += "\n"
        
        # Summary
        upload_success = len([r for r in upload_results if r['status'] == 'success'])
        download_success = len([r for r in download_results if r['status'] == 'success'])
        
        report += "## Summary\n\n"
        report += f"- **Upload Success Rate:** {upload_success}/{len(upload_results)} ({upload_success/len(upload_results)*100:.1f}%)\n"
        report += f"- **Download Success Rate:** {download_success}/{len(download_results)} ({download_success/len(download_results)*100:.1f}%)\n"
        
        Path('reports/file-functionality-test.md').write_text(report)
        print("File functionality test report generated")
        
        return upload_success > 0 and download_success > 0
    
    finally:
        # Cleanup server
        server_process.terminate()
        server_process.wait()

# Run functionality tests
is_valid = test_file_upload()
if not is_valid:
    print("❌ File functionality tests failed")
    exit(1)
else:
    print("✅ File functionality tests passed")
EOF
```

### 4. Performance Benchmarking

#### Load Testing and Performance Metrics
```bash
# Run performance benchmarks
python - << 'EOF'
import time
import asyncio
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def performance_test():
    """Run performance benchmarks."""
    
    print("⚡ Running performance benchmarks...")
    
    # Start server
    import subprocess
    server_process = subprocess.Popen(
        ['python', '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(5)  # Wait for server
    
    try:
        performance_results = {}
        
        # Test 1: Basic endpoint response time
        print("🏃 Testing basic endpoint performance...")
        response_times = []
        
        for i in range(10):
            start_time = time.time()
            response = requests.get('http://127.0.0.1:8000/', timeout=5)
            end_time = time.time()
            
            if response.status_code == 200:
                response_times.append(end_time - start_time)
        
        if response_times:
            performance_results['basic_endpoint'] = {
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'median_response_time': statistics.median(response_times),
                'requests_tested': len(response_times)
            }
            print(f"✅ Basic endpoint: {statistics.mean(response_times):.3f}s avg")
        
        # Test 2: Templates endpoint performance
        print("📋 Testing templates endpoint performance...")
        template_response_times = []
        
        for i in range(5):
            start_time = time.time()
            response = requests.get('http://127.0.0.1:8000/ai/templates', timeout=5)
            end_time = time.time()
            
            if response.status_code == 200:
                template_response_times.append(end_time - start_time)
        
        if template_response_times:
            performance_results['templates_endpoint'] = {
                'avg_response_time': statistics.mean(template_response_times),
                'requests_tested': len(template_response_times)
            }
            print(f"✅ Templates endpoint: {statistics.mean(template_response_times):.3f}s avg")
        
        # Test 3: Concurrent requests
        print("🔄 Testing concurrent request handling...")
        concurrent_results = []
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.get('http://127.0.0.1:8000/', timeout=5)
                end_time = time.time()
                return {
                    'success': response.status_code == 200,
                    'response_time': end_time - start_time
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            concurrent_results = [future.result() for future in futures]
        
        successful_requests = [r for r in concurrent_results if r['success']]
        failed_requests = [r for r in concurrent_results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            performance_results['concurrent_requests'] = {
                'total_requests': len(concurrent_results),
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'success_rate': len(successful_requests) / len(concurrent_results) * 100,
                'avg_response_time': statistics.mean(response_times) if response_times else 0
            }
            print(f"✅ Concurrent: {len(successful_requests)}/{len(concurrent_results)} successful")
        
        # Test 4: Memory usage (basic check)
        print("💾 Checking memory usage...")
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        performance_results['memory_usage'] = {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }
        print(f"✅ Memory: {memory_info.rss / 1024 / 1024:.1f} MB RSS")
        
        # Generate performance report
        report = "# Performance Benchmark Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Basic endpoint performance
        if 'basic_endpoint' in performance_results:
            basic = performance_results['basic_endpoint']
            report += "## Basic Endpoint Performance\n\n"
            report += f"- **Average Response Time:** {basic['avg_response_time']:.3f}s\n"
            report += f"- **Minimum Response Time:** {basic['min_response_time']:.3f}s\n"
            report += f"- **Maximum Response Time:** {basic['max_response_time']:.3f}s\n"
            report += f"- **Median Response Time:** {basic['median_response_time']:.3f}s\n"
            report += f"- **Requests Tested:** {basic['requests_tested']}\n\n"
        
        # Templates endpoint performance
        if 'templates_endpoint' in performance_results:
            templates = performance_results['templates_endpoint']
            report += "## Templates Endpoint Performance\n\n"
            report += f"- **Average Response Time:** {templates['avg_response_time']:.3f}s\n"
            report += f"- **Requests Tested:** {templates['requests_tested']}\n\n"
        
        # Concurrent request performance
        if 'concurrent_requests' in performance_results:
            concurrent = performance_results['concurrent_requests']
            report += "## Concurrent Request Performance\n\n"
            report += f"- **Total Requests:** {concurrent['total_requests']}\n"
            report += f"- **Successful Requests:** {concurrent['successful_requests']}\n"
            report += f"- **Failed Requests:** {concurrent['failed_requests']}\n"
            report += f"- **Success Rate:** {concurrent['success_rate']:.1f}%\n"
            report += f"- **Average Response Time:** {concurrent['avg_response_time']:.3f}s\n\n"
        
        # Memory usage
        if 'memory_usage' in performance_results:
            memory = performance_results['memory_usage']
            report += "## Memory Usage\n\n"
            report += f"- **RSS Memory:** {memory['rss_mb']:.1f} MB\n"
            report += f"- **VMS Memory:** {memory['vms_mb']:.1f} MB\n"
            report += f"- **Memory Percent:** {memory['percent']:.1f}%\n\n"
        
        # Performance recommendations
        report += "## Performance Recommendations\n\n"
        
        if 'basic_endpoint' in performance_results:
            avg_time = performance_results['basic_endpoint']['avg_response_time']
            if avg_time > 0.5:
                report += "- ⚠️ **Basic endpoint response time is high** (>0.5s)\n"
            else:
                report += "- ✅ **Basic endpoint response time is acceptable**\n"
        
        if 'concurrent_requests' in performance_results:
            success_rate = performance_results['concurrent_requests']['success_rate']
            if success_rate < 95:
                report += "- ⚠️ **Concurrent request success rate is low** (<95%)\n"
            else:
                report += "- ✅ **Concurrent request handling is good**\n"
        
        if 'memory_usage' in performance_results:
            memory_mb = performance_results['memory_usage']['rss_mb']
            if memory_mb > 500:
                report += "- ⚠️ **Memory usage is high** (>500MB)\n"
            else:
                report += "- ✅ **Memory usage is reasonable**\n"
        
        Path('reports/performance-benchmark.md').write_text(report)
        print("Performance benchmark report generated")
        
        return True
    
    finally:
        server_process.terminate()
        server_process.wait()

# Run performance tests
is_valid = performance_test()
if not is_valid:
    print("❌ Performance benchmarks failed")
    exit(1)
else:
    print("✅ Performance benchmarks completed")
EOF
```

### 5. Generate Deployment Summary

#### Comprehensive Deployment Report
```bash
# Generate comprehensive deployment summary
python - << 'EOF'
import json
from pathlib import Path
from datetime import datetime

def generate_deployment_summary():
    """Generate comprehensive deployment summary."""
    
    summary = f"""# Deployment Readiness Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report provides a comprehensive assessment of the Tax AI Agent deployment readiness, including environment validation, service health, functionality testing, and performance benchmarks.

## Deployment Status: [STATUS]

### ✅ Passed Checks
- [List of passed checks]

### ❌ Failed Checks  
- [List of failed checks]

### ⚠️ Warnings
- [List of warnings]

## Detailed Results

### 1. Environment Configuration
**Status:** [PASS/FAIL]

**Critical Variables:**
- ANTHROPIC_API_KEY: [Status]
- Required variables configured: [Count]/[Total]

**Configuration Issues:**
- [List of any issues]

**Recommendations:**
- [List of recommendations]

### 2. Service Health
**Status:** [PASS/FAIL]

**Endpoint Health:**
- Basic Health (/): [Status]
- API Documentation (/docs): [Status]
- OpenAPI Spec (/openapi.json): [Status]
- Templates (/ai/templates): [Status]
- Web UI (/ui): [Status]

**Service Dependencies:**
- LLM Service: [Status]
- File System: [Status]
- Storage Service: [Status]

### 3. Functionality Testing
**Status:** [PASS/FAIL]

**File Upload Tests:**
- PDF Upload: [Status]
- Image Upload: [Status]
- CSV Upload: [Status]
- Overall Success Rate: [Percentage]%

**File Download Tests:**
- Download Functionality: [Status]
- File Integrity: [Status]

### 4. Performance Benchmarks
**Status:** [PASS/FAIL]

**Response Times:**
- Basic Endpoint: [Time]s
- Templates Endpoint: [Time]s

**Concurrent Handling:**
- Success Rate: [Percentage]%
- Average Response Time: [Time]s

**Memory Usage:**
- RSS Memory: [MB]
- Memory Percent: [Percentage]%

### 5. Security Validation
**Status:** [PASS/FAIL]

**Security Checks:**
- Environment Variables: [Status]
- File Permissions: [Status]
- API Security: [Status]

## Deployment Checklist

### Pre-deployment Requirements
- [ ] All critical environment variables configured
- [ ] Service health checks passing
- [ ] File functionality tests passing
- [ ] Performance benchmarks acceptable
- [ ] Security validation complete

### Production Readiness
- [ ] Environment set to 'production'
- [ ] DEBUG logging disabled
- [ ] Rate limiting enabled
- [ ] SSL/TLS configured
- [ ] Monitoring enabled
- [ ] Backup procedures in place

### Post-deployment Verification
- [ ] All endpoints responding
- [ ] File uploads working
- [ ] LLM service connected
- [ ] Monitoring active
- [ ] Logs being generated

## Risk Assessment

### High Risk Items
- [List of high-risk items]

### Medium Risk Items
- [List of medium-risk items]

### Low Risk Items
- [List of low-risk items]

## Recommendations

### Immediate Actions (Pre-deployment)
1. [Action 1]
2. [Action 2]
3. [Action 3]

### Post-deployment Monitoring
1. [Monitor 1]
2. [Monitor 2]
3. [Monitor 3]

### Long-term Improvements
1. [Improvement 1]
2. [Improvement 2]
3. [Improvement 3]

## Deployment Decision

**Recommendation:** [DEPLOY/HOLD]

**Reasoning:** [Explanation for recommendation]

**Next Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

---

*This summary was generated automatically using the Deployment Check workflow.*
"""

    # Read individual reports to populate summary
    report_files = {
        'environment': 'reports/environment-validation.md',
        'directory': 'reports/directory-validation.md',
        'health': 'reports/health-check.md',
        'storage': 'reports/storage-validation.md',
        'functionality': 'reports/file-functionality-test.md',
        'performance': 'reports/performance-benchmark.md'
    }
    
    # Simple status checking (would be more sophisticated in production)
    status = "READY FOR DEPLOYMENT"
    passed_checks = []
    failed_checks = []
    warnings = []
    
    for report_type, report_file in report_files.items():
        if Path(report_file).exists():
            content = Path(report_file).read_text()
            if "✅" in content and "❌" not in content:
                passed_checks.append(f"{report_type.title()} validation")
            elif "❌" in content:
                failed_checks.append(f"{report_type.title()} validation")
            else:
                warnings.append(f"{report_type.title()} validation needs review")
        else:
            failed_checks.append(f"{report_type.title()} report missing")
    
    # Update summary with actual results
    summary = summary.replace("[STATUS]", "FAILED" if failed_checks else "PASSED")
    summary = summary.replace("[List of passed checks]", "\n- ".join([""] + passed_checks) if passed_checks else "None")
    summary = summary.replace("[List of failed checks]", "\n- ".join([""] + failed_checks) if failed_checks else "None")
    summary = summary.replace("[List of warnings]", "\n- ".join([""] + warnings) if warnings else "None")
    summary = summary.replace("[DEPLOY/HOLD]", "HOLD" if failed_checks else "DEPLOY")
    summary = summary.replace("[Explanation for recommendation]", 
                            "Critical issues found that must be resolved before deployment" if failed_checks else
                            "All checks passed - ready for deployment")
    
    Path('reports/deployment-summary.md').write_text(summary)
    print("Deployment summary generated: reports/deployment-summary.md")
    
    return len(failed_checks) == 0

# Generate deployment summary
is_ready = generate_deployment_summary()
if not is_ready:
    print("❌ Deployment checks failed - not ready for deployment")
    exit(1)
else:
    print("✅ Deployment checks passed - ready for deployment")
EOF
```

## Expected Outputs

### Generated Deployment Reports
```
reports/
├── environment-validation.md       # Environment configuration validation
├── directory-validation.md         # Directory structure and permissions
├── health-check.md                 # Service health endpoint tests
├── storage-validation.md           # Storage service functionality
├── file-functionality-test.md      # File upload/download tests
├── performance-benchmark.md        # Performance metrics and benchmarks
└── deployment-summary.md          # Comprehensive deployment readiness
```

## Integration with CI/CD Pipeline

### Pre-deployment Gate
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deployment-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run deployment checks
        run: |
          chmod +x .windsurf/workflows/deployment-check.md
          # Extract and run deployment check commands
          mkdir -p reports
          python -c "
# Run all deployment validation steps
exec(open('.windsurf/workflows/deployment-check.md').read())
"
      
      - name: Upload deployment reports
        uses: actions/upload-artifact@v2
        with:
          name: deployment-reports
          path: reports/
      
      - name: Deploy if ready
        if: success()
        run: echo "Deploying to production..."
```

## Deployment Best Practices

1. **Run all checks before deployment** - Never skip validation
2. **Fix critical issues immediately** - Don't deploy with known problems
3. **Monitor performance continuously** - Set up alerts for degradation
4. **Have rollback plan** - Always know how to revert
5. **Document deployment process** - Maintain runbooks
6. **Test in staging first** - Validate before production
7. **Monitor post-deployment** - Watch for issues after rollout

## Environment-Specific Considerations

### Development Environment
- ✅ Debug logging enabled
- ✅ Relaxed security settings
- ✅ Hot reload enabled
- ⚠️ Not suitable for production

### Staging Environment
- ✅ Production-like configuration
- ✅ Full security enabled
- ✅ Performance monitoring
- ✅ Final testing before production

### Production Environment
- ✅ All security measures enabled
- ✅ Performance optimized
- ✅ Monitoring and alerting
- ✅ Backup and recovery procedures

## Troubleshooting

### Common Deployment Issues
1. **Environment variables missing** - Check .env configuration
2. **File permissions denied** - Verify directory permissions
3. **Service won't start** - Check logs and dependencies
4. **Uploads failing** - Verify storage configuration
5. **Performance degraded** - Check resource utilization

### Debugging Steps
1. Check individual validation reports
2. Review application logs
3. Verify environment configuration
4. Test functionality manually
5. Monitor system resources

This comprehensive deployment check workflow ensures that the Tax AI Agent is fully validated and ready for production deployment across all critical dimensions.

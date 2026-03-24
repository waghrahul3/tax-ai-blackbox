---
description: Security vulnerability scanning and compliance validation workflow for Tax AI Agent project
---

# Security Scan Workflow

Comprehensive security scanning workflow for Tax AI Agent project that identifies vulnerabilities, validates security practices, and ensures compliance with security best practices.

## Usage

Run this workflow when you need to:
- Scan for security vulnerabilities in dependencies
- Validate secure coding practices
- Check for hardcoded secrets and credentials
- Analyze API security configurations
- Validate input sanitization and validation
- Ensure compliance with security standards

## Steps

### 1. Dependency Vulnerability Scanning

#### Safety Check for Known Vulnerabilities
```bash
# Install safety for dependency vulnerability checking
pip install safety

# Run comprehensive dependency scan
safety check --json --output reports/safety-report.json
safety check --html --output reports/safety-report.html

# Check specific severity levels
safety check --severity high --output reports/safety-high.json
safety check --severity medium --output reports/safety-medium.json
safety check --severity low --output reports/safety-low.json

# Check with custom ignore rules (if necessary)
safety check --ignore 51657 --ignore 51658 --output reports/safety-ignored.json

# Check development dependencies
safety check --development --json --output reports/safety-dev.json

# Generate summary report
python - << 'EOF'
import json
from pathlib import Path

def generate_safety_summary():
    """Generate safety vulnerability summary."""
    
    reports = {
        'all': 'reports/safety-report.json',
        'high': 'reports/safety-high.json',
        'medium': 'reports/safety-medium.json',
        'low': 'reports/safety-low.json'
    }
    
    summary = "# Dependency Security Scan Report\n\n"
    summary += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    total_vulnerabilities = 0
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for severity, report_file in reports.items():
        if Path(report_file).exists():
            with open(report_file, 'r') as f:
                data = json.load(f)
                vulns = data.get('vulnerabilities', [])
                total_vulnerabilities += len(vulns)
                
                if severity != 'all':
                    severity_counts[severity] = len(vulns)
    
    summary += "## Summary\n\n"
    summary += f"- **Total Vulnerabilities:** {total_vulnerabilities}\n"
    summary += f"- **High Severity:** {severity_counts['high']}\n"
    summary += f"- **Medium Severity:** {severity_counts['medium']}\n"
    summary += f"- **Low Severity:** {severity_counts['low']}\n\n"
    
    if total_vulnerabilities > 0:
        summary += "## Recommendations\n\n"
        if severity_counts['high'] > 0:
            summary += "🚨 **IMMEDIATE ACTION REQUIRED:** Update high-severity dependencies\n\n"
        if severity_counts['medium'] > 0:
            summary += "⚠️ **PLAN UPGRADES:** Address medium-severity vulnerabilities\n\n"
        if severity_counts['low'] > 0:
            summary += "📝 **MONITOR:** Review low-severity issues\n\n"
    else:
        summary += "✅ **No vulnerabilities found**\n\n"
    
    Path('reports/security-dependency-summary.md').write_text(summary)
    print("Dependency security summary generated")

generate_safety_summary()
EOF
```

#### Pip Audit for Package Security
```bash
# Install pip-audit for additional vulnerability scanning
pip install pip-audit

# Run pip-audit on requirements
pip-audit -r requirements.txt --format=json --output reports/pip-audit-report.json
pip-audit -r requirements.txt --format=html --output reports/pip-audit-report.html

# Check for vulnerable packages in current environment
pip-audit --format=json --output reports/pip-audit-env.json

# Generate vulnerability fix suggestions
pip-audit -r requirements.txt --fix --dry-run --output reports/pip-audit-fixes.txt
```

### 2. Code Security Analysis

#### Bandit Security Scanner
```bash
# Install bandit with additional plugins
pip install bandit bandit-sarif-formatter

# Run comprehensive security scan
bandit -r . \
  -f json \
  -o reports/bandit-report.json \
  --exclude=venv/,tests/,__pycache__/,output/ \
  --severity-level all

# Generate HTML report
bandit -r . \
  -f html \
  -o reports/bandit-report.html \
  --exclude=venv/,tests/,__pycache__/,output/

# Check specific security test suites
bandit -r . \
  --tests B101,B102,B103,B104,B105,B106,B107,B108,B110,B112 \
  -f json \
  -o reports/bandit-critical.json \
  --exclude=venv/,tests/,__pycache__/,output/

# Generate SARIF format for GitHub integration
bandit -r . \
  -f sarif \
  -o reports/bandit-report.sarif \
  --exclude=venv/,tests/,__pycache__/,output/

# Check specific severity levels
bandit -r . --severity-level high -f json -o reports/bandit-high.json
bandit -r . --severity-level medium -f json -o reports/bandit-medium.json
bandit -r . --severity-level low -f json -o reports/bandit-low.json
```

#### Semgrep Static Analysis
```bash
# Install semgrep for advanced security pattern detection
pip install semgrep

# Run OWASP Top 10 rules
semgrep --config=auto \
  --config=p/security-audit \
  --config=p/owasp-top-ten \
  --exclude=venv/ \
  --exclude=tests/ \
  --json \
  --output=reports/semgrep-report.json \
  .

# Generate HTML report
semgrep --config=auto \
  --config=p/security-audit \
  --exclude=venv/ \
  --exclude=tests/ \
  --html \
  --output=reports/semgrep-report.html \
  .

# Check specific security categories
semgrep --config=p/owasp-top-ten.a1 \
  --json --output=reports/semgrep-injection.json \
  .

semgrep --config=p/owasp-top-ten.a2 \
  --json --output=reports/semgrep-auth.json \
  .

semgrep --config=p/owasp-top-ten.a3 \
  --json --output=reports/semgrep-injection.xml \
  .
```

### 3. Secrets and Credentials Detection

#### TruffleHog for Secrets Scanning
```bash
# Install trufflehog for secrets detection
pip install trufflehog

# Scan repository for secrets
trufflehog filesystem . \
  --json \
  --output=reports/trufflehog-report.json

# Generate human-readable report
trufflehog filesystem . \
  --output=reports/trufflehog-report.txt

# Scan specific directories
trufflehog filesystem core/ services/ api/ \
  --json \
  --output=reports/trufflehog-code.json

# Check git history for secrets
trufflehog git . \
  --json \
  --output=reports/trufflehog-git.json
```

#### GitLeaks for Repository Secrets
```bash
# Install gitleaks
# (Download from https://github.com/zricethezav/gitleaks/releases)

# Run gitleaks scan
gitleaks detect \
  --source . \
  --report-path reports/gitleaks-report.json \
  --report-format json

# Generate summary report
gitleaks detect \
  --source . \
  --report-path reports/gitleaks-summary.txt \
  --report-format summary

# Check specific file types
gitleaks detect \
  --source . \
  --config-path=.gitleaks.toml \
  --report-path reports/gitleaks-custom.json \
  --report-format json
```

### 4. Custom Security Pattern Analysis

#### Python Security Pattern Scanner
```bash
# Run comprehensive Python security analysis
python - << 'EOF'
import ast
import re
from pathlib import Path
from typing import Dict, List, Set

class PythonSecurityAnalyzer:
    """Comprehensive Python security analyzer."""
    
    def __init__(self):
        self.issues = []
        self.security_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'execute\s*\(\s*["\'].*\+.*["\']',
                r'execute\s*\(\s*f["\'].*{.*}.*["\']'
            ],
            'hardcoded_secrets': [
                r'(password|passwd|pwd|secret|key|token|api_key|auth)\s*=\s*["\'][^"\']+["\']',
                r'(password|passwd|pwd|secret|key|token|api_key|auth)\s*=\s*[a-zA-Z0-9]{20,}'
            ],
            'insecure_deserialization': [
                r'pickle\.loads?\s*\(',
                r'cPickle\.loads?\s*\(',
                r'dill\.loads?\s*\(',
                r'shelve\.open\s*\('
            ],
            'weak_cryptography': [
                r'\.md5\s*\(',
                r'\.sha1\s*\(',
                r'\.des\s*\(',
                r'\.rc4\s*\(',
                r'md5\s*\(',
                r'sha1\s*\('
            ],
            'file_operations': [
                r'open\s*\(\s*["\'][^"\']*["\']\s*,\s*["\'][wW]',
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(',
                r'eval\s*\(',
                r'exec\s*\('
            ],
            'network_security': [
                r'verify\s*=\s*False',
                r'ssl\.create_default_context\s*\(\s*\)',
                r'urllib\.request\.urlopen\s*\(',
                r'requests\.get\s*\([^,]*,?\s*verify\s*=\s*False'
            ]
        }
    
    def check_sql_injection(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Check for SQL injection vulnerabilities."""
        for pattern in self.security_patterns['sql_injection']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append({
                    'file': file_path,
                    'type': 'SQL Injection',
                    'line': line_num,
                    'issue': 'Potential SQL injection with string formatting',
                    'code': match.group(),
                    'severity': 'HIGH',
                    'cwe': 'CWE-89'
                })
        
        # AST-based detection
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr in ['execute', 'executemany', 'query']):
                    for arg in node.args:
                        if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                            line_num = getattr(node, 'lineno', 0)
                            self.issues.append({
                                'file': file_path,
                                'type': 'SQL Injection',
                                'line': line_num,
                                'issue': f'Potential SQL injection with {type(arg).__name__}',
                                'severity': 'HIGH',
                                'cwe': 'CWE-89'
                            })
    
    def check_hardcoded_secrets(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Check for hardcoded secrets and credentials."""
        for pattern in self.security_patterns['hardcoded_secrets']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append({
                    'file': file_path,
                    'type': 'Hardcoded Secret',
                    'line': line_num,
                    'issue': f'Hardcoded {match.group(1)} detected',
                    'code': match.group(),
                    'severity': 'HIGH',
                    'cwe': 'CWE-798'
                })
        
        # AST-based detection
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(secret in var_name for secret in 
                               ['password', 'secret', 'key', 'token', 'api_key', 'auth']):
                            if isinstance(node.value, (ast.Str, ast.Constant)):
                                value = node.value.value if hasattr(node.value, 'value') else node.value.s
                                if value and len(str(value)) > 10:  # Exclude short placeholders
                                    line_num = getattr(node, 'lineno', 0)
                                    self.issues.append({
                                        'file': file_path,
                                        'type': 'Hardcoded Secret',
                                        'line': line_num,
                                        'issue': f'Hardcoded {var_name} detected',
                                        'severity': 'HIGH',
                                        'cwe': 'CWE-798'
                                    })
    
    def check_insecure_deserialization(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Check for insecure deserialization."""
        for pattern in self.security_patterns['insecure_deserialization']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append({
                    'file': file_path,
                    'type': 'Insecure Deserialization',
                    'line': line_num,
                    'issue': f'Use of insecure {match.group().split(".")[0]} module',
                    'code': match.group(),
                    'severity': 'MEDIUM',
                    'cwe': 'CWE-502'
                })
    
    def check_weak_cryptography(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Check for weak cryptographic algorithms."""
        for pattern in self.security_patterns['weak_cryptography']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append({
                    'file': file_path,
                    'type': 'Weak Cryptography',
                    'line': line_num,
                    'issue': f'Use of weak algorithm: {match.group()}',
                    'code': match.group(),
                    'severity': 'MEDIUM',
                    'cwe': 'CWE-327'
                })
    
    def check_file_operations(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Check for insecure file operations."""
        for pattern in self.security_patterns['file_operations']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                severity = 'HIGH' if 'eval' in match.group() or 'exec' in match.group() else 'MEDIUM'
                self.issues.append({
                    'file': file_path,
                    'type': 'Insecure File Operation',
                    'line': line_num,
                    'issue': f'Potentially insecure operation: {match.group()}',
                    'code': match.group(),
                    'severity': severity,
                    'cwe': 'CWE-78' if 'eval' in match.group() else 'CWE-22'
                })
    
    def check_network_security(self, tree: ast.AST, file_path: str, content: str) -> None:
        """Check for network security issues."""
        for pattern in self.security_patterns['network_security']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.issues.append({
                    'file': file_path,
                    'type': 'Network Security Issue',
                    'line': line_num,
                    'issue': f'Network security issue: {match.group()}',
                    'code': match.group(),
                    'severity': 'MEDIUM',
                    'cwe': 'CWE-295'
                })
    
    def check_input_validation(self, tree: ast.AST, file_path: str) -> None:
        """Check for missing input validation."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function handles external input
                has_file_params = any(
                    (isinstance(param.annotation, ast.Name) and 
                     'UploadFile' in str(param.annotation.id))
                    for param in node.args.args
                )
                
                if has_file_params:
                    # Check for validation
                    has_validation = any(
                        (isinstance(stmt, ast.Raise) or
                         (isinstance(stmt, ast.If) and 
                          any(isinstance(child, ast.Raise) for child in ast.walk(stmt))))
                        for stmt in node.body
                    )
                    
                    if not has_validation:
                        self.issues.append({
                            'file': file_path,
                            'type': 'Missing Input Validation',
                            'line': getattr(node, 'lineno', 0),
                            'issue': f'Function {node.name} handles file uploads without validation',
                            'severity': 'MEDIUM',
                            'cwe': 'CWE-20'
                        })
    
    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            self.check_sql_injection(tree, str(file_path), content)
            self.check_hardcoded_secrets(tree, str(file_path), content)
            self.check_insecure_deserialization(tree, str(file_path), content)
            self.check_weak_cryptography(tree, str(file_path), content)
            self.check_file_operations(tree, str(file_path), content)
            self.check_network_security(tree, str(file_path), content)
            self.check_input_validation(tree, str(file_path))
        
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def generate_report(self) -> str:
        """Generate comprehensive security analysis report."""
        report = "# Python Security Analysis Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Group by severity
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        medium_issues = [i for i in self.issues if i['severity'] == 'MEDIUM']
        low_issues = [i for i in self.issues if i['severity'] == 'LOW']
        
        report += "## Summary\n\n"
        report += f"- **High Severity:** {len(high_issues)}\n"
        report += f"- **Medium Severity:** {len(medium_issues)}\n"
        report += f"- **Low Severity:** {len(low_issues)}\n"
        report += f"- **Total Issues:** {len(self.issues)}\n\n"
        
        # Group by type
        issues_by_type = {}
        for issue in self.issues:
            issue_type = issue['type']
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        report += "## Issues by Type\n\n"
        for issue_type, issues in sorted(issues_by_type.items()):
            report += f"### {issue_type} ({len(issues)})\n\n"
            for issue in issues[:5]:  # Show first 5 issues
                report += f"**File:** {issue['file']}:{issue['line']}\n"
                report += f"**Issue:** {issue['issue']}\n"
                if 'code' in issue:
                    report += f"**Code:** `{issue['code']}`\n"
                report += f"**CWE:** {issue.get('cwe', 'N/A')}\n\n"
            
            if len(issues) > 5:
                report += f"... and {len(issues) - 5} more\n\n"
        
        # Recommendations
        report += "## Recommendations\n\n"
        if high_issues:
            report += "### High Priority\n"
            report += "1. **Immediately address all high-severity issues**\n"
            report += "2. **Remove hardcoded secrets** and use environment variables\n"
            report += "3. **Fix SQL injection vulnerabilities** with parameterized queries\n"
            report += "4. **Replace insecure deserialization** with safe alternatives\n\n"
        
        if medium_issues:
            report += "### Medium Priority\n"
            report += "1. **Upgrade weak cryptographic algorithms** to stronger alternatives\n"
            report += "2. **Add input validation** for all external inputs\n"
            report += "3. **Fix network security issues** and enable SSL verification\n"
            report += "4. **Review file operations** for path traversal vulnerabilities\n\n"
        
        return report

# Run comprehensive Python security analysis
analyzer = PythonSecurityAnalyzer()

print("Analyzing Python files for security issues...")
for py_file in Path('.').rglob('*.py'):
    if 'venv' in str(py_file) or '.pytest_cache' in str(py_file):
        continue
    analyzer.analyze_file(py_file)

# Generate report
security_report = analyzer.generate_report()
Path('reports/python-security-analysis.md').write_text(security_report)
print("Python security analysis report generated: reports/python-security-analysis.md")

# Print summary
high_issues = len([i for i in analyzer.issues if i['severity'] == 'HIGH'])
medium_issues = len([i for i in analyzer.issues if i['severity'] == 'MEDIUM'])
low_issues = len([i for i in analyzer.issues if i['severity'] == 'LOW'])

print(f"\nSecurity Issues Summary:")
print(f"High: {high_issues}")
print(f"Medium: {medium_issues}")
print(f"Low: {low_issues}")
print(f"Total: {len(analyzer.issues)}")
EOF
```

### 5. API Security Configuration Analysis

#### FastAPI Security Configuration Check
```bash
# Analyze FastAPI security configurations
python - << 'EOF'
import ast
from pathlib import Path
from typing import Dict, List

def analyze_fastapi_security():
    """Analyze FastAPI security configurations."""
    
    security_config = {
        'cors_enabled': False,
        'rate_limiting': False,
        'security_headers': False,
        'oauth2_enabled': False,
        'api_key_auth': False,
        'input_validation': False,
        'error_handling': False
    }
    
    issues = []
    
    for py_file in Path('api').rglob('*.py'):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Check for CORS middleware
            if 'CORSMiddleware' in content:
                security_config['cors_enabled'] = True
            
            # Check for rate limiting
            if 'limiter' in content or 'rate_limit' in content:
                security_config['rate_limiting'] = True
            
            # Check for security headers
            if any(header in content for header in ['X-Content-Type-Options', 'X-Frame-Options']):
                security_config['security_headers'] = True
            
            # Check for authentication
            if any(auth in content for auth in ['OAuth2PasswordBearer', 'APIKeyHeader', 'security']):
                security_config['oauth2_enabled'] = True
            
            # Check for input validation
            if 'BaseModel' in content and 'Field' in content:
                security_config['input_validation'] = True
            
            # Check for error handling
            if 'HTTPException' in content or 'ValidationError' in content:
                security_config['error_handling'] = True
        
        except Exception as e:
            print(f"Error analyzing {py_file}: {e}")
    
    # Generate recommendations
    report = "# FastAPI Security Configuration Report\n\n"
    report += "## Security Features Status\n\n"
    
    for feature, enabled in security_config.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        report += f"- **{feature.replace('_', ' ').title()}:** {status}\n"
    
    report += "\n## Recommendations\n\n"
    
    if not security_config['cors_enabled']:
        report += "1. **Enable CORS middleware** with proper origins configuration\n"
    
    if not security_config['rate_limiting']:
        report += "2. **Implement rate limiting** to prevent abuse\n"
    
    if not security_config['security_headers']:
        report += "3. **Add security headers** middleware\n"
    
    if not security_config['oauth2_enabled']:
        report += "4. **Implement authentication** for sensitive endpoints\n"
    
    if not security_config['input_validation']:
        report += "5. **Add comprehensive input validation** using Pydantic models\n"
    
    if not security_config['error_handling']:
        report += "6. **Implement proper error handling** to avoid information leakage\n"
    
    Path('reports/fastapi-security-config.md').write_text(report)
    print("FastAPI security configuration report generated")

analyze_fastapi_security()
EOF
```

### 6. Environment Security Check

#### Environment Variable Security Analysis
```bash
# Analyze environment configuration for security issues
python - << 'EOF'
import os
import re
from pathlib import Path

def analyze_environment_security():
    """Analyze environment configuration security."""
    
    security_issues = []
    
    # Check .env.example for security guidance
    env_example_path = Path('.env.example')
    if env_example_path.exists():
        content = env_example_path.read_text()
        
        # Check for placeholder secrets
        if 'replace-with-your-' in content:
            security_issues.append({
                'type': 'Weak Secret Placeholders',
                'issue': 'Environment file uses weak placeholder patterns',
                'recommendation': 'Use more specific placeholder patterns'
            })
        
        # Check for default passwords
        if 'password' in content.lower() and ('admin' in content.lower() or 'default' in content.lower()):
            security_issues.append({
                'type': 'Default Passwords',
                'issue': 'Default passwords found in environment template',
                'recommendation': 'Remove default passwords from templates'
            })
    
    # Check actual .env file if it exists
    env_path = Path('.env')
    if env_path.exists():
        content = env_path.read_text()
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'ANTHROPIC_API_KEY=sk-ant-[^$\s]+',
            r'PASSWORD=[^$\s]+',
            r'SECRET=[^$\s]+',
            r'TOKEN=[^$\s]+'
        ]
        
        for pattern in secret_patterns:
            matches = re.findall(pattern, content)
            if matches:
                security_issues.append({
                    'type': 'Hardcoded Secrets',
                    'issue': f'Found {len(matches)} potential secrets in .env file',
                    'recommendation': 'Ensure .env is properly secured and not committed'
                })
    
    # Check file permissions
    if env_path.exists():
        stat = env_path.stat()
        mode = oct(stat.st_mode)[-3:]
        if mode != '600':
            security_issues.append({
                'type': 'File Permissions',
                'issue': f'.env file has insecure permissions ({mode})',
                'recommendation': 'Set permissions to 600 (read/write for owner only)'
            })
    
    # Generate report
    report = "# Environment Security Analysis Report\n\n"
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if security_issues:
        report += "## Security Issues Found\n\n"
        for i, issue in enumerate(security_issues, 1):
            report += f"### {i}. {issue['type']}\n\n"
            report += f"**Issue:** {issue['issue']}\n\n"
            report += f"**Recommendation:** {issue['recommendation']}\n\n"
    else:
        report += "✅ **No security issues found**\n\n"
    
    report += "## Security Best Practices\n\n"
    report += "1. **Never commit .env files** to version control\n"
    report += "2. **Use strong, unique secrets** for all API keys\n"
    report += "3. **Set file permissions** to 600 for .env files\n"
    report += "4. **Use environment-specific** configuration files\n"
    report += "5. **Rotate secrets regularly** and update documentation\n"
    report += "6. **Use secret management** services in production\n"
    
    Path('reports/environment-security.md').write_text(report)
    print("Environment security analysis report generated")

analyze_environment_security()
EOF
```

### 7. Generate Comprehensive Security Summary

#### Security Dashboard Report
```bash
# Generate comprehensive security summary
python - << 'EOF'
import json
from pathlib import Path
from datetime import datetime

def generate_security_dashboard():
    """Generate comprehensive security dashboard."""
    
    dashboard = f"""# Security Dashboard

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This dashboard provides a comprehensive overview of the Tax AI Agent project's security posture, including dependency vulnerabilities, code security issues, and configuration analysis.

## Security Metrics

### 🚨 Critical Issues
- **High Severity Vulnerabilities:** [Count from reports]
- **Hardcoded Secrets:** [Count from reports]
- **Dependency Vulnerabilities:** [Count from safety report]

### ⚠️ Medium Risk Issues
- **Medium Severity Vulnerabilities:** [Count from reports]
- **Configuration Issues:** [Count from reports]
- **Input Validation Gaps:** [Count from reports]

### 📊 Security Coverage
- **Dependencies Scanned:** [Count from requirements.txt]
- **Code Files Analyzed:** [Count of Python files]
- **Security Tests:** [Count of security-focused tests]

## Detailed Findings

### 1. Dependency Security
**Status:** [Status based on safety report]
**Total Vulnerabilities:** [Number]
- High: [Count]
- Medium: [Count]
- Low: [Count]

**Recommendations:**
- Update high-severity dependencies immediately
- Plan upgrades for medium-severity issues
- Monitor low-severity issues

### 2. Code Security
**Status:** [Status based on code analysis]
**Total Issues:** [Number]
- SQL Injection: [Count]
- Hardcoded Secrets: [Count]
- Insecure Deserialization: [Count]
- Weak Cryptography: [Count]

**Recommendations:**
- Fix all high-severity code issues
- Implement secure coding practices
- Add security-focused tests

### 3. API Security
**Status:** [Status based on FastAPI analysis]
**Security Features:**
- CORS: [Enabled/Disabled]
- Rate Limiting: [Enabled/Disabled]
- Authentication: [Enabled/Disabled]
- Input Validation: [Enabled/Disabled]

**Recommendations:**
- Enable missing security features
- Implement proper authentication
- Add comprehensive input validation

### 4. Environment Security
**Status:** [Status based on environment analysis]
**Issues Found:** [Count]
- File Permissions: [Issues]
- Hardcoded Secrets: [Issues]
- Weak Placeholders: [Issues]

**Recommendations:**
- Secure environment files
- Use proper secret management
- Update configuration templates

## Risk Assessment

### Overall Risk Level: [CALCULATED]
- **Critical:** [Issues count]
- **High:** [Issues count]
- **Medium:** [Issues count]
- **Low:** [Issues count]

### Risk Factors
1. **Dependency Vulnerabilities** - External library risks
2. **Code Security** - Implementation vulnerabilities
3. **Configuration Security** - Setup and deployment issues
4. **Data Exposure** - Potential data leaks

## Action Plan

### Immediate Actions (24-48 hours)
1. **Fix all high-severity vulnerabilities**
2. **Remove hardcoded secrets**
3. **Update vulnerable dependencies**
4. **Secure environment configuration**

### Short-term Actions (1-2 weeks)
1. **Implement missing security features**
2. **Add comprehensive input validation**
3. **Set up security monitoring**
4. **Create security testing suite**

### Long-term Actions (1-3 months)
1. **Implement security CI/CD pipeline**
2. **Regular security audits**
3. **Security training for team**
4. **Incident response procedures**

## Security Best Practices

### Development
- [ ] Code reviews include security checks
- [ ] Security testing in CI/CD pipeline
- [ ] Regular dependency updates
- [ ] Secret management implementation

### Deployment
- [ ] Environment-specific configurations
- [ ] Proper file permissions
- [ ] Security headers enabled
- [ ] Rate limiting configured

### Monitoring
- [ ] Security logging enabled
- [ ] Intrusion detection systems
- [ ] Regular vulnerability scans
- [ ] Security metrics dashboard

## Compliance Checklist

### OWASP Top 10
- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Authentication Failures
- [ ] A08: Software/Data Integrity Failures
- [ ] A09: Logging/Monitoring Failures
- [ ] A10: Server-Side Request Forgery

### Security Standards
- [ ] GDPR compliance
- [ ] SOC 2 controls
- [ ] ISO 27001 practices
- [ ] Industry-specific requirements

## Next Steps

1. **Review all security reports** in detail
2. **Create ticket backlog** for security issues
3. **Implement fixes** based on priority
4. **Set up regular scanning** schedule
5. **Monitor security metrics** continuously

---

*This dashboard was generated automatically using the Security Scan workflow.*
"""

    Path('reports/security-dashboard.md').write_text(dashboard)
    print("Security dashboard generated: reports/security-dashboard.md")

generate_security_dashboard()
EOF
```

## Expected Outputs

### Generated Security Reports
```
reports/
├── safety-report.html             # Dependency vulnerability report
├── safety-report.json            # Dependency vulnerability data
├── pip-audit-report.html         # Additional dependency analysis
├── pip-audit-report.json         # Pip audit data
├── bandit-report.html            # Code security analysis
├── bandit-report.json           # Bandit scan results
├── bandit-report.sarif          # SARIF format for GitHub
├── semgrep-report.html          # Advanced security pattern analysis
├── semgrep-report.json          # Semgrep scan results
├── trufflehog-report.json       # Secrets detection results
├── trufflehog-report.txt        # Human-readable secrets report
├── gitleaks-report.json         # Git history secrets scan
├── python-security-analysis.md   # Custom Python security analysis
├── fastapi-security-config.md    # API security configuration
├── environment-security.md       # Environment security analysis
└── security-dashboard.md         # Comprehensive security summary
```

## Integration with Development Workflow

### Pre-commit Security Checks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: bandit
        name: bandit
        entry: bandit
        language: system
        args: [-r, ., --exclude=venv,tests]
      
      - id: trufflehog
        name: trufflehog
        entry: trufflehog
        language: system
        args: [filesystem, ., --json, --output=.trufflehog-report.json]
      
      - id: safety
        name: safety
        entry: safety
        language: system
        args: [check, --json, --output=.safety-report.json]
```

### CI/CD Security Pipeline
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: pip install -r requirements.txt bandit safety trufflehog semgrep
      
      - name: Run security scans
        run: |
          mkdir -p reports
          bandit -r . -f json -o reports/bandit.json || true
          safety check --json --output reports/safety.json || true
          trufflehog filesystem . --json --output reports/trufflehog.json || true
          semgrep --config=auto --json --output reports/semgrep.json . || true
      
      - name: Upload security reports
        uses: actions/upload-artifact@v2
        with:
          name: security-reports
          path: reports/
```

## Security Best Practices

1. **Run security scans regularly** - At least weekly or before releases
2. **Fix high-severity issues immediately** - Don't delay critical fixes
3. **Never commit secrets** - Use proper secret management
4. **Keep dependencies updated** - Regularly scan and update
5. **Implement defense in depth** - Multiple security layers
6. **Monitor security metrics** - Track trends over time
7. **Educate the team** - Security awareness training
8. **Have incident response plan** - Prepare for security incidents

## Remediation Guidelines

### High Severity Issues
- **Action Required:** Fix within 24-48 hours
- **Examples:** Hardcoded secrets, SQL injection, insecure deserialization
- **Process:** Immediate fix, security review, deployment

### Medium Severity Issues
- **Action Required:** Fix within 1-2 weeks
- **Examples:** Weak cryptography, missing input validation
- **Process:** Schedule fix, implement, test, deploy

### Low Severity Issues
- **Action Required:** Fix within 1 month
- **Examples:** Code quality issues, minor configuration problems
- **Process:** Plan fix, implement during regular maintenance

## Compliance and Standards

### Security Frameworks
- **OWASP Top 10** - Web application security risks
- **CWE (Common Weakness Enumeration)** - Software weakness types
- **NIST Cybersecurity Framework** - Security best practices
- **ISO 27001** - Information security management

### Industry Standards
- **GDPR** - Data protection and privacy
- **SOC 2** - Security controls and procedures
- **PCI DSS** - Payment card industry standards (if applicable)
- **HIPAA** - Healthcare information security (if applicable)

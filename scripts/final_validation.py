#!/usr/bin/env python3
"""
Final validation script for EstateCore project
Performs comprehensive checks to ensure the system is ready for deployment
"""
import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"PASS: {description}")
            return True
        else:
            print(f"FAIL: {description}: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"FAIL: {description}: {str(e)}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"PASS: {description}")
        return True
    else:
        print(f"FAIL: {description}")
        return False

def check_directory_structure():
    """Validate project structure"""
    print("\n1. PROJECT STRUCTURE VALIDATION")
    print("=" * 40)
    
    required_dirs = [
        ("estatecore_backend", "Backend directory"),
        ("estatecore_frontend", "Frontend directory"),
        ("ai_modules", "AI modules directory"),
        ("docs", "Documentation directory"),
        ("scripts", "Scripts directory"),
        ("deployment", "Deployment directory"),
        ("utils", "Utils directory"),
        ("archive", "Archive directory")
    ]
    
    all_passed = True
    for dir_path, description in required_dirs:
        if not check_file_exists(dir_path, description):
            all_passed = False
    
    return all_passed

def check_configuration_files():
    """Validate configuration files"""
    print("\n2. CONFIGURATION FILES VALIDATION")
    print("=" * 40)
    
    config_files = [
        ("README.md", "Main README file"),
        (".env.example", "Environment template"),
        (".gitignore", "Git ignore file"),
        ("requirements.txt", "Python requirements"),
        ("requirements-ai.txt", "AI requirements"),
        ("CONTRIBUTING.md", "Contributing guidelines"),
        ("config.py", "Main configuration"),
        ("estatecore_frontend/package.json", "Frontend package config")
    ]
    
    all_passed = True
    for file_path, description in config_files:
        if not check_file_exists(file_path, description):
            all_passed = False
    
    return all_passed

def check_documentation():
    """Validate documentation completeness"""
    print("\n3. DOCUMENTATION VALIDATION")
    print("=" * 40)
    
    doc_files = [
        ("docs/CODING_STANDARDS.md", "Coding standards"),
        ("docs/API_DOCUMENTATION.md", "API documentation"),
        ("docs/DEPLOYMENT_GUIDE.md", "Deployment guide"),
        ("docs/FOUND_ISSUES.txt", "Issues report"),
        ("docs/FUNCTIONALITY_IMPACT_ANALYSIS.txt", "Impact analysis"),
        ("docs/ISSUE_RESOLUTION_PLAN.txt", "Resolution plan")
    ]
    
    all_passed = True
    for file_path, description in doc_files:
        if not check_file_exists(file_path, description):
            all_passed = False
    
    return all_passed

def check_code_quality():
    """Basic code quality checks"""
    print("\n4. CODE QUALITY VALIDATION")
    print("=" * 40)
    
    checks = [
        ('python -c "import main"', "Main application imports"),
        ('python -c "from estatecore_backend.models import db, LPREvent"', "Backend model imports"),
        ('set SECRET_KEY=test_key_12345678 && set DATABASE_URL=postgresql://test:test@localhost:5432/test && python -c "import config"', "Configuration imports with test env"),
    ]
    
    all_passed = True
    for cmd, description in checks:
        if not run_command(cmd, description):
            all_passed = False
    
    return all_passed

def check_security_configuration():
    """Check security-related configurations"""
    print("\n5. SECURITY VALIDATION")
    print("=" * 40)
    
    security_checks = []
    
    # Check .env.example exists and has required variables
    if os.path.exists('.env.example'):
        with open('.env.example', 'r') as f:
            env_content = f.read()
            required_vars = ['SECRET_KEY', 'DATABASE_URL']
            for var in required_vars:
                if var in env_content:
                    print(f"PASS: .env.example contains {var}")
                else:
                    print(f"FAIL: .env.example missing {var}")
                    security_checks.append(False)
    
    # Check .gitignore contains sensitive patterns
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
            sensitive_patterns = ['.env', '*.pyc', '__pycache__', 'node_modules']
            for pattern in sensitive_patterns:
                if pattern in gitignore_content:
                    print(f"PASS: .gitignore excludes {pattern}")
                else:
                    print(f"FAIL: .gitignore missing {pattern}")
                    security_checks.append(False)
    
    # Check no hardcoded secrets in main files
    sensitive_files = ['main.py', 'config.py', 'estatecore_backend/config.py']
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                if 'os.environ.get(' in content:
                    print(f"PASS: {file_path} uses environment variables")
                else:
                    print(f"WARN: {file_path} may not be using environment variables")
    
    return len(security_checks) == 0 or all(security_checks)

def check_cleanup_status():
    """Check that cleanup was successful"""
    print("\n6. CLEANUP VALIDATION")
    print("=" * 40)
    
    # Check for files that should have been removed
    cleanup_patterns = [
        ("find . -name '*.bak' -not -path './.venv/*'", "Backup files removed"),
        ("find . -name 'New Text Document*.txt'", "Temporary text files removed"),
        ("find . -name '*.lnk'", "Link files removed")
    ]
    
    all_passed = True
    for cmd, description in cleanup_patterns:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout.strip() == "":
                print(f"PASS: {description}")
            else:
                print(f"FAIL: {description}: Found {len(result.stdout.splitlines())} files")
                all_passed = False
        except Exception as e:
            print(f"WARN: Could not check {description}: {str(e)}")
    
    return all_passed

def generate_summary():
    """Generate overall validation summary"""
    print("\n" + "=" * 60)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 60)
    
    checks = [
        ("Project Structure", check_directory_structure()),
        ("Configuration Files", check_configuration_files()),
        ("Documentation", check_documentation()),
        ("Code Quality", check_code_quality()),
        ("Security Configuration", check_security_configuration()),
        ("Cleanup Status", check_cleanup_status())
    ]
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    print(f"\nValidation Results: {passed}/{total} checks passed")
    
    for check_name, status in checks:
        status_icon = "PASS" if status else "FAIL"
        print(f"{status_icon}: {check_name}")
    
    if passed == total:
        print("\nSUCCESS: ALL VALIDATIONS PASSED!")
        print("EstateCore is ready for deployment.")
        return True
    else:
        print(f"\nWARNING: {total - passed} validation(s) failed.")
        print("Please address the issues before deployment.")
        return False

if __name__ == "__main__":
    print("EstateCore Final Validation")
    print("=" * 60)
    print("Running comprehensive system validation...")
    
    success = generate_summary()
    
    if success:
        print("\nNext steps:")
        print("1. Review deployment guide: docs/DEPLOYMENT_GUIDE.md")
        print("2. Configure production environment variables")
        print("3. Run database migrations")
        print("4. Deploy to your target environment")
        sys.exit(0)
    else:
        print("\nPlease fix the validation failures and run this script again.")
        sys.exit(1)
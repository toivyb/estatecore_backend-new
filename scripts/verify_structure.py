#!/usr/bin/env python3
"""
Project structure verification script
Checks that the EstateCore project structure is properly organized
"""
import os
import sys

def check_directory_structure():
    """Check that all expected directories exist"""
    expected_dirs = [
        'estatecore_backend',
        'estatecore_frontend',
        'ai_modules',
        'scripts',
        'docs',
        'deployment',
        'archive/legacy',
        'utils',
        'migrations',
        'instance'
    ]
    
    missing_dirs = []
    for dir_path in expected_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print("ERROR: Missing directories:")
        for dir_path in missing_dirs:
            print(f"  - {dir_path}")
        return False
    
    print("SUCCESS: All expected directories present")
    return True

def check_key_files():
    """Check that key configuration files exist"""
    key_files = [
        'README.md',
        '.env.example',
        '.gitignore',
        'requirements.txt',
        'requirements-ai.txt',
        'config.py',
        'main.py',
        'estatecore_frontend/package.json',
        'estatecore_backend/models/__init__.py'
    ]
    
    missing_files = []
    for file_path in key_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("ERROR: Missing key files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    print("SUCCESS: All key files present")
    return True

def check_cleanup():
    """Check that temporary and backup files were removed"""
    cleanup_patterns = [
        '*.bak',
        '*.bak.bak', 
        'New Text Document*.txt',
        '*.lnk',
        '*.tar'
    ]
    
    found_files = []
    for pattern in cleanup_patterns:
        import glob
        files = glob.glob(pattern, recursive=True)
        found_files.extend(files)
    
    if found_files:
        print("WARNING: Found files that should have been cleaned up:")
        for file_path in found_files[:10]:  # Show first 10
            print(f"  - {file_path}")
        if len(found_files) > 10:
            print(f"  ... and {len(found_files) - 10} more")
        return False
    
    print("SUCCESS: No cleanup remnants found")
    return True

if __name__ == "__main__":
    print("EstateCore Project Structure Verification")
    print("=" * 45)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Key Files", check_key_files),
        ("Cleanup Status", check_cleanup)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 45)
    if all_passed:
        print("OVERALL: Project structure verification PASSED!")
        sys.exit(0)
    else:
        print("OVERALL: Project structure verification FAILED!")
        sys.exit(1)
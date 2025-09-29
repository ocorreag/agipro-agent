#!/usr/bin/env python3
"""
Test script to validate the unified path management system
This ensures all components point to the correct directories
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def test_path_manager():
    """Test the path manager in both development and bundle modes"""
    print("🔧 Testing Path Manager System")
    print("=" * 60)

    # Import and test path manager
    from path_manager import path_manager

    # Print debug info
    path_manager.print_debug_info()

    # Test directory creation
    print("\n🏗️ Testing Directory Creation...")
    path_manager.ensure_directories()

    # Verify all directories exist
    paths_to_check = [
        'publicaciones',
        'drafts',
        'imagenes',
        'memory',
        'linea_grafica'
    ]

    all_good = True
    for path_key in paths_to_check:
        path = path_manager.get_path(path_key)
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {path_key:15}: {path}")
        if not exists:
            all_good = False

    return all_good

def test_component_imports():
    """Test that all components can import and use path_manager"""
    print("\n🔌 Testing Component Integration...")

    components_to_test = [
        ('csv_manager', 'PostManager'),
        ('images', 'SocialMediaImageGenerator'),
        ('file_manager', 'FileManager'),
    ]

    all_good = True
    for module_name, class_name in components_to_test:
        try:
            module = __import__(module_name)
            class_obj = getattr(module, class_name)

            # Try to instantiate
            instance = class_obj()
            print(f"  ✓ {module_name}.{class_name} - OK")

        except Exception as e:
            print(f"  ✗ {module_name}.{class_name} - ERROR: {e}")
            all_good = False

    return all_good

def test_duplicate_folders():
    """Check for duplicate folder structures"""
    print("\n📁 Checking for Duplicate Folders...")

    base_dir = Path(__file__).parent
    folders_to_check = ['publicaciones', 'memory', 'linea_grafica']

    duplicates_found = False
    for folder_name in folders_to_check:
        found_paths = list(base_dir.rglob(folder_name))
        # Filter to only directories
        found_dirs = [p for p in found_paths if p.is_dir()]

        if len(found_dirs) > 1:
            print(f"  ⚠️ Multiple {folder_name} directories found:")
            for path in found_dirs:
                print(f"    - {path}")
            duplicates_found = True
        else:
            print(f"  ✓ {folder_name}: Single directory found")

    return not duplicates_found

def cleanup_duplicates():
    """Clean up duplicate folder structures"""
    print("\n🧹 Cleaning up duplicate folders...")

    base_dir = Path(__file__).parent

    # Remove src/src if it exists (common PyInstaller artifact)
    src_src_path = base_dir / 'src' / 'src'
    if src_src_path.exists():
        import shutil
        try:
            shutil.rmtree(src_src_path)
            print(f"  ✓ Removed duplicate directory: {src_src_path}")
        except Exception as e:
            print(f"  ✗ Could not remove {src_src_path}: {e}")

def main():
    """Main test function"""
    print("🦋 CAUSA Agent - Path Management Validation")
    print("=" * 60)

    # Clean up any duplicates first
    cleanup_duplicates()

    # Run tests
    test1_passed = test_path_manager()
    test2_passed = test_component_imports()
    test3_passed = test_duplicate_folders()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"  Path Manager:       {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"  Component Integration: {'✓ PASS' if test2_passed else '✗ FAIL'}")
    print(f"  No Duplicates:      {'✓ PASS' if test3_passed else '✗ FAIL'}")

    overall_pass = all([test1_passed, test2_passed, test3_passed])
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_pass else '❌ SOME TESTS FAILED'}")

    if overall_pass:
        print("\n💡 The path management system is working correctly!")
        print("   All components will use consistent folder structures.")
    else:
        print("\n⚠️ Issues found that need to be resolved before building.")

    return 0 if overall_pass else 1

if __name__ == "__main__":
    sys.exit(main())

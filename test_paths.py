#!/usr/bin/env python3
"""
CAUSA Agent - Path & Configuration Verification

This script validates that:
1. All directories are correctly configured
2. No duplicate folder structures exist
3. All components can import and use path_manager
4. Configuration files are accessible

Run this after migration or to debug path issues.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))


class PathVerifier:
    """Verifies the CAUSA Agent path configuration"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.src_dir = self.base_dir / 'src'

        self.tests_passed = 0
        self.tests_failed = 0
        self.warnings = []

    def run(self):
        """Run all verification tests"""
        print("🦋 CAUSA Agent - Path Verification")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Base directory: {self.base_dir}")
        print()

        # Run test suites
        self._test_path_manager()
        self._test_no_duplicates()
        self._test_component_imports()
        self._test_configuration()

        # Print summary
        self._print_summary()

        return 0 if self.tests_failed == 0 else 1

    def _pass(self, message: str):
        """Record a passed test"""
        print(f"   ✓ {message}")
        self.tests_passed += 1

    def _fail(self, message: str):
        """Record a failed test"""
        print(f"   ✗ {message}")
        self.tests_failed += 1

    def _warn(self, message: str):
        """Record a warning"""
        print(f"   ⚠ {message}")
        self.warnings.append(message)

    def _test_path_manager(self):
        """Test the centralized path manager"""
        print("🔧 Testing Path Manager...")

        try:
            from path_manager import path_manager

            # Test that path_manager loads correctly
            self._pass("path_manager imports successfully")

            # Test execution mode detection
            mode = path_manager.get_execution_mode()
            if mode in ['development', 'bundle']:
                self._pass(f"Execution mode detected: {mode}")
            else:
                self._fail(f"Unknown execution mode: {mode}")

            # Test that all required paths exist
            required_paths = ['publicaciones', 'drafts', 'imagenes', 'memory', 'linea_grafica']

            # Ensure directories first
            path_manager.ensure_directories()

            for path_key in required_paths:
                try:
                    path = path_manager.get_path(path_key)
                    if path.exists():
                        self._pass(f"Path '{path_key}' exists: {path}")
                    else:
                        self._warn(f"Path '{path_key}' configured but doesn't exist yet: {path}")
                except KeyError:
                    self._fail(f"Path '{path_key}' not configured")

            # Verify paths are at project root, not in src/
            pub_path = path_manager.get_path('publicaciones')
            if 'src' not in pub_path.parts[:-1]:  # src shouldn't be in path except maybe at root
                self._pass("Data paths correctly point to project root")
            else:
                self._fail("Data paths incorrectly point inside src/")

        except ImportError as e:
            self._fail(f"Could not import path_manager: {e}")
        except Exception as e:
            self._fail(f"path_manager error: {e}")

    def _test_no_duplicates(self):
        """Check for duplicate folder structures"""
        print("\n📁 Checking for Duplicate Folders...")

        data_dirs = ['publicaciones', 'memory', 'linea_grafica']

        for dir_name in data_dirs:
            # Find all directories with this name
            found_dirs = []
            for path in self.base_dir.rglob(dir_name):
                if path.is_dir():
                    found_dirs.append(path)

            if len(found_dirs) == 0:
                self._warn(f"No '{dir_name}' directory found")
            elif len(found_dirs) == 1:
                rel_path = found_dirs[0].relative_to(self.base_dir)
                self._pass(f"Single '{dir_name}' at: {rel_path}")
            else:
                self._fail(f"Multiple '{dir_name}' directories found:")
                for path in found_dirs:
                    print(f"      - {path.relative_to(self.base_dir)}")

        # Check for src/src artifact
        src_src = self.src_dir / 'src'
        if src_src.exists():
            self._fail(f"Build artifact exists: src/src/ - run migrate_data.py to clean")
        else:
            self._pass("No src/src/ artifact found")

    def _test_component_imports(self):
        """Test that all components can import path_manager"""
        print("\n🔌 Testing Component Integration...")

        components = [
            ('csv_manager', 'PostManager'),
            ('images', 'SocialMediaImageGenerator'),
            ('file_manager', 'FileManager'),
            ('config_manager', 'ConfigManager'),
        ]

        for module_name, class_name in components:
            try:
                module = __import__(module_name)
                cls = getattr(module, class_name)

                # Try to instantiate (this tests that paths are accessible)
                instance = cls()
                self._pass(f"{module_name}.{class_name}")

            except ImportError as e:
                self._fail(f"{module_name}: Import error - {e}")
            except Exception as e:
                # Some initialization errors might be expected (e.g., missing API key)
                error_str = str(e).lower()
                if 'api' in error_str or 'key' in error_str or 'openai' in error_str:
                    self._warn(f"{module_name}.{class_name}: {e}")
                else:
                    self._fail(f"{module_name}.{class_name}: {e}")

    def _test_configuration(self):
        """Test configuration file access"""
        print("\n⚙️ Testing Configuration...")

        # Check .env exists
        env_file = self.base_dir / '.env'
        env_example = self.base_dir / '.env.example'

        if env_file.exists():
            self._pass(".env file exists at project root")
        elif env_example.exists():
            self._warn(".env not found, but .env.example exists - copy and configure it")
        else:
            self._fail("No .env or .env.example found at project root")

        # Check settings.json in publicaciones
        settings_file = self.base_dir / 'publicaciones' / 'settings.json'
        if settings_file.exists():
            self._pass("settings.json exists in publicaciones/")
        else:
            self._warn("settings.json not found - will be created on first run")

        # Check app_config.json
        config_file = self.base_dir / 'publicaciones' / 'app_config.json'
        if config_file.exists():
            self._pass("app_config.json exists in publicaciones/")
        else:
            self._warn("app_config.json not found - will be created on first run")

    def _print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 Verification Summary")
        print("=" * 60)

        total_tests = self.tests_passed + self.tests_failed
        print(f"   Tests passed:  {self.tests_passed}/{total_tests}")
        print(f"   Tests failed:  {self.tests_failed}/{total_tests}")
        print(f"   Warnings:      {len(self.warnings)}")

        if self.warnings:
            print("\n⚠️ Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")

        print("\n" + "=" * 60)

        if self.tests_failed == 0:
            print("✅ All tests passed! Path configuration is correct.")
            print("\n💡 The system is ready to use.")
        else:
            print("❌ Some tests failed. Please review and fix the issues above.")
            print("\n💡 Try running: python migrate_data.py")


def main():
    """Main entry point"""
    verifier = PathVerifier()
    return verifier.run()


if __name__ == "__main__":
    sys.exit(main())

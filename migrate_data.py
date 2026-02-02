#!/usr/bin/env python3
"""
CAUSA Agent - Data Migration & Cleanup Utility

This script handles:
1. Migration of data from old locations (src/) to the project root
2. Cleanup of duplicate/artifact directories (src/src/, etc.)
3. Verification of correct directory structure

Run this if you're upgrading from an older version or experiencing path issues.
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime


class DataMigrator:
    """Handles data migration and cleanup for CAUSA Agent"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.src_dir = self.base_dir / 'src'

        # Expected data directories at project root
        self.data_dirs = ['publicaciones', 'memory', 'linea_grafica']

        # Statistics
        self.stats = {
            'migrated_files': 0,
            'cleaned_dirs': 0,
            'errors': []
        }

    def run(self):
        """Run the complete migration and cleanup process"""
        print("🦋 CAUSA Agent - Data Migration & Cleanup Utility")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Base directory: {self.base_dir}")
        print()

        # Step 1: Clean up build artifacts (src/src/, etc.)
        self._cleanup_artifacts()

        # Step 2: Migrate any data from src/ subdirectories
        self._migrate_from_src()

        # Step 3: Ensure correct directory structure exists
        self._ensure_directories()

        # Step 4: Migrate .env if needed
        self._migrate_env()

        # Summary
        self._print_summary()

        return 0 if not self.stats['errors'] else 1

    def _cleanup_artifacts(self):
        """Remove build artifacts and duplicate structures"""
        print("🧹 Cleaning up build artifacts...")

        artifacts_to_remove = [
            self.src_dir / 'src',  # Nested src/src directory
        ]

        for artifact_path in artifacts_to_remove:
            if artifact_path.exists():
                try:
                    if artifact_path.is_dir():
                        shutil.rmtree(artifact_path)
                    else:
                        artifact_path.unlink()
                    print(f"   ✓ Removed: {artifact_path.relative_to(self.base_dir)}")
                    self.stats['cleaned_dirs'] += 1
                except Exception as e:
                    error_msg = f"Could not remove {artifact_path}: {e}"
                    print(f"   ✗ {error_msg}")
                    self.stats['errors'].append(error_msg)
            else:
                print(f"   - Not found (OK): {artifact_path.relative_to(self.base_dir)}")

    def _migrate_from_src(self):
        """Migrate data from old src/ subdirectories to project root"""
        print("\n📦 Checking for data to migrate from src/...")

        for dir_name in self.data_dirs:
            src_path = self.src_dir / dir_name
            dest_path = self.base_dir / dir_name

            if not src_path.exists():
                print(f"   - {dir_name}: No source directory")
                continue

            # Check if source has files
            src_files = list(src_path.rglob('*'))
            if not src_files:
                print(f"   - {dir_name}: Source is empty")
                # Remove empty source directory
                try:
                    shutil.rmtree(src_path)
                    print(f"     ✓ Removed empty: src/{dir_name}")
                except:
                    pass
                continue

            # Migrate files
            dest_path.mkdir(parents=True, exist_ok=True)
            migrated = self._migrate_directory(src_path, dest_path)
            print(f"   ✓ {dir_name}: Migrated {migrated} files")

            # Remove source after successful migration
            try:
                shutil.rmtree(src_path)
                print(f"     ✓ Cleaned up: src/{dir_name}")
            except Exception as e:
                print(f"     ⚠ Could not remove src/{dir_name}: {e}")

    def _migrate_directory(self, src_dir: Path, dest_dir: Path) -> int:
        """Migrate contents of a directory, returns count of migrated files"""
        migrated_count = 0

        for item in src_dir.iterdir():
            if item.name.startswith('.'):
                continue  # Skip hidden files

            dest_item = dest_dir / item.name

            try:
                if item.is_file():
                    if not dest_item.exists():
                        shutil.copy2(item, dest_item)
                        migrated_count += 1
                        self.stats['migrated_files'] += 1
                    elif item.stat().st_mtime > dest_item.stat().st_mtime:
                        # Source is newer, backup and replace
                        backup_name = f"{dest_item.stem}_backup_{datetime.now().strftime('%Y%m%d')}{dest_item.suffix}"
                        shutil.copy2(dest_item, dest_dir / backup_name)
                        shutil.copy2(item, dest_item)
                        migrated_count += 1
                        self.stats['migrated_files'] += 1

                elif item.is_dir():
                    dest_item.mkdir(parents=True, exist_ok=True)
                    migrated_count += self._migrate_directory(item, dest_item)

            except Exception as e:
                self.stats['errors'].append(f"Error migrating {item.name}: {e}")

        return migrated_count

    def _ensure_directories(self):
        """Ensure all required directories exist at project root"""
        print("\n📁 Ensuring directory structure...")

        for dir_name in self.data_dirs:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

            status = "✓ exists" if dir_path.exists() else "✗ failed"
            print(f"   {status}: {dir_name}/")

        # Also ensure subdirectories for publicaciones
        (self.base_dir / 'publicaciones' / 'drafts').mkdir(parents=True, exist_ok=True)
        (self.base_dir / 'publicaciones' / 'imagenes').mkdir(parents=True, exist_ok=True)
        print("   ✓ publicaciones/drafts/")
        print("   ✓ publicaciones/imagenes/")

    def _migrate_env(self):
        """Migrate .env file from src/ to root if needed"""
        print("\n🔐 Checking .env configuration...")

        src_env = self.src_dir / '.env'
        root_env = self.base_dir / '.env'
        root_env_example = self.base_dir / '.env.example'

        if src_env.exists() and not root_env.exists():
            try:
                shutil.copy2(src_env, root_env)
                src_env.unlink()
                print("   ✓ Migrated .env from src/ to project root")
                self.stats['migrated_files'] += 1
            except Exception as e:
                self.stats['errors'].append(f"Could not migrate .env: {e}")
        elif root_env.exists():
            print("   ✓ .env already at project root")
        elif root_env_example.exists():
            print("   ⚠ No .env found - copy .env.example to .env and add your API key")
        else:
            print("   ✗ No .env or .env.example found")

        # Remove duplicate .env.example from src/ if it exists
        src_env_example = self.src_dir / '.env.example'
        if src_env_example.exists():
            try:
                src_env_example.unlink()
                print("   ✓ Removed duplicate src/.env.example")
            except:
                pass

    def _print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 60)
        print("📊 Migration Summary")
        print("=" * 60)
        print(f"   Files migrated:     {self.stats['migrated_files']}")
        print(f"   Directories cleaned: {self.stats['cleaned_dirs']}")
        print(f"   Errors:             {len(self.stats['errors'])}")

        if self.stats['errors']:
            print("\n⚠️ Errors encountered:")
            for error in self.stats['errors']:
                print(f"   - {error}")

        print("\n" + "=" * 60)

        if not self.stats['errors']:
            print("✅ Migration completed successfully!")
            print("\n📍 Data Directory Structure:")
            print("   agipro_agent/")
            print("   ├── publicaciones/    <- Posts, drafts, images, config")
            print("   │   ├── drafts/       <- Draft CSV files")
            print("   │   └── imagenes/     <- Generated images")
            print("   ├── memory/           <- Collective memory documents (PDF, TXT)")
            print("   ├── linea_grafica/    <- Brand style images")
            print("   └── .env              <- API keys and configuration")
            print("\n💡 Run 'python test_paths.py' to verify everything works correctly.")
        else:
            print("⚠️ Migration completed with errors. Please review and fix manually.")


def main():
    """Main entry point"""
    migrator = DataMigrator()
    return migrator.run()


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Data migration script for CAUSA Agent
Migrates existing data from src/ subdirectories to project root
"""

import sys
import shutil
from pathlib import Path

def migrate_directory_contents(src_dir: Path, dest_dir: Path, folder_name: str):
    """Migrate contents from src directory to destination directory"""
    if not src_dir.exists():
        print(f"  ✓ {folder_name}: No source directory to migrate")
        return True

    # Create destination if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Check if source has any contents
    src_contents = list(src_dir.iterdir())
    if not src_contents:
        print(f"  ✓ {folder_name}: Source directory is empty")
        return True

    print(f"  🔄 {folder_name}: Migrating {len(src_contents)} items...")

    # Copy all contents
    migrated_count = 0
    for item in src_contents:
        if item.name.startswith('.'):
            continue  # Skip hidden files like .DS_Store

        dest_item = dest_dir / item.name

        try:
            if item.is_file():
                if dest_item.exists():
                    # File exists, check if they're different
                    if item.stat().st_size != dest_item.stat().st_size:
                        # Backup existing file
                        backup_name = f"{dest_item.stem}_backup{dest_item.suffix}"
                        shutil.copy2(dest_item, dest_dir / backup_name)
                        print(f"    📦 Backed up existing: {dest_item.name}")

                # Copy the file
                shutil.copy2(item, dest_item)
                migrated_count += 1

            elif item.is_dir():
                if dest_item.exists():
                    # Merge directories
                    for sub_item in item.rglob('*'):
                        if sub_item.is_file():
                            rel_path = sub_item.relative_to(item)
                            dest_sub_item = dest_item / rel_path
                            dest_sub_item.parent.mkdir(parents=True, exist_ok=True)

                            if not dest_sub_item.exists():
                                shutil.copy2(sub_item, dest_sub_item)
                                migrated_count += 1
                else:
                    # Copy entire directory
                    shutil.copytree(item, dest_item)
                    migrated_count += len(list(item.rglob('*')))

        except Exception as e:
            print(f"    ⚠️ Error copying {item.name}: {e}")

    print(f"  ✓ {folder_name}: Migrated {migrated_count} items")
    return True

def main():
    """Main migration function"""
    print("🔄 CAUSA Agent - Data Migration")
    print("=" * 50)

    base_dir = Path(__file__).parent
    src_dir = base_dir / 'src'

    # Migration mappings: (source_subdir, destination_dir, name)
    migrations = [
        (src_dir / 'publicaciones', base_dir / 'publicaciones', 'publicaciones'),
        (src_dir / 'memory', base_dir / 'memory', 'memory'),
        (src_dir / 'linea_grafica', base_dir / 'linea_grafica', 'linea_grafica'),
    ]

    print("Migrating data from src/ subdirectories to project root...")
    print()

    all_success = True
    for src_path, dest_path, name in migrations:
        success = migrate_directory_contents(src_path, dest_path, name)
        all_success = all_success and success

    # Special handling for .env file
    src_env = src_dir / '.env'
    dest_env = base_dir / '.env'
    src_env_example = src_dir / '.env.example'
    dest_env_example = base_dir / '.env.example'

    if src_env.exists() and not dest_env.exists():
        shutil.copy2(src_env, dest_env)
        print("  ✓ Migrated .env file")

    if src_env_example.exists() and not dest_env_example.exists():
        shutil.copy2(src_env_example, dest_env_example)
        print("  ✓ Migrated .env.example file")

    if all_success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Verify your data is accessible in the new locations")
        print("2. Test the application with: python test_paths.py")
        print("3. If everything works, you can remove the old directories:")
        print(f"   rm -rf {src_dir}/publicaciones")
        print(f"   rm -rf {src_dir}/memory")
        print(f"   rm -rf {src_dir}/linea_grafica")
    else:
        print("\n⚠️ Migration completed with some errors")
        print("Please review the output above and manually handle any failed items")

    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())

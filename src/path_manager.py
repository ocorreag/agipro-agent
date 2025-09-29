"""
Centralized path management for CAUSA Agent
Ensures consistent folder structure across all components
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

class PathManager:
    """Manages all paths consistently across the application"""

    def __init__(self):
        self._base_dir = None
        self._paths = {}
        self._setup_base_directory()
        self._setup_paths()

    def _setup_base_directory(self):
        """Determine the correct base directory based on execution context"""

        # Check if running as PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller executable
            # Base directory should be where the executable is located
            self._base_dir = Path(sys.executable).parent
            self._execution_mode = "bundle"
        else:
            # Running in development mode
            # Base directory should be the project root (parent of src)
            script_dir = Path(__file__).parent  # This is src/
            self._base_dir = script_dir.parent   # This is project root
            self._execution_mode = "development"

    def _setup_paths(self):
        """Setup all application paths"""
        self._paths = {
            # Data directories (always at base level for user access)
            'publicaciones': self._base_dir / 'publicaciones',
            'drafts': self._base_dir / 'publicaciones' / 'drafts',
            'imagenes': self._base_dir / 'publicaciones' / 'imagenes',
            'memory': self._base_dir / 'memory',
            'linea_grafica': self._base_dir / 'linea_grafica',

            # Configuration files
            'settings': self._base_dir / 'publicaciones' / 'settings.json',
            'published_posts': self._base_dir / 'publicaciones' / 'published_posts.csv',
            'env_file': self._base_dir / '.env',
            'env_example': self._base_dir / '.env.example',

            # Source code (different location based on execution mode)
            'src': self._get_src_path(),
        }

    def _get_src_path(self) -> Path:
        """Get source path based on execution context"""
        if self._execution_mode == "bundle":
            # In bundle mode, source files are extracted to _MEIPASS
            return Path(sys._MEIPASS)
        else:
            # In development mode, source is in src/
            return Path(__file__).parent

    def get_path(self, key: str) -> Path:
        """Get a specific path"""
        if key not in self._paths:
            raise KeyError(f"Unknown path key: {key}. Available keys: {list(self._paths.keys())}")
        return self._paths[key]

    def get_base_dir(self) -> Path:
        """Get the base directory"""
        return self._base_dir

    def get_execution_mode(self) -> str:
        """Get the current execution mode (bundle or development)"""
        return self._execution_mode

    def ensure_directories(self):
        """Create all necessary directories"""
        directories_to_create = [
            'publicaciones',
            'drafts',
            'imagenes',
            'memory',
            'linea_grafica'
        ]

        for dir_key in directories_to_create:
            dir_path = self.get_path(dir_key)
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_all_paths(self) -> Dict[str, Path]:
        """Get all paths for debugging"""
        return self._paths.copy()

    def setup_env_file(self):
        """Setup .env file from example if it doesn't exist"""
        env_file = self.get_path('env_file')
        env_example = self.get_path('env_example')

        if not env_file.exists() and env_example.exists():
            try:
                with open(env_example, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ Created .env file from template at: {env_file}")
                return True
            except Exception as e:
                print(f"⚠️ Could not create .env file: {e}")
                return False
        return env_file.exists()

    def print_debug_info(self):
        """Print debugging information about paths"""
        print("=" * 60)
        print("🔧 CAUSA Agent - Path Manager Debug Info")
        print("=" * 60)
        print(f"Execution Mode: {self._execution_mode}")
        print(f"Base Directory: {self._base_dir}")
        print(f"Base Dir Exists: {self._base_dir.exists()}")

        if self._execution_mode == "bundle":
            print(f"Executable Path: {sys.executable}")
            print(f"_MEIPASS: {getattr(sys, '_MEIPASS', 'Not available')}")

        print("\nPath Configuration:")
        for key, path in self._paths.items():
            exists = "✓" if path.exists() else "✗"
            print(f"  {key:15} {exists} {path}")
        print("=" * 60)

# Global instance
path_manager = PathManager()

# Convenience functions for backward compatibility
def get_publicaciones_dir() -> Path:
    return path_manager.get_path('publicaciones')

def get_drafts_dir() -> Path:
    return path_manager.get_path('drafts')

def get_imagenes_dir() -> Path:
    return path_manager.get_path('imagenes')

def get_memory_dir() -> Path:
    return path_manager.get_path('memory')

def get_linea_grafica_dir() -> Path:
    return path_manager.get_path('linea_grafica')

def ensure_all_directories():
    """Ensure all directories exist"""
    path_manager.ensure_directories()

def setup_environment():
    """Complete environment setup"""
    path_manager.ensure_directories()
    path_manager.setup_env_file()

if __name__ == "__main__":
    # Debug mode - print all path information
    path_manager.print_debug_info()

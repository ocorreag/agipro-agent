"""
File manager for handling memory documents and linea_grafica images.
Provides upload, delete, and management functionality for the CAUSA system.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
from datetime import datetime
import mimetypes

class FileManager:
    def __init__(self):
        self.memory_dir = Path("src/memory")
        self.linea_grafica_dir = Path("src/linea_grafica")
        self.publicaciones_dir = Path("src/publicaciones")

        # Ensure directories exist
        for dir_path in [self.memory_dir, self.linea_grafica_dir, self.publicaciones_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_memory_files(self) -> List[Dict[str, Any]]:
        """Get all files in the memory directory"""
        files = []
        if self.memory_dir.exists():
            for file_path in self.memory_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': self._format_file_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'type': self._get_file_type(file_path)
                    })
        return sorted(files, key=lambda x: x['name'])

    def get_linea_grafica_files(self) -> List[Dict[str, Any]]:
        """Get all files in the linea_grafica directory"""
        files = []
        if self.linea_grafica_dir.exists():
            for file_path in self.linea_grafica_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': self._format_file_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'type': self._get_file_type(file_path)
                    })
        return sorted(files, key=lambda x: x['name'])

    def get_generated_images(self) -> List[Dict[str, Any]]:
        """Get all generated images from publicaciones/imagenes"""
        images_dir = self.publicaciones_dir / "imagenes"
        files = []
        if images_dir.exists():
            for file_path in images_dir.iterdir():
                if file_path.is_file() and self._is_image_file(file_path):
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': self._format_file_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'type': 'image'
                    })
        return sorted(files, key=lambda x: x['modified'], reverse=True)

    def upload_memory_file(self, uploaded_file) -> bool:
        """Upload a file to the memory directory"""
        try:
            file_path = self.memory_dir / uploaded_file.name

            # Check if file already exists
            if file_path.exists():
                st.warning(f"File '{uploaded_file.name}' already exists and will be overwritten.")

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"✓ Uploaded '{uploaded_file.name}' to memory folder")
            return True
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")
            return False

    def upload_linea_grafica_file(self, uploaded_file) -> bool:
        """Upload an image to the linea_grafica directory"""
        try:
            # Validate it's an image
            if not self._is_image_file_by_name(uploaded_file.name):
                st.error(f"'{uploaded_file.name}' is not a valid image file")
                return False

            file_path = self.linea_grafica_dir / uploaded_file.name

            # Check if file already exists
            if file_path.exists():
                st.warning(f"Image '{uploaded_file.name}' already exists and will be overwritten.")

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"✓ Uploaded '{uploaded_file.name}' to linea gráfica folder")
            return True
        except Exception as e:
            st.error(f"Error uploading image: {str(e)}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                st.success(f"✓ Deleted '{path.name}'")
                return True
            else:
                st.error(f"File not found: {path.name}")
                return False
        except Exception as e:
            st.error(f"Error deleting file: {str(e)}")
            return False

    def delete_multiple_files(self, file_paths: List[str]) -> Tuple[int, int]:
        """Delete multiple files. Returns (success_count, total_count)"""
        success_count = 0
        total_count = len(file_paths)

        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    success_count += 1
            except Exception as e:
                st.error(f"Error deleting {Path(file_path).name}: {str(e)}")

        if success_count == total_count:
            st.success(f"✓ Deleted {success_count} files")
        else:
            st.warning(f"Deleted {success_count} of {total_count} files")

        return success_count, total_count

    def copy_generated_image_to_linea_grafica(self, image_path: str, new_name: Optional[str] = None) -> bool:
        """Copy a generated image to the linea_grafica folder"""
        try:
            source_path = Path(image_path)
            if not source_path.exists():
                st.error("Source image not found")
                return False

            # Use provided name or generate one with timestamp
            if new_name:
                filename = new_name
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_name = source_path.stem
                extension = source_path.suffix
                filename = f"{original_name}_{timestamp}{extension}"

            dest_path = self.linea_grafica_dir / filename

            # Check if destination already exists
            if dest_path.exists():
                st.warning(f"File '{filename}' already exists in linea gráfica and will be overwritten.")

            shutil.copy2(source_path, dest_path)
            st.success(f"✓ Copied image to linea gráfica as '{filename}'")
            return True

        except Exception as e:
            st.error(f"Error copying image: {str(e)}")
            return False

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)

        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1

        return f"{size:.1f} {size_names[i]}"

    def _get_file_type(self, file_path: Path) -> str:
        """Get file type based on extension"""
        extension = file_path.suffix.lower()

        if extension in ['.pdf']:
            return 'document'
        elif extension in ['.txt', '.md']:
            return 'text'
        elif extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']:
            return 'image'
        else:
            return 'other'

    def _is_image_file(self, file_path: Path) -> bool:
        """Check if file is an image based on extension"""
        extension = file_path.suffix.lower()
        return extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp']

    def _is_image_file_by_name(self, filename: str) -> bool:
        """Check if file is an image based on filename"""
        extension = Path(filename).suffix.lower()
        return extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp']

    def get_file_stats(self) -> Dict[str, int]:
        """Get statistics about files"""
        memory_count = len(self.get_memory_files())
        linea_grafica_count = len(self.get_linea_grafica_files())
        generated_images_count = len(self.get_generated_images())

        return {
            'memory_files': memory_count,
            'linea_grafica_files': linea_grafica_count,
            'generated_images': generated_images_count
        }
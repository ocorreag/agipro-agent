"""
Local Bridge - Communication layer between Cloud App and Local Helper.
Handles all HTTP requests to the Local Helper API.
"""

import os
import requests
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

# Default Local Helper URL (user's machine)
DEFAULT_HELPER_URL = "http://127.0.0.1:8765"

# Detect hybrid mode from environment
HYBRID_MODE = os.getenv("CAUSA_MODE", "local").lower() == "hybrid"


class LocalBridge:
    """Client for communicating with the Local Helper API."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("LOCAL_HELPER_URL", DEFAULT_HELPER_URL)
        self._connected = False
        self._last_error = None

    # =========================================================================
    # Connection Management
    # =========================================================================

    def check_connection(self) -> bool:
        """Check if Local Helper is reachable."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            self._connected = response.status_code == 200
            self._last_error = None
            return self._connected
        except requests.exceptions.RequestException as e:
            self._connected = False
            self._last_error = str(e)
            return False

    def is_connected(self) -> bool:
        """Return last known connection status."""
        return self._connected

    def get_last_error(self) -> Optional[str]:
        """Return last connection error."""
        return self._last_error

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status from Local Helper."""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"status": "disconnected"}

    # =========================================================================
    # Memory Files (PDFs for RAG)
    # =========================================================================

    def get_memory_files(self) -> List[Dict[str, Any]]:
        """Get list of memory files."""
        try:
            response = requests.get(f"{self.base_url}/api/files/memory", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self._last_error = str(e)
        return []

    def get_all_memory_content(self) -> List[Dict[str, Any]]:
        """Get extracted text content from all memory files (for RAG)."""
        try:
            response = requests.get(f"{self.base_url}/api/files/all-memory-content", timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self._last_error = str(e)
        return []

    def upload_memory_file(self, filename: str, content: bytes) -> bool:
        """Upload a memory file."""
        try:
            files = {"file": (filename, content)}
            response = requests.post(f"{self.base_url}/api/files/memory", files=files, timeout=30)
            return response.status_code == 200
        except Exception as e:
            self._last_error = str(e)
            return False

    def delete_memory_file(self, filename: str) -> bool:
        """Delete a memory file."""
        try:
            response = requests.delete(f"{self.base_url}/api/files/memory/{filename}", timeout=10)
            return response.status_code == 200
        except Exception as e:
            self._last_error = str(e)
            return False

    # =========================================================================
    # Images
    # =========================================================================

    def get_images(self) -> List[Dict[str, Any]]:
        """Get list of generated images."""
        try:
            response = requests.get(f"{self.base_url}/api/files/images", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self._last_error = str(e)
        return []

    def get_image(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get image as base64."""
        try:
            response = requests.get(f"{self.base_url}/api/files/images/{filename}", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self._last_error = str(e)
        return None

    def upload_image(self, filename: str, content: bytes) -> bool:
        """Upload/save an image."""
        try:
            files = {"file": (filename, content)}
            response = requests.post(f"{self.base_url}/api/files/images", files=files, timeout=30)
            return response.status_code == 200
        except Exception as e:
            self._last_error = str(e)
            return False

    # =========================================================================
    # Linea Grafica (Brand Images)
    # =========================================================================

    def get_linea_grafica(self) -> List[Dict[str, Any]]:
        """Get list of brand images."""
        try:
            response = requests.get(f"{self.base_url}/api/files/linea-grafica", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self._last_error = str(e)
        return []

    def get_linea_grafica_image(self, filename: str) -> Optional[bytes]:
        """Get brand image content."""
        try:
            response = requests.get(f"{self.base_url}/api/files/images/{filename}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "content" in data:
                    return base64.b64decode(data["content"])
        except Exception as e:
            self._last_error = str(e)
        return None

    def upload_linea_grafica(self, filename: str, content: bytes) -> bool:
        """Upload a brand image."""
        try:
            files = {"file": (filename, content)}
            response = requests.post(f"{self.base_url}/api/files/linea-grafica", files=files, timeout=30)
            return response.status_code == 200
        except Exception as e:
            self._last_error = str(e)
            return False

    # =========================================================================
    # Configuration
    # =========================================================================

    def get_config(self) -> Dict[str, Any]:
        """Get configuration from Local Helper."""
        try:
            response = requests.get(f"{self.base_url}/api/config", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self._last_error = str(e)
        return {}

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to Local Helper."""
        try:
            response = requests.post(
                f"{self.base_url}/api/config",
                json={"settings": config},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self._last_error = str(e)
            return False

    def get_prompts(self) -> Dict[str, str]:
        """Get prompts configuration."""
        try:
            response = requests.get(f"{self.base_url}/api/config/prompts", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self._last_error = str(e)
        return {}

    def save_prompts(self, prompts: Dict[str, str]) -> bool:
        """Save prompts configuration."""
        try:
            response = requests.post(
                f"{self.base_url}/api/config/prompts",
                json=prompts,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self._last_error = str(e)
            return False


# =============================================================================
# Singleton Instance
# =============================================================================

_bridge_instance: Optional[LocalBridge] = None


def get_bridge() -> LocalBridge:
    """Get or create the singleton bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = LocalBridge()
    return _bridge_instance


def is_hybrid_mode() -> bool:
    """Check if running in hybrid mode."""
    return HYBRID_MODE


# =============================================================================
# Utility Functions
# =============================================================================

def check_helper_connection() -> bool:
    """Quick check if Local Helper is available."""
    if not HYBRID_MODE:
        return True  # Not needed in local mode
    return get_bridge().check_connection()

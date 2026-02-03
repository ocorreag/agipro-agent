"""
CAUSA Agent Local Helper Server
FastAPI server for local file operations in hybrid architecture.
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Try to import PDF extractor
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


# =============================================================================
# Configuration
# =============================================================================

def get_base_dir() -> Path:
    """Get the base directory for data storage."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent


BASE_DIR = get_base_dir()
PORT = int(os.getenv("LOCAL_HELPER_PORT", "8765"))


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="CAUSA Local Helper",
    description="Local file server for CAUSA Agent hybrid architecture",
    version="1.0.0"
)

# CORS - Allow connections from cloud app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Pydantic Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    base_dir: str
    timestamp: str


class FileInfo(BaseModel):
    name: str
    size: int
    modified: str
    type: str


class ConfigData(BaseModel):
    settings: dict = {}


# =============================================================================
# Helper Functions
# =============================================================================

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = ["memory", "publicaciones", "publicaciones/drafts",
            "publicaciones/published", "linea_grafica", "imagenes"]
    for d in dirs:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)


def extract_pdf_text(file_path: Path) -> str:
    """Extract text from PDF file."""
    if not HAS_PYMUPDF:
        return ""
    try:
        doc = fitz.open(str(file_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Error extracting PDF: {e}"


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        base_dir=str(BASE_DIR),
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/status")
async def get_status():
    """Get detailed status of the local helper."""
    ensure_directories()
    return {
        "status": "running",
        "base_dir": str(BASE_DIR),
        "directories": {
            "memory": (BASE_DIR / "memory").exists(),
            "publicaciones": (BASE_DIR / "publicaciones").exists(),
            "linea_grafica": (BASE_DIR / "linea_grafica").exists(),
        },
        "pdf_support": HAS_PYMUPDF
    }


# -----------------------------------------------------------------------------
# Memory Files (PDFs for RAG)
# -----------------------------------------------------------------------------

@app.get("/api/files/memory")
async def list_memory_files():
    """List all memory files."""
    ensure_directories()
    memory_dir = BASE_DIR / "memory"
    files = []
    for f in memory_dir.iterdir():
        if f.is_file() and f.suffix.lower() in ['.pdf', '.txt']:
            files.append(FileInfo(
                name=f.name,
                size=f.stat().st_size,
                modified=datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                type=f.suffix.lower()
            ))
    return files


@app.post("/api/files/memory")
async def upload_memory_file(file: UploadFile = File(...)):
    """Upload a memory file."""
    ensure_directories()
    memory_dir = BASE_DIR / "memory"
    file_path = memory_dir / file.filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {"success": True, "filename": file.filename}


@app.delete("/api/files/memory/{filename}")
async def delete_memory_file(filename: str):
    """Delete a memory file."""
    file_path = BASE_DIR / "memory" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    file_path.unlink()
    return {"success": True}


@app.get("/api/files/all-memory-content")
async def get_all_memory_content():
    """Get extracted text from all memory files (for cloud RAG)."""
    ensure_directories()
    memory_dir = BASE_DIR / "memory"
    documents = []

    for f in memory_dir.iterdir():
        if f.is_file():
            doc = {"filename": f.name, "type": f.suffix.lower()}
            if f.suffix.lower() == '.pdf':
                doc["content"] = extract_pdf_text(f)
            elif f.suffix.lower() == '.txt':
                doc["content"] = f.read_text(encoding='utf-8', errors='ignore')
            else:
                continue
            documents.append(doc)

    return documents


# -----------------------------------------------------------------------------
# Images
# -----------------------------------------------------------------------------

@app.get("/api/files/images")
async def list_images():
    """List generated images."""
    ensure_directories()
    images_dir = BASE_DIR / "imagenes"
    files = []
    for f in images_dir.iterdir():
        if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            files.append(FileInfo(
                name=f.name,
                size=f.stat().st_size,
                modified=datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                type=f.suffix.lower()
            ))
    return files


@app.get("/api/files/images/{filename}")
async def get_image(filename: str):
    """Get image as base64."""
    file_path = BASE_DIR / "imagenes" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    return {"filename": filename, "content": content}


@app.post("/api/files/images")
async def upload_image(file: UploadFile = File(...)):
    """Upload/save an image."""
    ensure_directories()
    images_dir = BASE_DIR / "imagenes"
    file_path = images_dir / file.filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {"success": True, "filename": file.filename}


# -----------------------------------------------------------------------------
# Linea Grafica (Brand Images)
# -----------------------------------------------------------------------------

@app.get("/api/files/linea-grafica")
async def list_linea_grafica():
    """List brand images."""
    ensure_directories()
    lg_dir = BASE_DIR / "linea_grafica"
    files = []
    for f in lg_dir.iterdir():
        if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            files.append(FileInfo(
                name=f.name,
                size=f.stat().st_size,
                modified=datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                type=f.suffix.lower()
            ))
    return files


@app.post("/api/files/linea-grafica")
async def upload_linea_grafica(file: UploadFile = File(...)):
    """Upload a brand image."""
    ensure_directories()
    lg_dir = BASE_DIR / "linea_grafica"
    file_path = lg_dir / file.filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {"success": True, "filename": file.filename}


# -----------------------------------------------------------------------------
# Configuration (Prompts, Settings, API Keys)
# -----------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "organization_name": "Mi Organización",
    "system_prompt": """Eres un experto en comunicación y marketing digital especializado en crear contenido para redes sociales.
Tu objetivo es generar publicaciones atractivas, informativas y que generen engagement.
Debes adaptar el tono y estilo según la plataforma (Instagram, Facebook, Twitter/X, LinkedIn).
Usa emojis de forma moderada y estratégica.
Incluye llamados a la acción cuando sea apropiado.""",
    "content_guidelines": """- Mantén un tono profesional pero cercano
- Usa hashtags relevantes (3-5 por publicación)
- Incluye preguntas para fomentar interacción
- Adapta la longitud según la plataforma
- Evita contenido controversial o político""",
    "brand_voice": "Profesional, amigable, innovador",
    "target_audience": "Profesionales y emprendedores de 25-45 años",
    "platforms": ["instagram", "facebook", "linkedin"],
    "posts_per_day": 3,
    "include_images": True,
    "language": "es"
}


@app.get("/api/config")
async def get_config():
    """Get current configuration including prompts."""
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        try:
            saved_config = json.loads(config_path.read_text())
            # Merge with defaults (in case new fields were added)
            config = {**DEFAULT_CONFIG, **saved_config}
            return config
        except:
            pass
    return DEFAULT_CONFIG


@app.post("/api/config")
async def save_config(config: ConfigData):
    """Save configuration including prompts."""
    config_path = BASE_DIR / "config.json"
    # Merge with existing config
    existing = DEFAULT_CONFIG.copy()
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text())
        except:
            pass
    existing.update(config.settings)
    config_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    return {"success": True}


@app.get("/api/config/prompts")
async def get_prompts():
    """Get just the prompts configuration."""
    config = await get_config()
    return {
        "system_prompt": config.get("system_prompt", DEFAULT_CONFIG["system_prompt"]),
        "content_guidelines": config.get("content_guidelines", DEFAULT_CONFIG["content_guidelines"]),
        "brand_voice": config.get("brand_voice", DEFAULT_CONFIG["brand_voice"]),
        "target_audience": config.get("target_audience", DEFAULT_CONFIG["target_audience"]),
    }


@app.post("/api/config/prompts")
async def save_prompts(prompts: dict):
    """Save prompts configuration."""
    config_path = BASE_DIR / "config.json"
    existing = DEFAULT_CONFIG.copy()
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text())
        except:
            pass

    # Update only prompt-related fields
    for key in ["system_prompt", "content_guidelines", "brand_voice", "target_audience"]:
        if key in prompts:
            existing[key] = prompts[key]

    config_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    return {"success": True}


@app.get("/api/config/apikey")
async def get_api_key():
    """Get stored API key (encrypted)."""
    config = await get_config()
    # Return masked key for display
    key = config.get("openai_api_key", "")
    if key:
        return {"has_key": True, "masked": key[:8] + "..." + key[-4:] if len(key) > 12 else "***"}
    return {"has_key": False, "masked": ""}


@app.post("/api/config/apikey")
async def save_api_key(data: dict):
    """Save API key."""
    config_path = BASE_DIR / "config.json"
    existing = DEFAULT_CONFIG.copy()
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text())
        except:
            pass

    existing["openai_api_key"] = data.get("api_key", "")
    config_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    return {"success": True}


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the server."""
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           CAUSA Agent - Local Helper Server               ║
╠═══════════════════════════════════════════════════════════╣
║  Status: Running                                          ║
║  URL: http://127.0.0.1:{PORT}                          ║
║  Health: http://127.0.0.1:{PORT}/api/health            ║
╚═══════════════════════════════════════════════════════════╝
    """)
    print(f"CAUSA Local Helper starting...")
    print(f"Base directory: {BASE_DIR}")
    print(f"Listening on port {PORT}")

    ensure_directories()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")


if __name__ == "__main__":
    main()

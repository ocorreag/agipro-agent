"""
Configuration manager for the CAUSA social media system.
Handles all configuration settings, API keys, and user preferences.
"""

import json
import os
import streamlit as st
from pathlib import Path
from typing import Dict, Any, Optional
import base64
from cryptography.fernet import Fernet
import hashlib

class ConfigManager:
    def __init__(self):
        self.config_dir = Path("src/publicaciones")
        self.config_file = self.config_dir / "app_config.json"
        self.secrets_file = self.config_dir / "secrets.enc"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Default configuration
        self.default_config = {
            "posts_per_day": 3,
            "cleanup_months": 6,
            "days_to_generate": 2,
            "google_sheet_id": "1dL7ngg0P-E9QEiWCDtS5iF2ColQC7YVIM4pbIPQouuE",
            "google_sheet_name": "actividades",
            "collective_topics": "medio ambiente, animalismo, derechos humanos, urbanismo, política, cultura, Usaquén, Bogotá, Colombia",
            "prompts": {
                "system_message": """Eres un experto en comunicación social para el Colectivo Ambiental de Usaca (CAUSA), una organización ambiental y social de Bogotá, Colombia.

Tu misión es crear contenido para redes sociales que:
- Promueva la conciencia ambiental y los derechos de los animales
- Eduque sobre temas sociales y políticos relevantes
- Fomente la participación ciudadana en temas locales de Usaquén y Bogotá
- Mantenga un tono informativo, propositivo y esperanzador
- Use hashtags relevantes en español

El colectivo se enfoca en: medio ambiente, animalismo, derechos humanos, urbanismo sostenible, política local, cultura y memoria histórica.""",
                "news_prompt": "Crea una publicación sobre esta noticia reciente, conectándola con los valores del colectivo y sugiriendo acciones concretas que la comunidad puede tomar.",
                "ephemerides_prompt": "Crea una publicación educativa sobre esta fecha conmemorativa, resaltando su importancia para los temas que trabaja el colectivo.",
                "activity_prompt": "Crea una publicación promocional para esta actividad del colectivo, destacando su impacto comunitario y motivando la participación.",
                "image_prompt": "Describe una imagen para redes sociales que sea visualmente atractiva, use colores naturales (verdes, azules, marrones), incluya elementos de naturaleza urbana, y transmita el mensaje del post de manera clara y positiva."
            }
        }

    def _get_encryption_key(self) -> bytes:
        """Generate encryption key based on system info"""
        # Use a combination of factors to create a unique key per installation
        system_id = f"{os.path.expanduser('~')}-causa-app"
        key_source = hashlib.sha256(system_id.encode()).digest()
        return base64.urlsafe_b64encode(key_source)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            except Exception as e:
                st.error(f"Error loading config: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error saving config: {e}")
            return False

    def save_api_keys(self, api_keys: Dict[str, str]) -> bool:
        """Save API keys encrypted"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)

            # Encrypt the JSON string
            json_data = json.dumps(api_keys).encode()
            encrypted_data = fernet.encrypt(json_data)

            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            st.error(f"Error saving API keys: {e}")
            return False

    def load_api_keys(self) -> Dict[str, str]:
        """Load and decrypt API keys"""
        if not self.secrets_file.exists():
            return {}

        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)

            with open(self.secrets_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            st.error(f"Error loading API keys: {e}")
            return {}

    def update_env_file(self, api_keys: Dict[str, str]):
        """Update the .env file with API keys"""
        env_path = Path("src/.env")

        # Read existing .env content
        existing_vars = {}
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        existing_vars[key] = value

        # Update with new API keys
        existing_vars.update(api_keys)

        # Write back to .env
        try:
            with open(env_path, 'w') as f:
                for key, value in existing_vars.items():
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            st.error(f"Error updating .env file: {e}")
            return False

    def get_setting(self, key: str, default=None):
        """Get a specific setting value"""
        config = self.load_config()
        return config.get(key, default)

    def update_setting(self, key: str, value: Any) -> bool:
        """Update a specific setting"""
        config = self.load_config()
        config[key] = value
        return self.save_config(config)

    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        return self.save_config(self.default_config.copy())
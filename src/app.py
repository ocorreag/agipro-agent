"""
Main Streamlit application for the CAUSA social media management system.
Provides a comprehensive interface for content generation, configuration, and file management.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import os
import hashlib
from PIL import Image
import subprocess
import sys

# Local imports
from config_manager import ConfigManager
from file_manager import FileManager
from publication_editor import PublicationEditor
from csv_manager import PostManager
from path_manager import setup_environment
import agent
import images


# =============================================================================
# Authentication
# =============================================================================

# Credentials (hashed for security)
# In production, use environment variables or a secure vault
AUTH_USERS = {
    "causa": hashlib.sha256("queserasdelmedio1819".encode()).hexdigest()
}


def check_password():
    """Returns True if the user has entered correct credentials."""

    def password_entered():
        """Checks whether password entered is correct."""
        username = st.session_state.get("username", "")
        password = st.session_state.get("password", "")
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if username in AUTH_USERS and AUTH_USERS[username] == password_hash:
            st.session_state["authenticated"] = True
            st.session_state["current_user"] = username
            # Clear password from session state
            del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False
            st.session_state["login_error"] = True

    # First run or not authenticated
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        # Show login form
        st.markdown("""
        <style>
            .login-container {
                max-width: 400px;
                margin: 100px auto;
                padding: 40px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            .login-title {
                text-align: center;
                color: white;
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .login-subtitle {
                text-align: center;
                color: rgba(255,255,255,0.8);
                margin-bottom: 30px;
            }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("# 🌱 CAUSA")
            st.markdown("### Sistema de Gestión de Contenido")
            st.markdown("---")

            st.text_input("Usuario", key="username")
            st.text_input("Contraseña", type="password", key="password")

            if st.button("Iniciar Sesión", type="primary", use_container_width=True):
                password_entered()

            if st.session_state.get("login_error"):
                st.error("❌ Usuario o contraseña incorrectos")
                st.session_state["login_error"] = False

        return False

    return True


def logout():
    """Logout the current user."""
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None
    st.rerun()


# =============================================================================
# Hybrid Mode Detection
# =============================================================================

HYBRID_MODE = os.getenv("CAUSA_MODE", "local").lower() == "hybrid"

# Import bridge only in hybrid mode
if HYBRID_MODE:
    from local_bridge import get_bridge, check_helper_connection, LocalBridge
    _bridge: LocalBridge = None

    def get_app_bridge() -> LocalBridge:
        """Get or create bridge instance for the app."""
        global _bridge
        if _bridge is None:
            _bridge = get_bridge()
        return _bridge


def check_local_helper_status() -> dict:
    """Check Local Helper connection status."""
    if not HYBRID_MODE:
        return {"mode": "local", "connected": True, "message": "Modo local (filesystem directo)"}

    bridge = get_app_bridge()
    connected = bridge.check_connection()

    if connected:
        status = bridge.get_status()
        return {
            "mode": "hybrid",
            "connected": True,
            "message": "Local Helper conectado",
            "details": status
        }
    else:
        return {
            "mode": "hybrid",
            "connected": False,
            "message": "Local Helper no conectado",
            "error": bridge.get_last_error()
        }


# Import agent logger
from agent_logger import get_agent_logger

# Lazy import for chat interface to handle potential dependency issues
_chat_interface_available = None
_chat_import_error = None

def _get_chat_interface():
    """Lazy load chat interface to handle import errors gracefully."""
    global _chat_interface_available, _chat_import_error
    if _chat_interface_available is None:
        try:
            from chat_interface import show_chat_interface
            _chat_interface_available = show_chat_interface
        except ImportError as e:
            _chat_interface_available = False
            _chat_import_error = str(e)
    return _chat_interface_available, _chat_import_error

# Page configuration
st.set_page_config(
    page_title="CAUSA - Gestión de Contenido Social",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 3px solid #4CAF50;
        margin-bottom: 2rem;
    }
    .sidebar-section {
        padding: 1rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .stat-card {
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        background: #f8f9fa;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        padding: 0.75rem;
        color: #155724;
        margin: 1rem 0;
    }
    .warning-message {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 4px;
        padding: 0.75rem;
        color: #856404;
        margin: 1rem 0;
    }
    .stButton > button {
        width: 100%;
    }
    .upload-section {
        border: 2px dashed #ccc;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

class CausaApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.file_manager = FileManager()
        self.publication_editor = PublicationEditor()
        self.post_manager = PostManager()

        # Initialize session state
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state variables"""
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 'dashboard'
        if 'api_keys_configured' not in st.session_state:
            api_keys = self.config_manager.load_api_keys()
            st.session_state['api_keys_configured'] = bool(api_keys.get('OPENAI_API_KEY'))

    def run(self):
        """Main application entry point"""
        self._show_sidebar()
        self._show_main_content()

    def _show_sidebar(self):
        """Show sidebar navigation and quick stats"""
        with st.sidebar:
            st.markdown('<div class="main-header">', unsafe_allow_html=True)
            st.title("🌱 CAUSA")
            st.caption("Gestión de Contenido Social")
            st.markdown('</div>', unsafe_allow_html=True)

            # Show Local Helper connection status in hybrid mode
            if HYBRID_MODE:
                helper_status = check_local_helper_status()
                if helper_status["connected"]:
                    st.success("🔗 Local Helper conectado")
                else:
                    st.error("⚠️ Local Helper desconectado")
                    st.caption("Ejecute el Local Helper para guardar archivos")

            # Navigation
            st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
            st.subheader("🧭 Navegación")

            pages = {
                'dashboard': '🏠 Dashboard',
                'chat': '💬 Chat con Agente',
                'generate': '✨ Generar (Legacy)',
                'publications': '📝 Publicaciones',
                'files': '📁 Archivos',
                'config': '⚙️ Configuración'
            }

            for key, label in pages.items():
                if st.button(label, key=f"nav_{key}"):
                    st.session_state['current_page'] = key
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            # Quick stats
            self._show_quick_stats()

            # User info and logout
            st.markdown("---")
            current_user = st.session_state.get("current_user", "Usuario")
            st.caption(f"👤 Conectado como: **{current_user}**")
            if st.button("🚪 Cerrar Sesión", key="logout_btn"):
                logout()

            # System status
            self._show_system_status()

    def _show_quick_stats(self):
        """Show quick statistics in sidebar"""
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📊 Estadísticas")

        try:
            stats = self.post_manager.get_stats()
            file_stats = self.file_manager.get_file_stats()

            st.markdown(f"""
            <div class="stat-card">
                <strong>{stats['total_drafts']}</strong><br>
                <small>Borradores</small>
            </div>
            <div class="stat-card">
                <strong>{stats['total_published']}</strong><br>
                <small>Publicados</small>
            </div>
            <div class="stat-card">
                <strong>{file_stats['memory_files']}</strong><br>
                <small>Docs Memoria</small>
            </div>
            <div class="stat-card">
                <strong>{file_stats['linea_grafica_files']}</strong><br>
                <small>Imágenes LG</small>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error loading stats: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

    def _show_system_status(self):
        """Show system status indicators"""
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("🔧 Estado del Sistema")

        # API Key status
        api_status = "🟢 Configurada" if st.session_state.get('api_keys_configured') else "🔴 Sin configurar"
        st.write(f"**API Key OpenAI:** {api_status}")

        # Memory files status
        memory_files = self.file_manager.get_memory_files()
        memory_status = "🟢 Disponibles" if memory_files else "🟡 Vacía"
        st.write(f"**Memoria:** {memory_status}")

        # Linea grafica status
        lg_files = self.file_manager.get_linea_grafica_files()
        lg_status = "🟢 Disponibles" if lg_files else "🟡 Vacía"
        st.write(f"**Línea Gráfica:** {lg_status}")

        st.markdown('</div>', unsafe_allow_html=True)

    def _show_main_content(self):
        """Show main content area based on current page"""
        current_page = st.session_state.get('current_page', 'dashboard')

        if current_page == 'dashboard':
            self._show_dashboard()
        elif current_page == 'chat':
            self._show_chat()
        elif current_page == 'generate':
            self._show_generate_content()
        elif current_page == 'publications':
            self._show_publications()
        elif current_page == 'files':
            self._show_files()
        elif current_page == 'config':
            self._show_configuration()

    def _show_chat(self):
        """Show the chat interface with the CAUSA agent"""
        chat_interface, error = _get_chat_interface()

        if chat_interface:
            chat_interface()
        else:
            st.title("💬 Chat con Agente")
            st.error(f"""
            **Error cargando el chat:**

            {error}

            **Solución sugerida:**

            El error parece estar relacionado con la biblioteca `lxml`.
            Ejecuta estos comandos en tu terminal para reinstalar:

            ```bash
            pip uninstall lxml ddgs
            pip install --no-cache-dir lxml ddgs
            ```

            Si estás en un Mac con chip M1/M2, también puedes probar:
            ```bash
            pip install --no-binary :all: lxml
            ```

            Mientras tanto, puedes usar el generador legacy desde "Generar (Legacy)" en el menú.
            """)

    def _show_dashboard(self):
        """Show dashboard overview"""
        st.markdown('<div class="main-header">', unsafe_allow_html=True)
        st.title("🏠 Dashboard - CAUSA")
        st.write("Colectivo Ambiental de Usaca - Gestión de Contenido Social")
        st.markdown('</div>', unsafe_allow_html=True)

        # Show Local Helper warning in hybrid mode
        if HYBRID_MODE:
            helper_status = check_local_helper_status()
            if not helper_status["connected"]:
                st.warning("""
                ⚠️ **Local Helper no conectado**

                Para usar todas las funciones, necesitas ejecutar el Local Helper en tu computadora:

                1. Descarga y extrae el Local Helper
                2. Abre una terminal y ejecuta: `python server.py`
                3. Mantén la terminal abierta mientras usas la aplicación

                Sin el Local Helper:
                - ❌ No se pueden cargar documentos de memoria (RAG)
                - ❌ No se pueden guardar publicaciones
                - ❌ No se pueden usar imágenes de marca
                """)

        # Welcome and status
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("👋 Bienvenido")
            st.write("""
            Esta aplicación te permite gestionar todo el contenido social del colectivo CAUSA:
            - 💬 **Chat con el Agente** - Crea contenido conversando con IA
            - 📝 **Editar publicaciones** antes de publicar
            - 📁 **Gestionar archivos** de memoria y línea gráfica
            - ⚙️ **Configurar** prompts, API keys y parámetros
            """)

            # Highlight the new Chat feature
            st.info("""
            **Nuevo: Agente Conversacional**

            Ahora puedes crear contenido conversando con el agente. El agente puede:
            - Buscar noticias y efemérides con sus propias consultas
            - Revisar publicaciones anteriores para evitar repeticiones
            - Crear posts flexiblemente (1 o muchos)
            - Generar imágenes solo cuando las apruebes
            """)

            # Quick actions
            st.subheader("🚀 Acciones Rápidas")

            col_a, col_b, col_c, col_d = st.columns(4)

            with col_a:
                if st.button("💬 Chat con Agente", type="primary"):
                    st.session_state['current_page'] = 'chat'
                    st.rerun()

            with col_b:
                if st.button("📝 Ver Publicaciones"):
                    st.session_state['current_page'] = 'publications'
                    st.rerun()

            with col_c:
                if st.button("📁 Archivos"):
                    st.session_state['current_page'] = 'files'
                    st.rerun()

            with col_d:
                if st.button("⚙️ Configuración"):
                    st.session_state['current_page'] = 'config'
                    st.rerun()

        with col2:
            st.subheader("📈 Actividad Reciente")

            try:
                recent_posts = self.post_manager.get_draft_posts()
                if recent_posts:
                    st.write("**Últimas publicaciones:**")
                    for post in recent_posts[-5:]:  # Last 5 posts
                        st.write(f"• {post['fecha']}: {post['titulo'][:30]}...")
                else:
                    st.info("No hay publicaciones recientes")
            except Exception as e:
                st.error(f"Error loading recent activity: {e}")

        # System warnings
        if not st.session_state.get('api_keys_configured'):
            st.warning("⚠️ **API Key no configurada.** Ve a Configuración para añadir tu clave de OpenAI.")

    def _show_generate_content(self):
        """Show content generation interface"""
        st.title("✨ Generar Nuevo Contenido")

        # Check if system is ready
        if not st.session_state.get('api_keys_configured'):
            st.error("❌ **API Key de OpenAI requerida.** Configura tu API key de OpenAI en la sección Configuración.")
            return

        # Generation parameters
        st.subheader("📋 Parámetros de Generación")

        col1, col2, col3 = st.columns(3)

        with col1:
            days_to_generate = st.number_input(
                "📅 Días desde hoy:",
                min_value=1,
                max_value=30,
                value=self.config_manager.get_setting('days_to_generate', 2),
                help="Número de días desde hoy para generar contenido"
            )

        with col2:
            posts_per_day = st.number_input(
                "📊 Posts por día:",
                min_value=1,
                max_value=6,
                value=self.config_manager.get_setting('posts_per_day', 3)
            )

        with col3:
            generate_images = st.checkbox(
                "🖼️ Generar imágenes",
                value=True,
                help="Generar imágenes con DALL-E 3"
            )

        # Advanced options
        with st.expander("🔧 Opciones Avanzadas"):
            collective_topics = st.text_area(
                "🏷️ Temas del Colectivo:",
                value=self.config_manager.get_setting('collective_topics', ''),
                height=100,
                help="Temas principales del colectivo separados por comas"
            )

            custom_prompts = st.checkbox(
                "📝 Usar prompts personalizados",
                help="Usar los prompts configurados en lugar de los predeterminados"
            )

        # Generation button
        st.divider()

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("🚀 Generar Contenido", type="primary", use_container_width=True):
                # Save current settings
                self.config_manager.update_setting('days_to_generate', days_to_generate)
                self.config_manager.update_setting('posts_per_day', posts_per_day)

                if collective_topics.strip():
                    self.config_manager.update_setting('collective_topics', collective_topics)

                # Run generation
                self._run_content_generation(days_to_generate, posts_per_day, generate_images)

    def _run_content_generation(self, days: int, posts_per_day: int, generate_images: bool):
        """Run the content generation process"""
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Step 1: Generate content
            status_text.text("🤖 Generando contenido con IA...")
            progress_bar.progress(20)

            # Setup directories
            agent.setup_directories()

            # Generate calendar
            calendar = agent.generate_social_media_calendar(days=days, posts_per_day=posts_per_day)

            if not calendar:
                st.error("❌ No se pudo generar contenido. Verifica la configuración de API keys.")
                return

            progress_bar.progress(50)

            # Step 2: Save posts
            status_text.text("💾 Guardando publicaciones...")

            new_posts = []
            for post in calendar:
                new_posts.append({
                    'fecha': post['fecha'],
                    'titulo': post['titulo'],
                    'imagen': post['imagen'],
                    'descripcion': post['descripcion']
                })

            self.post_manager.save_draft_posts(new_posts)
            progress_bar.progress(70)

            # Step 3: Generate images if requested
            if generate_images:
                status_text.text("🎨 Generando imágenes...")

                csv_file = self.post_manager.export_for_image_generation()
                if csv_file:
                    try:
                        image_generator = images.SocialMediaImageGenerator()
                        image_generator.process_calendar(csv_file)

                        # Update posts with image paths
                        df_with_images = pd.read_csv(csv_file)
                        for _, row in df_with_images.iterrows():
                            fecha = row['fecha']
                            titulo = row['titulo']

                            image_path = None
                            # Check for universal image first, then fallback to old column names
                            if 'universal_image' in df_with_images.columns and pd.notna(row['universal_image']):
                                image_path = row['universal_image']
                            else:
                                # Fallback to old column names for backward compatibility
                                for col in ['instagram_image', 'facebook_image']:
                                    if col in df_with_images.columns and pd.notna(row[col]):
                                        image_path = row[col]
                                        break

                            if image_path:
                                self.post_manager.update_image_path(fecha, titulo, image_path)

                    except Exception as e:
                        st.warning(f"⚠️ Error generando imágenes: {str(e)}")

            progress_bar.progress(100)
            status_text.text("✅ ¡Generación completada!")

            # Show success message
            st.success(f"""
            ✅ **Contenido generado exitosamente!**

            📊 **Resumen:**
            - {len(new_posts)} publicaciones generadas
            - {days} días de contenido
            - {posts_per_day} posts por día
            {'- Imágenes generadas con DALL-E 3' if generate_images else '- Sin generar imágenes'}

            💡 Ve a la sección **Publicaciones** para revisar y editar el contenido antes de publicar.
            """)

        except Exception as e:
            st.error(f"❌ Error en la generación: {str(e)}")
            progress_bar.progress(0)
            status_text.text("❌ Error en la generación")

    def _show_publications(self):
        """Show publications management interface"""
        self.publication_editor.show_publications_interface()

    def _show_files(self):
        """Show file management interface"""
        st.title("📁 Gestión de Archivos")

        # File tabs
        tab1, tab2, tab3 = st.tabs(["📚 Memoria", "🎨 Línea Gráfica", "🖼️ Imágenes Generadas"])

        with tab1:
            self._show_memory_files()

        with tab2:
            self._show_linea_grafica_files()

        with tab3:
            self._show_generated_images()

    def _show_memory_files(self):
        """Show memory files management"""
        st.subheader("📚 Documentos de Memoria")
        st.write("Archivos PDF y texto que contienen la historia e ideología del colectivo.")

        # Upload section
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.write("**📤 Subir nuevos documentos**")

        uploaded_files = st.file_uploader(
            "Selecciona archivos (PDF, TXT):",
            type=['pdf', 'txt', 'md'],
            accept_multiple_files=True,
            key="memory_upload"
        )

        if uploaded_files:
            if st.button("📤 Subir Archivos", type="primary"):
                success_count = 0
                for file in uploaded_files:
                    if self.file_manager.upload_memory_file(file):
                        success_count += 1

                if success_count > 0:
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # Current files
        st.subheader("📋 Archivos Actuales")

        memory_files = self.file_manager.get_memory_files()

        if not memory_files:
            st.info("📝 No hay documentos de memoria. Sube algunos archivos PDF o TXT.")
            return

        # File list with selection
        selected_files = []

        col1, col2 = st.columns([0.1, 0.9])

        with col1:
            st.write("**Sel.**")

        with col2:
            st.write("**Archivo | Tamaño | Modificado | Tipo**")

        for file_info in memory_files:
            col1, col2 = st.columns([0.1, 0.9])

            with col1:
                if st.checkbox("Select", key=f"memory_{file_info['name']}", label_visibility="collapsed"):
                    selected_files.append(file_info['path'])

            with col2:
                col_a, col_b, col_c, col_d = st.columns([3, 1, 2, 1])

                with col_a:
                    st.write(file_info['name'])
                with col_b:
                    st.write(file_info['size'])
                with col_c:
                    st.write(file_info['modified'])
                with col_d:
                    st.write(file_info['type'])

        # Bulk operations
        if selected_files:
            st.subheader("🗂️ Operaciones en Lote")

            if st.button("🗑️ Eliminar Seleccionados", type="secondary"):
                success, total = self.file_manager.delete_multiple_files(selected_files)
                if success > 0:
                    st.rerun()

    def _show_linea_grafica_files(self):
        """Show linea grafica files management"""
        st.subheader("🎨 Línea Gráfica")
        st.write("Imágenes que definen el estilo visual del colectivo.")

        # Upload section
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.write("**📤 Subir nuevas imágenes**")

        uploaded_images = st.file_uploader(
            "Selecciona imágenes:",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp'],
            accept_multiple_files=True,
            key="lg_upload"
        )

        if uploaded_images:
            if st.button("📤 Subir Imágenes", type="primary"):
                success_count = 0
                for image in uploaded_images:
                    if self.file_manager.upload_linea_grafica_file(image):
                        success_count += 1

                if success_count > 0:
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # Current images
        st.subheader("🖼️ Imágenes Actuales")

        lg_files = self.file_manager.get_linea_grafica_files()

        if not lg_files:
            st.info("🎨 No hay imágenes en la línea gráfica. Sube algunas imágenes.")
            return

        # Display images in grid
        selected_images = []

        # Selection and bulk operations
        st.subheader("🗂️ Selección")

        cols = st.columns(4)

        for i, file_info in enumerate(lg_files):
            col = cols[i % 4]

            with col:
                # Checkbox for selection
                if st.checkbox(f"Seleccionar", key=f"lg_sel_{file_info['name']}"):
                    selected_images.append(file_info['path'])

                st.write(f"**{file_info['name'][:20]}...**" if len(file_info['name']) > 20 else f"**{file_info['name']}**")
                st.write(f"📏 {file_info['size']} | 📅 {file_info['modified']}")

        # Bulk delete
        if selected_images:
            if st.button("🗑️ Eliminar Seleccionadas", type="secondary"):
                success, total = self.file_manager.delete_multiple_files(selected_images)
                if success > 0:
                    st.rerun()

    def _show_generated_images(self):
        """Show generated images with preview and management"""
        st.subheader("🖼️ Imágenes Generadas")
        st.write("Imágenes creadas automáticamente por DALL-E 3 para las publicaciones.")

        generated_images = self.file_manager.get_generated_images()

        if not generated_images:
            st.info("🎨 No hay imágenes generadas. Crea contenido con imágenes primero.")
            return

        # Display images with previews
        cols = st.columns(3)

        for i, image_info in enumerate(generated_images):
            col = cols[i % 3]

            with col:
                st.write(f"**{image_info['name']}**")

                # Show image preview
                try:
                    image = Image.open(image_info['path'])
                    st.image(image, width="stretch")
                except Exception as e:
                    st.error(f"Error loading image: {e}")

                # Image info
                st.write(f"📏 {image_info['size']}")
                st.write(f"📅 {image_info['modified']}")

                # Actions
                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("➕ A Línea Gráfica", key=f"add_lg_{i}", type="secondary"):
                        success = self.file_manager.copy_generated_image_to_linea_grafica(image_info['path'])
                        if success:
                            st.rerun()

                with col_b:
                    if st.button("🗑️ Eliminar", key=f"del_gen_{i}", type="secondary"):
                        success = self.file_manager.delete_file(image_info['path'])
                        if success:
                            st.rerun()

                st.divider()

    def _show_configuration(self):
        """Show configuration interface"""
        st.title("⚙️ Configuración")

        # Configuration tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔑 API Keys", "📋 General", "💬 Prompts", "📊 Google Sheets", "📜 Logs"])

        with tab1:
            self._show_api_config()

        with tab2:
            self._show_general_config()

        with tab3:
            self._show_prompts_config()

        with tab4:
            self._show_sheets_config()

        with tab5:
            self._show_agent_logs()

    def _show_agent_logs(self):
        """Show agent activity logs"""
        st.subheader("📜 Registro de Actividad del Agente")

        agent_logger = get_agent_logger()

        # Summary
        summary = agent_logger.get_summary()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Acciones", summary["total_actions"])
        with col2:
            st.metric("Exitosas", summary["success_count"])
        with col3:
            st.metric("Errores", summary["error_count"])
        with col4:
            st.metric("Duración", f"{summary['duration_seconds']:.0f}s")

        # Action breakdown
        if summary["action_breakdown"]:
            st.subheader("Desglose por Tipo")
            cols = st.columns(len(summary["action_breakdown"]))
            for i, (action_type, count) in enumerate(summary["action_breakdown"].items()):
                with cols[i % len(cols)]:
                    st.metric(action_type, count)

        st.divider()

        # Recent actions
        st.subheader("Acciones Recientes")

        # Refresh button
        if st.button("🔄 Actualizar Logs"):
            st.rerun()

        actions = agent_logger.get_recent_actions(limit=50)

        if not actions:
            st.info("No hay acciones registradas aún. El agente registrará sus acciones cuando genere contenido.")
        else:
            for action in reversed(actions):
                # Color based on success
                if action["success"]:
                    icon = "✅" if action["action_type"] != "init" else "🚀"
                else:
                    icon = "❌"

                # Format timestamp
                timestamp = action["timestamp"].split("T")[1].split(".")[0] if "T" in action["timestamp"] else action["timestamp"]

                with st.expander(f"{icon} [{timestamp}] {action['action_type']}: {action['description']}", expanded=False):
                    st.write(f"**Tipo:** {action['action_type']}")
                    st.write(f"**Descripción:** {action['description']}")

                    if action.get("duration_ms"):
                        st.write(f"**Duración:** {action['duration_ms']:.0f}ms")

                    if action.get("details"):
                        st.write("**Detalles:**")
                        st.json(action["details"])

                    if action.get("error"):
                        st.error(f"**Error:** {action['error']}")

        # Clear logs button
        st.divider()
        if st.button("🗑️ Limpiar Logs", type="secondary"):
            agent_logger.clear()
            st.success("Logs limpiados")
            st.rerun()

    def _show_api_config(self):
        """Show API keys configuration"""
        st.subheader("🔑 Configuración de API Key")

        current_keys = self.config_manager.load_api_keys()

        # API Key form
        openai_key = st.text_input(
            "🤖 OpenAI API Key:",
            value=current_keys.get('OPENAI_API_KEY', ''),
            type="password",
            help="Necesaria para generar contenido con LLM y imágenes con DALL-E 3"
        )


        if st.button("💾 Guardar API Key", type="primary"):
            api_keys = {}

            if openai_key.strip():
                api_keys['OPENAI_API_KEY'] = openai_key.strip()


            if api_keys:
                # Save encrypted keys
                if self.config_manager.save_api_keys(api_keys):
                    # Update .env file
                    if self.config_manager.update_env_file(api_keys):
                        st.success("✅ API Key guardada correctamente")
                        st.session_state['api_keys_configured'] = True
                        st.rerun()
                    else:
                        st.error("❌ Error actualizando archivo .env")
                else:
                    st.error("❌ Error guardando API key")
            else:
                st.warning("⚠️ No se proporcionó API key")

        # Test connection
        if current_keys:
            st.subheader("🧪 Probar Conexión")

            if current_keys.get('OPENAI_API_KEY') and st.button("🧪 Probar OpenAI"):
                # Test OpenAI connection
                # Note: Actual testing would require importing and testing the API
                st.info("Funcionalidad de prueba en desarrollo")

    def _show_general_config(self):
        """Show general configuration settings"""
        st.subheader("📋 Configuración General")

        config = self.config_manager.load_config()

        # General settings
        posts_per_day = st.number_input(
            "📊 Posts por día:",
            min_value=1,
            max_value=6,
            value=config.get('posts_per_day', 3)
        )

        days_to_generate = st.number_input(
            "📅 Días a generar por defecto:",
            min_value=1,
            max_value=30,
            value=config.get('days_to_generate', 2)
        )

        cleanup_months = st.number_input(
            "🧹 Limpieza automática (meses):",
            min_value=1,
            max_value=12,
            value=config.get('cleanup_months', 6),
            help="Eliminar archivos automáticamente después de X meses"
        )

        collective_topics = st.text_area(
            "🏷️ Temas del Colectivo:",
            value=config.get('collective_topics', ''),
            height=100,
            help="Temas principales separados por comas"
        )

        if st.button("💾 Guardar Configuración General", type="primary"):
            config.update({
                'posts_per_day': posts_per_day,
                'days_to_generate': days_to_generate,
                'cleanup_months': cleanup_months,
                'collective_topics': collective_topics
            })

            if self.config_manager.save_config(config):
                st.success("✅ Configuración guardada")
                st.rerun()
            else:
                st.error("❌ Error guardando configuración")

    def _show_prompts_config(self):
        """Show prompts configuration"""
        st.subheader("💬 Configuración de Prompts")

        config = self.config_manager.load_config()
        prompts = config.get('prompts', {})

        # System message
        system_message = st.text_area(
            "🧠 Mensaje del Sistema:",
            value=prompts.get('system_message', ''),
            height=150,
            help="Prompt principal que define el comportamiento del AI"
        )

        # Specific prompts
        news_prompt = st.text_area(
            "📰 Prompt para Noticias:",
            value=prompts.get('news_prompt', ''),
            height=100
        )

        ephemerides_prompt = st.text_area(
            "📅 Prompt para Efemérides:",
            value=prompts.get('ephemerides_prompt', ''),
            height=100
        )

        activity_prompt = st.text_area(
            "🎯 Prompt para Actividades:",
            value=prompts.get('activity_prompt', ''),
            height=100
        )

        image_prompt = st.text_area(
            "🖼️ Prompt para Imágenes:",
            value=prompts.get('image_prompt', ''),
            height=100
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Guardar Prompts", type="primary"):
                config['prompts'] = {
                    'system_message': system_message,
                    'news_prompt': news_prompt,
                    'ephemerides_prompt': ephemerides_prompt,
                    'activity_prompt': activity_prompt,
                    'image_prompt': image_prompt
                }

                if self.config_manager.save_config(config):
                    st.success("✅ Prompts guardados")
                else:
                    st.error("❌ Error guardando prompts")

        with col2:
            if st.button("🔄 Restaurar Predeterminados", type="secondary"):
                if self.config_manager.reset_to_defaults():
                    st.success("✅ Prompts restaurados a valores predeterminados")
                    st.rerun()
                else:
                    st.error("❌ Error restaurando prompts")

    def _show_sheets_config(self):
        """Show Google Sheets configuration"""
        st.subheader("📊 Configuración de Google Sheets")

        config = self.config_manager.load_config()

        # Google Sheets settings
        sheet_id = st.text_input(
            "📋 ID de Google Sheet:",
            value=config.get('google_sheet_id', ''),
            help="ID del documento de Google Sheets (parte de la URL)"
        )

        sheet_name = st.text_input(
            "📄 Nombre de la Hoja:",
            value=config.get('google_sheet_name', 'Hoja 1'),
            help="Nombre de la hoja específica dentro del documento"
        )

        st.info("""
        **💡 Instrucciones:**

        1. Copia el ID de tu Google Sheet desde la URL:
           `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`

        2. Asegúrate de que la hoja sea **pública** o que el sistema tenga acceso

        3. La hoja debe contener las actividades del colectivo con formato adecuado
        """)

        if st.button("💾 Guardar Configuración Sheets", type="primary"):
            config.update({
                'google_sheet_id': sheet_id,
                'google_sheet_name': sheet_name
            })

            if self.config_manager.save_config(config):
                st.success("✅ Configuración de Sheets guardada")
            else:
                st.error("❌ Error guardando configuración")

        # Test connection
        if sheet_id and st.button("🧪 Probar Conexión"):
            st.info("Funcionalidad de prueba en desarrollo")


def main():
    """Main entry point"""
    # Check authentication first
    if not check_password():
        return  # Stop here if not authenticated

    # Setup environment and paths
    setup_environment()

    app = CausaApp()
    app.run()


if __name__ == "__main__":
    main()

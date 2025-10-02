import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image
import shutil
import tempfile
from io import BytesIO

# Local imports
from csv_manager import PostManager
import agent
import images

# Configure Streamlit page
st.set_page_config(
    page_title="CAUSA - Social Media Content Manager",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    padding: 1rem 0;
    border-bottom: 2px solid #4CAF50;
    margin-bottom: 2rem;
}
.config-section {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
}
.post-card {
    border: 1px solid #ddd;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    background-color: white;
}
.success-message {
    color: #28a745;
    font-weight: bold;
}
.error-message {
    color: #dc3545;
    font-weight: bold;
}
.publish-button {
    background-color: #28a745;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
}
.draft-badge {
    background-color: #ffc107;
    color: #212529;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
}
.published-badge {
    background-color: #28a745;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

class StreamlitConfig:
    """Configuration manager for the Streamlit app"""

    def __init__(self):
        self.config_file = Path("streamlit_config.json")
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = self.get_default_config()

    def get_default_config(self):
        """Default configuration"""
        return {
            "system_prompt": "",
            "openai_api_key": "",
            "google_sheet_id": "",
            "google_sheet_name": "",
            "generation_days": 2,
            "topics": "medio ambiente, animalismo, derechos humanos, urbanismo, política, cultura, Usaquén, Bogotá, Colombia"
        }

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

def resize_image_for_openai(image_file, max_size_mb=20):
    """Resize image if it's too large for OpenAI processing"""
    try:
        img = Image.open(image_file)

        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')

        # Calculate current file size
        img_buffer = BytesIO()
        img.save(img_buffer, format='JPEG', quality=95)
        current_size_mb = len(img_buffer.getvalue()) / (1024 * 1024)

        # If image is already small enough, return as is
        if current_size_mb <= max_size_mb:
            return img

        # Calculate resize ratio
        ratio = (max_size_mb / current_size_mb) ** 0.5
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)

        # Resize image
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return resized_img

    except Exception as e:
        st.error(f"Error resizing image: {e}")
        return None

def main():
    # Initialize config and post manager
    config = StreamlitConfig()
    pm = PostManager()

    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🌱 CAUSA - Social Media Content Manager")
        st.markdown("*Gestión integral de contenido para redes sociales*")
    with col2:
        st.image("https://via.placeholder.com/100x100/4CAF50/white?text=CAUSA", width=100)
    st.markdown('</div>', unsafe_allow_html=True)

    # Sidebar Navigation
    st.sidebar.title("🗂️ Navegación")
    page = st.sidebar.selectbox(
        "Seleccionar Sección",
        ["📊 Dashboard", "⚙️ Configuración", "📁 Archivos", "✍️ Generar Contenido", "📝 Gestionar Publicaciones"]
    )

    # Dashboard
    if page == "📊 Dashboard":
        show_dashboard(pm, config)

    # Configuration
    elif page == "⚙️ Configuración":
        show_configuration(config, pm)

    # File Management
    elif page == "📁 Archivos":
        show_file_management()

    # Content Generation
    elif page == "✍️ Generar Contenido":
        show_content_generation(pm, config)

    # Post Management
    elif page == "📝 Gestionar Publicaciones":
        show_post_management(pm)

def show_dashboard(pm, config):
    """Show dashboard with statistics and overview"""
    st.header("📊 Dashboard")

    # Get statistics
    stats = pm.get_stats()

    # Metrics cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📝 Borradores",
            value=stats['total_drafts'],
            delta=f"Configurado: {stats['settings']['posts_per_day']}/día"
        )

    with col2:
        st.metric(
            label="✅ Publicados",
            value=stats['total_published'],
            delta=None
        )

    with col3:
        st.metric(
            label="📅 Archivos CSV",
            value=stats['draft_files'],
            delta=None
        )

    with col4:
        memory_files = len(list(Path("memory").glob("*.pdf"))) + len(list(Path("memory").glob("*.txt")))
        st.metric(
            label="🧠 Archivos Memoria",
            value=memory_files,
            delta=None
        )

    st.divider()

    # Recent activity
    st.subheader("🕐 Actividad Reciente")

    drafts = pm.get_draft_posts()
    if drafts:
        recent_drafts = sorted(drafts, key=lambda x: x.get('created_at', ''), reverse=True)[:5]

        for draft in recent_drafts:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{draft['titulo'][:60]}...**")
                with col2:
                    st.write(f"📅 {draft['fecha']}")
                with col3:
                    st.markdown('<span class="draft-badge">BORRADOR</span>', unsafe_allow_html=True)
    else:
        st.info("No hay borradores recientes. ¡Genera contenido nuevo!")

    # Configuration status
    st.divider()
    st.subheader("🔧 Estado de Configuración")

    config_status = []
    config_status.append(("Sistema OpenAI", "✅" if config.get("openai_api_key") else "❌"))
    config_status.append(("Prompt del Sistema", "✅" if config.get("system_prompt") else "❌"))
    config_status.append(("Google Sheets", "✅" if config.get("google_sheet_id") else "❌"))

    for item, status in config_status:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(item)
        with col2:
            st.write(status)

def show_configuration(config, pm):
    """Show configuration management interface"""
    st.header("⚙️ Configuración del Sistema")

    st.markdown("""
    Configura los parámetros principales del sistema. Los cambios se guardan automáticamente.
    """)

    # OpenAI Configuration
    with st.expander("🤖 Configuración de OpenAI", expanded=True):
        openai_key = st.text_input(
            "API Key de OpenAI",
            value=config.get("openai_api_key", ""),
            type="password",
            help="Tu API key de OpenAI para generación de contenido e imágenes"
        )
        if openai_key != config.get("openai_api_key", ""):
            config.set("openai_api_key", openai_key)
            st.success("✅ API Key actualizada")

    # System Prompt Configuration
    with st.expander("📝 Prompt del Sistema", expanded=True):
        system_prompt = st.text_area(
            "Contexto de la Organización",
            value=config.get("system_prompt", ""),
            height=150,
            help="Describe tu organización, valores, temas de interés, etc. Este contexto se usará para generar contenido relevante.",
            placeholder="Ejemplo: Somos el Colectivo Ambiental de Usaca - CAUSA, trabajamos en temas de medio ambiente, animalismo, derechos humanos, educación popular y cultura en Bogotá, Colombia..."
        )
        if system_prompt != config.get("system_prompt", ""):
            config.set("system_prompt", system_prompt)
            st.success("✅ Prompt del sistema actualizado")

    # Google Sheets Configuration
    with st.expander("📊 Configuración de Google Sheets", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            sheet_id = st.text_input(
                "ID de Google Sheet",
                value=config.get("google_sheet_id", ""),
                help="ID de tu Google Sheet (se encuentra en la URL)"
            )
            if sheet_id != config.get("google_sheet_id", ""):
                config.set("google_sheet_id", sheet_id)
                st.success("✅ Sheet ID actualizado")

        with col2:
            sheet_name = st.text_input(
                "Nombre de la Hoja",
                value=config.get("google_sheet_name", ""),
                placeholder="publicaciones",
                help="Nombre de la hoja dentro del spreadsheet"
            )
            if sheet_name != config.get("google_sheet_name", ""):
                config.set("google_sheet_name", sheet_name)
                st.success("✅ Nombre de hoja actualizado")

    # Content Generation Settings
    with st.expander("🎯 Configuración de Generación", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            generation_days = st.number_input(
                "Días a generar",
                min_value=1,
                max_value=30,
                value=config.get("generation_days", 2),
                help="Número de días hacia el futuro para generar contenido"
            )
            if generation_days != config.get("generation_days", 2):
                config.set("generation_days", generation_days)
                st.success("✅ Días de generación actualizados")

        with col2:
            # Get posts per day from PostManager settings
            current_posts_per_day = pm.get_setting("posts_per_day", 3)
            posts_per_day = st.number_input(
                "Posts por día",
                min_value=1,
                max_value=10,
                value=int(current_posts_per_day),
                help="Número de publicaciones a generar por día"
            )
            if posts_per_day != int(current_posts_per_day):
                pm.update_setting("posts_per_day", posts_per_day)
                st.success("✅ Posts por día actualizados")

    # Topics Configuration
    with st.expander("🏷️ Temas de Interés", expanded=False):
        topics = st.text_area(
            "Temas principales",
            value=config.get("topics", ""),
            height=100,
            help="Lista de temas separados por comas que interesan a tu organización",
            placeholder="medio ambiente, animalismo, derechos humanos, urbanismo, política, cultura"
        )
        if topics != config.get("topics", ""):
            config.set("topics", topics)
            st.success("✅ Temas actualizados")

    st.divider()

    # Test Configuration
    st.subheader("🧪 Probar Configuración")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Probar OpenAI"):
            if openai_key:
                try:
                    os.environ['OPENAI_API_KEY'] = openai_key
                    from openai import OpenAI
                    client = OpenAI()
                    # Simple test
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                    st.success("✅ Conexión con OpenAI exitosa")
                except Exception as e:
                    st.error(f"❌ Error conectando con OpenAI: {e}")
            else:
                st.warning("⚠️ Ingresa una API Key primero")

    with col2:
        if st.button("📊 Probar Google Sheets"):
            if sheet_id and sheet_name:
                st.info("🔄 Función de prueba de Google Sheets pendiente de implementar")
            else:
                st.warning("⚠️ Completa la configuración de Google Sheets primero")

def show_file_management():
    """Show file management interface for memory and graphics"""
    st.header("📁 Gestión de Archivos")

    tab1, tab2 = st.tabs(["🧠 Archivos de Memoria", "🎨 Línea Gráfica"])

    with tab1:
        st.subheader("Archivos para RAG (Memoria Organizacional)")
        st.markdown("*Sube documentos PDF y TXT que contengan información sobre tu organización*")

        memory_dir = Path("memory")
        memory_dir.mkdir(exist_ok=True)

        # Upload new files
        uploaded_files = st.file_uploader(
            "Subir archivos de memoria",
            type=['pdf', 'txt'],
            accept_multiple_files=True,
            help="Documentos que contienen información sobre tu organización, valores, historia, etc."
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = memory_dir / uploaded_file.name
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"✅ Archivo guardado: {uploaded_file.name}")

        # List existing files
        st.divider()
        st.subheader("📄 Archivos Existentes")

        memory_files = list(memory_dir.glob("*.pdf")) + list(memory_dir.glob("*.txt"))

        if memory_files:
            for file_path in memory_files:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.write(f"📄 {file_path.name}")

                with col2:
                    file_size = file_path.stat().st_size / (1024 * 1024)  # MB
                    st.write(f"{file_size:.1f} MB")

                with col3:
                    modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    st.write(modified.strftime("%Y-%m-%d"))

                with col4:
                    if st.button("🗑️", key=f"delete_memory_{file_path.name}"):
                        file_path.unlink()
                        st.rerun()
        else:
            st.info("No hay archivos de memoria. Sube algunos documentos para mejorar la generación de contenido.")

    with tab2:
        st.subheader("Imágenes de Línea Gráfica")
        st.markdown("*Sube imágenes que representen el estilo visual de tu organización*")

        graphics_dir = Path("linea_grafica")
        graphics_dir.mkdir(exist_ok=True)

        # Upload new images
        uploaded_images = st.file_uploader(
            "Subir imágenes de línea gráfica",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Imágenes que representen el estilo visual de tu marca/organización"
        )

        if uploaded_images:
            for uploaded_image in uploaded_images:
                # Resize image if necessary
                resized_img = resize_image_for_openai(uploaded_image)

                if resized_img:
                    file_path = graphics_dir / uploaded_image.name
                    resized_img.save(file_path)
                    st.success(f"✅ Imagen guardada: {uploaded_image.name}")

        # Display existing images
        st.divider()
        st.subheader("🖼️ Imágenes Existentes")

        image_files = list(graphics_dir.glob("*.png")) + list(graphics_dir.glob("*.jpg")) + list(graphics_dir.glob("*.jpeg"))

        if image_files:
            # Display in grid
            cols = st.columns(3)
            for i, image_path in enumerate(image_files):
                with cols[i % 3]:
                    try:
                        img = Image.open(image_path)
                        st.image(img, caption=image_path.name, use_column_width=True)

                        col_a, col_b = st.columns(2)
                        with col_a:
                            file_size = image_path.stat().st_size / (1024 * 1024)
                            st.caption(f"📐 {img.size[0]}x{img.size[1]}")
                        with col_b:
                            st.caption(f"💾 {file_size:.1f} MB")

                        if st.button("🗑️ Eliminar", key=f"delete_graphics_{image_path.name}"):
                            image_path.unlink()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error loading {image_path.name}: {e}")
        else:
            st.info("No hay imágenes de línea gráfica. Sube algunas para mejorar el estilo de las imágenes generadas.")

def show_content_generation(pm, config):
    """Show content generation interface"""
    st.header("✍️ Generar Contenido")

    # Check configuration
    missing_config = []
    if not config.get("openai_api_key"):
        missing_config.append("API Key de OpenAI")
    if not config.get("system_prompt"):
        missing_config.append("Prompt del Sistema")

    if missing_config:
        st.error(f"❌ Configuración incompleta: {', '.join(missing_config)}")
        st.info("Ve a la sección de Configuración para completar la configuración necesaria.")
        return

    # Generation settings
    col1, col2 = st.columns(2)

    with col1:
        generation_days = st.number_input(
            "Días a generar desde hoy",
            min_value=1,
            max_value=30,
            value=config.get("generation_days", 2),
            help="¿Para cuántos días generar contenido?"
        )

    with col2:
        posts_per_day = st.number_input(
            "Posts por día",
            min_value=1,
            max_value=10,
            value=int(pm.get_setting("posts_per_day", 3)),
            help="¿Cuántos posts generar por día?"
        )

    st.divider()

    # Generation preview
    st.subheader("📅 Vista Previa de Generación")

    dates_to_generate = []
    start_date = datetime.now()
    for i in range(generation_days):
        date = start_date + timedelta(days=i)
        dates_to_generate.append(date.strftime('%Y-%m-%d'))

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Fechas a procesar:**")
        for date in dates_to_generate:
            st.write(f"📅 {date}")

    with col2:
        st.write("**Total a generar:**")
        st.write(f"📝 {generation_days * posts_per_day} publicaciones")
        st.write(f"🖼️ {generation_days * posts_per_day * 2} imágenes")

    st.divider()

    # Generation button
    if st.button("🚀 Generar Contenido", type="primary", use_container_width=True):
        generate_content_with_progress(pm, config, generation_days, posts_per_day)

def generate_content_with_progress(pm, config, generation_days, posts_per_day):
    """Generate content with progress feedback"""

    # Set OpenAI API key
    os.environ['OPENAI_API_KEY'] = config.get("openai_api_key", "")

    # Update posts per day setting
    pm.update_setting("posts_per_day", posts_per_day)

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: Generate content with Agent
        status_text.text("🤖 Generando contenido con IA...")
        progress_bar.progress(10)

        agent.setup_directories()
        calendar = agent.generate_social_media_calendar(days=generation_days, posts_per_day=posts_per_day)

        progress_bar.progress(40)
        status_text.text(f"✅ Generadas {len(calendar)} publicaciones")

        if not calendar:
            st.error("❌ No se pudo generar contenido. Revisa la configuración.")
            return

        # Step 2: Save to CSV
        status_text.text("💾 Guardando borradores...")

        new_posts = []
        for post in calendar:
            new_posts.append({
                'fecha': post['fecha'],
                'titulo': post['titulo'],
                'imagen': post['imagen'],
                'descripcion': post['descripcion']
            })

        pm.save_draft_posts(new_posts)
        progress_bar.progress(60)

        # Step 3: Generate images
        status_text.text("🎨 Generando imágenes...")

        csv_file = pm.export_for_image_generation()
        if csv_file:
            image_generator = images.SocialMediaImageGenerator()
            image_generator.process_calendar(csv_file)

            # Update CSV with image paths
            df_with_images = pd.read_csv(csv_file)
            for _, row in df_with_images.iterrows():
                fecha = row['fecha']
                titulo = row['titulo']

                # Find image path
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
                    pm.update_image_path(fecha, titulo, image_path)

        progress_bar.progress(100)
        status_text.text("🎉 ¡Contenido generado exitosamente!")

        # Show success message
        st.success(f"✅ Se generaron {len(calendar)} publicaciones con imágenes")

        # Show summary
        with st.expander("📊 Resumen de Generación", expanded=True):
            for i, post in enumerate(calendar[:5]):  # Show first 5
                st.write(f"**{i+1}. {post['titulo'][:60]}...**")
                st.write(f"📅 {post['fecha']}")
                st.divider()

        if len(calendar) > 5:
            st.info(f"... y {len(calendar) - 5} publicaciones más")

        st.info("💡 Ve a 'Gestionar Publicaciones' para editar y publicar el contenido generado")

    except Exception as e:
        st.error(f"❌ Error durante la generación: {str(e)}")
        progress_bar.progress(0)
        status_text.text("Error en la generación")

def show_post_management(pm):
    """Show post management interface"""
    st.header("📝 Gestionar Publicaciones")

    # Tabs for draft and published posts
    tab1, tab2 = st.tabs(["📝 Borradores", "✅ Publicados"])

    with tab1:
        show_draft_posts(pm)

    with tab2:
        show_published_posts(pm)

def show_draft_posts(pm):
    """Show draft posts management"""
    drafts = pm.get_draft_posts()

    if not drafts:
        st.info("📭 No hay borradores disponibles. Ve a 'Generar Contenido' para crear publicaciones.")
        return

    st.write(f"**📝 {len(drafts)} borradores disponibles**")

    # Bulk actions
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write("**Acciones en lote:**")
    with col2:
        if st.button("🔄 Regenerar Seleccionados"):
            st.info("🔄 Función de regeneración pendiente")
    with col3:
        if st.button("📤 Publicar Todos"):
            st.info("📤 Función de publicación en lote pendiente")

    st.divider()

    # Show each draft
    for i, draft in enumerate(drafts):
        with st.container():
            # Post card
            st.markdown('<div class="post-card">', unsafe_allow_html=True)

            # Header with title and date
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                st.markdown(f"**📝 {draft['titulo']}**")

            with col2:
                st.write(f"📅 {draft['fecha']}")

            with col3:
                st.markdown('<span class="draft-badge">BORRADOR</span>', unsafe_allow_html=True)

            # Content editing
            with st.expander(f"✏️ Editar Publicación {i+1}", expanded=False):

                # Edit form
                with st.form(f"edit_post_{i}"):
                    new_titulo = st.text_input(
                        "Título:",
                        value=draft['titulo'],
                        key=f"titulo_{i}"
                    )

                    new_imagen = st.text_area(
                        "Descripción de imagen:",
                        value=draft['imagen'],
                        height=100,
                        key=f"imagen_{i}"
                    )

                    new_descripcion = st.text_area(
                        "Contenido:",
                        value=draft['descripcion'],
                        height=150,
                        key=f"descripcion_{i}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.form_submit_button("💾 Guardar Cambios"):
                            success = pm.update_post_content(
                                draft['fecha'],
                                draft['titulo'],  # Original title as key
                                new_titulo,
                                new_descripcion,
                                new_imagen
                            )
                            if success:
                                st.success("✅ Cambios guardados")
                                st.rerun()
                            else:
                                st.error("❌ Error guardando cambios")

                    with col2:
                        if st.form_submit_button("🔄 Regenerar"):
                            st.info("🔄 Función de regeneración individual pendiente")

            # Image preview (if available)
            if draft.get('image_path') and Path(draft['image_path']).exists():
                with st.expander("🖼️ Vista Previa de Imagen", expanded=False):
                    try:
                        img = Image.open(draft['image_path'])
                        st.image(img, caption="Imagen generada", use_column_width=True)
                    except Exception as e:
                        st.error(f"Error cargando imagen: {e}")

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📤 Publicar", key=f"publish_{i}", type="primary"):
                    # TODO: Implement actual publishing to Google Sheets
                    st.info("📤 Publicación a Google Sheets pendiente de implementar")
                    # For now, just mark as published in local CSV
                    pm.update_post_status(draft['fecha'], draft['titulo'], 'published')
                    st.success("✅ Marcado como publicado localmente")
                    st.rerun()

            with col2:
                if st.button("👁️ Vista Previa", key=f"preview_{i}"):
                    show_post_preview(draft)

            with col3:
                if st.button("📋 Copiar", key=f"copy_{i}"):
                    st.info("📋 Función de copia pendiente")

            with col4:
                if st.button("🗑️ Eliminar", key=f"delete_{i}"):
                    st.info("🗑️ Función de eliminación pendiente")

            st.markdown('</div>', unsafe_allow_html=True)
            st.divider()

def show_published_posts(pm):
    """Show published posts"""
    published = pm.get_published_posts()

    if not published:
        st.info("📭 No hay publicaciones publicadas aún.")
        return

    st.write(f"**✅ {len(published)} publicaciones publicadas**")

    # Show published posts in a simpler view
    for i, post in enumerate(published):
        with st.container():
            col1, col2, col3 = st.columns([4, 2, 1])

            with col1:
                st.write(f"**{post['titulo']}**")
                st.caption(post['descripcion'][:100] + "...")

            with col2:
                st.write(f"📅 {post['fecha']}")
                st.write(f"🕐 {post.get('published_at', 'N/A')}")

            with col3:
                st.markdown('<span class="published-badge">PUBLICADO</span>', unsafe_allow_html=True)

        st.divider()

def show_post_preview(draft):
    """Show post preview in a modal-style display"""
    st.markdown("### 👁️ Vista Previa de Publicación")

    st.markdown(f"**📅 Fecha:** {draft['fecha']}")
    st.markdown(f"**📝 Título:** {draft['titulo']}")

    st.markdown("**🖼️ Descripción de imagen:**")
    st.info(draft['imagen'])

    st.markdown("**📄 Contenido:**")
    st.write(draft['descripcion'])

    if draft.get('image_path') and Path(draft['image_path']).exists():
        st.markdown("**🖼️ Imagen generada:**")
        try:
            img = Image.open(draft['image_path'])
            st.image(img, use_column_width=True)
        except Exception as e:
            st.error(f"Error cargando imagen: {e}")

if __name__ == "__main__":
    main()

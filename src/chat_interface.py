"""
Streamlit Chat Interface for the CAUSA Agent.

Provides a conversational interface for interacting with the agent
to create social media content.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import uuid
import re
import os
from PIL import Image

from causa_agent import create_causa_agent, chat, get_conversation_history
from langchain_core.messages import HumanMessage, AIMessage
from path_manager import setup_environment, path_manager


# ============================================================================
# Session State Management
# ============================================================================

def init_chat_session():
    """Initialize chat session state."""
    if 'chat_agent' not in st.session_state:
        setup_environment()
        st.session_state.chat_agent = create_causa_agent()

    if 'chat_thread_id' not in st.session_state:
        st.session_state.chat_thread_id = f"streamlit_{uuid.uuid4().hex[:8]}"

    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    if 'processing' not in st.session_state:
        st.session_state.processing = False


def clear_chat():
    """Clear the current chat and start a new conversation."""
    st.session_state.chat_thread_id = f"streamlit_{uuid.uuid4().hex[:8]}"
    st.session_state.chat_messages = []
    st.session_state.processing = False


# ============================================================================
# Image Detection and Display
# ============================================================================

def extract_image_paths(content: str) -> list:
    """Extract image file paths from message content."""
    image_paths = []

    # Pattern to match file paths ending in .png, .jpg, .jpeg
    # Need to handle paths with spaces in filenames
    patterns = [
        # Absolute paths - capture everything until .png/.jpg/.jpeg
        r'(/Users/[^\n]*?\.(?:png|jpg|jpeg))',
        r'(/home/[^\n]*?\.(?:png|jpg|jpeg))',
        # Relative paths
        r'(publicaciones/imagenes/[^\n]*?\.(?:png|jpg|jpeg))',
        # **File saved:** format
        r'\*\*File saved:\*\*\s*([^\n]+\.(?:png|jpg|jpeg))',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # Clean up the path - remove trailing punctuation or markdown
            clean_path = match.strip().rstrip('*').rstrip(',').rstrip(')')
            image_paths.append(clean_path)

    # Deduplicate while preserving order
    seen = set()
    unique_paths = []
    for path in image_paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)

    return unique_paths


def display_image_preview(image_path: str):
    """Display an image preview if the file exists."""
    try:
        # Clean up the path
        image_path = image_path.strip()

        # Handle both absolute and relative paths
        path = Path(image_path)

        if not path.is_absolute():
            # Try relative to src directory
            src_path = Path(__file__).parent / image_path
            if src_path.exists():
                path = src_path
            else:
                # Try relative to publicaciones
                pub_path = path_manager.get_path('publicaciones').parent / image_path
                if pub_path.exists():
                    path = pub_path

        if path.exists() and path.is_file():
            img = Image.open(path)
            st.image(img, caption=f"📷 {path.name}", width="stretch")
            return True
        else:
            st.warning(f"⚠️ Imagen no encontrada: {image_path}")
            return False
    except Exception as e:
        st.error(f"Error cargando imagen: {str(e)}")
        return False


def render_message_with_images(content: str):
    """Render message content and display any embedded images."""
    # First, display the text content
    st.markdown(content)

    # Then, extract and display any images
    image_paths = extract_image_paths(content)

    if image_paths:
        st.divider()
        st.markdown("**🖼️ Vista previa de imágenes:**")
        for img_path in image_paths:
            display_image_preview(img_path)


# ============================================================================
# Chat UI Components
# ============================================================================

def render_message(role: str, content: str):
    """Render a chat message with appropriate styling."""
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    else:
        with st.chat_message("assistant", avatar="🌱"):
            render_message_with_images(content)


def render_chat_history():
    """Render all messages in the chat history."""
    for message in st.session_state.chat_messages:
        render_message(message["role"], message["content"])


def process_user_message(user_input: str):
    """Process a user message and get agent response."""
    if not user_input.strip():
        return

    # Add user message to history
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input
    })

    # Display user message
    render_message("user", user_input)

    # Get agent response
    with st.chat_message("assistant", avatar="🌱"):
        with st.spinner("Pensando..."):
            try:
                response = chat(
                    st.session_state.chat_agent,
                    user_input,
                    st.session_state.chat_thread_id
                )

                # Display response with image previews
                render_message_with_images(response)

                # Add to history
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response
                })

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"Lo siento, ocurrió un error: {str(e)}"
                })


# ============================================================================
# Quick Actions
# ============================================================================

def render_quick_actions():
    """Render quick action buttons for common tasks."""
    st.markdown("### Acciones Rápidas")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📰 Buscar noticias de hoy", use_container_width=True):
            return "Busca noticias relevantes de hoy en Colombia sobre medio ambiente, derechos humanos o temas sociales"

        if st.button("📅 Efemérides de hoy", use_container_width=True):
            today = datetime.now().strftime("%Y-%m-%d")
            return f"Busca efemérides para hoy {today} relacionadas con los temas del colectivo"

        if st.button("📋 Ver publicaciones recientes", use_container_width=True):
            return "Muéstrame las publicaciones de los últimos 7 días para evitar repetir temas"

    with col2:
        if st.button("🎯 Actividades del colectivo", use_container_width=True):
            return "Muéstrame las actividades confirmadas del colectivo para las próximas semanas"

        if st.button("📚 Temas del colectivo", use_container_width=True):
            return "Cuáles son los temas principales del colectivo CAUSA?"

        if st.button("✨ Crear publicación", use_container_width=True):
            return "Ayúdame a crear una publicación para redes sociales. Primero revisa qué se ha publicado recientemente y luego sugiere un tema relevante."

    return None


# ============================================================================
# Main Chat Interface
# ============================================================================

def show_chat_interface():
    """Main function to display the chat interface."""

    # Initialize session
    init_chat_session()

    # Header
    st.title("💬 Chat con el Agente CAUSA")
    st.caption("Conversa con el agente para crear contenido para redes sociales")

    # Sidebar with controls
    with st.sidebar:
        st.markdown("### Controles del Chat")

        if st.button("🗑️ Nueva Conversación", use_container_width=True):
            clear_chat()
            st.rerun()

        st.divider()

        # Quick action buttons
        quick_action = render_quick_actions()

        st.divider()

        # Chat stats
        st.markdown("### Estadísticas")
        st.write(f"**Mensajes:** {len(st.session_state.chat_messages)}")
        st.write(f"**Thread ID:** {st.session_state.chat_thread_id[:12]}...")

        st.divider()

        # Tips
        st.markdown("### Consejos")
        st.markdown("""
        - Pide al agente que **revise publicaciones recientes** antes de crear contenido nuevo
        - Sé **específico** sobre el tema que quieres publicar
        - El agente te mostrará una **vista previa** antes de guardar
        - Solo se generan **imágenes** cuando las apruebes
        """)

    # Main chat area
    chat_container = st.container()

    with chat_container:
        # Render chat history
        render_chat_history()

    # Handle quick action if selected
    if quick_action:
        process_user_message(quick_action)
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Escribe tu mensaje..."):
        process_user_message(prompt)
        st.rerun()

    # Welcome message if no messages
    if not st.session_state.chat_messages:
        st.info("""
        👋 **¡Hola! Soy el agente de CAUSA.**

        Puedo ayudarte a:
        - 🔍 Buscar noticias y efemérides relevantes
        - 📝 Crear publicaciones para redes sociales
        - 🖼️ Generar imágenes con DALL-E
        - 📊 Revisar el contenido publicado anteriormente

        **Para empezar**, usa los botones de acciones rápidas en la barra lateral o escríbeme directamente.
        """)


# ============================================================================
# Standalone Run
# ============================================================================

def main():
    """Run the chat interface as a standalone Streamlit app."""
    st.set_page_config(
        page_title="CAUSA Agent Chat",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
        .stChatMessage {
            padding: 1rem;
        }
        .stChatInput {
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    show_chat_interface()


if __name__ == "__main__":
    main()

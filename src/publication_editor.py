"""
Publication editor component for the CAUSA social media system.
Handles editing individual posts and bulk operations.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from csv_manager import PostManager
from file_manager import FileManager
from PIL import Image
import os

class PublicationEditor:
    def __init__(self):
        self.post_manager = PostManager()
        self.file_manager = FileManager()

    def show_publications_interface(self):
        """Main interface for managing publications"""
        st.header("📝 Gestión de Publicaciones")

        # Load current draft posts
        draft_posts = self.post_manager.get_draft_posts()

        if not draft_posts:
            st.info("No hay publicaciones en borrador. ¡Genera nuevo contenido primero!")
            return

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(draft_posts)

        # Bulk operations section
        st.subheader("🗂️ Operaciones en Lote")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ Eliminar Seleccionadas", type="secondary"):
                self._show_bulk_delete_interface(df)

        with col2:
            if st.button("📅 Cambiar Fechas en Lote", type="secondary"):
                self._show_bulk_date_change_interface(df)

        with col3:
            if st.button("✅ Marcar como Publicadas", type="secondary"):
                self._show_bulk_publish_interface(df)

        st.divider()

        # Posts grid with selection
        st.subheader("📋 Lista de Publicaciones")

        # Filter and sort options
        col1, col2, col3 = st.columns(3)

        with col1:
            date_filter = st.selectbox(
                "Filtrar por fecha:",
                ["Todas"] + sorted(df['fecha'].unique().tolist()),
                key="date_filter"
            )

        with col2:
            sort_by = st.selectbox(
                "Ordenar por:",
                ["Fecha", "Título", "Fecha de creación"],
                key="sort_by"
            )

        with col3:
            sort_order = st.radio(
                "Orden:",
                ["Descendente", "Ascendente"],
                key="sort_order",
                horizontal=True
            )

        # Apply filters and sorting
        filtered_df = df.copy()

        if date_filter != "Todas":
            filtered_df = filtered_df[filtered_df['fecha'] == date_filter]

        # Sort DataFrame
        sort_column_map = {
            "Fecha": "fecha",
            "Título": "titulo",
            "Fecha de creación": "created_at"
        }

        sort_column = sort_column_map[sort_by]
        ascending = sort_order != "Descendente"  # Descendente is now the default

        filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)

        # Display posts as cards
        if len(filtered_df) == 0:
            st.warning("No hay publicaciones que coincidan con los filtros.")
            return

        st.write(f"Mostrando {len(filtered_df)} de {len(df)} publicaciones")

        # Selection checkboxes and post cards
        selected_posts = []

        for idx, post in filtered_df.iterrows():
            with st.container():
                col1, col2 = st.columns([0.05, 0.95])

                with col1:
                    if st.checkbox("", key=f"select_{post['titulo']}_{post['fecha']}", label_visibility="collapsed"):
                        selected_posts.append(post)

                with col2:
                    self._show_post_card(post, idx)

        # Store selected posts in session state for bulk operations
        st.session_state['selected_posts'] = selected_posts

    def _show_post_card(self, post: Dict[str, Any], index: int):
        """Display a single post card with edit option"""
        # Card container
        with st.expander(f"📄 {post['titulo'][:50]}{'...' if len(post['titulo']) > 50 else ''}", expanded=False):
            col1, col2 = st.columns([0.7, 0.3])

            with col1:
                st.write(f"**📅 Fecha:** {post['fecha']}")
                st.write(f"**🏷️ Título:** {post['titulo']}")
                st.write(f"**📝 Descripción:**")
                st.write(post['descripcion'])

                if 'image_path' in post and post['image_path'] and isinstance(post['image_path'], str):
                    st.write(f"**🖼️ Imagen:** {os.path.basename(post['image_path'])}")

            with col2:
                st.write(f"**📊 Estado:** {post.get('status', 'draft')}")
                st.write(f"**🕐 Creado:** {post.get('created_at', 'N/A')}")

                if st.button("✏️ Editar", key=f"edit_{index}", type="primary"):
                    self._show_edit_modal(post)

                # Show image if available
                image_path = post.get('image_path', '')
                # Handle both NaN values and empty strings
                if image_path and str(image_path) != 'nan' and isinstance(image_path, str) and image_path.strip():
                    if os.path.exists(image_path):
                        try:
                            image = Image.open(image_path)
                            st.image(image, caption="Imagen generada", width=150)

                            # Option to add to linea gráfica
                            if st.button("➕ Añadir a Línea Gráfica", key=f"add_to_lg_{index}", type="secondary"):
                                success = self.file_manager.copy_generated_image_to_linea_grafica(image_path)
                                if success:
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error loading image: {e}")

    @st.dialog("✏️ Editar Publicación")
    def _show_edit_modal(self, post: Dict[str, Any]):
        """Show modal for editing a single post"""
        st.write("### Editar Publicación")

        # Edit form
        new_fecha = st.date_input(
            "📅 Fecha de publicación:",
            value=datetime.strptime(post['fecha'], '%Y-%m-%d').date(),
            key=f"edit_fecha_{post['titulo']}"
        )

        new_titulo = st.text_input(
            "🏷️ Título:",
            value=post['titulo'],
            key=f"edit_titulo_{post['titulo']}"
        )

        new_imagen = st.text_area(
            "🖼️ Descripción de imagen:",
            value=post['imagen'],
            key=f"edit_imagen_{post['titulo']}",
            height=100
        )

        new_descripcion = st.text_area(
            "📝 Descripción del post:",
            value=post['descripcion'],
            key=f"edit_descripcion_{post['titulo']}",
            height=200
        )

        new_status = st.selectbox(
            "📊 Estado:",
            ["draft", "ready", "published"],
            index=["draft", "ready", "published"].index(post.get('status', 'draft')),
            key=f"edit_status_{post['titulo']}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Guardar Cambios", type="primary"):
                # Update post
                updated_post = {
                    'fecha': new_fecha.strftime('%Y-%m-%d'),
                    'titulo': new_titulo,
                    'imagen': new_imagen,
                    'descripcion': new_descripcion,
                    'status': new_status,
                    'created_at': post.get('created_at', datetime.now().isoformat()),
                    'image_path': post.get('image_path', '')
                }

                # Update in PostManager
                success = self.post_manager.update_post(
                    post['fecha'],
                    post['titulo'],
                    updated_post
                )

                if success:
                    st.success("✅ Publicación actualizada")
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar")

        with col2:
            if st.button("🗑️ Eliminar", type="secondary"):
                if st.session_state.get('confirm_delete', False):
                    success = self.post_manager.delete_post(post['fecha'], post['titulo'])
                    if success:
                        st.success("✅ Publicación eliminada")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar")
                else:
                    st.session_state['confirm_delete'] = True
                    st.warning("⚠️ Haz clic otra vez para confirmar eliminación")

        with col3:
            if st.button("❌ Cancelar"):
                st.session_state.pop('confirm_delete', None)
                st.rerun()

    def _show_bulk_delete_interface(self, df: pd.DataFrame):
        """Show interface for bulk deleting posts"""
        selected_posts = st.session_state.get('selected_posts', [])

        if not selected_posts:
            st.warning("⚠️ No hay publicaciones seleccionadas")
            return

        st.warning(f"🗑️ ¿Eliminar {len(selected_posts)} publicaciones seleccionadas?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Confirmar Eliminación", type="primary"):
                success_count = 0
                for post in selected_posts:
                    if self.post_manager.delete_post(post['fecha'], post['titulo']):
                        success_count += 1

                if success_count == len(selected_posts):
                    st.success(f"✅ {success_count} publicaciones eliminadas")
                else:
                    st.warning(f"⚠️ {success_count} de {len(selected_posts)} publicaciones eliminadas")

                st.rerun()

        with col2:
            if st.button("❌ Cancelar"):
                st.rerun()

    def _show_bulk_date_change_interface(self, df: pd.DataFrame):
        """Show interface for changing dates in bulk"""
        selected_posts = st.session_state.get('selected_posts', [])

        if not selected_posts:
            st.warning("⚠️ No hay publicaciones seleccionadas")
            return

        st.info(f"📅 Cambiar fechas de {len(selected_posts)} publicaciones seleccionadas")

        # Date adjustment options
        adjustment_type = st.radio(
            "Tipo de ajuste:",
            ["Fecha específica", "Desplazar días"],
            key="date_adjustment_type"
        )

        if adjustment_type == "Fecha específica":
            new_base_date = st.date_input(
                "📅 Nueva fecha base:",
                value=datetime.now().date(),
                key="bulk_new_date"
            )

            spacing = st.number_input(
                "📊 Espaciado entre publicaciones (días):",
                min_value=0,
                max_value=30,
                value=1,
                key="bulk_spacing"
            )

        else:  # Desplazar días
            days_offset = st.number_input(
                "📊 Días a desplazar (positivo = futuro, negativo = pasado):",
                min_value=-365,
                max_value=365,
                value=0,
                key="bulk_days_offset"
            )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Aplicar Cambios", type="primary"):
                success_count = 0

                for i, post in enumerate(selected_posts):
                    if adjustment_type == "Fecha específica":
                        new_date = new_base_date + timedelta(days=i * spacing)
                    else:
                        current_date = datetime.strptime(post['fecha'], '%Y-%m-%d').date()
                        new_date = current_date + timedelta(days=days_offset)

                    updated_post = post.copy()
                    updated_post['fecha'] = new_date.strftime('%Y-%m-%d')

                    if self.post_manager.update_post(post['fecha'], post['titulo'], updated_post):
                        success_count += 1

                if success_count == len(selected_posts):
                    st.success(f"✅ {success_count} fechas actualizadas")
                else:
                    st.warning(f"⚠️ {success_count} de {len(selected_posts)} fechas actualizadas")

                st.rerun()

        with col2:
            if st.button("❌ Cancelar"):
                st.rerun()

    def _show_bulk_publish_interface(self, df: pd.DataFrame):
        """Show interface for marking posts as published"""
        selected_posts = st.session_state.get('selected_posts', [])

        if not selected_posts:
            st.warning("⚠️ No hay publicaciones seleccionadas")
            return

        st.info(f"✅ Marcar {len(selected_posts)} publicaciones como publicadas")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Marcar como Publicadas", type="primary"):
                success_count = 0

                for post in selected_posts:
                    updated_post = post.copy()
                    updated_post['status'] = 'published'

                    if self.post_manager.update_post(post['fecha'], post['titulo'], updated_post):
                        success_count += 1

                if success_count == len(selected_posts):
                    st.success(f"✅ {success_count} publicaciones marcadas como publicadas")
                else:
                    st.warning(f"⚠️ {success_count} de {len(selected_posts)} publicaciones actualizadas")

                st.rerun()

        with col2:
            if st.button("❌ Cancelar"):
                st.rerun()

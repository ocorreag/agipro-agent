"""
Publication management tools for the CAUSA agent.
Handles reading past publications and saving new drafts.
"""

import pandas as pd
from langchain_core.tools import tool
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from csv_manager import PostManager
from path_manager import path_manager
from config_manager import ConfigManager
from urllib.parse import quote


# Initialize managers (lazy loading to avoid import issues)
_post_manager = None
_config_manager = None


def get_post_manager():
    global _post_manager
    if _post_manager is None:
        _post_manager = PostManager()
    return _post_manager


def get_config_manager():
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


@tool
def read_past_publications(days_back: int = 30, include_published: bool = True) -> str:
    """
    Read past publications to understand what content has already been created.

    Use this tool BEFORE creating new content to:
    - Avoid repeating topics that were recently covered
    - Maintain variety in content themes
    - Check the style and format of previous posts

    Args:
        days_back: Number of days to look back (default 30)
        include_published: Whether to include already published posts (default True)

    Returns:
        Summary of recent publications with dates, titles, and brief descriptions.
    """
    try:
        pm = get_post_manager()

        # Get drafts
        drafts = pm.get_draft_posts()

        # Get published posts if requested
        published = []
        if include_published:
            published = pm.get_published_posts()

        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        recent_drafts = [d for d in drafts if d.get('fecha', '') >= cutoff_str]
        recent_published = [p for p in published if p.get('fecha', '') >= cutoff_str]

        if not recent_drafts and not recent_published:
            return f"No publications found in the last {days_back} days. You have a clean slate for new content!"

        result = f"Recent publications (last {days_back} days):\n\n"

        if recent_drafts:
            result += "**DRAFTS (pending publication):**\n"
            for d in recent_drafts[:10]:  # Limit to avoid too much text
                result += f"- [{d.get('fecha', 'N/A')}] {d.get('titulo', 'No title')}\n"
                desc = d.get('descripcion', '')[:100]
                if desc:
                    result += f"  Preview: {desc}...\n"
            if len(recent_drafts) > 10:
                result += f"  ... and {len(recent_drafts) - 10} more drafts\n"
            result += "\n"

        if recent_published:
            result += "**PUBLISHED:**\n"
            for p in recent_published[:10]:
                result += f"- [{p.get('fecha', 'N/A')}] {p.get('titulo', 'No title')}\n"
            if len(recent_published) > 10:
                result += f"  ... and {len(recent_published) - 10} more published\n"

        result += f"\n**Summary:** {len(recent_drafts)} drafts, {len(recent_published)} published"

        return result

    except Exception as e:
        return f"Error reading past publications: {str(e)}"


@tool
def save_draft_post(fecha: str, titulo: str, imagen: str, descripcion: str) -> str:
    """
    Save a new post as a draft.

    Use this tool AFTER the user has approved the post content.
    The post will be saved as a draft for later review and image generation.

    Args:
        fecha: Publication date in YYYY-MM-DD format
        titulo: Post title (short, attention-grabbing)
        imagen: Detailed description for DALL-E image generation.
                Be specific about visual elements, style, colors, and any text to include.
        descripcion: Full post content including hashtags, emojis, and call-to-action.

    Returns:
        Confirmation message with the saved post details.
    """
    try:
        pm = get_post_manager()

        post = {
            'fecha': fecha,
            'titulo': titulo,
            'imagen': imagen,
            'descripcion': descripcion
        }

        # Save as draft
        draft_file = pm.save_draft_posts([post], date=fecha)

        return f"""Post saved successfully as draft!

**Date:** {fecha}
**Title:** {titulo}
**Image prompt:** {imagen[:100]}...
**Content preview:** {descripcion[:150]}...

The post is now ready for image generation. Ask the user if they want to generate the image now."""

    except Exception as e:
        return f"Error saving draft: {str(e)}"


@tool
def get_activities() -> str:
    """
    Get the list of confirmed activities from the collective's calendar.

    Use this tool to find upcoming events and activities that need promotion.
    Only returns activities with status 'confirmada' (confirmed).

    Returns:
        List of confirmed activities with dates, names, and details.
    """
    try:
        cm = get_config_manager()

        # Get Google Sheets configuration
        gsheet_id = cm.get_setting('google_sheet_id', '1dL7ngg0P-E9QEiWCDtS5iF2ColQC7YVIM4pbIPQouuE')
        sheet_name = cm.get_setting('google_sheet_name', 'actividades')

        # URL encode the sheet name
        encoded_sheet_name = quote(sheet_name)
        url = f'https://docs.google.com/spreadsheets/d/{gsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}'

        # Read activities
        all_activities = pd.read_csv(url)

        if 'status' in all_activities.columns:
            confirmed = all_activities[all_activities['status'].str.lower() == 'confirmada'].copy()
        else:
            confirmed = all_activities.copy()

        if confirmed.empty:
            return "No confirmed activities found in the calendar. Consider creating content based on news or ephemerides instead."

        result = f"**Confirmed Activities ({len(confirmed)} total):**\n\n"

        for _, row in confirmed.iterrows():
            result += f"- **{row.get('nombre', row.get('actividad', 'Activity'))}**\n"
            if 'fecha' in row:
                result += f"  Date: {row['fecha']}\n"
            if 'lugar' in row:
                result += f"  Location: {row['lugar']}\n"
            if 'descripcion' in row:
                result += f"  Description: {str(row['descripcion'])[:100]}...\n"
            result += "\n"

        return result

    except Exception as e:
        return f"Error reading activities: {str(e)}. The Google Sheet may not be accessible or properly configured."


@tool
def update_post_image_path(fecha: str, titulo: str, image_path: str) -> str:
    """
    Update the image path for an existing draft post.

    This is used internally after image generation to link the image to the post.

    Args:
        fecha: Post date in YYYY-MM-DD format
        titulo: Post title (must match exactly)
        image_path: Path to the generated image file

    Returns:
        Confirmation message.
    """
    try:
        pm = get_post_manager()

        success = pm.update_image_path(fecha, titulo, image_path)

        if success:
            return f"Image path updated for post '{titulo}' on {fecha}"
        else:
            return f"Could not find post '{titulo}' on {fecha} to update image path"

    except Exception as e:
        return f"Error updating image path: {str(e)}"

"""
Image generation tool for the CAUSA agent.
Provides DALL-E 3 integration for creating social media images.
"""

from langchain_core.tools import tool
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the standalone function from images.py
from images import generate_single_image
from path_manager import path_manager


@tool
def generate_image(titulo: str, imagen_description: str, fecha: str) -> str:
    """
    Generate a social media image using DALL-E 3.

    Use this tool ONLY AFTER the user has approved the post content.
    The image will be saved and linked to the post automatically.

    Args:
        titulo: The post title (used for filename and context)
        imagen_description: Detailed description for the image.
                           Be specific about visual elements, composition,
                           colors, style, and any text that should appear.
        fecha: The post date in YYYY-MM-DD format (used for filename)

    Returns:
        Path to the generated image and confirmation message.
    """
    try:
        # Use the standalone function from images.py
        filepath = generate_single_image(
            titulo=titulo,
            imagen_description=imagen_description,
            fecha=fecha
        )

        if not filepath:
            return "Error: No image was generated. Please try again or check your OpenAI API key."

        return f"""Image generated successfully!

**File saved:** {filepath}
**Size:** 1024x1024 (universal format for all social media)

The image has been created based on:
- Title: {titulo}
- Description: {imagen_description[:100]}...

You can now update the post with this image path using the update_post_image_path tool."""

    except Exception as e:
        return f"Error generating image: {str(e)}. Please check your OpenAI API key and try again."


@tool
def regenerate_image(titulo: str, imagen_description_original: str, cambios: str, fecha: str) -> str:
    """
    Regenerate an image with modifications based on user feedback.

    Use this tool when the user wants to change something in a generated image.
    This creates a NEW image with the modifications applied to the original description.

    Args:
        titulo: The post title
        imagen_description_original: The original image description that was used
        cambios: The changes/modifications the user wants (e.g., "make it brighter",
                "add more people", "change the background to blue", "remove the text")
        fecha: The post date in YYYY-MM-DD format

    Returns:
        Path to the new generated image with the modifications.
    """
    # Combine original description with modifications
    modified_description = f"""{imagen_description_original}

IMPORTANT MODIFICATIONS REQUESTED:
{cambios}

Apply these modifications while keeping the overall theme and style of the original description."""

    try:
        # Use the standalone function from images.py
        filepath = generate_single_image(
            titulo=titulo,
            imagen_description=modified_description,
            fecha=fecha
        )

        if not filepath:
            return "Error: No image was generated. Please try again."

        return f"""Image regenerated with your modifications!

**Changes applied:** {cambios}

**New file saved:** {filepath}

The new image incorporates your requested changes. Let me know if you'd like any further adjustments."""

    except Exception as e:
        return f"Error regenerating image: {str(e)}"


@tool
def preview_image_prompt(titulo: str, imagen_description: str) -> str:
    """
    Preview what prompt will be sent to DALL-E before generating.

    Use this to verify the image description is detailed enough
    before spending API credits on generation.

    Args:
        titulo: The post title
        imagen_description: The image description to preview

    Returns:
        The full prompt that would be sent to DALL-E.
    """
    # Build a preview of what the prompt would look like
    full_prompt = f"""Create a social media image for the following post:

Title: {titulo}
Image description: {imagen_description}

Additional requirements:
- Professional and attractive visual style
- Vibrant but not oversaturated colors
- Balanced composition
- If text is requested, render it clearly and legibly
- High quality and detail
- Style coherent with the CAUSA brand (if including logo, only the butterfly and 'CAUSA' below it)

[Brand colors from linea_grafica/ will be automatically extracted and applied]
"""

    return f"""**Preview of DALL-E prompt:**

{full_prompt}

---
**Estimated tokens:** ~{len(full_prompt.split())} words
**Image size:** 1024x1024 (square)
**Quality:** High

If this looks good, use the `generate_image` tool to create the actual image."""

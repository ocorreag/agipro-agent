"""
Image generation tool for the CAUSA agent.
Provides GPT-Image-1 integration for creating social media images.
Uses línea gráfica images as visual style references for brand consistency.
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
def generate_image(titulo: str, imagen_description: str, fecha: str, size: str = "1024x1536") -> str:
    """
    Generate a social media image using GPT-Image-1 with línea gráfica as visual reference.

    Use this tool ONLY AFTER the user has approved the post content.
    The image will automatically use the brand images from linea_grafica/ folder
    as style references to maintain visual consistency.

    Args:
        titulo: The post title (used for filename and context)
        imagen_description: Detailed description for the image.
                           Be specific about visual elements, composition,
                           and any text that should appear.
                           Colors and style will be matched from línea gráfica.
        fecha: The post date in YYYY-MM-DD format (used for filename)
        size: Image dimensions. Choose based on content and platform:

            SIZE OPTIONS AND WHEN TO USE THEM:

            "1024x1536" (PORTRAIT - DEFAULT, RECOMMENDED)
            - Best for: Instagram feed, Facebook feed, Pinterest
            - Use when: The content is about people, portraits, vertical scenes,
              events, protests, nature scenes with trees, buildings, etc.
            - Engagement: Highest on Instagram/Facebook feeds
            - Aspect ratio: 2:3 (vertical)

            "1024x1024" (SQUARE)
            - Best for: Twitter/X, LinkedIn, universal sharing, profile-style images
            - Use when: The content is balanced, logos, icons, centered subjects,
              or when the user specifically asks for square format
            - Engagement: Good universal compatibility
            - Aspect ratio: 1:1

            "1536x1024" (LANDSCAPE)
            - Best for: Twitter/X headers, YouTube thumbnails, blog posts
            - Use when: The content is about landscapes, panoramas, group photos,
              wide scenes, banners, or when horizontal composition is needed
            - Aspect ratio: 3:2 (horizontal)

            "auto" (LET MODEL DECIDE)
            - Use when: Unsure which format fits best
            - The model will analyze the prompt and choose appropriately

    Returns:
        Path to the generated image and confirmation message.
    """
    # Validate size parameter
    valid_sizes = ["1024x1024", "1024x1536", "1536x1024", "auto"]
    if size not in valid_sizes:
        size = "1024x1536"  # Default to portrait

    try:
        # Use the standalone function from images.py
        filepath = generate_single_image(
            titulo=titulo,
            imagen_description=imagen_description,
            fecha=fecha,
            size=size
        )

        if not filepath:
            return "Error: No image was generated. Please try again or check your OpenAI API key."

        # Format size description for response
        size_desc = {
            "1024x1536": "1024x1536 (portrait - optimal for Instagram/Facebook)",
            "1024x1024": "1024x1024 (square - universal)",
            "1536x1024": "1536x1024 (landscape - optimal for Twitter/banners)",
            "auto": "auto (model selected optimal size)"
        }

        return f"""✅ Image generated successfully!

**File saved:** {filepath}
**Size:** {size_desc.get(size, size)}
**Style reference:** Images from linea_grafica/ folder

The image has been created based on:
- Title: {titulo}
- Description: {imagen_description[:100]}...
- Visual style: Matched to your brand guidelines (línea gráfica)

You can now update the post with this image path using the update_post_image_path tool."""

    except Exception as e:
        return f"Error generating image: {str(e)}. Please check your OpenAI API key and try again."


@tool
def regenerate_image(titulo: str, imagen_description_original: str, cambios: str, fecha: str, size: str = "1024x1536") -> str:
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
        size: Image dimensions - "1024x1536" (portrait), "1024x1024" (square),
              "1536x1024" (landscape), or "auto". See generate_image for detailed guidance.

    Returns:
        Path to the new generated image with the modifications.
    """
    # Validate size parameter
    valid_sizes = ["1024x1024", "1024x1536", "1536x1024", "auto"]
    if size not in valid_sizes:
        size = "1024x1536"

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
            fecha=fecha,
            size=size
        )

        if not filepath:
            return "Error: No image was generated. Please try again."

        return f"""✅ Image regenerated with your modifications!

**Changes applied:** {cambios}
**Size:** {size}
**New file saved:** {filepath}

The new image incorporates your requested changes. Let me know if you'd like any further adjustments."""

    except Exception as e:
        return f"Error regenerating image: {str(e)}"


@tool
def preview_image_prompt(titulo: str, imagen_description: str, size: str = "1024x1536") -> str:
    """
    Preview what prompt will be sent to GPT-Image-1 before generating.

    Use this to verify the image description is detailed enough
    before spending API credits on generation.

    Args:
        titulo: The post title
        imagen_description: The image description to preview
        size: Intended image size - "1024x1536" (portrait), "1024x1024" (square),
              "1536x1024" (landscape), or "auto"

    Returns:
        The full prompt that would be sent along with reference images.
    """
    # Check for reference images
    from path_manager import path_manager
    style_dir = path_manager.get_path('linea_grafica')
    ref_images = []
    if style_dir.exists():
        for pattern in ['*.jpg', '*.jpeg', '*.png']:
            ref_images.extend(style_dir.glob(pattern))

    ref_count = min(len(ref_images), 5)

    # Size descriptions
    size_info = {
        "1024x1536": "1024x1536 (portrait 2:3) - Best for Instagram/Facebook feeds",
        "1024x1024": "1024x1024 (square 1:1) - Universal, good for Twitter/LinkedIn",
        "1536x1024": "1536x1024 (landscape 3:2) - Best for banners, Twitter headers",
        "auto": "auto - Model will choose based on content"
    }

    # Build a preview of what the prompt would look like
    full_prompt = f"""Create a social media image for the following post:

Title: {titulo}
Image description: {imagen_description}

IMPORTANT: Match the visual style, color palette, and aesthetic of the reference images provided.

Additional requirements:
- Professional and attractive visual style
- Vibrant but not oversaturated colors
- Balanced composition
- If text is requested, render it clearly and legibly
- High quality and detail
- Style coherent with the CAUSA brand (if including logo, only the butterfly and 'CAUSA' below it)
"""

    return f"""**Preview of GPT-Image-1 prompt:**

{full_prompt}

---
**🎨 Reference Images:** {ref_count} images from linea_grafica/ will be sent as visual style guides
**📐 Image size:** {size_info.get(size, size)}
**Quality:** High
**Input Fidelity:** High (closely match reference style)

**SIZE GUIDE FOR AGENT:**
- Portrait (1024x1536): People, events, vertical scenes, nature with trees → Instagram/Facebook
- Square (1024x1024): Logos, icons, balanced subjects → Universal/Twitter/LinkedIn
- Landscape (1536x1024): Panoramas, groups, wide scenes → Banners/Twitter headers

{'✅ Reference images found - brand style will be applied!' if ref_count > 0 else '⚠️ No reference images found - consider adding images to linea_grafica/ folder'}

If this looks good, use the `generate_image` tool with size="{size}" to create the actual image."""

"""
CAUSA Agent Tools Package

This package provides all the tools available to the CAUSA content generation agent.
Each tool is a LangChain @tool decorated function that the agent can call.
"""

from .web_search import search_web, search_ephemerides, get_current_date
from .publications import (
    read_past_publications,
    save_draft_post,
    get_activities,
    update_post_image_path
)
from .memory import query_collective_memory, get_collective_themes, reload_memory
from .images import generate_image, regenerate_image, preview_image_prompt


# All tools available to the agent
ALL_TOOLS = [
    # Date/Time tools
    get_current_date,

    # Research tools
    search_web,
    search_ephemerides,
    query_collective_memory,
    get_collective_themes,
    get_activities,

    # Publication tools
    read_past_publications,
    save_draft_post,
    update_post_image_path,

    # Image tools
    generate_image,
    regenerate_image,
    preview_image_prompt,
]

# Tools that don't modify state (safe to use anytime)
READ_ONLY_TOOLS = [
    get_current_date,
    search_web,
    search_ephemerides,
    query_collective_memory,
    get_collective_themes,
    get_activities,
    read_past_publications,
    preview_image_prompt,
]

# Tools that modify state (require confirmation)
WRITE_TOOLS = [
    save_draft_post,
    update_post_image_path,
    generate_image,
    regenerate_image,
]


__all__ = [
    # Individual tools
    'get_current_date',
    'search_web',
    'search_ephemerides',
    'query_collective_memory',
    'get_collective_themes',
    'get_activities',
    'read_past_publications',
    'save_draft_post',
    'update_post_image_path',
    'generate_image',
    'regenerate_image',
    'preview_image_prompt',
    'reload_memory',

    # Tool collections
    'ALL_TOOLS',
    'READ_ONLY_TOOLS',
    'WRITE_TOOLS',
]

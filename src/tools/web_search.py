"""
Web search tool for the CAUSA agent.
Provides flexible web search capabilities using DuckDuckGo.
"""

from langchain_core.tools import tool
from datetime import datetime, timedelta
from typing import Optional

# Try to import DDGS, handle if lxml/ddgs has architecture issues
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError as e:
    DDGS_AVAILABLE = False
    DDGS_ERROR = str(e)


@tool
def search_web(query: str, search_type: str = "news", max_results: int = 7) -> str:
    """
    Search the web for information using DuckDuckGo.

    Use this tool when you need to find:
    - Current news and events
    - Historical information (ephemerides)
    - Any topic relevant to creating social media content

    Args:
        query: The search query. Be specific and include relevant keywords.
               For Colombian news, include "Colombia" or city names.
               For dates, include the specific date in Spanish.
        search_type: Type of search - "news" for recent news, "text" for general web search
        max_results: Maximum number of results to return (default 7)

    Returns:
        Formatted search results with titles, descriptions, and sources.
    """
    if not DDGS_AVAILABLE:
        return f"""Web search is temporarily unavailable due to a dependency issue: {DDGS_ERROR}

To fix this, run in your terminal:
```
pip uninstall lxml ddgs
pip install --no-cache-dir lxml ddgs
```

For now, you can create content based on:
- The collective's themes and values
- Information from the collective's memory documents
- General knowledge about environmental and social topics"""

    try:
        with DDGS() as ddgs:
            if search_type == "news":
                results = list(ddgs.news(
                    query,
                    max_results=max_results,
                    region="co-es",  # Colombia, Spanish
                    safesearch="moderate"
                ))
            else:
                results = list(ddgs.text(
                    query,
                    max_results=max_results,
                    region="co-es",
                    safesearch="moderate"
                ))

        if not results:
            return f"No results found for query: '{query}'. Try rephrasing or broadening the search."

        formatted_results = f"Search results for '{query}':\n\n"

        for i, r in enumerate(results, 1):
            title = r.get('title', 'No title')
            body = r.get('body', r.get('description', 'No description'))
            source = r.get('source', r.get('href', 'Unknown source'))
            date = r.get('date', '')

            formatted_results += f"{i}. **{title}**\n"
            formatted_results += f"   {body}\n"
            if date:
                formatted_results += f"   Date: {date}\n"
            formatted_results += f"   Source: {source}\n\n"

        return formatted_results

    except Exception as e:
        return f"Error searching the web: {str(e)}. Try a different query or search type."


@tool
def search_ephemerides(date: str) -> str:
    """
    Search for historical events and commemorations (ephemerides) for a specific date.

    Use this tool when you need to find historical events, commemorations,
    or important dates related to the collective's themes (human rights,
    environment, social movements, Colombian history).

    Args:
        date: The date to search for in YYYY-MM-DD format (e.g., "2026-01-31")

    Returns:
        Historical events and commemorations for that date.
    """
    if not DDGS_AVAILABLE:
        return f"""Ephemerides search is temporarily unavailable due to a dependency issue.

To fix this, run in your terminal:
```
pip uninstall lxml ddgs
pip install --no-cache-dir lxml ddgs
```

For now, you can create content based on well-known dates and commemorations."""

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        month_name = meses[date_obj.month - 1]

        # Topics relevant to the collective
        topics = "historia de Colombia, derechos humanos, memoria, medio ambiente, movimientos sociales"

        query = f"efemérides del {date_obj.day} de {month_name} en Colombia {topics}"

        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                max_results=7,
                region="co-es",
                safesearch="moderate"
            ))

        if not results:
            # Try a more general search
            fallback_query = f"{date_obj.day} de {month_name} efemérides historia"
            with DDGS() as ddgs:
                results = list(ddgs.text(fallback_query, max_results=5, region="co-es"))

        if not results:
            return f"No ephemerides found for {date}. Consider creating content based on other topics."

        formatted_results = f"Ephemerides for {date_obj.day} de {month_name}:\n\n"

        for i, r in enumerate(results, 1):
            title = r.get('title', 'No title')
            body = r.get('body', 'No description')
            formatted_results += f"{i}. **{title}**\n   {body}\n\n"

        return formatted_results

    except ValueError:
        return f"Invalid date format: {date}. Please use YYYY-MM-DD format."
    except Exception as e:
        return f"Error searching ephemerides: {str(e)}"


@tool
def get_current_date() -> str:
    """
    Get the current date and time information.

    Use this tool when you need to:
    - Know what today's date is
    - Calculate dates for "next week", "tomorrow", etc.
    - Verify the current date before creating content

    Returns:
        Current date information including day of week and formatted date.
    """
    now = datetime.now()

    day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    month_names = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                   "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    day_name = day_names[now.weekday()]
    month_name = month_names[now.month - 1]

    # Calculate useful dates
    tomorrow = now + timedelta(days=1)
    next_week_start = now + timedelta(days=(7 - now.weekday()))

    return f"""**Current Date Information:**

- **Today:** {day_name}, {now.day} de {month_name} de {now.year}
- **ISO format:** {now.strftime('%Y-%m-%d')}
- **Time:** {now.strftime('%H:%M')} (Colombia time)

**Useful Dates:**
- **Tomorrow:** {tomorrow.strftime('%Y-%m-%d')} ({day_names[tomorrow.weekday()]})
- **Next Monday:** {next_week_start.strftime('%Y-%m-%d')}
- **Next week dates:** {next_week_start.strftime('%Y-%m-%d')} to {(next_week_start + timedelta(days=6)).strftime('%Y-%m-%d')}

Use these dates when creating content for upcoming publications."""

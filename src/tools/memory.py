"""
Collective memory tool for the CAUSA agent.
Provides RAG-based search over the collective's documents.
"""

from langchain_core.tools import tool
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from pathlib import Path
from typing import Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from path_manager import path_manager
from safe_print import safe_print


# Global memory database (lazy loaded)
_memory_db = None
_embeddings = None


def _get_embeddings():
    """Get or create embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings()
    return _embeddings


def _load_memory_db():
    """Load the collective's memory documents into a vector database."""
    global _memory_db

    if _memory_db is not None:
        return _memory_db

    documents = []
    memory_path = path_manager.get_path('memory')

    if not memory_path.exists():
        safe_print(f"Warning: Memory path does not exist: {memory_path}")
        return None

    # Load all supported files
    for ext in ["*.txt", "*.pdf"]:
        for file_path in memory_path.glob(ext):
            try:
                if file_path.suffix.lower() == '.pdf':
                    loader = PyPDFLoader(str(file_path))
                else:
                    loader = TextLoader(str(file_path))

                docs = loader.load()
                if docs:
                    documents.extend(docs)
                    safe_print(f"Loaded memory document: {file_path.name}")

            except Exception as e:
                safe_print(f"Error loading {file_path}: {str(e)}")

    if not documents:
        safe_print("No memory documents found")
        return None

    safe_print(f"Total memory documents loaded: {len(documents)}")

    try:
        _memory_db = Chroma.from_documents(documents, _get_embeddings())
        return _memory_db
    except Exception as e:
        safe_print(f"Error creating vector database: {str(e)}")
        return None


@tool
def query_collective_memory(question: str, num_results: int = 3) -> str:
    """
    Search the collective's memory documents (PDFs and text files).

    Use this tool to:
    - Find information about the collective's history and values
    - Get context about past activities and positions
    - Ensure content aligns with the collective's ideology
    - Find specific information mentioned in uploaded documents

    The memory contains documents about the collective's:
    - History and founding principles
    - Past campaigns and activities
    - Position statements on various issues
    - Community relationships and partnerships

    Args:
        question: A natural language question about the collective.
                 Be specific to get better results.
        num_results: Number of relevant document chunks to return (default 3)

    Returns:
        Relevant excerpts from the collective's documents.
    """
    try:
        db = _load_memory_db()

        if db is None:
            return """No memory documents are currently loaded.
The collective's memory folder may be empty.
You can still create content based on:
- Web searches for current news
- Ephemerides and historical dates
- The collective's general themes: environment, animal rights, human rights, urban planning, culture, and memory."""

        # Perform similarity search
        results = db.similarity_search(question, k=num_results)

        if not results:
            return f"No relevant information found in the collective's memory for: '{question}'. Try rephrasing your question."

        formatted_results = f"**From the collective's memory (regarding: {question}):**\n\n"

        for i, doc in enumerate(results, 1):
            # Get source filename if available
            source = doc.metadata.get('source', 'Unknown document')
            if source != 'Unknown document':
                source = Path(source).name

            content = doc.page_content.strip()
            # Truncate very long content
            if len(content) > 500:
                content = content[:500] + "..."

            formatted_results += f"**[{i}] From: {source}**\n"
            formatted_results += f"{content}\n\n"

        formatted_results += "\nUse this context to ensure your content aligns with the collective's values and history."

        return formatted_results

    except Exception as e:
        return f"Error searching collective memory: {str(e)}"


@tool
def get_collective_themes() -> str:
    """
    Get the main themes and focus areas of the collective.

    Use this tool to understand what topics are relevant for content creation.
    This provides a quick overview without searching specific documents.

    Returns:
        List of the collective's main themes and focus areas.
    """
    # This is based on the CLAUDE.md documentation
    themes = """
**CAUSA - Colectivo Ambiental de Usaca**

The collective focuses on the following themes:

1. **Environment** (Medio Ambiente)
   - Environmental conservation
   - Climate action
   - Sustainable urban development
   - Green spaces and nature protection

2. **Animal Rights** (Animalismo)
   - Animal welfare
   - Anti-cruelty campaigns
   - Wildlife protection
   - Ethical treatment of animals

3. **Human Rights** (Derechos Humanos)
   - Social justice
   - Community rights
   - Access to public services
   - Civic participation

4. **Urban Planning** (Urbanismo)
   - Sustainable city development
   - Public transportation
   - Green infrastructure
   - Community spaces

5. **Culture** (Cultura)
   - Local cultural events
   - Art and community expression
   - Cultural heritage preservation

6. **Popular Education** (Educación Popular)
   - Community workshops
   - Environmental education
   - Civic engagement training

7. **Historical Memory** (Memoria)
   - Remembrance of social movements
   - Documentation of community history
   - Commemoration of important dates

**Geographic Focus:**
- Usaquén (neighborhood in Bogotá)
- Bogotá (capital city)
- Colombia (national issues)

Use these themes to guide content creation and ensure relevance to the collective's mission.
"""
    return themes


def reload_memory():
    """Reload the memory database (useful after uploading new documents)."""
    global _memory_db
    _memory_db = None
    return _load_memory_db()

#!/usr/bin/env python3
"""
Test script to verify the RAG (Retrieval-Augmented Generation) system is working.

Run with: python test_rag.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

def test_rag():
    """Test the RAG memory system."""
    print("\n" + "="*60)
    print("🧪 RAG Memory System Test")
    print("="*60)

    # Step 1: Check environment
    print("\n📋 Step 1: Checking environment...")
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment!")
        print("   Set it in .env file or export it in your shell.")
        return False
    print(f"✅ OpenAI API key found (starts with: {api_key[:8]}...)")

    # Step 2: Check memory folder
    print("\n📋 Step 2: Checking memory folder...")
    from path_manager import path_manager, setup_environment
    setup_environment()

    memory_path = path_manager.get_path('memory')
    print(f"   Memory path: {memory_path}")

    if not memory_path.exists():
        print("❌ Memory folder does not exist!")
        return False

    files = list(memory_path.glob("*.pdf")) + list(memory_path.glob("*.txt"))
    print(f"✅ Found {len(files)} document(s):")
    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"   - {f.name} ({size_mb:.2f} MB)")

    if not files:
        print("⚠️  No PDF or TXT files found in memory folder.")
        print("   Upload some documents to test RAG.")
        return False

    # Step 3: Test embeddings
    print("\n📋 Step 3: Testing OpenAI Embeddings...")
    try:
        from langchain_openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings()

        # Test with a simple text
        test_text = "This is a test of the embeddings system."
        result = embeddings.embed_query(test_text)
        print(f"✅ Embeddings working! (Vector dimension: {len(result)})")
    except Exception as e:
        print(f"❌ Embeddings failed: {e}")
        return False

    # Step 4: Load documents and create vector store
    print("\n📋 Step 4: Loading documents into vector store...")
    try:
        from tools.memory import _load_memory_db, reload_memory

        # Force reload to test fresh
        db = reload_memory()

        if db is None:
            print("❌ Failed to create vector database!")
            return False

        print("✅ Vector database created successfully!")
    except Exception as e:
        print(f"❌ Error loading memory: {e}")
        return False

    # Step 5: Test queries
    print("\n📋 Step 5: Testing RAG queries...")

    test_queries = [
        "¿Cuáles son los valores del colectivo?",
        "¿Qué actividades ha realizado el colectivo?",
        "medio ambiente y sostenibilidad"
    ]

    try:
        from tools.memory import query_collective_memory

        for query in test_queries:
            print(f"\n🔍 Query: \"{query}\"")
            print("-" * 40)

            # Call the tool directly (it's a @tool decorated function)
            result = query_collective_memory.invoke({"question": query, "num_results": 2})

            # Show first 500 chars of result
            if len(result) > 500:
                print(result[:500] + "...\n[truncated]")
            else:
                print(result)

        print("\n✅ RAG queries working!")

    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "="*60)
    print("✅ RAG SYSTEM TEST PASSED!")
    print("="*60)
    print("""
Your RAG system is working correctly:
- OpenAI embeddings: ✅
- Document loading: ✅
- Vector database: ✅
- Similarity search: ✅

You can now use the agent to query the collective's memory.
""")
    return True


if __name__ == "__main__":
    success = test_rag()
    sys.exit(0 if success else 1)

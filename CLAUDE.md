# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **agipro-agent**, a Python-based social media content generation system for "Colectivo Ambiental de Usaca - CAUSA", an environmental and social collective based in Bogotá, Colombia. The system automatically generates social media posts, creates associated images, and manages content locally using CSV files for easy review and publishing.

## Key Architecture

### Core Components

- **`main.py`**: Orchestration script that runs the complete pipeline - content generation, image creation, and local file management
- **`agent.py`**: LangGraph-based AI agent system using OpenAI LLM that generates contextualized social media content based on news, ephemerides, and collective activities
- **`images.py`**: OpenAI GPT-Image-1 integration for generating social media images using línea gráfica as visual style references
- **`csv_manager.py`**: Local file management system using CSV files and JSON configuration

### Data Flow

1. **Content Generation**: Agent searches for current news and ephemerides, combines with collective's memory documents
2. **Content Review**: Second AI pass validates and corrects generated content
3. **Draft Storage**: Posts saved as CSV files in `publicaciones/drafts/posts_YYYY-MM-DD.csv`
4. **Image Generation**: GPT-Image-1 creates branded images using línea gráfica images as visual style references
5. **Local Management**: All data stored locally for frontend review and publishing

### Directory Structure

- **`src/`**: Main source code
- **`src/memory/`**: PDF documents containing collective's historical contributions and ideology
- **`src/linea_grafica/`**: Brand guideline images for consistent visual styling
- **`src/publicaciones/`**: Generated content and images output directory
  - **`drafts/`**: CSV files with draft posts (one file per date)
  - **`imagenes/`**: Generated social media images
  - **`settings.json`**: Configuration file (posts_per_day, cleanup_months)
  - **`published_posts.csv`**: Record of published content

## Installation & Running

### Quick Start
```bash
# Clone and install
git clone https://github.com/your-username/agipro-agent.git
cd agipro-agent
./install.sh  # macOS/Linux
# or: install.bat  # Windows

# Activate environment and run
source venv/bin/activate
cd src && streamlit run app.py
```

### Manual Installation
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r src/requirements.txt
cp .env.example .env  # Add your OPENAI_API_KEY
cd src && streamlit run app.py
```

### Development Commands
```bash
# Streamlit UI (recommended)
cd src && streamlit run app.py

# Full pipeline (legacy batch mode)
python src/main.py

# Content generation only
python src/agent.py

# Image generation only (requires existing CSV)
python src/images.py
```

### Dependencies
Requirements are managed in `src/requirements.txt`. Key dependencies:
- LangChain + LangGraph for AI workflows
- OpenAI for LLM inference, embeddings, and image generation (DALL-E 3)
- ChromaDB for vector storage (uses OpenAI embeddings)
- pandas for CSV management
- Streamlit for web UI

### LLM Model Configuration
- **Model**: `gpt-5-nano` (OpenAI's reasoning model)
- **Temperature**: 1 (not top_p)
- **Reasoning Effort**: medium
- **Max Tokens**: 8192
- **Usage**: Both ContentGenerator and ContentReviewer classes use this configuration

### Image Generation Configuration
- **Default Size**: `1024x1536px` (2:3 portrait - best engagement on Instagram/Facebook)
- **Quality**: High
- **Model**: gpt-image-1 (GPT-Image-1)
- **Method**: Uses `/v1/images/edit` endpoint with línea gráfica images as visual references
- **Input Fidelity**: High (closely matches reference style)
- **Format**: Single image per post (replaces separate Instagram/Facebook images)

#### Available Image Sizes
The agent can choose the optimal size based on content:

| Size | Aspect Ratio | Best For | Token Cost (High) |
|------|-------------|----------|-------------------|
| `1024x1536` | 2:3 portrait | Instagram/Facebook feeds, people, events | 6240 tokens |
| `1024x1024` | 1:1 square | Twitter, LinkedIn, universal, logos | 4160 tokens |
| `1536x1024` | 3:2 landscape | Banners, panoramas, group photos | 6208 tokens |
| `auto` | Model decides | When unsure | Varies |

#### Agent Size Selection Guide
The agent uses this guidance to select sizes:
- **Portrait (1024x1536)**: People, events, vertical scenes, nature with trees, buildings
- **Square (1024x1024)**: Logos, icons, balanced subjects, profile-style images
- **Landscape (1536x1024)**: Panoramas, groups, wide scenes, banners, headers

#### Visual Style Reference System
The image generation uses the edit endpoint instead of generate, passing brand images as references:
```python
# Up to 5 images from linea_grafica/ are sent as visual style references
client.images.edit(
    model="gpt-image-1",
    image=[open(img, "rb") for img in style_images],  # Reference images
    prompt=enhanced_prompt,
    size="1024x1536",  # Agent can override based on content
    quality="high",
    input_fidelity="high"  # Match reference style closely
)
```
This ensures consistent brand aesthetics across all generated images.

## Configuration

### Environment Variables (.env)
- **API Keys**: OpenAI (DuckDuckGo search requires no API key)

### Local Configuration
- **Settings**: `publicaciones/settings.json` contains user preferences
- **Posts per Day**: Configurable from 1-6 posts
- **Activities Sheet**: External Google Sheet `1dL7ngg0P-E9QEiWCDtS5iF2ColQC7YVIM4pbIPQouuE` (read-only)
- **Auto-cleanup**: Removes files older than 4 months by default

### CSV File Structure
```csv
fecha,titulo,imagen,descripcion,status,created_at,image_path
2024-09-27,"Post title","Image description","Content with hashtags",draft,2024-09-27T10:00:00,publicaciones/imagenes/image.png
```

## Content Generation Logic

The system generates 3 types of posts per day:
1. **News-based**: Current events from Colombia/Bogotá relevant to environmental/social causes
2. **Ephemerides**: Historical commemorations aligned with collective values
3. **Activity announcements**: From the collective's confirmed activities calendar

Content must align with the collective's focus areas: environmentalism, animal rights, human rights, popular education, culture, and memory preservation.

## Conversational Agent System (New Architecture)

The system now features a **conversational AI agent** that replaces the rigid batch-generation workflow with a flexible, tool-based approach inspired by [Deep Agents](https://github.com/langchain-ai/deepagents).

### Agent Architecture

```
User Chat → CAUSA Agent → Tools → Response
                ↓
        [search_web]
        [search_ephemerides]
        [query_collective_memory]
        [get_activities]
        [read_past_publications]
        [save_draft_post]
        [generate_image]
```

### Core Agent Components

- **`causa_agent.py`**: Main LangGraph ReAct agent with conversation support
- **`chat_interface.py`**: Streamlit chat UI for conversational interaction
- **`tools/`**: Package containing all agent tools
  - `web_search.py`: Flexible web search (DuckDuckGo)
  - `publications.py`: Read history, save drafts, get activities
  - `memory.py`: RAG search on collective documents
  - `images.py`: DALL-E 3 image generation

### Agent Features

1. **Flexible Content Creation**: Create 1 post or many, based on conversation
2. **History Awareness**: Reads past publications to avoid repetition
3. **Dynamic Research**: Agent decides what to search and when
4. **Human-in-the-Loop**: Images generated only after user approval
5. **Conversation Memory**: Maintains context across multi-turn conversations

### Running the Agent

```bash
# Chat mode via Streamlit UI
streamlit run app.py
# Navigate to "Chat con Agente" in sidebar

# CLI mode for testing
python src/causa_agent.py

# Direct Python usage
from causa_agent import create_causa_agent, chat
agent = create_causa_agent()
response = chat(agent, "Create a post about climate action")
```

### Agent Tools Reference

| Tool | Purpose | Parameters |
|------|---------|------------|
| `search_web` | Flexible web search | query, search_type, max_results |
| `search_ephemerides` | Historical events for a date | date (YYYY-MM-DD) |
| `query_collective_memory` | RAG on memory docs | question, num_results |
| `get_collective_themes` | Overview of focus areas | (none) |
| `get_activities` | Confirmed activities | (none) |
| `read_past_publications` | Recent posts history | days_back, include_published |
| `save_draft_post` | Save individual post | fecha, titulo, imagen, descripcion |
| `generate_image` | GPT-Image-1 generation | titulo, imagen_description, fecha, size |
| `regenerate_image` | Regenerate with changes | titulo, imagen_description_original, cambios, fecha, size |
| `preview_image_prompt` | Preview image prompt | titulo, imagen_description, size |

### Agent Workflow Example

1. User: "Create a post about the climate march"
2. Agent uses `search_web` to find news
3. Agent uses `read_past_publications` to check for duplicates
4. Agent uses `query_collective_memory` for context
5. Agent presents draft post to user
6. User approves → Agent uses `generate_image`
7. Agent uses `save_draft_post` to store result

## Streamlit UI System

### UI Components
- **`app.py`**: Main Streamlit application with navigation to Chat and Dashboard
- **`chat_interface.py`**: Conversational interface with the CAUSA agent
- **`config_manager.py`**: Secure configuration and API key management
- **`file_manager.py`**: File upload, deletion, and management system
- **`publication_editor.py`**: Post editing interface with bulk operations

### UI Features
- **Chat Interface**: Conversational content creation with quick actions
- **Configuration Interface**: All prompts, topics, and settings configurable
- **File Management**: Drag & drop upload for memory documents and brand images
- **Publication Editor**: Modal editors, bulk operations, image preview
- **Secure API Management**: Encrypted local storage of API keys
- **Google Sheets Integration**: Configurable sheet ID and name

### Running the UI
```bash
# Install dependencies
cd src
pip install -r requirements.txt

# Run Streamlit UI (includes Chat and Dashboard)
streamlit run app.py
```

### Legacy Batch Generation
The original batch generation system is still available via:
- Navigation: "Generar (Legacy)" in sidebar
- CLI: `python src/main.py`
- Direct: `python src/agent.py`

## Development Lessons & Common Errors

### Session Learning Summary
During the development of the Streamlit UI system, several critical issues were identified and resolved:

#### 1. **Google Sheets URL Encoding Issue**
**Error**: `URL can't contain control characters` when sheet name contains spaces
```
Error: '/spreadsheets/d/.../sheet=Hoja 1' (found at least ' ')
```
**Cause**: Space in "Hoja 1" sheet name not URL-encoded
**Solution**: Added proper URL encoding in `agent.py`
```python
from urllib.parse import quote
encoded_sheet_name = quote(sheet_name)
url = f'https://docs.google.com/spreadsheets/d/{gsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}'
```

#### 2. **LangGraph "creator" Error**
**Error**: `Error en la generación: "creator"`
**Cause**: Incorrect LangGraph workflow configuration
**Solutions Applied**:
- Removed redundant `set_finish_point()` call
- Fixed `add_messages` import and usage
- Proper StateGraph edge configuration

#### 4. **ChatPromptTemplate Formatting Error**
**Error**: `Error en la generación: "creationdate"`
**Root Cause**: **Mixing f-string syntax with ChatPromptTemplate placeholders**

**Problematic Code**:
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""{system_message}
    Genera {{posts_per_day}} publicaciones para la fecha: {{current_date}}
    ACTIVIDADES: {activities}  # ❌ Immediate f-string formatting
    NOTICIAS: {news}           # ❌ Would fail - variables not defined
    """)
])
```

**Fixed Code**:
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", system_message + """
    Genera {posts_per_day} publicaciones para la fecha: {current_date}
    ACTIVIDADES: {activities}  # ✅ Proper template placeholder
    NOTICIAS: {news}          # ✅ Proper template placeholder
    """)
])
```

**Key Learning**: Never mix f-string formatting (`f"""{var}`) with ChatPromptTemplate placeholders (`{template_var}`). Use string concatenation instead.

#### 5. **LLM Model Configuration**
**Initial Error**: Used non-existent model names
**Final Configuration**:
```python
ChatOpenAI(
    model="gpt-5-nano",
    temperature=1,
    max_tokens=40192,
    reasoning_effort="medium"
)
```

### Development Best Practices Learned

#### 1. **Template System Design**
- Use consistent placeholder syntax throughout
- Avoid mixing string formatting approaches
- Test template variables before deployment

#### 2. **Error Handling Strategy**
- Read error messages carefully - "creator" and "creationdate" were misleading
- The actual issue was template formatting, not graph creation
- Always check prompt template syntax when LLM calls fail

#### 3. **Configuration Management**
- Centralized configuration through `ConfigManager`
- Encrypted local storage for sensitive data
- Environment variable synchronization

#### 4. **UI Development Approach**
- Modular component design
- Consistent error messaging
- Progressive feature implementation

### Debugging Workflow
1. **Identify Error Pattern**: Look beyond surface error messages
2. **Check Dependencies**: Ensure all packages are installed
3. **Validate Templates**: Test prompt formatting separately
4. **Trace Data Flow**: Follow variables from input to LLM
5. **Test Components**: Isolate issues in individual modules

#### 6. **Image Path Synchronization Issue**
**Error**: UI shows images only for first date, not subsequent dates
**Root Cause**: `update_image_path()` method assumed one CSV per date, but system stores multiple dates in single CSV
**Symptoms**:
- Images generated successfully for all dates
- Image files exist in `/imagenes/` folder
- CSV `image_path` column empty for some posts
- UI shows images only for posts with populated `image_path`

**Solution**: Enhanced `update_image_path()` to search across all CSV files:
```python
# Before: Only looked in posts_{fecha}.csv
draft_file = self.drafts_dir / f"posts_{fecha}.csv"

# After: Search all draft files if specific date file doesn't exist
if not draft_file.exists():
    draft_files = list(self.drafts_dir.glob("posts_*.csv"))
```

### Future Development Notes
- Always URL-encode user-provided sheet names
- Validate template syntax before LangGraph execution
- Implement proper error boundaries in Streamlit UI
- Consider template validation utilities for complex prompts
- **Image path updates**: Ensure image path synchronization works across multi-date CSV files
- **Universal image format**: Use 1080x1080px for optimal cross-platform compatibility and cost efficiency

## System Optimizations

### Universal Image Format (Latest Update)
The system now generates **single universal images** instead of separate platform-specific images:

#### **Configuration:**
- **Size**: 1024x1024px (1:1 square format)
- **Quality**: High (DALL-E 3)
- **Compatibility**: Instagram, Facebook, Twitter, LinkedIn, WhatsApp, Telegram

#### **Benefits:**
- **50% cost reduction**: Half the DALL-E API calls
- **50% faster generation**: Single image per post
- **50% less storage**: Simplified file management
- **Universal compatibility**: Works across all major platforms

#### **Technical Implementation:**
```python
# New universal format
self.universal_size = "1080x1080"

# Single image generation
df['universal_image'] = ''  # Replaces instagram_image + facebook_image

# Backward compatibility maintained
if 'universal_image' in df.columns:
    image_path = row['universal_image']
else:
    # Fallback to old format
    for col in ['instagram_image', 'facebook_image']:
        if col in df.columns and pd.notna(row[col]):
            image_path = row[col]
            break
```

### Error Resolution Summary
This session resolved several critical system issues:

1. **✅ Google Sheets URL encoding** - Fixed space character handling
2. **✅ LangGraph workflow errors** - Fixed StateGraph configuration
3. **✅ ChatPromptTemplate formatting** - Resolved f-string/template mixing
4. **✅ Image path synchronization** - Fixed multi-date CSV handling
5. **✅ UI TypeError fixes** - Added NaN protection for pandas DataFrames
6. **✅ Universal image format** - Optimized for cost and compatibility

### Performance Improvements
- **Reduced API costs**: 50% fewer DALL-E calls
- **Faster generation**: Single image per post
- **Better error handling**: Comprehensive NaN protection
- **Improved synchronization**: Cross-file image path updates
- **Enhanced compatibility**: Universal social media format

**Privacy Policy**
https://www.termsfeed.com/live/72a5f116-1efd-4516-83a7-ee84638dee81

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **agipro-agent**, a Python-based social media content generation system for "Colectivo Ambiental de Usaca - CAUSA", an environmental and social collective based in Bogotá, Colombia. The system automatically generates social media posts, creates associated images, and manages content locally using CSV files for easy review and publishing.

## Key Architecture

### Core Components

- **`main.py`**: Orchestration script that runs the complete pipeline - content generation, image creation, and local file management
- **`agent.py`**: LangGraph-based AI agent system using OpenAI LLM that generates contextualized social media content based on news, ephemerides, and collective activities
- **`images.py`**: OpenAI DALL-E 3 integration for generating social media images with brand consistency
- **`csv_manager.py`**: Local file management system using CSV files and JSON configuration

### Data Flow

1. **Content Generation**: Agent searches for current news and ephemerides, combines with collective's memory documents
2. **Content Review**: Second AI pass validates and corrects generated content
3. **Draft Storage**: Posts saved as CSV files in `publicaciones/drafts/posts_YYYY-MM-DD.csv`
4. **Image Generation**: DALL-E 3 creates branded images based on content descriptions
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

## Development Commands

### Running the System
```bash
# Full pipeline (from project root)
python src/main.py

# Content generation only
python src/agent.py

# Image generation only (requires existing CSV)
python src/images.py
```

### Docker Deployment
```bash
# Build image
docker build -t agipro-agent .

# Run container
docker run agipro-agent
```

### Dependencies
Requirements are managed in `src/requirements.txt`. Key dependencies:
- LangChain + LangGraph for AI workflows
- OpenAI for LLM inference and image generation (DALL-E 3)
- pandas for CSV management

### LLM Model Configuration
- **Model**: `gpt-5-nano` (OpenAI's reasoning model)
- **Temperature**: 1 (not top_p)
- **Reasoning Effort**: medium
- **Max Tokens**: 8192
- **Usage**: Both ContentGenerator and ContentReviewer classes use this configuration

### Image Generation Configuration
- **Size**: `1024x1024px` (1:1 square format - universal for all social media, DALL-E 3 compatible)
- **Quality**: High
- **Model**: gpt-image-1 (DALL-E 3)
- **Format**: Single image per post (replaces separate Instagram/Facebook images)
- **Compatibility**: Works across Instagram, Facebook, Twitter, LinkedIn, WhatsApp, Telegram

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

## Streamlit UI System

### New UI Components
- **`app.py`**: Main Streamlit application with full UI interface
- **`config_manager.py`**: Secure configuration and API key management
- **`file_manager.py`**: File upload, deletion, and management system
- **`publication_editor.py`**: Post editing interface with bulk operations

### UI Features
- **Configuration Interface**: All prompts, topics, and settings configurable through UI
- **File Management**: Drag & drop upload for memory documents and brand images
- **Publication Editor**: Modal editors, bulk operations, image preview
- **Secure API Management**: Encrypted local storage of API keys
- **Google Sheets Integration**: Configurable sheet ID and name

### Running the UI
```bash
# Install dependencies
cd src
pip install -r requirements.txt

# Run Streamlit UI
streamlit run app.py
```

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

#### 2. **Missing Dependencies Error**
**Error**: `Package 'sentence-transformers' is not installed`
**Cause**: Required package not listed in requirements.txt
**Solution**: Added missing dependency to requirements.txt

#### 3. **LangGraph "creator" Error**
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
2. **✅ Missing dependencies** - Added sentence-transformers
3. **✅ LangGraph workflow errors** - Fixed StateGraph configuration
4. **✅ ChatPromptTemplate formatting** - Resolved f-string/template mixing
5. **✅ Image path synchronization** - Fixed multi-date CSV handling
6. **✅ UI TypeError fixes** - Added NaN protection for pandas DataFrames
7. **✅ Universal image format** - Optimized for cost and compatibility

### Performance Improvements
- **Reduced API costs**: 50% fewer DALL-E calls
- **Faster generation**: Single image per post
- **Better error handling**: Comprehensive NaN protection
- **Improved synchronization**: Cross-file image path updates
- **Enhanced compatibility**: Universal social media format

**Privacy Policy**
https://www.termsfeed.com/live/72a5f116-1efd-4516-83a7-ee84638dee81

# CAUSA - Streamlit UI Documentation

## 🚀 Quick Start

### Installation

1. Install the new dependencies:
```bash
cd src
pip install -r requirements.txt
```

2. Run the new Streamlit UI:
```bash
streamlit run app.py
```

The application will open in your web browser at `http://localhost:8501`

### First-Time Setup

1. **Configure API Keys** (Configuration → API Keys tab):
   - Add your OpenAI API Key (for DALL-E 3 image generation)
   - Add your Groq API Key (for LLM content generation)

2. **Upload Memory Documents** (Files → Memoria tab):
   - Upload PDF and TXT files containing collective's ideology and history

3. **Upload Brand Images** (Files → Línea Gráfica tab):
   - Upload PNG/JPG images that define the visual style

4. **Configure Settings** (Configuration → General tab):
   - Set posts per day (1-6)
   - Set days to generate content for
   - Set collective topics

## 🎛️ Main Features

### 🏠 Dashboard
- Overview of system status
- Quick statistics (drafts, published posts, files)
- System health indicators
- Quick action buttons

### ✨ Generate Content
- **Configurable Parameters**: Days to generate, posts per day
- **Custom Topics**: Editable collective topics string
- **Image Generation**: Optional DALL-E 3 integration
- **Advanced Options**: Custom prompts, timeline settings
- **Progress Tracking**: Real-time generation progress

### 📝 Publications Management
- **Individual Editing**: Modal editors for each post
- **Bulk Operations**:
  - Delete multiple posts
  - Change dates in batch
  - Mark as published
- **Filtering & Sorting**: By date, title, creation time
- **Image Preview**: See generated images
- **Add to Brand**: Copy generated images to línea gráfica

### 📁 File Management

#### 📚 Memory Documents
- **Drag & Drop Upload**: Multiple PDF/TXT files
- **File Information**: Size, modification date, type
- **Bulk Delete**: Select and delete multiple files

#### 🎨 Línea Gráfica Images
- **Image Upload**: PNG, JPG, GIF, WebP support
- **Bulk Management**: Select and delete multiple images
- **File Details**: Size and modification info

#### 🖼️ Generated Images
- **Visual Preview**: Thumbnail previews of all generated images
- **Add to Brand**: One-click copy to línea gráfica folder
- **Management**: Delete unwanted generated images

### ⚙️ Configuration

#### 🔑 API Keys
- **Secure Storage**: Encrypted local storage
- **Easy Management**: Input fields with password masking
- **Auto .env Update**: Automatically updates .env file
- **Connection Testing**: Test API connections (coming soon)

#### 📋 General Settings
- **Posts per Day**: 1-6 configurable posts
- **Generation Timeline**: Days from today
- **Auto-cleanup**: Months before auto-deletion
- **Collective Topics**: Freely editable topics string

#### 💬 Prompts Configuration
- **System Message**: Main AI behavior prompt
- **Content Prompts**: News, ephemerides, activities
- **Image Prompts**: DALL-E 3 generation instructions
- **Reset Option**: Restore default prompts

#### 📊 Google Sheets Integration
- **Sheet ID Configuration**: Change source Google Sheet
- **Sheet Name**: Configure specific sheet name
- **Instructions**: Setup guidance for public sheets

## 🔧 Technical Details

### New Components Created:
- **`config_manager.py`**: Secure configuration and API key management
- **`file_manager.py`**: File upload, deletion, and management
- **`publication_editor.py`**: Post editing and bulk operations
- **`app.py`**: Main Streamlit application

### Security Features:
- **Encrypted API Keys**: Using Fernet encryption
- **Local Storage**: All sensitive data stored locally
- **No Remote Dependencies**: Self-contained system

### Integration:
- **Backward Compatible**: Works with existing `main.py`, `agent.py`, `images.py`
- **Enhanced Configuration**: Existing modules now use configurable settings
- **Preserved Functionality**: All original features maintained

## 📖 Usage Workflow

1. **Setup**: Configure API keys and upload memory/brand files
2. **Generate**: Create new content with custom parameters
3. **Review**: Edit individual posts or perform bulk operations
4. **Manage**: Organize files and generated images
5. **Configure**: Adjust prompts and settings as needed

## 🔄 Migration from Old System

The new UI is fully compatible with the existing system:

- **Existing CSV files** are automatically recognized
- **Memory and línea gráfica folders** work as before
- **Generated images** are compatible
- **Old main.py** can still be used for command-line operation

## 🎯 Advanced Features

- **Custom Prompts**: Full control over AI behavior
- **Flexible Timeline**: Generate for any number of days ahead
- **Visual Management**: See all content before publishing
- **Bulk Operations**: Efficient multi-post editing
- **Smart Filters**: Find posts by various criteria
- **Secure Config**: Encrypted, local configuration storage

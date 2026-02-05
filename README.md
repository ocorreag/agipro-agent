# CAUSA Agent - Social Media Content Generator

AI-powered social media content generation system for **Colectivo Ambiental de Usaca - CAUSA**, an environmental and social collective based in Bogotá, Colombia.

## Features

- **AI Content Generation**: Creates contextual social media posts based on news, historical dates, and collective activities
- **Image Generation**: DALL-E 3 integration for branded social media images
- **RAG Memory**: Searches collective's documents to ensure content alignment
- **Web Interface**: Streamlit-based chat interface and content management dashboard
- **Local Storage**: All data stored locally in CSV files for easy review

## Quick Start

### Prerequisites

- Python 3.11 or higher
- OpenAI API key

### Installation

**Option 1: Using install script (recommended)**

```bash
# Clone the repository
git clone https://github.com/your-username/agipro-agent.git
cd agipro-agent

# Run install script
# macOS/Linux:
./install.sh

# Windows (Command Prompt - cmd.exe):
install.bat

# Windows (PowerShell):
.\install.bat
```

**Option 2: Manual installation**

```bash
# Clone the repository
git clone https://github.com/your-username/agipro-agent.git
cd agipro-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r src/requirements.txt

# Copy environment file and add your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Start the application
cd src
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### First-Time Setup

1. Go to **Configuration** tab
2. Enter your **OpenAI API Key**
3. (Optional) Upload memory documents in **Files > Memoria**
4. (Optional) Upload brand images in **Files > Línea Gráfica**

## Usage

### Chat Interface
Navigate to "Chat con Agente" to have a conversation with the AI agent. You can:
- Request posts about specific topics
- Ask for news-based content
- Request historical commemorations (ephemerides)
- Generate images for approved content

### Dashboard
View and manage all generated content:
- Edit individual posts
- Generate images
- Mark posts as published
- Delete unwanted content

### Legacy Batch Generation
For automated batch generation:
```bash
cd src
python main.py
```

## Project Structure

```
agipro-agent/
├── src/                    # Source code
│   ├── app.py             # Main Streamlit application
│   ├── causa_agent.py     # AI agent with tools
│   ├── chat_interface.py  # Chat UI component
│   ├── images.py          # DALL-E 3 integration
│   ├── csv_manager.py     # Data management
│   └── tools/             # Agent tools
├── publicaciones/         # Generated content (created at runtime)
│   ├── drafts/           # Draft posts (CSV)
│   └── imagenes/         # Generated images
├── memory/               # Collective documents (created at runtime)
├── linea_grafica/        # Brand images (created at runtime)
├── .env.example          # Environment template
└── requirements.txt      # Python dependencies
```

## Configuration

### Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Google Sheets for activities calendar
GOOGLE_SHEETS_ID=your_google_sheets_id_here
GOOGLE_SHEETS_NAME=Hoja 1

# Content settings
POSTS_PER_DAY=3
DAYS_TO_GENERATE=2
```

## Requirements

- Python 3.11+
- OpenAI API key with access to:
  - GPT models (for content generation)
  - DALL-E 3 (for image generation)
  - Embeddings API (for RAG memory search)

## Troubleshooting

### Windows: "install.bat no se reconoce" in PowerShell
In PowerShell, you need to use `.\` prefix:
```powershell
.\install.bat
```
Or use Command Prompt (cmd.exe) instead.

### Windows: "Microsoft Visual C++ 14.0 required" error
If you see errors about `hnswlib` or C++ Build Tools, first ensure you're using the latest requirements:
```bash
pip install --upgrade pip
pip install -r src/requirements.txt
```

If the error persists, you may have an old cached package. Clear and reinstall:
```bash
pip cache purge
pip install -r src/requirements.txt
```

### "Module not found" errors
Make sure you've activated the virtual environment:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### API key issues
1. Verify your OpenAI API key is valid
2. Check you have credits in your OpenAI account
3. Ensure the key has access to GPT and DALL-E models

### Port already in use
If port 8501 is busy, Streamlit will automatically try the next available port. Check the terminal output for the correct URL.

## License

This project is for use by Colectivo Ambiental de Usaca - CAUSA.

## Privacy Policy

https://www.termsfeed.com/live/72a5f116-1efd-4516-83a7-ee84638dee81

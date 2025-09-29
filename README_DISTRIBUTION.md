# CAUSA Agent - Desktop Distribution Guide

This guide explains how to build and distribute the CAUSA Agent desktop application for Windows and macOS.

## Quick Start (Local Building)

### Prerequisites
- Python 3.11+ installed
- Git repository cloned
- OpenAI API key ready for testing

### Build Locally

1. **Navigate to project root:**
   ```bash
   cd agipro-agent
   ```

2. **Run the build script:**
   ```bash
   python build_scripts/build_local.py
   ```

3. **Test the application:**
   - **Windows**: Extract `CAUSA-Agent-Windows.zip` and run `CAUSA-Agent.exe`
   - **macOS**: Mount `CAUSA-Agent-macOS.dmg` and run `CAUSA-Agent.app`

## Automated Builds (GitHub Actions)

### Setting Up Releases

1. **Push a version tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Actions will automatically:**
   - Build Windows `.exe` and macOS `.app`
   - Create installers (`.zip` for Windows, `.dmg` for macOS)
   - Create a GitHub release with download links

### Manual Trigger
You can also trigger builds manually from GitHub Actions tab without creating a tag.

## Distribution Files

### Windows Distribution
- **File**: `CAUSA-Agent-Windows.zip`
- **Contents**: `CAUSA-Agent.exe` + README
- **Installation**: Extract and double-click to run
- **Requirements**: Windows 10+ (no Python installation needed)

### macOS Distribution
- **File**: `CAUSA-Agent-macOS.dmg`
- **Contents**: `CAUSA-Agent.app` bundle
- **Installation**: Mount DMG, drag to Applications
- **Requirements**: macOS 10.14+ (no Python installation needed)

## User Instructions

### First Time Setup
1. Download the appropriate file for your system
2. Install/extract the application
3. Run CAUSA Agent
4. Browser will open automatically to `http://localhost:8501`
5. Go to **Configuration** tab
6. Enter your OpenAI API key
7. Configure other settings as needed

### Data Storage
- All data is stored locally on the user's machine
- **Windows**: Next to the executable
- **macOS**: In the app bundle directory
- Folders created automatically:
  - `publicaciones/` - Generated content and images
  - `memory/` - User-uploaded documents
  - `linea_grafica/` - Brand guideline images

### Sharing with Friends

#### Option 1: Direct File Sharing
- Upload built files to Google Drive, Dropbox, etc.
- Share download links with instructions

#### Option 2: GitHub Releases
- Push version tags to trigger automated builds
- Direct friends to GitHub releases page
- Professional download experience

#### Option 3: Website Distribution
- Host files on your website
- Provide download page with instructions

## Troubleshooting

### Build Issues

**PyInstaller not found:**
```bash
pip install pyinstaller
```

**Missing dependencies:**
```bash
cd src
pip install -r requirements.txt
```

**macOS DMG creation fails:**
```bash
brew install create-dmg
```

### Runtime Issues

**Windows: "Windows protected your PC"**
- Click "More info" → "Run anyway"
- This is normal for unsigned executables

**macOS: "Cannot open because developer cannot be verified"**
- Right-click → "Open" → "Open" (first time only)
- Or: System Preferences → Security & Privacy → "Open Anyway"

**Application won't start:**
- Check that port 8501 isn't already in use
- Try running from terminal to see error messages

### User Support

**Common user issues:**
1. **API key not working**: Verify OpenAI API key is correct
2. **No images generated**: Check OpenAI account has credits
3. **App won't open**: Port conflict, try restarting

## File Structure After Build

```
CAUSA-Agent/
├── CAUSA-Agent.exe (or .app)    # Main executable
├── publicaciones/               # Generated content (created on first run)
│   ├── drafts/                 # Draft posts CSV files
│   ├── imagenes/               # Generated images
│   └── settings.json           # User preferences
├── memory/                     # User documents (created on first run)
├── linea_grafica/             # Brand images (created on first run)
├── .env                       # Configuration file (created on first run)
└── README.txt                 # User instructions
```

## Version Management

### Version Numbering
- Use semantic versioning: `v1.0.0`, `v1.1.0`, etc.
- Tag format triggers automatic builds: `v*`

### Release Notes Template
```markdown
## CAUSA Agent v1.0.0

### New Features
- Social media content generation with AI
- DALL-E 3 image generation
- Local content storage and management

### Installation
- Windows: Download and extract ZIP file
- macOS: Download and mount DMG file

### Requirements
- OpenAI API key
- Internet connection for AI generation
```

## Security Considerations

- API keys are stored encrypted locally
- No data is sent to external servers (except OpenAI for generation)
- All content remains on user's machine
- User controls all data and file access

## Development Notes

### Testing Builds
Always test built applications on clean machines without Python installed to ensure they work for end users.

### File Size Optimization
- Current builds are ~300-500MB due to Python runtime
- Consider excluding unnecessary packages in future versions
- UPX compression is enabled to reduce size

### Future Improvements
- Code signing certificates for trusted distribution
- Auto-updater functionality
- Installer packages (MSI for Windows, PKG for macOS)
- Digital signatures for enhanced security
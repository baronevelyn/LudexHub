# 🎮 LudexHub v1.1

A modern desktop application for Windows that centralizes your entire game collection with automatic import from Steam and Epic Games Store, featuring a sleek borderless interface, advanced theme customization, automatic updates, and extensive organization tools.

---

## 📚 Documentation

- **[🗺️ v1.1 Roadmap](ROADMAP.md)** - Completed features and development progress
- **[📜 License](LICENSE)** - MIT License
- **[🔄 Changelog](CHANGELOG.md)** - Version history and updates

---

## ✨ Features

### 📚 Game Management
- **Automatic Steam Import** - Detects and imports all your Steam games with proper metadata
- **Automatic Epic Games Import** - Scans and adds Epic Games Store titles seamlessly
- **Manual Game Addition** - Add any game with custom name, executable path, and cover image
- **Smart Image Fallback** - If Epic doesn't provide artwork, automatically fetches from Steam
- **Real-time Search** - Quickly find games as you type
- **Dual View Modes** - Switch between Grid and List layouts
- **⭐ Favorites System** - Mark and filter your favorite games
- **🎯 Advanced Filtering** - Filter by platform (Steam/Epic/Manual) and favorites
- **📊 Sorting Options** - Sort by name, last played, playtime, or date added
- **Auto Icon Extraction** - Extracts icons directly from .exe files
- **Image Caching** - Fast loading with local cache system + Clear Cache button

### ⏱️ Playtime Tracking
- **Automatic Launch Tracking** - Detects when you start/stop playing
- **Total Playtime Display** - See hours/minutes per game
- **Toggle Tracking** - Enable/disable to reduce resource usage
- **Persistent Storage** - Playtime saved across sessions

### 🎨 Theme Customization (10 Presets + Custom)
- **Built-in Theme Presets**:
  - **Base** - Dark blue/purple gradient (original)
  - **Light** - Clean light theme
  - **Dark** - Deep dark with purple accents
  - **Pink** - Warm pink/magenta
  - **Cyberpunk** - Neon colors with sharp borders (NEW)
  - **Sunset** - Warm orange/red theme (NEW)
  - **Forest** - Green nature aesthetic (NEW)
  - **Ocean** - Cool blue professional (NEW)
  - **Retro** - 80s nostalgia theme (NEW)
  - **Minimal** - Clean minimalist design (NEW)
- **Full Customization**:
  - 14+ color values (gradients, accents, text, borders)
  - Typography (font family, title sizes, secondary text)
  - Spacing (card radius, padding, border width)
- **Live Preview** - See changes in real-time before applying
- **Custom Themes** - Save, load, and delete your own themes
- **Custom Backgrounds** - Set any image/GIF/video as wallpaper
- **Background Opacity** - Adjust background transparency
- **Background History** - Quick access to previous images

### 🎬 Animated Backgrounds
- **GIF Support** - Animate your background with GIF files
- **Video Support** - WebM/MP4 backgrounds (muted playback)
- **Performance Optimized** - Animations pause when off-screen to save resources
- **Smooth Playback** - ~30fps frame update rate
- **Type Selector** - Switch between static/animated/video in settings

### 🔄 Auto-Update System (NEW)
- **GitHub Integration** - Automatically checks for new releases
- **Smart Update Check** - On startup (configurable) with 1-hour cache
- **Manual Check** - "Check for Updates" button in Settings
- **Update Dialog** - Shows version, date, size before downloading
- **Download Progress** - Real-time progress bar with percentage and speed
- **Changelog Viewer** - View what's new in the update before installing
- **Safe Installation** - Automatic backup + batch script replacement
- **SHA256 Verification** - Checksum validation of downloads

### 🌍 Internationalization
- **Multi-language Support** - English and Spanish (60+ strings)
- **Dynamic Language Switching** - Change language on-the-fly
- **Complete Translations** - All dialogs, settings, and messages
- **Persistent Settings** - Language preference saved

### ⚙️ Settings & Configuration
- **Auto-start on Windows Startup** - Optional launch with system
- **Process Priority** - High/Normal/Low CPU priority selection
- **Playtime Tracking Toggle** - Enable/disable tracking
- **Auto-Update Toggle** - Check for updates automatically on startup
- **Theme Selection** - Quick preset or custom theme selection
- **Clear Cache Button** - Free up disk space from cached images
- **Language Selection** - Switch between ES/EN

### ⚡ Modern UI/UX
- **Borderless Window** - Sleek frameless design with custom title bar
- **Smooth Animations** - Fade-in effects with staggered timing
- **Minimize/Restore Animation** - Elegant transitions
- **Double-click Launch** - Open games directly
- **Platform Badges** - Visual Steam/Epic indicators
- **Responsive Design** - Adapts to different resolutions

---

## 🚀 Installation

### Option 1: Download Release (Recommended)
1. Go to [Releases](https://github.com/baronevelyn/LudexHub/releases) and download the latest `LudexHub-v1.1.0.zip`
2. Extract the ZIP file to your preferred location
3. Run `LudexHub.exe` - no installation required
4. On first launch:
   - Creates `~/.game_library` folder for data
   - Generates `games.json` and `theme.json`
   - Prompts for preferences
   - Auto-downloads fonts if needed
   - Auto-checks for updates (optional)

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/baronevelyn/LudexHub.git
cd LudexHub

# Install dependencies
pip install -r requirements.txt

# Run the application
python game_library.py
```

## 📋 Requirements

- **OS**: Windows 10 or later
- **Development**: Python 3.10+ (if running from source)
- **Dependencies**: 
  - PyQt5 5.15.10
  - requests 2.28.0+
  - opencv-python 4.12.0.88
  - packaging 21.0+
  - pyinstaller 6.3.0 (for building)
  - pywin32 (Windows API)

See `requirements.txt` for complete list.

## 🎯 Quick Start Guide

1. **Import Games**: 
   - Click "📥 Importar" → Choose Steam or Epic
   - Games automatically added to library

2. **Add Games Manually**:
   - Click "+ Agregar" → Fill in name, .exe path, cover image URL

3. **Organize**:
   - Use favorites (⭐) to mark important games
   - Create custom folders for organization
   - Filter by platform or favorites

4. **Customize Appearance**:
   - Click "⚙️" → Settings → Choose theme preset
   - Or customize colors, fonts, spacing manually
   - Preview changes before applying

5. **Launch Games**:
   - Double-click any game card to play
   - Playtime tracked automatically

6. **Keep Updated**:
   - Updates checked automatically on startup
   - Click "Check for Updates" anytime in Settings
   - One-click download and install

## 📁 Project Structure

```
LudexHub/
├── game_library.py          # Main application
├── auto_updater.py          # Auto-update system (NEW)
├── steam_scanner.py         # Steam library scanner
├── epic_scanner.py          # Epic Games scanner
├── font_installer.py        # Font management system
├── i18n.py                  # Internationalization
├── ROADMAP.md               # Development roadmap
├── README.md                # This file
├── game_library.spec        # PyInstaller config
├── requirements.txt         # Python dependencies
└── tests/                   # Unit tests
    ├── test_steam_scanner.py
    ├── test_epic_scanner.py
    └── test_epic_images.py
```

**User Data** (created at `~/.game_library/`):
```
.game_library/
├── games.json              # Game library database
├── theme.json              # User preferences & themes
├── update_cache.json       # Auto-update cache
├── icons/                  # Extracted game icons
├── steam_images/           # Cached Steam artwork
├── epic_images/            # Cached Epic artwork
├── fonts/                  # Custom fonts (JetBrains Mono, Inter)
└── __pycache__/            # Python cache
```

## 🛠️ Development

### Building the Executable
```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller game_library.spec

# Output: dist/LudexHub.exe
```

### Running Tests
```bash
python -m pytest tests/
```

### Code Quality
```bash
# Check syntax
python -m py_compile *.py

# Run all Python files through parser
python -m compileall .
```

## 📝 v1.1.0 Changes

### New Features
- ⭐ **Favorites System** - Mark and filter favorite games
- 🎨 **6 New Theme Presets** - Cyberpunk, Sunset, Forest, Ocean, Retro, Minimal
- 🔄 **Auto-Update System** - GitHub integration with changelog viewer
- 🧹 **Clear Cache Button** - Free up disk space
- ⏱️ **Playtime Tracking** - Track hours played per game

### Improvements
- Enhanced theme customization with 10 total presets
- Advanced sorting and filtering options
- Configurable playtime tracking
- Automatic process priority management
- Better animation performance with GIF pause optimization
- 60+ translation keys for complete i18n

### Bug Fixes
- Fixed crashes when switching Grid/List view rapidly
- Improved widget cleanup during animations
- Better error handling in font installation

## 🐛 Known Limitations

- Multiple game folder assignment (coming in v1.2)
- Folder persistence needs refinement
- No built-in cloud sync (planned for future)

## 📊 Statistics

- **Lines of Code**: ~5,500
- **Supported Platforms**: Steam, Epic Games, Manual
- **Languages**: Spanish, English
- **Theme Presets**: 10
- **Translation Keys**: 60+

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Developed with ❤️ by Eden

---

## 🙏 Contributing

Found a bug or want to contribute? Feel free to open an issue or submit a pull request!

---

**Enjoy organizing your game collection!** 🎮✨

**Latest Release**: v1.1.0 (December 7, 2025)

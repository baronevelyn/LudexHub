# 🎮 LudexHub v1.0

A modern desktop application for Windows that centralizes your entire game collection with automatic import from Steam and Epic Games Store, featuring a sleek borderless interface and extensive customization options.

## ✨ Key Features

### 📚 Game Management
- **Automatic Steam Import** - Detects and imports all your Steam games with proper metadata
- **Automatic Epic Games Import** - Scans and adds Epic Games Store titles seamlessly
- **Manual Game Addition** - Add any game with custom name, executable path, and cover image
- **Smart Image Fallback** - If Epic doesn't provide artwork, automatically fetches from Steam
- **Real-time Search** - Quickly find games as you type
- **Dual View Modes** - Switch between Grid and List layouts
- **Auto Icon Extraction** - Extracts icons directly from .exe files
- **Image Caching** - Fast loading with local cache system

### 🎨 Full Customization
- **Built-in Theme Presets**:
  - **Base** - Dark blue/purple gradient (default)
  - **Light** - Clean light theme with white backgrounds
  - **Dark** - Deep dark theme with purple accents
  - **Pink** - Warm pink/magenta theme
- **Custom Color Schemes** - Configure every UI element:
  - Background colors and accent gradients
  - Card colors (background, border, hover states)
  - Button colors and hover effects
- **Custom Backgrounds** - Set any image as wallpaper with opacity control
- **Background History** - Quick access to previously used images

### 🌍 Internationalization
- **Multi-language Support** - English and Spanish
- **Dynamic Language Switching** - Change language on-the-fly without restart
- **Persistent Settings** - Language preference saved across sessions

### ⚡ Modern UI/UX
- **Borderless Window** - Sleek frameless design with custom title bar
- **Smooth Animations** - Fade-in effects for game cards with staggered timing
- **Minimize/Restore Animation** - Elegant window state transitions
- **Launch Integration** - Double-click to launch games via Steam protocol or direct executable
- **Platform Badges** - Visual indicators for Steam and Epic games
- **Auto-start Option** - Launch at Windows startup (configurable)

## 🚀 Installation

### Option 1: Download Release (Recommended)
1. Go to [Releases](https://github.com/yourusername/LudexHub/releases) and download the latest `LudexHub-v1.0.zip`
2. Extract the ZIP file to your preferred location
3. Run `LudexHub.exe` - no installation required
4. On first launch:
   - Creates `~/.game_library` folder (icons, steam_images, epic_images)
   - Generates `games.json` and `theme.json`
   - Prompts for auto-startup preference and language selection

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/LudexHub.git
cd LudexHub

# Install dependencies
pip install -r requirements.txt

# Run the application
python game_library.py
```

## 📋 Requirements

- **OS**: Windows 10 or later
- **Development**: Python 3.10+ (if running from source)
- **Dependencies**: PyQt5 5.15.10, PyInstaller 6.3.0 (see `requirements.txt`)

## 🎯 Quick Start Guide

1. **Import Games**: Click "📥 Import Games" → Choose Steam or Epic
2. **Add Manually**: Click "+ Add Game" → Fill in name, .exe path, and cover image
3. **Customize**: Click "⚙️ Settings" → Choose theme preset or customize colors
4. **Search**: Use the "🔍 Search games..." box to filter your library
5. **Launch**: Double-click any game card to play
6. **Switch Views**: Use the Grid/List dropdown to change layout

## 📁 Project Structure

```
LudexHub/
├── game_library.py       # Main application
├── steam_scanner.py      # Steam library scanner
├── epic_scanner.py       # Epic Games scanner
├── i18n.py              # Internationalization module
├── game_library.spec    # PyInstaller build spec
├── requirements.txt     # Python dependencies
├── release/
│   ├── 1.0/
│   │   └── LudexHub.exe
│   └── LudexHub-v1.0.zip
└── tests/               # Unit tests
    ├── test_steam_scanner.py
    ├── test_epic_scanner.py
    └── test_epic_images.py
```

**User Data** (created at `~/.game_library/`):
- `icons/` - Extracted game icons
- `steam_images/` - Cached Steam artwork
- `epic_images/` - Cached Epic artwork
- `games.json` - Game library database
- `theme.json` - User preferences and theme settings

## 🛠️ Development

### Building the Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Build with spec file
pyinstaller game_library.spec

# Output: dist/LudexHub.exe
```

### Running Tests
```bash
python -m pytest tests/
```

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Developed with ❤️ by Eden

---

**Enjoy organizing your game collection!** 🎮✨

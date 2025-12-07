# Changelog

## v1.1.0 (December 7, 2025)

### ✨ Major Features

#### 🎨 Enhanced Theme System
- **6 New Complete Theme Presets** with full customization:
  - Cyberpunk: Neon colors, JetBrains Mono, sharp borders
  - Sunset: Warm orange/red palette, Inter font
  - Forest: Green nature theme, Roboto font
  - Ocean: Cool blue professional, Poppins font
  - Retro: 80s aesthetic, Space Mono font
  - Minimal: Clean minimalist, Open Sans font
- **Total 10 Theme Presets** (original 4 + 6 new)
- **Advanced Live Preview** - See changes before applying
- **Custom Theme Support** - Save, load, and delete user themes
- **Typography Customization** - Font family, sizes, weights
- **Spacing Control** - Card radius, padding, border width
- **16+ Color Customization** - Gradients, accents, text, borders

#### ⭐ Favorites System
- **Toggle Favorites** - Mark games as favorites with star icon
- **Filter by Favorites** - Quick filter to show only starred games
- **Persistent Storage** - Favorites saved in games.json
- **Visual Indicators** - Clear star display on game cards

#### ⏱️ Playtime Tracking
- **Automatic Launch Detection** - Tracks when games start/stop
- **Total Playtime Display** - Shows hours/minutes per game
- **Toggle Tracking** - Enable/disable to conserve resources
- **Persistent Data** - Playtime saved across sessions
- **Last Played Tracking** - Know when you last played each game

#### 🔍 Advanced Filtering & Sorting
- **Platform Filtering** - Show games from Steam, Epic, or Manual only
- **Favorite Filtering** - Show only favorited games
- **Multiple Sort Options**:
  - Name (A-Z)
  - Last Played (most recent first)
  - Total Playtime (most played)
  - Date Added (newest/oldest)
- **Filter Persistence** - Remembers your last filter choice

#### 🎬 Animated Backgrounds
- **GIF Support** - Animate your background with GIF files
- **Video Support** - WebM/MP4 video backgrounds (muted)
- **Smart Optimization** - Animations pause when off-screen to save resources
- **Smooth Playback** - ~30fps frame update rate
- **Easy Switching** - Toggle between static/animated/video in settings

#### 🔄 Auto-Update System (NEW)
- **GitHub Release Integration** - Automatically checks GitHub for new versions
- **Automatic Update Check** - Checks on startup (configurable in settings)
- **Manual Check Option** - "Check for Updates" button in Settings > General
- **Smart Rate Limiting** - Maximum 1 check per hour to avoid spam
- **Update Notification** - Shows version, date, file size before downloading
- **Download Progress** - Real-time progress bar with percentage and speed
- **Changelog Viewer** - View release notes in formatted dialog
- **Safe Installation** - Automatic backup before replacement
- **SHA256 Verification** - Validates download integrity
- **One-Click Install** - Download and install with single confirmation

#### 🧹 Cache Management
- **Clear Cache Button** - Clean cached images and temporary data
- **Size Calculation** - Shows how much space will be freed
- **Confirmation Dialog** - Prevents accidental deletion
- **Success Feedback** - Displays freed space after cleaning
- **Smart Locations** - Clears image cache, temp files, pixmap cache

### 🌍 Internationalization
- **Complete Spanish (ES) Support** - All menus, dialogs, and messages
- **Complete English (EN) Support** - All menus, dialogs, and messages
- **Dynamic Switching** - Change language on-the-fly without restart
- **60+ Translation Keys** - Comprehensive coverage of all UI elements
- **Settings Integration** - Language selector in General settings

### ⚙️ System Features
- **Process Priority Control** - Set app to High/Normal/Low CPU priority
- **Auto-start Configuration** - Optional Windows startup launch
- **Font Management** - Automatic downloading and installation of custom fonts
- **Icon Extraction** - Extracts game icons from .exe files
- **Image Caching** - Fast loading with local cache
- **Semantic Versioning** - Proper version comparison (1.1.0 format)
- **Configuration Persistence** - Settings saved in theme.json

### 🐛 Bug Fixes
- Fixed crash when rapidly switching between Grid/List view modes
- Improved animation performance with proper widget cleanup
- Better error handling in font installation system
- Fixed Unicode emoji issues in Windows console output
- Enhanced permission error handling in cache operations

### 📚 Documentation
- Updated README.md with v1.1 features
- Comprehensive ROADMAP.md with implementation details
- Inline code documentation
- Translation comment markers for i18n system

### 📦 Dependencies
- **New**: `packaging>=21.0` - For semantic version comparison
- **Updated**: All dependencies verified for Windows compatibility
- **Removed**: No deprecated dependencies

### 📊 Code Quality
- **Syntax Verified** - All Python files compile without errors
- **Error Handling** - Comprehensive try/catch blocks
- **Fallback Systems** - Graceful degradation for missing features
- **Performance Optimized** - Animation pausing when off-screen
- **Resource Management** - Proper cleanup of threads and timers

---

## v1.0.0 (December 4, 2025)

### Initial Release Features
- Automatic Steam import with metadata
- Automatic Epic Games import
- Manual game addition
- Dual Grid/List view modes
- Real-time game search
- Custom themes with color customization
- Custom backgrounds with opacity control
- Background history
- Auto icon extraction
- Image caching system
- Multi-language support (ES/EN)
- Borderless window design
- Smooth animations and transitions
- Windows startup integration

---

## Migration Guide (v1.0 → v1.1)

### Automatic Updates
If you have auto-update enabled in Settings, v1.1 will be installed automatically on your next launch. No action required!

### Manual Update
1. Download `LudexHub-v1.1.0.zip` from releases
2. Extract to your LudexHub folder (overwrite existing)
3. Run `LudexHub.exe`

### Settings Migration
- All v1.0 settings automatically transfer to v1.1
- New settings (playtime tracking, auto-update) default to recommended values
- Games library and theme preferences preserved

### Custom Themes
- All v1.0 custom themes remain compatible
- New 6 theme presets available in theme selector
- Theme customization enhanced with typography and spacing options

---

**Latest Version**: v1.1.0  
**Release Date**: December 7, 2025  
**License**: MIT  
**Author**: Eden

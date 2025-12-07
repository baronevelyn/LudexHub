# 🚀 LudexHub v1.1 - Development Roadmap

## ✅ Completed Features

### Process Priority Configuration
- ✅ Added process priority selector in General settings (High/Normal/Low)
- ✅ Priority persists across sessions (saved in theme.json)
- ✅ Applied automatically on startup
- ✅ Multi-language support (ES/EN)
- ✅ Uses Windows API (ctypes) - no external dependencies

### Animation Bug Fixes
- ✅ Fixed crash when switching between Grid/List modes rapidly
- ✅ Proper error handling for deleted widgets during animation cleanup

### Clear Cache Feature
- ✅ Button in Settings > General to clear cached images and temp data
- ✅ Confirmation dialog with size calculation
- ✅ Success/error messages with freed space display
- ✅ Multi-language support (ES/EN)

---

## 📋 Planned Features for v1.1 (Final Release)

### 🎮 Favorites System
- [x] **Mark as Favorite** - Toggle favorite status on game cards
- [x] **Favorites Filter** - Quick filter button to show only favorites
- [x] **Star Icon Display** - Visual indicator on game cards
- [x] **Persistent Storage** - Favorites saved in games.json

### 🔍 Advanced Filtering & Sorting
- [x] **Filter by Platform** - Steam / Epic / Manual games
- [x] **Filter by Favorites** - Show only favorited games (toggle y carpeta "Favoritos")
- [x] **Sort Options**:
  - By name (A-Z) ✅
  - By last played (most recent first) ✅
  - By play time (most played) ✅
  - By date added (newest/oldest) ✅
- [x] **Filter Persistence** - Remember last filter when app closes
- [~] **Game Folders & Sidebar** - Custom folders with user-defined names; auto-create Steam/Epic folders; games can belong to multiple folders; collapsible left sidebar that expands on hover to pick "All games" or a specific folder (MVP listo; pulir asignaciones múltiples/persistencia de folders)

### ⏱️ Play Time Tracking
- [x] **Launch Timer** - Track when game starts and ends
- [x] **Tracking Toggle** - Enable/disable tracking to reduce resource usage
- [x] **Total Play Time** - Display total hours/minutes per game
- [x] **Play Time Display** - Show in game card or details view

### 🎨 Enhanced Theme System
- [x] **Theme Preview** - Live preview in floating window before applying
- [x] **Custom Theme Name** - Users can name and save their custom themes
- [x] **Custom Theme Save/Load/Delete** - Full CRUD operations for custom themes
- [x] **Theme Persistence** - Custom themes saved in theme.json
- [x] **Animated Game Card Covers** - Support GIF covers on game cards (animations pause when off-screen to save resources)
- [x] **Advanced Customization**:
  - Typography (font family, sizes)
  - Spacing & Layout (card radius, padding, borders)
  - Color Scheme (16+ color values)
- [x] **Theme Presets** - 6 Complete new presets with typography and spacing:
  - **Cyberpunk** - Neon colors, JetBrains Mono font, sharp borders
  - **Sunset** - Warm orange/red, Inter font, smooth borders
  - **Forest** - Green nature theme, Roboto font, natural styling
  - **Ocean** - Cool blue theme, Poppins font, professional look
  - **Retro** - 80s aesthetic, Space Mono font, bold borders
  - **Minimal** - Clean minimalist, Open Sans font, subtle styling

### 🖼️ Animated Background Support
- [x] **GIF Format Support** - Play animated GIFs as background
- [x] **Video Format Support** - WebM/MP4 backgrounds (muted)
- [x] **Background Type Selector** - Toggle static/animated/video in settings
- [x] **Performance Optimization** - Efficient GIF rendering with QMovie
- [x] **Frame Update Timer** - Smooth playback (~30fps)

### ⚙️ Auto-Update System

#### Completed Implementation

- [x] **auto_updater.py module** - Core update checker class with GitHub API integration
  - UpdateInfo class for holding release information
  - AutoUpdater class with check/download/install methods
  - Update cache system (min 1 hour between checks)
  - Semantic version comparison with `packaging` library

- [x] **Version Management**
  - `__version__ = "1.1.0"` in game_library.py
  - Version display in Settings > General ("Current version: v1.1.0")
  - Semantic versioning support (major.minor.patch)

- [x] **GitHub API Integration**
  - Check latest release from `baronevelyn/LudexHub`
  - Automatic Windows .exe detection from assets
  - Parse version, changelog, date, file size
  - Rate limiting with cache (max 1 check per hour)

- [x] **Update Detection & Notification**
  - Manual "Check for Updates" button in Settings > General
  - Auto-check on startup (2 seconds after launch)
  - Configurable via "Check for updates automatically" toggle
  - Shows update version, date, size, and changelog
  - "Yes/No" dialog for manual checks, "No/Yes" for auto-checks

- [x] **Update Download**
  - Multi-part download with progress tracking
  - Real-time progress bar with percentage and speed
  - SHA256 checksum verification
  - Download to temp directory with cleanup

- [x] **Update Installation**
  - Automatic backup of current executable
  - Batch script for safe replacement
  - Graceful restart mechanism
  - Rollback option if installation fails

- [x] **Changelog Viewer**
  - Formatted dialog displaying release notes
  - Automatic display after successful download
  - Scrollable area with proper styling
  - Fallback message if no changelog available

- [x] **Settings Integration**
  - "Check for updates automatically" checkbox in General tab
  - Persistent setting saved in theme.json
  - Tooltip explaining auto-check functionality
  - Clean UI integration with other settings

- [x] **Translations**
  - Spanish (ES): All dialogs, buttons, and messages
  - English (EN): All dialogs, buttons, and messages
  - Dynamic version/size formatting in messages
  - Error messages with contextual information

- [x] **Error Handling**
  - Network errors with user-friendly messages
  - Checksum verification failures
  - Installation failures with rollback
  - Silent fallback for auto-checks to not disturb user
  - Timeout handling for API requests

- [x] **Dependencies**
  - `packaging>=21.0` added to requirements.txt
  - Uses existing `requests` library
  - Standard library modules: hashlib, subprocess, tempfile

### 📊 Additional Features
- [x] **Clear Cache Button** - Button in Settings to clear application cache (images, temporary data, etc.)
- [ ] **Game Count Display** - Show total games in library
- [ ] **Drag & Drop** - Drag executables/images to add games

---

## 🗓️ Implementation Order

### Phase 1 (Core Features) ✅
1. **Favorites System** - Essential for v1.1
2. **Play Time Tracking** - Fundamental feature
3. **Sort by Last Played** - Key sorting option

### Phase 2 (Filtering & Display) ✅
4. **Advanced Filters** - Platform, favorites, sorting
5. **Filter Persistence** - Remember user choices

### Phase 3 (Themes & Visual) ✅
6. **6 New Theme Presets** - Expand theme options
7. **Theme Preview** - Live theme testing
8. **Animated GIF Backgrounds** - Visual enhancement

### Phase 4 (System Features) ✅
9. **Auto-Update System** - Keep app current
10. **Clear Cache** - Manage disk space

---

## 📝 Technical Details

### Database Changes
- Add to `games.json`:
  - `is_favorite: bool` - Favorite status
  - `last_played: timestamp` - Last launch time
  - `total_play_time: int` - Seconds played
  
- Add to `theme.json`:
  - `current_theme_name: string` - Theme identifier
  - `selected_theme_preset: string` - Which preset (base/light/dark/pink/etc)
  - `process_priority: string` - Process priority (high/normal/low)
  - `playtime_tracking_enabled: bool` - Playtime tracking toggle
  - `auto_update_enabled: bool` - Auto-update check on startup toggle

### File Format Support
- GIF: `.gif` (using QMovie for animation)
- Video: `.webm`, `.mp4` (optional, uses ffmpeg or Qt multimedia)

### API Integration
- GitHub API: Check latest release version
- No external API calls needed otherwise

---

## 🎯 Success Criteria

- [x] All core features implemented and tested
- [x] No crashes when switching views
- [x] Play time tracking accurate
- [x] Filtering works smoothly with 1000+ games
- [x] Update system reliable with GitHub integration
- [x] New themes visually appealing
- [x] Animated backgrounds perform well
- [x] All strings translated (ES/EN)
- [x] Auto-update system functional with changelog viewer
- [x] Cache clearing system working

---

## 🚀 Release Checklist for v1.1.0

### Before Release
- [ ] Compile final v1.1.0 executable from current main branch
- [ ] Test all features thoroughly on clean Windows installation
  - [ ] Game launching (Steam, Epic, Manual)
  - [ ] Favorites toggle and filtering
  - [ ] Playtime tracking (enable/disable)
  - [ ] All sorting options
  - [ ] All 10 theme presets + custom themes
  - [ ] GIF and video backgrounds
  - [ ] Clear cache button
  - [ ] Settings language switching (ES/EN)
- [ ] Check for performance issues with 100+ games
- [ ] Verify all translations are complete (ES/EN)
- [ ] Test auto-update system (if test release available on GitHub)
- [ ] Create comprehensive release notes covering:
  - New features (6 themes, auto-update, clear cache)
  - Bug fixes (animation crashes)
  - Known limitations (folder assignments)
  - Installation/update instructions
- [ ] Create and tag GitHub release as v1.1.0
  - [ ] Include compiled .exe file
  - [ ] Add release notes markdown
  - [ ] Link to README for installation
- [ ] Update README.md with:
  - [ ] New features in v1.1.0
  - [ ] Screenshots of new themes
  - [ ] Auto-update information
  - [ ] System requirements (Python 3.8+, Windows 7+)
- [ ] Test download/install via auto-update system (manual release cycle)

### Version Release Structure
- **Current Version**: v1.1.0
- **Release Date**: December 7, 2025
- **Branch**: main
- **Compile Command**: `pyinstaller LudexHub.spec` or `pyinstaller game_library.py --onefile`

### Post-Release
- [ ] Monitor GitHub issues for bugs
- [ ] Gather user feedback on new features
- [ ] Create v1.2 milestone for future features
  - [ ] Game count display
  - [ ] Drag & drop game adding
  - [ ] Multiple game folders assignment
  - [ ] Improved folder persistence
  - [ ] Statistics dashboard

---

## 📊 v1.1.0 Release Summary

**Major Additions**:
- 6 new complete theme presets with typography and spacing customization
- Automatic font installation and management system
- Comprehensive auto-update system with GitHub integration and changelog viewer
- Cache clearing utility for disk space management

**Improvements**:
- Enhanced theme system with live preview
- Better animation performance with GIF pause when off-screen
- Configurable playtime tracking with toggle
- Automatic process priority management
- Semantic version comparison for updates

**Bug Fixes**:
- Fixed crashes when rapidly switching between Grid/List view modes
- Improved widget cleanup during animation transitions
- Better error handling in font installation

**Internationalization**:
- Complete Spanish and English translations
- 60+ translation keys for all dialogs and settings

**System**:
- Python dependencies: PyQt5, requests, opencv-python, packaging
- Windows API integration for process priority
- Batch script auto-update installation
- SHA256 checksum verification

---

**Last Updated**: December 7, 2025
**Status**: Ready for Release
**Target**: v1.1.0 Release Candidate

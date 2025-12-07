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
- [ ] **Update Checker** - Check GitHub releases on startup
- [ ] **Update Notification** - Notify user of available updates
- [ ] **One-Click Update** - Download and install updates
- [ ] **Version Display** - Show current version in About dialog
- [ ] **Changelog Viewer** - Show what's new in each version

### 📊 Additional Features
- [ ] **Game Count Display** - Show total games in library
- [ ] **Quick Stats** - Games by platform in header
- [ ] **Drag & Drop** - Drag executables/images to add games

---

## 🗓️ Implementation Order

### Phase 1 (Core Features)
1. **Favorites System** - Essential for v1.1
2. **Play Time Tracking** - Fundamental feature
3. **Sort by Last Played** - Key sorting option

### Phase 2 (Filtering & Display)
4. **Advanced Filters** - Platform, favorites, sorting
5. **Filter Persistence** - Remember user choices

### Phase 3 (Themes & Visual)
6. **6 New Theme Presets** - Expand theme options
7. **Theme Preview** - Live theme testing
8. **Animated GIF Backgrounds** - Visual enhancement

### Phase 4 (System Features)
9. **Auto-Update System** - Keep app current
10. **Statistics Dashboard** - Show library insights

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

### File Format Support
- GIF: `.gif` (using QMovie for animation)
- Video: `.webm`, `.mp4` (optional, uses ffmpeg or Qt multimedia)

### API Integration
- GitHub API: Check latest release version
- No external API calls needed otherwise

---

## 🎯 Success Criteria

- [ ] All core features implemented and tested
- [ ] No crashes when switching views
- [ ] Play time tracking accurate
- [ ] Filtering works smoothly with 1000+ games
- [ ] Update system reliable
- [ ] New themes visually appealing
- [ ] Animated backgrounds perform well
- [ ] All strings translated (ES/EN)

---

## 🚀 Release Checklist

### Before Release
- [ ] Compile final v1.1 executable
- [ ] Test all features thoroughly
- [ ] Check for performance issues
- [ ] Verify translations
- [ ] Write comprehensive release notes
- [ ] Create GitHub release with v1.1.0 tag
- [ ] Update README with new features

### Post-Release
- [ ] Monitor for bugs
- [ ] Gather user feedback
- [ ] Plan v1.2 features

---

**Last Updated**: December 6, 2025
**Status**: Planning phase
**Target Release**: End of Q4 2025

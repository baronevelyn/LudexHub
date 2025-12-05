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
- [ ] **Mark as Favorite** - Toggle favorite status on game cards
- [ ] **Favorites Filter** - Quick filter button to show only favorites
- [ ] **Star Icon Display** - Visual indicator on game cards
- [ ] **Persistent Storage** - Favorites saved in games.json

### 🔍 Advanced Filtering & Sorting
- [ ] **Filter by Platform** - Steam / Epic / Manual games
- [ ] **Filter by Favorites** - Show only favorited games
- [ ] **Sort Options**:
  - By name (A-Z)
  - By date added (newest/oldest)
  - By last played (most recent first)
  - By play time (most played)
- [ ] **Filter Persistence** - Remember last filter when app closes

### ⏱️ Play Time Tracking
- [ ] **Launch Timer** - Track when game starts and ends
- [ ] **Total Play Time** - Display total hours/minutes per game
- [ ] **Last Played** - Show timestamp of last game launch
- [ ] **Play Time Display** - Show in game card or details view
- [ ] **Statistics** - Aggregate stats in dashboard

### 🎨 Enhanced Theme System
- [ ] **New Theme Presets** (6+ additional themes):
  - **Cyberpunk** - Neon colors with dark background
  - **Sunset** - Orange/red gradient theme
  - **Forest** - Green nature-inspired theme
  - **Ocean** - Blue water theme
  - **Retro** - Vintage/80s aesthetic
  - **Minimal** - Clean, minimalist design
- [ ] **Theme Preview** - Live preview before applying
- [ ] **Custom Theme Name** - Users can name their custom themes

### 🖼️ Animated Background Support
- [ ] **GIF Format Support** - Play animated GIFs as background
- [ ] **Video Format Support** - WebM/MP4 backgrounds (optional)
- [ ] **Background Animation Speed** - Control playback speed
- [ ] **Performance Optimization** - Efficient GIF rendering
- [ ] **Fallback to First Frame** - If animation fails to play

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

**Last Updated**: December 5, 2025
**Status**: Planning phase
**Target Release**: End of Q4 2025

# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-12-04
- Initial public release of the PyQt5 desktop game library.
- Features:
  - Steam import: scan libraries, dedupe by AppID, launch via `steam://`, fetch covers from CDN/cache, EXE icon extraction.
  - Epic import: scan manifests, launch via protocol, robust image pipeline (catalog, offers, products, local caches, install dir), Steam-inferred fallback for covers/icons.
  - Unified import button with platform icons.
  - Grid/List views with polished GameCards and badges.
  - Frameless window with minimize/restore animations.
  - Comprehensive customization dialog with presets; theme persist.
- Tests: Added coverage for Epic images and scanners; suite passes (13 tests).
- Build: PyInstaller spec and batch script to produce a one-file EXE.

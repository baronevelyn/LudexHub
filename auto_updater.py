"""
Auto-Update System for LudexHub
Checks GitHub releases, downloads updates, and handles installation
"""

import requests
import hashlib
import json
import tempfile
import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from packaging import version


# GitHub repository info
REPO_OWNER = "baronevelyn"
REPO_NAME = "LudexHub"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

# Update check cache settings
UPDATE_CHECK_CACHE_FILE = Path(__file__).parent / "update_cache.json"
MIN_CHECK_INTERVAL = timedelta(hours=1)  # Minimum time between checks


class UpdateInfo:
    """Information about an available update"""
    def __init__(self, version: str, download_url: str, changelog: str, 
                 asset_size: int, published_at: str):
        self.version = version
        self.download_url = download_url
        self.changelog = changelog
        self.asset_size = asset_size
        self.published_at = published_at
    
    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'download_url': self.download_url,
            'changelog': self.changelog,
            'asset_size': self.asset_size,
            'published_at': self.published_at
        }


class AutoUpdater:
    """Handles automatic updates from GitHub releases"""
    
    def __init__(self, current_version: str):
        """
        Initialize the auto-updater
        
        Args:
            current_version: Current application version (e.g. "1.1.0")
        """
        self.current_version = current_version.lstrip('v')  # Remove 'v' prefix if present
        self.temp_dir = Path(tempfile.gettempdir()) / "ludexhub_updates"
        self.temp_dir.mkdir(exist_ok=True)
    
    def should_check_for_updates(self) -> bool:
        """
        Check if enough time has passed since last update check
        
        Returns:
            True if should check, False if too recent
        """
        if not UPDATE_CHECK_CACHE_FILE.exists():
            return True
        
        try:
            with open(UPDATE_CHECK_CACHE_FILE, 'r') as f:
                cache = json.load(f)
                last_check = datetime.fromisoformat(cache.get('last_check', '2000-01-01'))
                return datetime.now() - last_check > MIN_CHECK_INTERVAL
        except:
            return True
    
    def update_check_cache(self):
        """Update the last check timestamp"""
        cache = {'last_check': datetime.now().isoformat()}
        with open(UPDATE_CHECK_CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    
    def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Check GitHub for latest release
        
        Returns:
            UpdateInfo if update available, None otherwise
        """
        try:
            # Query GitHub API
            response = requests.get(GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            
            # Compare versions
            if version.parse(latest_version) <= version.parse(self.current_version):
                return None
            
            # Find Windows executable asset
            windows_asset = None
            for asset in release_data.get('assets', []):
                asset_name = asset['name'].lower()
                if asset_name.endswith('.exe') and 'windows' in asset_name:
                    windows_asset = asset
                    break
            
            if not windows_asset:
                print(f"[WARN] No Windows executable found in release {latest_version}")
                return None
            
            # Update cache
            self.update_check_cache()
            
            # Return update info
            return UpdateInfo(
                version=latest_version,
                download_url=windows_asset['browser_download_url'],
                changelog=release_data.get('body', 'No changelog available'),
                asset_size=windows_asset['size'],
                published_at=release_data['published_at']
            )
        
        except requests.RequestException as e:
            print(f"[ERROR] Failed to check for updates: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error checking updates: {e}")
            return None
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two semantic versions
        
        Args:
            v1: First version string
            v2: Second version string
        
        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        v1_parsed = version.parse(v1.lstrip('v'))
        v2_parsed = version.parse(v2.lstrip('v'))
        
        if v1_parsed < v2_parsed:
            return -1
        elif v1_parsed > v2_parsed:
            return 1
        else:
            return 0
    
    def download_update(self, update_info: UpdateInfo, 
                       progress_callback=None) -> Optional[Path]:
        """
        Download update file with progress tracking
        
        Args:
            update_info: Update information
            progress_callback: Optional callback(bytes_downloaded, total_bytes)
        
        Returns:
            Path to downloaded file, or None on failure
        """
        try:
            download_path = self.temp_dir / f"LudexHub-v{update_info.version}.exe"
            
            # Download with progress
            response = requests.get(update_info.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            
            return download_path
        
        except Exception as e:
            print(f"[ERROR] Failed to download update: {e}")
            return None
    
    def verify_checksum(self, file_path: Path, expected_hash: Optional[str] = None) -> bool:
        """
        Verify SHA256 checksum of downloaded file
        
        Args:
            file_path: Path to file to verify
            expected_hash: Expected SHA256 hash (if None, just compute and return True)
        
        Returns:
            True if valid, False otherwise
        """
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            computed_hash = sha256_hash.hexdigest()
            
            if expected_hash:
                return computed_hash.lower() == expected_hash.lower()
            
            # If no expected hash, just return True (file is readable)
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to verify checksum: {e}")
            return False
    
    def install_update(self, update_file: Path) -> bool:
        """
        Install the update by creating a batch script
        
        Args:
            update_file: Path to the new executable
        
        Returns:
            True if installation initiated, False otherwise
        """
        try:
            current_exe = Path(__file__).parent / "LudexHub.exe"
            backup_exe = Path(__file__).parent / "LudexHub.exe.backup"
            
            # Create backup
            if current_exe.exists():
                import shutil
                shutil.copy2(current_exe, backup_exe)
            
            # Create batch script for update
            batch_script = self.temp_dir / "update.bat"
            batch_content = f"""@echo off
echo Updating LudexHub...
timeout /t 2 /nobreak > nul

REM Kill any running instances
taskkill /F /IM LudexHub.exe > nul 2>&1

REM Replace executable
move /Y "{update_file}" "{current_exe}"

REM Start new version
start "" "{current_exe}"

REM Clean up
timeout /t 2 /nobreak > nul
del "{backup_exe}" > nul 2>&1
del "%~f0"
"""
            
            with open(batch_script, 'w') as f:
                f.write(batch_content)
            
            # Execute batch script
            subprocess.Popen(['cmd', '/c', str(batch_script)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to install update: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Remove temporary update files"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass


def get_latest_version_info(current_version: str) -> Optional[UpdateInfo]:
    """
    Convenience function to check for updates
    
    Args:
        current_version: Current application version
    
    Returns:
        UpdateInfo if update available, None otherwise
    """
    updater = AutoUpdater(current_version)
    
    if not updater.should_check_for_updates():
        return None
    
    return updater.check_for_updates()

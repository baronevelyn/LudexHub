"""Módulo para instalar fuentes del sistema automáticamente"""

import os
import sys
import shutil
import zipfile
import tempfile
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

# URLs para descargar fuentes (solo las que funcionan)
FONTS_TO_INSTALL = {
    'JetBrains Mono': 'https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip',
    'Inter': 'https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip',
}

# Fuentes fallback si no se pueden descargar
FONT_FALLBACKS = {
    'JetBrains Mono': 'Courier New',
    'Inter': 'Arial',
    'Roboto': 'Segoe UI',
    'Poppins': 'Tahoma',
    'Space Mono': 'Courier New',
    'Open Sans': 'Arial',
}

def get_fonts_directory():
    """Obtener el directorio de fuentes de la aplicación"""
    fonts_dir = Path(__file__).parent / 'fonts'
    fonts_dir.mkdir(exist_ok=True)
    return fonts_dir

def font_available(font_name):
    """Verificar si una fuente está disponible (descargada o en sistema)"""
    fonts_dir = get_fonts_directory()
    
    # Buscar en directorio local
    for font_file in list(fonts_dir.glob('*.ttf')) + list(fonts_dir.glob('*.otf')):
        if font_name.lower() in font_file.name.lower():
            return True
    
    # Buscar en sistema
    try:
        from PyQt5.QtGui import QFontDatabase
        db = QFontDatabase()
        available = db.families()
        return font_name in available
    except:
        pass
    
    return False

def download_and_install_font(font_name, url):
    """Descargar e instalar una fuente"""
    if not requests:
        return False
    
    try:
        print(f"[DL] Descargando {font_name}...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        fonts_dir = get_fonts_directory()
        tmp_path = None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        try:
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                with tempfile.TemporaryDirectory() as extract_dir:
                    zip_ref.extractall(extract_dir)
                    extract_path = Path(extract_dir)
                    fonts = list(extract_path.rglob('*.ttf'))[:2] + list(extract_path.rglob('*.otf'))[:2]
                    
                    for font_file in fonts:
                        dest = fonts_dir / font_file.name
                        shutil.copy(font_file, dest)
                    
                    if fonts:
                        print(f"[OK] {len(fonts)} archivo(s) descargado(s): {font_name}")
                        return True
        except:
            pass
        
        return False
    
    except Exception as e:
        print(f"[SKIP] {font_name}: {str(e)[:40]}")
        return False
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass

def load_application_fonts():
    """Cargar fuentes locales en QFontDatabase"""
    try:
        from PyQt5.QtGui import QFontDatabase
        fonts_dir = get_fonts_directory()
        count = 0
        
        for font_file in sorted(fonts_dir.glob('*.ttf')) + sorted(fonts_dir.glob('*.otf')):
            if QFontDatabase.addApplicationFont(str(font_file)) >= 0:
                count += 1
        
        if count > 0:
            print(f"[OK] {count} fuente(s) cargada(s) localmente")
        return count
    except:
        return 0

def ensure_fonts_installed():
    """Asegurar disponibilidad de fuentes"""
    print("\n[INFO] Iniciando sistema de fuentes...")
    
    # Verificar fuentes
    missing = []
    for font_name in list(FONTS_TO_INSTALL.keys()) + list(FONT_FALLBACKS.keys()):
        if not font_available(font_name):
            missing.append(font_name)
            fallback = FONT_FALLBACKS.get(font_name, 'Arial')
            print(f"[INFO] {font_name} usa fallback: {fallback}")
        else:
            print(f"[OK] {font_name} disponible")
    
    # Descargar solo las que faltan Y tenemos URL
    if missing and requests:
        for font_name, url in FONTS_TO_INSTALL.items():
            if font_name in missing:
                download_and_install_font(font_name, url)
    
    # Cargar fuentes locales
    print("\n[INFO] Cargando fuentes locales...")
    load_application_fonts()
    print()

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    ensure_fonts_installed()

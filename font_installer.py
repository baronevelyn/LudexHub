"""Módulo para instalar fuentes del sistema automáticamente en Windows"""

import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

# Diccionario de fuentes con URLs de descarga (Google Fonts)
FONTS_TO_INSTALL = {
    'JetBrains Mono': 'https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip',
    'Inter': 'https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip',
    'Roboto': 'https://fonts.google.com/download?family=Roboto',
    'Poppins': 'https://fonts.google.com/download?family=Poppins',
    'Space Mono': 'https://fonts.google.com/download?family=Space%20Mono',
    'Open Sans': 'https://fonts.google.com/download?family=Open%20Sans',
}

# URLs alternativas desde Google Fonts API
GOOGLE_FONTS_URLS = {
    'JetBrains Mono': 'https://fonts.google.com/download?family=JetBrains%20Mono',
    'Inter': 'https://fonts.google.com/download?family=Inter',
    'Roboto': 'https://fonts.google.com/download?family=Roboto',
    'Poppins': 'https://fonts.google.com/download?family=Poppins',
    'Space Mono': 'https://fonts.google.com/download?family=Space%20Mono',
    'Open Sans': 'https://fonts.google.com/download?family=Open%20Sans',
}

def get_fonts_directory():
    """Obtener el directorio de fuentes del sistema Windows"""
    if sys.platform == 'win32':
        return Path(os.environ['WINDIR']) / 'Fonts'
    elif sys.platform == 'darwin':  # macOS
        return Path.home() / 'Library' / 'Fonts'
    else:  # Linux
        return Path.home() / '.local' / 'share' / 'fonts'

def font_already_installed(font_name):
    """Verificar si una fuente ya está instalada en el sistema"""
    from PyQt5.QtGui import QFontDatabase
    available_fonts = QFontDatabase.families()
    return font_name in available_fonts

def install_font_windows(font_path):
    """Instalar una fuente en Windows usando registro y ctypes"""
    try:
        import ctypes
        import winreg
        
        # Copiar la fuente a la carpeta de Fonts
        fonts_dir = get_fonts_directory()
        font_name = os.path.basename(font_path)
        dest_path = fonts_dir / font_name
        
        if not dest_path.exists():
            shutil.copy(font_path, dest_path)
            print(f"✓ Fuente instalada: {font_name}")
        
        # Registrar en el registro de Windows
        font_reg_name = font_name.replace('.ttf', '').replace('.otf', '')
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts',
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, font_reg_name, 0, winreg.REG_SZ, str(dest_path))
            winreg.CloseKey(key)
        except PermissionError:
            # Si no tenemos permisos de admin, intentar con HKEY_CURRENT_USER
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts',
                    0,
                    winreg.KEY_SET_VALUE
                )
                winreg.SetValueEx(key, font_reg_name, 0, winreg.REG_SZ, str(dest_path))
                winreg.CloseKey(key)
            except Exception as e:
                print(f"⚠ Advertencia: No se pudo registrar {font_name} en el registro: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Error instalando fuente {font_path}: {e}")
        return False

def download_and_install_font(font_name, url):
    """Descargar e instalar una fuente desde una URL"""
    if not requests:
        print(f"⚠ 'requests' no instalado. Saltando descarga de {font_name}")
        return False
    
    try:
        print(f"📥 Descargando {font_name}...")
        
        # Descargar
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Guardar en temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        # Extraer y buscar archivos TTF/OTF
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Buscar fuentes
            extract_path = Path(extract_dir)
            font_files = list(extract_path.rglob('*.ttf')) + list(extract_path.rglob('*.otf'))
            
            if font_files:
                # Instalar todas las fuentes encontradas
                for font_file in font_files:
                    if sys.platform == 'win32':
                        install_font_windows(str(font_file))
                    else:
                        shutil.copy(font_file, get_fonts_directory() / font_file.name)
                        print(f"✓ Fuente instalada: {font_file.name}")
                return True
            else:
                print(f"✗ No se encontraron archivos de fuente en {font_name}")
                return False
        
    except Exception as e:
        print(f"✗ Error descargando {font_name}: {e}")
        return False
    finally:
        # Limpiar archivo temporal
        try:
            os.remove(tmp_path)
        except:
            pass

def ensure_fonts_installed():
    """Asegurar que todas las fuentes requeridas estén instaladas"""
    print("\n🔍 Verificando fuentes del sistema...")
    
    fonts_to_download = {}
    
    for font_name in FONTS_TO_INSTALL.keys():
        if not font_already_installed(font_name):
            print(f"⚠ Fuente no encontrada: {font_name}")
            fonts_to_download[font_name] = GOOGLE_FONTS_URLS.get(
                font_name, 
                FONTS_TO_INSTALL[font_name]
            )
        else:
            print(f"✓ Fuente ya instalada: {font_name}")
    
    # Si faltan fuentes y tenemos requests, intentar descargarlas
    if fonts_to_download:
        if requests:
            print(f"\n📦 Instalando {len(fonts_to_download)} fuente(s) faltante(s)...")
            for font_name, url in fonts_to_download.items():
                download_and_install_font(font_name, url)
            print("✓ Instalación de fuentes completada\n")
        else:
            print("\n⚠ Las siguientes fuentes no están instaladas:")
            for font_name in fonts_to_download.keys():
                print(f"  - {font_name}")
            print("\nInstalación manual recomendada o ejecutar: pip install requests")
    else:
        print("✓ Todas las fuentes requeridas están instaladas\n")

if __name__ == '__main__':
    ensure_fonts_installed()

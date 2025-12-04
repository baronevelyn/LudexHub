"""
Módulo para detectar y escanear juegos instalados de Steam
"""
import os
import re
import winreg
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class SteamScanner:
    """Escanea la instalación de Steam y detecta juegos instalados"""
    
    def __init__(self):
        self.steam_path = self.find_steam_installation()
        self.library_folders = []
        if self.steam_path:
            self.library_folders = self.parse_library_folders()
    
    def find_steam_installation(self) -> Optional[str]:
        """
        Encuentra la ruta de instalación de Steam desde el registro de Windows
        
        Returns:
            Ruta a la carpeta de Steam o None si no se encuentra
        """
        # Intentar en HKEY_CURRENT_USER primero (más común)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
            winreg.CloseKey(key)
            if os.path.exists(steam_path):
                return steam_path
        except (WindowsError, FileNotFoundError):
            pass
        
        # Intentar en HKEY_LOCAL_MACHINE (instalación para todos los usuarios)
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            if os.path.exists(steam_path):
                return steam_path
        except (WindowsError, FileNotFoundError):
            pass
        
        return None
    
    def parse_vdf(self, content: str) -> Dict:
        """
        Parser simple para archivos VDF de Steam
        
        Args:
            content: Contenido del archivo VDF como string
            
        Returns:
            Diccionario con la estructura parseada
        """
        result = {}
        stack = [result]
        current_key = None
        
        # Eliminar comentarios
        lines = []
        for line in content.split('\n'):
            # Remover comentarios //
            if '//' in line:
                line = line[:line.index('//')]
            lines.append(line.strip())
        
        for line in lines:
            if not line:
                continue
            
            # Inicio de bloque
            if line == '{':
                if current_key:
                    new_dict = {}
                    stack[-1][current_key] = new_dict
                    stack.append(new_dict)
                    current_key = None
                continue
            
            # Fin de bloque
            if line == '}':
                if len(stack) > 1:
                    stack.pop()
                continue
            
            # Par clave-valor
            # Formato: "clave" "valor" o "clave"
            matches = re.findall(r'"([^"]*)"', line)
            if len(matches) >= 2:
                key, value = matches[0], matches[1]
                stack[-1][key] = value
                current_key = None
            elif len(matches) == 1:
                current_key = matches[0]
        
        return result
    
    def parse_library_folders(self) -> List[str]:
        """
        Parsea el archivo libraryfolders.vdf para encontrar todas las bibliotecas de Steam
        
        Returns:
            Lista de rutas a carpetas de bibliotecas
        """
        if not self.steam_path:
            return []
        
        library_file = Path(self.steam_path) / "steamapps" / "libraryfolders.vdf"
        if not library_file.exists():
            # Fallback: solo la carpeta principal de Steam
            return [self.steam_path]
        
        try:
            with open(library_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            data = self.parse_vdf(content)
            folders_raw = [self.steam_path]  # Siempre incluir la carpeta principal

            # El formato es: libraryfolders -> "0" -> "path", "1" -> "path", etc.
            if 'libraryfolders' in data:
                lib_data = data['libraryfolders']
                for key, value in lib_data.items():
                    if key.isdigit() and isinstance(value, dict):
                        path = value.get('path', '')
                        if path and os.path.exists(path):
                            folders_raw.append(path)

            # Normalizar rutas y deduplicar de forma insensible a mayúsculas/minúsculas
            normed = []
            seen = set()
            for p in folders_raw:
                np = os.path.normcase(os.path.normpath(p))
                if np not in seen:
                    seen.add(np)
                    normed.append(p)

            return normed
            
        except Exception as e:
            print(f"Error parsing libraryfolders.vdf: {e}")
            return [self.steam_path]
    
    def parse_appmanifest(self, manifest_path: Path) -> Optional[Dict]:
        """
        Parsea un archivo appmanifest_<appid>.acf para extraer información del juego
        
        Args:
            manifest_path: Ruta al archivo appmanifest
            
        Returns:
            Diccionario con información del juego o None si hay error
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            data = self.parse_vdf(content)
            
            # La estructura es: AppState -> {appid, name, installdir, StateFlags, ...}
            if 'AppState' in data:
                app_data = data['AppState']
                
                # StateFlags: "4" significa completamente instalado
                state = app_data.get('StateFlags', '0')
                if state != '4':
                    return None
                
                return {
                    'appid': app_data.get('appid', ''),
                    'name': app_data.get('name', ''),
                    'installdir': app_data.get('installdir', ''),
                    'icon': app_data.get('icon', ''),  # Hash del icono
                    'library_folder': str(manifest_path.parent.parent)  # Carpeta de biblioteca
                }
            
            return None
            
        except Exception as e:
            print(f"Error parsing {manifest_path.name}: {e}")
            return None
    
    def scan_installed_games(self) -> List[Dict]:
        """
        Escanea todas las bibliotecas de Steam y encuentra juegos instalados
        
        Returns:
            Lista de diccionarios con información de cada juego
        """
        games_by_appid = {}

        for library_folder in self.library_folders:
            steamapps = Path(library_folder) / "steamapps"
            if not steamapps.exists():
                continue
            
            # Buscar todos los archivos appmanifest_*.acf
            for manifest_file in steamapps.glob("appmanifest_*.acf"):
                game_data = self.parse_appmanifest(manifest_file)
                if game_data:
                    appid = game_data.get('appid')
                    if appid and appid not in games_by_appid:
                        games_by_appid[appid] = game_data

        return list(games_by_appid.values())
    
    def get_game_executable_path(self, game_data: Dict) -> Optional[str]:
        """
        Intenta encontrar el ejecutable principal de un juego de Steam
        
        Args:
            game_data: Diccionario con información del juego (de scan_installed_games)
            
        Returns:
            Ruta al ejecutable principal o None
        """
        library_folder = game_data.get('library_folder')
        install_dir = game_data.get('installdir')
        
        if not library_folder or not install_dir:
            return None
        
        game_folder = Path(library_folder) / "steamapps" / "common" / install_dir
        if not game_folder.exists():
            return None
        
        # Buscar archivos .exe (excluir algunos comunes que no son el juego)
        exclude_names = ['unins', 'crash', 'report', 'launcher', 'setup', 'config', 'redist']
        
        for exe_file in game_folder.rglob("*.exe"):
            exe_name_lower = exe_file.name.lower()
            # Skip si contiene palabras excluidas
            if any(excl in exe_name_lower for excl in exclude_names):
                continue
            # Preferir .exe en la raíz
            if exe_file.parent == game_folder:
                return str(exe_file)
        
        # Si no hay en raíz, retornar el primero encontrado
        for exe_file in game_folder.rglob("*.exe"):
            exe_name_lower = exe_file.name.lower()
            if not any(excl in exe_name_lower for excl in exclude_names):
                return str(exe_file)
        
        return None
    
    def get_cached_image(self, appid: str, image_type: str = 'header') -> Optional[str]:
        """
        Busca imágenes en el caché local de Steam
        
        Args:
            appid: ID de la aplicación de Steam
            image_type: Tipo de imagen ('header', 'icon', 'logo', 'library_600x900', 'library_hero')
            
        Returns:
            Ruta a la imagen en caché o None
        """
        if not self.steam_path:
            return None
        
        cache_dir = Path(self.steam_path) / "appcache" / "librarycache"
        if not cache_dir.exists():
            return None
        
        # Patrones de búsqueda según tipo
        patterns = {
            'header': f"{appid}_header.jpg",
            'icon': f"{appid}_icon.jpg",
            'logo': f"{appid}_logo.png",
            'library_600x900': f"{appid}_library_600x900.jpg",
            'library_hero': f"{appid}_library_hero.jpg"
        }
        
        image_file = cache_dir / patterns.get(image_type, patterns['header'])
        
        if image_file.exists():
            return str(image_file)
        
        return None
    
    def get_cdn_image_url(self, appid: str, image_type: str = 'header') -> str:
        """
        Genera URL del CDN de Steam para descargar imágenes
        
        Args:
            appid: ID de la aplicación de Steam
            image_type: Tipo de imagen ('header', 'logo', 'library_600x900', 'library_hero')
            
        Returns:
            URL de la imagen en el CDN
        """
        base_url = "https://cdn.cloudflare.steamstatic.com/steam/apps"
        
        urls = {
            'header': f"{base_url}/{appid}/header.jpg",
            'logo': f"{base_url}/{appid}/logo.png",
            'icon': f"{base_url}/{appid}/logo.png",  # Fallback: usar logo como 'icon' si no hay caché local
            'library_600x900': f"{base_url}/{appid}/library_600x900.jpg",
            'library_hero': f"{base_url}/{appid}/library_hero.jpg"
        }

        return urls.get(image_type, urls['header'])
    
    def download_image(self, appid: str, image_type: str = 'header', save_dir: Optional[Path] = None) -> Optional[str]:
        """
        Descarga una imagen del CDN de Steam
        
        Args:
            appid: ID de la aplicación de Steam
            image_type: Tipo de imagen ('header', 'logo', 'library_600x900', 'library_hero')
            save_dir: Directorio donde guardar la imagen (si None, usa caché de la app)
            
        Returns:
            Ruta al archivo descargado o None si falla
        """
        # Primero intentar caché local de Steam
        cached = self.get_cached_image(appid, image_type)
        if cached:
            return cached
        
        # Si no está en caché, descargar del CDN
        url = self.get_cdn_image_url(appid, image_type)
        
        # Determinar directorio de destino
        if save_dir is None:
            save_dir = Path.home() / '.game_library' / 'steam_images'
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Determinar extensión
        ext = '.png' if image_type in ('logo', 'icon') else '.jpg'
        filename = f"{appid}_{image_type}{ext}"
        save_path = save_dir / filename
        
        # Si ya existe, retornarlo
        if save_path.exists():
            return str(save_path)
        
        # Descargar
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as f:
                        f.write(response.read())
                    return str(save_path)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"Error descargando imagen para appid {appid}: {e}")
            return None
        
        return None
    
    def get_game_metadata(self, game_data: Dict) -> Dict[str, Optional[str]]:
        """
        Obtiene metadatos (imágenes) para un juego de Steam
        
        Args:
            game_data: Diccionario con información del juego (de scan_installed_games)
            
        Returns:
            Diccionario con rutas a imágenes: {'header': path, 'icon': path, 'grid': path}
        """
        appid = game_data.get('appid', '')
        if not appid:
            return {'header': None, 'icon': None, 'grid': None}
        
        return {
            'header': self.download_image(appid, 'header'),
            'icon': self.download_image(appid, 'icon'),
            'grid': self.download_image(appid, 'library_600x900')
        }

"""
Módulo para detectar y escanear juegos instalados de Epic Games Store
"""
import os
import json
import winreg
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional
import urllib.parse


class EpicScanner:
    """Escanea la instalación de Epic Games Store y detecta juegos instalados"""
    
    def __init__(self):
        self.epic_path = self.find_epic_installation()
        self.manifest_folder = self.find_manifest_folder()
    
    def find_epic_installation(self) -> Optional[str]:
        """
        Encuentra la ruta de instalación de Epic Games Launcher desde el registro de Windows
        
        Returns:
            Ruta a la carpeta de Epic Games o None si no se encuentra
        """
        # Intentar en HKEY_LOCAL_MACHINE
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, 
                r"SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher"
            )
            install_path, _ = winreg.QueryValueEx(key, "AppDataPath")
            winreg.CloseKey(key)
            if os.path.exists(install_path):
                return install_path
        except (WindowsError, FileNotFoundError):
            pass
        
        # Intentar ubicación por defecto
        default_path = Path.home() / "AppData" / "Local" / "EpicGamesLauncher"
        if default_path.exists():
            return str(default_path)
        
        return None
    
    def find_manifest_folder(self) -> Optional[str]:
        """
        Encuentra la carpeta donde Epic almacena los manifiestos de juegos instalados
        
        Returns:
            Ruta a la carpeta de manifiestos o None
        """
        # Epic guarda manifiestos en ProgramData\Epic\EpicGamesLauncher\Data\Manifests
        manifest_path = Path("C:/ProgramData/Epic/EpicGamesLauncher/Data/Manifests")
        
        if manifest_path.exists():
            return str(manifest_path)
        
        return None
    
    def parse_manifest(self, manifest_path: Path) -> Optional[Dict]:
        """
        Parsea un archivo .item (manifiesto de Epic) para extraer información del juego
        
        Args:
            manifest_path: Ruta al archivo .item
            
        Returns:
            Diccionario con información del juego o None si hay error
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verificar que no sea DLC o contenido adicional
            # Los juegos tienen "AppName", DLCs generalmente tienen otras estructuras
            if not data.get('AppName'):
                return None
            
            # Verificar que esté instalado
            install_location = data.get('InstallLocation', '')
            if not install_location or not os.path.exists(install_location):
                return None
            
            display_name = data.get('DisplayName', data.get('AppName', 'Unknown'))
            app_name = data.get('AppName', '')
            launch_executable = data.get('LaunchExecutable', '')
            
            return {
                'app_name': app_name,
                'display_name': display_name,
                'install_location': install_location,
                'launch_executable': launch_executable,
                'catalog_namespace': data.get('CatalogNamespace', ''),
                'catalog_item_id': data.get('CatalogItemId', ''),
                'app_version': data.get('AppVersionString', '')
            }
            
        except Exception as e:
            print(f"Error parsing {manifest_path.name}: {e}")
            return None
    
    def scan_installed_games(self) -> List[Dict]:
        """
        Escanea los manifiestos de Epic y encuentra juegos instalados
        
        Returns:
            Lista de diccionarios con información de cada juego
        """
        if not self.manifest_folder:
            return []
        
        games = []
        manifest_dir = Path(self.manifest_folder)
        
        # Buscar todos los archivos .item
        for manifest_file in manifest_dir.glob("*.item"):
            game_data = self.parse_manifest(manifest_file)
            if game_data:
                games.append(game_data)
        
        return games
    
    def get_game_executable_path(self, game_data: Dict) -> Optional[str]:
        """
        Obtiene la ruta completa al ejecutable de un juego de Epic
        
        Args:
            game_data: Diccionario con información del juego (de scan_installed_games)
            
        Returns:
            Ruta al ejecutable principal o None
        """
        install_location = game_data.get('install_location')
        launch_executable = game_data.get('launch_executable')
        
        if not install_location or not launch_executable:
            return None
        
        exe_path = Path(install_location) / launch_executable
        
        if exe_path.exists():
            return str(exe_path)
        
        # Buscar en subdirectorios si no está en la raíz
        install_dir = Path(install_location)
        if install_dir.exists():
            for exe_file in install_dir.rglob(launch_executable):
                return str(exe_file)
        
        return None
    
    def get_launch_command(self, game_data: Dict) -> str:
        """
        Genera el comando de lanzamiento para un juego de Epic usando el protocolo com.epicgames.launcher://
        
        Args:
            game_data: Diccionario con información del juego
            
        Returns:
            String con el comando de lanzamiento
        """
        app_name = game_data.get('app_name', '')
        if app_name:
            return f"com.epicgames.launcher://apps/{app_name}?action=launch&silent=true"
        return ""
    
    def get_game_metadata(self, game_data: Dict) -> Dict[str, Optional[str]]:
        """
        Obtiene metadatos (imágenes) para un juego de Epic usando el catálogo público
        
        Args:
            game_data: Diccionario con información del juego
            
        Returns:
            Diccionario con rutas a imágenes encontradas
        """
        namespace = game_data.get('catalog_namespace')
        item_id = game_data.get('catalog_item_id')

        if not namespace or not item_id:
            return {'header': None, 'icon': None, 'grid': None}

        # Endpoint público del catálogo
        api_url = (
            f"https://catalog-public-service-prod06.ol.epicgames.com/catalog/api/shared/namespace/"
            f"{namespace}/bulk/items?ids={item_id}"
        )

        try:
            with urllib.request.urlopen(api_url, timeout=10) as resp:
                if resp.status != 200:
                    data = {}
                else:
                    data = json.loads(resp.read().decode('utf-8'))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            data = {}

        # La respuesta es un dict con el item_id como clave
        item = data.get(item_id) or {}
        key_images = item.get('keyImages') or []

        # Fallback: buscar por nombre en ofertas si no hay imágenes
        if not key_images:
            raw_title = game_data.get('display_name') or game_data.get('app_name') or ''
            title = raw_title.strip()
            # Generar variantes de búsqueda
            variants = [
                title,
                title.replace("'", "").replace(":", "").replace("-", " "),
                ' '.join(w for w in title.split() if len(w) > 2),
                (title.split(':')[0] if ':' in title else title),
                game_data.get('app_name', '')
            ]
            locales = ['en-US','es-ES']
            for query in variants:
                if not query:
                    continue
                for loc in locales:
                    q = urllib.parse.quote(query)
                    offers_url = (
                        "https://catalog-public-service-prod06.ol.epicgames.com/catalog/api/shared/offers"
                        f"?locale={loc}&searchKeywords={q}&country=US"
                    )
                    try:
                        with urllib.request.urlopen(offers_url, timeout=10) as resp:
                            if resp.status == 200:
                                offers_data = json.loads(resp.read().decode('utf-8'))
                                elements = offers_data.get('elements') or []
                                # Elegir el elemento cuyo title coincida mejor
                                chosen = None
                                for el in elements:
                                    t = (el.get('title') or '').lower().strip()
                                    if t == (title or '').lower().strip():
                                        chosen = el
                                        break
                                if not chosen and elements:
                                    chosen = elements[0]
                                if chosen:
                                    key_images = chosen.get('keyImages') or []
                                    if key_images:
                                        break
                    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
                        continue
                if key_images:
                    break

        # Preferencias de tipos de imagen (ampliadas)
        preferred_grid = [
            'DieselGameBox', 'DieselGameBoxWide', 'OfferImageWide',
            'OfferImageTall', 'Screenshot', 'Featured']
        preferred_header = ['DieselGameBoxWide', 'OfferImageWide', 'Featured']
        preferred_icon = ['Thumbnail', 'DieselSmallBox', 'Logo']

        def _find_image(types: List[str]) -> Optional[str]:
            for t in types:
                for ki in key_images:
                    if ki.get('type') == t and ki.get('url'):
                        return ki['url']
            return None

        grid_url = _find_image(preferred_grid)
        header_url = _find_image(preferred_header) or grid_url
        icon_url = _find_image(preferred_icon)

        # Si aún no hay imágenes, usar Store Content products API
        if not key_images:
            title = (game_data.get('display_name') or game_data.get('app_name') or '').strip()
            if title:
                q = urllib.parse.quote(title)
                products_url = (
                    "https://store-content-public-service-prod06.ol.epicgames.com/store/api/products"
                    f"?locale=en-US&country=US&keywords={q}"
                )
                try:
                    with urllib.request.urlopen(products_url, timeout=10) as resp:
                        if resp.status == 200:
                            prod_data = json.loads(resp.read().decode('utf-8'))
                            elements = prod_data.get('elements') or []
                            chosen = None
                            for el in elements:
                                t = (el.get('title') or '').lower().strip()
                                if t == title.lower().strip():
                                    chosen = el
                                    break
                            if not chosen and elements:
                                chosen = elements[0]
                            if chosen:
                                key_images = chosen.get('keyImages') or []
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
                    pass

        # Si seguimos sin URL por tipos preferidos pero hay key_images, tomar la primera disponible
        if (not grid_url or not header_url or not icon_url) and key_images:
            def _first_url():
                for ki in key_images:
                    if ki.get('url'):
                        return ki['url']
                return None
            grid_url = grid_url or _first_url()
            header_url = header_url or grid_url or _first_url()
            icon_url = icon_url or _first_url()

        # Descargar y cachear
        cache_dir = Path.home() / '.game_library' / 'epic_images'
        cache_dir.mkdir(parents=True, exist_ok=True)

        def _download(url: Optional[str], suffix: str) -> Optional[str]:
            if not url:
                return None
            # Construir nombre de archivo estable
            ext = '.jpg' if '.jpg' in url or '.jpeg' in url else '.png'
            filename = f"{item_id}_{suffix}{ext}"
            save_path = cache_dir / filename
            if save_path.exists():
                return str(save_path)
            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    if r.status == 200:
                        with open(save_path, 'wb') as f:
                            f.write(r.read())
                        return str(save_path)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
                return None
            return None

        result = {
            'header': _download(header_url, 'header'),
            'icon': _download(icon_url, 'icon'),
            'grid': _download(grid_url, 'grid') or _download(header_url, 'grid')
        }

        # Fallback local: buscar imágenes en ProgramData o carpeta de instalación
        if not (result['grid'] or result['header'] or result['icon']):
            candidates: List[Path] = []
            # ProgramData rutas conocidas
            program_data_paths = [
                Path("C:/ProgramData/Epic/EpicGamesLauncher/Data/Images/CatalogImages"),
                Path("C:/ProgramData/Epic/EpicGamesLauncher/Data/Images/ManifestImages"),
            ]
            for p in program_data_paths:
                if p.exists():
                    for ext in ('*.jpg','*.jpeg','*.png'):
                        candidates.extend(list(p.rglob(ext)))
            # Carpeta de instalación del juego
            install_location = Path(game_data.get('install_location',''))
            if install_location.exists():
                for ext in ('*.jpg','*.jpeg','*.png'):
                    # limitar profundidad para rendimiento
                    for fp in install_location.rglob(ext):
                        # ignorar archivos minúsculos (iconos)
                        try:
                            if fp.stat().st_size > 50_000:
                                candidates.append(fp)
                        except Exception:
                            continue
            # Heurística por nombre
            name_hints = ['cover','splash','header','art','poster','box','wide']
            scored: List[tuple[int, Path]] = []
            for fp in candidates:
                fname = fp.name.lower()
                score = 0
                for h in name_hints:
                    if h in fname:
                        score += 2
                # preferir anchos grandes
                try:
                    size = fp.stat().st_size
                    if size > 150_000:
                        score += 2
                    elif size > 80_000:
                        score += 1
                except Exception:
                    pass
                # preferir coincidencias con app_name o item_id
                app_name = (game_data.get('app_name') or '').lower()
                if app_name and app_name in fname:
                    score += 2
                if item_id and item_id in fname:
                    score += 1
                if score:
                    scored.append((score, fp))
            if scored:
                scored.sort(key=lambda x: (-x[0], x[1].name))
                best = scored[0][1]
                # copiar al cache
                ext = best.suffix.lower()
                def _copy_to_cache(src: Path, suffix: str) -> Optional[str]:
                    dst = cache_dir / f"{item_id}_{suffix}{ext}"
                    try:
                        if not dst.exists():
                            with open(src, 'rb') as rf, open(dst, 'wb') as wf:
                                wf.write(rf.read())
                        return str(dst)
                    except Exception:
                        return None
                # usar como grid y header
                result['grid'] = result['grid'] or _copy_to_cache(best, 'grid_local')
                result['header'] = result['header'] or _copy_to_cache(best, 'header_local')
                # icono: intentar uno más pequeño si disponible
                small = None
                for _, fp in scored[::-1]:
                    try:
                        if fp.stat().st_size < 120_000:
                            small = fp
                            break
                    except Exception:
                        continue
                if small:
                    result['icon'] = result['icon'] or _copy_to_cache(small, 'icon_local')

        # Último intento: si ninguna imagen descargó pero alguna URL existía, intenta nuevamente con tiempos distintos
        if not (result['grid'] or result['header'] or result['icon']):
            # Reintentar con header como grid si existe URL
            if header_url and not result['grid']:
                result['grid'] = _download(header_url, 'grid2')
            # Reintentar con grid como header
            if grid_url and not result['header']:
                result['header'] = _download(grid_url, 'header2')
            # Reintentar con cualquier
            if icon_url and not result['icon']:
                result['icon'] = _download(icon_url, 'icon2')

        return result


def test_epic_scanner():
    """Función de prueba para el escáner de Epic"""
    scanner = EpicScanner()
    
    print("=== Epic Games Scanner Test ===")
    print(f"Epic installation path: {scanner.epic_path}")
    print(f"Manifest folder: {scanner.manifest_folder}")
    print()
    
    if scanner.manifest_folder:
        games = scanner.scan_installed_games()
        print(f"Found {len(games)} installed games:\n")
        
        for i, game in enumerate(games, 1):
            print(f"{i}. {game['display_name']}")
            print(f"   App Name: {game['app_name']}")
            print(f"   Location: {game['install_location']}")
            
            exe_path = scanner.get_game_executable_path(game)
            if exe_path:
                print(f"   Executable: {exe_path}")
            
            launch_cmd = scanner.get_launch_command(game)
            if launch_cmd:
                print(f"   Launch: {launch_cmd}")
            print()
    else:
        print("Epic Games Store not found or no games installed.")


if __name__ == "__main__":
    test_epic_scanner()

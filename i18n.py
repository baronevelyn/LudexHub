"""Módulo de internacionalización (i18n) para Game Library"""

# Diccionario de traducciones: ES (español) e EN (inglés)
TRANSLATIONS = {
    'es': {
        # Ventana principal
        'app_title': 'Mi Biblioteca de Juegos',
        'app_title_alt': 'Game Library v1.0',
        
        # Botones principales
        'btn_add_game': '+ Agregar Juego',
        'btn_import_games': 'Importar Juegos',
        'btn_settings': 'Configuración',
        'btn_search_placeholder': '🔍 Buscar juegos...',
        
        # Modos de vista
        'view_grid': 'Vista Grid',
        'view_list': 'Vista Lista',
        
        # Diálogo de agregar/editar juego
        'dialog_add_game': 'Agregar Juego',
        'dialog_edit_game': 'Editar Juego',
        'label_game_name': 'Nombre del Juego *',
        'placeholder_game_name': 'Ej: The Witcher 3',
        'label_exe_path': 'Ruta del Ejecutable *',
        'placeholder_exe_path': 'C:\\Program Files\\Game\\game.exe',
        'label_cover_image': 'Imagen de Portada',
        'placeholder_cover_image': 'URL o ruta local de la imagen',
        'label_icon': 'Icono del Juego',
        'placeholder_icon': 'URL o ruta local del icono',
        'btn_browse': '📁',
        'btn_cancel': 'Cancelar',
        'btn_save': 'Guardar',
        
        # Diálogo de importar juegos
        'dialog_import': 'Importar Juegos',
        'btn_steam': 'Steam',
        'btn_epic': 'Epic',
        
        # Diálogo de configuración
        'dialog_settings': 'Configuración',
        'dialog_customization': 'Personalizar Apariencia',
        'tab_general': 'General',
        'tab_background': 'Fondo',
        'tab_general_colors': 'Colores Generales',
        'tab_card_colors': 'Colores de Tarjetas',
        'label_bg_image': 'Imagen de Fondo (opcional)',
        'placeholder_bg_image': 'Ruta local a imagen (PNG/JPG)',
        'label_opacity': 'Opacidad del Fondo (0 = invisible, 40 = más visible)',
        'label_opacity_current': 'Opacidad actual: {value}%',
        'label_bg_history': 'Historial de Fondos (hasta 8)',
        'label_presets': 'Presets de Tema:',
        'preset_base': 'Base',
        'preset_light': 'Light',
        'preset_dark': 'Dark',
        'preset_pink': 'Pink',
        'btn_reset': 'Restablecer',
        'label_language': 'Idioma:',
        'language_es': 'Español',
        'language_en': 'English',
        'label_auto_start': 'Abrir al encender el PC',
        
        # Colores personalizables
        'label_general_colors': 'Colores Generales',
        'label_card_bg': 'Fondo de Tarjeta',
        'label_card_border': 'Borde de Tarjeta',
        'label_card_hover_bg': 'Fondo Tarjeta (Hover)',
        'label_card_hover_border': 'Borde Tarjeta (Hover)',
        'label_accent_start': 'Color Primario',
        'label_accent_end': 'Color Secundario',
        'label_text_primary': 'Texto Principal',
        'label_text_secondary': 'Texto Secundario',
        'label_bg_gradient_start': 'Fondo Gradiente (Inicio)',
        'label_bg_gradient_end': 'Fondo Gradiente (Final)',
        'label_top_bar_bg': 'Barra Superior',
        'label_input_bg': 'Fondo de Campos',
        'label_input_border': 'Borde de Campos',
        
        # Badges
        'badge_steam': 'Steam',
        'badge_epic': 'Epic',
        
        # Mensajes
        'msg_game_added': 'Juego agregado exitosamente',
        'msg_game_updated': 'Juego actualizado',
        'msg_game_deleted': 'Juego eliminado',
        'msg_error_name': 'Por favor ingresa un nombre',
        'msg_error_path': 'Por favor selecciona una ruta válida',
        'msg_confirm_delete': '¿Estás seguro de que deseas eliminar "{name}"?',
        'msg_no_games_steam': 'No se encontraron juegos de Steam',
        'msg_no_games_epic': 'No se encontraron juegos de Epic',
        'msg_startup_enable': '¿Quieres que Game Library se abra al encender tu PC?',
        'msg_startup_title': 'Inicio automático',
        'msg_startup_enabled': 'Auto-inicio habilitado',
        'msg_startup_disabled': 'Auto-inicio deshabilitado',
        
        # Errores
        'error_loading_image': 'Error al cargar imagen',
        'error_invalid_path': 'Ruta inválida',
        'error_no_executable': 'Archivo ejecutable no encontrado',
        'error_generic': 'Error',
        
        # Primera ejecución
        'first_run_title': 'Bienvenido a Game Library',
        'first_run_msg': 'Se ha creado la carpeta de datos en tu perfil. ¿Deseas que la aplicación se abra al encender tu PC?',
        
        # Otros
        'btn_yes': 'Sí',
        'btn_no': 'No',
        'btn_ok': 'OK',
        'loading': 'Cargando...',
        'importing': 'Importando...',
    },
    'en': {
        # Ventana principal
        'app_title': 'My Game Library',
        'app_title_alt': 'Game Library v1.0',
        
        # Botones principales
        'btn_add_game': '+ Add Game',
        'btn_import_games': 'Import Games',
        'btn_settings': 'Settings',
        'btn_search_placeholder': '🔍 Search games...',
        
        # Modos de vista
        'view_grid': 'Grid View',
        'view_list': 'List View',
        
        # Diálogo de agregar/editar juego
        'dialog_add_game': 'Add Game',
        'dialog_edit_game': 'Edit Game',
        'label_game_name': 'Game Name *',
        'placeholder_game_name': 'E.g.: The Witcher 3',
        'label_exe_path': 'Executable Path *',
        'placeholder_exe_path': 'C:\\Program Files\\Game\\game.exe',
        'label_cover_image': 'Cover Image',
        'placeholder_cover_image': 'URL or local image path',
        'label_icon': 'Game Icon',
        'placeholder_icon': 'URL or local icon path',
        'btn_browse': '📁',
        'btn_cancel': 'Cancel',
        'btn_save': 'Save',
        
        # Diálogo de importar juegos
        'dialog_import': 'Import Games',
        'btn_steam': 'Steam',
        'btn_epic': 'Epic',
        
        # Diálogo de configuración
        'dialog_settings': 'Settings',
        'dialog_customization': 'Customize Appearance',
        'tab_general': 'General',
        'tab_background': 'Background',
        'tab_general_colors': 'General Colors',
        'tab_card_colors': 'Card Colors',
        'label_bg_image': 'Background Image (optional)',
        'placeholder_bg_image': 'Local image path (PNG/JPG)',
        'label_opacity': 'Background Opacity (0 = invisible, 40 = more visible)',
        'label_opacity_current': 'Current opacity: {value}%',
        'label_bg_history': 'Background History (up to 8)',
        'label_presets': 'Theme Presets:',
        'preset_base': 'Base',
        'preset_light': 'Light',
        'preset_dark': 'Dark',
        'preset_pink': 'Pink',
        'btn_reset': 'Reset',
        'label_language': 'Language:',
        'language_es': 'Español',
        'language_en': 'English',
        'label_auto_start': 'Open when PC starts',
        
        # Colores personalizables
        'label_general_colors': 'General Colors',
        'label_card_bg': 'Card Background',
        'label_card_border': 'Card Border',
        'label_card_hover_bg': 'Card Background (Hover)',
        'label_card_hover_border': 'Card Border (Hover)',
        'label_accent_start': 'Primary Color',
        'label_accent_end': 'Secondary Color',
        'label_text_primary': 'Primary Text',
        'label_text_secondary': 'Secondary Text',
        'label_bg_gradient_start': 'Background Gradient (Start)',
        'label_bg_gradient_end': 'Background Gradient (End)',
        'label_top_bar_bg': 'Top Bar',
        'label_input_bg': 'Input Background',
        'label_input_border': 'Input Border',
        
        # Badges
        'badge_steam': 'Steam',
        'badge_epic': 'Epic',
        
        # Mensajes
        'msg_game_added': 'Game added successfully',
        'msg_game_updated': 'Game updated',
        'msg_game_deleted': 'Game deleted',
        'msg_error_name': 'Please enter a game name',
        'msg_error_path': 'Please select a valid path',
        'msg_confirm_delete': 'Are you sure you want to delete "{name}"?',
        'msg_no_games_steam': 'No Steam games found',
        'msg_no_games_epic': 'No Epic games found',
        'msg_startup_enable': 'Do you want Game Library to open when your PC starts?',
        'msg_startup_title': 'Auto-start',
        'msg_startup_enabled': 'Auto-start enabled',
        'msg_startup_disabled': 'Auto-start disabled',
        
        # Errores
        'error_loading_image': 'Error loading image',
        'error_invalid_path': 'Invalid path',
        'error_no_executable': 'Executable file not found',
        'error_generic': 'Error',
        
        # Primera ejecución
        'first_run_title': 'Welcome to Game Library',
        'first_run_msg': 'Data folder has been created. Do you want Game Library to open when your PC starts?',
        
        # Otros
        'btn_yes': 'Yes',
        'btn_no': 'No',
        'btn_ok': 'OK',
        'loading': 'Loading...',
        'importing': 'Importing...',
    }
}

class I18n:
    """Gestor de idioma y traducciones"""
    _instance = None
    _language = 'es'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Retorna la instancia singleton"""
        return cls()
    
    @classmethod
    def set_language(cls, lang: str):
        """Cambia el idioma actual (es/en)"""
        if lang in ['es', 'en']:
            cls._language = lang
    
    @classmethod
    def get_language(cls) -> str:
        """Retorna el idioma actual"""
        return cls._language
    
    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        """Obtiene la traducción de una clave con interpolación opcional"""
        lang = cls._language
        translations = TRANSLATIONS.get(lang, TRANSLATIONS['es'])
        text = translations.get(key, key)
        
        # Soportar interpolación de variables: {variable} -> valor
        if kwargs:
            text = text.format(**kwargs)
        
        return text

def translate(key: str, **kwargs) -> str:
    """Función de conveniencia para obtener traducciones"""
    return I18n.t(key, **kwargs)

# Alias corto
t = translate

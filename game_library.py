import sys
import json
import os
import subprocess
from pathlib import Path
import tempfile
import ctypes
import uuid
from datetime import datetime, timedelta
from steam_scanner import SteamScanner
from epic_scanner import EpicScanner
from i18n import I18n, t
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                             QLineEdit, QDialog, QScrollArea, QFrame, QComboBox,
                             QMessageBox, QFileDialog, QMenu, QSlider, QToolButton, 
                             QProgressDialog, QCheckBox, QGraphicsOpacityEffect, QInputDialog,
                             QActionGroup)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QFileInfo, QPropertyAnimation, QEasingCurve, QPoint, QEvent, QRect, QTimer
try:
    from PyQt5.QtWinExtras import QtWin
except Exception:
    QtWin = None
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QColor, QFont, QPainter, QBrush, QMovie, QImage


class ImageLoader(QThread):
    """Thread para cargar imágenes desde URLs sin bloquear la UI"""
    image_loaded = pyqtSignal(str, QPixmap)
    
    def __init__(self, url, game_id):
        super().__init__()
        self.url = url
        self.game_id = game_id
    
    def run(self):
        import urllib.request
        try:
            # Descargar la imagen usando urllib
            with urllib.request.urlopen(self.url, timeout=10) as response:
                data = response.read()
                pixmap = QPixmap()
                if pixmap.loadFromData(data):
                    self.image_loaded.emit(self.game_id, pixmap)
        except Exception as e:
            print(f"Error al cargar imagen {self.url}: {e}")


class GameCard(QFrame):
    """Widget personalizado para mostrar cada juego"""
    _custom_colors = {}
    
    def __init__(self, game, parent=None, list_mode=False, animation_delay=0):
        super().__init__(parent)
        self.game = game
        self.parent_window = parent
        self.list_mode = list_mode
        self.animation_delay = animation_delay
        self.cover_movie = None  # QMovie para GIF animado en cover
        self._is_visible = False  # Track visibility para pausar GIF
        self.setup_ui()

    def _format_playtime(self, seconds):
        seconds = int(seconds or 0)
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        # Usar colores personalizados si existen
        c = GameCard._custom_colors
        card_bg = c.get('card_bg', '#1a1f2e')
        card_border = c.get('card_border', 'transparent')
        card_hover_border = c.get('card_hover_border', '#667eea')
        card_hover_bg = c.get('card_hover_bg', '#252d3d')
        card_radius = c.get('card_radius', 12)
        border_width = c.get('border_width', 2)
        font_family = c.get('font_family', 'Segoe UI')
        card_title_size = c.get('card_title_size', 15)
        secondary_size = c.get('secondary_size', 12)
        button_radius = c.get('button_radius', 8)
        
        self.setStyleSheet(f"""
            GameCard {{
                background-color: {card_bg};
                border-radius: {card_radius}px;
                border: {border_width}px solid {card_border};
                font-family: {font_family};
            }}
            GameCard:hover {{
                border: {border_width}px solid {card_hover_border};
                background-color: {card_hover_bg};
            }}
        """)
        if self.list_mode:
            self.setFixedSize(900, 180)
        else:
            self.setFixedSize(300, 280)
        self.setCursor(Qt.PointingHandCursor)
        self._orig_rect = None
        self._anim = None
        self.is_favorite = self.game.get('is_favorite', False)
        
        # Layout raíz: en lista usamos horizontal (imagen a la izquierda)
        if self.list_mode:
            layout = QHBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(12)
        else:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        
        # Imagen del juego
        self.image_label = QLabel()
        if self.list_mode:
            self.image_label.setFixedSize(316, 176)
        else:
            self.image_label.setFixedSize(296, 176)
        self.image_label.setAlignment(Qt.AlignCenter)
        accent_start = c.get('accent_start', '#667eea')
        accent_end = c.get('accent_end', '#764ba2')
        self.image_label.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {accent_start}, stop:1 {accent_end});
            font-size: 48px;
        """)
        
        # Cargar imagen si existe
        if self.game.get('image'):
            self.load_image(self.game['image'])
        else:
            self.image_label.setText("🎮")
        
        # Botón de favorito (aparece solo en hover)
        self.favorite_btn = QPushButton('⭐' if self.is_favorite else '☆')
        self.favorite_btn.setFixedSize(40, 40)
        self.favorite_btn.setVisible(False)  # Oculto por defecto
        self.favorite_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 200);
                border: none;
                border-radius: 20px;
                font-size: 20px;
                color: #FFD700;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 240);
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 180);
            }}
        """)
        def toggle_favorite():
            self.is_favorite = not self.is_favorite
            self.favorite_btn.setText('⭐' if self.is_favorite else '☆')
            if self.parent_window:
                self.parent_window.toggle_favorite(self.game['id'], self.is_favorite)
        self.favorite_btn.clicked.connect(toggle_favorite)
        
        if self.list_mode:
            # Lista: imagen a la izquierda y, a la derecha, SOLO el nombre grande
            layout.addWidget(self.image_label)
            right = QWidget()
            right_layout = QVBoxLayout(right)
            right_layout.setContentsMargins(10, 10, 10, 10)
            right_layout.setSpacing(8)
            name_label = QLabel(self.game['name'])
            text_color = c.get('text_primary', '#e8eaed')
            text_secondary = c.get('text_secondary', '#9aa0a6')
            name_font = QFont(font_family, card_title_size + 6, QFont.Bold)
            name_label.setFont(name_font)
            name_label.setStyleSheet(f"color:{text_color};")
            name_label.setWordWrap(True)
            right_layout.addWidget(name_label)

            playtime_seconds = int(self.game.get('total_play_time', 0) or 0)
            playtime_label = QLabel(t('label_playtime', value=self._format_playtime(playtime_seconds)))
            playtime_font = QFont(font_family, secondary_size)
            playtime_label.setFont(playtime_font)
            playtime_label.setStyleSheet(f"color:{text_secondary};")
            self.playtime_label = playtime_label
            right_layout.addWidget(playtime_label)
            # Badge Steam si aplica
            if self.game.get('is_steam_game'):
                steam_badge = QLabel("Steam")
                steam_badge.setStyleSheet("""
                    QLabel { color: #cfe6ff; background-color:#1b2838; border:1px solid #2a475e; border-radius:6px; padding:4px 8px; font-weight:700; font-size:12px;}
                """)
                steam_badge.setFixedHeight(24)
                right_layout.addWidget(steam_badge)
            # Badge Epic si aplica
            if self.game.get('is_epic_game'):
                epic_badge = QLabel("Epic")
                epic_badge.setStyleSheet("""
                    QLabel { color: #ffffff; background-color:#1a1a1a; border:1px solid #2d2d2d; border-radius:6px; padding:4px 8px; font-weight:700; font-size:12px;}
                """)
                epic_badge.setFixedHeight(24)
                right_layout.addWidget(epic_badge)
            right_layout.addStretch()
            # Agregar botón favorito en lista
            right_layout.addWidget(self.favorite_btn, alignment=Qt.AlignTop | Qt.AlignRight)
            layout.addWidget(right, 1)
        else:
            # Grid: imagen arriba, debajo icono + nombre + ruta
            # Crear container para imagen + botón favorito
            image_container = QWidget()
            image_container_layout = QHBoxLayout(image_container)
            image_container_layout.setContentsMargins(0, 0, 0, 0)
            image_container_layout.addWidget(self.image_label)
            image_container_layout.addStretch()
            image_container_layout.addWidget(self.favorite_btn, alignment=Qt.AlignTop | Qt.AlignRight)
            layout.addWidget(image_container)
            
            content_widget = QWidget()
            content_widget.setStyleSheet(f"background-color: {card_bg};")
            content_layout = QHBoxLayout()
            content_layout.setContentsMargins(15, 15, 15, 15)

            # Icono
            icon_label = QLabel()
            icon_label.setFixedSize(50, 50)
            from PyQt5 import QtCore
            icon_label.setAlignment(QtCore.Qt.AlignCenter)
            icon_label.setStyleSheet(f"""
                background-color: {card_hover_bg};
                border-radius: {button_radius}px;
                font-size: 24px;
            """)
            self.icon_label = icon_label
            if self.game.get('icon'):
                self.load_icon(self.game['icon'], icon_label)
            else:
                if self.game.get('path') and os.path.exists(self.game['path']):
                    self.extract_exe_icon(self.game['path'], icon_label)
                else:
                    icon_label.setText("🎮")
            # Añadir icono e info (nombre y ruta) en la parte inferior (grid)
            content_layout.addWidget(icon_label)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(5)

            name_label = QLabel(self.game['name'])
            text_color = c.get('text_primary', '#e8eaed')
            name_font = QFont(font_family, card_title_size, QFont.Bold)
            name_label.setFont(name_font)
            name_label.setStyleSheet(f"color: {text_color};")
            name_label.setWordWrap(False)

            path_label = QLabel(self.game['path'])
            text_secondary = c.get('text_secondary', '#9aa0a6')
            path_font = QFont(font_family, secondary_size - 1)
            path_label.setFont(path_font)
            path_label.setStyleSheet(f"color: {text_secondary};")
            path_label.setWordWrap(False)

            info_layout.addWidget(name_label)
            info_layout.addWidget(path_label)
            playtime_seconds = int(self.game.get('total_play_time', 0) or 0)
            playtime_label = QLabel(t('label_playtime', value=self._format_playtime(playtime_seconds)))
            playtime_font = QFont(font_family, secondary_size - 1)
            playtime_label.setFont(playtime_font)
            playtime_label.setStyleSheet(f"color: {text_secondary};")
            self.playtime_label = playtime_label
            info_layout.addWidget(playtime_label)
            # Badge Steam si aplica
            if self.game.get('is_steam_game'):
                steam_badge = QLabel("Steam")
                steam_badge.setStyleSheet("""
                    QLabel { color: #cfe6ff; background-color:#1b2838; border:1px solid #2a475e; border-radius:6px; padding:3px 6px; font-weight:700; font-size:11px;}
                """)
                steam_badge.setFixedHeight(20)
                info_layout.addWidget(steam_badge)
            # Badge Epic si aplica
            if self.game.get('is_epic_game'):
                epic_badge = QLabel("Epic")
                epic_badge.setStyleSheet("""
                    QLabel { color: #ffffff; background-color:#1a1a1a; border:1px solid #2d2d2d; border-radius:6px; padding:3px 6px; font-weight:700; font-size:11px;}
                """)
                epic_badge.setFixedHeight(20)
                info_layout.addWidget(epic_badge)
            info_layout.addStretch()

            content_layout.addLayout(info_layout, 1)
            content_widget.setLayout(content_layout)
            layout.addWidget(content_widget)

        self.setLayout(layout)
        
        # Aplicar fade-in después de que el widget esté construido
        self.setWindowOpacity(1.0)  # Asegurar opacidad normal
        opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)  # Empezar invisible
        self.fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)  # 500ms - más lento
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        # Remover el efecto cuando termine para no interferir con hover
        # Verificar si el widget aún existe antes de remover el efecto
        def remove_effect():
            try:
                if self and self.isValid() if hasattr(self, 'isValid') else True:
                    self.setGraphicsEffect(None)
            except RuntimeError:
                pass  # Widget fue eliminado
        self.fade_animation.finished.connect(remove_effect)
        # Iniciar con delay para efecto secuencial
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(self.animation_delay, self.fade_animation.start)

    def load_image(self, url_or_path):
        """Cargar imagen desde URL o ruta local (soporta GIF animados)"""
        if os.path.exists(url_or_path):
            # Detectar si es GIF
            if url_or_path.lower().endswith('.gif'):
                self._load_gif_cover(url_or_path)
                return
            pixmap = QPixmap(url_or_path)
            if not pixmap.isNull():
                self.set_image(self.game['id'], pixmap)
                return
        if url_or_path.startswith(('http://', 'https://')):
            loader = ImageLoader(url_or_path, self.game['id'])
            loader.image_loaded.connect(self.set_image)
            loader.start()
            self.image_loader = loader

    def set_image(self, game_id, pixmap):
        """Establecer la imagen cargada en el label de portada"""
        if game_id == self.game['id']:
            target_size = self.image_label.size()
            w = max(1, target_size.width())
            h = max(1, target_size.height())
            scaled_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")

    def _load_gif_cover(self, gif_path):
        """Cargar GIF animado en el cover de la card"""
        try:
            if self.cover_movie:
                self.cover_movie.stop()
            self.cover_movie = QMovie(gif_path)
            self.cover_movie.setCacheMode(QMovie.CacheAll)
            # Conectar señal para actualizar label con cada frame
            self.cover_movie.frameChanged.connect(self._update_gif_frame)
            self.image_label.setMovie(self.cover_movie)
            self.image_label.setText("")
            # Solo iniciar si la card es visible
            if self._is_visible:
                self.cover_movie.start()
        except Exception as e:
            print(f'Error cargando GIF cover: {e}')

    def _update_gif_frame(self):
        """Actualiza el frame del GIF en el label (escalado)"""
        if not self.cover_movie:
            return
        current = self.cover_movie.currentPixmap()
        if not current.isNull():
            target_size = self.image_label.size()
            w = max(1, target_size.width())
            h = max(1, target_size.height())
            scaled = current.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            
    def load_icon(self, url_or_path, label):
        """Cargar icono desde URL o ruta local"""
        # Si es una ruta local, cargar directamente
        if os.path.exists(url_or_path):
            pixmap = QPixmap(url_or_path)
            if not pixmap.isNull():
                self.set_icon(label, pixmap)
                return
        
        # Si es una URL, cargar en thread separado
        if url_or_path.startswith(('http://', 'https://')):
            loader = ImageLoader(url_or_path, self.game['id'] + '_icon')
            loader.image_loaded.connect(lambda gid, pm: self.set_icon(label, pm))
            loader.start()
            self.icon_loader = loader
        
    def set_icon(self, label, pixmap):
        """Establecer el icono cargado"""
        from PyQt5 import QtCore
        from PyQt5.QtGui import QPixmap as _QPixmap, QPainter
        # Render consistente dentro de un lienzo 50x50 para evitar problemas de DPI
        canvas = _QPixmap(50, 50)
        canvas.fill(Qt.transparent)
        # Escalar icono con margen 4px por lado
        icon_pm = pixmap.scaled(42, 42, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        painter = QPainter(canvas)
        x = (50 - icon_pm.width()) // 2
        y = (50 - icon_pm.height()) // 2
        painter.drawPixmap(x, y, icon_pm)
        painter.end()
        label.setPixmap(canvas)
        label.setText("")
    
    def extract_exe_icon(self, exe_path, label):
        """Extraer icono del archivo ejecutable usando win32api"""
        # Intentar cargar icono guardado previamente
        icon_dir = Path.home() / '.game_library' / 'icons'
        icon_dir.mkdir(parents=True, exist_ok=True)
        saved_icon = icon_dir / (Path(exe_path).stem + '_icon.png')
        
        if saved_icon.exists():
            pm = QPixmap(str(saved_icon))
            if not pm.isNull():
                # Validar que el caché no esté corrupto (muy pequeño)
                if pm.width() >= 16 and pm.height() >= 16:
                    self.set_icon(label, pm)
                    return
                else:
                    # Caché corrupto, borrarlo y re-extraer
                    saved_icon.unlink()
                    print(f"Caché corrupto borrado: {saved_icon.name}")
        
        # Método principal: QtWinExtras (más confiable que QIcon)
        try:
            from PyQt5.QtWinExtras import QtWin
            import ctypes
            from ctypes import wintypes, byref, POINTER
            
            # Usar shell32 para extraer el icono
            ExtractIconExW = ctypes.windll.shell32.ExtractIconExW
            ExtractIconExW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, POINTER(wintypes.HICON), POINTER(wintypes.HICON), wintypes.UINT]
            ExtractIconExW.restype = wintypes.UINT
            
            large_icon = wintypes.HICON()
            small_icon = wintypes.HICON()
            
            count = ExtractIconExW(exe_path, 0, byref(large_icon), byref(small_icon), 1)
            print(f'ExtractIconExW count: {count}, large_icon: {large_icon.value}')
            
            if count > 0 and large_icon.value:
                # Convertir HICON a QPixmap usando QtWinExtras
                pixmap = QtWin.fromHICON(large_icon.value)
                print(f'Pixmap extraído: {pixmap.width()}x{pixmap.height()}, isNull: {pixmap.isNull()}')
                
                if not pixmap.isNull():
                    # Escalar a 40x40 si es necesario (algunos .exe tienen iconos pequeños)
                    if pixmap.width() != 40 or pixmap.height() != 40:
                        pixmap = pixmap.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                        print(f'Pixmap escalado a: {pixmap.width()}x{pixmap.height()}')
                    
                    # Guardar como PNG y aplicar al label de forma consistente
                    success = pixmap.save(str(saved_icon), 'PNG')
                    print(f'PNG guardado: {success} -> {saved_icon}')
                    self.set_icon(label, pixmap)
                    
                    # Limpiar recursos
                    ctypes.windll.user32.DestroyIcon(large_icon)
                    if small_icon.value:
                        ctypes.windll.user32.DestroyIcon(small_icon)
                    return
                else:
                    print(f'Pixmap es null después de fromHICON')
                    
        except Exception as e:
            print(f'QtWinExtras fallo: {e}')
            import traceback
            traceback.print_exc()
        
        # Fallback emoji
        label.setText('🎮')
    
    def mouseDoubleClickEvent(self, event):
        """Ejecutar juego al hacer doble clic"""
        if self.parent_window:
            self.parent_window.play_game(self.game)
            
    def contextMenuEvent(self, event):
        """Menú contextual con clic derecho"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1f2e;
                border: 1px solid #2d3748;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                color: #e8eaed;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #252d3d;
            }
        """)
        
        play_action = menu.addAction("▶ Jugar")
        edit_action = menu.addAction("✎ Editar")
        delete_action = menu.addAction("🗑 Eliminar")

        folders_menu = menu.addMenu(t('menu_folders'))
        folders_menu.setStyleSheet(menu.styleSheet())
        new_folder_action = folders_menu.addAction(f"＋ {t('btn_new_folder')}")
        folders_menu.addSeparator()
        folders = []
        if self.parent_window:
            folders = self.parent_window._collect_folders()
        for fname in ['Steam', 'Epic']:
            if fname not in folders:
                folders.append(fname)
        seen = set()
        for fname in folders:
            if fname in seen:
                continue
            seen.add(fname)
            action = folders_menu.addAction(fname)
            action.setCheckable(True)
            if fname in (self.game.get('folders') or []):
                action.setChecked(True)
            is_auto_locked = (fname == 'Steam' and self.game.get('is_steam_game')) or (fname == 'Epic' and self.game.get('is_epic_game'))
            if is_auto_locked:
                action.setDisabled(True)
            def make_handler(folder=fname, act=action, locked=is_auto_locked):
                return lambda: self.parent_window and self.parent_window._update_game_folders(self.game['id'], folder, add=act.isChecked(), lock_auto=locked)
            action.toggled.connect(make_handler())

        def handle_new_folder():
            if self.parent_window:
                self.parent_window._show_new_folder_dialog()
        new_folder_action.triggered.connect(handle_new_folder)
        
        action = menu.exec_(event.globalPos())
        
        if action == play_action:
            self.parent_window.play_game(self.game)
        elif action == edit_action:
            self.parent_window.edit_game(self.game)
        elif action == delete_action:
            self.parent_window.delete_game(self.game)

    def enterEvent(self, event):
        self.favorite_btn.setVisible(True)  # Mostrar botón de favorito
        if self.list_mode:
            return super().enterEvent(event)
        self._orig_rect = self.geometry()
        g = self._orig_rect
        target = QRect(g.x()-5, g.y()-5, g.width()+10, g.height()+10)
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(140)
        anim.setStartValue(g)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        self._anim = anim
        anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.favorite_btn.setVisible(False)  # Ocultar botón de favorito
        if self.list_mode:
            return super().leaveEvent(event)
        if self._orig_rect:
            g = self.geometry()
            anim = QPropertyAnimation(self, b"geometry")
            anim.setDuration(140)
            anim.setStartValue(g)
            anim.setEndValue(self._orig_rect)
            anim.setEasingCurve(QEasingCurve.OutQuad)
            self._anim = anim
            anim.start()
        super().leaveEvent(event)

    def showEvent(self, event):
        """Cuando la card se hace visible, reanudar GIF si existe"""
        super().showEvent(event)
        self._is_visible = True
        if self.cover_movie and not self.cover_movie.state() == QMovie.Running:
            self.cover_movie.start()

    def hideEvent(self, event):
        """Cuando la card se oculta, pausar GIF para ahorrar recursos"""
        super().hideEvent(event)
        self._is_visible = False
        if self.cover_movie and self.cover_movie.state() == QMovie.Running:
            self.cover_movie.setPaused(True)


class AddGameDialog(QDialog):
    """Diálogo para agregar o editar juegos"""
    
    def __init__(self, parent=None, game=None):
        super().__init__(parent)
        self.game = game
        self.setup_ui()
        
        if game:
            self.load_game_data()
            
    def setup_ui(self):
        self.setWindowTitle(t('dialog_add_game') if not self.game else t('dialog_edit_game'))
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1f2e;
            }
            QLabel {
                color: #e8eaed;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #0f1419;
                border: 2px solid #2d3748;
                border-radius: 8px;
                padding: 10px;
                color: #e8eaed;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: #252d3d;
            }
            QPushButton {
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#primaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7c8ef5, stop:1 #8a5cb8);
            }
            QPushButton#secondaryBtn {
                background-color: #252d3d;
                color: #e8eaed;
                border: 1px solid #2d3748;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #2d3748;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Nombre
        layout.addWidget(QLabel(t('label_game_name')))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(t('placeholder_game_name'))
        layout.addWidget(self.name_input)
        
        # Ruta con botón de búsqueda
        layout.addWidget(QLabel(t('label_exe_path')))
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(t('placeholder_exe_path'))
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("📁")
        browse_btn.setFixedSize(45, 45)
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Imagen
        layout.addWidget(QLabel(t('label_cover_image')))
        image_layout = QHBoxLayout()
        self.image_input = QLineEdit()
        self.image_input.setPlaceholderText(t('placeholder_cover_image'))
        image_layout.addWidget(self.image_input)
        
        browse_image_btn = QPushButton("📁")
        browse_image_btn.setFixedSize(45, 45)
        browse_image_btn.setObjectName("secondaryBtn")
        browse_image_btn.clicked.connect(self.browse_image)
        image_layout.addWidget(browse_image_btn)
        
        layout.addLayout(image_layout)
        
        # Icono
        layout.addWidget(QLabel(t('label_icon')))
        icon_layout = QHBoxLayout()
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText(t('placeholder_icon'))
        icon_layout.addWidget(self.icon_input)
        
        browse_icon_btn = QPushButton("📁")
        browse_icon_btn.setFixedSize(45, 45)
        browse_icon_btn.setObjectName("secondaryBtn")
        browse_icon_btn.clicked.connect(self.browse_icon)
        icon_layout.addWidget(browse_icon_btn)
        
        layout.addLayout(icon_layout)
        
        layout.addStretch()
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton(t('btn_cancel'))
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton(t('btn_save'))
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def browse_file(self):
        """Abrir diálogo para seleccionar archivo ejecutable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Ejecutable del Juego",
            "",
            "Ejecutables (*.exe);;Todos los archivos (*.*)"
        )
        if file_path:
            self.path_input.setText(file_path)
            if not self.icon_input.text().strip():
                self._auto_extract_icon(file_path)

    def _auto_extract_icon(self, exe_path):
        icon_dir = Path.home() / '.game_library' / 'icons'
        icon_dir.mkdir(exist_ok=True)
        out_path = icon_dir / (Path(exe_path).stem + '_icon.png')
        
        # Si ya existe, validar que no esté corrupto
        if out_path.exists():
            pm = QPixmap(str(out_path))
            if not pm.isNull() and pm.width() >= 16 and pm.height() >= 16:
                self.icon_input.setText(str(out_path))
                return
            else:
                # Caché corrupto, borrarlo
                out_path.unlink()
        
        # Extraer usando QtWinExtras
        try:
            from PyQt5.QtWinExtras import QtWin
            import ctypes
            from ctypes import wintypes, byref, POINTER
            
            ExtractIconExW = ctypes.windll.shell32.ExtractIconExW
            ExtractIconExW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, POINTER(wintypes.HICON), POINTER(wintypes.HICON), wintypes.UINT]
            ExtractIconExW.restype = wintypes.UINT
            
            large_icon = wintypes.HICON()
            small_icon = wintypes.HICON()
            
            count = ExtractIconExW(exe_path, 0, byref(large_icon), byref(small_icon), 1)
            
            if count > 0 and large_icon.value:
                pixmap = QtWin.fromHICON(large_icon.value)
                
                if not pixmap.isNull():
                    # Escalar a 40x40 forzado (algunos .exe tienen iconos pequeños)
                    if pixmap.width() != 40 or pixmap.height() != 40:
                        pixmap = pixmap.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                    
                    pixmap.save(str(out_path), 'PNG')
                    self.icon_input.setText(str(out_path))
                    
                    # Limpiar recursos
                    ctypes.windll.user32.DestroyIcon(large_icon)
                    if small_icon.value:
                        ctypes.windll.user32.DestroyIcon(small_icon)
                    return
                    
        except Exception as e:
            print(f'QtWinExtras auto-extract fallo: {e}')
    
    def browse_image(self):
        """Abrir diálogo para seleccionar imagen de portada"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Imagen de Portada",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif);;Todos los archivos (*.*)"
        )
        if file_path:
            self.image_input.setText(file_path)
    
    def browse_icon(self):
        """Abrir diálogo para seleccionar icono"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Icono del Juego",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.ico);;Todos los archivos (*.*)"
        )
        if file_path:
            self.icon_input.setText(file_path)
            
    def load_game_data(self):
        """Cargar datos del juego para edición"""
        self.name_input.setText(self.game['name'])
        self.path_input.setText(self.game['path'])
        self.image_input.setText(self.game.get('image', ''))
        self.icon_input.setText(self.game.get('icon', ''))
        
    def get_game_data(self):
        """Obtener datos del formulario"""
        return {
            'name': self.name_input.text().strip(),
            'path': self.path_input.text().strip(),
            'image': self.image_input.text().strip(),
            'icon': self.icon_input.text().strip()
        }


class ColorPickerDialog(QDialog):
    """Diálogo de configuración con pestañas para colores, fondo, tipografía e idioma"""
    language_changed = pyqtSignal(str)  # Emite cuando cambia el idioma
    
    def __init__(self, parent=None, current_bg='', current_opacity=0.15, color_scheme=None, current_bg_type='static', current_theme=None):
        super().__init__(parent)
        self.setWindowTitle(t('dialog_settings'))
        self.setFixedSize(900, 700)
        self._current_bg = current_bg
        self._current_opacity = current_opacity
        self._current_bg_type = current_bg_type or 'static'
        # Si se pasa un tema completo, usarlo; si no, construir desde color_scheme o defaults
        if current_theme:
            self._current_theme = current_theme.copy()
        elif color_scheme:
            # Migrar desde color_scheme antiguo + defaults para nuevos campos
            base = self.default_theme()
            base.update(color_scheme)
            self._current_theme = base
        else:
            self._current_theme = self.default_theme()
        # Mantener _color_scheme para compatibilidad (es un view de los colores del tema)
        self._color_scheme = {k: v for k, v in self._current_theme.items() if isinstance(v, str) and v.startswith('#')}
        self._color_buttons = {}
        self._font_controls = {}
        self._spacing_controls = {}
        self.setup_ui()

    def default_theme(self):
        """Retorna configuración de tema completo con colores, tipografía y espaciado"""
        return {
            # Colores
            'bg_gradient_start': '#0f1419',
            'bg_gradient_end': '#1a1f2e',
            'top_bar_bg': '#121822',
            'card_bg': '#1a1f2e',
            'card_border': 'transparent',
            'card_hover_border': '#667eea',
            'card_hover_bg': '#252d3d',
            'accent_start': '#667eea',
            'accent_end': '#764ba2',
            'text_primary': '#e8eaed',
            'text_secondary': '#9aa0a6',
            'input_bg': '#1a1f2e',
            'input_border': '#2d3748',
            # Tipografía
            'font_family': 'Segoe UI',
            'title_size': 18,
            'card_title_size': 16,
            'secondary_size': 13,
            'font_weight_title': 700,
            'font_weight_secondary': 600,
            # Espaciado y bordes
            'card_radius': 12,
            'card_padding': 10,
            'button_radius': 8,
            'border_width': 2,
            # Gradientes en cards
            'card_gradient_enabled': False,
            'card_gradient_start': '#1a1f2e',
            'card_gradient_end': '#252d3d'
        }

    def default_colors(self):
        """Mantener para compatibilidad - devuelve solo colores"""
        theme = self.default_theme()
        return {k: v for k, v in theme.items() if k not in ['font_family', 'title_size', 'card_title_size', 'secondary_size', 'font_weight_title', 'font_weight_secondary', 'card_radius', 'card_padding', 'button_radius', 'border_width', 'card_gradient_enabled', 'card_gradient_start', 'card_gradient_end']}

    def preset_presets(self):
        """Retorna un diccionario con todos los presets de temas disponibles"""
        return {
            'Base': {
                'bg_gradient_start': '#0f1419',
                'bg_gradient_end': '#1a1f2e',
                'top_bar_bg': '#121822',
                'card_bg': '#1a1f2e',
                'card_border': 'transparent',
                'card_hover_border': '#667eea',
                'card_hover_bg': '#252d3d',
                'accent_start': '#667eea',
                'accent_end': '#764ba2',
                'text_primary': '#e8eaed',
                'text_secondary': '#9aa0a6',
                'input_bg': '#1a1f2e',
                'input_border': '#2d3748'
            },
            'Light': {
                'bg_gradient_start': '#f5f5f5',
                'bg_gradient_end': '#ffffff',
                'top_bar_bg': '#e8e8e8',
                'card_bg': '#ffffff',
                'card_border': '#d1d5db',
                'card_hover_border': '#3b82f6',
                'card_hover_bg': '#f3f4f6',
                'accent_start': '#3b82f6',
                'accent_end': '#2563eb',
                'text_primary': '#1f2937',
                'text_secondary': '#6b7280',
                'input_bg': '#f9fafb',
                'input_border': '#d1d5db'
            },
            'Dark': {
                'bg_gradient_start': '#0a0e14',
                'bg_gradient_end': '#111827',
                'top_bar_bg': '#0f1419',
                'card_bg': '#1f2937',
                'card_border': 'transparent',
                'card_hover_border': '#a78bfa',
                'card_hover_bg': '#374151',
                'accent_start': '#8b5cf6',
                'accent_end': '#7c3aed',
                'text_primary': '#f9fafb',
                'text_secondary': '#9ca3af',
                'input_bg': '#1f2937',
                'input_border': '#374151'
            },
            'Pink': {
                'bg_gradient_start': '#2d1b29',
                'bg_gradient_end': '#1a1325',
                'top_bar_bg': '#221628',
                'card_bg': '#2d1b29',
                'card_border': 'transparent',
                'card_hover_border': '#ff6b9d',
                'card_hover_bg': '#3d2535',
                'accent_start': '#ff6b9d',
                'accent_end': '#c44569',
                'text_primary': '#ffd1dc',
                'text_secondary': '#d4a5b0',
                'input_bg': '#2d1b29',
                'input_border': '#4a2f3f'
            }
        }

    def apply_preset(self, preset_name):
        """Aplica un preset de tema y actualiza todos los botones de color"""
        presets = self.preset_presets()
        if preset_name in presets:
            self._color_scheme = presets[preset_name].copy()
            for key, btn in self._color_buttons.items():
                if key in self._color_scheme:
                    color = self._color_scheme[key]
                    btn.setText(color)
                    btn.setStyleSheet(f"QPushButton#colorBtn {{ background:{color}; color:white; border:2px solid #2d3748; }}")

    def setup_ui(self):
        from PyQt5.QtWidgets import QTabWidget, QColorDialog
        self.setStyleSheet("""
            QDialog { background-color:#1a1f2e; }
            QLabel { color:#e8eaed; font-weight:600; }
            QLineEdit { background:#0f1419; border:2px solid #2d3748; border-radius:8px; padding:8px; color:#e8eaed; }
            QLineEdit:focus { border-color:#667eea; background:#252d3d; }
            QPushButton { border-radius:8px; font-weight:600; }
            QPushButton#primary { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #667eea, stop:1 #764ba2); color:white; border:none; padding:10px 20px; }
            QPushButton#primary:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7c8ef5, stop:1 #8a5cb8); }
            QPushButton#secondary { background:#252d3d; color:#e8eaed; border:1px solid #2d3748; padding:10px 18px; }
            QPushButton#secondary:hover { background:#2d3748; }
            QPushButton#colorBtn { background:#252d3d; border:2px solid #2d3748; padding:8px 16px; min-width:120px; }
            QPushButton#colorBtn:hover { border-color:#667eea; }
            QSlider::groove:horizontal { background:#2d3748; height:6px; border-radius:3px; }
            QSlider::handle:horizontal { background:#667eea; width:16px; margin:-6px 0; border-radius:8px; }
            QTabWidget::pane { border:none; background:#1a1f2e; }
            QTabBar::tab { background:#252d3d; color:#9aa0a6; padding:10px 20px; border-radius:6px 6px 0 0; margin-right:4px; }
            QTabBar::tab:selected { background:#1a1f2e; color:#e8eaed; border-bottom:2px solid #667eea; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet("QWidget{background-color:#121822;}")
        tlay = QHBoxLayout(top_bar)
        tlay.setContentsMargins(16,8,16,8)
        title = QLabel(t('dialog_settings'))
        title.setStyleSheet("color:#e8eaed; font-size:18px; font-weight:700;")
        tlay.addWidget(title)
        tlay.addStretch()
        root.addWidget(top_bar)

        # Drag
        def _press(ev):
            if ev.button() == Qt.LeftButton:
                self._drag_pos = ev.globalPos() - self.frameGeometry().topLeft()
                ev.accept()
        def _move(ev):
            if ev.buttons() & Qt.LeftButton:
                self.move(ev.globalPos() - self._drag_pos)
                ev.accept()
        top_bar.mousePressEvent = _press
        top_bar.mouseMoveEvent = _move

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_general_tab(), t('tab_general'))
        tabs.addTab(self.create_background_tab(), t('tab_background'))
        tabs.addTab(self.create_general_colors_tab(), t('tab_general_colors'))
        tabs.addTab(self.create_card_colors_tab(), t('tab_card_colors'))
        tabs.addTab(self.create_typography_tab(), t('tab_typography'))
        tabs.addTab(self.create_spacing_tab(), t('tab_spacing_layout'))
        root.addWidget(tabs)

        # Buttons
        button_container = QWidget()
        button_container.setStyleSheet("background:#1a1f2e;")
        buttons = QHBoxLayout(button_container)
        buttons.setContentsMargins(24,16,24,16)
        buttons.addStretch()
        reset = QPushButton(t('btn_reset'))
        reset.setObjectName('secondary')
        reset.clicked.connect(self.reset_colors)
        buttons.addWidget(reset)
        cancel = QPushButton(t('btn_cancel'))
        cancel.setObjectName('secondary')
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton(t('btn_save'))
        save.setObjectName('primary')
        save.clicked.connect(self.accept)
        buttons.addWidget(save)
        root.addWidget(button_container)

    def create_general_tab(self):
        """Pestaña General con idioma y auto-start"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(24,24,24,24)

        # Selector de idioma
        lang_container = QWidget()
        lang_layout = QHBoxLayout(lang_container)
        lang_layout.setContentsMargins(0,0,0,0)
        lang_layout.setSpacing(10)
        lang_layout.addWidget(QLabel(t('label_language')))
        self.lang_combo = QComboBox()
        self.lang_combo.setStyleSheet("""
            QComboBox { background:#252d3d; border:2px solid #2d3748; border-radius:8px; padding:8px; color:#e8eaed; min-width:150px; }
            QComboBox:hover { border-color:#667eea; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView { background:#252d3d; border:1px solid #2d3748; color:#e8eaed; selection-background-color:#667eea; }
        """)
        current_lang = I18n.get_language()
        self.lang_combo.addItems([t('language_es'), t('language_en')])
        self.lang_combo.setCurrentIndex(0 if current_lang == 'es' else 1)
        def on_lang_change(idx):
            new_lang = 'es' if idx == 0 else 'en'
            I18n.set_language(new_lang)
            # Emitir señal para que la ventana principal se recargue
            self.language_changed.emit(new_lang)
            # Intentar guardar en theme.json si el parent es GameLibrary
            try:
                parent = self.parent()
                if parent and hasattr(parent, 'theme_file'):
                    data = json.load(open(parent.theme_file, 'r', encoding='utf-8'))
                    data['language'] = new_lang
                    json.dump(data, open(parent.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
            except Exception as e:
                print(f'Error guardando idioma: {e}')
        self.lang_combo.currentIndexChanged.connect(on_lang_change)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        layout.addWidget(lang_container)

        # Toggle de inicio automático
        startup_container = QWidget()
        startup_layout = QHBoxLayout(startup_container)
        startup_layout.setContentsMargins(0,0,0,0)
        startup_layout.setSpacing(10)
        startup_checkbox = QCheckBox(t('label_auto_start'))
        # Estado actual desde theme.json
        try:
            parent = self.parent() if isinstance(self.parent(), GameLibrary) else None
            current = False
            if parent and parent.theme_file.exists():
                data = json.load(open(parent.theme_file, 'r', encoding='utf-8'))
                current = bool(data.get('startup_on_boot', False))
            startup_checkbox.setChecked(current)
        except Exception:
            pass
        def on_toggle(state):
            parent = self.parent() if isinstance(self.parent(), GameLibrary) else None
            if parent:
                want = state == Qt.Checked
                parent._set_startup_on_boot(want)
                try:
                    data = json.load(open(parent.theme_file, 'r', encoding='utf-8'))
                    data['startup_on_boot'] = want
                    data['startup_on_boot_decided'] = True
                    json.dump(data, open(parent.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                except Exception:
                    pass
        startup_checkbox.stateChanged.connect(on_toggle)
        startup_layout.addWidget(startup_checkbox)
        startup_layout.addStretch()
        layout.addWidget(startup_container)
        
        # Selector de prioridad de proceso
        priority_container = QWidget()
        priority_layout = QHBoxLayout(priority_container)
        priority_layout.setContentsMargins(0,0,0,0)
        priority_layout.setSpacing(10)
        priority_layout.addWidget(QLabel(t('label_process_priority')))
        self.priority_combo = QComboBox()
        self.priority_combo.setStyleSheet("""
            QComboBox { background:#252d3d; border:2px solid #2d3748; border-radius:8px; padding:8px; color:#e8eaed; min-width:150px; }
            QComboBox:hover { border-color:#667eea; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView { background:#252d3d; border:1px solid #2d3748; color:#e8eaed; selection-background-color:#667eea; }
        """)
        self.priority_combo.addItems([t('priority_high'), t('priority_normal'), t('priority_low')])
        # Cargar prioridad actual
        try:
            parent = self.parent() if isinstance(self.parent(), GameLibrary) else None
            current_priority = 'normal'
            if parent and parent.theme_file.exists():
                data = json.load(open(parent.theme_file, 'r', encoding='utf-8'))
                current_priority = data.get('process_priority', 'normal')
            priority_index = {'high': 0, 'normal': 1, 'low': 2}.get(current_priority, 1)
            self.priority_combo.setCurrentIndex(priority_index)
        except Exception:
            self.priority_combo.setCurrentIndex(1)
        def on_priority_change(idx):
            parent = self.parent() if isinstance(self.parent(), GameLibrary) else None
            if parent:
                priority_map = {0: 'high', 1: 'normal', 2: 'low'}
                new_priority = priority_map.get(idx, 'normal')
                parent._set_process_priority(new_priority)
                try:
                    data = json.load(open(parent.theme_file, 'r', encoding='utf-8'))
                    data['process_priority'] = new_priority
                    json.dump(data, open(parent.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                except Exception:
                    pass
        self.priority_combo.currentIndexChanged.connect(on_priority_change)
        priority_layout.addWidget(self.priority_combo)
        priority_layout.addStretch()
        layout.addWidget(priority_container)

        # Toggle de tracking de tiempo de juego
        playtime_container = QWidget()
        playtime_layout = QHBoxLayout(playtime_container)
        playtime_layout.setContentsMargins(0,0,0,0)
        playtime_layout.setSpacing(10)

        self.playtime_checkbox = QCheckBox(t('label_playtime_tracking'))
        try:
            parent = self.parent() if isinstance(self.parent(), GameLibrary) else None
            current = parent.playtime_tracking_enabled if parent else True
            self.playtime_checkbox.setChecked(current)
        except Exception:
            self.playtime_checkbox.setChecked(True)

        def on_playtime_toggle(state):
            parent = self.parent() if isinstance(self.parent(), GameLibrary) else None
            if parent:
                enabled = state == Qt.Checked
                parent.set_playtime_tracking(enabled)
                try:
                    data = json.load(open(parent.theme_file, 'r', encoding='utf-8'))
                    data['playtime_tracking_enabled'] = enabled
                    json.dump(data, open(parent.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                except Exception:
                    pass
        self.playtime_checkbox.stateChanged.connect(on_playtime_toggle)
        playtime_layout.addWidget(self.playtime_checkbox)

        hint = QLabel(t('hint_playtime_tracking'))
        hint.setStyleSheet('color:#9aa0a6;')
        playtime_layout.addWidget(hint)
        playtime_layout.addStretch()
        layout.addWidget(playtime_container)
        
        layout.addStretch()
        return widget

    def create_background_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(18)
        layout.setContentsMargins(24,24,24,24)

        # Background type selector
        type_container = QWidget()
        type_layout = QHBoxLayout(type_container)
        type_layout.setContentsMargins(0,0,0,0)
        type_layout.setSpacing(10)
        type_layout.addWidget(QLabel(t('label_bg_type')))
        self.bg_type_combo = QComboBox()
        self.bg_type_combo.setStyleSheet("""
            QComboBox { background:#252d3d; border:2px solid #2d3748; border-radius:8px; padding:8px; color:#e8eaed; min-width:150px; }
            QComboBox:hover { border-color:#667eea; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView { background:#252d3d; border:1px solid #2d3748; color:#e8eaed; selection-background-color:#667eea; }
        """)
        self.bg_type_combo.addItem(t('bg_type_static'), 'static')
        self.bg_type_combo.addItem(t('bg_type_animated'), 'animated')
        self.bg_type_combo.addItem(t('bg_type_video'), 'video')
        # Seleccionar tipo actual
        current_idx = self.bg_type_combo.findData(self._current_bg_type)
        if current_idx >= 0:
            self.bg_type_combo.setCurrentIndex(current_idx)
        else:
            self.bg_type_combo.setCurrentIndex(0)
        type_layout.addWidget(self.bg_type_combo)
        type_layout.addStretch()
        layout.addWidget(type_container)

        layout.addWidget(QLabel(t('label_bg_image')))
        hl_bg = QHBoxLayout()
        self.bg_input = QLineEdit()
        self.bg_input.setPlaceholderText(t('placeholder_bg_image'))
        self.bg_input.setText(self._current_bg)
        hl_bg.addWidget(self.bg_input)
        btn_pick = QPushButton('📁')
        btn_pick.setObjectName('secondary')
        btn_pick.setFixedWidth(50)
        btn_pick.clicked.connect(self.pick_background)
        hl_bg.addWidget(btn_pick)
        layout.addLayout(hl_bg)

        layout.addWidget(QLabel(t('label_opacity')))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(40)
        self.opacity_slider.setValue(int(self._current_opacity * 100))
        layout.addWidget(self.opacity_slider)

        self.preview_label = QLabel(t('label_opacity_current', value=self.opacity_slider.value()))
        self.preview_label.setStyleSheet('color:#9aa0a6;')
        layout.addWidget(self.preview_label)
        self.opacity_slider.valueChanged.connect(lambda v: self.preview_label.setText(t('label_opacity_current', value=v)))

        layout.addWidget(QLabel(t('label_bg_history')))
        self.history_container = QWidget()
        self.history_grid = QGridLayout(self.history_container)
        self.history_grid.setContentsMargins(0,0,0,0)
        self.history_grid.setSpacing(10)
        layout.addWidget(self.history_container)

        layout.addStretch()
        return widget

    def create_general_colors_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(24,24,24,24)

        # Preset selector
        preset_container = QWidget()
        preset_layout = QHBoxLayout(preset_container)
        preset_layout.setContentsMargins(0,0,0,0)
        preset_layout.addWidget(QLabel(t('label_presets')))
        
        from PyQt5.QtWidgets import QComboBox
        self.preset_combo = QComboBox()
        self.preset_combo.setStyleSheet("""
            QComboBox { background:#252d3d; border:2px solid #2d3748; border-radius:8px; padding:8px; color:#e8eaed; min-width:150px; }
            QComboBox:hover { border-color:#667eea; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView { background:#252d3d; border:1px solid #2d3748; color:#e8eaed; selection-background-color:#667eea; }
        """)
        self.preset_combo.addItems([t('preset_base'), t('preset_light'), t('preset_dark'), t('preset_pink')])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        layout.addWidget(preset_container)

        # Separator
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background:#2d3748; margin:8px 0;")
        layout.addWidget(separator)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(16)

        colors = [
            ('bg_gradient_start', t('label_bg_gradient_start')),
            ('bg_gradient_end', t('label_bg_gradient_end')),
            ('top_bar_bg', t('label_top_bar_bg')),
            ('accent_start', t('label_accent_start')),
            ('accent_end', t('label_accent_end')),
            ('text_primary', t('label_text_primary')),
            ('text_secondary', t('label_text_secondary')),
            ('input_bg', t('label_input_bg')),
            ('input_border', t('label_input_border'))
        ]

        for i, (key, label) in enumerate(colors):
            grid.addWidget(QLabel(label), i, 0)
            btn = self.create_color_button(key)
            grid.addWidget(btn, i, 1)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    def create_card_colors_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(24,24,24,24)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(16)

        colors = [
            ('card_bg', t('label_card_bg')),
            ('card_border', t('label_card_border')),
            ('card_hover_border', t('label_card_hover_border')),
            ('card_hover_bg', t('label_card_hover_bg'))
        ]

        for i, (key, label) in enumerate(colors):
            grid.addWidget(QLabel(label), i, 0)
            btn = self.create_color_button(key)
            grid.addWidget(btn, i, 1)

        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    def create_typography_tab(self):
        """Tab para tipografía: font family, sizes, weights"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Font Family
        layout.addWidget(QLabel('Font Family'))
        font_combo = QComboBox()
        font_combo.setStyleSheet("""
            QComboBox { background:#252d3d; border:2px solid #2d3748; border-radius:8px; padding:8px; color:#e8eaed; min-width:150px; }
            QComboBox:hover { border-color:#667eea; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView { background:#252d3d; border:1px solid #2d3748; color:#e8eaed; selection-background-color:#667eea; }
        """)
        fonts = ['Segoe UI', 'Arial', 'Calibri', 'Tahoma', 'Courier New', 'Georgia']
        font_combo.addItems(fonts)
        current_font = self._current_theme.get('font_family', 'Segoe UI')
        idx = font_combo.findText(current_font)
        if idx >= 0:
            font_combo.setCurrentIndex(idx)
        def on_font_change(idx):
            self._current_theme['font_family'] = font_combo.currentText()
        font_combo.currentIndexChanged.connect(on_font_change)
        layout.addWidget(font_combo)

        # Title Size
        layout.addWidget(QLabel('Title Size (14-24px)'))
        title_slider = QSlider(Qt.Horizontal)
        title_slider.setMinimum(14)
        title_slider.setMaximum(24)
        title_slider.setValue(self._current_theme.get('title_size', 18))
        title_label = QLabel(f"{title_slider.value()}px")
        title_label.setStyleSheet('color:#9aa0a6;')
        def on_title_change(v):
            self._current_theme['title_size'] = v
            title_label.setText(f"{v}px")
        title_slider.valueChanged.connect(on_title_change)
        layout.addWidget(title_slider)
        layout.addWidget(title_label)

        # Card Title Size
        layout.addWidget(QLabel('Card Title Size (12-20px)'))
        card_title_slider = QSlider(Qt.Horizontal)
        card_title_slider.setMinimum(12)
        card_title_slider.setMaximum(20)
        card_title_slider.setValue(self._current_theme.get('card_title_size', 16))
        card_title_label = QLabel(f"{card_title_slider.value()}px")
        card_title_label.setStyleSheet('color:#9aa0a6;')
        def on_card_title_change(v):
            self._current_theme['card_title_size'] = v
            card_title_label.setText(f"{v}px")
        card_title_slider.valueChanged.connect(on_card_title_change)
        layout.addWidget(card_title_slider)
        layout.addWidget(card_title_label)

        # Secondary Size
        layout.addWidget(QLabel('Secondary Text Size (10-16px)'))
        secondary_slider = QSlider(Qt.Horizontal)
        secondary_slider.setMinimum(10)
        secondary_slider.setMaximum(16)
        secondary_slider.setValue(self._current_theme.get('secondary_size', 13))
        secondary_label = QLabel(f"{secondary_slider.value()}px")
        secondary_label.setStyleSheet('color:#9aa0a6;')
        def on_secondary_change(v):
            self._current_theme['secondary_size'] = v
            secondary_label.setText(f"{v}px")
        secondary_slider.valueChanged.connect(on_secondary_change)
        layout.addWidget(secondary_slider)
        layout.addWidget(secondary_label)

        layout.addStretch()
        return widget

    def create_spacing_tab(self):
        """Tab para espaciado: card radius, padding, border width"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Card Radius
        layout.addWidget(QLabel('Card Border Radius (0-20px)'))
        radius_slider = QSlider(Qt.Horizontal)
        radius_slider.setMinimum(0)
        radius_slider.setMaximum(20)
        radius_slider.setValue(self._current_theme.get('card_radius', 12))
        radius_label = QLabel(f"{radius_slider.value()}px")
        radius_label.setStyleSheet('color:#9aa0a6;')
        def on_radius_change(v):
            self._current_theme['card_radius'] = v
            radius_label.setText(f"{v}px")
        radius_slider.valueChanged.connect(on_radius_change)
        layout.addWidget(radius_slider)
        layout.addWidget(radius_label)

        # Card Padding
        layout.addWidget(QLabel('Card Padding (4-20px)'))
        padding_slider = QSlider(Qt.Horizontal)
        padding_slider.setMinimum(4)
        padding_slider.setMaximum(20)
        padding_slider.setValue(self._current_theme.get('card_padding', 10))
        padding_label = QLabel(f"{padding_slider.value()}px")
        padding_label.setStyleSheet('color:#9aa0a6;')
        def on_padding_change(v):
            self._current_theme['card_padding'] = v
            padding_label.setText(f"{v}px")
        padding_slider.valueChanged.connect(on_padding_change)
        layout.addWidget(padding_slider)
        layout.addWidget(padding_label)

        # Button Radius
        layout.addWidget(QLabel('Button Border Radius (4-12px)'))
        btn_radius_slider = QSlider(Qt.Horizontal)
        btn_radius_slider.setMinimum(4)
        btn_radius_slider.setMaximum(12)
        btn_radius_slider.setValue(self._current_theme.get('button_radius', 8))
        btn_radius_label = QLabel(f"{btn_radius_slider.value()}px")
        btn_radius_label.setStyleSheet('color:#9aa0a6;')
        def on_btn_radius_change(v):
            self._current_theme['button_radius'] = v
            btn_radius_label.setText(f"{v}px")
        btn_radius_slider.valueChanged.connect(on_btn_radius_change)
        layout.addWidget(btn_radius_slider)
        layout.addWidget(btn_radius_label)

        # Border Width
        layout.addWidget(QLabel('Border Width (1-3px)'))
        border_slider = QSlider(Qt.Horizontal)
        border_slider.setMinimum(1)
        border_slider.setMaximum(3)
        border_slider.setValue(self._current_theme.get('border_width', 2))
        border_label = QLabel(f"{border_slider.value()}px")
        border_label.setStyleSheet('color:#9aa0a6;')
        def on_border_change(v):
            self._current_theme['border_width'] = v
            border_label.setText(f"{v}px")
        border_slider.valueChanged.connect(on_border_change)
        layout.addWidget(border_slider)
        layout.addWidget(border_label)

        layout.addStretch()
        return widget

    def create_color_button(self, key):
        from PyQt5.QtWidgets import QColorDialog
        color = self._color_scheme.get(key, '#000000')
        btn = QPushButton(color)
        btn.setObjectName('colorBtn')
        btn.setStyleSheet(f"QPushButton#colorBtn {{ background:{color}; color:white; border:2px solid #2d3748; }}")
        def pick():
            c = QColorDialog.getColor(QColor(color), self, f"Seleccionar {key}")
            if c.isValid():
                hex_color = c.name()
                self._color_scheme[key] = hex_color
                self._current_theme[key] = hex_color
                btn.setText(hex_color)
                btn.setStyleSheet(f"QPushButton#colorBtn {{ background:{hex_color}; color:white; border:2px solid #667eea; }}")
        btn.clicked.connect(pick)
        self._color_buttons[key] = btn
        return btn

    def reset_colors(self):
        self._color_scheme = self.default_colors()
        for key, btn in self._color_buttons.items():
            color = self._color_scheme[key]
            btn.setText(color)
            btn.setStyleSheet(f"QPushButton#colorBtn {{ background:{color}; color:white; border:2px solid #2d3748; }}")

    def pick_background(self):
        file_filter = 'All Supported (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.webm *.mkv *.mov);;Static Images (*.png *.jpg *.jpeg *.bmp);;Animated GIF (*.gif);;Video (*.mp4 *.webm *.mkv *.mov)'
        file_path, selected_filter = QFileDialog.getOpenFileName(self, t('label_bg_image'), '', file_filter)
        if file_path:
            self.bg_input.setText(file_path)
            # Detectar tipo de archivo
            lower = file_path.lower()
            if lower.endswith('.gif'):
                idx = self.bg_type_combo.findData('animated')
                self.bg_type_combo.setCurrentIndex(idx if idx >= 0 else 0)
            elif lower.endswith(('.mp4', '.webm', '.mkv', '.mov')):
                idx = self.bg_type_combo.findData('video')
                self.bg_type_combo.setCurrentIndex(idx if idx >= 0 else 0)
            else:
                idx = self.bg_type_combo.findData('static')
                self.bg_type_combo.setCurrentIndex(idx if idx >= 0 else 0)

    def get_data(self):
        return {
            'background_image': self.bg_input.text().strip(),
            'background_type': self.bg_type_combo.currentData(),
            'background_opacity': round(self.opacity_slider.value()/100.0, 3),
            'color_scheme': self._color_scheme,
            'theme': self._current_theme  # Retornar tema completo con tipografía y espaciado
        }

    def apply_history(self, history_list):
        try:
            self._history = [p for p in (history_list or []) if isinstance(p, str) and os.path.exists(p)]
        except Exception:
            self._history = []
        while self.history_grid.count():
            item = self.history_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for idx, path in enumerate(self._history[:8]):
            thumb = QPushButton()
            thumb.setObjectName('secondary')
            thumb.setCheckable(False)
            thumb.setFixedSize(150, 100)
            pm = QPixmap(path)
            if not pm.isNull():
                scaled = pm.scaled(150, 100, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                icon = QIcon(scaled)
                thumb.setIcon(icon)
                thumb.setIconSize(QSize(150,100))
            thumb.setToolTip(path)
            def make_handler(p=path):
                def handler():
                    self.bg_input.setText(p)
                    lower = p.lower()
                    if lower.endswith('.gif'):
                        idx = self.bg_type_combo.findData('animated')
                    elif lower.endswith(('.mp4', '.webm', '.mkv', '.mov')):
                        idx = self.bg_type_combo.findData('video')
                    else:
                        idx = self.bg_type_combo.findData('static')
                    if idx is not None and idx >= 0:
                        self.bg_type_combo.setCurrentIndex(idx)
                return handler
            thumb.clicked.connect(make_handler())
            r, c = divmod(idx, 4)
            self.history_grid.addWidget(thumb, r, c)


class GameLibrary(QMainWindow):
    """Ventana principal de la biblioteca de juegos"""
    
    def __init__(self):
        super().__init__()
        self.games = []
        self.data_file = Path.home() / '.game_library' / 'games.json'
        self.data_file.parent.mkdir(exist_ok=True)
        self.theme_file = Path.home() / '.game_library' / 'theme.json'
        self.custom_folders = []
        self.active_folder = None  # None -> todos
        self.folder_buttons = {}
        self.folder_icons = {}  # folder_name -> icon_path
        self.sidebar_anim = None
        self.filter_favorites = False
        self.filter_platform = None  # None/Steam/Epic/Manual
        self.sort_mode = 'name_asc'  # default sort
        self._suppress_render_animation = False

        # Seguimiento de tiempo de juego
        self.playtime_tracking_enabled = True
        self._play_session = None  # {'game_id': str, 'start_time': datetime, 'process': Popen}
        self.playtime_timer = QTimer(self)
        self.playtime_timer.setInterval(1000)
        self.playtime_timer.timeout.connect(self._tick_playtime)
        
        # Cargar idioma ANTES de crear la UI
        self._load_language()
        
        # Cargar y aplicar prioridad de proceso
        self._load_process_priority()

        # Cargar preferencia de seguimiento de tiempo
        self._load_playtime_setting()
        
        self.bg_pixmap = None
        self.bg_movie = None  # QMovie para GIF animados
        self.bg_video_cap = None  # cv2.VideoCapture para videos
        self.bg_video_timer = None  # Timer para refrescar frames de video
        self.bg_opacity = 0.15
        self.bg_history = []
        self.bg_type = 'static'  # static, animated, video
        self.color_scheme = {}
        self._bg_paint_update_timer = None  # Timer para actualizar paintEvent durante animación
        # Arrastre simple
        self._drag_pos = None
        # Animación de minimizar/restaurar
        self._minimize_animation = None
        self._restore_animation = None
        self._saved_geometry = None
        
        self._first_run_setup()
        self.load_games()
        # Limpieza defensiva de duplicados por steam_appid
        if hasattr(self, '_dedupe_games_by_appid') and self._dedupe_games_by_appid():
            self.save_games()
        self.load_theme()
        
        # Establecer icono de la aplicación
        # Buscar icono en la ubicación correcta (PyInstaller o desarrollo)
        if getattr(sys, 'frozen', False):
            # Ejecutando como .exe empaquetado
            icon_path = Path(sys._MEIPASS) / 'icon.ico'
        else:
            # Ejecutando desde código fuente
            icon_path = Path(__file__).parent / 'icon.ico'
        
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            # Configurar icono en la barra de tareas de Windows
            try:
                myappid = 'com.eden.ludexhub.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass
        
        try:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        except Exception:
            pass
        self.setup_ui()
        self.apply_color_scheme_fixed()
        self.render_games()
        self.enable_shadow()

    def enable_shadow(self):
        try:
            from PyQt5.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(40)
            shadow.setXOffset(0)
            shadow.setYOffset(10)
            shadow.setColor(QColor(0,0,0,160))
            self.centralWidget().setGraphicsEffect(shadow)
        except Exception as e:
            print("Shadow effect no disponible", e)

    def apply_color_scheme_fixed(self):
        """Aplicar el esquema de colores, tipografía y espaciado personalizado a toda la interfaz"""
        if not self.color_scheme:
            return
        
        c = self.color_scheme
        bg_start = c.get('bg_gradient_start', '#0f1419')
        bg_end = c.get('bg_gradient_end', '#1a1f2e')
        top_bar_bg = c.get('top_bar_bg', '#121822')
        card_bg = c.get('card_bg', '#1a1f2e')
        card_hover_bg = c.get('card_hover_bg', '#252d3d')
        card_border = c.get('card_border', 'transparent')
        card_hover_border = c.get('card_hover_border', '#667eea')
        accent_start = c.get('accent_start', '#667eea')
        accent_end = c.get('accent_end', '#764ba2')
        text_primary = c.get('text_primary', '#e8eaed')
        text_secondary = c.get('text_secondary', '#9aa0a6')
        input_bg = c.get('input_bg', '#1a1f2e')
        input_border = c.get('input_border', '#2d3748')
        
        # Extraer tipografía del color_scheme (que ahora incluye toda la información de tema)
        font_family = c.get('font_family', 'Segoe UI')
        title_size = c.get('title_size', 20)
        card_title_size = c.get('card_title_size', 15)
        secondary_size = c.get('secondary_size', 12)
        
        # Extraer espaciado
        card_radius = c.get('card_radius', 12)
        card_padding = c.get('card_padding', 12)
        button_radius = c.get('button_radius', 8)
        border_width = c.get('border_width', 2)
        
        style_template = """
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg1}, stop:1 {bg2});
                font-family: {font_family};
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {bg1};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {cbg};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {chbg};
            }}
        """
        
        style = style_template.format(
            bg1=bg_start,
            bg2=bg_end,
            cbg=card_bg,
            chbg=card_hover_bg,
            font_family=font_family
        )
        self.setStyleSheet(style)
        
        # Aplicar colores a la barra superior
        if hasattr(self, 'top_bar'):
            self.top_bar.setStyleSheet(f"QWidget {{background-color:{top_bar_bg};font-family:{font_family};}}")
        
        # Aplicar tipografía y colores al título
        if hasattr(self, 'title_label'):
            title_font = QFont(font_family, title_size, QFont.Bold)
            self.title_label.setFont(title_font)
            self.title_label.setStyleSheet(f"color:{text_primary}; letter-spacing:.5px;")
        
        # Aplicar tipografía a inputs
        if hasattr(self, 'search_input'):
            search_font = QFont(font_family, secondary_size)
            self.search_input.setFont(search_font)
            self.search_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {input_bg};
                    border: 1px solid {input_border};
                    border-radius: {button_radius}px;
                    padding: 10px 15px;
                    color: {text_primary};
                    min-width: 250px;
                    max-width: 400px;
                }}
                QLineEdit:focus {{
                    border: 1px solid {accent_start};
                    background-color: {card_hover_bg};
                }}
            """)
        
        if hasattr(self, 'view_combo'):
            combo_font = QFont(font_family, secondary_size)
            self.view_combo.setFont(combo_font)
            self.view_combo.setStyleSheet(f"""
                QComboBox {{
                    background-color: {input_bg};
                    border: 1px solid {input_border};
                    border-radius: {button_radius}px;
                    padding: 10px 15px;
                    color: {text_primary};
                    min-width: 120px;
                }}
                QComboBox:hover {{
                    border: 1px solid {accent_start};
                    background-color: {card_hover_bg};
                }}
                QComboBox::drop-down {{
                    border: none;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {input_bg};
                    border: 1px solid {input_border};
                    selection-background-color: {card_hover_bg};
                    color: {text_primary};
                }}
            """)
        
        if hasattr(self, 'add_btn'):
            btn_font = QFont(font_family, secondary_size, QFont.Bold)
            self.add_btn.setFont(btn_font)
            self.add_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {accent_start}, stop:1 {accent_end});
                    color: white;
                    border: none;
                    border-radius: {button_radius}px;
                    padding: 12px 24px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {accent_start}, stop:1 {accent_end});
                    opacity: 0.9;
                }}
            """)
        
        if hasattr(self, 'customize_btn'):
            btn_font = QFont(font_family, secondary_size, QFont.Bold)
            self.customize_btn.setFont(btn_font)
            self.customize_btn.setStyleSheet(f"""
                QPushButton {{
                    background:{input_bg}; color:{text_primary}; border:1px solid {input_border}; border-radius:{button_radius}px; padding:10px 20px;
                }}
                QPushButton:hover {{background:{card_hover_bg}; border-color:{accent_start};}}
            """)
        
        # Actualizar estilos de GameCard con el nuevo espaciado
        GameCard._custom_colors = {
            'card_bg': card_bg,
            'card_border': card_border,
            'card_hover_border': card_hover_border,
            'card_hover_bg': card_hover_bg,
            'text_primary': text_primary,
            'text_secondary': text_secondary,
            'accent_start': accent_start,
            'accent_end': accent_end,
            'card_radius': card_radius,
            'card_padding': card_padding,
            'button_radius': button_radius,
            'border_width': border_width,
            'font_family': font_family,
            'title_size': title_size,
            'card_title_size': card_title_size,
            'secondary_size': secondary_size
        }
        
        # Recargar las tarjetas para aplicar nuevos estilos de espaciado
        if hasattr(self, 'render_games'):
            self.render_games()

    def load_theme(self):
        if self.theme_file.exists():
            try:
                data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
                bg_path = data.get('background_image')
                self.bg_type = data.get('background_type', 'static')  # static, animated, video
                self.bg_opacity = float(data.get('background_opacity', self.bg_opacity))
                self.bg_history = list(data.get('background_history', []) or [])
                
                # Cargar tema completo (incluye colors, typography, spacing)
                theme_data = data.get('theme')
                if theme_data:
                    # Copiar TODO el objeto tema (colores, tipografía, espaciado, gradientes)
                    self.color_scheme = dict(theme_data)
                else:
                    # Fallback a color_scheme para compatibilidad hacia atrás
                    self.color_scheme = data.get('color_scheme', {})
                
                self.playtime_tracking_enabled = bool(data.get('playtime_tracking_enabled', self.playtime_tracking_enabled))
                self.custom_folders = list(data.get('custom_folders', []) or [])
                self.folder_icons = dict(data.get('folder_icons', {}) or {})
                self.active_folder = data.get('last_folder') or None
                self.filter_platform = data.get('filter_platform') or None
                self.filter_favorites = bool(data.get('filter_favorites', False))
                self.sort_mode = data.get('sort_mode') or 'name_asc'
                
                if bg_path and os.path.exists(bg_path):
                    if self.bg_type == 'animated' and bg_path.lower().endswith('.gif'):
                        # Cargar GIF como QMovie
                        self._load_animated_background(bg_path)
                    elif self.bg_type == 'video':
                        # Cargar video como fondo
                        self._load_video_background(bg_path)
                    else:
                        # Cargar estático
                        pm = QPixmap(bg_path)
                        if not pm.isNull():
                            # Detener recursos previos (gif/video)
                            if self.bg_movie:
                                self.bg_movie.stop()
                                self.bg_movie = None
                            self._stop_video_background()
                            if self._bg_paint_update_timer and self._bg_paint_update_timer.isActive():
                                self._bg_paint_update_timer.stop()
                            self.bg_pixmap = pm
            except Exception as e:
                print('Error cargando theme:', e)

    def _load_animated_background(self, gif_path):
        """Carga un GIF animado como fondo"""
        try:
            # Detener video si estaba activo
            self._stop_video_background()
            if self.bg_movie:
                self.bg_movie.stop()
            
            self.bg_movie = QMovie(gif_path)
            self.bg_movie.setCacheMode(QMovie.CacheAll)
            
            # Conectar señal para redibujar cuando cambia el frame
            self.bg_movie.frameChanged.connect(self.update)
            
            # Iniciar reproducción
            self.bg_movie.start()
            
            # Limpiar pixmap estático
            self.bg_pixmap = None
            
            # Crear timer para actualizar cada frame (aprox 30fps)
            if not self._bg_paint_update_timer:
                self._bg_paint_update_timer = QTimer(self)
                self._bg_paint_update_timer.timeout.connect(self.update)
                self._bg_paint_update_timer.setInterval(33)  # ~30fps
            
            if not self._bg_paint_update_timer.isActive():
                self._bg_paint_update_timer.start()
                
        except Exception as e:
            print(f'Error cargando GIF animado: {e}')

    def _stop_video_background(self):
        """Detiene y libera recursos de fondo de video"""
        try:
            if self.bg_video_timer and self.bg_video_timer.isActive():
                self.bg_video_timer.stop()
        except Exception:
            pass
        self.bg_video_timer = None
        try:
            if self.bg_video_cap:
                self.bg_video_cap.release()
        except Exception:
            pass
        self.bg_video_cap = None

    def _load_video_background(self, video_path):
        """Carga un video como fondo (sin audio) usando OpenCV"""
        try:
            # Detener GIF/animaciones previas
            if self.bg_movie:
                self.bg_movie.stop()
                self.bg_movie = None
            if self._bg_paint_update_timer and self._bg_paint_update_timer.isActive():
                self._bg_paint_update_timer.stop()

            # Detener video previo
            self._stop_video_background()

            try:
                import cv2
            except ImportError:
                print('OpenCV no está instalado; fondo de video no disponible')
                return

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f'No se pudo abrir el video: {video_path}')
                return

            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            if fps <= 1 or fps > 120:
                fps = 30
            interval = max(15, int(1000 / fps))

            self.bg_video_cap = cap
            if not self.bg_video_timer:
                self.bg_video_timer = QTimer(self)
                self.bg_video_timer.timeout.connect(self._update_video_frame)
            self.bg_video_timer.setInterval(interval)
            self.bg_video_timer.start()

            # Limpiar pixmap inicial; se actualizará en el siguiente frame
            self.bg_pixmap = None
            self._update_video_frame()
        except Exception as e:
            print(f'Error cargando video: {e}')

    def _update_video_frame(self):
        """Lee el siguiente frame del video y actualiza el fondo"""
        if not self.bg_video_cap:
            if self.bg_video_timer:
                self.bg_video_timer.stop()
            return
        try:
            import cv2
        except ImportError:
            if self.bg_video_timer:
                self.bg_video_timer.stop()
            return

        ret, frame = self.bg_video_cap.read()
        if not ret:
            # Reiniciar al inicio
            self.bg_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.bg_video_cap.read()
            if not ret:
                if self.bg_video_timer:
                    self.bg_video_timer.stop()
                return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        bytes_per_line = 3 * w
        img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self.bg_pixmap = QPixmap.fromImage(img)
        self.update()

    def save_theme(self, background_image, background_opacity, color_scheme=None, background_type='static', theme=None):
        # Actualizar historial (máx 8, sin duplicados, vacío si no hay imagen)
        new_hist = list(self.bg_history or [])
        if background_image:
            # eliminar si ya existe y poner al frente
            new_hist = [p for p in new_hist if p != background_image]
            new_hist.insert(0, background_image)
            new_hist = new_hist[:8]
        else:
            # no añadir entradas vacías
            pass
        
        # Cargar datos existentes para preservar language y startup_on_boot
        existing_data = {}
        try:
            if self.theme_file.exists():
                existing_data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
        except Exception:
            pass
        
        # Actualizar solo los campos que queremos cambiar
        payload = existing_data.copy()
        payload.update({
            'background_image': background_image if background_image else '',
            'background_type': background_type,
            'background_opacity': background_opacity,
            'background_history': new_hist,
            'color_scheme': color_scheme or {},
            'theme': theme or {},  # Guardar tema completo
            'custom_folders': self.custom_folders,
            'folder_icons': self.folder_icons,
            'last_folder': self.active_folder,
            'filter_platform': self.filter_platform,
            'filter_favorites': self.filter_favorites,
            'sort_mode': self.sort_mode
        })
        if 'playtime_tracking_enabled' not in payload:
            payload['playtime_tracking_enabled'] = self.playtime_tracking_enabled
        
        try:
            json.dump(payload, open(self.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        except Exception as e:
            print('Error guardando theme', e)
        self.load_theme()
        self.apply_color_scheme_fixed()
        self.render_games()
        self.update()

    def _load_language(self):
        """Carga el idioma desde theme.json antes de crear la UI"""
        try:
            if self.theme_file.exists():
                data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
                lang = data.get('language', 'en')
                I18n.set_language(lang)
            else:
                # Idioma por defecto: inglés
                I18n.set_language('en')
        except Exception as e:
            print(f'Error cargando idioma: {e}')
            I18n.set_language('en')
    
    def _load_process_priority(self):
        """Cargar y aplicar la prioridad de proceso guardada"""
        try:
            if self.theme_file.exists():
                data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
                priority = data.get('process_priority', 'normal')
                self._set_process_priority(priority)
            else:
                self._set_process_priority('normal')
        except Exception as e:
            print(f'Error cargando prioridad: {e}')
            self._set_process_priority('normal')

    def _load_playtime_setting(self):
        """Cargar preferencia de tracking de tiempo desde theme.json"""
        try:
            if self.theme_file.exists():
                data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
                self.playtime_tracking_enabled = bool(data.get('playtime_tracking_enabled', True))
            else:
                self.playtime_tracking_enabled = True
        except Exception as e:
            print(f'Error cargando preferencia de playtime: {e}')
            self.playtime_tracking_enabled = True
    
    def _first_run_setup(self):
        """Prepara entorno de primera ejecución: crea carpetas, archivos base y verifica dependencias externas."""
        try:
            base = self.data_file.parent
            base.mkdir(parents=True, exist_ok=True)
            # Crear games.json si no existe
            if not self.data_file.exists():
                json.dump([], open(self.data_file, 'w', encoding='utf-8'))
            # Crear theme.json por defecto si no existe
            if not self.theme_file.exists():
                dialog = ColorPickerDialog(None)
                json.dump({
                    'background_image': '',
                    'background_type': 'static',
                    'background_opacity': 0.15,
                    'background_history': [],
                    'color_scheme': dialog.default_colors(),
                    'theme': dialog.default_theme(),  # Guardar tema completo
                    'startup_on_boot': False,
                    'startup_on_boot_decided': False,
                    'language': 'en',
                    'playtime_tracking_enabled': True,
                    'process_priority': 'normal'
                }, open(self.theme_file, 'w', encoding='utf-8'))
            # Crear carpetas de caché
            (Path.home() / '.game_library' / 'icons').mkdir(parents=True, exist_ok=True)
            (Path.home() / '.game_library' / 'steam_images').mkdir(parents=True, exist_ok=True)
            (Path.home() / '.game_library' / 'epic_images').mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print('First-run setup error:', e)

        # Verificar presencia de Steam/Epic y mostrar guía breve
        try:
            steam = SteamScanner()
            epic = EpicScanner()
            missing = []
            if not steam.steam_path:
                missing.append('Steam')
            if not epic.manifest_folder:
                missing.append('Epic Games Launcher')
            if missing:
                QMessageBox.information(
                    self,
                    'Sugerencia de configuración',
                    'Faltan componentes: ' + ', '.join(missing) + '\n\n'
                    'Instala las plataformas para importar automáticamente tus juegos.'
                )
        except Exception:
            pass

        # Preguntar sobre inicio automático en la primera ejecución
        try:
            data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
            if not data.get('startup_on_boot_decided', False):
                reply = QMessageBox.question(
                    self,
                    t('msg_startup_title'),
                    t('msg_startup_enable'),
                    QMessageBox.Yes | QMessageBox.No
                )
                want = reply == QMessageBox.Yes
                self._set_startup_on_boot(want)
                data['startup_on_boot'] = want
                data['startup_on_boot_decided'] = True
                json.dump(data, open(self.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        except Exception as e:
            print('Startup prompt error:', e)

    def _startup_shortcut_path(self) -> Path:
        appdata = os.environ.get('APPDATA', str(Path.home() / 'AppData' / 'Roaming'))
        return Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup' / 'GameLibrary.lnk'

    def _set_startup_on_boot(self, enable: bool):
        """Crea o elimina el acceso directo en la carpeta de inicio."""
        try:
            # Determinar ejecutable objetivo
            if getattr(sys, 'frozen', False):
                target_exe = sys.executable
            else:
                candidate = Path(__file__).parent / 'release' / '1.0' / 'GameLibrary.exe'
                target_exe = str(candidate) if candidate.exists() else sys.executable
            shortcut_path = self._startup_shortcut_path()
            if enable:
                try:
                    import win32com.client
                    shell = win32com.client.Dispatch('WScript.Shell')
                    sh = shell.CreateShortcut(str(shortcut_path))
                    sh.TargetPath = target_exe
                    sh.WorkingDirectory = str(Path(target_exe).parent)
                    sh.IconLocation = target_exe
                    sh.Save()
                except Exception as e:
                    print('Fallo creando acceso directo de inicio:', e)
            else:
                try:
                    if shortcut_path.exists():
                        shortcut_path.unlink()
                except Exception:
                    pass
        except Exception as e:
            print('Startup setup error:', e)
    
    def _set_process_priority(self, priority: str):
        """Establece la prioridad del proceso actual."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            
            priority_map = {
                'high': psutil.HIGH_PRIORITY_CLASS,
                'normal': psutil.NORMAL_PRIORITY_CLASS,
                'low': psutil.IDLE_PRIORITY_CLASS
            }
            
            priority_class = priority_map.get(priority, psutil.NORMAL_PRIORITY_CLASS)
            process.nice(priority_class)
            print(f'Process priority set to: {priority}')
        except ImportError:
            # Si psutil no está disponible, usar ctypes en Windows
            try:
                import ctypes
                priorities = {
                    'high': 0x00000080,  # HIGH_PRIORITY_CLASS
                    'normal': 0x00000020,  # NORMAL_PRIORITY_CLASS
                    'low': 0x00000040  # IDLE_PRIORITY_CLASS
                }
                priority_flag = priorities.get(priority, 0x00000020)
                handle = ctypes.windll.kernel32.GetCurrentProcess()
                ctypes.windll.kernel32.SetPriorityClass(handle, priority_flag)
                print(f'Process priority set to: {priority}')
            except Exception as e:
                print(f'Error setting process priority: {e}')
        except Exception as e:
            print(f'Error setting process priority: {e}')
    
    def create_steam_icon(self):
        """Crea un icono de Steam usando QPixmap"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo azul de Steam
        painter.setBrush(QBrush(QColor("#1b2838")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 24, 24, 4, 4)
        
        # Dibujar "S" estilizada de Steam en blanco
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "S")
        
        painter.end()
        return QIcon(pixmap)
    
    def create_epic_icon(self):
        """Crea un icono de Epic Games usando QPixmap"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo negro de Epic
        painter.setBrush(QBrush(QColor("#0d0d0d")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 24, 24, 4, 4)
        
        # Dibujar "E" de Epic en blanco
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "E")
        
        painter.end()
        return QIcon(pixmap)
        
    def setup_ui(self):
        self.setWindowTitle(t('app_title'))
        # Volver a tamaño fijo para evitar recortes entre pantallas
        self.setFixedSize(1400, 700)
        try:
            primary = QApplication.primaryScreen()
            avail = primary.availableGeometry() if primary else None
            if avail:
                x = avail.x() + (avail.width() - self.width()) // 2
                y = avail.y() + (avail.height() - self.height()) // 2
                self.move(x, y)
        except Exception:
            pass
        
        # Estilo general
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f1419, stop:1 #1a1f2e);
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #0f1419;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #252d3d;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2d3748;
            }
        """)
        
        # Widget central
        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barra superior personalizada
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(56)
        self.top_bar.setStyleSheet("""
            QWidget {background-color:#121822;}
        """)
        tb_layout = QHBoxLayout(self.top_bar)
        tb_layout.setContentsMargins(16, 8, 8, 8)
        tb_layout.setSpacing(12)

        self.title_label = QLabel(t('app_title'))
        self.title_label.setStyleSheet("""
            color:#e8eaed; font-size:20px; font-weight:700; letter-spacing:.5px;
        """)
        tb_layout.addWidget(self.title_label)
        
        # Barra de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('btn_search_placeholder'))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a1f2e;
                border: 1px solid #2d3748;
                border-radius: 8px;
                padding: 10px 15px;
                color: #e8eaed;
                font-size: 14px;
                min-width: 250px;
                max-width: 400px;
            }
            QLineEdit:focus {
                border: 1px solid #667eea;
                background-color: #252d3d;
            }
        """)
        self.search_input.textChanged.connect(self.render_games)
        tb_layout.addWidget(self.search_input)
        
        tb_layout.addStretch()

        # Botones de vista y agregar dentro de una sub-barra
        header_controls = QHBoxLayout()
        header_controls.setSpacing(10)
        
        # Selector de vista
        self.view_combo = QComboBox()
        self.view_combo.addItems([t('view_grid'), t('view_list')])
        self.view_combo.setStyleSheet("""
            QComboBox {
                background-color: #1a1f2e;
                border: 1px solid #2d3748;
                border-radius: 8px;
                padding: 10px 15px;
                color: #e8eaed;
                font-size: 14px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #667eea;
                background-color: #252d3d;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1f2e;
                border: 1px solid #2d3748;
                selection-background-color: #252d3d;
                color: #e8eaed;
            }
        """)
        self.view_combo.currentIndexChanged.connect(self.render_games)
        header_controls.addWidget(self.view_combo)
        
        # Botón de filtros desplegable junto a la búsqueda
        self.filter_btn = QToolButton()
        self.filter_btn.setText('▼')
        self.filter_btn.setPopupMode(QToolButton.InstantPopup)
        self.filter_btn.setStyleSheet("""
            QToolButton { background-color:#1a1f2e; border:1px solid #2d3748; border-radius:8px; padding:8px 12px; color:#e8eaed; font-size:14px; }
            QToolButton:hover { border-color:#667eea; background:#252d3d; }
        """)
        self._build_filter_menu()
        tb_layout.insertWidget(tb_layout.indexOf(self.search_input)+1, self.filter_btn)
        
        # Botón agregar
        self.add_btn = QPushButton(t('btn_add_game'))
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7c8ef5, stop:1 #8a5cb8);
            }
        """)
        self.add_btn.clicked.connect(self.add_game)
        header_controls.addWidget(self.add_btn)
        
        # Botón de importar con menú desplegable
        self.import_btn = QPushButton("📥 " + t('btn_import_games'))
        self.import_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #374151, stop:1 #252d3d);
            }
            QPushButton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 16px;
                padding-right: 4px;
            }
        """)
        
        # Crear menú de importación
        import_menu = QMenu(self)
        import_menu.setStyleSheet("""
            QMenu {
                background-color: #1a1f2e;
                border: 2px solid #2d3748;
                border-radius: 8px;
                padding: 8px 0;
            }
            QMenu::item {
                background-color: transparent;
                color: #e8eaed;
                padding: 12px 40px 12px 50px;
                font-size: 14px;
                font-weight: 600;
            }
            QMenu::item:selected {
                background-color: #252d3d;
            }
            QMenu::icon {
                padding-left: 15px;
            }
        """)
        
        # Acción Steam con icono
        steam_action = import_menu.addAction(t('btn_steam'))
        steam_icon = self.create_steam_icon()
        steam_action.setIcon(steam_icon)
        steam_action.triggered.connect(self.import_steam_games)
        
        # Acción Epic con icono
        epic_action = import_menu.addAction(t('btn_epic'))
        epic_icon = self.create_epic_icon()
        epic_action.setIcon(epic_icon)
        epic_action.triggered.connect(self.import_epic_games)
        
        self.import_btn.setMenu(import_menu)
        header_controls.addWidget(self.import_btn)


        # Botón personalización
        self.customize_btn = QPushButton(t('btn_settings'))
        self.customize_btn.setStyleSheet("""
            QPushButton {
                background:#1a1f2e; color:#e8eaed; border:1px solid #2d3748; border-radius:8px; padding:10px 20px; font-weight:600;
            }
            QPushButton:hover {background:#252d3d; border-color:#667eea;}
        """)
        self.customize_btn.clicked.connect(self.open_settings)
        header_controls.addWidget(self.customize_btn)

        tb_layout.addLayout(header_controls)
        
        # Botones de ventana (minimizar y cerrar)
        window_controls = QHBoxLayout()
        window_controls.setSpacing(0)
        window_controls.setContentsMargins(0, 0, 0, 0)
        
        minimize_btn = QPushButton("—")
        minimize_btn.setFixedSize(40, 40)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e8eaed;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #252d3d;
            }
        """)
        minimize_btn.clicked.connect(self.animate_minimize)
        window_controls.addWidget(minimize_btn)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(40, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e8eaed;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e53e3e;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        window_controls.addWidget(close_btn)
        
        tb_layout.addLayout(window_controls)

        main_layout.addWidget(self.top_bar)

        # Contenedor interior con padding
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(30, 20, 30, 30)
        inner_layout.setSpacing(20)
        
        # Área de contenido con sidebar + scroll
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        self._init_sidebar()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.games_widget = QWidget()
        self.games_widget.setStyleSheet("background: transparent;")
        self.games_layout = QGridLayout()
        self.games_layout.setSpacing(25)
        self.games_widget.setLayout(self.games_layout)
        
        scroll.setWidget(self.games_widget)

        content_layout.addWidget(self.sidebar_container)
        content_layout.addWidget(scroll, 1)
        inner_layout.addLayout(content_layout)
        main_layout.addWidget(inner)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Permitir arrastre de ventana desde la barra
        def top_bar_press(ev):
            self._start_move(ev)
        def top_bar_move(ev):
            self._move_window(ev)
        self.top_bar.mousePressEvent = top_bar_press
        self.top_bar.mouseMoveEvent = top_bar_move
        # Sin acciones de doble clic (no hay maximizar/restaurar)

    def _start_move(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def _move_window(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def _init_sidebar(self):
        self.sidebar_container = QWidget()
        self.sidebar_container.setFixedWidth(60)
        self.sidebar_container.setMinimumWidth(60)
        self.sidebar_container.setMaximumWidth(60)
        self.sidebar_container.setStyleSheet("background-color:#0f1419; border-radius:12px;")
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_layout.setContentsMargins(8, 12, 8, 12)
        self.sidebar_layout.setSpacing(8)
        self.sidebar_hint = QLabel(t('sidebar_hint'))
        self.sidebar_hint.setStyleSheet("color:#9aa0a6; font-size:11px;")
        self.sidebar_hint.setWordWrap(True)
        self.sidebar_hint.setVisible(False)
        self.sidebar_layout.addWidget(self.sidebar_hint)
        self.sidebar_layout.addStretch()
        self._refresh_sidebar_buttons()

        def enter(ev):
            self._expand_sidebar()
            QWidget.enterEvent(self.sidebar_container, ev)
        def leave(ev):
            self._collapse_sidebar()
            QWidget.leaveEvent(self.sidebar_container, ev)
        self.sidebar_container.enterEvent = enter
        self.sidebar_container.leaveEvent = leave

    def _expand_sidebar(self):
        target = 220
        if self.sidebar_container.maximumWidth() == target:
            return
        anim = QPropertyAnimation(self.sidebar_container, b"maximumWidth")
        anim.setDuration(180)
        anim.setStartValue(self.sidebar_container.maximumWidth())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self.sidebar_anim = anim
        self.sidebar_hint.setVisible(True)

    def _collapse_sidebar(self):
        target = 60
        if self.sidebar_container.maximumWidth() == target:
            return
        anim = QPropertyAnimation(self.sidebar_container, b"maximumWidth")
        anim.setDuration(180)
        anim.setStartValue(self.sidebar_container.maximumWidth())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self.sidebar_anim = anim
        self.sidebar_hint.setVisible(False)

    def _collect_folders(self):
        folders = set(self.custom_folders or [])
        for g in self.games:
            for f in g.get('folders', []) or []:
                folders.add(f)
        has_steam = any(g.get('is_steam_game') for g in self.games)
        has_epic = any(g.get('is_epic_game') for g in self.games)
        if has_steam:
            folders.add('Steam')
        if has_epic:
            folders.add('Epic')
        return sorted(folders)

    def _build_filter_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color:#1a1f2e; border:1px solid #2d3748; border-radius:8px; padding:6px 0; }
            QMenu::item { color:#e8eaed; padding:8px 18px; }
            QMenu::item:selected { background:#252d3d; }
        """)

        # Plataforma - radio buttons (solo una opción)
        platform_menu = QMenu(t('menu_platform'), self)
        platform_group = QActionGroup(self)
        platform_group.setExclusive(True)
        def add_platform(label, key):
            act = platform_menu.addAction(label)
            act.setCheckable(True)
            platform_group.addAction(act)
            act.setChecked(self.filter_platform == key)
            act.triggered.connect(lambda checked, k=key: self._set_platform_filter(k) if checked else None)
        add_platform(t('label_all_games'), None)
        add_platform(t('label_folder_steam'), 'Steam')
        add_platform(t('label_folder_epic'), 'Epic')
        add_platform(t('label_platform_manual'), 'Manual')
        menu.addMenu(platform_menu)

        fav_act = menu.addAction(t('btn_favorites_filter'))
        fav_act.setCheckable(True)
        fav_act.setChecked(self.filter_favorites)
        fav_act.triggered.connect(self._toggle_favorites_filter)

        menu.addSeparator()

        # Ordenar - radio buttons (solo una opción)
        sort_menu = QMenu(t('menu_sort'), self)
        sort_group = QActionGroup(self)
        sort_group.setExclusive(True)
        def add_sort(label, key):
            act = sort_menu.addAction(label)
            act.setCheckable(True)
            sort_group.addAction(act)
            act.setChecked(self.sort_mode == key)
            act.triggered.connect(lambda checked, k=key: self._set_sort_mode(k) if checked else None)
        add_sort(t('sort_name_asc'), 'name_asc')
        add_sort(t('sort_last_played_desc'), 'last_played_desc')
        add_sort(t('sort_playtime_desc'), 'playtime_desc')
        add_sort(t('sort_date_newest'), 'date_added_desc')
        add_sort(t('sort_date_oldest'), 'date_added_asc')
        menu.addMenu(sort_menu)

        self.filter_btn.setMenu(menu)

    def _set_platform_filter(self, key):
        self.filter_platform = key
        self._persist_filters()
        self._build_filter_menu()  # Reconstruir menú para actualizar checks
        self.render_games()

    def _toggle_favorites_filter(self):
         self.filter_favorites = not self.filter_favorites
         if self.filter_favorites:
             self.active_folder = '__favorites__'
         elif self.active_folder == '__favorites__':
             self.active_folder = None
         self._sync_folder_selection()
         self._persist_filters()
         self.render_games()

    def _set_sort_mode(self, key):
         self.sort_mode = key
         self._persist_filters()
         self._build_filter_menu()  # Reconstruir menú para actualizar checks
         self.render_games()

    def _persist_filters(self):
         try:
             data = json.load(open(self.theme_file, 'r', encoding='utf-8')) if self.theme_file.exists() else {}
             data['filter_platform'] = self.filter_platform
             data['filter_favorites'] = self.filter_favorites
             data['sort_mode'] = self.sort_mode
             data['last_folder'] = self.active_folder
             json.dump(data, open(self.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
         except Exception:
             pass

    def _refresh_sidebar_buttons(self):
        while self.sidebar_layout.count() > 0:
            item = self.sidebar_layout.takeAt(0)
            w = item.widget()
            if w and w is not self.sidebar_hint:
                w.deleteLater()
        self.folder_buttons = {}

        self.sidebar_layout.addWidget(self.sidebar_hint)

        def add_btn(key, label_text, icon_text='📁', checkable=True, disabled=False, is_custom=False):
            btn = QPushButton(f"{icon_text}  {label_text}")
            btn.setCheckable(checkable)
            btn.setDisabled(disabled)
            btn.setStyleSheet("""
                QPushButton {background:#1a1f2e; color:#e8eaed; border:1px solid #2d3748; border-radius:10px; padding:10px; text-align:left;}
                QPushButton:hover {border-color:#667eea; background:#252d3d;}
                QPushButton:checked {background:#667eea; color:white; border-color:#667eea;}
                QPushButton:disabled {color:#6b7280;}
            """)
            btn.clicked.connect(lambda _, k=key: self._on_folder_clicked(k))
            if is_custom:
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(lambda pos, k=key, b=btn: self._on_folder_context(k, b))
            self.sidebar_layout.addWidget(btn)
            self.folder_buttons[key] = btn

        add_btn('__all__', t('label_all_games'), icon_text='🗂')

        has_steam = any(g.get('is_steam_game') for g in self.games)
        has_epic = any(g.get('is_epic_game') for g in self.games)
        if has_steam:
            add_btn('Steam', t('label_folder_steam'), icon_text='🟦')
        if has_epic:
            add_btn('Epic', t('label_folder_epic'), icon_text='⬛')

        add_btn('__favorites__', t('btn_favorites_filter'), icon_text='⭐')

        for folder in self._collect_folders():
            if folder in ('Steam', 'Epic'):
                continue
            icon_path = self.folder_icons.get(folder)
            icon_text = '📁'
            if icon_path and os.path.exists(icon_path):
                pm = QPixmap(icon_path)
                if not pm.isNull():
                    icon_text = ''
                    btn = QPushButton(folder)
                    btn.setIcon(QIcon(pm))
                    btn.setIconSize(QSize(20, 20))
                    btn.setCheckable(True)
                    btn.setStyleSheet("""
                        QPushButton {background:#1a1f2e; color:#e8eaed; border:1px solid #2d3748; border-radius:10px; padding:10px; text-align:left;}
                        QPushButton:hover {border-color:#667eea; background:#252d3d;}
                        QPushButton:checked {background:#667eea; color:white; border-color:#667eea;}
                    """)
                    btn.clicked.connect(lambda _, k=folder: self._on_folder_clicked(k))
                    btn.setContextMenuPolicy(Qt.CustomContextMenu)
                    btn.customContextMenuRequested.connect(lambda pos, k=folder, b=btn: self._on_folder_context(k, b))
                    self.sidebar_layout.addWidget(btn)
                    self.folder_buttons[folder] = btn
                    continue
            add_btn(folder, folder, icon_text=icon_text, is_custom=True)

        new_btn = QPushButton(f"＋  {t('btn_new_folder')}")
        new_btn.setStyleSheet("""
            QPushButton {background:#2d3748; color:#e8eaed; border:1px dashed #3b4454; border-radius:10px; padding:10px; text-align:left;}
            QPushButton:hover {border-color:#667eea; background:#252d3d;}
        """)
        new_btn.clicked.connect(self._show_new_folder_dialog)
        self.sidebar_layout.addWidget(new_btn)

        self.sidebar_layout.addStretch()
        self.sidebar_layout.insertWidget(0, self.sidebar_hint)
        self._sync_folder_selection()

    def _sync_folder_selection(self):
        active = self.active_folder or '__all__'
        for key, btn in self.folder_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(key == active)
            btn.blockSignals(False)

    def _on_folder_clicked(self, key):
        if key == '__favorites__':
            self.filter_favorites = True
            self.active_folder = '__favorites__'
        else:
            self.filter_favorites = False
            self.active_folder = None if key == '__all__' else key
        try:
            if self.theme_file.exists():
                data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
            else:
                data = {}
            data['last_folder'] = self.active_folder
            data['filter_favorites'] = self.filter_favorites
            json.dump(data, open(self.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        except Exception:
            pass
        self._sync_folder_selection()
        self.render_games()

    def _show_new_folder_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(t('dialog_new_folder'))
        dialog.setFixedSize(400, 200)
        layout = QVBoxLayout(dialog)
        
        name_label = QLabel(t('placeholder_folder_name'))
        name_input = QLineEdit()
        
        icon_label = QLabel(t('label_folder_icon'))
        icon_input = QLineEdit()
        icon_input.setPlaceholderText(t('placeholder_folder_icon'))
        
        browse_btn = QPushButton('📁')
        browse_btn.setFixedSize(45, 45)
        browse_btn.clicked.connect(lambda: self._browse_folder_icon(icon_input))
        
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(icon_input)
        icon_layout.addWidget(browse_btn)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(t('btn_save'))
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton(t('btn_cancel'))
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addWidget(icon_label)
        layout.addLayout(icon_layout)
        layout.addStretch()
        layout.addLayout(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            icon_path = icon_input.text().strip()
            if name and name not in ('Steam', 'Epic', '__all__', '__favorites__'):
                if name not in self.custom_folders:
                    self.custom_folders.append(name)
                if icon_path and os.path.exists(icon_path):
                    self.folder_icons[name] = icon_path
                try:
                    if self.theme_file.exists():
                        data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
                    else:
                        data = {}
                    data['custom_folders'] = self.custom_folders
                    data['folder_icons'] = self.folder_icons
                    json.dump(data, open(self.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                except Exception:
                    pass
                self._refresh_sidebar_buttons()

    def _show_edit_folder_dialog(self, folder_name):
        dialog = QDialog(self)
        dialog.setWindowTitle(t('dialog_edit_folder'))
        dialog.setFixedSize(400, 200)
        layout = QVBoxLayout(dialog)
        
        name_label = QLabel(t('placeholder_folder_name'))
        name_input = QLineEdit()
        name_input.setText(folder_name)
        
        icon_label = QLabel(t('label_folder_icon'))
        icon_input = QLineEdit()
        icon_input.setPlaceholderText(t('placeholder_folder_icon'))
        if folder_name in self.folder_icons:
            icon_input.setText(self.folder_icons[folder_name])
        
        browse_btn = QPushButton('📁')
        browse_btn.setFixedSize(45, 45)
        browse_btn.clicked.connect(lambda: self._browse_folder_icon(icon_input))
        
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(icon_input)
        icon_layout.addWidget(browse_btn)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton(t('btn_save'))
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton(t('btn_cancel'))
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addWidget(icon_label)
        layout.addLayout(icon_layout)
        layout.addStretch()
        layout.addLayout(btn_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            new_name = name_input.text().strip()
            icon_path = icon_input.text().strip()
            if new_name and new_name not in ('Steam', 'Epic', '__all__', '__favorites__'):
                # Renombrar si cambió
                if new_name != folder_name:
                    idx = self.custom_folders.index(folder_name) if folder_name in self.custom_folders else -1
                    if idx >= 0:
                        self.custom_folders[idx] = new_name
                    for g in self.games:
                        if g.get('folders'):
                            g['folders'] = [new_name if f == folder_name else f for f in g['folders']]
                    if folder_name in self.folder_icons:
                        self.folder_icons[new_name] = self.folder_icons.pop(folder_name)
                    if self.active_folder == folder_name:
                        self.active_folder = new_name
                # Actualizar icono
                if icon_path and os.path.exists(icon_path):
                    self.folder_icons[new_name] = icon_path
                elif new_name in self.folder_icons and not icon_path:
                    del self.folder_icons[new_name]
                try:
                    if self.theme_file.exists():
                        data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
                    else:
                        data = {}
                    data['custom_folders'] = self.custom_folders
                    data['folder_icons'] = self.folder_icons
                    data['last_folder'] = self.active_folder
                    json.dump(data, open(self.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
                except Exception:
                    pass
                self.save_games()
                self._refresh_sidebar_buttons()
                self.render_games()

    def _browse_folder_icon(self, input_widget):
        file_path, _ = QFileDialog.getOpenFileName(self, t('label_folder_icon'), '', 'Images (*.png *.jpg *.jpeg)')
        if file_path:
            input_widget.setText(file_path)

    def _on_folder_context(self, key, btn_widget):
        if key in ('Steam', 'Epic', '__all__', '__favorites__'):
            return
        menu = QMenu(self)
        edit_action = menu.addAction(t('btn_edit_folder'))
        delete_action = menu.addAction(t('btn_delete_folder'))
        action = menu.exec_(btn_widget.mapToGlobal(QPoint(btn_widget.width()//2, btn_widget.height()//2)))
        if action == edit_action:
            self._show_edit_folder_dialog(key)
        elif action == delete_action:
            self._delete_custom_folder(key)

    def _delete_custom_folder(self, folder_name):
        if folder_name in self.custom_folders:
            self.custom_folders = [f for f in self.custom_folders if f != folder_name]
        # Quitar la carpeta de todos los juegos
        for g in self.games:
            if g.get('folders'):
                g['folders'] = [f for f in g['folders'] if f != folder_name]
        # Si era la carpeta activa, volver a All
        if self.active_folder == folder_name:
            self.active_folder = None
        # Persistir en theme y games
        try:
            if self.theme_file.exists():
                data = json.load(open(self.theme_file, 'r', encoding='utf-8'))
            else:
                data = {}
            data['custom_folders'] = self.custom_folders
            data['last_folder'] = self.active_folder
            json.dump(data, open(self.theme_file, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        except Exception:
            pass
        self.save_games()
        self._refresh_sidebar_buttons()
        self._suppress_render_animation = True
        self.render_games()

    def _update_game_folders(self, game_id, folder_name, add=True, lock_auto=True):
        for g in self.games:
            if g['id'] == game_id:
                folders = g.get('folders') or []
                if lock_auto and g.get('is_steam_game') and folder_name == 'Steam':
                    return
                if lock_auto and g.get('is_epic_game') and folder_name == 'Epic':
                    return
                if add:
                    if folder_name not in folders:
                        folders.append(folder_name)
                else:
                    folders = [f for f in folders if f != folder_name]
                g['folders'] = folders
                break
        self.save_games()
        self._refresh_sidebar_buttons()
        self.render_games()

    def animate_minimize(self):
        """Animación de minimizar hacia la barra de tareas"""
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup
        from PyQt5.QtWidgets import QApplication
        
        # Guardar geometría actual para restaurar después
        self._saved_geometry = self.geometry()
        
        # Determinar en qué pantalla está la ventana (la que tiene más área visible)
        current_screen = QApplication.screenAt(self.geometry().center())
        if not current_screen:
            current_screen = QApplication.primaryScreen()
        
        screen_geo = current_screen.geometry()
        taskbar_y = screen_geo.y() + screen_geo.height() - 40
        
        # Crear grupo de animaciones paralelas
        animation_group = QParallelAnimationGroup(self)
        
        # Animación de geometría (posición y tamaño)
        geometry_anim = QPropertyAnimation(self, b"geometry")
        geometry_anim.setDuration(300)
        geometry_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Mover hacia el centro inferior de la pantalla actual y reducir
        end_x = screen_geo.x() + screen_geo.width() // 2 - 50
        end_y = taskbar_y - 50
        end_geo = QRect(end_x, end_y, 100, 100)
        
        geometry_anim.setStartValue(self._saved_geometry)
        geometry_anim.setEndValue(end_geo)
        animation_group.addAnimation(geometry_anim)
        
        # Animación de opacidad
        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(300)
        opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        animation_group.addAnimation(opacity_anim)
        
        # Al finalizar, minimizar realmente
        animation_group.finished.connect(self._finish_minimize)
        
        self._minimize_animation = animation_group
        animation_group.start()
    
    def _finish_minimize(self):
        """Finalizar minimización y restaurar opacidad"""
        self.setWindowOpacity(1.0)
        self.showMinimized()
    
    def animate_restore(self):
        """Animación de restaurar desde la barra de tareas"""
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup
        from PyQt5.QtWidgets import QApplication
        
        if not self._saved_geometry:
            # Si no hay geometría guardada, restaurar sin animación
            self.showNormal()
            return
        
        # Determinar en qué pantalla debería aparecer la ventana
        current_screen = QApplication.screenAt(self._saved_geometry.center())
        if not current_screen:
            current_screen = QApplication.primaryScreen()

        screen_geo = current_screen.geometry()
        taskbar_y = screen_geo.y() + screen_geo.height() - 40

        # Asegurar que el objetivo a restaurar cabe en la pantalla destino
        avail = current_screen.availableGeometry() if current_screen else screen_geo
        target_geo = self._saved_geometry
        if avail:
            w = min(self._saved_geometry.width(), avail.width())
            h = min(self._saved_geometry.height(), avail.height())
            x = max(avail.x(), min(self._saved_geometry.x(), avail.right() - w))
            y = max(avail.y(), min(self._saved_geometry.y(), avail.bottom() - h))
            target_geo = QRect(x, y, w, h)
        
        # Posición inicial (pequeña en la barra de tareas)
        start_x = screen_geo.x() + screen_geo.width() // 2 - 50
        start_y = taskbar_y - 50
        start_geo = QRect(start_x, start_y, 100, 100)
        
        # Configurar geometría inicial antes de mostrar
        self.setGeometry(start_geo)
        self.setWindowOpacity(0.0)
        self.showNormal()
        
        # Crear grupo de animaciones paralelas
        animation_group = QParallelAnimationGroup(self)
        
        # Animación de geometría
        geometry_anim = QPropertyAnimation(self, b"geometry")
        geometry_anim.setDuration(300)
        geometry_anim.setEasingCurve(QEasingCurve.OutQuad)
        geometry_anim.setStartValue(start_geo)
        geometry_anim.setEndValue(target_geo)
        animation_group.addAnimation(geometry_anim)
        
        # Animación de opacidad
        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(300)
        opacity_anim.setEasingCurve(QEasingCurve.OutQuad)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        animation_group.addAnimation(opacity_anim)
        
        self._restore_animation = animation_group
        animation_group.start()
    
    def changeEvent(self, event):
        """Interceptar cambios de estado de la ventana"""
        from PyQt5.QtCore import QEvent, QTimer
        
        if event.type() == QEvent.WindowStateChange:
            # Si la ventana se está restaurando desde minimizada
            if not self.isMinimized() and event.oldState() & Qt.WindowMinimized:
                # Prevenir restauración inmediata, hacer animación
                if self._saved_geometry:
                    QTimer.singleShot(0, self.animate_restore)
                    event.ignore()
                    return
        
        super().changeEvent(event)

    # Animaciones y lógica de maximizar eliminadas para ventana fija

    # Eliminado eventFilter y animación de ventana para evitar agrandar toda la ventana.

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.bg_movie and self.bg_movie.isValid():
            # Dibujar GIF animado
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            current_pixmap = self.bg_movie.currentPixmap()
            if not current_pixmap.isNull():
                scaled = current_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                painter.setOpacity(self.bg_opacity)
                painter.drawPixmap(0, 0, scaled)
        elif self.bg_pixmap:
            # Dibujar imagen estática
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            scaled = self.bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.setOpacity(self.bg_opacity)
            painter.drawPixmap(0, 0, scaled)

    def open_settings(self):
        bg = ''
        current_theme = None
        if self.theme_file.exists():
            try:
                with open(self.theme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    bg = data.get('background_image', '') or ''
                    current_theme = data.get('theme')  # Cargar tema completo si existe
            except Exception:
                pass
        dlg = ColorPickerDialog(self, current_bg=bg, current_opacity=self.bg_opacity, color_scheme=self.color_scheme, current_bg_type=self.bg_type, current_theme=current_theme)
        # Conectar señal de cambio de idioma para recargar UI
        dlg.language_changed.connect(self.reload_ui_text)
        try:
            dlg.apply_history(self.bg_history)
        except Exception:
            pass
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            self.save_theme(data['background_image'], data['background_opacity'], data.get('color_scheme'), data.get('background_type', 'static'), data.get('theme'))

        
    def reload_ui_text(self, lang=None):
        """Recarga todos los strings de la UI cuando cambia el idioma"""
        # Actualizar título
        self.setWindowTitle(t('app_title'))
        self.title_label.setText(t('app_title'))
        
        # Actualizar placeholder de búsqueda
        self.search_input.setPlaceholderText(t('btn_search_placeholder'))
        
        # Actualizar botones
        self.add_btn.setText(t('btn_add_game'))
        self.import_btn.setText(t('btn_import_games'))
        self.customize_btn.setText(t('btn_settings'))
        
        # Actualizar selector de vista
        if hasattr(self, 'view_combo'):
            current_index = self.view_combo.currentIndex()
            self.view_combo.blockSignals(True)
            self.view_combo.clear()
            self.view_combo.addItems([t('view_grid'), t('view_list')])
            self.view_combo.setCurrentIndex(current_index)
            self.view_combo.blockSignals(False)
        
        # Actualizar sidebar con nuevas traducciones
        if hasattr(self, '_refresh_sidebar_buttons'):
            self._refresh_sidebar_buttons()
        
        # Actualizar menú de filtros
        if hasattr(self, '_build_filter_menu'):
            self._build_filter_menu()
        
    def load_games(self):
        """Cargar juegos desde el archivo JSON"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.games = json.load(f)
            except Exception as e:
                print(f"Error al cargar juegos: {e}")
                self.games = []
        else:
            self.games = []
        # Asegurar campos para playtime y favoritos en datos existentes
        changed = False
        fallback_base = datetime.now()
        for idx, game in enumerate(self.games):
            if 'is_favorite' not in game:
                game['is_favorite'] = False
                changed = True
            if 'total_play_time' not in game:
                game['total_play_time'] = 0
                changed = True
            if 'last_played' not in game:
                game['last_played'] = None
                changed = True
            if 'date_added' not in game:
                # Intentar campos previos; si no, usar orden del archivo como prioridad más antigua
                ts = game.get('created_at') or game.get('added_at')
                if not ts:
                    ts = (fallback_base - timedelta(seconds=(len(self.games) - idx))).isoformat()
                game['date_added'] = ts
                changed = True
            folders = game.get('folders')
            if not isinstance(folders, list):
                game['folders'] = []
                folders = game['folders']
                changed = True
            auto_added = False
            if game.get('is_steam_game') and 'Steam' not in folders:
                folders.append('Steam')
                auto_added = True
            if game.get('is_epic_game') and 'Epic' not in folders:
                folders.append('Epic')
                auto_added = True
            if auto_added:
                changed = True
        if changed:
            self.save_games()
            
    def save_games(self):
        """Guardar juegos en el archivo JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.games, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar juegos: {e}")
    
    def toggle_favorite(self, game_id, is_favorite):
        """Alternar estado favorito de un juego y guardar"""
        for game in self.games:
            if game['id'] == game_id:
                game['is_favorite'] = is_favorite
                break
        self.save_games()

    def _update_last_played(self, game_id, persist=False):
        """Actualizar el campo last_played para un juego"""
        timestamp = datetime.now().isoformat()
        for game in self.games:
            if game['id'] == game_id:
                game['last_played'] = timestamp
                break
        if persist:
            self.save_games()

    def _update_playtime_labels(self, game_id, total_seconds):
        """Refresca el texto de tiempo jugado en la tarjeta correspondiente."""
        # Recorre el grid para encontrar la GameCard y actualizar su label sin re-renderizar todo
        try:
            for i in range(self.games_layout.count()):
                item = self.games_layout.itemAt(i)
                w = item.widget()
                # En grid, el widget es un contenedor; en lista es la propia card
                candidates = []
                if hasattr(w, 'game'):
                    candidates.append(w)
                if hasattr(w, 'layout') and callable(w.layout):
                    layout = w.layout()
                    if layout and layout.count() == 1 and hasattr(layout.itemAt(0).widget(), 'game'):
                        candidates.append(layout.itemAt(0).widget())
                for card in candidates:
                    if hasattr(card, 'game') and card.game.get('id') == game_id:
                        if hasattr(card, 'playtime_label'):
                            card.playtime_label.setText(t('label_playtime', value=card._format_playtime(total_seconds)))
                        return
        except Exception:
            pass

    def _start_play_session(self, game_id, process_handle=None):
        """Inicia una sesión de juego para acumular tiempo."""
        # Cerrar sesión anterior si existiera
        self._finish_play_session()
        self._play_session = {
            'game_id': game_id,
            'start_time': datetime.now(),
            'process': process_handle
        }
        self._update_last_played(game_id, persist=True)
        if self.playtime_tracking_enabled and not self.playtime_timer.isActive():
            self.playtime_timer.start()

    def _finish_play_session(self, force_elapsed=None):
        """Finaliza la sesión actual sumando el tiempo transcurrido."""
        if not self._play_session:
            return
        start = self._play_session.get('start_time')
        game_id = self._play_session.get('game_id')
        if not start or not game_id:
            self._play_session = None
            self.playtime_timer.stop()
            return
        elapsed = force_elapsed if force_elapsed is not None else int((datetime.now() - start).total_seconds())
        elapsed = max(0, elapsed)
        for game in self.games:
            if game['id'] == game_id:
                base = int(game.get('total_play_time', 0) or 0)
                total = base + elapsed
                game['total_play_time'] = total
                game['last_played'] = datetime.now().isoformat()
                self._update_playtime_labels(game_id, total)
                break
        self.save_games()
        self._play_session = None
        self.playtime_timer.stop()

    def _tick_playtime(self):
        """Revisa periódicamente si el proceso terminó para cerrar la sesión."""
        if not self._play_session:
            self.playtime_timer.stop()
            return
        proc = self._play_session.get('process')
        game_id = self._play_session.get('game_id')
        start = self._play_session.get('start_time')
        if start and game_id:
            elapsed = int((datetime.now() - start).total_seconds())
            # Mostrar tiempo vivo en la tarjeta
            for game in self.games:
                if game['id'] == game_id:
                    base = int(game.get('total_play_time', 0) or 0)
                    self._update_playtime_labels(game_id, base + elapsed)
                    break
        running = True
        if proc is not None:
            try:
                running = proc.poll() is None
            except Exception:
                running = False
        else:
            running = True  # Sin handle: asumimos sigue corriendo hasta cerrar manualmente
        if not running:
            self._finish_play_session()

    def set_playtime_tracking(self, enabled: bool):
        """Permite activar/desactivar el seguimiento de tiempo desde la UI."""
        self.playtime_tracking_enabled = enabled
        if not enabled:
            self._finish_play_session()
        elif enabled and self._play_session and not self.playtime_timer.isActive():
            self.playtime_timer.start()
            
    def render_games(self):
        """Renderizar la lista de juegos"""
        # Limpiar layout
        while self.games_layout.count():
            item = self.games_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Filtrar juegos por búsqueda
        search_query = self.search_input.text().lower().strip() if hasattr(self, 'search_input') else ''
        filtered_games = [g for g in self.games if search_query in g['name'].lower()] if search_query else self.games
        
        # Filtrar por favoritos (dropdown o carpeta Favoritos)
        if self.filter_favorites or (self.active_folder == '__favorites__'):
            filtered_games = [g for g in filtered_games if g.get('is_favorite', False)]

        # Filtrar por carpeta activa (custom/Steam/Epic)
        if self.active_folder and self.active_folder not in ('__favorites__', '__all__'):
            filtered_games = [g for g in filtered_games if self.active_folder in (g.get('folders') or [])]

        # Filtrar por plataforma
        if self.filter_platform == 'Steam':
            filtered_games = [g for g in filtered_games if g.get('is_steam_game')]
        elif self.filter_platform == 'Epic':
            filtered_games = [g for g in filtered_games if g.get('is_epic_game')]
        elif self.filter_platform == 'Manual':
            filtered_games = [g for g in filtered_games if not g.get('is_steam_game') and not g.get('is_epic_game')]

        # Ordenamiento
        def sort_key(game):
            if self.sort_mode == 'name_asc':
                return (game.get('name') or '').lower()
            if self.sort_mode == 'last_played_desc':
                ts = game.get('last_played') or ''
                return ts
            if self.sort_mode == 'playtime_desc':
                return -(int(game.get('total_play_time', 0) or 0))
            if self.sort_mode == 'date_added_desc':
                return game.get('date_added') or ''
            if self.sort_mode == 'date_added_asc':
                return game.get('date_added') or ''
            return 0
        reverse = True if self.sort_mode in ('last_played_desc', 'playtime_desc', 'date_added_desc') else False
        filtered_games = sorted(filtered_games, key=sort_key, reverse=reverse)
        
        if not filtered_games:
            # Mostrar estado vacío o sin resultados
            if not self.games:
                empty_label = QLabel("Tu biblioteca está vacía\n\nAgrega tu primer juego para comenzar")
            else:
                empty_label = QLabel(f"No se encontraron juegos con '{search_query}'")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                color: #9aa0a6;
                font-size: 18px;
                padding: 100px;
            """)
            self.games_layout.addWidget(empty_label, 0, 0)
            return
        
        # Mostrar juegos en grid
        list_mode = self.view_combo.currentIndex() == 1  # 0=Grid, 1=List
        columns = 1 if list_mode else 3
        skip_anim = getattr(self, '_suppress_render_animation', False)
        for i, game in enumerate(filtered_games):
            delay = 0 if skip_anim else i * 50
            card = GameCard(game, self, list_mode=list_mode, animation_delay=delay)
            if list_mode:
                # Direct add (vertical stack)
                self.games_layout.addWidget(card, i, 0)
            else:
                container = QWidget()
                container.setFixedSize(320, 300)
                c_layout = QHBoxLayout(container)
                c_layout.setContentsMargins(10, 10, 10, 10)
                c_layout.addWidget(card)
                row = i // columns
                col = i % columns
                self.games_layout.addWidget(container, row, col)
            self._suppress_render_animation = False
            
    def add_game(self):
        """Abrir diálogo para agregar juego"""
        dialog = AddGameDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            game_data = dialog.get_game_data()
            if game_data['name'] and game_data['path']:
                game_data.setdefault('is_favorite', False)
                game_data['total_play_time'] = 0
                game_data['last_played'] = None
                game_data['date_added'] = datetime.now().isoformat()
                game_data['folders'] = []
                game_data['id'] = str(len(self.games) + 1)
                self.games.append(game_data)
                # Intentar icono si vacío
                if not game_data.get('icon') and os.path.exists(game_data['path']):
                    try:
                        import win32gui
                        import win32ui
                        import win32con
                        from PyQt5.QtGui import QImage
                        
                        icon_dir = Path.home() / '.game_library' / 'icons'
                        icon_dir.mkdir(exist_ok=True)
                        out_path = icon_dir / (Path(game_data['path']).stem + '_icon.png')
                        
                        large, small = win32gui.ExtractIconEx(game_data['path'], 0)
                        if large:
                            hicon = large[0]
                            ico_x = win32con.SM_CXICON
                            ico_y = win32con.SM_CYICON
                            
                            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                            hbmp = win32ui.CreateBitmap()
                            hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
                            hdc_mem = hdc.CreateCompatibleDC()
                            
                            hdc_mem.SelectObject(hbmp)
                            hdc_mem.DrawIcon((0, 0), hicon)
                            
                            bmpinfo = hbmp.GetInfo()
                            bmpstr = hbmp.GetBitmapBits(True)
                            
                            img = QImage(bmpstr, bmpinfo['bmWidth'], bmpinfo['bmHeight'], QImage.Format_ARGB32)
                            
                            if not img.isNull():
                                pixmap = QPixmap.fromImage(img)
                                pixmap.save(str(out_path), 'PNG')
                                game_data['icon'] = str(out_path)
                                
                                win32gui.DestroyIcon(hicon)
                                for icon in large[1:]:
                                    win32gui.DestroyIcon(icon)
                                for icon in small:
                                    win32gui.DestroyIcon(icon)
                                hdc_mem.DeleteDC()
                                hdc.DeleteDC()
                    except Exception:
                        pass
                self.save_games()
                self.render_games()
            else:
                QMessageBox.warning(self, "Error", "Por favor completa los campos obligatorios")
    
    def import_steam_games(self):
        """Importar juegos desde Steam"""
        try:
            # Crear scanner
            scanner = SteamScanner()
            
            if not scanner.steam_path:
                QMessageBox.warning(
                    self, 
                    "Steam no encontrado",
                    "No se pudo detectar Steam en este sistema.\n\n"
                    "Asegúrate de que Steam esté instalado correctamente."
                )
                return
            
            # Escanear juegos
            QApplication.setOverrideCursor(Qt.WaitCursor)
            games = scanner.scan_installed_games()
            QApplication.restoreOverrideCursor()
            
            if not games:
                QMessageBox.information(
                    self,
                    "Sin juegos",
                    "No se encontraron juegos instalados en Steam."
                )
                return
            
            # Dedupe de juegos escaneados por appid (defensivo)
            games_by_appid = {}
            for g in games:
                aid = g.get('appid')
                if aid and aid not in games_by_appid:
                    games_by_appid[aid] = g

            # Filtrar juegos que ya existen
            existing_appids = set()
            for game in self.games:
                if game.get('steam_appid'):
                    existing_appids.add(game['steam_appid'])

            # Crear lista de nuevos juegos sin duplicados
            new_games = [g for aid, g in games_by_appid.items() if aid not in existing_appids]
            
            if not new_games:
                QMessageBox.information(
                    self,
                    "Todos importados",
                    f"Todos los {len(games)} juegos de Steam ya están en tu biblioteca."
                )
                return
            
            # Confirmar importación
            reply = QMessageBox.question(
                self,
                "Importar juegos de Steam",
                f"Se encontraron {len(new_games)} juegos nuevos de Steam.\n"
                f"({len(games) - len(new_games)} ya están en tu biblioteca)\n\n"
                f"¿Deseas importarlos?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Crear diálogo de progreso
            progress = QProgressDialog(
                "Importando juegos de Steam...",
                "Cancelar",
                0,
                len(new_games),
                self
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("Importando Steam")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            imported_count = 0
            
            for i, game_data in enumerate(new_games):
                if progress.wasCanceled():
                    break
                
                progress.setLabelText(f"Importando: {game_data['name']}\n({i+1}/{len(new_games)})")
                progress.setValue(i)
                QApplication.processEvents()
                
                try:
                    # Obtener metadatos (imágenes)
                    metadata = scanner.get_game_metadata(game_data)

                    # Calcular icono cuadrado preferiblemente desde el .exe del juego
                    icon_path = None
                    exe_path = scanner.get_game_executable_path(game_data)
                    if exe_path and os.path.exists(exe_path):
                        try:
                            icon_path = self._extract_icon_to_cache(exe_path)
                        except Exception:
                            icon_path = None
                    # Fallback: usar icono de caché de Steam (si existe) o logo del CDN (evita los banners)
                    if not icon_path:
                        icon_path = metadata.get('icon')

                    # Crear entrada del juego
                    new_game = {
                        'id': str(uuid.uuid4()),
                        'name': game_data['name'],
                        'path': f"steam://rungameid/{game_data['appid']}",
                        'image': metadata.get('header') or metadata.get('grid'),
                        'icon': icon_path or '',
                        'steam_appid': game_data['appid'],
                        'is_steam_game': True,
                        'is_favorite': False,
                        'total_play_time': 0,
                        'last_played': None,
                        'date_added': datetime.now().isoformat()
                    }

                    self.games.append(new_game)
                    imported_count += 1

                except Exception as e:
                    print(f"Error importando {game_data['name']}: {e}")
                    continue
            
            progress.setValue(len(new_games))
            
            # Guardar y renderizar
            if imported_count > 0:
                self.save_games()
                self.render_games()
                
                QMessageBox.information(
                    self,
                    "Importación completa",
                    f"Se importaron {imported_count} juegos de Steam correctamente."
                )
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(
                self,
                "Error",
                f"Error al importar juegos de Steam:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def import_epic_games(self):
        """Importar juegos desde Epic Games Store"""
        try:
            # Crear scanner
            scanner = EpicScanner()
            
            if not scanner.manifest_folder:
                QMessageBox.warning(
                    self, 
                    "Epic Games Store no encontrado",
                    "No se pudo detectar Epic Games Store en este sistema.\n\n"
                    "Asegúrate de que Epic Games Launcher esté instalado correctamente."
                )
                return
            
            # Escanear juegos
            QApplication.setOverrideCursor(Qt.WaitCursor)
            games = scanner.scan_installed_games()
            QApplication.restoreOverrideCursor()
            
            if not games:
                QMessageBox.information(
                    self,
                    "Sin juegos",
                    "No se encontraron juegos instalados en Epic Games Store."
                )
                return
            
            # Filtrar juegos que ya existen (por app_name de Epic)
            existing_epic_apps = set()
            for game in self.games:
                if game.get('epic_app_name'):
                    existing_epic_apps.add(game['epic_app_name'])
            
            new_games = [g for g in games if g['app_name'] not in existing_epic_apps]
            
            if not new_games:
                QMessageBox.information(
                    self,
                    "Todos importados",
                    f"Todos los {len(games)} juegos de Epic ya están en tu biblioteca."
                )
                return
            
            # Confirmar importación
            reply = QMessageBox.question(
                self,
                "Importar juegos de Epic Games Store",
                f"Se encontraron {len(new_games)} juegos nuevos de Epic.\n"
                f"({len(games) - len(new_games)} ya están en tu biblioteca)\n\n"
                f"¿Deseas importarlos?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Crear diálogo de progreso
            progress = QProgressDialog(
                "Importando juegos de Epic Games Store...",
                "Cancelar",
                0,
                len(new_games),
                self
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("Importando Epic")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            imported_count = 0
            
            for i, game_data in enumerate(new_games):
                if progress.wasCanceled():
                    break
                
                progress.setLabelText(f"Importando: {game_data['display_name']}\n({i+1}/{len(new_games)})")
                progress.setValue(i)
                QApplication.processEvents()
                
                try:
                    # Obtener metadatos (imágenes) desde Epic
                    metadata = scanner.get_game_metadata(game_data) or {}
                    # Debug simple: reportar metadatos
                    try:
                        print('[Epic Import] metadata for', game_data.get('display_name'), metadata)
                    except Exception:
                        pass

                    # Extraer icono del ejecutable si no hay icono del catálogo
                    icon_path = metadata.get('icon')
                    exe_path = scanner.get_game_executable_path(game_data)
                    if not icon_path and exe_path and os.path.exists(exe_path):
                        try:
                            icon_path = self._extract_icon_to_cache(exe_path)
                        except Exception:
                            icon_path = None
                    
                    # Obtener comando de lanzamiento usando el protocolo de Epic
                    launch_command = scanner.get_launch_command(game_data)
                    
                    # Selección de imagen de portada: grid > header; si falta, intentar fallback en Steam por título
                    cover_image = metadata.get('grid') or metadata.get('header') or ''
                    if not cover_image:
                        try:
                            steam_scanner = SteamScanner()
                            steam_games = steam_scanner.scan_installed_games()
                            title = (game_data.get('display_name') or '').lower().strip()
                            match = None
                            for sg in steam_games:
                                t = (sg.get('name') or '').lower().strip()
                                if t == title:
                                    match = sg
                                    break
                            if not match and steam_games and title:
                                words = [w for w in title.split() if len(w) > 3]
                                for sg in steam_games:
                                    t = (sg.get('name') or '').lower()
                                    if all(w in t for w in words[:2]):
                                        match = sg
                                        break
                            if match:
                                smeta = steam_scanner.get_game_metadata(match)
                                cover_image = smeta.get('library_600x900') or smeta.get('header') or cover_image
                                # Si aún no hay icono, intentar usar el de Steam
                                if not icon_path:
                                    icon_path = smeta.get('icon') or icon_path
                        except Exception:
                            pass

                    new_game = {
                        'id': str(uuid.uuid4()),
                        'name': game_data['display_name'],
                        'path': launch_command if launch_command else (exe_path or ''),
                        'image': cover_image,
                        'icon': icon_path or '',
                        'epic_app_name': game_data['app_name'],
                        'is_epic_game': True,
                        'is_favorite': False,
                        'total_play_time': 0,
                        'last_played': None,
                        'date_added': datetime.now().isoformat()
                    }
                    
                    self.games.append(new_game)
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Error importando {game_data['display_name']}: {e}")
                    continue
            
            progress.setValue(len(new_games))
            
            # Guardar y renderizar
            if imported_count > 0:
                self.save_games()
                self.render_games()
                
                QMessageBox.information(
                    self,
                    "Importación completa",
                    f"Se importaron {imported_count} juegos de Epic Games Store correctamente."
                )
        
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(
                self,
                "Error",
                f"Error al importar juegos de Epic Games Store:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def _extract_icon_to_cache(self, exe_path: str) -> str:
        """Extrae el icono de un .exe y lo guarda en caché, retornando la ruta PNG.
        Fuerza 40x40 para consistencia con el render de 50x50.
        """
        from PyQt5.QtWinExtras import QtWin
        import ctypes
        from ctypes import wintypes, byref, POINTER

        icon_dir = Path.home() / '.game_library' / 'icons'
        icon_dir.mkdir(parents=True, exist_ok=True)
        out_path = icon_dir / (Path(exe_path).stem + '_icon.png')

        # Si ya existe y es válido, reutilizar
        if out_path.exists():
            pm = QPixmap(str(out_path))
            if not pm.isNull() and pm.width() >= 16 and pm.height() >= 16:
                return str(out_path)
            else:
                try:
                    out_path.unlink()
                except Exception:
                    pass

        ExtractIconExW = ctypes.windll.shell32.ExtractIconExW
        ExtractIconExW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, POINTER(wintypes.HICON), POINTER(wintypes.HICON), wintypes.UINT]
        ExtractIconExW.restype = wintypes.UINT

        large_icon = wintypes.HICON()
        small_icon = wintypes.HICON()

        count = ExtractIconExW(exe_path, 0, byref(large_icon), byref(small_icon), 1)
        if count > 0 and large_icon.value:
            pm = QtWin.fromHICON(large_icon.value)
            if not pm.isNull():
                if pm.width() != 40 or pm.height() != 40:
                    pm = pm.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                pm.save(str(out_path), 'PNG')
                ctypes.windll.user32.DestroyIcon(large_icon)
                if small_icon.value:
                    ctypes.windll.user32.DestroyIcon(small_icon)
                return str(out_path)

        # Fallback
        return ''
                
    def edit_game(self, game):
        """Editar juego existente"""
        dialog = AddGameDialog(self, game)
        if dialog.exec_() == QDialog.Accepted:
            game_data = dialog.get_game_data()
            if game_data['name'] and game_data['path']:
                for i, g in enumerate(self.games):
                    if g['id'] == game['id']:
                        self.games[i].update(game_data)
                        # Icono auto si falta
                        if not self.games[i].get('icon') and os.path.exists(game_data['path']):
                            try:
                                from PyQt5.QtWinExtras import QtWin
                                import ctypes
                                from ctypes import wintypes, byref, POINTER
                                
                                icon_dir = Path.home() / '.game_library' / 'icons'
                                icon_dir.mkdir(exist_ok=True)
                                out_path = icon_dir / (Path(game_data['path']).stem + '_icon.png')
                                
                                ExtractIconExW = ctypes.windll.shell32.ExtractIconExW
                                ExtractIconExW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, POINTER(wintypes.HICON), POINTER(wintypes.HICON), wintypes.UINT]
                                ExtractIconExW.restype = wintypes.UINT
                                
                                large_icon = wintypes.HICON()
                                small_icon = wintypes.HICON()
                                
                                count = ExtractIconExW(game_data['path'], 0, byref(large_icon), byref(small_icon), 1)
                                
                                if count > 0 and large_icon.value:
                                    pixmap = QtWin.fromHICON(large_icon.value)
                                    
                                    if not pixmap.isNull():
                                        # Escalar a 40x40 forzado
                                        if pixmap.width() != 40 or pixmap.height() != 40:
                                            pixmap = pixmap.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                                        
                                        pixmap.save(str(out_path), 'PNG')
                                        self.games[i]['icon'] = str(out_path)
                                        
                                        # Limpiar recursos
                                        ctypes.windll.user32.DestroyIcon(large_icon)
                                        if small_icon.value:
                                            ctypes.windll.user32.DestroyIcon(small_icon)
                            except Exception:
                                pass
                        break
                self.save_games()
                self.render_games()
                
    def _dedupe_games_by_appid(self) -> bool:
        """Elimina duplicados conservando el primero cuando comparten steam_appid.
        Retorna True si hubo cambios."""
        seen = set()
        new_list = []
        changed = False
        for g in self.games:
            appid = g.get('steam_appid')
            if appid:
                if appid in seen:
                    changed = True
                    continue
                seen.add(appid)
            new_list.append(g)
        if changed:
            self.games = new_list
        return changed

    def delete_game(self, game):
        """Eliminar juego"""
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de que quieres eliminar '{game['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.games = [g for g in self.games if g['id'] != game['id']]
            self.save_games()
            self.render_games()
            
    def play_game(self, game):
        """Ejecutar el juego"""
        try:
            game_path = game['path']
            process_handle = None
            launched = False
            # Soporte para juegos de Steam via protocolo
            if isinstance(game_path, str) and game_path.startswith('steam://'):
                try:
                    os.startfile(game_path)
                    launched = True
                    if self.playtime_tracking_enabled:
                        # No tenemos handle, pero iniciamos sesión para contar mientras está abierto
                        self._start_play_session(game['id'], process_handle=None)
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo abrir Steam:\n{e}")
                    return

            if os.path.exists(game_path):
                game_dir = os.path.dirname(game_path) or None

                try:
                    # Intentar ejecutar normalmente
                    process_handle = subprocess.Popen(
                        [game_path],
                        cwd=game_dir,
                        shell=False,
                        start_new_session=True
                    )
                    launched = True
                except OSError as e:
                    # Si requiere elevación (WinError 740), intentar con UAC
                    needs_elevation = getattr(e, 'winerror', None) == 740 or 'requires elevation' in str(e).lower()
                    if needs_elevation:
                        try:
                            r = ctypes.windll.shell32.ShellExecuteW(None, "runas", game_path, None, game_dir, 1)
                            if r <= 32:
                                QMessageBox.warning(self, "Error", f"No se pudo iniciar con permisos de administrador (código {r}).")
                            else:
                                launched = True
                                if self.playtime_tracking_enabled:
                                    self._update_last_played(game['id'], persist=True)
                        except Exception as ee:
                            QMessageBox.critical(self, "Error", f"No se pudo solicitar permisos de administrador:\n{ee}")
                    else:
                        raise
                # No mostrar mensaje para no interrumpir
            else:
                QMessageBox.warning(self, "Error", f"No se encontró el ejecutable:\n{game_path}")

            # Iniciar tracking de tiempo si corresponde
            if launched:
                if self.playtime_tracking_enabled and process_handle:
                    self._start_play_session(game['id'], process_handle)
                elif self.playtime_tracking_enabled:
                    # Si no se pudo adjuntar proceso, al menos marcar última vez jugado
                    self._start_play_session(game['id'], process_handle=None)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al ejecutar el juego:\n{str(e)}")

        def closeEvent(self, event):
            """Al cerrar la app, finaliza sesión de juego en curso."""
            try:
                if self.playtime_tracking_enabled:
                    self._finish_play_session()
            except Exception:
                pass
            super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Paleta oscura
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(15, 20, 25))
    palette.setColor(QPalette.WindowText, QColor(232, 234, 237))
    palette.setColor(QPalette.Base, QColor(26, 31, 46))
    palette.setColor(QPalette.AlternateBase, QColor(37, 45, 61))
    palette.setColor(QPalette.Text, QColor(232, 234, 237))
    palette.setColor(QPalette.Button, QColor(26, 31, 46))
    palette.setColor(QPalette.ButtonText, QColor(232, 234, 237))
    app.setPalette(palette)
    
    window = GameLibrary()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

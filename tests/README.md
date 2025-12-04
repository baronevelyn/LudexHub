# Test de Extracción de Iconos

Este script de prueba ayuda a diagnosticar por qué no se están extrayendo los iconos de los ejecutables.

## Cómo usar

1. Ejecutar desde la terminal:
```powershell
cd C:\Users\alext\Desktop\libreria
python tests\test_icon_extraction.py
```

2. Hacer clic en "Seleccionar archivo .exe"

3. Elegir un juego .exe de tu biblioteca

4. El test intentará extraer el icono usando 3 métodos diferentes:
   - **Método 1**: QIcon directo (guardando como .ico)
   - **Método 2**: SHGetFileInfo de Windows API (si QtWinExtras está disponible)
   - **Método 3**: QIcon directo (guardando como .png)

## Qué verificar

- Si algún método funciona, verás el icono extraído en la ventana
- La consola mostrará información detallada sobre cada intento
- Busca mensajes de error específicos que indiquen el problema

## Archivos de salida

Los iconos de prueba se guardan en:
- `~/.game_library/icons/test_icon.ico` (Método 1)
- `~/.game_library/icons/test_icon2.ico` (Método 2)
- `~/.game_library/icons/test_icon.png` (Método 3)

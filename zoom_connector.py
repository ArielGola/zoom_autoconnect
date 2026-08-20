"""
Funciones para conectarse, verificar y cerrar la app de escritorio de Zoom.
"""
 
import os
import re
import time
 
import psutil
import pyautogui
import pygetwindow as gw
from colorama import Fore, Style
 
# Palabras clave para encontrar la ventana de la reunión entre todas las
# ventanas abiertas (el título exacto varía según el idioma/versión de Zoom).
ZOOM_WINDOW_TITLE_KEYWORDS = ("Zoom Meeting", "Zoom Webinar", "Reunión de Zoom", "Zoom")
 
 
def extract_meeting_info(zoom_link):
    """Extrae tipo de evento (meeting/webinar), ID y contraseña/token desde el link."""
    match_meeting = re.search(r"j/(\d+)\?pwd=([\w\d\.]+)", zoom_link)
    if match_meeting:
        return "meeting", match_meeting.group(1), match_meeting.group(2)
 
    match_webinar = re.search(r"w/(\d+)\?tk=([\w\d\.\-_]+)", zoom_link)
    if match_webinar:
        return "webinar", match_webinar.group(1), match_webinar.group(2)
 
    return None, None, None  # Si el enlace no es válido
 
 
def close_zoom():
    """Cierra la app de Zoom."""
    print("     --Cerrando Zoom en 5 segundos.\n")
    time.sleep(5)
    os.system("taskkill /f /im Zoom.exe")  # Windows
    print(Fore.GREEN + "\n     --Zoom ha sido cerrado." + Style.RESET_ALL)
 
 
def click_iniciar_reunion(timeout=15, interval=1):
    """Busca y hace clic en el botón 'Iniciar reunión' mediante reconocimiento de imagen."""
    print("     --Buscando el botón 'Iniciar reunión'.")
    start_time_click = time.time()
 
    while time.time() - start_time_click < timeout:
        try:
            time.sleep(10)
            location = pyautogui.locateCenterOnScreen('iniciar_reunion.png', confidence=0.6)
 
            if location:
                pyautogui.click(location)
                print("     --Botón 'Iniciar reunión' clickeado automáticamente.")
                return True
 
        except pyautogui.ImageNotFoundException:
            # Si se lanza la excepción, se ignora y se espera para el siguiente intento.
            pass
 
        time.sleep(interval)
 
    print("     --No se encontró el botón 'Iniciar reunión'.")
    return False
 
 
def is_zoom_running():
    """Comprueba si Zoom está corriendo (en Windows, busca 'Zoom.exe')."""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and 'Zoom.exe' in proc.info['name']:
            return True
    return False
 
 
def check_zoom_opened(timeout=15):
    """Devuelve True si Zoom aparece en la lista de procesos dentro de 'timeout' segundos."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_zoom_running():
            return True
        time.sleep(1)
    return False
 
 
def focus_zoom_window(timeout=15, interval=1):
    """
    Busca la ventana principal de la reunión de Zoom (por su título) y la
    trae al frente, para asegurar que el teclado/mouse le llegan a Zoom y
    no a otra ventana que haya robado el foco (notificaciones, etc.).
    Devuelve True si la encontró y activó, False si no la encontró a tiempo.
    """
    print("     --Buscando y enfocando la ventana de Zoom.")
    start_time = time.time()
 
    while time.time() - start_time < timeout:
        for keyword in ZOOM_WINDOW_TITLE_KEYWORDS:
            windows = gw.getWindowsWithTitle(keyword)
            if windows:
                window = windows[0]
                try:
                    if window.isMinimized:
                        window.restore()
                    window.activate()
                except Exception:
                    pass
                time.sleep(0.5)
                print("     --Ventana de Zoom enfocada.")
                return True
        time.sleep(interval)
 
    print(Fore.RED + "     --No se encontró ninguna ventana de Zoom para enfocar." + Style.RESET_ALL)
    return False
 
 
def accept_recording_notice(timeout=20, interval=1):
    """
    Espera a que aparezca el aviso de grabación y lo acepta haciendo clic
    en su botón (buscado por reconocimiento de imagen), en vez de asumir
    que apareció y mandar un Enter a ciegas.
 
    Si no aparece dentro de 'timeout' segundos, se asume que esta reunión
    no lo mostró y se continúa sin marcar error.
 
    Requiere la imagen assets/aviso_grabacion_aceptar.png (un recorte del
    botón "Aceptar"/"Got it" del aviso, capturado en tu propia pantalla).
    """
    print("     --Esperando el aviso de grabación.")
    start_time = time.time()
    warned = False
 
    while time.time() - start_time < timeout:
        try:
            location = pyautogui.locateCenterOnScreen(
                'assets/aviso_grabacion_aceptar.png', confidence=0.7
            )
            if location:
                pyautogui.click(location)
                print(Fore.GREEN + "     --Aviso de grabación aceptado." + Style.RESET_ALL)
                return True
        except Exception as error:
            # Cualquier error al intentar reconocer la imagen en pantalla
            # (imagen no encontrada, falla de pyscreeze/Pillow, problema de
            # captura de pantalla, etc.) NO debe tirar abajo todo el script.
            # Lo tratamos como "no se pudo detectar todavía" y seguimos.
            if not warned:
                print(Fore.YELLOW + f"     --Aviso: no se pudo usar el reconocimiento de imagen ({error}). Reintentando..." + Style.RESET_ALL)
                warned = True
 
        time.sleep(interval)
 
    print(Fore.YELLOW + "     --No apareció el aviso de grabación (o no se detectó). Continuando." + Style.RESET_ALL)
    return False
 
"""
Envío del mensaje de presente por el chat de Zoom.
 
A diferencia de la versión original (que asumía a ciegas que el chat ya
estaba abierto y enfocado), acá cada paso se confirma antes de seguir:
  1. Se enfoca la ventana de Zoom explícitamente.
  2. Se abre el chat y se confirma que el campo de texto es visible.
  3. Se hace clic directo en el campo de texto (no se asume que el cursor
     ya está ahí).
  4. Si algo falla en el camino, se reintenta todo el proceso.
  5. Una vez enviado, se guarda una captura de pantalla como comprobante.
 
Requiere una imagen de referencia (capturada en tu propia pantalla),
guardada en la carpeta assets/:
  - assets/chat_input_box.png -> recorte del campo de texto del chat, vacío
"""
 
import os
import time
from datetime import datetime
 
import pyautogui
from colorama import Fore, Style
 
from zoom_connector import focus_zoom_window
 
CHAT_INPUT_IMAGE = "assets/chat_input_box.png"
SCREENSHOTS_DIR = "screenshots"
 
 
def _locate(image_path, confidence=0.7, timeout=10, interval=0.5):
    """Intenta localizar 'image_path' en pantalla hasta 'timeout' segundos."""
    start_time = time.time()
    warned = False
 
    while time.time() - start_time < timeout:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                return location
        except Exception as error:
            # Cualquier error al reconocer la imagen (no encontrada, falla
            # de pyscreeze/Pillow, etc.) se trata como "todavía no", nunca
            # como un crash del script.
            if not warned:
                print(Fore.YELLOW + f"     --Aviso: no se pudo usar el reconocimiento de imagen ({error}). Reintentando..." + Style.RESET_ALL)
                warned = True
 
        time.sleep(interval)
    return None
 
 
def _save_confirmation_screenshot(label="asistencia"):
    """
    Guarda una captura de pantalla completa como comprobante de que el
    mensaje se envió. El nombre incluye fecha y hora para poder revisar
    después qué pasó esa noche en particular.
    """
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
 
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_label = label.replace(" ", "_")
    filename = os.path.join(SCREENSHOTS_DIR, f"{safe_label}_{timestamp}.png")
 
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
 
    print(f"     --Captura de comprobante guardada en: {filename}")
    return filename
 
 
def open_chat_panel():
    """
    Abre el panel de chat y confirma (por imagen) que realmente se abrió,
    en vez de asumirlo con una espera fija.
    """
    print("     --Abriendo el panel de chat.")
 
    # Si ya está abierto (por ejemplo, de un intento anterior), no hace
    # falta volver a abrirlo.
    if _locate(CHAT_INPUT_IMAGE, timeout=2):
        print("     --El chat ya estaba abierto.")
        return True
 
    pyautogui.hotkey('alt', 'h')
 
    if _locate(CHAT_INPUT_IMAGE, timeout=10):
        print("     --Panel de chat confirmado (campo de texto visible).")
        return True
 
    print(Fore.RED + "     --No se pudo confirmar que el chat se haya abierto." + Style.RESET_ALL)
    return False
 
 
def send_zoom_message(message, label="asistencia", max_retries=3):
    """
    Envía 'message' por el chat de Zoom, con foco de ventana explícito,
    confirmación de que el chat está abierto, clic directo en el campo de
    texto y reintentos automáticos si algo falla en el camino.
 
    'label' se usa para nombrar el archivo de la captura de comprobante
    (por ejemplo, el día/materia: "Jueves").
    """
    for attempt in range(1, max_retries + 1):
        print(f"     --Intento {attempt}/{max_retries} de enviar el mensaje al chat.")
 
        if not focus_zoom_window():
            time.sleep(2)
            continue
 
        if not open_chat_panel():
            time.sleep(2)
            continue
 
        input_box = _locate(CHAT_INPUT_IMAGE, timeout=5)
        if not input_box:
            print(Fore.RED + "     --No se encontró el campo de texto del chat." + Style.RESET_ALL)
            time.sleep(2)
            continue
 
        # Clic directo en el campo para asegurar que el cursor está ahí
        # (no asumimos que ya estaba enfocado).
        pyautogui.click(input_box)
        time.sleep(0.3)
 
        pyautogui.write(message, interval=0.05)
        time.sleep(0.3)
        pyautogui.press('enter')
 
        # Pequeña espera para que el mensaje ya aparezca renderizado en el
        # chat antes de sacar la captura.
        time.sleep(1)
        _save_confirmation_screenshot(label=label)
 
        print(Fore.GREEN + "     --Mensaje enviado." + Style.RESET_ALL)
        return True
 
    print(Fore.RED + "     --No se pudo enviar el mensaje después de varios intentos." + Style.RESET_ALL)
    return False
 
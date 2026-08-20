"""
Funciones para evitar que la PC entre en suspensión mientras corre el script (Windows).
"""
 
import ctypes
 
from colorama import Fore, Style
 
 
def prevent_sleep():
    """Evita que la PC entre en suspensión durante la ejecución del script."""
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    # También podrías usar ES_DISPLAY_REQUIRED (0x00000002) si quieres mantener activo el monitor.
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    print(Fore.YELLOW + "\n-Se ha desactivado la suspensión del sistema.\n" + Style.RESET_ALL)
 
 
def allow_sleep():
    """Restablece la configuración para que la PC pueda entrar en suspensión."""
    ES_CONTINUOUS = 0x80000000
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    print(Fore.YELLOW + "\n-Se ha permitido la suspensión del sistema.\n" + Style.RESET_ALL)
 
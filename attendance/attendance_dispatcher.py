"""
Decide qué método de asistencia usar para una materia (según su "day")
y lo ejecuta, usando la configuración definida en ATTENDANCE_METHODS.
"""
 
from colorama import Fore, Style
 
from config import ATTENDANCE_METHODS
from attendance.chat_attendance import send_zoom_message
from attendance.form_attendance import fill_google_form
 
 
def give_attendance(day):
    """Busca el método de asistencia configurado para 'day' y lo ejecuta."""
    attendance = ATTENDANCE_METHODS.get(day)
 
    if not attendance:
        print(Fore.RED + f"     --No hay método de asistencia configurado para '{day}'." + Style.RESET_ALL)
        return
 
    method = attendance.get("method")
 
    if method == "chat":
        send_zoom_message(attendance["message"], label=day)
 
    elif method == "form":
        fill_google_form(attendance["form_url"], attendance.get("form_data", {}))
 
    else:
        print(Fore.RED + f"     --Método de asistencia desconocido: '{method}'." + Style.RESET_ALL)
 
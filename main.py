"""
Punto de entrada del proyecto.
 
Para cada materia definida en config.py:
  1. Espera hasta POLL_LEAD_MINUTES antes del horario de inicio.
  2. A partir de ahí, revisa periódicamente el campus buscando el link real
     de Zoom de la clase de hoy (por si el profesor lo publica tarde).
  3. En cuanto aparece, se conecta y da la asistencia con el método que
     corresponda según el día de la materia.
"""
 
import time
import webbrowser
 
from colorama import init, Fore, Style
 
from config import (
    EVENTS,
    MOODLE_BASE_URL,
    POLL_LEAD_MINUTES,
    POLL_INTERVAL_SECONDS,
    POLL_MAX_MINUTES_AFTER_START,
)
from credentials import MOODLE_USERNAME, MOODLE_PASSWORD
from time_utils import time_to_minutes, get_current_minutes, subtract_minutes
from system_utils import prevent_sleep, allow_sleep
from zoom_connector import (
    extract_meeting_info,
    close_zoom,
    check_zoom_opened,
    accept_recording_notice,
)
from attendance.attendance_dispatcher import give_attendance
from moodle_scraper import login, get_todays_zoom_link, today_weekday_name, normalize_day_name
 
init()  # Inicializa colorama
 
 
def wait_for_time(target_time_str):
    """Espera (bloqueando) hasta que el reloj del sistema marque target_time_str (HH:MM)."""
    while True:
        current_time = time.strftime("%H:%M")
        if current_time == target_time_str:
            return
        time.sleep(10)
 
 
def wait_for_zoom_link(session, course_url, start_minutes):
    """
    Sondea el campus hasta encontrar el link real de Zoom de la clase de hoy.
    Deja de intentar después de POLL_MAX_MINUTES_AFTER_START minutos desde el
    horario de inicio. Devuelve el link, o None si se agotó el tiempo.
    """
    deadline_minutes = start_minutes + POLL_MAX_MINUTES_AFTER_START
 
    while True:
        current_minutes = get_current_minutes()
        if current_minutes < start_minutes:
            current_minutes += 24 * 60
 
        zoom_link = get_todays_zoom_link(session, course_url)
        if zoom_link:
            return zoom_link
 
        if current_minutes >= deadline_minutes:
            return None
 
        print("     --El link de Zoom todavía no fue publicado. Reintentando...")
        time.sleep(POLL_INTERVAL_SECONDS)
 
 
def run():
    try:
        # Evitar suspensión mientras el script se ejecuta.
        prevent_sleep()
 
        # El login al campus se hace de forma perezosa: solo si algún evento
        # realmente necesita scrapear el link (no tiene un "zoom_link" fijo
        # configurado en config.py). Así, correr eventos de prueba con link
        # fijo no requiere loguearse al campus.
        session = None
 
        # Solo procesamos la(s) materia(s) cuyo "day" coincide con el día de
        # HOY (en Argentina). Sin este filtro, el script intentaría conectarse
        # a TODAS las materias configuradas todas las noches, sin importar
        # qué día es.
        today_name = today_weekday_name()
        today_normalized = normalize_day_name(today_name)
        todays_events = [
            event for event in EVENTS
            if normalize_day_name(event["day"]) == today_normalized
        ]
 
        if not todays_events:
            print(Fore.YELLOW + f"\n-Hoy es {today_name} y no hay ninguna materia configurada para ese día. No hay nada que hacer.\n" + Style.RESET_ALL)
            return
 
        print(Fore.CYAN + f"\n-Hoy es {today_name}. Materias a procesar: {[e['day'] for e in todays_events]}\n" + Style.RESET_ALL)
 
        for event in todays_events:
            day = event["day"]
            course_url = event["course_url"]
            start_time = event["start_time"]
            end_time = event["end_time"]
            message_time = event["message_time"]
 
            start_minutes = time_to_minutes(start_time)
            end_minutes = time_to_minutes(end_time)
            message_minutes = time_to_minutes(message_time)
 
            # Ajuste por cambio de día
            if message_minutes < start_minutes:
                message_minutes += 24 * 60
 
            fixed_zoom_link = event.get("zoom_link")
 
            if fixed_zoom_link:
                # Link fijo configurado a mano: no hace falta scrapear el
                # campus (ni loguearse), directamente esperamos la hora de
                # inicio y usamos este link tal cual.
                print(Fore.CYAN + f"\n-'{day}' tiene un link fijo configurado. Se omite la búsqueda en el campus.\n" + Style.RESET_ALL)
                wait_for_time(start_time)
                zoom_link = fixed_zoom_link
 
            else:
                # Sin link fijo: hay que loguearse al campus (una sola vez
                # para toda la ejecución) y sondear hasta que aparezca.
                if session is None:
                    print(Fore.CYAN + "\n-Iniciando sesión en el campus virtual.\n" + Style.RESET_ALL)
                    session = login(MOODLE_USERNAME, MOODLE_PASSWORD, MOODLE_BASE_URL)
 
                poll_start_time = subtract_minutes(start_time, POLL_LEAD_MINUTES)
 
                print(Fore.CYAN + f"\n-Esperando para buscar el link de '{day}' a partir de las {poll_start_time}.\n" + Style.RESET_ALL)
                wait_for_time(poll_start_time)
 
                print(Fore.MAGENTA + f"    -Buscando el link de Zoom de '{day}'." + Style.RESET_ALL)
                zoom_link = wait_for_zoom_link(session, course_url, start_minutes)
 
                if not zoom_link:
                    print(Fore.RED + f"     --No se encontró el link de Zoom de '{day}' a tiempo. Saltando esta materia." + Style.RESET_ALL)
                    continue
 
            event_type, event_id, event_key = extract_meeting_info(zoom_link)
            if not event_id or not event_key:
                print(Fore.RED + f"    -Error: el link encontrado para '{day}' no tiene un formato válido: {zoom_link}" + Style.RESET_ALL)
                continue
 
            print("    -Uniéndose a " + Fore.MAGENTA + f"'{day}' ({event_type.upper()})." + Style.RESET_ALL)
            webbrowser.open(zoom_link)
            time.sleep(10)
 
            # Aceptar la notificación de grabación
            accept_recording_notice()
            time.sleep(10)
 
            # Verificar si Zoom realmente se abrió
            if check_zoom_opened(timeout=10):
                print(Fore.GREEN + "     --Zoom se abrió correctamente." + Style.RESET_ALL)
            else:
                print(Fore.RED + "     --Error: Zoom no se abrió. Pasando a la siguiente materia." + Style.RESET_ALL)
                continue
 
            # ===== ESPERAR Y DAR ASISTENCIA =====
            attendance_given = False
            while True:
                current_minutes = get_current_minutes()
 
                if current_minutes < start_minutes:
                    current_minutes += 24 * 60
 
                if not attendance_given and current_minutes >= message_minutes:
                    give_attendance(day)
                    attendance_given = True
                    break
 
                time.sleep(5)
 
            if end_minutes < start_minutes:
                # Se asume que la reunión finaliza al día siguiente
                end_minutes += 24 * 60
 
            current_minutes = get_current_minutes()
 
            if current_minutes < start_minutes:
                current_minutes += 24 * 60
 
            remaining_minutes = end_minutes - current_minutes
            duration = remaining_minutes * 60
 
            if duration < 0:
                print(Fore.RED + f"-Error en '{day}': la hora de fin ({end_time}) es menor que la de inicio ({start_time}). Corrigiendo." + Style.RESET_ALL)
                duration = 0
 
            print(f"     --Permaneciendo en '{day}' durante {duration // 60} minutos.")
            time.sleep(duration)
 
            # Salir de Zoom automáticamente
            close_zoom()
 
        print(Fore.CYAN + "\n-Se han completado todos los eventos.\n" + Style.RESET_ALL)
 
    finally:
        # Permitir nuevamente que la PC se suspenda
        allow_sleep()
 
 
if __name__ == "__main__":
    run()
 
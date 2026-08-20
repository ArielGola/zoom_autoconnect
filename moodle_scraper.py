"""
Scraper del campus virtual (Moodle) de la UTN.
 
Se encarga de:
  1. Iniciar sesión a través del SSO (Keycloak).
  2. Buscar, dentro de la página de una materia, la actividad de Zoom
     correspondiente a la clase de HOY.
  3. Extraer el link real de Zoom (el que empieza con https://...zoom.us/...)
     desde adentro de esa actividad.
 
Todo esto se hace con 'requests' (sin abrir un navegador), porque las páginas
del campus son HTML renderizado por el servidor y no necesitan JavaScript
para mostrar esta información.
"""
 
import html
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo
 
import requests
from colorama import Fore, Style
 
# Zona horaria de Argentina: las fechas que muestra el campus están en esta
# zona, sin importar en qué zona horaria esté corriendo el script (ej. Italia).
ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
 
WEEKDAYS_ES = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo",
}
 
MONTHS_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre",
    11: "Noviembre", 12: "Diciembre",
}
 
 
def today_in_argentina():
    """Devuelve el datetime actual en la zona horaria de Argentina."""
    return datetime.now(ARGENTINA_TZ)
 
 
def normalize_day_name(day_name):
    """
    Quita tildes y pasa a minúsculas, para poder comparar nombres de día
    sin depender de mayúsculas ni tildes (ej. "Miércoles" == "miercoles").
    """
    nfkd = unicodedata.normalize("NFKD", day_name)
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return without_accents.strip().lower()
 
 
def today_weekday_name():
    """Devuelve el nombre del día de la semana de HOY en Argentina (ej. 'Jueves')."""
    return WEEKDAYS_ES[today_in_argentina().weekday()]
 
 
def format_spanish_date(dt):
    """Convierte un datetime al formato que usa el campus: 'Jueves, 06 de Agosto de 2026'."""
    weekday = WEEKDAYS_ES[dt.weekday()]
    month = MONTHS_ES[dt.month]
    return f"{weekday}, {dt.day:02d} de {month} de {dt.year}"
 
 
def login(username, password, moodle_base_url):
    """
    Inicia sesión en el campus a través del SSO de Keycloak.
    Devuelve una requests.Session ya autenticada (con las cookies necesarias).
    """
    session = requests.Session()
 
    # Muchos servidores (y sistemas anti-bots) bloquean o responden distinto
    # a pedidos sin un User-Agent de navegador real. Simulamos uno.
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "es-ES,es;q=0.9",
    })
 
    # Pedimos una página que requiere estar logueado (el panel "Mis cursos").
    # Moodle nos devuelve su propia pantalla de login (no redirige solo),
    # pero esa pantalla trae un link al plugin auth_oauth2 que sí dispara
    # el redirect real hacia el SSO de Keycloak.
    login_page = session.get(f"{moodle_base_url}/my/")
 
    sso_link_match = re.search(
        r'href="([^"]*auth/oauth2/login\.php\?[^"]*)"',
        login_page.text,
    )
    if not sso_link_match:
        debug_file = "debug_login_page.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(login_page.text)
 
        raise RuntimeError(
            "No se encontró el link de login SSO (auth/oauth2/login.php).\n"
            f"     --Código de estado HTTP: {login_page.status_code}\n"
            f"     --URL final después de los redirects: {login_page.url}\n"
            f"     --Guardé la página recibida en '{debug_file}' para poder revisarla."
        )
 
    sso_link = html.unescape(sso_link_match.group(1))
 
    # Seguimos ese link: acá sí nos termina redirigiendo a la página de
    # login de Keycloak (con su formulario kc-form-login).
    keycloak_page = session.get(sso_link)
 
    match = re.search(
        r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"',
        keycloak_page.text,
    )
    if not match:
        # Guardamos lo que realmente devolvió el servidor para poder
        # diagnosticar qué página es (¿otra pantalla intermedia?
        # ¿un bloqueo anti-bot? ¿cambió el formulario?).
        debug_file = "debug_keycloak_page.html"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(keycloak_page.text)
 
        raise RuntimeError(
            "No se encontró el formulario de login (kc-form-login).\n"
            f"     --Código de estado HTTP: {keycloak_page.status_code}\n"
            f"     --URL final después de los redirects: {keycloak_page.url}\n"
            f"     --Guardé la página recibida en '{debug_file}' para poder revisarla."
        )
 
    action_url = html.unescape(match.group(1))
 
    login_response = session.post(
        action_url,
        data={"username": username, "password": password},
    )
 
    # Si después de enviar el form seguimos viendo el formulario de login,
    # las credenciales fallaron (o cambió algo en la página).
    if "kc-form-login" in login_response.text:
        raise RuntimeError(
            "Login fallido: usuario/contraseña incorrectos, o la página de login cambió."
        )
 
    print(Fore.GREEN + "     --Sesión iniciada correctamente en el campus." + Style.RESET_ALL)
    return session
 
 
def find_zoom_activity_url(session, course_url, expected_date_str):
    """
    Busca, dentro de la página de la materia, la actividad de Zoom cuyo título
    contiene la fecha esperada (ej. 'Jueves, 06 de Agosto de 2026').
    Devuelve la URL de esa actividad (mod/zoomutnba/view.php?id=...) o None si
    todavía no fue publicada.
    """
    response = session.get(course_url)
 
    # Cada actividad de Zoom es un <li class="activity zoomutnba ..."> que
    # contiene un <a class="aalink" href="...mod/zoomutnba/view.php?id=NNN">
    # con el título de la clase adentro (<span class="instancename">).
    # Nota: <span class="instancename"> tiene adentro otro <span class="accesshide">
    # (texto para lectores de pantalla) antes de cerrarse, por eso no anclamos contra
    # el "</span>" de cierre: solo capturamos el texto hasta la primera etiqueta.
    pattern = re.compile(
        r'<a class="aalink"[^>]*href="([^"]*mod/zoomutnba/view\.php\?id=\d+)"[^>]*>.*?'
        r'<span class="instancename">([^<]*)',
        re.DOTALL,
    )
 
    for activity_url, title in pattern.findall(response.text):
        if expected_date_str in title:
            return html.unescape(activity_url)
 
    return None
 
 
def extract_real_zoom_link(session, activity_url):
    """
    Entra a la página de la actividad y extrae el link real de Zoom
    (el que aparece en el link 'Si no puedes ingresar, cliclea aqui!').
    """
    response = session.get(activity_url)
 
    match = re.search(r"href=['\"]([^'\"]*zoom\.us[^'\"]*)['\"]", response.text)
    if not match:
        return None
 
    return html.unescape(match.group(1))
 
 
def get_todays_zoom_link(session, course_url):
    """
    Combina todo: busca la actividad de hoy y extrae su link real de Zoom.
    Devuelve None si la clase de hoy todavía no fue publicada.
    """
    expected_date_str = format_spanish_date(today_in_argentina())
 
    activity_url = find_zoom_activity_url(session, course_url, expected_date_str)
    if not activity_url:
        return None
 
    return extract_real_zoom_link(session, activity_url)
 
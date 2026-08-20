"""
Configuración central del proyecto — PLANTILLA.
 
Copiá este archivo como 'config.py' (que está en .gitignore, así que tus
datos reales nunca se suben al repositorio) y completá con tus propios
valores.
 
EVENTS define el cronograma: a qué materia conectarse, cuándo, y en qué
página del campus buscar el link de Zoom. El campo "day" identifica a la
materia y sirve como clave para buscar en ATTENDANCE_METHODS cómo dar la
asistencia en esa clase. Debe coincidir con el día de la semana real
("Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"
— con o sin tildes, no importa).
 
Cada evento admite un campo opcional "zoom_link": si se completa con un
link real de Zoom, se usa directamente y NO se hace scraping al campus
(ni falta loguearse). Sirve para:
  - Testing rápido de una materia sin depender del campus ni del horario.
  - Materias donde el link ya se conoce de antemano (siempre el mismo,
    o publicado con mucha anticipación).
Dejalo en None para que busque el link automáticamente.
 
ATTENDANCE_METHODS define, por día/materia, qué método de asistencia usar:
  - "chat": envía un mensaje de texto por el chat de Zoom (nombre + documento)
  - "form": completa un Google Form (link fijo) — pendiente de implementar
"""
 
# URL base de tu campus virtual (Moodle).
MOODLE_BASE_URL = "https://tu-campus.ejemplo.edu"
 
# Cuántos minutos antes del horario de inicio empezar a buscar el link de Zoom.
POLL_LEAD_MINUTES = 15
 
# Cada cuántos segundos reintentar la búsqueda del link mientras no aparece.
POLL_INTERVAL_SECONDS = 20
 
# Si pasado el inicio de la clase el link sigue sin aparecer, dejar de
# intentar después de esta cantidad de minutos (red de seguridad).
POLL_MAX_MINUTES_AFTER_START = 20
 
# Cronograma de materias/reuniones.
EVENTS = [
    {
        "day": "Miercoles",                 # IDENTIFICA LA MATERIA
        "course_url": "https://tu-campus.ejemplo.edu/course/view.php?id=000&section=0",
        "zoom_link": None,                  # Opcional: si se completa, se salta el scraping
        "start_time": "20:00",              # Horario de inicio, hora local de tu PC
        "end_time": "22:00",                # Horario de fin
        "message_time": "20:30",            # Hora a la que se da presente
    },
    {
        "day": "Jueves",
        "course_url": "https://tu-campus.ejemplo.edu/course/view.php?id=000&section=0",
        "zoom_link": None,
        "start_time": "20:00",
        "end_time": "22:00",
        "message_time": "20:30",
    },
]
 
# Método de asistencia por materia (según el "day" del evento).
ATTENDANCE_METHODS = {
    "Miercoles": {
        "method": "chat",
        "message": "Nombre Apellido - 12345678",  # nombre + número de documento
    },
    "Jueves": {
        "method": "form",
        "form_url": "https://forms.gle/xxxxxxxx",
        "form_data": {
            # Pendiente: form_attendance.py todavía no está implementado.
        },
    },
}
 
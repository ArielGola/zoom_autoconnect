"""
Funciones utilitarias para trabajar con horas y minutos.
"""
 
import time
 
 
def time_to_minutes(hour_str):
    """Convierte una hora 'HH:MM' a minutos totales desde las 00:00."""
    h, m = map(int, hour_str.split(":"))
    return h * 60 + m
 
 
def get_current_minutes():
    """Devuelve la hora actual del sistema en minutos totales desde las 00:00."""
    now = time.localtime()
    return now.tm_hour * 60 + now.tm_min
 
 
def subtract_minutes(hour_str, minutes_to_subtract):
    """
    Resta minutos a una hora 'HH:MM' y devuelve el resultado como 'HH:MM'.
    Ajusta correctamente si el resultado cruza la medianoche hacia atrás
    (ej. subtract_minutes("00:02", 15) -> "23:47").
    """
    total = time_to_minutes(hour_str) - minutes_to_subtract
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"
 
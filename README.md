# Zoom Autoconnect

Bot personal que se conecta automáticamente a mis clases de Zoom aunque yo esté durmiendo.

## El problema que resuelve

Vivo en Italia y curso una carrera a distancia en Argentina. La diferencia horaria hace que algunas clases empiecen a la 1 o 2 de la madrugada, hora local — imposible de sostener despierto de forma sostenida. Este proyecto automatiza todo el proceso para que la clase quede "atendida" mientras duermo, y yo recupero el contenido después con la grabación.

## Qué hace

- **Detecta el día de la semana** y sabe qué materia corresponde conectar.
- **Scrapea el campus virtual (Moodle)** buscando el link real de Zoom de la clase de hoy — incluso cuando el profesor lo publica recién unos minutos antes de que empiece (algo frecuente y que rompía cualquier automatización con horario fijo).
- **Se loguea al campus por SSO (Keycloak)** de forma automática.
- **Se conecta a la reunión** usando la app de escritorio de Zoom.
- **Acepta el aviso de grabación** por reconocimiento de imagen.
- **Da presente automáticamente** por el chat de Zoom (nombre + documento), con verificación de cada paso y reintentos si algo falla.
- **Guarda una captura de pantalla** como comprobante después de cada asistencia, para poder revisar a la mañana siguiente qué pasó.
- **Se desconecta sola** al finalizar el horario de la clase.

Cada materia puede tener un método de asistencia distinto (algunas piden un mensaje en el chat, otras un Google Form) — el sistema elige el método correcto según la materia del día.

## Cómo está armado

```
zoom_autoconnect/
├── main.py                          # orquesta todo el flujo, noche a noche
├── config.example.py                # plantilla de configuración (copiar a config.py)
├── credentials.example.py           # plantilla de credenciales (copiar a credentials.py)
├── moodle_scraper.py                # login SSO + scraping del campus (Moodle)
├── zoom_connector.py                # conexión, foco de ventana y control de Zoom
├── time_utils.py                    # utilidades de horarios
├── system_utils.py                  # evitar que la PC se suspenda
├── requirements.txt
├── assets/                          # capturas de referencia para reconocimiento de imagen
└── attendance/
    ├── attendance_dispatcher.py     # elige el método de asistencia según la materia
    ├── chat_attendance.py           # asistencia por chat de Zoom
    └── form_attendance.py           # asistencia por Google Form (pendiente)
```

## Instalación

1. Cloná el repositorio e instalá las dependencias:
   ```
   pip install -r requirements.txt
   ```

2. Copiá los archivos de configuración de ejemplo y completalos con tus datos:
   ```
   cp config.example.py config.py
   cp credentials.example.py credentials.py
   ```
   (Ambos quedan fuera del control de versiones — están en `.gitignore` — así que tus datos nunca se suben a ningún repo.)

3. En `config.py`, completá:
   - La URL de tu campus virtual
   - Tus materias, con sus horarios y el link a la página del curso
   - El método de asistencia de cada una

4. En `credentials.py`, completá tu usuario y contraseña del campus.

5. Capturá tus propias imágenes de referencia (necesarias porque `pyautogui` compara contra pixeles reales de tu pantalla, no genéricos) y guardalas en `assets/`:
   - `chat_input_box.png`: recorte ajustado del campo de texto vacío del chat de Zoom
   - `aviso_grabacion_aceptar.png`: recorte ajustado del botón "Aceptar" del aviso de grabación

6. Corré el script:
   ```
   python main.py
   ```

## Sobre cómo se hizo este proyecto

Este proyecto fue programado en su totalidad por **Claude (Anthropic)**, en una sesión de trabajo conversacional. Mi rol fue el de definir el problema, aportar el contexto real (capturas de pantalla, HTML de las páginas involucradas, comportamiento real observado), tomar las decisiones de diseño cuando había una disyuntiva (por ejemplo: app de escritorio vs. navegador para Zoom), y testear cada iteración hasta que funcionó de punta a punta.

Ninguna línea de código de este repositorio la escribí yo a mano. Lo que aporté fue la supervisión: verificar que cada pieza funcionara con datos reales, reportar los errores exactos que aparecían, y decidir qué camino tomar en cada punto de ambigüedad.

Creo que vale la pena decirlo explícitamente, no como descargo sino porque me parece una demostración honesta de cómo cambió el proceso de programar: cada vez menos "escribir cada línea" y cada vez más "definir el problema, supervisar, testear, iterar".

## Advertencia

Este proyecto automatiza el registro de asistencia sin presencia real y efectiva durante la clase en vivo (la idea es recuperar el contenido después, vía la grabación). Antes de usar algo así, vale la pena que revises el reglamento de tu institución — lo que es razonable para mi situación particular puede no serlo para la tuya, y el código en sí no te exime de esa responsabilidad.

## Licencia

MIT — ver [LICENSE](LICENSE).

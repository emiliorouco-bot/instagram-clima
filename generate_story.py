import os
import json
import datetime
import calendar
import requests
from html2image import Html2Image

# ---------------------------------------------------------
# 1. CONFIGURACIÓN Y API KEY
# ---------------------------------------------------------
API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
CITY = "La Plata,AR"
URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=es"
URL_PRONOSTICO = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric&lang=es"
HISTORIAL_FILE = "historial_clima.json"
FRASES_HISTORIAL_FILE = "historial_frases.json"

# ---------------------------------------------------------
# CITAS DE ARQUITECTOS
# Frases cortas y verificadas en varias fuentes. Cada 5 citas de
# arquitectos aparece una "descontracture".
# ---------------------------------------------------------
CITAS_ARQUITECTOS = [
    {"texto": "La luz construye el tiempo.", "autor": "Alberto Campo Baeza"},
    {"texto": "La luz es el material más lujoso que existe.", "autor": "Alberto Campo Baeza"},
    {"texto": "El espacio debe ser el resultado de la luz, no de la oscuridad.", "autor": "Luis Barragán"},
    {"texto": "Cualquier obra arquitectónica que no exprese serenidad, es un error.", "autor": "Luis Barragán"},
    {"texto": "La forma sigue a la función, pero sigue siendo la forma.", "autor": "Kenzo Tange"},
    {"texto": "La arquitectura no es una cuestión de estilo, es una cuestión de ideas.", "autor": "Oscar Niemeyer"},
    {"texto": "Lo que me atrae es la curva libre y sensual.", "autor": "Oscar Niemeyer"},
    {"texto": "Si se ignora al hombre, la arquitectura es innecesaria.", "autor": "Álvaro Siza"},
    {"texto": "La arquitectura no es un arte.", "autor": "Jacques Herzog"},
    {"texto": "Toca la tierra ligeramente.", "autor": "Glenn Murcutt"},
    {"texto": "La sustentabilidad se ha transformado en una frase hecha.", "autor": "Glenn Murcutt"},
    {"texto": "Poder hacer una cosa no legitima hacerla.", "autor": "Glenn Murcutt"},
    {"texto": "Todo lo que tiene aire acondicionado es porque está construido al revés.", "autor": "Glenn Murcutt"},
    {"texto": "Elijo geometrías simples para crear juegos dramáticos de luz y sombra.", "autor": "Tadao Ando"},
]

# ---------------------------------------------------------
# DESCONTRACTURE
# Aparece 1 de cada 5 veces, para bajarle el tono solemne.
# ---------------------------------------------------------
CITAS_DESCONTRACTURE = [
    {"texto": "¡A la grande le puse Cuca!", "autor": "Homero Simpson"},
    {"texto": "¡No vives de ensalada!", "autor": "Homero Simpson"},
    {"texto": "Sin tele y sin cerveza, Homero pierde la cabeza.", "autor": "Homero Simpson"},
    {"texto": "Yo no leo a Borges, no leo a Cortázar, leo a Sbaraglia y nada más.", "autor": "Homero Simpson"},
]

def elegir_frase():
    """Elige una cita: 4 de cada 5 veces de arquitectos, 1 de cada 5
    descontracture. No repite hasta agotar el banco correspondiente."""
    import random

    estado = {"usadas_arq": [], "usadas_descontr": [], "contador": 0}
    if os.path.exists(FRASES_HISTORIAL_FILE):
        with open(FRASES_HISTORIAL_FILE, "r", encoding="utf-8") as f:
            try:
                estado = json.load(f)
            except Exception:
                pass

    estado["contador"] = estado.get("contador", 0) + 1
    es_descontracture = (estado["contador"] % 5 == 0)
    banco = CITAS_DESCONTRACTURE if es_descontracture else CITAS_ARQUITECTOS
    clave_usadas = "usadas_descontr" if es_descontracture else "usadas_arq"

    ya_usadas = estado.get(clave_usadas, [])
    disponibles = [c for c in banco if c["texto"] not in ya_usadas]
    if not disponibles:
        disponibles = banco
        ya_usadas = []

    elegida = random.choice(disponibles)
    ya_usadas.append(elegida["texto"])
    estado[clave_usadas] = ya_usadas

    with open(FRASES_HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)

    return elegida

# ---------------------------------------------------------
# ÍCONOS DE CLIMA
# Rediseñados con más detalle para que se lean bien incluso
# chicos, sobre todo nublado y lluvia (antes eran una sola
# forma difusa).
# ---------------------------------------------------------
SVG_ICONS = {
    "sol": '''<svg viewBox="0 0 100 100" width="52">
      <circle cx="50" cy="50" r="22" fill="#eab308"/>
      <g stroke="#eab308" stroke-width="6" stroke-linecap="round">
        <line x1="50" y1="8" x2="50" y2="20"/>
        <line x1="50" y1="80" x2="50" y2="92"/>
        <line x1="8" y1="50" x2="20" y2="50"/>
        <line x1="80" y1="50" x2="92" y2="50"/>
        <line x1="20" y1="20" x2="28" y2="28"/>
        <line x1="72" y1="72" x2="80" y2="80"/>
        <line x1="80" y1="20" x2="72" y2="28"/>
        <line x1="28" y1="72" x2="20" y2="80"/>
      </g>
    </svg>''',
    "nublado": '''<svg viewBox="0 0 100 100" width="56">
      <circle cx="38" cy="55" r="17" fill="#d4d4d8"/>
      <circle cx="58" cy="45" r="21" fill="#d4d4d8"/>
      <circle cx="74" cy="55" r="15" fill="#d4d4d8"/>
      <rect x="32" y="53" width="47" height="24" rx="12" fill="#d4d4d8"/>
    </svg>''',
    "lluvia": '''<svg viewBox="0 0 100 100" width="56">
      <circle cx="35" cy="42" r="15" fill="#71717a"/>
      <circle cx="53" cy="34" r="19" fill="#71717a"/>
      <circle cx="68" cy="42" r="13" fill="#71717a"/>
      <rect x="30" y="40" width="43" height="21" rx="10" fill="#71717a"/>
      <g fill="#38bdf8">
        <path d="M 38 68 C 34 74, 34 80, 38 84 C 42 80, 42 74, 38 68 Z"/>
        <path d="M 55 72 C 51 78, 51 84, 55 88 C 59 84, 59 78, 55 72 Z"/>
        <path d="M 70 68 C 66 74, 66 80, 70 84 C 74 80, 74 74, 70 68 Z"/>
      </g>
    </svg>'''
}

def obtener_clima():
    """Consulta el clima actual (para viento) y el pronóstico de lo que
    resta del día (para decidir si hoy es un día de lluvia, en vez de
    mirar solo el instante exacto en que corre el script).
    Devuelve (tipo_clima, viento_kmh)."""
    try:
        res = requests.get(URL).json()
        main_weather_ahora = res['weather'][0]['main'].lower()
        viento_ms = res.get('wind', {}).get('speed', 0.0)
        viento_kmh = round(viento_ms * 3.6, 1)
    except Exception as e:
        print(f"Error consultando el clima actual: {e}. Se usará 'sol' por defecto.")
        return "sol", 0.0

    tipos_lluvia = ('rain', 'drizzle', 'thunderstorm')
    hay_lluvia_hoy = any(t in main_weather_ahora for t in tipos_lluvia)

    # Reviso el pronóstico de lo que resta del día de hoy: si en
    # cualquier franja horaria está previsto lluvia, marco el día
    # como lluvia, aunque en este instante puntual esté despejado.
    try:
        hoy_str = datetime.datetime.now().strftime("%Y-%m-%d")
        pronostico = requests.get(URL_PRONOSTICO).json()
        for franja in pronostico.get('list', []):
            if franja.get('dt_txt', '').startswith(hoy_str):
                main_franja = franja['weather'][0]['main'].lower()
                if any(t in main_franja for t in tipos_lluvia):
                    hay_lluvia_hoy = True
                    break
    except Exception as e:
        print(f"Error consultando el pronóstico: {e}. Sigo solo con el clima actual.")

    if hay_lluvia_hoy:
        tipo = "lluvia"
    elif 'clear' in main_weather_ahora:
        tipo = "sol"
    else:
        tipo = "nublado"

    return tipo, viento_kmh

def gestionar_historial(today, tipo_clima):
    historial = {}
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            try:
                historial = json.load(f)
            except Exception:
                historial = {}

    fecha_key = today.strftime("%Y-%m-%d")
    historial[fecha_key] = tipo_clima

    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2)

    return historial

def contar_dias_lluvia_mes(historial, today):
    """Cuenta cuántos días del mes en curso están marcados como 'lluvia'
    en el historial del calendario — dato que ya se guarda siempre bien,
    a diferencia de un total de milímetros."""
    prefijo_mes = today.strftime("%Y-%m")
    return sum(1 for k, v in historial.items() if k.startswith(prefijo_mes) and v == "lluvia")

def calcular_progreso_año(today):
    dia_del_año = today.timetuple().tm_yday
    total_dias = 366 if calendar.isleap(today.year) else 365
    return round((dia_del_año / total_dias) * 100, 1)

def generar_filas_calendario(today, historial):
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(today.year, today.month)

    rows_html = ""
    for week in month_days:
        rows_html += "<tr>"
        for day in week:
            if day == 0:
                rows_html += "<td></td>"
            else:
                fecha_str = f"{today.year}-{today.month:02d}-{day:02d}"
                tipo_clima = historial.get(fecha_str)
                icon_svg = SVG_ICONS.get(tipo_clima, "") if tipo_clima else ""

                if day == today.day:
                    rows_html += f'''
                    <td>
                      <div class="today-cell-box">
                        <span class="day-number">{day}</span>
                        <div class="day-icon">{icon_svg}</div>
                      </div>
                    </td>'''
                else:
                    rows_html += f'''
                    <td>
                      <span class="day-number">{day}</span>
                      <div class="day-icon">{icon_svg}</div>
                    </td>'''
        rows_html += "</tr>"
    return rows_html

# ---------------------------------------------------------
# 2. GENERACIÓN DEL DISEÑO Y CONVERSIÓN A PNG
# ---------------------------------------------------------
today = datetime.datetime.now()
clima_actual, viento_kmh = obtener_clima()
historial = gestionar_historial(today, clima_actual)
progreso_año = calcular_progreso_año(today)
dias_lluvia_mes = contar_dias_lluvia_mes(historial, today)
frase_del_dia = elegir_frase()

meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
nombre_mes = meses_es[today.month - 1]

filas_calendario_html = generar_filas_calendario(today, historial)

html_final = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 0;
    width: 1080px; height: 1920px;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background-color: #000000;
    color: #ffffff;
    position: relative;
    overflow: hidden;
  }}
  .container {{ padding: 100px 50px 60px 50px; height: 100%; position: relative; z-index: 10; }}
  .header {{ text-align: center; margin-bottom: 30px; }}
  .month-title {{ font-size: 56pt; font-weight: 900; text-transform: uppercase; color: #ffffff; margin: 0; letter-spacing: 3px; }}
  .progress-card {{ background: #111111; border: 1px solid #27272a; border-radius: 20px; padding: 24px 30px; margin-bottom: 26px; }}
  .progress-header-table {{ width: 100%; margin-bottom: 16px; }}
  .progress-title {{ font-size: 18pt; font-weight: 700; color: #e4e4e7; text-align: left; }}
  .progress-value {{ font-size: 20pt; font-weight: 800; color: #eab308; text-align: right; }}
  .progress-bar-border {{ border: 3px solid #3f3f46; padding: 6px; background-color: #000000; border-radius: 8px; }}
  .progress-bar-bg {{ width: 100%; height: 36px; background-color: #18181b; position: relative; }}
  .progress-bar-fill {{ height: 100%; background-color: #eab308; }}
  .stats-card {{ background: #111111; border: 1px solid #27272a; border-radius: 20px; padding: 20px 30px; margin-bottom: 30px; }}
  .stats-row {{ width: 100%; }}
  .stats-col {{ text-align: center; width: 50%; }}
  .stats-value {{ font-size: 30pt; font-weight: 800; color: #38bdf8; }}
  .stats-label {{ font-size: 14pt; font-weight: 600; color: #a1a1aa; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
  .stats-divider {{ width: 1px; background: #27272a; }}
  .calendar-card {{ background: #09090b; border: 1px solid #27272a; border-radius: 28px; padding: 28px 25px; margin-bottom: 26px; }}
  .calendar-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
  .calendar-table th {{ font-size: 16pt; color: #71717a; padding-bottom: 25px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }}
  .calendar-table td {{ height: 122px; text-align: center; vertical-align: top; padding-top: 10px; border-top: 1px solid #18181b; position: relative; }}
  .day-number {{ font-size: 20pt; font-weight: 700; color: #f4f4f5; display: block; }}
  .today-cell-box {{ background: transparent; border: 3px solid #eab308; border-radius: 16px; padding: 6px 4px 4px 4px; margin: -4px auto 0 auto; width: 88%; box-shadow: 0 0 15px rgba(234, 179, 8, 0.3); }}
  .today-cell-box .day-number {{ color: #ffffff; font-weight: 900; }}
  .day-icon {{ height: 60px; text-align: center; margin-top: 6px; }}
  .quote-final {{ text-align: center; padding: 0 20px; }}
  .quote-final .quote-mark {{ font-family: Georgia, 'Times New Roman', serif; font-size: 54pt; font-weight: 900; color: #eab308; opacity: 0.5; line-height: 0.6; margin-bottom: 4px; }}
  .quote-final .quote-text {{ font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 23pt; font-weight: 500; color: #ffffff; line-height: 1.35; margin: 0; }}
  .quote-final .quote-author {{ font-size: 15pt; font-weight: 700; color: #eab308; text-transform: uppercase; letter-spacing: 1px; margin-top: 16px; }}
  .footer {{ text-align: center; font-size: 13pt; color: #52525b; font-weight: 500; margin-top: 22px; }}
  .footer .fuente {{ display: block; font-size: 11pt; color: #3f3f46; margin-top: 6px; }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 class="month-title">{nombre_mes.upper()} {today.year}</h1>
    </div>
    <div class="progress-card">
      <table class="progress-header-table">
        <tr>
          <td class="progress-title">Progreso del año {today.year}</td>
          <td class="progress-value">{progreso_año}%</td>
        </tr>
      </table>
      <div class="progress-bar-border">
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: {progreso_año}%;"></div>
        </div>
      </div>
    </div>
    <div class="stats-card">
      <table class="stats-row">
        <tr>
          <td class="stats-col">
            <div class="stats-value">{viento_kmh} km/h</div>
            <div class="stats-label">Viento hoy</div>
          </td>
          <td class="stats-divider"></td>
          <td class="stats-col">
            <div class="stats-value">{dias_lluvia_mes}</div>
            <div class="stats-label">Días de lluvia este mes</div>
          </td>
        </tr>
      </table>
    </div>
    <div class="calendar-card">
      <table class="calendar-table">
        <thead>
          <tr><th>Lun</th><th>Mar</th><th>Mié</th><th>Jue</th><th>Vie</th><th>Sáb</th><th>Dom</th></tr>
        </thead>
        <tbody>
          {filas_calendario_html}
        </tbody>
      </table>
    </div>
    <div class="quote-final">
      <div class="quote-mark">"</div>
      <p class="quote-text">{frase_del_dia['texto']}</p>
      <p class="quote-author">— {frase_del_dia['autor']}</p>
    </div>
  </div>
  <div class="footer">
    Sigue el clima diario en <span style="color: #eab308;">@emilio.rouco</span>
    <span class="fuente">Fuente: OpenWeatherMap — La Plata, Argentina</span>
  </div>
</body>
</html>"""

# Generar la imagen PNG directamente en formato 1080x1920
hti = Html2Image(
    size=(1080, 1920),
    custom_flags=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
)
hti.screenshot(html_str=html_final, save_as='instagram_story.png')

print("¡Imagen generada exitosamente como 'instagram_story.png'!")
print(f"Clima: {clima_actual} | Viento: {viento_kmh}km/h | Días de lluvia este mes: {dias_lluvia_mes}")

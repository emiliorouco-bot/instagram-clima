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
HISTORIAL_FILE = "historial_clima.json"
LLUVIA_HISTORIAL_FILE = "historial_lluvia.json"

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
    """Consulta el clima actual. Devuelve (tipo_clima, lluvia_mm).
    lluvia_mm es la lluvia registrada en la última hora al momento
    de la consulta (no un total exacto de las 24hs, limitación de
    la API gratuita de OpenWeatherMap)."""
    try:
        res = requests.get(URL).json()
        main_weather = res['weather'][0]['main'].lower()
        lluvia_mm = 0.0
        if 'rain' in res:
            lluvia_mm = res['rain'].get('1h', res['rain'].get('3h', 0.0))

        if 'clear' in main_weather:
            tipo = "sol"
        elif 'rain' in main_weather or 'drizzle' in main_weather or 'thunderstorm' in main_weather:
            tipo = "lluvia"
        else:
            tipo = "nublado"
        return tipo, round(lluvia_mm, 1)
    except Exception as e:
        print(f"Error consultando la API: {e}. Se usará 'sol' por defecto.")
        return "sol", 0.0

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

def gestionar_lluvia(today, lluvia_mm_hoy):
    """Guarda la lluvia del día y devuelve el acumulado del mes en curso."""
    historial = {}
    if os.path.exists(LLUVIA_HISTORIAL_FILE):
        with open(LLUVIA_HISTORIAL_FILE, "r", encoding="utf-8") as f:
            try:
                historial = json.load(f)
            except Exception:
                historial = {}

    fecha_key = today.strftime("%Y-%m-%d")
    historial[fecha_key] = lluvia_mm_hoy

    with open(LLUVIA_HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2)

    prefijo_mes = today.strftime("%Y-%m")
    acumulado_mes = round(sum(v for k, v in historial.items() if k.startswith(prefijo_mes)), 1)
    return acumulado_mes

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
clima_actual, lluvia_mm_hoy = obtener_clima()
historial = gestionar_historial(today, clima_actual)
progreso_año = calcular_progreso_año(today)
lluvia_acumulada_mes = gestionar_lluvia(today, lluvia_mm_hoy)

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
  .header {{ text-align: center; margin-bottom: 50px; }}
  .month-title {{ font-size: 56pt; font-weight: 900; text-transform: uppercase; color: #ffffff; margin: 0; letter-spacing: 3px; }}
  .progress-card {{ background: #111111; border: 1px solid #27272a; border-radius: 20px; padding: 30px; margin-bottom: 40px; }}
  .progress-header-table {{ width: 100%; margin-bottom: 16px; }}
  .progress-title {{ font-size: 18pt; font-weight: 700; color: #e4e4e7; text-align: left; }}
  .progress-value {{ font-size: 20pt; font-weight: 800; color: #eab308; text-align: right; }}
  .progress-bar-border {{ border: 3px solid #3f3f46; padding: 6px; background-color: #000000; border-radius: 8px; }}
  .progress-bar-bg {{ width: 100%; height: 36px; background-color: #18181b; position: relative; }}
  .progress-bar-fill {{ height: 100%; background-color: #eab308; }}
  .rain-card {{ background: #111111; border: 1px solid #27272a; border-radius: 20px; padding: 26px 30px; margin-bottom: 50px; }}
  .rain-row {{ width: 100%; }}
  .rain-col {{ text-align: center; width: 50%; }}
  .rain-value {{ font-size: 30pt; font-weight: 800; color: #38bdf8; }}
  .rain-label {{ font-size: 14pt; font-weight: 600; color: #a1a1aa; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
  .rain-divider {{ width: 1px; background: #27272a; }}
  .calendar-card {{ background: #09090b; border: 1px solid #27272a; border-radius: 28px; padding: 35px 25px; }}
  .calendar-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
  .calendar-table th {{ font-size: 16pt; color: #71717a; padding-bottom: 25px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }}
  .calendar-table td {{ height: 135px; text-align: center; vertical-align: top; padding-top: 10px; border-top: 1px solid #18181b; position: relative; }}
  .day-number {{ font-size: 20pt; font-weight: 700; color: #f4f4f5; display: block; }}
  .today-cell-box {{ background: transparent; border: 3px solid #eab308; border-radius: 16px; padding: 6px 4px 4px 4px; margin: -4px auto 0 auto; width: 88%; box-shadow: 0 0 15px rgba(234, 179, 8, 0.3); }}
  .today-cell-box .day-number {{ color: #ffffff; font-weight: 900; }}
  .day-icon {{ height: 60px; text-align: center; margin-top: 6px; }}
  .footer {{ position: absolute; bottom: 50px; left: 0; width: 100%; text-align: center; font-size: 14pt; color: #52525b; font-weight: 500; }}
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
    <div class="rain-card">
      <table class="rain-row">
        <tr>
          <td class="rain-col">
            <div class="rain-value">{lluvia_mm_hoy} mm</div>
            <div class="rain-label">Hoy</div>
          </td>
          <td class="rain-divider"></td>
          <td class="rain-col">
            <div class="rain-value">{lluvia_acumulada_mes} mm</div>
            <div class="rain-label">Acumulado del mes</div>
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
print(f"Clima: {clima_actual} | Lluvia hoy: {lluvia_mm_hoy}mm | Acumulado mes: {lluvia_acumulada_mes}mm")

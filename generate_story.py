import os
import json
import datetime
import calendar
import requests
from html2image import Html2Image

# ---------------------------------------------------------
# 1. CONFIGURACIÓN Y API KEY
# ---------------------------------------------------------
API_KEY = "b8dbb3cc91cdd2ac7cf5adae5dedbb2f"
CITY = "Buenos Aires"
URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=es"
HISTORIAL_FILE = "historial_clima.json"

SVG_ICONS = {
    "sol": '<svg viewBox="0 0 100 100" width="36"><circle cx="50" cy="50" r="28" fill="#eab308"/></svg>',
    "nublado": '''<svg viewBox="0 0 100 100" width="38">
      <path d="M 25 65 C 20 65, 15 55, 25 48 C 25 35, 45 30, 55 40 C 65 32, 85 40, 80 52 C 90 58, 85 65, 75 65 Z" fill="#a1a1aa"/>
    </svg>''',
    "lluvia": '''<svg viewBox="0 0 100 100" width="38">
      <path d="M 25 55 C 20 55, 15 45, 25 38 C 25 25, 45 20, 55 30 C 65 22, 85 30, 80 42 C 90 48, 85 55, 75 55 Z" fill="#71717a"/>
      <line x1="38" y1="62" x2="30" y2="78" stroke="#38bdf8" stroke-width="5" stroke-linecap="round"/>
      <line x1="58" y1="62" x2="50" y2="78" stroke="#38bdf8" stroke-width="5" stroke-linecap="round"/>
    </svg>'''
}

def obtener_clima():
    try:
        res = requests.get(URL).json()
        main_weather = res['weather'][0]['main'].lower()
        if 'clear' in main_weather:
            return "sol"
        elif 'rain' in main_weather or 'drizzle' in main_weather or 'thunderstorm' in main_weather:
            return "lluvia"
        else:
            return "nublado"
    except Exception as e:
        print(f"Error consultando la API: {e}. Se usará 'sol' por defecto.")
        return "sol"

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
clima_actual = obtener_clima()
historial = gestionar_historial(today, clima_actual)
progreso_año = calcular_progreso_año(today)

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
  .progress-card {{ background: #111111; border: 1px solid #27272a; border-radius: 20px; padding: 30px; margin-bottom: 50px; }}
  .progress-header-table {{ width: 100%; margin-bottom: 16px; }}
  .progress-title {{ font-size: 18pt; font-weight: 700; color: #e4e4e7; text-align: left; }}
  .progress-value {{ font-size: 20pt; font-weight: 800; color: #eab308; text-align: right; }}
  .progress-bar-border {{ border: 3px solid #3f3f46; padding: 6px; background-color: #000000; border-radius: 8px; }}
  .progress-bar-bg {{ width: 100%; height: 36px; background-color: #18181b; position: relative; }}
  .progress-bar-fill {{ height: 100%; background-color: #eab308; }}
  .calendar-card {{ background: #09090b; border: 1px solid #27272a; border-radius: 28px; padding: 35px 25px; }}
  .calendar-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
  .calendar-table th {{ font-size: 16pt; color: #71717a; padding-bottom: 25px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; }}
  .calendar-table td {{ height: 135px; text-align: center; vertical-align: top; padding-top: 10px; border-top: 1px solid #18181b; position: relative; }}
  .day-number {{ font-size: 20pt; font-weight: 700; color: #f4f4f5; display: block; }}
  .today-cell-box {{ background: transparent; border: 3px solid #eab308; border-radius: 16px; padding: 6px 4px 4px 4px; margin: -4px auto 0 auto; width: 88%; box-shadow: 0 0 15px rgba(234, 179, 8, 0.3); }}
  .today-cell-box .day-number {{ color: #ffffff; font-weight: 900; }}
  .day-icon {{ height: 48px; text-align: center; margin-top: 6px; }}
  .footer {{ position: absolute; bottom: 50px; left: 0; width: 100%; text-align: center; font-size: 16pt; color: #52525b; font-weight: 500; }}
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
  <div class="footer">Sigue el clima diario en <span style="color: #eab308;">@tu_cuenta</span></div>
</body>
</html>"""

# Generar la imagen PNG directamente en formato 1080x1920
hti = Html2Image(size=(1080, 1920))
hti.screenshot(html_str=html_final, save_as='instagram_story.png')

print("¡Imagen generada exitosamente como 'instagram_story.png'!")
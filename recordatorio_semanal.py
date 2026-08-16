import os
import json
import datetime
import requests

# ---------------------------------------------------------
# CONFIGURACIÓN
# Requiere dos variables de entorno (Secrets en GitHub Actions):
#   TELEGRAM_BOT_TOKEN  -> token del bot
#   TELEGRAM_CHAT_ID    -> tu chat id personal
# ---------------------------------------------------------
BOT_TOKEN = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip().strip('"').strip("'")
CHAT_ID = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip().strip('"').strip("'")

# Orden fijo de categorías. No hace falta guardar estado en
# ningún lado: el número de semana ISO decide cuál toca.
CATEGORIAS = [
    {
        "titulo": "Gestión edilicia (GIE FAU)",
        "sugerencia": "Una foto de un avance o intervención edilicia, o un criterio de gestión explicado en 2-3 líneas."
    },
    {
        "titulo": "Investigación y territorio",
        "sugerencia": "Un mapa/imagen de un caso (Pila, Villa Devoto) o un concepto breve de tu marco teórico."
    },
    {
        "titulo": "Docencia (Taller de Comunicación)",
        "sugerencia": "Un trabajo destacado de estudiantes (con permiso) o una consigna/criterio pedagógico."
    },
    {
        "titulo": "Práctica profesional y pericial",
        "sugerencia": "Un concepto técnico-legal explicado simple, o una reflexión sobre la práctica profesional.",
        "carpeta": "practica_profesional"
    },
    {
        "titulo": "Mirada arquitectónica (fotografía)",
        "sugerencia": "Una foto de obra, material o luz con tu mirada personal — un detalle que otros no se detienen a mirar.",
        "carpeta": "mirada_arquitectonica"
    },
]

# Las primeras 4 categorías no tienen banco de fotos propio todavía
# (usan foto que él elige a mano); les completo la clave para que
# el resto del script funcione igual para las 5.
CATEGORIAS[0]["carpeta"] = "gestion_edilicia"
CATEGORIAS[1]["carpeta"] = "investigacion_territorio"
CATEGORIAS[2]["carpeta"] = "docencia"

def categoria_de_la_semana(fecha):
    numero_semana = fecha.isocalendar()[1]  # semana ISO del año (1-53)
    indice = numero_semana % len(CATEGORIAS)
    return CATEGORIAS[indice]

# ---------------------------------------------------------
# BANCO DE FOTOS
# Estructura esperada:
#   banco_fotos/<carpeta_categoria>/
#       foto1.jpg
#       foto2.jpg
#       captions.json   -> {"foto1.jpg": "pie de foto...", "foto2.jpg": "..."}
# Vos solo subís fotos y completás el captions.json. El script
# elige una sin repetir hasta agotar la carpeta.
# ---------------------------------------------------------
BANCO_FOTOS_DIR = "banco_fotos"
FOTOS_HISTORIAL_FILE = "historial_fotos.json"
EXTENSIONES_VALIDAS = (".jpg", ".jpeg", ".png")

def elegir_foto(carpeta_categoria):
    import random

    ruta_carpeta = os.path.join(BANCO_FOTOS_DIR, carpeta_categoria)
    if not os.path.isdir(ruta_carpeta):
        return None

    fotos = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith(EXTENSIONES_VALIDAS)]
    if not fotos:
        return None

    captions = {}
    ruta_captions = os.path.join(ruta_carpeta, "captions.json")
    if os.path.exists(ruta_captions):
        with open(ruta_captions, "r", encoding="utf-8") as f:
            try:
                captions = json.load(f)
            except Exception:
                captions = {}

    usadas = {}
    if os.path.exists(FOTOS_HISTORIAL_FILE):
        with open(FOTOS_HISTORIAL_FILE, "r", encoding="utf-8") as f:
            try:
                usadas = json.load(f)
            except Exception:
                usadas = {}

    ya_usadas = usadas.get(carpeta_categoria, [])
    disponibles = [f for f in fotos if f not in ya_usadas]

    if not disponibles:
        disponibles = fotos
        ya_usadas = []

    elegida = random.choice(disponibles)
    ya_usadas.append(elegida)
    usadas[carpeta_categoria] = ya_usadas

    with open(FOTOS_HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(usadas, f, indent=2, ensure_ascii=False)

    return {"archivo": elegida, "pie_de_foto": captions.get(elegida, "(sin pie de foto cargado)")}

def enviar_telegram(mensaje):
    if not BOT_TOKEN or not CHAT_ID:
        print("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID. Mensaje que se hubiera enviado:")
        print(mensaje)
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    respuesta = requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})
    print(f"Respuesta de Telegram (código {respuesta.status_code}): {respuesta.text}")

if __name__ == "__main__":
    hoy = datetime.datetime.now()
    categoria = categoria_de_la_semana(hoy)
    foto = elegir_foto(categoria["carpeta"])

    mensaje = (
        f"📅 Recordatorio semanal — semana {hoy.isocalendar()[1]}\n\n"
        f"Esta semana toca: *{categoria['titulo']}*\n\n"
        f"Idea: {categoria['sugerencia']}"
    )

    if foto:
        mensaje += (
            f"\n\n📷 Foto sugerida del banco: {foto['archivo']}\n"
            f"Pie de foto: {foto['pie_de_foto']}"
        )
    else:
        mensaje += "\n\n(Todavía no hay fotos cargadas en el banco para esta categoría.)"

    enviar_telegram(mensaje)
    print(mensaje)

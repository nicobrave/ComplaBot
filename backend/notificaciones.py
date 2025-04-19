import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote
from usuarios import obtener_usuario_por_email, obtener_datos_usuario
from supabase import create_client
import datetime

# Cargar variables de entorno
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Configuración
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
BASE_URL = os.getenv("BASE_URL") or "http://localhost:5000"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def enviar_email(email, asunto, cuerpo):
    """ENVÍA UN EMAIL UNIVERSAL vía MAILGUN para respuestas directas"""
    if not MAILGUN_DOMAIN or not MAILGUN_API_KEY:
        print("❌ Configuración de Mailgun incompleta")
        return False

    resp = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"ComplaBot <notificaciones@{MAILGUN_DOMAIN}>",
            "to": [email],
            "subject": asunto,
            "text": cuerpo
        }
    )

    print(f"📬 [{asunto}] enviado a {email} :: código response {resp.status_code}")
    return resp.status_code == 200


def obtener_interacciones_usuario(email: str) -> list:
    response = supabase.table("interacciones").select("*").eq("email", email).execute()
    return response.data or []


def enviar_correo_bienvenida(email: str) -> bool:
    if not MAILGUN_DOMAIN or not MAILGUN_API_KEY:
        raise ValueError("Faltan configuraciones de Mailgun en el archivo .env")

    industrias = ["tecnologia", "construccion", "servicios", "agricultura", "otra"]
    links = "\n".join([
        f"👉 {i.capitalize()}: {BASE_URL}/respuesta-industria?i={i}&e={email}"
        for i in industrias
    ])

    mensaje = f"""¡Bienvenido/a al agente de cumplimiento normativo!

A partir de ahora recibirás correos personalizados con recomendaciones prácticas para cumplir las leyes que afectan a tu empresa.

Comencemos con una pregunta simple: ¿en qué industria trabajas?
Haz clic en una opción para continuar:

{links}

Gracias por confiar en nosotros.
"""

    return enviar_email(email, "👋 Bienvenido a CumpliBot", mensaje)


def enviar_recomendacion_agente(email: str, industria: str, etapa: str, texto: str) -> bool:
    if not MAILGUN_DOMAIN or not MAILGUN_API_KEY:
        raise ValueError("Faltan configuraciones de Mailgun")

    etapa_url = quote(etapa)

    acciones = f"""
🛠️ Acciones rápidas:
- ✅ Marcar como completado: {BASE_URL}/accion?e={email}&etapa={etapa_url}&accion=completado
- 🔁 Siguiente etapa: {BASE_URL}/accion?e={email}&etapa={etapa_url}&accion=siguiente
- 📊 Ver mi reporte: {BASE_URL}/accion?e={email}&accion=reporte
"""

    cuerpo = f"""{texto}

{acciones}
"""

    return enviar_email(
        email,
        f"📌 Recomendaciones para {industria} – Etapa: {etapa}",
        cuerpo
    )


def enviar_reporte_estado(email: str) -> bool:
    print(f"📩 Generando resumen de estado para {email}")

    usuario = obtener_datos_usuario(email)
    interacciones = obtener_interacciones_usuario(email)

    industria = usuario.get("industria", "Sin declarar")
    etapa = usuario.get("etapa", "Diagnóstico")

    total = len(interacciones)
    completadas = sum(1 for i in interacciones if i["tipo"] == "completado")
    avance = int((completadas / total) * 100) if total > 0 else 0
    etapa_url = quote(etapa)

    resumen = f"""
📊 Resumen de la semana para {email}

🔹 Industria: {industria}
🔹 Etapa actual: {etapa}
🔹 Interacciones registradas: {total}
✅ Etapas completadas: {completadas}
📈 Progreso estimado: {avance}%
"""

    acciones = f"""
🛠️ Acciones disponibles:
- 🔁 Siguiente etapa: {BASE_URL}/accion?e={email}&etapa={etapa_url}&accion=siguiente
- ✅ Marcar como completado: {BASE_URL}/accion?e={email}&etapa={etapa_url}&accion=completado
"""

    cuerpo = resumen + acciones + "\nGracias por seguir avanzando con ComplaBot. 🚀"

    return enviar_email(
        email,
        f"📬 Tu resumen semanal – {industria}",
        cuerpo
    )
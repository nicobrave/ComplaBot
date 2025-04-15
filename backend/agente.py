import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def agente_cumplimiento(email):
    email = email.strip().lower()
    
    usuario = supabase.table("usuarios").select("*").ilike("email", email).execute()
    if not usuario.data:
        print("🚫 Usuario no encontrado")
        return

    industria = usuario.data[0].get("industria", "Otra")
    print(f"🎯 Industria detectada: {industria}")

    historial = supabase.table("interacciones")\
        .select("*")\
        .eq("email", email)\
        .order("timestamp", desc=True)\
        .execute()

    etapa_actual = "intro"
    if historial.data:
        etapas_previas = [h["etapa"] for h in historial.data]
        if "intro" in etapas_previas:
            etapa_actual = "ley1"

    contenido = f"Hola, te damos la bienvenida a tu guía de cumplimiento para la industria {industria}.\n\n"
    if etapa_actual == "intro":
        contenido += "Comenzaremos con una introducción general a las obligaciones legales más comunes."
    elif etapa_actual == "ley1":
        contenido += f"Hoy revisaremos la primera ley clave que aplica a {industria.lower()}."

    domain = os.getenv("MAILGUN_DOMAIN")
    api_key = os.getenv("MAILGUN_API_KEY")
    response = requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": f"ComplaBot <notificaciones@{domain}>",
            "to": [email],
            "subject": f"📌 Comienza tu ruta de cumplimiento: {etapa_actual}",
            "text": contenido
        }
    )

    print(f"📬 Correo enviado ({etapa_actual}) → {email}")
    print(f"🛠️ Status: {response.status_code} - {response.text}")

    supabase.table("interacciones").insert({
        "email": email,
        "tipo": "enviado",
        "etapa": etapa_actual,
        "industria": industria,
        "estado_agente": {"etapa": etapa_actual}
    }).execute()

# usuarios.py
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from pathlib import Path
import datetime

# Cargar variables de entorno
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def obtener_todos_los_usuarios():
    # Puedes ajustar para filtrar solo usuarios activos si quieres
    resp = supabase.table("usuarios").select("email").execute()
    return [item["email"] for item in resp.data or []]

def obtener_usuario_por_email(email: str) -> dict:
    response = supabase.table("usuarios")\
        .select("*")\
        .ilike("email", f"%{email.strip().lower()}%")\
        .execute()
    return response.data[0] if response.data else None

def obtener_etapa_usuario(email: str) -> str:
    response = supabase.table("interacciones")\
        .select("etapa")\
        .eq("email", email)\
        .order("timestamp", desc=True)\
        .limit(1)\
        .execute()
    if response.data and response.data[0].get("etapa"):
        return response.data[0]["etapa"]
    return "Diagnóstico"

def obtener_industria_usuario(email: str) -> str:
    usuario = obtener_usuario_por_email(email)
    return usuario.get("industria", "") if usuario else ""

def existe_usuario(email: str) -> bool:
    return bool(obtener_usuario_por_email(email))

def obtener_fecha_hoy():
    return datetime.date.today().isoformat()

def usuario_uso_respuesta_literal_hoy(email):
    today = obtener_fecha_hoy()
    response = supabase.table("interacciones")\
        .select("id")\
        .eq("email", email)\
        .eq("tipo", "respuesta_literal")\
        .gte("timestamp", today)\
        .execute()
    return len(response.data) > 0

def registrar_respuesta_literal(email: str, etapa: str = None) -> bool:
    """
    Registra en la tabla 'interacciones' una respuesta literal del usuario.
    Si no se pasa 'etapa', usa 'diagnostico' por defecto.
    """
    now = datetime.datetime.now().isoformat()
    etapa_a_insertar = etapa if etapa is not None else "diagnostico"

    supabase.table("interacciones").insert({
        "email":         email,
        "tipo":          "respuesta_literal",
        "etapa":         etapa_a_insertar,
        "estado_agente": "usado",
        "timestamp":     now
    }).execute()

    return True

def insertar_usuario(email: str) -> bool:
    response = supabase.table("usuarios").insert({
        "email": email.strip().lower(),
        "etapa": "Diagnóstico"
    }).execute()
    return bool(response.data)

def actualizar_industria(email: str, nueva_industria: str) -> bool:
    usuario = obtener_usuario_por_email(email)
    if not usuario:
        return False
    user_id = usuario.get("id")
    response = supabase.table("usuarios")\
        .update({"industria": nueva_industria})\
        .eq("id", user_id)\
        .execute()
    return bool(response.data)

def actualizar_etapa_usuario(email: str, nueva_etapa: str) -> bool:
    usuario = obtener_usuario_por_email(email)
    if not usuario:
        return False
    user_id = usuario.get("id")
    response = supabase.table("usuarios")\
        .update({"etapa": nueva_etapa})\
        .eq("id", user_id)\
        .execute()
    return bool(response.data)

def obtener_datos_usuario(email: str) -> dict:
    response = supabase.table("usuarios")\
        .select("*")\
        .ilike("email", f"%{email.strip().lower()}%")\
        .execute()
    if response.data and isinstance(response.data, list) and len(response.data) > 0:
        return response.data[0]
    return {}
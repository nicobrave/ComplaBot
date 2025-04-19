import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
from agente import agente_cumplimiento
from notificaciones import enviar_reporte_estado

# Cargar entorno
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def obtener_usuarios_con_interacciones():
    """
    Devuelve lista de emails de usuarios que tienen al menos una interacción registrada.
    """
    response = supabase.table("interacciones")\
        .select("email")\
        .execute()

    if not response.data:
        return []

    # Evita duplicados
    correos_unicos = list(set([item["email"] for item in response.data if "email" in item]))
    return correos_unicos

def run_inicio_semana():
    print("🚀 Enviando inicio de semana...")
    usuarios = obtener_usuarios_con_interacciones()
    print(f"👥 Usuarios con interacciones: {len(usuarios)}")

    if not usuarios:
        print("⚠️ No se encontraron usuarios con interacciones.")
        return

    for email in usuarios:
        try:
            print(f"🔄 Ejecutando agente para {email}")
            agente_cumplimiento(email)
        except Exception as e:
            print(f"❌ Error con {email}: {str(e)}")

def run_fin_semana():
    print("📊 Enviando resumen de fin de semana...")
    usuarios = obtener_usuarios_con_interacciones()
    print(f"👥 Usuarios con interacciones: {len(usuarios)}")

    if not usuarios:
        print("⚠️ No se encontraron usuarios con interacciones.")
        return

    for email in usuarios:
        try:
            print(f"📩 Enviando reporte a {email}")
            enviar_reporte_estado(email)
        except Exception as e:
            print(f"❌ Error con {email}: {str(e)}")

if __name__ == "__main__":
    opcion = input("¿Qué tarea quieres correr? (inicio | fin): ").strip().lower()
    
    if opcion == "inicio":
        run_inicio_semana()
    elif opcion == "fin":
        run_fin_semana()
    else:
        print("⚠️ Opción inválida. Usa: inicio o fin")

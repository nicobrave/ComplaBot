import os
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
from agente import agente_cumplimiento
from notificaciones import enviar_reporte_estado
from usuarios import obtener_todos_los_usuarios

# Cargar entorno
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def seguimiento_diario():
    print("📅 Enviando seguimiento diario a usuarios...")
    usuarios = obtener_todos_los_usuarios()
    print(f"👥 Usuarios encontrados: {len(usuarios)}")

    for email in usuarios:
        try:
            print(f"🔁 Enviando seguimiento IA a {email}")
            agente_cumplimiento(email)
        except Exception as e:
            print(f"❌ Error con {email}: {str(e)}")

def inicio_semana():
    print("🚀 Enviando apertura de semana...")
    usuarios = obtener_todos_los_usuarios()
    print(f"👥 Usuarios encontrados: {len(usuarios)}")

    for email in usuarios:
        try:
            print(f"🔄 Inicio de semana para {email}")
            agente_cumplimiento(email)
        except Exception as e:
            print(f"❌ Error con {email}: {str(e)}")

def fin_semana():
    print("📊 Enviando resumen de fin de semana...")
    usuarios = obtener_todos_los_usuarios()
    print(f"👥 Usuarios encontrados: {len(usuarios)}")

    for email in usuarios:
        try:
            print(f"📩 Enviando reporte a {email}")
            enviar_reporte_estado(email)
        except Exception as e:
            print(f"❌ Error con {email}: {str(e)}")

if __name__ == "__main__":
    import sys
    # Modo de uso: python scheduler.py diario
    if len(sys.argv) < 2:
        print("⚠️ Modo de uso: python scheduler.py diario|inicio|fin")
        exit(1)

    opcion = sys.argv[1]
    if opcion == "diario":
        seguimiento_diario()
    elif opcion == "inicio":
        inicio_semana()
    elif opcion == "fin":
        fin_semana()
    else:
        print("⚠️ Opción inválida. Usa: diario | inicio | fin")
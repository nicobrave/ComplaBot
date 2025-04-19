from supabase import create_client
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Cargar entorno
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def registrar_interaccion(email: str, tipo: str, etapa: str, industria: str, estado_agente: str = "activo") -> bool:
    try:
        data = {
            "email": email,
            "tipo": tipo,
            "etapa": etapa,
            "industria": industria,
            "estado_agente": estado_agente,
            "timestamp": datetime.utcnow().isoformat()
        }
        supabase.table("interacciones").insert(data).execute()
        print(f"✅ Interacción registrada: {data}")
        return True
    except Exception as e:
        print(f"❌ Error al registrar interacción: {str(e)}")
        return False

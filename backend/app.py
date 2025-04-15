from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from supabase import create_client
import requests
from dotenv import load_dotenv
from pathlib import Path

# Configuración inicial
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Carga MÁS TEMPRANO posible (antes de cualquier otra importación)
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Verificación EXPLÍCITA
# print("\n=== VALORES CARGADOS ===")
# print(f"MAILGUN_DOMAIN: {os.getenv('MAILGUN_DOMAIN')}")
# print(f"MAILGUN_API_KEY: {'***' if os.getenv('MAILGUN_API_KEY') else 'NO'}")
# print("=======================\n")

if "sandbox" in os.getenv("MAILGUN_DOMAIN", "").lower():
    raise ValueError("ERROR: Se está usando dominio sandbox. ¡Verifica tu .env!")

# Configuración de clientes
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def enviar_correo_bienvenida(email):
    """Envía correo usando dominio configurado en .env"""
    domain = os.getenv("MAILGUN_DOMAIN")
    api_key = os.getenv("MAILGUN_API_KEY")
    base_url = os.getenv("BASE_URL") or "http://localhost:5000"  # Puedes usar ngrok o dominio real

    if not domain or not api_key:
        raise ValueError("Faltan configuraciones de Mailgun en .env")

    if "sandbox" in domain:
        print(f"¡ADVERTENCIA! Usando dominio sandbox: {domain}")

    industrias = ["tecnologia", "construccion", "servicios", "agricultura", "otra"]

    links = "\n".join([
        f"👉 {i.capitalize()}: {base_url}/respuesta-industria?i={i}&e={email}"
        for i in industrias
    ])

    mensaje = f"""¡Bienvenido/a al agente de cumplimiento normativo!

A partir de ahora recibirás correos personalizados con recomendaciones prácticas para cumplir las leyes que afectan a tu empresa.

Comencemos con una pregunta simple: ¿en qué industria trabajas?
Haz clic en una opción para continuar:

{links}

Gracias por confiar en nosotros.
"""

    response = requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": f"ComplaBot <notificaciones@{domain}>",
            "to": [email],
            "subject": "👋 Bienvenido a ComplaBot",
            "text": mensaje
        }
    )

    print(f"\n=== Debug Email ===")
    print(f"Dominio usado: {domain}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    print("==================\n")

    return response


@app.route("/suscribirse", methods=["POST"])
def suscribirse():
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "Falta el email"}), 400

        # Verificar existencia
        existing = supabase.rpc(
            "verificar_email_existente", 
            {"email_input": email}
        ).execute()
        
        if existing.data:
            return jsonify({"message": "Ya estás suscrito"}), 200

        # Insertar nuevo usuario
        supabase.rpc(
            "insertar_usuario",
            {"email_input": email}
        ).execute()
        
        # Enviar correo con manejo explícito de errores
        try:
            mail_response = enviar_correo_bienvenida(email)
            if mail_response.status_code != 200:
                raise ValueError(f"Error Mailgun: {mail_response.text}")
        except Exception as mail_error:
            print(f"Error enviando correo: {str(mail_error)}")
            # Continúa aunque falle el correo
            return jsonify({
                "message": "Suscripción completada (pero correo no enviado)",
                "warning": str(mail_error)
            }), 200

        return jsonify({"message": "Suscripción exitosa"}), 200

    except Exception as e:
        print(f"\n=== Error en suscripción ===")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print("==========================\n")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/test-config")
def test_config():
    """Ruta para verificar configuraciones"""
    return jsonify({
        "mailgun_domain": os.getenv("MAILGUN_DOMAIN"),
        "supabase_connected": bool(os.getenv("SUPABASE_URL")),
        "env_file": str(env_path),
        "env_exists": env_path.exists()
    })

@app.route("/respuesta-industria", methods=["GET"])
def respuesta_industria_click():
    industria = request.args.get("i")
    email = request.args.get("e")

    if not industria or not email:
        return "❌ Datos inválidos", 400

    # Normalizar valores
    email = email.strip()
    industria = industria.strip().capitalize()

    try:
        # Actualizar con búsqueda insensible a mayúsculas
        response = supabase.table("usuarios").update({
            "industria": industria
        }).ilike("email", email).execute()

        print("🔍 Resultado del UPDATE:", response.data)

        if not response.data:
            return "⚠️ No se encontró el usuario para actualizar.", 404

        return f"✅ Gracias, hemos registrado tu industria: {industria}."

    except Exception as e:
        print("❌ Error al actualizar industria:", str(e))
        return "Error interno del servidor", 500


if __name__ == "__main__":
    # Verificación final antes de iniciar
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "MAILGUN_DOMAIN", "MAILGUN_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"\n❌ Faltan variables requeridas: {missing}")
        print("Verifica tu archivo .env y reinicia Flask\n")
    else:
        print("\n✅ Configuración válida detectada")
        print(f"Dominio Mailgun: {os.getenv('MAILGUN_DOMAIN')}\n")
    
    app.run(debug=True, port=5000)
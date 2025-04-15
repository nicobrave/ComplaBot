from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from supabase import create_client
import requests
from dotenv import load_dotenv
from pathlib import Path
from agente import agente_cumplimiento
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

from flask import render_template

@app.route("/")
def landing():
    return render_template("index.html")

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

    print(f"\n=== PARÁMETROS RECIBIDOS ===")
    print(f"Email: '{email}'")
    print(f"Industria: '{industria}'")
    
    if not industria or not email:
        return jsonify({"error": "Parámetros incompletos"}), 400

    try:
        email = email.strip().lower()
        industria = industria.strip().capitalize()

        print(f"\n=== PARÁMETROS NORMALIZADOS ===")
        print(f"Email: '{email}'")
        print(f"Industria: '{industria}'")

        all_users = supabase.table('usuarios').select('*').execute()
        print(f"\n=== TODOS LOS USUARIOS ===")
        for user in all_users.data:
            print(f"Usuario: {user['email']} - ID: {user.get('id')}")
        print("========================")

        user = supabase.table('usuarios')\
                     .select('*')\
                     .ilike('email', f"%{email}%")\
                     .execute()

        print(f"\n=== CONSULTA USUARIO ILIKE ===")
        print(f"Resultado: {user}")
        print(f"Datos: {user.data}")
        print("============================")

        if not user.data:
            return jsonify({"error": "Email no encontrado en la base de datos"}), 404

        user_id = user.data[0]['id']
        print(f"ID de usuario encontrado: {user_id}")

        update = supabase.table('usuarios')\
                       .update({'industria': industria})\
                       .eq('id', user_id)\
                       .execute()

        print(f"\n=== RESULTADO UPDATE ===")
        print(f"Update: {update}")
        print(f"Update data: {update.data}")

        updated = supabase.table('usuarios')\
                        .select('*')\
                        .eq('id', user_id)\
                        .execute()

        print(f"\n=== VERIFICACIÓN POST-ACTUALIZACIÓN ===")
        print(f"Usuario completo: {updated.data[0] if updated.data else 'No data'}")

        if updated.data:
            actual = updated.data[0].get('industria')
            print(f"Industria en BD: {actual}")
            print(f"Industria esperada: {industria}")

            if actual == industria:
                return f"""
                <html>
                  <head>
                    <title>Industria registrada</title>
                    <meta charset="UTF-8">
                    <style>
                      body {{
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding-top: 80px;
                        background-color: #f9f9f9;
                      }}
                      .card {{
                        display: inline-block;
                        background: white;
                        padding: 30px;
                        border-radius: 12px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                      }}
                      h2 {{
                        color: #2c3e50;
                      }}
                      p {{
                        color: #555;
                        font-size: 16px;
                      }}
                    </style>
                  </head>
                  <body>
                    <div class="card">
                      <h2>✅ ¡Gracias por registrarte!</h2>
                      <p>Hemos guardado tu industria como:</p>
                      <p><strong>{industria}</strong></p>
                      <p>Muy pronto recibirás recomendaciones adaptadas a tu sector.</p>
                    </div>
                  </body>
                </html>
                """
            else:
                return jsonify({
                    "warning": "La BD no refleja los cambios",
                    "current_data": updated.data[0]
                }), 500
        else:
            return jsonify({"error": "No se pudo verificar la actualización"}), 500

    except Exception as e:
        print(f"\n❌ Error crítico: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/activar-agente", methods=["GET"])
def activar_agente_manual():
    email = request.args.get("e")

    if not email:
        return "❌ Falta el parámetro ?e=email", 400

    try:
        from agente import agente_cumplimiento
        agente_cumplimiento(email)
        return f"✅ Agente ejecutado correctamente para: {email}", 200
    except Exception as e:
        print("❌ Error ejecutando el agente:", str(e))
        return f"⚠️ Error: {str(e)}", 500


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
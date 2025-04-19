# app.py
from flask import Flask, request, jsonify, render_template, render_template_string
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from supabase import create_client
from acciones import manejar_accion, procesar_respuesta_literal
from usuarios import (
    insertar_usuario,
    existe_usuario,
    actualizar_industria,
    obtener_usuario_por_email
)
from agente import agente_cumplimiento
from notificaciones import enviar_email
from agente import ComplaBotAgent
from usuarios import obtener_datos_usuario

# Configuración
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def enviar_correo_bienvenida(email):
    if not MAILGUN_DOMAIN or not MAILGUN_API_KEY:
        raise ValueError("Faltan configuraciones de Mailgun")

    industrias = ["tecnologia", "construccion", "servicios", "agricultura", "otra"]

    links = "\n".join([
        f"👉 {i.capitalize()}: {BASE_URL}/respuesta-industria?i={i}&e={email}"
        for i in industrias
    ])

    mensaje = f"""¡Bienvenido/a CumpliBot, tu agente de cumplimiento normativo!

A partir de ahora recibirás correos personalizados con recomendaciones prácticas para cumplir las leyes que afectan a tu empresa.

Comencemos con una pregunta simple: ¿en qué industria trabajas?
Haz clic en una opción para continuar:

{links}

Gracias por confiar en nosotros.
"""

    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"ComplaBot <notificaciones@{MAILGUN_DOMAIN}>",
            "to": [email],
            "subject": "👋 Bienvenido a ComplaBot",
            "text": mensaje
        }
    )

    print(f"📬 Envío correo → {response.status_code}")
    return response

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

        if existe_usuario(email):
            return jsonify({"message": "Ya estás suscrito"}), 200

        insertar_usuario(email)
        try:
            enviar_correo_bienvenida(email)
        except Exception as e:
            return jsonify({"message": "Suscripción completada, pero sin correo", "warning": str(e)}), 200

        return jsonify({"message": "Suscripción exitosa"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/respuesta-industria", methods=["GET"])
def respuesta_industria_click():
    industria = request.args.get("i")
    email = request.args.get("e")

    if not industria or not email:
        return jsonify({"error": "Faltan parámetros"}), 400

    if not existe_usuario(email):
        return jsonify({"error": "Usuario no encontrado"}), 404

    actualizar_industria(email, industria.capitalize())

    # NUEVO: Trigger automático de seguimiento con GPT (tras elegir industria)
    from agente import agente_cumplimiento
    agente_cumplimiento(email)
    
    return f"""
    <html><head><meta charset="UTF-8"><style>
    body {{ font-family: sans-serif; text-align: center; padding: 50px; }}
    .card {{ background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
    </style></head><body>
    <div class="card">
        <h2>✅ Industria registrada</h2>
        <p>Tu industria ha sido registrada como: <strong>{industria.capitalize()}</strong></p>
        <p>Pronto recibirás recomendaciones personalizadas.</p>
    </div></body></html>
    """

@app.route('/mailgun-webhook', methods=['POST'])
def mailgun_webhook():
    # Mailgun manda los campos como form-data
    sender = request.form.get('sender')
    recipient = request.form.get('recipient')
    subject = request.form.get('subject')
    body_plain = request.form.get('body-plain')
    # Puedes agregar más logs para inspección inicial
    print(f"Nuevo correo recibido de {sender} para {recipient}: {subject}")
    print(body_plain)

    # Procesa aquí la lógica según correo recibido
    # Por ejemplo: si el sender es un usuario registrado, procesar body_plain como consulta literal
    from usuarios import existe_usuario
    from acciones import procesar_respuesta_literal
    from agente import interpretar_gpt
    from notificaciones import enviar_email

    # Extrae el correo del usuario desde 'sender'
    # Ejemplo: "Nombre <micorreo@email.com>" -> extraer el correo dentro de <>
    import re
    match = re.search(r"<(.+?)>", sender)
    email = match.group(1) if match else sender

    if existe_usuario(email):
        result = procesar_respuesta_literal(email, body_plain)
        if result["status"] == "limitado":
            enviar_email(email, "Límite diario de consultas alcanzado", result["respuesta"])
        else:
            respuesta_gpt = interpretar_gpt(body_plain, email)
            enviar_email(email, "Respuesta de ComplaBot", respuesta_gpt)
    else:
        # ignorar o notificar de que no es usuario
        print(f"Correo de remitente desconocido: {email}")

    # Siempre responde 200 OK a Mailgun
    return "OK", 200

@app.route("/activar-agente", methods=["GET"])
def activar_agente_manual():
    email = request.args.get("e")
    if not email:
        return "❌ Falta el parámetro ?e=email", 400
    try:
        agente_cumplimiento(email)
        return f"✅ Agente ejecutado correctamente para: {email}", 200
    except Exception as e:
        return f"⚠️ Error: {str(e)}", 500

@app.route("/accion", methods=["GET"])
def accion_usuario():
    email = request.args.get("e")
    etapa = request.args.get("etapa", "")
    accion = request.args.get("accion")
    if not email or not accion:
        return "❌ Parámetros incompletos", 400
    email = email.strip().lower()
    return manejar_accion(email, accion, etapa)

@app.route('/respuesta', methods=['POST'])
def recibir_respuesta():
    data = request.json
    email = data.get("email")
    texto = data.get("texto")
    resultado = procesar_respuesta_literal(email, texto)
    if resultado["status"] == "limitado":
        enviar_email(
            email,
            "Límite diario de consultas alcanzado",
            resultado["respuesta"]
        )
        return jsonify({"accion": "limitado", "mensaje": resultado["respuesta"]}), 200

    # Nuevo pipeline IA: usa agente modular
    usuario = obtener_datos_usuario(email)
    industria = usuario.get("industria", "General")
    etapa = usuario.get("etapa", "Diagnóstico")

    agent = ComplaBotAgent()
    output = agent.interpretar(texto, email, industria, etapa)

    # Enviar el mensaje estructurado al usuario
    enviar_email(email, "Respuesta de ComplaBot", output.respuesta)

    # Puedes rutear lógica basada en output.accion, output.parametros aquí si lo deseas

    return jsonify({
        "accion": "permitido",
        "mensaje": "Respuesta enviada por email.",
        "respuesta_ia": output.respuesta,
        "deteccion_accion": output.accion,
        "confianza": output.confianza,
        "resumen": output.resumen,
        "parametros": output.parametros
    }), 200

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=True)

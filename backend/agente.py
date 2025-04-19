# agente.py
import requests
import openai
import os
from usuarios import obtener_datos_usuario
from notificaciones import enviar_recomendacion_agente

openai.api_key = os.environ.get("OPENAI_API_KEY")

def obtener_respuesta_langflow(industria: str, etapa: str, resultado: str) -> str:
    try:
        url = "http://localhost:7860/api/v1/run/2e0a65f2-07e6-4411-8187-78b072acdfbe"
        payload = {
            "industria": industria,
            "etapa": etapa,
            "resultado": resultado,
            "input_type": "text",
            "output_type": "text"
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        return response.text if response.ok else "⚠️ Error generando recomendación con Langflow"
    except Exception as e:
        return f"❌ Error llamando a Langflow: {str(e)}"

def interpretar_gpt(contenido_usuario, email):
    system_prompt = (
        "Eres CumpliBot, un agente de cumplimiento normativo que responde profesional, "
        "claro y siempre en tono humano. Solo responde a temas reales de cumplimiento. "
        "El/La usuario/a puede pausar, pedir reporte, sugerir frecuencia, solicitar contenido legal, o avanzar etapa. "
        "Si la consulta es poco clara, pide reformular la pregunta."
    )
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": contenido_usuario}
            ],
            max_tokens=500,
            temperature=0.2,
            user=email
        )
        texto_respuesta = respuesta['choices'][0]['message']['content'].strip()
        return texto_respuesta
    except Exception as e:
        print(f"Error GPT-4.1: {e}")
        return (
            "Lo siento, hubo un problema técnico procesando tu mensaje. "
            "Intenta nuevamente en unos minutos."
        )

def agente_cumplimiento(email: str):
    print(f"\n🎯 Ejecutando agente para: {email}")
    usuario = obtener_datos_usuario(email)

    if not isinstance(usuario, dict):
        print("🚫 Usuario no encontrado o formato inválido")
        return

    industria = usuario.get("industria", "").strip().capitalize()
    etapa = usuario.get("etapa", "Diagnóstico").strip().capitalize()

    print(f"🎯 Industria detectada: {industria}")
    print(f"🔄 Etapa actual: {etapa}")

    resultado_placeholder = "..."  # si quieres puedes cambiarlo por algo más informativo
    texto = obtener_respuesta_langflow(industria, etapa, resultado_placeholder)

    enviar_recomendacion_agente(email, industria, etapa, texto)
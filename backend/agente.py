# agente.py
import openai
import os
from usuarios import obtener_datos_usuario
from notificaciones import enviar_recomendacion_agente


openai.api_key = os.environ.get("OPENAI_API_KEY")

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

    # Usamos GPT para generar el texto de recomendación inicial
    prompt = f"Envia una primera recomendación legal y de cumplimiento para una empresa de la industria {industria} en la etapa {etapa}."
    texto = interpretar_gpt(prompt, email)

    enviar_recomendacion_agente(email, industria, etapa, texto)
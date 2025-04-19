# agente.py

import os
import json
import openai
from pydantic import BaseModel
from usuarios import obtener_datos_usuario
from notificaciones import enviar_recomendacion_agente

# Inicializa cliente compatible con openai>=1.0.0
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Output estructurado
class CumplimientoOutput(BaseModel):
    accion: str            # e.g. "pausa", "siguiente", "completado", etc.
    parametros: dict
    respuesta: str
    confianza: float
    resumen: str

class ComplaBotAgent:
    def __init__(self, nombre="ComplaBot"):
        self.nombre = nombre

    def interpretar(self, user_input, user_email, industria, etapa):
        system_prompt = (
            f"Eres ComplaBot, un agente experto en cumplimiento normativo para empresas chilenas. "
            f"Industria: {industria}. Etapa: {etapa}. "
            "Interpreta la consulta del usuario para identificar su intención principal "
            "(pausar, avanzar etapa, reporte, ajustar frecuencia, solicitar contenido legal, etc). "
            "Devuelve SIEMPRE un JSON con este schema: {accion, parametros, respuesta, confianza, resumen}. "
            "Si no entiendes la intención o hay mezcla, sé honesto y acláralo en 'respuesta'."
        )
        user_prompt = f"Usuario: '{user_input}'"

        try:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1,
                user=user_email
            )
            raw = response.choices[0].message.content

            def limpiar_json(texto):
                import re
                # Quita ```json ... ``` o ``` ... ``` y espacios extras
                texto = texto.strip()
                texto = re.sub(r'^```json', '', texto)
                texto = re.sub(r'^```', '', texto)
                texto = re.sub(r'```$', '', texto)
                return texto.strip()

            try:
                clean_json = limpiar_json(raw)
                output = CumplimientoOutput(**json.loads(clean_json))
            except Exception:
                output = CumplimientoOutput(
                    accion="desconocido",
                    parametros={},
                    respuesta=raw,
                    confianza=0.5,
                    resumen="Respuesta directa, no estructurada."
                )
            return output

        except Exception as e:
            return CumplimientoOutput(
                accion="error",
                parametros={},
                respuesta=f"Error técnico: {e}",
                confianza=0,
                resumen="Fallo técnico"
            )

def agente_cumplimiento(email: str):
    usuario = obtener_datos_usuario(email)
    if not isinstance(usuario, dict):
        print("🚫 Usuario no encontrado o formato inválido")
        return

    industria = usuario.get("industria", "General")
    etapa = usuario.get("etapa", "Diagnóstico")

    prompt = f"Envia una primera recomendación legal y de cumplimiento para una empresa de la industria {industria} en la etapa {etapa}."
    agent = ComplaBotAgent()
    output = agent.interpretar(prompt, email, industria, etapa)
    enviar_recomendacion_agente(email, industria, etapa, output.respuesta)

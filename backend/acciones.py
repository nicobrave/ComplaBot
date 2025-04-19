# acciones.py
from usuarios import (
    usuario_uso_respuesta_literal_hoy,
    registrar_respuesta_literal,
    obtener_usuario_por_email,
    actualizar_etapa_usuario
)
from notificaciones import enviar_reporte_estado, enviar_recomendacion_agente
from interacciones import registrar_interaccion
from agente import obtener_respuesta_langflow

ETAPAS = ["Diagnóstico", "Evaluación", "Implementación", "Verificación", "Cierre"]

def avanzar_etapa(etapa_actual: str) -> str:
    try:
        idx = ETAPAS.index(etapa_actual)
        return ETAPAS[idx + 1] if idx + 1 < len(ETAPAS) else etapa_actual
    except Exception:
        return etapa_actual

def procesar_respuesta_literal(email, texto, etapa=None):
    if usuario_uso_respuesta_literal_hoy(email):
        return {
            "status": "limitado",
            "respuesta": (
                "¡Hola! Por políticas de uso, solo puedes realizar una "
                "consulta libre diaria. Si necesitas ampliar tu acceso, "
                "escríbenos a contacto@recomai.cl para conocer nuestros planes premium."
            )
        }
    registrar_respuesta_literal(email, etapa=etapa)
    return {
        "status": "permitido",
        "respuesta": None
    }

def manejar_accion(email: str, accion: str, etapa: str = None) -> str:
    usuario = obtener_usuario_por_email(email)
    if not usuario:
        return "❌ Usuario no encontrado"

    industria = usuario.get("industria", "General (todas las industrias)")
    etapa_actual = etapa or usuario.get("etapa", "Diagnóstico")

    if accion == "completado":
        registrar_interaccion(email, "completado", etapa_actual, industria)
        return f"""
        <html><head><meta charset="utf-8"></head>
        <body style="font-family:sans-serif;padding:40px;text-align:center;">
        <h2>✅ Acción registrada</h2>
        <p>Tu acción <strong>completado</strong> fue registrada para la etapa <strong>{etapa_actual}</strong>.</p>
        <p>¡Gracias por mantener tu cumplimiento al día!</p>
        </body></html>
        """

    elif accion == "siguiente":
        nueva_etapa = avanzar_etapa(etapa_actual)
        actualizar_etapa_usuario(email, nueva_etapa)
        registrar_interaccion(email, "siguiente", nueva_etapa, industria)

        resultado = obtener_respuesta_langflow(industria, nueva_etapa, "sin contexto")

        ok = enviar_recomendacion_agente(email, industria, nueva_etapa, resultado)

        return f"""
        <html><head><meta charset="utf-8"></head>
        <body style="font-family:sans-serif;padding:40px;text-align:center;">
        <h2>🔁 Etapa actualizada</h2>
        <p>Tu nueva etapa es <strong>{nueva_etapa}</strong>.</p>
        <p>{'📬 Recomendación enviada a tu correo.' if ok else '⚠️ No se pudo enviar el correo.'}</p>
        </body></html>
        """

    elif accion == "reporte":
        registrar_interaccion(email, "reporte", etapa_actual, industria)
        ok = enviar_reporte_estado(email)
        return f"""
        <html><head><meta charset="utf-8"></head>
        <body style="font-family:sans-serif;padding:40px;text-align:center;">
        <h2>📬 Reporte semanal</h2>
        <p>{'Tu resumen ha sido enviado a tu correo.' if ok else '⚠️ No se pudo enviar el reporte por correo.'}</p>
        </body></html>
        """
    else:
        return f"""
        <html><head><meta charset="utf-8"></head>
        <body style="font-family:sans-serif;padding:40px;text-align:center;">
        <h2>⚠️ Acción no reconocida</h2>
        <p>No se pudo procesar la acción: <strong>{accion}</strong>.</p>
        <p>Intenta con otra opción válida.</p>
        </body></html>
        """
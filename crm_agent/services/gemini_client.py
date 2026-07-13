import json

from decouple import config
from google import genai
from google.genai import types

MODEL_ID = config('GEMINI_MODEL', default='gemini-3.5-flash')

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=config('GEMINI_API_KEY'))
    return _client


def _formatear_historial(mensajes: list[dict]) -> str:
    return '\n'.join(f"{m['emisor']}: {m['contenido']}" for m in mensajes)


def responder_chat(mensajes_conversacion: list[dict], tipo_lead: str) -> str:
    system_instruction = (
        'Eres el Agente Comercial IA de un ISP. Identifica si el prospecto es '
        f'B2B o B2C (ya confirmado como {tipo_lead}) y haz preguntas relevantes '
        'sobre interés, presupuesto y urgencia. Sé breve, cordial y profesional. '
        'No prometas descuentos ni fechas concretas — eso lo decide un humano.'
    )
    response = _get_client().models.generate_content(
        model=MODEL_ID,
        contents=_formatear_historial(mensajes_conversacion),
        config=types.GenerateContentConfig(
            system_instruction=system_instruction, temperature=0.6,
        ),
    )
    return response.text


def calificar_lead(mensajes_conversacion: list[dict], tipo_lead: str) -> dict:
    system_instruction = (
        f'Eres un agente comercial de un ISP. Analiza la conversación con un '
        f'prospecto {tipo_lead} y devuelve SOLO JSON con las claves: '
        'prioridad_score (entero 0-100), urgencia (BAJA|MEDIA|ALTA), '
        'resumen_necesidad (string), objeciones (string), '
        'siguiente_accion_sugerida (AGENDAR|ENVIAR_MATERIAL|DERIVAR_ESPECIALISTA|NONE).'
    )
    response = _get_client().models.generate_content(
        model=MODEL_ID,
        contents=_formatear_historial(mensajes_conversacion),
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type='application/json',
            temperature=0.3,
        ),
    )
    return json.loads(response.text)


def tutor_responder(pregunta_usuario: str) -> dict:
    system_instruction = (
        "Eres el tutor financiero de 'Futuro Academy'. Responde solo con "
        'conceptos básicos de ahorro e inversión, en español sencillo. '
        'Indica siempre la fuente del contenido. Devuelve SOLO JSON con claves: '
        'respuesta (string), fuente (string), quiz (lista de exactamente 3 '
        'objetos con pregunta, opciones [lista de 4 strings], respuesta_correcta).'
    )
    response = _get_client().models.generate_content(
        model=MODEL_ID,
        contents=pregunta_usuario,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type='application/json',
            temperature=0.4,
        ),
    )
    return json.loads(response.text)
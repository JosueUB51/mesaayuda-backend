import json
import os
from openai import OpenAI

from app.config import OPENAI_API_KEY, MODEL, BACKEND_PUBLIC_URL
from app.agent.memory import get_session
from app.agent.router import classify_intent

client = OpenAI(api_key=OPENAI_API_KEY)

USER_FIELDS = ["nombre", "area", "edificio", "piso"]

USER_QUESTIONS = [
    "Por favor indícame tu nombre completo.",
    "¿En qué área trabajas?",
    "¿En qué edificio te encuentras?",
    "¿En qué piso estás ubicado?"
]


def load_playbook(intent):

    path = f"app/playbooks/{intent}.json"

    if not os.path.exists(path):
        return None

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_intelligent_agent(session_id, user_input):

    session = get_session(session_id)

    session.setdefault("intent", None)
    session.setdefault("status", "intent_detection")
    session.setdefault("user_step", 0)
    session.setdefault("problem_description", None)
    session.setdefault("history", [])

    session.setdefault("vpn_form_uploaded", False)
    session.setdefault("correo_form_uploaded", False)

    session.setdefault("user_data", {
        "nombre": None,
        "area": None,
        "edificio": None,
        "piso": None
    })

    # =========================================
    # SESIÓN COMPLETADA
    # =========================================

    if session.get("status") == "completed":

        system_prompt = """
Eres un agente humano de Mesa de Ayuda.

La solicitud del usuario ya fue registrada correctamente y el equipo técnico la procesará.

Responde de forma natural dependiendo del mensaje del usuario.
"""

        response = client.chat.completions.create(
            model=MODEL,
            temperature=0.4,
            max_tokens=150,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )

        return response.choices[0].message.content

    # =========================================
    # BIENVENIDA
    # =========================================

    if session["status"] == "welcome":

        session["status"] = "intent_detection"

        return """Hola 👋

Soy el asistente de Mesa de Ayuda.

Puedo ayudarte con:

• Internet
• VPN
• Correo institucional
• Sistemas

Por favor describe tu problema."""

    # =========================================
    # DETECTAR INTENCIÓN
    # =========================================

    if session["status"] == "intent_detection":

        intent = classify_intent(user_input)

        session["intent"] = intent
        session["problem_description"] = user_input

        if intent == "otro":

            return """Hola 👋

Puedo ayudarte con los siguientes servicios:

• Internet
• VPN
• Correo institucional
• Sistemas

Por favor describe tu problema."""

        session["status"] = "collecting_user_data"

        return USER_QUESTIONS[0]

    # =========================================
    # RECOLECTAR DATOS
    # =========================================

    if session["status"] == "collecting_user_data":

        field_index = session["user_step"]

        if field_index < len(USER_FIELDS):

            field_name = USER_FIELDS[field_index]

            session["user_data"][field_name] = user_input

            session["user_step"] += 1

            if session["user_step"] < len(USER_FIELDS):

                return USER_QUESTIONS[session["user_step"]]

        session["status"] = "active"

    # =========================================
    # FLUJO VPN
    # =========================================

    if session["intent"] == "vpn":

        problem = (session.get("problem_description") or "").lower()

        keywords_solicitud = [
            "solicitar",
            "crear vpn",
            "alta vpn",
            "nueva vpn",
            "pedir vpn"
        ]

        solicitud = any(k in problem for k in keywords_solicitud)

        # ---------------------------
        # SOLICITUD VPN
        # ---------------------------

        if solicitud:

            if session.get("vpn_form_uploaded"):

                session["status"] = "completed"

                return {
                    "type": "vpn_success",
                    "message": """Tu solicitud de VPN fue recibida correctamente.

El equipo técnico procesará tu solicitud.
Normalmente tarda entre 24 y 48 horas."""
                }

            url = f"{BACKEND_PUBLIC_URL}/vpn/formato"

            return {
                "type": "vpn_download",
                "message": """Para solicitar VPN:

1. Descarga el formato
2. Llénalo
3. Asegúrate de que el formato esté nombrado correctamente (vpn_formato.pdf)
4. Súbelo usando el botón +

Procesaremos tu solicitud.""",
                "fileName": "Formato_Solicitud_VPN.pdf",
                "url": url
            }

        # ---------------------------
        # PROBLEMA VPN
        # ---------------------------

        # continuar diagnóstico con IA

    # =========================================
    # FLUJO CORREO
    # =========================================

    if session["intent"] == "correo":

        problem = (session.get("problem_description") or "").lower()

        keywords_solicitud = [
            "solicitar",
            "crear correo",
            "nuevo correo",
            "alta de correo"
        ]

        solicitud = any(k in problem for k in keywords_solicitud)

        # ---------------------------
        # SOLICITUD CORREO
        # ---------------------------

        if solicitud:

            if session.get("correo_form_uploaded"):

                session["status"] = "completed"

                return {
                    "type": "correo_success",
                    "message": """Tu solicitud de correo fue recibida correctamente.

El área de TI procesará tu solicitud."""
                }

            url = f"{BACKEND_PUBLIC_URL}/correo/formato"

            return {
                "type": "correo_download",
                "message": """Para solicitar un correo institucional:

1. Descarga el formato oficial
2. Llénalo completamente
3. Asegúrate de que el formato esté nombrado correctamente (correo_formato.pdf)
4. Súbelo usando el botón +

Procesaremos tu solicitud.""",
                "fileName": "Formato_Solicitud_Correo.pdf",
                "url": url
            }

        # ---------------------------
        # PROBLEMA CORREO
        # ---------------------------

        # continuar diagnóstico con IA

    # =========================================
    # IA DIAGNÓSTICO
    # =========================================

    playbook = load_playbook(session["intent"])

    session["history"].append({
        "role": "user",
        "content": user_input
    })

    system_prompt = f"""
Eres un agente técnico de Mesa de Ayuda gubernamental.

Tu objetivo es ayudar al usuario paso a paso.

REGLAS:

• SOLO da un paso de diagnóstico por respuesta
• nunca des listas largas
• pregunta siempre qué ocurrió después del paso

Si después de varios intentos no se resuelve el problema,
indica que será canalizado con un asesor técnico.

Datos del usuario:

Nombre: {session['user_data']['nombre']}
Área: {session['user_data']['area']}
Edificio: {session['user_data']['edificio']}
Piso: {session['user_data']['piso']}

Problema reportado:
{session['problem_description']}

Playbook técnico:
{playbook}
"""

    messages = [{"role": "system", "content": system_prompt}] + session["history"]

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=300,
        temperature=0.2,
        messages=messages
    )

    answer = response.choices[0].message.content

    session["history"].append({
        "role": "assistant",
        "content": answer
    })

    return answer
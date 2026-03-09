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
    # 1 DETECTAR INTENCIÓN PRIMERO
    # =========================================

    if session["status"] == "intent_detection":

        intent = classify_intent(user_input)
        session["intent"] = intent

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
    # 2 RECOLECCIÓN DE DATOS
    # =========================================

    if session["status"] == "collecting_user_data":

        field_index = session["user_step"]

        if field_index < len(USER_FIELDS):
            field_name = USER_FIELDS[field_index]
            session["user_data"][field_name] = user_input

            session["user_step"] += 1

            if session["user_step"] < len(USER_FIELDS):
                return USER_QUESTIONS[session["user_step"]]

        session["status"] = "collecting_problem"

        return "Gracias. Ahora descríbeme tu problema."

    # =========================================
    # 3 GUARDAR PROBLEMA
    # =========================================

    if session["status"] == "collecting_problem":

        session["problem_description"] = user_input
        session["status"] = "active"

    # =========================================
    # FLUJO VPN
    # =========================================

    if session["intent"] == "vpn":

        if not session["vpn_form_uploaded"]:

            url = f"{BACKEND_PUBLIC_URL}/vpn/formato"

            return {
                "type": "vpn_download",
                "message": """Para continuar con tu solicitud de VPN:

1. Descarga el formato oficial
2. Llénalo completamente
3. Súbelo usando el botón +

Una vez que lo subas procesaremos tu solicitud.
""",
                "fileName": "Formato_Solicitud_VPN.pdf",
                "url": url
            }

        else:

            session["status"] = "completed"

            return {
                "type": "vpn_success",
                "message": "Tu solicitud de VPN fue recibida correctamente. Recibirás tus credenciales en tu correo institucional."
            }

    # =========================================
    # FLUJO CORREO
    # =========================================

    if session["intent"] == "correo":

        if not session["correo_form_uploaded"]:

            url = f"{BACKEND_PUBLIC_URL}/correo/formato"

            return {
                "type": "correo_download",
                "message": """Para solicitar un correo institucional:

1. Descarga el formato oficial
2. Llénalo completamente
3. Súbelo usando el botón +

Una vez que lo subas procesaremos tu solicitud.
""",
                "fileName": "Formato_Solicitud_Correo.pdf",
                "url": url
            }

        else:

            session["status"] = "completed"

            return {
                "type": "correo_success",
                "message": "Tu solicitud de correo fue recibida correctamente. Recibirás tus credenciales en breve."
            }

    # =========================================
    # IA NORMAL
    # =========================================

    playbook = load_playbook(session["intent"])

    session["history"].append({
        "role": "user",
        "content": user_input
    })

    system_prompt = f"""
Eres un agente profesional de Mesa de Ayuda gubernamental.

Datos del usuario:

Nombre: {session['user_data']['nombre']}
Área: {session['user_data']['area']}
Edificio: {session['user_data']['edificio']}
Piso: {session['user_data']['piso']}

Problema reportado:
{session['problem_description']}

Nunca te identifiques con el nombre del usuario.

Playbook:
{playbook}
"""

    messages = [{"role": "system", "content": system_prompt}] + session["history"]

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=400,
        temperature=0.3,
        messages=messages
    )

    answer = response.choices[0].message.content

    session["history"].append({
        "role": "assistant",
        "content": answer
    })

    return answer
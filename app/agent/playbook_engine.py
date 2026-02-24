import json
import os
from openai import OpenAI
from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL
from app.agent.memory import get_session
from app.agent.router import classify_intent

# =========================================
# CONFIGURACIÓN
# =========================================

PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL")

USER_FIELDS = ["nombre", "area", "edificio", "piso"]

USER_QUESTIONS = [
    "Por favor indícame tu nombre completo.",
    "¿En qué área trabajas?",
    "¿En qué edificio te encuentras?",
    "¿En qué piso estás ubicado?"
]

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    default_headers={
        "HTTP-Referer": PUBLIC_BACKEND_URL or "",
        "X-Title": "Mesa de Ayuda IA"
    }
)

# =========================================
# CARGAR PLAYBOOK
# =========================================

def load_playbook(intent):
    if not intent:
        return None

    path = f"app/playbooks/{intent}.json"
    if not os.path.exists(path):
        return None

    with open(path) as f:
        return json.load(f)


# =========================================
# AGENTE PRINCIPAL
# =========================================

def run_intelligent_agent(session_id, user_input):

    session = get_session(session_id)

    session.setdefault("intent", None)
    session.setdefault("status", "collecting_user_data")
    session.setdefault("user_step", 0)
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
    # FASE 1 — RECOLECCIÓN DE DATOS
    # =========================================

    if session["status"] == "collecting_user_data":

        if session["user_step"] == 0 and session["user_data"]["nombre"] is None:
            session["user_step"] = 1
            return USER_QUESTIONS[0]

        field_index = session["user_step"] - 1

        if 0 <= field_index < len(USER_FIELDS):
            field_name = USER_FIELDS[field_index]
            session["user_data"][field_name] = user_input

        if session["user_step"] < len(USER_FIELDS):
            question = USER_QUESTIONS[session["user_step"]]
            session["user_step"] += 1
            return question

        session["status"] = "active"
        session["user_step"] = None

        return f"Gracias {session['user_data']['nombre']}. Ahora descríbeme tu problema."

    # =========================================
    # CLASIFICAR INTENCIÓN
    # =========================================

    if session["intent"] is None:
        session["intent"] = classify_intent(user_input)

    # =========================================
    # FLUJO VPN
    # =========================================

    if session["intent"] == "vpn":

        if not session["vpn_form_uploaded"]:
            return {
                "type": "vpn_download",
                "message": """Para continuar con tu solicitud de VPN:

1. Descarga el formato oficial.
2. Llénalo completamente.
3. Súbelo usando el botón "+".

Una vez que lo subas, procesaremos tu solicitud.
""",
                "fileName": "Formato_Solicitud_VPN.pdf",
                "url": f"{PUBLIC_BACKEND_URL}/vpn/formato"
            }

        else:
            session["intent"] = None
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
            return {
                "type": "correo_download",
                "message": """Para solicitar un correo institucional:

1. Descarga el formato oficial.
2. Llénalo completamente.
3. Súbelo usando el botón "+".

Una vez que lo subas, procesaremos tu solicitud.
""",
                "fileName": "Formato_Solicitud_Correo.pdf",
                "url": f"{PUBLIC_BACKEND_URL}/correo/formato"
            }

        else:
            session["intent"] = None
            session["status"] = "completed"

            return {
                "type": "correo_success",
                "message": "Tu solicitud de correo fue recibida correctamente. Recibirás tus credenciales en breve."
            }

    # =========================================
    # AGENTE IA NORMAL
    # =========================================

    playbook = load_playbook(session["intent"])

    session["history"].append({"role": "user", "content": user_input})

    system_prompt = f"""
Eres un agente profesional de Mesa de Ayuda gubernamental.

Nombre: {session['user_data']['nombre']}
Área: {session['user_data']['area']}
Edificio: {session['user_data']['edificio']}
Piso: {session['user_data']['piso']}

Playbook:
{playbook}

Responde profesionalmente y de forma conversacional.
"""

    messages = [{"role": "system", "content": system_prompt}] + session["history"]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=400,
            temperature=0.4,
            messages=messages
        )

        answer = response.choices[0].message.content

        session["history"].append({"role": "assistant", "content": answer})

        return answer

    except Exception as e:
        print("ERROR OPENROUTER:", e)
        return "Ocurrió un error procesando tu solicitud. Intenta nuevamente."